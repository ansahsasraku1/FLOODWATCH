"""
Chatbot Component for FloodWatch
Renders an interactive chatbot interface for real-time Q&A about the app.
"""

import streamlit as st
from services.chatbot_service import get_chatbot_response, get_chatbot_client
from components.banners import render_image_banner


def render_chatbot():
    """
    Render the chatbot interface with message history.
    """
    render_image_banner("ai_page.jpg")
    st.markdown("AMA - AI Assistant")
    #st.markdown(
        #"Ask me anything about FloodWatch, your flood risk assessment, spatial data interpretation, "
        #"drainage infrastructure, or how to use the app."
    #)
    #🤖
    # Check if API key is available
    if not get_chatbot_client():
        st.warning(
            "🔑 **API Key Not Configured**\n\n"
            "To use the chatbot, you need a Google Gemini API key. "
            "Please add it to your Streamlit secrets:\n\n"
            "`gemini_api_key=your-api-key-here`\n\n"
            "Get a free API key at: https://aistudio.google.com/app/apikey"
        )
        return
    
    # Initialize chat history in session state
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = [
            {"role": "assistant", "content": "Hello! 👋 I'm **AMA**, your FloodWatch AI guide. I can help you:\n\n Interpret your flood risk score"
            "\n\n Explain how slope, elevation (DEM), flow accumulation, and land cover affect your area"
            "\n\n Navigate the app and its features "
            "\n\n Understand drainage conditions \n\nWhat would you like to know ?"
            }
        ]
    
    # Display chat history
    chat_container = st.container()
    with chat_container:
        for message in st.session_state.chat_history:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
    
    # User input
    user_input = st.chat_input("Ask me something...", key="user_input")
    
    if user_input:
        # Add user message to history and display
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        
        with st.chat_message("user"):
            st.markdown(user_input)
        
        # Get chatbot response
        with st.spinner("🤔 AMA is thinking..."):
            # Add context if user has a current prediction
            system_context = ""
            if "user_lat" in st.session_state and "current_prediction" in st.session_state:
                current_pred = st.session_state.current_prediction
                user_loc = f"({st.session_state.user_lat:.5f}, {st.session_state.user_lng:.5f})"
                system_context = f"""
**Current Flood Assessment Context:**
- Location: {user_loc}
- Risk Score: {current_pred.get('score', 'N/A')}
- Risk Level: {current_pred.get('level', 'N/A')}
- Blockage Percentage: {current_pred.get('blockage_percentage', 'N/A')}%
"""
            
            recent_history = st.session_state.chat_history[-6:]
            response = get_chatbot_response(
                user_input,
                system_context,
                conversation_history=recent_history,
            )
        
        if response:
            st.session_state.chat_history.append({"role": "assistant", "content": response})
            with st.chat_message("assistant"):
                st.markdown(response)
        else:
            st.error("Failed to get a response. Please check your API key and try again.")
    
    # Clear history button in sidebar
    if st.session_state.chat_history:
        st.divider()
        if st.button("Clear Chat History", use_container_width=True):
            st.session_state.chat_history = []
            st.rerun()
