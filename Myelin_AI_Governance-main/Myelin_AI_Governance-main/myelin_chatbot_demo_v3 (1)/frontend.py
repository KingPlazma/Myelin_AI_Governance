import os
import json
import time
import requests
import streamlit as st
from typing import Dict, Any


DEMO_BACKEND_URL = os.getenv("DEMO_BACKEND_URL", "http://127.0.0.1:8000")

# Dark theme configuration
st.set_page_config(
    page_title="Myelin Bot",
    page_icon="🛡️",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Dark background with ChatGPT-style styling
st.markdown("""
<style>
    * {
        background-color: #0d0d0d;
        color: #ececec;
    }
    .stTextInput > div > div > input {
        background-color: #40414f;
        color: #ececec;
    }
    .stButton > button {
        background-color: #10a37f;
        color: white;
    }
    .stButton > button:hover {
        background-color: #0d8967;
    }
    .chat-message {
        margin: 1rem 0;
        padding: 1rem;
        border-radius: 8px;
    }
    .user-message {
        background-color: #40414f;
        margin-left: 5%;
    }
    .bot-message {
        background-color: #444654;
        margin-right: 5%;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "history" not in st.session_state:
    st.session_state.history = []

# Main title
st.title("🛡️ Myelin Bot")

# Chat container
st.subheader("Chat")

# Display chat history
for item in st.session_state.history[-50:]:
    st.markdown(f"""
    <div class="chat-message user-message">
        <strong>You:</strong> {item['prompt']}
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"""
    <div class="chat-message bot-message">
        <strong>Bot:</strong> {item['response']}
    </div>
    """, unsafe_allow_html=True)

# Input form
with st.form(key="chat_form"):
    prompt = st.text_input(
        "Message:",
        key="chat_input",
        placeholder="Type a message..."
    )
    submit_button = st.form_submit_button("Send", use_container_width=True)

if st.button("Clear", use_container_width=True):
    st.session_state.history = []
    st.rerun()


def send_chat_request(prompt: str):
    """Send chat request to backend."""
    try:
        session_id = st.session_state.get("session_id", f"streamlit_{hash(str(time.time()))}")
        st.session_state.session_id = session_id

        response = requests.post(
            f"{DEMO_BACKEND_URL}/chat",
            json={"prompt": prompt, "session_id": session_id},
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()

        # Add to history (only prompt and response)
        st.session_state.history.append({
            "prompt": prompt,
            "response": data["response"],
            "timestamp": time.time()
        })

        # Rerun to update UI
        st.rerun()

    except Exception as exc:
        st.error(f"Error: {exc}")
        st.session_state.history.append({
            "prompt": prompt,
            "response": f"Error: {exc}",
            "error": True,
            "timestamp": time.time()
        })


# Handle form submission
if submit_button and prompt.strip():
    send_chat_request(prompt.strip())
