import streamlit as st
import sys
import os
import requests
from dotenv import load_dotenv

# Path setup
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

load_dotenv()

# ──────────────────────────────────────────────
# THEME (shared)
# ──────────────────────────────────────────────

def apply_theme():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

        :root {
            --primary: #7c6aef;
            --primary-hover: #9586f5;
            --bg: #0e1117;
            --surface: #161b22;
            --border: #21262d;
            --text: #e6edf3;
            --text-secondary: #8b949e;
            --radius: 8px;
        }

        html, body, [data-testid="stAppViewContainer"] {
            font-family: 'Inter', sans-serif;
            background-color: var(--bg) !important;
            color: var(--text);
        }

        .sec-title {
            font-size: 1.25rem; font-weight: 600; color: var(--text); margin-bottom: 0.5rem;
        }
        .sec-desc {
            font-size: 0.85rem; color: var(--text-secondary); margin-bottom: 1.5rem;
        }
        
        .brand {
            text-align: center; padding: 1.25rem 0 0.5rem 0;
        }
        .brand h1 {
            font-size: 1.5rem; font-weight: 300; letter-spacing: 5px; color: var(--text); margin: 0;
        }
        .brand h1 b { font-weight: 700; color: var(--primary); }

        .settings-card {
            background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 1.5rem; margin-bottom: 1rem;
        }
        
        [data-testid="stSidebar"] {
            background-color: var(--surface) !important;
            border-right: 1px solid var(--border) !important;
        }
        
        .stButton > button {
            border-radius: var(--radius) !important;
            background: var(--primary) !important;
            color: #fff !important;
            font-weight: 600 !important;
        }
        </style>
    """, unsafe_allow_html=True)


def test_openrouter_connection(api_key, model):
    """Simple test call to OpenRouter to verify the key."""
    if not api_key:
        return False, "API Key is required"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": "Say 'OK' if you can hear me."}],
        "max_tokens": 10
    }
    
    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=10
        )
        if response.status_code == 200:
            return True, "Connection Successful!"
        else:
            return False, f"Error {response.status_code}: {response.text[:100]}"
    except Exception as e:
        return False, f"Network Error: {str(e)}"


def main():
    st.set_page_config(page_title="Settings - Product AI", layout="wide")
    apply_theme()

    st.markdown(
        '<div class="brand">'
        "<h1>Agent<b>Settings</b></h1>"
        '<p style="font-size:0.65rem; color:#8b949e; letter-spacing:2px; text-transform:uppercase;">BYOK & Engine Configuration</p>'
        "</div>",
        unsafe_allow_html=True,
    )

    # Initialize session state if not set
    if "OPENROUTER_API_KEY" not in st.session_state:
        st.session_state.OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
    if "OPENROUTER_MODEL" not in st.session_state:
        st.session_state.OPENROUTER_MODEL = "openrouter/free"

    tab_byok, tab_system = st.tabs(["Bring Your Own Key", "System Info"])

    with tab_byok:
        st.markdown('<p class="sec-title">OpenRouter Configuration</p>', unsafe_allow_html=True)
        st.markdown('<p class="sec-desc">Configure your OpenRouter API key and preferred model. These settings are stored in your current session.</p>', unsafe_allow_html=True)

        col_form, col_help = st.columns([1.5, 1], gap="large")

        with col_form:
            with st.container(border=True):
                st.subheader("API Credentials")
                
                # API Key Input
                new_key = st.text_input(
                    "OpenRouter API Key", 
                    value=st.session_state.OPENROUTER_API_KEY, 
                    type="password",
                    help="Find or create your key at https://openrouter.ai/keys"
                )
                
                # Model Selection
                models = [
                    "openrouter/free",
                    "google/gemini-2.0-flash-001",
                    "google/gemini-pro-1.5",
                    "anthropic/claude-3-haiku",
                    "anthropic/claude-3.5-sonnet",
                    "meta-llama/llama-3.1-8b-instruct",
                    "mistralai/mistral-7b-instruct",
                    "deepseek/deepseek-chat"
                ]
                
                # Ensure current model is in list or add it
                current_model = st.session_state.OPENROUTER_MODEL
                if current_model not in models:
                    models.insert(0, current_model)
                
                new_model = st.selectbox(
                    "Primary AI Model", 
                    options=models,
                    index=models.index(current_model),
                    help="The model used for generating product descriptions."
                )
                
                st.markdown("<br>", unsafe_allow_html=True)
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Save Settings", use_container_width=True):
                        st.session_state.OPENROUTER_API_KEY = new_key
                        st.session_state.OPENROUTER_MODEL = new_model
                        st.success("Settings saved for this session!")
                
                with col2:
                    if st.button("Test Connection", use_container_width=True):
                        with st.spinner("Testing handshake..."):
                            success, msg = test_openrouter_connection(new_key, new_model)
                            if success:
                                st.toast(msg, icon="✅")
                            else:
                                st.error(msg)

        with col_help:
            st.info("""
            **Why use BYOK?**
            - Control your own usage limits and billing.
            - Access specialized models (Gemini, Claude, Llama).
            - Ensure data privacy with your own API management.
            
            **How to get a key:**
            1. Go to [OpenRouter.ai](https://openrouter.ai)
            2. Sign up or login.
            3. Go to **Keys** and click **Create Key**.
            4. Copy and paste it here.
            """)

    with tab_system:
        st.markdown('<p class="sec-title">Environment Information</p>', unsafe_allow_html=True)
        
        env_cols = st.columns(3)
        with env_cols[0]:
            st.metric("App Version", "1.0.4-NEURAL")
        with env_cols[1]:
            st.metric("Status", "Operational", delta="Normal")
        with env_cols[2]:
            st.metric("Connectivity", "Cloud-Active")

        st.divider()
        st.caption("Developed by Google DeepMind / Advanced Agentic Coding Team.")


if __name__ == "__main__":
    main()
