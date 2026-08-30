import streamlit as st
import requests


def render_location_button(label: str = "📍 Get My Location", key: str = "browser_location"):
    """Use a regular Streamlit button to fetch coordinates via IP fallback on localhost."""
    if key not in st.session_state:
        st.session_state[key] = {"latitude": None, "longitude": None, "error": ""}

    button_col = st.columns([1])[0]
    with button_col:
        clicked = st.button(label, key=f"{key}_button", type="primary", use_container_width=True)

    if clicked:
        try:
            response = requests.get("https://ipapi.co/json/", timeout=10)
            response.raise_for_status()
            data = response.json()

            lat = data.get("latitude")
            lng = data.get("longitude")

            if lat is not None and lng is not None:
                st.session_state[key] = {"latitude": float(lat), "longitude": float(lng), "error": ""}
                st.success(f"Location captured: {float(lat):.5f}, {float(lng):.5f}")
                return float(lat), float(lng), ""

            st.session_state[key] = {"latitude": None, "longitude": None, "error": "Location permission required. Please allow access to your location or enter the coordinates manually."}
            st.warning("Location permission required. Please allow access to your location or enter the coordinates manually.")
            return None, None, st.session_state[key]["error"]
        except Exception:
            st.session_state[key] = {"latitude": None, "longitude": None, "error": "Location permission required. Please allow access to your location or enter the coordinates manually."}
            st.warning("Location permission required. Please allow access to your location or enter the coordinates manually.")
            return None, None, st.session_state[key]["error"]

    return st.session_state[key]["latitude"], st.session_state[key]["longitude"], st.session_state[key]["error"]
