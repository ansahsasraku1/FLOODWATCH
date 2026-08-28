import os
import json
import streamlit as st

UPLOADS_DIR = os.path.join(
    os.path.dirname(__file__), "..", "uploads"
)

def get_pending_submissions() -> list[dict]:
    """Retrieves all JSON submissions currently tagged as PENDING."""
    if not os.path.exists(UPLOADS_DIR):
        return []

    submissions = []
    for file in os.listdir(UPLOADS_DIR):
        if file.endswith(".json"):
            file_path = os.path.join(UPLOADS_DIR, file)
            with open(file_path, "r") as f:
                data = json.load(f)
                if data.get("status") == "PENDING":
                    data["_json_path"] = file_path
                    submissions.append(data)
    return submissions

def render_admin_panel():
    """
    Renders the administrator queue for reviewing and verifying citizen contributions.
    """
    st.markdown("### 🛠️ Administrator Verification Hub")
    
    pending_list = get_pending_submissions()
    st.metric("Pending Citizen Submissions", len(pending_list))

    if not pending_list:
        st.info("No pending submissions require review at this time.")
        return

    st.markdown("---")

    for sub in pending_list:
        sub_id = sub["submission_id"]
        json_path = sub["_json_path"]
        img_path = os.path.join(UPLOADS_DIR, sub.get("image_filename", ""))

        with st.expander(f"📌 Submission {sub_id} — {sub.get('nearest_landmark', 'Unknown')}"):
            col1, col2 = st.columns([1, 1])
            
            with col1:
                if os.path.exists(img_path):
                    st.image(img_path, caption=f"Submitted Image ({sub_id})", use_column_width=True)
                else:
                    st.warning("Photograph unavailable.")

            with col2:
                st.markdown(
                    f"""
                    <strong>Timestamp:</strong> {sub.get('timestamp')}<br>
                    <strong>Coordinates:</strong> {sub.get('latitude'):.5f}, {sub.get('longitude'):.5f}<br>
                    <strong>Landmark:</strong> {sub.get('nearest_landmark')}<br>
                    <strong>Size Category:</strong> {sub.get('drain_size')}<br>
                    <strong>Citizen Verification:</strong> <span style="color:#2EC4B6;">{sub.get('citizen_verification')}</span>
                    """,
                    unsafe_allow_html=True
                )
                
                cv = sub.get("cv_assessment", {})
                st.markdown(
                    f"""
                    <div style="background: rgba(255,255,255,0.05); padding: 10px; border-radius: 6px; margin-top: 10px; border: 1px solid rgba(255,255,255,0.1);">
                        <strong style="color:#00A8E8;">Computer Vision Inference:</strong><br>
                        Blockage: {cv.get('blockage_category', 'N/A')}<br>
                        Confidence: {int(cv.get('confidence', 0) * 100)}%
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            st.markdown("<br>", unsafe_allow_html=True)
            btn_col1, btn_col2 = st.columns(2)
            
            with btn_col1:
                if st.button("✅ APPROVE (Promote to Verified)", key=f"app_{sub_id}", type="primary", use_container_width=True):
                    # Update status to APPROVED
                    sub["status"] = "APPROVED"
                    del sub["_json_path"]
                    with open(json_path, "w") as f:
                        json.dump(sub, f, indent=2)
                    st.success(f"Submission {sub_id} approved!")
                    st.rerun()

            with btn_col2:
                if st.button("❌ REJECT", key=f"rej_{sub_id}", use_container_width=True):
                    # Update status to REJECTED
                    sub["status"] = "REJECTED"
                    del sub["_json_path"]
                    with open(json_path, "w") as f:
                        json.dump(sub, f, indent=2)
                    st.error(f"Submission {sub_id} rejected.")
                    st.rerun()