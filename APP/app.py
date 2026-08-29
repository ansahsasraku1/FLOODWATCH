import streamlit as st

# 1. Page Configuration (Must be first Streamlit command)
st.set_page_config(
    page_title="FloodWatch Kisseman",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Services & Config Imports
from services.data_loader import get_unified_survey_points
from services.spatial import find_nearby_survey_points
from services.weather_api import get_rainfall_forecast
from services.risk_engine import calculate_flood_risk
from config import DEVELOPER_PROFILE
from services.logger import log_prediction
# Component Imports
from components.splash import render_splash
from components.sidebar import render_sidebar
from components.risk_card import render_risk_results
from components.camera import render_camera_workflow
from components.admin_panel import render_admin_panel
from components.map_view import render_interactive_map
from components.gallery import render_community_gallery
#from components.flood_history import render_flood_history

# 2. Session State Initialization
if "page" not in st.session_state:
    st.session_state.page = "splash"
if "user_lat" not in st.session_state:
    st.session_state.user_lat = 5.6493  # Default Kisseman Lat
if "user_lng" not in st.session_state:
    st.session_state.user_lng = -0.2069 # Default Kisseman Lng

# 3. Router Logic
if st.session_state.page == "splash":
    render_splash()
else:
    # Render Navigation Sidebar and get active route key
    active_route = render_sidebar()

    # ------------------------------------------------------------------
    # ROUTE 1: CHECK MY FLOOD RISK
    # ------------------------------------------------------------------
   # ------------------------------------------------------------------
    # ROUTE 1: CHECK MY FLOOD RISK
    # ------------------------------------------------------------------
    if active_route == "Check My Risk":
        st.markdown("## 🌧️ Check My Flood Risk")
        st.write("View real-time risk scores based on local terrain, current 7-day rainfall, and nearby drainage conditions.")

        # Load dataset on-demand for this view
        survey_points = get_unified_survey_points()

        # Coordinate inputs (Simulated GPS / Picker)
        col_a, col_b = st.columns(2)
        with col_a:
            st.session_state.user_lat = st.number_input("Latitude", value=st.session_state.user_lat, format="%.5f")
        with col_b:
            st.session_state.user_lng = st.number_input("Longitude", value=st.session_state.user_lng, format="%.5f")

        # Dynamic calculations
        rainfall = get_rainfall_forecast(st.session_state.user_lat, st.session_state.user_lng)
        
        # Search up to 1000m for closest surveyed drain point
        nearby = find_nearby_survey_points(st.session_state.user_lat, st.session_state.user_lng, survey_points, max_distance_m=1000.0)

        if nearby:
            top = nearby[0]
            st.info(f"📍 Linked to nearest survey point **{top.get('Nearest_Landmark', 'Point')}** ({top['distance_m']}m away)")
            blk = float(top.get('BlockScore', 0.2))
            slp = float(top.get('Slope_Score', 0.2))
            flw = float(top.get('FlowAcc_Score', 0.0))
            cap = float(top.get('Capacity_Risk', 0.5))
            lulc = float(top.get('LULC_Risk', 1.0))
        else:
            # Absolute fallback to nearest point across all survey data
            all_sorted = find_nearby_survey_points(st.session_state.user_lat, st.session_state.user_lng, survey_points, max_distance_m=100000.0)
            if all_sorted:
                top = all_sorted[0]
                st.warning(f"⚠️ Selected location is {top['distance_m']}m from nearest survey point. Using nearest regional baseline.")
                blk = float(top.get('BlockScore', 0.2))
                slp = float(top.get('Slope_Score', 0.2))
                flw = float(top.get('FlowAcc_Score', 0.0))
                cap = float(top.get('Capacity_Risk', 0.5))
                lulc = float(top.get('LULC_Risk', 1.0))
            else:
                top = {}
                blk, slp, flw, cap, lulc = 0.25, 0.5, 0.0, 0.5, 1.0

        # 1. Run updated risk calculation
        risk_res = calculate_flood_risk(
            block_score=blk,
            rainfall_mm=rainfall.get('total_7day', 0.0),
            slope_score=slp,
            flow_acc_score=flw,
            capacity_risk=cap,
            lulc_risk=lulc,
            is_daily_rainfall=False
        )

        # 2. Log prediction ONLY AFTER risk_res is defined
        log_prediction(st.session_state.user_lat, st.session_state.user_lng, top, rainfall, risk_res)

        def switch_to_contribute():
            st.session_state.page = "app"
            st.session_state.active_nav = "Report Issue"
            st.session_state.selected_route = "Report Issue"
            st.rerun()

        render_risk_results(risk_res, rainfall, nearby, on_contribute_click=switch_to_contribute)     
    # ------------------------------------------------------------------
    # ROUTE 2: INTERACTIVE MAP
    # ------------------------------------------------------------------
    elif active_route == "Interactive Map":
        # Load dataset on-demand for map rendering
        survey_points = get_unified_survey_points()
        render_interactive_map(
            survey_points=survey_points, 
            center_lat=st.session_state.user_lat, 
            center_lng=st.session_state.user_lng
        )

    # ------------------------------------------------------------------
    # # ROUTE 3: FLOOD HISTORY
    # # ------------------------------------------------------------------
    # elif active_route == "Flood History":
    #     render_flood_history()

    # # ------------------------------------------------------------------
    # # ROUTE 4: COMMUNITY GALLERY
    # # ------------------------------------------------------------------
    # elif active_route == "Community Gallery":
    #     # Load dataset on-demand for gallery grid
    #     survey_points = get_unified_survey_points()
    #     render_community_gallery(survey_points)

    # ------------------------------------------------------------------
    # ROUTE 5: USER GUIDE
    # ------------------------------------------------------------------
    elif active_route == "User Guide":
        from components.user_guide import render_user_guide

        render_user_guide()

    # ------------------------------------------------------------------
    # ROUTE 6: REPORT ISSUE / CONTRIBUTE (CAMERA)
    # ------------------------------------------------------------------
    elif active_route == "Report Issue":
        render_camera_workflow(st.session_state.user_lat, st.session_state.user_lng)

    # ------------------------------------------------------------------
    # ROUTE 7: DEVELOPER HUB & ADMIN PANEL
    # ------------------------------------------------------------------
    elif active_route == "Developer Hub":
        st.markdown("## 👨🏾‍💻 Developer & System Hub")
        
        tab1, tab2 = st.tabs(["Developer Profile", "Admin Moderation Queue"])
        
        with tab1:
            st.markdown(
                f"""
                ### {DEVELOPER_PROFILE['name']}
                **{DEVELOPER_PROFILE['title']}**
                
                {DEVELOPER_PROFILE['bio']}
                
                **Primary Email:** {DEVELOPER_PROFILE['contact']['email']}  
                **Alternative Email:** {DEVELOPER_PROFILE['contact']['email2']}  
                **Phone:** {DEVELOPER_PROFILE['contact']['phone']}  
                **Location:** {DEVELOPER_PROFILE['contact']['location']}
                """
            )
            st.markdown("##### **Built With**")
            st.write(", ".join(DEVELOPER_PROFILE['tools']))

        with tab2:
            render_admin_panel()

    # Fallback View
    else:
        st.markdown(f"## {active_route}")
        st.info("Section view under construction.")
        
