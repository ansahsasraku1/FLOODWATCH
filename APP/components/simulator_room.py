"""
Rainfall Simulator Room - Interactive flood risk simulation
Allows users to test different rainfall scenarios and see how gutter points respond
"""

import os
import math
import streamlit as st
import folium
from streamlit_folium import st_folium
from streamlit_geolocation import streamlit_geolocation
from services.data_loader import get_unified_survey_points
from services.risk_engine import calculate_flood_risk
from services.gis_service import get_lulc_at_point, get_terrain_at_point
from components.banners import render_image_banner


def haversine_distance(lat1, lng1, lat2, lng2):
    """Calculate distance in meters between two coordinates."""
    R = 6371000  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lng2 - lng1)
    
    a = math.sin(delta_phi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda/2)**2
    c = 2 * math.atan2(a**0.5, (1-a)**0.5)
    return R * c


def render_simulator_room():
    """Render the interactive rainfall simulator."""
    render_image_banner("flood_map.jpg")
    
    st.markdown("##### Flood Risk Simulator Room")
    st.write("Test different rainfall scenarios and see how nearby gutter points respond to varying conditions.")
    
    # Load survey points
    survey_points = get_unified_survey_points()
    if not survey_points:
        st.error("No survey points available.")
        return
    
    # --- Get User Location ---
    if "simulator_center" not in st.session_state:
        st.session_state.simulator_center = (5.6493, -0.2069)
    center_lat, center_lng = st.session_state.simulator_center
    
    st.markdown("##### 📍 Use my current location")
    location = streamlit_geolocation()
    
    if location and location.get("latitude") is not None and location.get("longitude") is not None:
        if not st.session_state.get("simulator_auto_location_used", False):
            center_lat = float(location["latitude"])
            center_lng = float(location["longitude"])
            st.session_state.simulator_center = (center_lat, center_lng)
            st.session_state.simulator_auto_location_used = True
        st.success(f"Location captured: {location['latitude']:.5f}, {location['longitude']:.5f}")
    else:
        st.info("Allow location access to center the simulator on your position. Or tap anywhere on the map to simulate rainfall at that location.")
    
    # --- Main Rainfall Control (Prominent) ---
    st.markdown("---")
    st.markdown("### 🌧️ Rainfall Input (SIM)")
    
    col_rain1, col_rain2 = st.columns([3, 1])
    with col_rain1:
        rainfall_mm = st.slider(
            "Expected Rainfall (mm)",
            min_value=0,
            max_value=100,
            value=0,
            step=1,
            help="Slide to simulate different rainfall amounts. The map will update in real-time."
        )
    
    with col_rain2:
        st.metric(label="Rainfall", value=f"{rainfall_mm} mm")
    
    # Convert mm to percentage
    rainfall_percentage = (rainfall_mm / 100) * 100 if rainfall_mm > 0 else 0
    
    # --- Sidebar Controls ---
    st.sidebar.markdown("### ⚙️ Display Options")
    show_points = st.sidebar.checkbox("Show Gutter Points (500m radius)", value=True)
    filter_risk = st.sidebar.multiselect(
        "Filter by Risk Level",
        options=["High", "Moderately High", "Moderately Low", "Low"],
        default=["High", "Moderately High", "Moderately Low", "Low"]
    )
    
    # --- Main Map ---
    st.markdown("---")
    st.markdown("#### 🗺️ Interactive Map (Tap anywhere to change location)")
    
    m = folium.Map(location=[center_lat, center_lng], zoom_start=16, tiles="OpenStreetMap")
    
    # Color mapping for risk levels
    color_map = {
        "High": "red",
        "Moderately High": "orange",
        "Moderately Low": "blue",
        "Low": "darkgreen"
    }
    
    # Recalculate risk for each point based on simulated rainfall
    simulated_results = []
    
    if show_points:
        survey_group = folium.FeatureGroup(name="Survey Points (Risk-Based on Rainfall)", control=True)
        
        for pt in survey_points:
            lat = pt.get("lat") or pt.get("Latitude")
            lng = pt.get("lng") or pt.get("Longitude")
            
            if lat is None or lng is None:
                continue
            
            try:
                lat, lng = float(lat), float(lng)
            except (ValueError, TypeError):
                continue
            
            # Calculate distance from user
            distance_m = haversine_distance(center_lat, center_lng, lat, lng)
            
            # Only show points within 500m radius
            if distance_m > 500:
                continue
            
            landmark = pt.get("Nearest_Landmark", "Drainage Point")
            gutter_type = pt.get("Gutter_Type", "Unknown")
            
            # Get point characteristics from CSV (current conditions)
            block_score = float(pt.get("BlockScore", 0.2))
            slope_score = float(pt.get("Slope_Score", 0.2))
            flow_acc_score = float(pt.get("FlowAcc_Score", 0.0))
            capacity_risk = float(pt.get("Capacity_Risk", 0.5))
            lulc_risk = float(pt.get("LULC_Risk", 1.0))
            
            # Calculate risk based on simulated rainfall AND all current conditions
            risk_result = calculate_flood_risk(
                block_score=block_score,
                rainfall_mm=rainfall_mm,
                slope_score=slope_score,
                flow_acc_score=flow_acc_score,
                capacity_risk=capacity_risk,
                lulc_risk=lulc_risk,
                is_daily_rainfall=True
            )
            
            risk_category = risk_result.get("category", "Low")
            risk_score = risk_result.get("score", 0.0)
            
            # Keep the calculated result live as rainfall changes. The default
            # filter includes every risk category in the 500 m radius.
            if risk_category not in filter_risk:
                continue
            
            simulated_results.append({
                "landmark": landmark,
                "lat": lat,
                "lng": lng,
                "risk_category": risk_category,
                "risk_score": risk_score,
                "gutter_type": gutter_type,
                "block_score": block_score,
                "slope_score": slope_score,
                "flow_acc_score": flow_acc_score,
                "capacity_risk": capacity_risk,
                "lulc_risk": lulc_risk,
                "distance_m": distance_m
            })
            
            marker_color = color_map.get(risk_category, "gray")
            
            # Create popup with risk information
            popup_html = f"""
            <div style="font-family: Arial; width: 280px;">
                <h4 style="margin-top: 0; color: #333;">{landmark}</h4>
                <p style="margin: 5px 0;"><b>Type:</b> {gutter_type}</p>
                <p style="margin: 5px 0;"><b>Distance:</b> {distance_m:.0f}m</p>
                <p style="margin: 5px 0;"><b>Risk Category:</b> <span style="color: {color_map.get(risk_category, 'gray')}; font-weight: bold;">{risk_category}</span></p>
                <p style="margin: 5px 0;"><b>Risk Score:</b> {risk_score:.2f}</p>
                <hr style="margin: 8px 0;">
                <p style="margin: 3px 0; font-size: 0.85em;"><b>Current Conditions:</b></p>
                <p style="margin: 3px 0; font-size: 0.85em;">Blockage: {block_score:.2f} | Slope: {slope_score:.2f}</p>
                <p style="margin: 3px 0; font-size: 0.85em;">Flow Acc: {flow_acc_score:.2f} | Capacity: {capacity_risk:.2f}</p>
                <p style="margin: 3px 0; color: #666; font-size: 0.85em;">
                    Simulated rainfall: {rainfall_mm} mm
                </p>
            </div>
            """
            
            folium.CircleMarker(
                location=[lat, lng],
                radius=10,
                popup=folium.Popup(popup_html, max_width=300),
                tooltip=f"{landmark} ({risk_category}) • {distance_m:.0f}m",
                color=marker_color,
                fill=True,
                fill_color=marker_color,
                fill_opacity=0.8,
                weight=2
            ).add_to(survey_group)
        
        survey_group.add_to(m)
    
    # Add user location indicator
    folium.Circle(
        location=[center_lat, center_lng],
        radius=50,
        color="#f39c12",
        weight=2,
        fill=True,
        fill_color="#f39c12",
        fill_opacity=0.18,
        tooltip="Your location / Simulation center"
    ).add_to(m)
    
    folium.Marker(
        location=[center_lat, center_lng],
        popup="Simulation Center",
        tooltip="Your location / Tap map to change",
        icon=folium.Icon(color="orange", icon="info-sign")
    ).add_to(m)
    
    # Add 500m radius circle
    folium.Circle(
        location=[center_lat, center_lng],
        radius=500,
        color="#0099ff",
        weight=1,
        fill=False,
        opacity=0.5,
        tooltip="500m radius",
        name="500m Search Radius"
    ).add_to(m)
    
    folium.LayerControl(
        position="topright",
        collapsed=True,
        title="Layers"
    ).add_to(m)
    
    # Render map and capture clicks
    map_data = st_folium(m, use_container_width=True, height=430, key="simulator_map")
    
    # Handle map clicks - update simulation center
    if map_data and map_data.get("last_clicked"):
        clicked = map_data["last_clicked"]
        if clicked.get("lat") is not None and clicked.get("lng") is not None:
            clicked_center = (round(float(clicked["lat"]), 6), round(float(clicked["lng"]), 6))
            if clicked_center != st.session_state.get("simulator_last_click"):
                st.session_state.simulator_center = clicked_center
                st.session_state.simulator_last_click = clicked_center
                st.rerun()
    
    # --- Results Summary ---
    st.markdown("---")
    st.markdown(f"#### 📊 Simulation Results for {rainfall_mm}mm Rainfall")
    
    if simulated_results:
        col1, col2, col3, col4 = st.columns(4)
        
        high_risk_count = len([r for r in simulated_results if r["risk_category"] == "High"])
        mod_high_count = len([r for r in simulated_results if r["risk_category"] == "Moderately High"])
        mod_count = len([r for r in simulated_results if r["risk_category"] == "Moderately Low"])
        low_risk_count = len([r for r in simulated_results if r["risk_category"] == "Low"])
        
        with col1:
            st.metric("🚨 High Risk", high_risk_count)
        with col2:
            st.metric("⚠️ Moderately High", mod_high_count)
        with col3:
            st.metric("⚡ Moderately Low", mod_count)
        with col4:
            st.metric("✅ Lower Risk", low_risk_count)
        
        st.markdown("---")
        st.markdown("#### 🔍 Detailed Point Analysis")
        
        # Sort by risk score (highest first)
        sorted_results = sorted(simulated_results, key=lambda x: x["risk_score"], reverse=True)
        
        for result in sorted_results:
            color = color_map.get(result["risk_category"], "gray")
            st.markdown(
                f"""
                <div style="background: rgba(255,255,255,0.03); border-left: 4px solid {color}; padding: 12px 16px; border-radius: 6px; margin-bottom: 8px;">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                        <div style="flex: 1;">
                            <strong style="color: #FFFFFF;">{result['landmark']}</strong>
                            <div style="font-size: 0.8rem; color: #94A3B8; margin-top: 4px;">
                                {result['gutter_type']} • {result['distance_m']:.0f}m away
                            </div>
                            <div style="font-size: 0.75rem; color: #64748B; margin-top: 4px;">
                                Block: {result['block_score']:.2f} | Slope: {result['slope_score']:.2f} | Flow: {result['flow_acc_score']:.2f} | Cap: {result['capacity_risk']:.2f}
                            </div>
                        </div>
                        <div style="text-align: right;">
                            <div style="font-size: 1.2rem; font-weight: 700; color: {color};">{result['risk_score']:.2f}</div>
                            <span style="background: rgba({255 if result['risk_category']=='High' else 255},{165 if result['risk_category']=='Moderately High' else 0},{0 if result['risk_category'] in ['High','Moderately High'] else 100}, 0.2); color: {color}; border: 1px solid {color}; padding: 4px 8px; border-radius: 12px; font-size: 0.7rem; font-weight: 700; display: inline-block;">
                                {result['risk_category']}
                            </span>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
    else:
        st.info("No points found within 500m of your location. Try moving closer to a surveyed drainage area or adjusting filters.")
    
    # --- Rainfall Guidance ---
    st.markdown("---")
    st.markdown("#### 💡 Rainfall Simulation Guide")
    
    col_guide1, col_guide2 = st.columns(2)
    
    with col_guide1:
        st.markdown("""
        **Rainfall Levels:**
        - **0-10 mm**: Light rainfall
        - **10-30 mm**: Moderate rainfall
        - **30-60 mm**: Heavy rainfall
        - **60-100 mm**: Extreme rainfall
        """)
    
    with col_guide2:
        st.markdown("""
        **Risk Interpretation:**
        - **High**: Immediate flooding likely
        - **Moderately High**: Flooding possible
        - **Moderately**: Watch conditions
        - **Low**: Minimal flood risk
        
        *Risk is based on simulated rainfall + current drainage conditions*
        """)

