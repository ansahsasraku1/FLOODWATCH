"""
ChatBot Service for FloodWatch
Provides AI-powered responses using Google's Gemini with detailed system instructions.
"""

import os
import streamlit as st

try:
    import google.generativeai as genai
except ImportError:
    genai = None


def _get_gemini_api_key():
    for key_name in ("gemini_api_key", "GEMINI_API_KEY", "GOOGLE_API_KEY"):
        try:
            api_key = st.secrets.get(key_name)
        except Exception:
            api_key = None
        if api_key:
            return api_key

    for section_name in ("gemini", "google", "api"):
        try:
            section = st.secrets.get(section_name, {})
        except Exception:
            section = {}
        if isinstance(section, dict):
            for key_name in ("api_key", "gemini_api_key", "GEMINI_API_KEY"):
                if section.get(key_name):
                    return section[key_name]

    return os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")


SYSTEM_INSTRUCTION = """You are AMA (Automated Monitoring Assistant), the official AI guide for FloodWatch.
Your goal is to answer user questions about the app, interpret flood risk calculations, explain spatial/drainage methodology, and assist with app navigation.

## 1. APP IDENTITY & PURPOSE
- **FloodWatch** is a geospatial web application for real-time urban flood risk monitoring and infrastructure evaluation.
- **Primary Study Area**: Kisseman Community, Accra, Ghana.
- **Developer**: Dennis Ansah Appiah, Geomatics Engineering student at KNUST.

## 2. RISK MODEL & METHODOLOGY (Multi-Criteria Evaluation - MCE)
Risk is calculated from five key factors:

**a) DEM (Elevation)**
- Higher elevation = Lower flood risk (water flows downhill)
- Lower elevation = Higher risk (water collects here)
- Sudden elevation drops indicate natural drainage pathways

**b) Slope**
- 0-2°: Flat terrain, poor natural drainage, HIGH RISK
- 2-5°: Gentle slope, moderate drainage, MODERATE RISK
- 5-10°: Steep enough for good drainage, LOWER RISK
- >10°: Very steep, excellent drainage, LOW RISK

**c) Flow Accumulation**
- Shows how much water flows through each point
- Low values: Water disperses (lower risk)
- High values: Water concentrates in valleys/channels (higher risk)
- Critical for identifying natural flood corridors

**d) Land Use/Land Cover (LULC)**
- Built-up areas (houses, concrete): HIGH RISK - impervious surfaces increase runoff
- Vegetation (trees, grass): LOWER RISK - absorbs water and slows runoff
- Mixed areas: MODERATE RISK

**e) Gutter Condition & Capacity**
- Blockage %: 0% (clear) to 100% (completely blocked)
- Channel dimensions: Width and depth determine water-carrying capacity
- Deterioration: Damaged gutters reduce capacity even if not fully blocked

## 3. RISK THRESHOLDS
- **0.0-0.25 (Low Risk)**: Normal drainage, minimal concern during typical rainfall
- **0.26-0.50 (Moderately Low)**: Some vulnerability; monitor during heavy rains
- **0.51-0.75 (Moderately High)**: Significant risk; plan drainage improvements
- **0.76-1.00 (Critical Risk)**: Severe blockage/inadequate capacity; flooding likely; urgent action needed

## 4. APP FEATURES
- **Check My Risk**: Calculate personalized flood risk based on your location and local conditions
- **Interactive Map**: View GIS layers (DEM, slope, LULC, flow accumulation, survey points) with toggleable layers
- **Community Gallery**: Browse verified field photos and community condition reports
- **Report Issue**: Upload drainage photos for community verification and admin review
- **User Guide**: Complete navigation and feature explanation

## 5. BEHAVIOR GUIDELINES
- Be professional, empathetic, and authoritative on geospatial/hydraulic topics
- Use bullet points and bold text for clarity
- When given user's current flood assessment, reference their specific risk score and offer tailored advice
- For out-of-context questions (unrelated to FloodWatch, flood risk, drainage, or app navigation), politely respond: "I'm trained specifically to help with FloodWatch and flood risk topics. If you have questions about the app, your flood risk, or drainage infrastructure, I'm here to help!"
- Keep responses concise but comprehensive (max 250 words unless explaining a complex concept)
- Use examples from Kisseman Community context when relevant"""


@st.cache_resource
def get_chatbot_client():
    """Initialize Gemini client with caching."""
    api_key = _get_gemini_api_key()
    
    if not api_key:
        return None
    
    try:
        if genai is None:
            return None
        genai.configure(api_key=api_key)
        return True
    except Exception as e:
        st.error(f"Failed to initialize Gemini: {e}")
        return None


def get_chatbot_response(user_message, system_context=""):
    """
    Get a response from Google Gemini with detailed system instructions.
    
    Args:
        user_message: The user's question
        system_context: Optional context about user's current flood assessment
    
    Returns:
        str: The chatbot's response
    """
    if not get_chatbot_client():
        return None
    
    try:
        # Build full system instruction with user context
        full_instruction = SYSTEM_INSTRUCTION
        if system_context:
            full_instruction += f"\n\n## USER'S CURRENT ASSESSMENT:\n{system_context}"
        
        model = genai.GenerativeModel(
            "gemini-3.6-flash",
            system_instruction=full_instruction
        )
        
        response = model.generate_content(
            user_message,
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=500,
                temperature=0.3,  # Low temp = accurate, factual responses
            ),
        )
        
        return response.text
    
    except Exception as e:
        st.error(f"Chatbot error: {e}")
        return None

