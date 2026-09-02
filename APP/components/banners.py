import os
import base64
import streamlit as st

def resolve_banner_asset(filename: str) -> str:
    """Find video or image files directly inside FLOODWATCH_CODE/APP/assets/."""
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # Search candidates relative to execution path or script location
    candidate_paths = [
        # Path when banners.py is inside components/ or APP/components/
        os.path.abspath(os.path.join(current_dir, "..", "APP", "assets", filename)),
        os.path.abspath(os.path.join(current_dir, "..", "assets", filename)),
        # Path relative to working directory (where `streamlit run` is executed)
        os.path.abspath(os.path.join(os.getcwd(), "APP", "assets", filename)),
        os.path.abspath(os.path.join(os.getcwd(), "assets", filename)),
    ]

    for path in candidate_paths:
        if os.path.exists(path):
            return path

    return candidate_paths[0]


def render_video_banner(filename: str = "check_risk.mp4", height: int = 160):
    """Render an autoplaying HTML5 video loop banner encoded in base64."""
    path = resolve_banner_asset(filename)

    if os.path.exists(path):
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
                unsafe_allow_html=True,
            )
        except Exception as e:
            st.error(f"Error loading video file: {e}")
    else:
        st.error(f"⚠️ Video banner not found at: `{path}`")


def render_image_banner(filename: str, use_container_width: bool = True):
    """
    Renders image banner or redirects flood_map.jpg to check_risk.mp4
    so you don't have to edit main.py.
    """
    # If main.py calls flood_map.jpg, intercept it and display check_risk.mp4 instead
    if filename in ["flood_map.jpg", "flood_map.png"]:
        render_video_banner("check_risk.mp4")
        return

    path = resolve_banner_asset(filename)
    if os.path.exists(path):
        st.image(path, use_container_width=use_container_width)
    else:
        st.warning(f"⚠️ Image banner not found at: `{path}`")