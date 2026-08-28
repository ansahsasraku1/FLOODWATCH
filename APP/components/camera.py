import os
import streamlit as st
from datetime import datetime
from streamlit_geolocation import streamlit_geolocation
from services.cv_inference import analyze_drain_image
from services.gis_service import get_lulc_at_point
from services.staging_service import save_pending_submission
from components.banners import render_image_banner
def render_camera_workflow(user_lat=None, user_lng=None):
    #st.title("📷 Capture & Submit Field Report")
    #st.write("Upload a drainage photo, verify observations, and record field data.")
    render_image_banner("report.jpg")
    


    # --- Intro Guide Video ---
    video_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "APP", "assets", "intro_guide.mp4"
    )
    if os.path.exists(video_path):
        st.video(video_path)
    else:
        st.info("📹 Intro guide video not found.")

    st.markdown("---")

    # --- Live Geolocation Capture ---
    st.subheader("1. Location Capture")

    fallback_lat = user_lat if user_lat is not None else st.session_state.get("user_lat", 5.65231)
    fallback_lng = user_lng if user_lng is not None else st.session_state.get("user_lng", -0.18742)

    location = streamlit_geolocation()

    if location and location.get("latitude") is not None and location.get("longitude") is not None:
        fallback_lat = location["latitude"]
        fallback_lng = location["longitude"]
        st.success(f"Location captured: {fallback_lat:.6f}, {fallback_lng:.6f}")

    col1, col2 = st.columns(2)
    with col1:
        input_lat = st.number_input("Latitude", value=float(fallback_lat), format="%.6f")
    with col2:
        input_lng = st.number_input("Longitude", value=float(fallback_lng), format="%.6f")

    st.markdown("---")
    st.subheader("2. Photo & AI Verification")

    uploaded_file = st.file_uploader("Capture or Upload Field Photo", type=["jpg", "jpeg", "png"])

    if uploaded_file is not None:
        ai_result = analyze_drain_image(uploaded_file)

        if not ai_result["is_drain"]:
            st.error(ai_result["error"])
        else:
            st.success("✅ Gutter structure detected! Please verify details below.")

            with st.form("submission_form"):
                st.subheader("Field Data Form")

                ai_pred_text = ai_result["predicted_condition"]
                st.info(f"🤖 **AI Suggested Condition:** {ai_pred_text} (Confidence: {ai_result['confidence']*100:.1f}%)")

                score_options = [
                    ("Clear / Low Blockage (0–25%)", 0.25),
                    ("Minor Blockage (25–50%)", 0.50),
                    ("Partially Blocked (50–75%)", 0.75),
                    ("Severely Blocked (75–100%)", 1.00)
                ]

                labels_only = [item[0] for item in score_options]
                default_idx = labels_only.index(ai_pred_text) if ai_pred_text in labels_only else 1

                selected_label = st.selectbox(
                    "Verified Blockage Level (Overridden by User)",
                    options=labels_only,
                    index=default_idx
                )

                drain_type = st.selectbox(
                    "Drainage Structure Type",
                    [
                        "Roadside Concrete Drain",
                        "Medium Primary Collector Drain",
                        "Large Main Outfall Channel",
                        "Small Soil / Earthen Drain"
                    ]
                )

                landmark_notes = st.text_input("Landmark / Location Notes", placeholder="e.g. Near Assemblies of God Church")

                submit_btn = st.form_submit_button("Submit Field Report")

                if submit_btn:
                    verified_score = next(score for label, score in score_options if label == selected_label)
                    choke_code = int(verified_score * 4)

                    lulc_class = get_lulc_at_point(input_lat, input_lng)

                    photo_name = f"report_{int(datetime.now().timestamp())}.jpg"
                    uploads_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads")
                    os.makedirs(uploads_dir, exist_ok=True)

                    photo_path = os.path.join(uploads_dir, photo_name)
                    with open(photo_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())

                    success = save_pending_submission(
                        photo_filename=photo_name,
                        lat=input_lat,
                        lng=input_lng,
                        ai_suggested=ai_pred_text,
                        choke_code=choke_code,
                        drain_type=drain_type,
                        lulc_class=lulc_class,
                        landmark=landmark_notes
                    )

                    if success:
                        st.success(f"🎉 Field report saved! Verified Score recorded: {verified_score} | LULC Class: '{lulc_class}'")