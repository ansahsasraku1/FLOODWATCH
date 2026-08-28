import streamlit as st
from services.asset_paths import get_asset_path


def render_splash():
    logo_path = get_asset_path("logo.jpg")

    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if logo_path and logo_path.lower().endswith((".jpg", ".jpeg", ".png")):
            st.image(logo_path, use_container_width=True)

    st.markdown(
        """
        <div style="text-align: center; padding: 0px 0px;">
            <h1 style="color: #00A8E8; font-size: 1rem; margin-bottom: -20px;">
                Built for resilient communities,
            </h1>
            <h1 style="color: #00A000; font-size: 1rem; margin-bottom: 0;">
                For sustainable urban development.
            </h1>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # st.markdown(
    #     """
    #     <div style="
    #         background: rgba(255,255,255,0.05);
    #         padding: 20px;
    #         border-radius: 12px;
    #         border: 1px solid rgba(255,255,255,0.1);
    #         margin: 20px 0;
    #     ">
    #         <p style="
    #             font-size: 1rem;
    #             line-height: 1.6;
    #             justify-content: center;
    #             color: #E2E8F0;
    #         ">
    #             <strong>FLOODWATCH</strong> is currently in test mode.
    #         </p>

    #         <div style="
    #             margin-top: 15px;
    #             display: flex;
    #             gap: 10px;
    #             justify-content: center;
    #             flex-wrap: wrap;
    #         ">
    #             <span style="background: #1E293B; color: #38BDF8; padding: 6px 72px; border-radius: 20px; font-size: 0.85rem; border: 1px solid #334155;">SDG 13: Climate Action</span>
    #             <span style="background: #1E293B; color: #4ADE80; padding: 6px 90px; border-radius: 20px; font-size: 0.85rem; border: 1px solid #334155;">Urban Resilience</span>
    #             <span style="background: #1E293B; color: #F43F5E; padding: 6px 84px; border-radius: 20px; font-size: 0.85rem; border: 1px solid #334155;">Safe Environments</span>
    #         </div>
    #     </div>
    #     """,
    #     unsafe_allow_html=True,
    # )

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("Get Started", use_container_width=True, type="primary"):
            st.session_state.page = "main"
            st.rerun()