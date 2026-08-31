import os
import tempfile
import time
from io import BytesIO

import numpy as np
import rasterio
import streamlit as st
import folium
from PIL import Image
from streamlit_folium import st_folium
from services.cv_inference import get_photo_path_by_id
from services.gis_service import get_lulc_at_point, get_terrain_at_point
from services.risk_engine import calculate_flood_risk
from services.spatial import find_nearby_survey_points
from components.banners import render_image_banner

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, "DATA")


def safe_float(value, default=0.0):
    try:
        if value == "" or value is None:
            return default
        return float(value)
    except (ValueError, TypeError):
        return default


def render_interactive_map(survey_points: list[dict], center_lat: float = 5.6493, center_lng: float = -0.2069):
    #st.markdown("### 🗺️ Interactive Flood Risk Map — Kisseman")
    render_image_banner("flood_map.jpg")
    #st.caption("💡 *Tap a survey point to view its photo and details. Tap empty ground for a new prediction.*")

    # --- DEBUG: how many points are we even dealing with? ---
    #st.write(f"DEBUG: survey_points count = {len(survey_points) if survey_points else 0}")

    c_lat = float(center_lat) if center_lat else 5.6493
    c_lng = float(center_lng) if center_lng else -0.2069

    t0 = time.time()
    m = folium.Map(location=[c_lat, c_lng], zoom_start=16, tiles="OpenStreetMap")
    #st.write(f"DEBUG: Map object created in {time.time()-t0:.2f}s")

    def colorize_raster(array: np.ndarray, mode: str, colormap: dict | None = None):
        arr = np.asarray(array, dtype=np.float32)
        mask = np.isfinite(arr)
        rgb = np.zeros((arr.shape[0], arr.shape[1], 3), dtype=np.uint8)

        if colormap:
            for val, color in colormap.items():
                if not isinstance(color, (tuple, list)):
                    continue
                if len(color) >= 3:
                    target = np.array(color[:3], dtype=np.uint8)
                    idx = (arr == float(val)) & mask
                    rgb[idx] = target
            alpha = np.where(mask, 255, 0).astype(np.uint8)
            rgba = np.dstack([rgb, alpha])
            return rgba

        if mode == "lulc":
            color_map = {
                0: np.array([82, 82, 82], dtype=np.uint8),
                1: np.array([34, 139, 34], dtype=np.uint8),
            }
            for val, color in color_map.items():
                rgb[np.where((arr == val) & mask)] = color
        elif mode == "slope":
            finite = arr[np.isfinite(arr)]
            if finite.size:
                lo, hi = float(np.nanmin(finite)), float(np.nanmax(finite))
                if hi > lo:
                    norm = np.clip((arr - lo) / (hi - lo), 0, 1)
                else:
                    norm = np.zeros_like(arr)
            else:
                norm = np.zeros_like(arr)
            rgb[:, :, 0] = np.uint8(255 * (1 - norm))
            rgb[:, :, 1] = np.uint8(220 * norm)
            rgb[:, :, 2] = np.uint8(50 * (1 - norm))
        elif mode == "flow":
            finite = arr[np.isfinite(arr)]
            if finite.size:
                lo, hi = float(np.nanmin(finite)), float(np.nanmax(finite))
                if hi > lo:
                    norm = np.clip((arr - lo) / (hi - lo), 0, 1)
                else:
                    norm = np.zeros_like(arr)
            else:
                norm = np.zeros_like(arr)
            rgb[:, :, 0] = np.uint8(255 * norm)
            rgb[:, :, 1] = np.uint8(120 + 115 * norm)
            rgb[:, :, 2] = np.uint8(20 + 80 * (1 - norm))
        elif mode == "dem":
            finite = arr[np.isfinite(arr)]
            if finite.size:
                lo, hi = float(np.nanmin(finite)), float(np.nanmax(finite))
                if hi > lo:
                    norm = np.clip((arr - lo) / (hi - lo), 0, 1)
                else:
                    norm = np.zeros_like(arr)
            else:
                norm = np.zeros_like(arr)
            rgb[:, :, 0] = np.uint8(255 * (1 - norm))
            rgb[:, :, 1] = np.uint8(140 + 100 * norm)
            rgb[:, :, 2] = np.uint8(60 + 120 * (1 - norm))
        else:
            rgb[:] = [180, 180, 180]

        alpha = np.where(mask, 255, 0).astype(np.uint8)
        rgba = np.dstack([rgb, alpha])
        return rgba

    def add_raster_layer(raster_path: str, name: str, mode: str, opacity: float = 0.55):
        with rasterio.open(raster_path) as src:
            array = src.read(1, masked=True)
            west, south, east, north = src.bounds
            try:
                colormap = src.colormap(1)
            except ValueError:
                colormap = None
            rgba = colorize_raster(array, mode, colormap=colormap if colormap else None)
            image = Image.fromarray(rgba, mode="RGBA")
            buffer = BytesIO()
            image.save(buffer, format="PNG")

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp.write(buffer.getvalue())
            temp_path = tmp.name

        overlay = folium.raster_layers.ImageOverlay(
            image=temp_path,
            bounds=[[south, west], [north, east]],
            opacity=opacity,
            name=name,
            overlay=True,
            control=True,
        )
        overlay.add_to(m)
        return overlay

    # Raster layers that can be toggled on/off
    add_raster_layer(os.path.join(DATA_DIR, "Kisseman_lulc.tif"), "Land Use / Land Cover", "lulc", opacity=0.65)
    add_raster_layer(os.path.join(DATA_DIR, "Kisseman_slope.tif"), "Slope Map", "slope", opacity=0.55)
    add_raster_layer(os.path.join(DATA_DIR, "Kisseman_facc.tif"), "Flow Accumulation", "flow", opacity=0.5)
    add_raster_layer(os.path.join(DATA_DIR, "Kisseman_dem.tif"), "Elevation / DEM", "dem", opacity=0.45)

    # User location indicator: orange dot + 50m transparent buffer + pulsing ring
    folium.Circle(
        location=[c_lat, c_lng],
        radius=50,
        color="#f39c12",
        weight=2,
        fill=True,
        fill_color="#f39c12",
        fill_opacity=0.18,
        tooltip="Your current location"
    ).add_to(m)

    pulse_css = """
    <style>
    @keyframes locatorPulse {
        0% {
            transform: scale(0.8);
            opacity: 1;
        }
        70% {
            transform: scale(2.1);
            opacity: 0.3;
        }
        100% {
            transform: scale(2.4);
            opacity: 0;
        }
    }
    .locator-pulse-ring {
        position: absolute;
        width: 26px;
        height: 26px;
        border-radius: 50%;
        border: 2px solid rgba(243, 156, 18, 0.9);
        background: rgba(243, 156, 18, 0.12);
        animation: locatorPulse 2.2s infinite;
        left: 0;
        top: 0;
    }
    .locator-core {
        position: absolute;
        width: 12px;
        height: 12px;
        left: 7px;
        top: 7px;
        border-radius: 50%;
        background: #f39c12;
        border: 2px solid white;
        box-shadow: 0 0 10px rgba(243, 156, 18, 0.9);
    }
    </style>
    """
    m.get_root().header.add_child(folium.Element(pulse_css))

    pulse_icon_html = """
    <div style="position: relative; width: 26px; height: 26px;">
        <div class="locator-pulse-ring"></div>
        <div class="locator-core"></div>
    </div>
    """

    folium.Marker(
        location=[c_lat, c_lng],
        icon=folium.DivIcon(
            html=pulse_icon_html,
            icon_size=(26, 26),
            icon_anchor=(13, 13),
        ),
        popup="Your current location",
        tooltip="Your current location"
    ).add_to(m)

    color_map = {
        "High": "red",
        "Moderately High": "orange",
        "Moderately Low": "blue",
        "Low": "green"
    }

    point_lookup = {}

    t1 = time.time()
    survey_group = folium.FeatureGroup(name="Survey Points", control=True)
    if survey_points:
        for pt in survey_points:
            lat = pt.get("lat") or pt.get("Latitude")
            lng = pt.get("lng") or pt.get("Longitude")
            if lat is None or lng is None:
                continue
            try:
                lat, lng = float(lat), float(lng)
            except (ValueError, TypeError):
                continue

            risk_lvl = pt.get("Risk_Level", "Low")
            landmark = pt.get("Nearest_Landmark", "Drainage Point")
            marker_color = color_map.get(risk_lvl, "gray")
            key = (round(lat, 6), round(lng, 6))
            point_lookup[key] = pt

            folium.CircleMarker(
                location=[lat, lng],
                radius=7,
                tooltip=f"{landmark} ({risk_lvl})",
                color=marker_color,
                fill=True,
                fill_color=marker_color,
                fill_opacity=0.8
            ).add_to(survey_group)
    survey_group.add_to(m)
    #st.write(f"DEBUG: Markers added in {time.time()-t1:.2f}s")

    folium.LayerControl(
        position="topright",
        collapsed=True,
        title="Layers"
    ).add_to(m)

    # --- DEBUG: this is the line we need to see print or not ---
    #st.write("DEBUG: about to call st_folium...")
    t2 = time.time()
    map_data = st_folium(m, use_container_width=True, height=355, key="interactive_kisseman_map")
    #st.write(f"DEBUG: st_folium returned in {time.time()-t2:.2f}s")

    clicked_obj = map_data.get("last_object_clicked") if map_data else None
    last_clicked = map_data.get("last_clicked") if map_data else None

    click_lat = None
    click_lng = None
    if last_clicked and last_clicked.get("lat") is not None and last_clicked.get("lng") is not None:
        click_lat = float(last_clicked["lat"])
        click_lng = float(last_clicked["lng"])

    if click_lat is not None and click_lng is not None:
        st.markdown("---")
        st.subheader("📍 Spatial Analysis")
        col1, col2 = st.columns(2)

        with col1:
            st.write(f"**Latitude:** `{click_lat:.6f}`")
            st.write(f"**Longitude:** `{click_lng:.6f}`")

            lulc_class = get_lulc_at_point(click_lat, click_lng)
            terrain = get_terrain_at_point(click_lat, click_lng)
            slope_score = terrain.get("Slope_Score")
            slope_value = terrain.get("Slope")
            flow_value = terrain.get("FlowAccumulation")
            dem_value = terrain.get("DEM_Value")

            st.write(f"**Dominant land cover:** `{lulc_class}`")
            st.write(f"**Elevation (DEM):** `{dem_value} m`" if dem_value is not None else "**Elevation (DEM):** `Unavailable`")
            st.write(f"**Slope:** `{slope_value}°`" if slope_value is not None else "**Slope:** `Unavailable`")
            st.write(f"**Flow accumulation:** `{flow_value}`" if flow_value is not None else "**Flow accumulation:** `Unavailable`")

        with col2:
            lulc_factor = 1.0 if lulc_class == "Built-up" else 0.4
            pred = calculate_flood_risk(
                block_score=0.50,
                rainfall_mm=45.0,
                slope_score=0.35 if slope_score is None else float(slope_score),
                lulc_risk=lulc_factor,
                is_daily_rainfall=True
            )
            st.metric(label="Predicted Flood Risk", value=pred["category"], delta=f"Score: {pred['score']}")
            st.info(f"**Status:** {pred['label']}")
            st.caption("This spatial context is computed for the exact location you tapped.")

        clicked_key = (round(click_lat, 6), round(click_lng, 6))
        pt = point_lookup.get(clicked_key)

        if pt is not None:
            st.markdown("---")
            landmark = pt.get("Nearest_Landmark", "Drainage Point")
            gutter = pt.get("Gutter_Type", "Unknown Channel")
            block_score = safe_float(pt.get("BlockScore"), 0.0)
            risk_lvl = pt.get("Risk_Level", "Low")
            photo_id = pt.get("Photo_ID", "")

            st.subheader(f"📍 Gutter Information: {landmark}")
            col3, col4 = st.columns([1, 1])

            with col3:
                photo_path = get_photo_path_by_id(photo_id) if photo_id else ""
                if photo_path and os.path.exists(photo_path):
                    st.image(photo_path, use_container_width=True)
                else:
                    st.info("No photo available for this point.")

            with col4:
                st.write(f"**Risk Level:** {risk_lvl}")
                st.write(f"**Channel Type:** {gutter}")
                st.write(f"**Block Score:** {block_score:.2f}")
                st.write(f"**Exact location:** {landmark}")
        else:
            nearest = find_nearby_survey_points(click_lat, click_lng, survey_points, max_distance_m=2000.0)
            if nearest:
                closest = nearest[0]
                st.markdown("---")
                st.subheader("📍 Nearest Gutter Point")
                st.info(f"The nearest surveyed drainage is close to **{closest.get('Nearest_Landmark', 'Drainage Point')}** and it is **{closest.get('distance_m', 0)}m** away.")

                contact_landmark = closest.get("Nearest_Landmark", "Drainage Point")
                contact_gutter = closest.get("Gutter_Type", "Unknown Channel")
                contact_block = safe_float(closest.get("BlockScore"), 0.0)
                contact_photo = closest.get("Photo_ID", "")
                contact_path = get_photo_path_by_id(contact_photo) if contact_photo else ""

                col3, col4 = st.columns([1, 1])
                with col3:
                    if contact_path and os.path.exists(contact_path):
                        st.image(contact_path, use_container_width=True)
                    else:
                        st.info("No photo available for the nearest gutter point.")
                with col4:
                    st.write(f"**Nearest landmark:** {contact_landmark}")
                    st.write(f"**Channel type:** {contact_gutter}")
                    st.write(f"**Block score:** {contact_block:.2f}")
                    st.write(f"**Distance:** {closest.get('distance_m', 0)} m")
            else:
                st.markdown("---")
                st.info("No nearby gutter data was found within the current search radius.")