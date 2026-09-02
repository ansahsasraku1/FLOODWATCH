import os
import re
import streamlit as st
from services.cv_inference import get_photo_path_by_id
from services.risk_engine import calculate_flood_risk
from components.banners import render_image_banner

def clean_text_encoding(text: str) -> str:
    """Strips broken UTF-8 encoding artifacts and en-dashes from CSV descriptions."""
    if not text or str(text).lower() == "nan":
        return "No visual notes available"
    cleaned = re.sub(r'[\x00-\x1F\x7F-\x9F]', '', str(text))
    cleaned = cleaned.replace("–", "-").replace("—", "-")
    return cleaned.strip()


def get_risk_bucket_for_score(score_value) -> str:
    """Map a numeric risk score to the requested gallery categories."""
    try:
        score = float(score_value)
    except (TypeError, ValueError):
        return "Low"

    # risk_engine returns a 0-1 score in the app, but the gallery uses the requested 0-10-style bucket ranges.
    if score <= 1.0:
        score = score * 10.0

    if score < 2.5:
        return "Low"
    if score < 5:
        return "Moderately Low"
    if score < 7.5:
        return "Moderately High"
    return "High"


def get_point_risk_bucket(point: dict) -> str:
    """Calculate the risk bucket using the same risk-engine logic as the live app."""
    try:
        block_score = float(point.get("BlockScore", 0.0))
        rainfall_score = float(point.get("Rainfall_Score", 0.3))
        slope_score = float(point.get("Slope_Score", 0.3))
        flow_acc_score = float(point.get("FlowAcc_Score", 0.0))
        capacity_risk = float(point.get("Capacity_Risk", 0.5))
        lulc_risk = float(point.get("LULC_Risk", 1.0))

        risk_result = calculate_flood_risk(
            block_score=block_score,
            rainfall_mm=rainfall_score * 200.0,
            slope_score=slope_score,
            flow_acc_score=flow_acc_score,
            capacity_risk=capacity_risk,
            lulc_risk=lulc_risk,
            is_daily_rainfall=False,
        )
        return get_risk_bucket_for_score(risk_result.get("score", 0.0))
    except Exception:
        score_value = point.get("Risk_Score", point.get("RiskScore", point.get("score", 0.0)))
        return get_risk_bucket_for_score(score_value)


def render_community_gallery(survey_points: list[dict]):
    """Renders a grid gallery of survey photos with CV blockage stats."""
    #st.markdown("### Community Drainage Gallery")
    #st.write("Browse bh field photos and AI-assisted blockage diagnostics captured across Kisseman.")

    render_image_banner("communitygallery.jpg")

    # ... rest of the file unchanged from here

    # Filter records that have valid Photo_IDs
    records_with_photos = [
        pt for pt in survey_points
        if pt.get("Photo_ID") and str(pt.get("Photo_ID")).strip() != "" and str(pt.get("Photo_ID")).lower() != "nan"
    ]

    if not records_with_photos:
        st.info("No survey photos available in the dataset.")
        return

    # Filter options
    filter_level = st.selectbox(
        "Filter by Risk Level",
        ["All Levels", "High", "Moderately High", "Moderately Low", "Low"]
    )

    if filter_level != "All Levels":
        records_with_photos = [pt for pt in records_with_photos if get_point_risk_bucket(pt) == filter_level]

    st.markdown(f"**Showing {len(records_with_photos)} surveyed locations**")
    st.markdown("---")

    # Render grid (3 columns)
    cols_per_row = 3
    for i in range(0, len(records_with_photos), cols_per_row):
        cols = st.columns(cols_per_row)
        for idx, pt in enumerate(records_with_photos[i:i + cols_per_row]):
            with cols[idx]:
                photo_id = pt.get("Photo_ID")
                img_path = get_photo_path_by_id(photo_id)
                landmark = pt.get("Nearest_Landmark", "Unknown Landmark")
                risk_lvl = get_point_risk_bucket(pt)
                block_score = pt.get("BlockScore", 0.0)
                
                # Sanitize text string
                choke_desc = clean_text_encoding(pt.get("Choke_Description", ""))

                # Render Image
                if img_path and os.path.exists(img_path):
                    st.image(img_path, use_container_width=True)
                else:
                    st.warning(f"📷 `{photo_id}` not found")

                # Info Card
                st.markdown(
                    f"""
                    <div style="background: rgba(255,255,255,0.04); padding: 12px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.1); margin-bottom: 20px;">
                        <strong style="color: #00A8E8; font-size: 1rem;">{landmark}</strong><br>
                        <hr style="margin: 8px 0; border-color: rgba(255,255,255,0.1);">
                        <div style="font-size: 0.85rem;">
                            <strong>Risk Level:</strong> {risk_lvl}<br>
                            <strong>Blockage Score:</strong> {float(block_score):.2f}<br>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
#<span style="font-size: 0.85rem; color: #94A3B8;">Photo ID: {photo_id}</span>
#<span <strong>Choke Notes:</strong> {choke_desc}</span>