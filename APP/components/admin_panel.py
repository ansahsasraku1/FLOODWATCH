import csv
import os
from pathlib import Path

import streamlit as st

from services.data_loader import get_unified_survey_points
from services.admin_auth import ADMIN_USERS_CSV, authenticate
from services.staging_service import (
    HEADERS,
    STAGING_CSV,
    UPLOADS_DIR,
    approve_submission,
    migrate_pending_submissions,
    reject_submission,
)


def get_pending_submissions() -> list[dict]:
    """Read pending camera submissions from the CSV staging queue."""
    rows = migrate_pending_submissions()
    return [row for row in rows if row.get("Status", "").lower() == "pending approval"]


def _save_remaining_submissions(submissions: list[dict]) -> None:
    with open(STAGING_CSV, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=HEADERS)
        writer.writeheader()
        writer.writerows(submissions)


def _display_number(value, decimals=5):
    try:
        return f"{float(value):.{decimals}f}"
    except (TypeError, ValueError):
        return "N/A"


def render_admin_panel():
    """Render the administrator queue for reviewing citizen contributions."""
    if not st.session_state.get("admin_authenticated", False):
        st.markdown("### Licensed Administrator Sign In")
        if not os.path.exists(ADMIN_USERS_CSV):
            st.error("Administrator account file is missing.")
            return
        with st.form("admin_login"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Sign in", type="primary")
        if submitted:
            if authenticate(username, password):
                st.session_state.admin_authenticated = True
                st.rerun()
            st.error("Invalid administrator credentials.")
        return

    st.markdown("### 🛠️ Administrator Verification Hub")
    if st.button("Sign out", key="admin_sign_out"):
        st.session_state.admin_authenticated = False
        st.rerun()
    pending_list = get_pending_submissions()
    st.metric("Pending Citizen Submissions", len(pending_list))

    if not pending_list:
        st.info("No pending submissions require review at this time.")
        return

    st.markdown("---")
    for submission in pending_list:
        submission_id = submission.get("Survey_ID", "Unknown")
        photo_name = Path(submission.get("Photo_ID", "")).name
        image_path = os.path.join(UPLOADS_DIR, photo_name)
        landmark = submission.get("Landmark_Notes") or "Unknown landmark"

        with st.expander(f"📌 Submission {submission_id} — {landmark}"):
            col_image, col_details = st.columns([1, 1])
            with col_image:
                if os.path.exists(image_path):
                    st.image(image_path, caption=f"Submitted Image ({submission_id})", use_container_width=True)
                else:
                    st.warning("Photograph unavailable.")

            with col_details:
                st.markdown(
                    f"**Timestamp:** {submission.get('Timestamp', 'N/A')}  \n"
                    f"**Coordinates:** {_display_number(submission.get('Latitude'))}, "
                    f"{_display_number(submission.get('Longitude'))}  \n"
                    f"**Landmark:** {landmark}  \n"
                    f"**Drain type:** {submission.get('Drain_Type', 'N/A')}  \n"
                    f"**AI condition:** {submission.get('AI_Suggested_Blockage', 'N/A')}  \n"
                    f"**Choke code:** {submission.get('Choke_Code', 'N/A')}  \n"
                    f"**LULC:** {submission.get('LULC_Class', 'NULL')}  \n"
                    f"**DEM:** {submission.get('DEM_Value', 'N/A')}  \n"
                    f"**Slope:** {submission.get('Slope', 'N/A')}  \n"
                    f"**Flow accumulation:** {submission.get('FlowAccumulation', 'N/A')}  \n"
                    f"**Slope score:** {submission.get('Slope_Score', 'N/A')}  \n"
                    f"**Flow score:** {submission.get('FlowAcc_Score', 'N/A')}"
                )

            approve_col, reject_col = st.columns(2)
            with approve_col:
                if st.button("✅ Approve and publish", key=f"approve_{submission_id}", type="primary", use_container_width=True):
                    try:
                        approve_submission(submission)
                        remaining = [
                            item for item in pending_list
                            if item.get("Survey_ID") != submission_id
                        ]
                        _save_remaining_submissions(remaining)
                        get_unified_survey_points.clear()
                        st.success("Submission approved, photo published, and survey data updated.")
                        st.rerun()
                    except Exception as error:
                        st.error(f"Approval failed: {error}")

            with reject_col:
                if st.button("❌ Reject", key=f"reject_{submission_id}", use_container_width=True):
                    reject_submission(submission)
                    remaining = [
                        item for item in pending_list
                        if item.get("Survey_ID") != submission_id
                    ]
                    _save_remaining_submissions(remaining)
                    st.success("Submission rejected and removed from the queue.")
                    st.rerun()
