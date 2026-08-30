import streamlit as st

from config import DEVELOPER_PROFILE
from components.banners import render_image_banner


def render_user_guide():
    st.markdown(
        """
        <style>
        div[data-testid="stMarkdownContainer"] p,
        div[data-testid="stMarkdownContainer"] li,
        div[data-testid="stMarkdownContainer"] ul,
        div[data-testid="stMarkdownContainer"] ol {
            text-align: justify;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    render_image_banner("user_guide.jpg")
    #st.markdown("## FloodWatch User Guide")
    st.markdown(
        "FloodWatch helps you understand local flood risk using drainage observations, "
        "terrain data, land-cover information, and seven-day rainfall forecasts."
    )

    st.markdown("### Navigating FloodWatch")
    st.markdown(
        '''
        **Check My Flood Risk**  
        Allow location access or adjust the latitude and longitude manually to view the flood-risk estimate for your current position. The app uses nearby drainage conditions, rainfall, slope, flow accumulation, land cover, and drainage capacity to produce the score.\n\n
        **Interactive Flood Map**  \n
        The map shows the user location as a pulsing orange marker with a 50 m radius buffer. You can toggle the map layers from the **Layers** menu, including land cover, slope, flow accumulation, DEM, and survey points. Tap any location to see the spatial analysis and, if relevant, the nearest drainage point details.\n\n
        **Survey Point Information**  \n
        When a user taps a survey/gutter point, FloodWatch displays the exact drainage information for that point, including the photo, risk level, channel type, and block score. If the tap falls between points, the app shows the nearest gutter location and its distance from the selected point.\n\n
        **Community Gallery**  \n
        Browse verified drainage photographs and compare the visual conditions from different locations.\n\n
        **Report an Issue**  \n
        Capture or upload a drainage photograph, review the computer-vision assessment, enter the location details, and submit it for administrator verification.\n\n
        **Developer Hub**  \n
        View developer information. Licensed administrators can open the moderation queue, review submissions, and approve or reject reports.
        '''
    )

    st.markdown("### How the map works")
    st.markdown(
        "1. The app tracks the user’s location and centers the flood map on that position when permission is granted.\n"
        "2. Use the **Layers** menu to switch between land cover, slope, flow accumulation, DEM, and survey points.\n"
        "3. Tap any location on the map to see the spatial analysis for that coordinate.\n"
        "4. If the tapped location matches a gutter/survey point, FloodWatch shows the drainage photo and point-level condition.\n"
        "5. If the tap is not on a recorded gutter point, FloodWatch shows the nearest gutter and the distance to it.\n"
        "6. The orange pulse marker and 50 m circular buffer help users understand their local assessment area."
    )

    st.markdown("### Submitting a Field Report")
    st.markdown(
        "1. Open **Report an Issue** from the sidebar.\n"
        "2. Confirm your latitude and longitude.\n"
        "3. Upload a clear photograph showing the drainage structure.\n"
        "4. Check the AI suggestion and select the observed blockage level.\n"
        "5. Choose the drainage type and add a nearby landmark.\n"
        "6. Submit the report for administrator review."
    )

    st.markdown("### Understanding Risk Results")
    st.markdown(
        "Risk results combine blockage, seven-day rainfall, slope, flow accumulation, "
        "drainage capacity, and land-cover risk. A higher score indicates greater localized flood vulnerability."
    )
    st.markdown(
        "- **Low:** 0.00-0.25\n"
        "- **Moderately Low:** 0.26-0.50\n"
        "- **Moderately High:** 0.51-0.75\n"
        "- **High:** 0.76-1.00"
    )

    st.markdown("### Contact the Developer")
    st.markdown(
        f"For questions, feedback, or technical support, contact **{DEVELOPER_PROFILE['name']}**."
    )
    
    col1, col2 = st.columns(2)
    with col1:
        email = DEVELOPER_PROFILE["contact"]["email2"]
        st.link_button("📧 Email", f"mailto:{email}", use_container_width=True)
    
    with col2:
        phone = DEVELOPER_PROFILE["contact"]["phone"].replace("+", "").replace(" ", "")
        st.link_button("💬 WhatsApp", f"https://wa.me/{phone}", use_container_width=True)
