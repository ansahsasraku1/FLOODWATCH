import base64
import os
import streamlit as st
import plotly.express as px
import pandas as pd
from services.audio_guide import generate_twi_audio
from services.cv_inference import get_photo_path_by_id
from services.risk_engine import calculate_flood_risk
from services.asset_paths import get_asset_path



# def render_floating_audio_player(audio_bytes: bytes):
#     """Render a fixed-position audio control for the current risk result."""
#     if not audio_bytes:
#         return

#     b64_audio = base64.b64encode(audio_bytes).decode("utf-8")
#     st.markdown(
#         f"""
#         <div style="position: fixed; right: clamp(12px, 2vw, 28px); bottom: clamp(12px, 2vw, 24px); z-index: 9999; width: min(92vw, 360px); background: rgba(15, 23, 42, 0.95); border: 1px solid rgba(148, 163, 184, 0.35); border-radius: 14px; padding: clamp(10px, 1.4vw, 16px); box-shadow: 0 12px 30px rgba(0,0,0,0.28);">
#             <div style="font-size: clamp(0.8rem, 1.4vw, 0.96rem); color: #E2E8F0; margin-bottom: 8px; font-weight: 700;">🔊 Audio Guide</div>
#             <audio controls autoplay style="width: 100%; height: clamp(32px, 3vw, 42px);">
#                 <source src="data:audio/mp3;base64,{b64_audio}" type="audio/mpeg">
#             </audio>
#         </div>
#         """,
#         unsafe_allow_html=True,
#     )


def render_risk_results(risk_data: dict, rainfall_data: dict, nearest_points: list, user_lat: float = None, user_lng: float = None, on_contribute_click=None):
    """
    Renders the flood risk score, 7-day rainfall forecast,
    the nearest surveyed drainage point, and (optionally) the Twi audio guide.
    Includes the update gutter point form before rainfall chart.
    """
    nearest_points = nearest_points or []
    risk_color_map = {
        "High": {"bg": "#FF4D4D22", "border": "#FF4D4D", "text": "#FF4D4D", "icon": "🚨"},
        "Moderately High": {"bg": "#FFA50022", "border": "#FFA500", "text": "#FFA500", "icon": "⚠️"},
        "Moderately Low": {"bg": "#00A8E822", "border": "#00A8E8", "text": "#00A8E8", "icon": "⚡"},
        "Low": {"bg": "#2EC4B622", "border": "#2EC4B6", "text": "#2EC4B6", "icon": "✅"}
    }

    cat = risk_data.get('category', 'Low')
    score = risk_data.get('score', 0.0)
    style = risk_color_map.get(cat, risk_color_map['Low'])

    top_pt = nearest_points[0] if nearest_points else {}
    landmark = top_pt.get('Nearest_Landmark') or "your area"

    # --- Intro Guide Video ---
    video_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "APP", "assets", "check_risk.mp4"
    )
    # import base64
    # import os
    # import streamlit as st

    # # Locate the root folder of your project dynamically:
    # # 1. Path of this file
    # current_dir = os.path.dirname(os.path.abspath(__file__))

    # # 2. Traverse up to the main project root (adjust parents if needed)
    # # If this file is inside APP/components or APP/pages, navigate to project root:
    # project_root = os.path.abspath(os.path.join(current_dir, "..", "..")) 

    # # 3. Target the file in APP/assets/
    # video_path = os.path.join(project_root, "APP", "assets", "check_risk.mp4")

    # # Alternative: If this current script itself is in the project root:
    # # video_path = os.path.join(current_dir, "APP", "assets", "check_risk.mp4")

    # if os.path.exists(video_path):
    #     with open(video_path, "rb") as video_file:
    #         video_bytes = video_file.read()
        
    #     b64_video = base64.b64encode(video_bytes).decode("utf-8")
        
    #     st.markdown(
    #         f"""
    #         <video autoplay loop muted playsinline
    #             style="width:100%; height:160px; object-fit:cover; border-radius:12px; margin-bottom:16px;">
    #             <source src="data:video/mp4;base64,{b64_video}" type="video/mp4">
    #         </video>
    #         """,
    #         unsafe_allow_html=True,
    #     )
    # else:
    #     # Diagnostic alert to show you the exact path Python tried to open
    #     st.error(f"⚠️ Video not found at: `{video_path}`")
        
    # # Banner video for this page, editable here when needed.
    # video_path = get_asset_path("check_risk.mp4")
    # if os.path.exists(video_path):
    #     with open(video_path, "rb") as video_file:
    #         video_bytes = video_file.read()
    #     b64_video = base64.b64encode(video_bytes).decode("utf-8")
    #     st.markdown(
    #         f"""
    #         <video autoplay loop muted playsinline
    #                style="width:100%; height:160px; object-fit:cover; border-radius:12px; margin-bottom:16px;">
    #             <source src="data:video/mp4;base64,{b64_video}" type="video/mp4">
    #         </video>
    #         """,
    #         unsafe_allow_html=True,
    #     )

    # 1. Primary Risk Banner Card
    st.markdown(
        f"""
        <div style="background: {style['bg']}; border: 2px solid {style['border']}; border-radius: 16px; padding: 24px; text-align: center; margin-bottom: 20px;">
            <div style="font-size: 2.5rem; margin-bottom: 5px;">{style['icon']}</div>
            <h2 style="color: {style['text']}; margin: 0; font-size: 1.8rem; font-weight: 800;">
                {risk_data.get('label', 'Assessment Unavailable')}
            </h2>
            <p style="color: #E2E8F0; font-size: 1rem; margin-top: 8px;">
                Your current location is assessed with a <strong>{cat.lower()}</strong> risk score of
                <span style="font-weight: 700; color: {style['text']};">{score:.2f}</span>.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # --- Audio Guide: always refresh based on the current station/result ---
    st.sidebar.markdown("### 🔊 Accessibility Settings")
    enable_audio = st.sidebar.toggle("Enable Audio Guide", value=False, key="audio_toggle")

    current_audio_key = (
        f"risk:{cat}:{score:.4f}:{landmark}:"
        f"{st.session_state.get('user_lat', 0):.5f}:{st.session_state.get('user_lng', 0):.5f}"
    )

    if enable_audio:
        audio_bytes = st.session_state.get("risk_audio_bytes")
        saved_key = st.session_state.get("risk_audio_key")

        if saved_key != current_audio_key or not audio_bytes:
            with st.spinner("Generating audio guide for this station..."):
                audio_fp = generate_twi_audio(cat, score, landmark)
                audio_bytes = audio_fp.getvalue() if audio_fp else None
            st.session_state["risk_audio_bytes"] = audio_bytes
            st.session_state["risk_audio_key"] = current_audio_key

        render_floating_audio_player(audio_bytes)
    else:
        st.session_state.pop("risk_audio_bytes", None)
        st.session_state.pop("risk_audio_key", None)

    # 2. Nearest Survey Point Linked to Calculation
    if nearest_points:
        dist = top_pt.get('distance_m', 0)
        gutter_type = top_pt.get('Gutter_Type') or top_pt.get('Drain_Type') or "Drainage Channel"
        point_risk_category = calculate_point_risk_category(top_pt, rainfall_data, fallback=cat)
        blockage_level = format_blockage_level(top_pt)

        img_path = get_photo_path_by_id(top_pt.get('Photo_ID', ''))

        col_img, col_info = st.columns([1, 2])

        with col_img:
            if img_path and (os.path.exists(str(img_path)) or str(img_path).startswith('http')):
                st.image(img_path, caption=f"Field Photo: {landmark}", use_container_width=True)
            else:
                st.markdown(
                    """
                    <div style="background: rgba(255,255,255,0.05); border: 1px dashed rgba(255,255,255,0.2); border-radius: 10px; padding: 30px; text-align: center; color: #94A3B8;">
                        📷 <br><span style="font-size: 0.8rem;">No Photo Available</span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

        with col_info:
            p_style = risk_color_map.get(point_risk_category, risk_color_map['Low'])
            st.markdown(
                f"""
                <div style="background: rgba(255,255,255,0.03); border-left: 4px solid {p_style['border']}; padding: 16px; border-radius: 8px;">
                    <h4 style="margin: 0 0 6px 0; color: #FFFFFF;">📍 {landmark}</h4>
                    <p style="margin: 0; color: #94A3B8; font-size: 0.9rem;">
                        <strong>Type:</strong> {gutter_type}<br>
                        <strong>Proximity:</strong> {dist} meters away from your location<br>
                        <strong>Flood Risk:</strong> <span style="color: {p_style['text']}; font-weight: 700;">{point_risk_category}</span><br>
                        <strong>Drain Blockage Level:</strong> <span style="font-weight: 700;">{blockage_level}</span>
                    </p>
                </div>
                """,
                unsafe_allow_html=True
            )

    # --- Update Gutter Point Form (Before Rainfall Chart) ---
    st.markdown("---")
    if nearest_points and len(nearest_points) > 0 and user_lat is not None and user_lng is not None:
        render_update_gutter_point(nearest_points[0], user_lat, user_lng)

    st.markdown("---")
    st.markdown("##### **7-Day Rainfall Forecast**")

    # 3. Rainfall Forecast Display
    dates = rainfall_data.get("dates", []) or []
    daily = rainfall_data.get("daily") or rainfall_data.get("daily_breakdown", []) or []

    if dates and daily:
        total_rainfall = sum(daily)
        
        # Calculate percentage chance of rainfall (max 100mm = 100% chance)
        max_rainfall = max(daily) if daily else 1
        rainfall_percentages = [(v / max(max_rainfall, 1)) * 100 for v in daily]

        st.markdown(
            f"""
            <div style="background: rgba(0,168,232,0.1); border: 1px solid #00A8E8; border-radius: 10px; padding: 12px; text-align: center; margin-bottom: 15px;">
                <div style="font-size: 0.8rem; color: #94A3B8;">Total Expected Rainfall</div>
                <div style="font-size: 1.5rem; font-weight: 800; color: #00A8E8;">{total_rainfall:.1f} mm</div>
                <div style="font-size: 0.75rem; color: #CBD5E1;">Next 7 days</div>
            </div>
            """,
            unsafe_allow_html=True
        )

        df_rain = pd.DataFrame({
            "Date": dates,
            "Rainfall Chance (%)": rainfall_percentages,
            "Rainfall (mm)": daily,
            "Label": [f"{p:.0f}%" for p in rainfall_percentages]
        })

        fig = px.bar(df_rain, x="Date", y="Rainfall Chance (%)", text="Label", title=None)
        fig.update_traces(
            marker_color="#00A8E8",
            textposition="outside",
            textfont=dict(color="#E2E8F0", size=12, family="sans-serif"),
            hovertemplate="<b>Date:</b> %{x}<br><b>Rainfall Chance:</b> %{y:.1f}%<extra></extra>"
        )
        fig.update_layout(
            height=280,
            margin=dict(l=10, r=10, t=25, b=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(showgrid=False, tickfont=dict(color="#94A3B8", size=11), title=None),
            yaxis=dict(
                showgrid=True,
                gridcolor="rgba(255, 255, 255, 0.1)",
                tickfont=dict(color="#94A3B8", size=11),
                title=dict(text="Rainfall Chance (%)", font=dict(color="#94A3B8", size=11))
            )
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    else:
        st.info("7-day rainfall forecast is currently unavailable.")

    # 4. Nearby Drainage Points List
    st.markdown("##### **Other Nearby Drainage Points (1km Radius)**")

    if not nearest_points:
        st.info("No surveyed drainage points found within 200m of your position.")
        st.markdown(
            """
            <div style="background: rgba(0, 168, 232, 0.1); border: 1px dashed #00A8E8; padding: 15px; border-radius: 10px; text-align: center; margin-top: 10px;">
                <p style="margin: 0 0 10px 0; color: #E2E8F0;">Help FloodWatch update your area's data.</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        if st.button("📍 Contribute a Drainage Point", type="primary", use_container_width=True):
            if on_contribute_click:
                on_contribute_click()
    else:
        closest_distance = nearest_points[0].get('distance_m', 0)

        for pt in nearest_points:
            pt_dist = pt.get('distance_m', 0)
            pt_landmark = pt.get('Nearest_Landmark') or pt.get('Landmark') or pt.get('Name') or "Drainage Location"
            point_risk_category = calculate_point_risk_category(pt, rainfall_data)
            blockage_level = format_blockage_level(pt)
            pt_gutter = pt.get('Gutter_Type', 'Drain')

            p_style = risk_color_map.get(point_risk_category, risk_color_map['Low'])

            st.markdown(
                f"""
                <div style="background: rgba(255,255,255,0.03); border-left: 4px solid {p_style['border']}; padding: 12px 16px; border-radius: 6px; margin-bottom: 8px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <strong style="color: #FFFFFF;">{pt_landmark}</strong>
                            <div style="font-size: 0.8rem; color: #94A3B8;">{pt_gutter} • {pt_dist} m away</div>
                            <div style="font-size: 0.8rem; color: #CBD5E1; margin-top: 4px;">Drain Blockage: {blockage_level}</div>
                        </div>
                        <span style="background: {p_style['bg']}; color: {p_style['text']}; border: 1px solid {p_style['border']}; padding: 4px 10px; border-radius: 12px; font-size: 0.75rem; font-weight: 700;">
                            {point_risk_category}
                        </span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

        if closest_distance >= 50:
            st.markdown("<br>", unsafe_allow_html=True)
            st.warning("Nearest surveyed point is over 50 meters away.")
            if st.button("📍 Contribute a Drainage Point Nearby", type="primary", use_container_width=True):
                if on_contribute_click:
                    on_contribute_click()


def calculate_point_risk_category(point: dict, rainfall_data: dict, fallback: str = "Low") -> str:
    """Calculate a point's current category using the central risk engine."""
    try:
        result = calculate_flood_risk(
            block_score=float(point.get("BlockScore", 0.2)),
            rainfall_mm=float(rainfall_data.get("total_7day", 0.0)),
            slope_score=float(point.get("Slope_Score", 0.2)),
            flow_acc_score=float(point.get("FlowAcc_Score", 0.0)),
            capacity_risk=float(point.get("Capacity_Risk", 0.5)),
            lulc_risk=float(point.get("LULC_Risk", 1.0)),
            is_daily_rainfall=False,
        )
        return result.get("category", fallback)
    except (TypeError, ValueError):
        return fallback


def format_blockage_level(point: dict) -> str:
    """Format the surveyed drain blockage score without confusing it with flood risk."""
    try:
        blockage_score = min(max(float(point.get("BlockScore", 0.0)), 0.0), 1.0)
    except (TypeError, ValueError):
        blockage_score = 0.0

    blockage_percent = blockage_score * 100
    if blockage_score <= 0.25:
        condition = "Clear / Low"
    elif blockage_score <= 0.50:
        condition = "Minor"
    elif blockage_score <= 0.75:
        condition = "Moderate"
    else:
        condition = "Severe"
    return f"{condition} ({blockage_percent:.0f}%)"


def render_update_gutter_point(nearest_point: dict, user_lat: float, user_lng: float):
    """
    Render the form to update a gutter point with new photo and blockage level.
    Validates that user is within 20m of the point before allowing submission.
    """
    import io
    import math
    import wave
    from datetime import datetime
    import csv
    from services.cv_inference import analyze_drain_image
    
    if not nearest_point:
        st.warning("No gutter point selected for update.")
        return
    
    pt_lat = float(nearest_point.get("lat") or nearest_point.get("Latitude", 0))
    pt_lng = float(nearest_point.get("lng") or nearest_point.get("Longitude", 0))
    
    # Calculate distance using Haversine formula
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
    
    distance_m = haversine_distance(user_lat, user_lng, pt_lat, pt_lng)
    
    st.markdown("---")
    st.markdown("##### 🔄 Update Gutter Point Information")
    
    landmark = nearest_point.get("Nearest_Landmark", "Drainage Point")
    st.info(f"📍 Updating: **{landmark}** (Distance: {distance_m:.1f}m)")
    
    if distance_m > 20:
        st.error(f"⚠️ You must be within 20 meters of the gutter point to submit an update. You are currently {distance_m:.1f}m away.")
        st.stop()

    success_notice = st.session_state.pop("update_success_notice", None)
    if success_notice:
        st.success("✅ Photo submitted successfully and is awaiting admin review.")
        st.info(f"CV confidence: {success_notice['confidence']:.1%} | Status: Pending Review")

        sample_rate = 44100
        duration = 0.18
        frequency = 880
        samples = b"".join(
            int(12000 * math.sin(2 * math.pi * frequency * index / sample_rate)).to_bytes(
                2, "little", signed=True
            )
            for index in range(int(sample_rate * duration))
        )
        beep = io.BytesIO()
        with wave.open(beep, "wb") as audio:
            audio.setnchannels(1)
            audio.setsampwidth(2)
            audio.setframerate(sample_rate)
            audio.writeframes(samples)
        st.audio(beep.getvalue(), format="audio/wav", autoplay=True)

    form_key = st.session_state.get("update_form_reset", 0)
    
    # Update form in expander (collapsed by default, expands downward when clicked)
    with st.expander("📝 Click to Update Gutter Point", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            # Photo upload
            st.markdown("**📷 Photo of Drainage Point**")
            uploaded_file = st.file_uploader(
                "Upload a new photo of the gutter point",
                type=["jpg", "jpeg", "png"],
                key=f"update_gutter_photo_{form_key}"
            )
            
            if uploaded_file:
                st.image(uploaded_file, caption="New photo preview", use_container_width=True)
        
        with col2:
            # Blockage level update
            st.markdown("**🚫 Blockage Level**")
            blockage_level = st.selectbox(
                "Select blockage level",
                options=[0, 1, 2, 3],
                index=min(int(float(nearest_point.get("BlockScore", 0.5)) * 3), 3),
                format_func=lambda x: {
                    0: "Clear (0%)",
                    1: "Minor (25-50%)",
                    2: "Moderate (50-75%)",
                    3: "Severe (75-100%)"
                }[x],
                key=f"update_blockage_{form_key}"
            )
            
            blockage_percentage = (blockage_level / 3) * 100
            st.caption(f"Blockage: {blockage_percentage:.0f}%")
        
        st.markdown("---")
        
        # Landmark and gutter type
        col3, col4 = st.columns(2)
        
        with col3:
            landmark_name = st.text_input(
                "Nearest Landmark Name",
                value=nearest_point.get("Nearest_Landmark", ""),
                help="Update the landmark name near this gutter point",
                key=f"update_landmark_{form_key}"
            )
        
        with col4:
            gutter_type = st.selectbox(
                "Gutter Type",
                options=["Open concrete drain", "Earthen / soil drain", "Covered / underground drain"],
                index=0 if "Open concrete" in nearest_point.get("Gutter_Type", "") else (1 if "Earthen" in nearest_point.get("Gutter_Type", "") else 2),
                key=f"update_gutter_type_{form_key}",
                help="Select the type of drainage channel"
            )
        
        st.markdown("---")
        
        # Contact information (optional but advisable)
        st.markdown("**📱 Your Contact Information (Optional but Advisable)**")
        
        col5, col6 = st.columns(2)
        
        with col5:
            phone_number = st.text_input(
                "Phone Number",
                placeholder="+233XXXXXXXXX",
                help="Your phone number for follow-up",
                key=f"update_phone_{form_key}"
            )
        
        with col6:
            submitter_name = st.text_input(
                "Your Name",
                placeholder="Enter your name",
                help="Your name for identification",
                key=f"update_name_{form_key}"
            )
        
        # Additional comments
        st.markdown("**💬 Additional Comments**")
        comments = st.text_area(
            "Describe any issues or changes (optional)",
            placeholder="e.g., New blockage found, drain repaired, etc.",
            height=80,
            key=f"update_comments_{form_key}"
        )
        
        st.markdown("---")
        
        # Submission
        if st.button("✅ Submit Update", type="primary", use_container_width=True):
            if uploaded_file is None:
                st.error("📷 Please upload a photo of the gutter point.")
                st.stop()
            
            # Run CV verification on uploaded photo
            with st.spinner("🔍 Running Computer Vision verification..."):
                cv_result = analyze_drain_image(uploaded_file)
            
            # IMPORTANT: Check is_drain flag (model confidence) - not just success
            # If CV model is not confident it's a drain, reject immediately
            if not cv_result.get("is_drain", False):
                st.error("❌ Photo Rejected: Image does not appear to be drainage infrastructure")
                st.warning(f"⚠️ {cv_result.get('error', 'Please upload a photo of an actual drain/gutter.')}")
                st.info("✅ Please try again with a clear photo of the drainage point.")
                st.stop()
            
            # If CV confidence is low (< 0.7), reject for low confidence
            if cv_result.get("confidence", 0) < 0.7:
                st.error(f"❌ Photo Rejected: Low confidence ({cv_result.get('confidence', 0):.1%})")
                st.warning("The image quality is unclear. Please upload a clearer photo of the drainage point.")
                st.info("✅ Please try again with better lighting or angle.")
                st.stop()
            
            # Save photo file to uploads directory
            photo_filename = f"update_{int(datetime.now().timestamp())}_{uploaded_file.name}"
            photo_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                "APP", "uploads", photo_filename
            )
            
            try:
                os.makedirs(os.path.dirname(photo_path), exist_ok=True)
                with open(photo_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
            except Exception as e:
                st.error(f"⚠️ Error saving photo: {str(e)}")
                st.stop()
            
            # Use staging_service to save to correct format for admin dashboard
            from services.staging_service import save_pending_submission
            
            success = save_pending_submission(
                photo_filename=photo_filename,
                lat=user_lat,
                lng=user_lng,
                ai_suggested=cv_result.get("predicted_condition", "Unknown"),
                choke_code=cv_result.get("choke_code", 0),
                drain_type=gutter_type,
                lulc_class="Unknown",
                landmark=landmark_name or nearest_point.get("Nearest_Landmark", ""),
                source_survey_id=str(nearest_point.get("Survey_ID", "")),
                block_score=blockage_level / 3.0
            )
            
            if success:
                st.session_state.update_success_notice = {
                    "confidence": cv_result.get("confidence", 0)
                }
                st.session_state.update_form_reset = form_key + 1
                st.balloons()
                st.rerun()
            else:
                st.error("⚠️ Error saving submission. Please try again.")