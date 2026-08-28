import os
import time
import streamlit as st
import folium
from streamlit_folium import st_folium
from services.cv_inference import get_photo_path_by_id
from services.gis_service import get_lulc_at_point
from services.risk_engine import calculate_flood_risk
from components.banners import render_image_banner


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

    color_map = {
        "High": "red",
        "Moderately High": "orange",
        "Moderately Low": "blue",
        "Low": "green"
    }

    point_lookup = {}

    t1 = time.time()
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
            ).add_to(m)
    #st.write(f"DEBUG: Markers added in {time.time()-t1:.2f}s")

    # --- DEBUG: this is the line we need to see print or not ---
    #st.write("DEBUG: about to call st_folium...")
    t2 = time.time()
    map_data = st_folium(m, use_container_width=True, height=520, key="interactive_kisseman_map")
    #st.write(f"DEBUG: st_folium returned in {time.time()-t2:.2f}s")

    clicked_obj = map_data.get("last_object_clicked") if map_data else None
    if clicked_obj:
        key = (round(clicked_obj["lat"], 6), round(clicked_obj["lng"], 6))
        pt = point_lookup.get(key)

        if pt:
            st.markdown("---")
            landmark = pt.get("Nearest_Landmark", "Drainage Point")
            gutter = pt.get("Gutter_Type", "Unknown Channel")
            block_score = safe_float(pt.get("BlockScore"), 0.0)
            risk_lvl = pt.get("Risk_Level", "Low")
            photo_id = pt.get("Photo_ID", "")

            st.subheader(f"📍 {landmark}")
            col1, col2 = st.columns([1, 1])

            with col1:
                photo_path = get_photo_path_by_id(photo_id) if photo_id else ""
                if photo_path and os.path.exists(photo_path):
                    st.image(photo_path, use_container_width=True)
                else:
                    st.info("No photo available for this point.")

            with col2:
                st.write(f"**Risk Level:** {risk_lvl}")
                st.write(f"**Channel Type:** {gutter}")
                st.write(f"**Block Score:** {block_score:.2f}")

    elif map_data and map_data.get("last_clicked"):
        last_clicked = map_data["last_clicked"]
        click_lat = last_clicked.get("lat")
        click_lng = last_clicked.get("lng")

        if click_lat is not None and click_lng is not None:
            st.markdown("---")
            st.subheader("📍 On-Demand Location Risk Prediction")

            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Latitude:** `{click_lat:.6f}`")
                st.write(f"**Longitude:** `{click_lng:.6f}`")
                lulc_class = get_lulc_at_point(click_lat, click_lng)
                st.write(f"**Sampled LULC:** `{lulc_class}`")

            with col2:
                lulc_factor = 1.0 if lulc_class == "Built-up" else 0.4
                pred = calculate_flood_risk(
                    block_score=0.50,
                    rainfall_mm=45.0,
                    slope_score=0.35,
                    lulc_risk=lulc_factor,
                    is_daily_rainfall=True
                )
                st.metric(label="Predicted Flood Risk", value=pred["category"], delta=f"Score: {pred['score']}")
                st.info(f"**Status:** {pred['label']}")