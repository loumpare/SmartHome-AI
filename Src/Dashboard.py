import streamlit as st # pyright: ignore[reportMissingImports]
import requests
import os

# Page configuration
st.set_page_config(page_title="AI Home OS", page_icon="🤖")

# Load API URL from environment variables (defaults to localhost for dev)
# In production/Docker, this would be http://backend:8000/ask
API_URL = os.getenv("BACKEND_API_URL", "http://127.0.0.1:8000/ask-agent")

st.title("🤖 AI Home OS")

# Sidebar for Quick Scenarios
with st.sidebar:
    st.header("Quick Actions")
    
    if st.button("🔌 Arrival (Night Mode)"):
        # Sends a pre-defined instruction in English
        res = requests.post(API_URL, 
                            json={"instruction": "I am home, it's dark and cold."})
        st.success("Arrival sequence initiated")

    if st.button("🛡️ Departure (Security)"):
        res = requests.post(API_URL, 
                            json={"instruction": "I'm leaving, turn off everything and secure the house."})
        st.warning("House secured")

# Chat Interface
st.subheader("Control Center")
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User input
if prompt := st.chat_input("How can I help you today?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    try:
        # FastAPI API Call
        response = requests.post(API_URL, json={"instruction": prompt})
        data = response.json()
        
        # Safely extract response and execution details
        api_response = data.get('response', "No response from server.")
        api_details = data.get('details', [])

        # Format output for the UI
        full_response = f"{api_response}\n\n**System Logs:** {', '.join(api_details) if api_details else 'None'}"

    except Exception as e:
        full_response = f"⚠️ Connection error: Could not reach the AI Backend. ({str(e)})"

    with st.chat_message("assistant"):
        st.markdown(full_response)
    st.session_state.messages.append({"role": "assistant", "content": full_response})