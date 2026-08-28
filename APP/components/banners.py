import os
import base64
import streamlit as st
from services.asset_paths import get_asset_path

def render_video_banner(filename: str, height: int = 190):
    path = get_asset_path(filename)
    try:
        with open(path, "rb") as f:
            video_bytes = f.read()
        encoded = base64.b64encode(video_bytes).decode("utf-8")
        st.markdown(
            f"""
            <video autoplay loop muted playsinline
                   style="width:100%; height:{height}px; object-fit:cover; border-radius:12px; margin-bottom:16px;">
                <source src="data:video/mp4;base64,{encoded}" type="video/mp4">
            </video>
            """,
            unsafe_allow_html=True
        )
    except FileNotFoundError:
        st.info("Banner video not found.")

def render_image_banner(filename: str, use_container_width: bool = True):
    path = get_asset_path(filename)
    if os.path.exists(path):
        st.image(path, use_container_width=use_container_width)
    else:
        st.info("Banner image not found.")