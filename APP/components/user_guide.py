import streamlit as st

from config import DEVELOPER_PROFILE
from components.banners import render_image_banner


def render_user_guide():
    render_image_banner("user_guide.jpg")
    st.markdown("## FloodWatch User Guide")
    st.markdown(
        "FloodWatch helps you understand local flood risk using drainage observations, "
        "terrain data, land-cover information, and seven-day rainfall forecasts."
    )

    st.markdown("### Navigating FloodWatch")
    st.markdown(
        """
        **Check My Flood Risk**  
        Enter your location or allow location access to view the current risk assessment. """
        "The result uses the nearest surveyed drainage point together with rainfall and terrain data.\n\n"
        "**Flood Map**  \n"
        "Explore surveyed drainage points on the interactive map. Select a point to view its risk level, channel type, and field photograph.\n\n"
        "**Community Gallery**  \n"
        "Browse verified drainage photographs and filter observations by risk level.\n\n"
        "**Report an Issue**  \n"
        "Capture or upload a drainage photograph, review the computer-vision assessment, enter the location details, and submit it for administrator verification.\n\n"
        "**Developer Hub**  \n"
        "View developer information. Licensed administrators can open the moderation queue, review submissions, and approve or reject reports."
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
    email, whatsapp = st.columns(2)
    with email:
        st.link_button(
            "Email: daappiah11@gmail.com",
            f"mailto:{DEVELOPER_PROFILE['contact']['email2']}",
            use_container_width=True,
        )
    with whatsapp:
        phone = DEVELOPER_PROFILE["contact"]["phone"]
        whatsapp_number = phone.replace("+", "").replace(" ", "")
        st.link_button(
            f"WhatsApp: {phone}",
            f"https://wa.me/{whatsapp_number}",
            use_container_width=True,
        )
