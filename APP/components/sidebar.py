import streamlit as st
from config import APP_TITLE, LOCATION_NAME, DEVELOPER_PROFILE

def render_sidebar() -> str:
    """
    Renders the FloodWatch navigation sidebar and returns the selected route.
    """
    with st.sidebar:
        # Hydrological Header Block
        st.markdown(
            f"""
            <div style="text-align: center; padding: 10px 0 20px 0; border-bottom: 1px solid rgba(255,255,255,0.1);">
                <h1 style="color: #00A8E8; font-size: 1.8rem; margin: 0; font-weight: 800;">FLOODWATCH</h1>
                <p style="color: #94A3B8; font-size: 1rem; margin-top: 4px;">{LOCATION_NAME}</p>
            </div>
            """,
            unsafe_allow_html=True
        )
#🌊 
        st.markdown("<br>", unsafe_allow_html=True)
        #st.markdown("---")

        # Persistent Audio Advisory Player for the latest result only
        latest_audio_key = st.session_state.get("risk_audio_key")
        latest_audio_bytes = st.session_state.get("risk_audio_bytes")
        if latest_audio_key and latest_audio_bytes:
            st.markdown("#### 🔊 Risk Advisory Audio")
            st.audio(latest_audio_bytes, format="audio/mp3")
            st.markdown("---")

        # Navigation Options
        nav_options = {
            "Check My Risk": "🌧️ Check My Flood Risk",
            "Interactive Map": "🗺️ Flood Map",
            #"Flood History": "📜 Flood History",
            "Community Gallery": "🖼️ Community Gallery",
            "User Guide": "📖 User Guide",
            "Chatbot": "-🤖- FloodWatch Assistant",
            "Developer Hub": "👨🏾‍💻 Developer Hub",
            "Report Issue": "🚨 Report an Issue"
        }

        # Session state navigation management
        if "active_nav" not in st.session_state:
            st.session_state.active_nav = "Check My Risk"

        selected_label = st.radio(
            "Navigation",
            options=list(nav_options.values()),
            index=list(nav_options.keys()).index(st.session_state.active_nav),
            label_visibility="collapsed"
        )

        # Update active navigation key
        for key, value in nav_options.items():
            if value == selected_label:
                st.session_state.active_nav = key

        st.markdown("---")

        # Quick Status / Information Footer
        st.markdown(
            f"""
            <div style="font-size: 0.8rem; color: #94A3B8; padding: 10px 0;">
                <strong>Developer:</strong> {DEVELOPER_PROFILE['name']}<br>
                <strong>Affiliation:</strong> KNUST Geomatic Engineering Dept<br>
                <span style="color: #2EC4B6;">● System Active</span>
            </div>
            """,
            unsafe_allow_html= True
        )

    return st.session_state.active_nav