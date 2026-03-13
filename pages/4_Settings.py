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
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500&family=Orbitron:wght@400;500;700;900&family=Inter:wght@300;400;500;600;700&display=swap');

        :root {
            --primary: #bc13fe;
            --primary-glow: rgba(188, 19, 254, 0.4);
            --secondary: #00f3ff;
            --secondary-glow: rgba(0, 243, 255, 0.3);
            --bg: #050505;
            --surface: rgba(16, 16, 24, 0.7);
            --border: rgba(188, 19, 254, 0.3);
            --text: #e6edf3;
            --text-secondary: #8b949e;
            --radius: 4px;
        }

        html, body, [data-testid="stAppViewContainer"],
        .stApp, [data-testid="stMainBlockContainer"] {
            font-family: 'Inter', sans-serif;
            background-color: var(--bg) !important;
            background-image: 
                radial-gradient(circle at 50% 50%, rgba(188, 19, 254, 0.05) 0%, transparent 50%),
                linear-gradient(rgba(188, 19, 254, 0.02) 1px, transparent 1px),
                linear-gradient(90deg, rgba(188, 19, 254, 0.02) 1px, transparent 1px);
            background-size: 100% 100%, 30px 30px, 30px 30px;
        }

        .sec-title {
            font-family: 'Orbitron', sans-serif !important;
            font-size: 1.25rem; font-weight: 600; color: var(--text); margin-bottom: 0.5rem;
            text-transform: uppercase; letter-spacing: 2px;
        }
        .sec-desc {
            font-size: 0.85rem; color: var(--text-secondary); margin-bottom: 1.5rem;
        }
        
        .brand {
            text-align: center; padding: 1.5rem 0;
        }
        .brand h1 {
            font-family: 'Orbitron', sans-serif !important;
            font-size: 2rem; font-weight: 900; letter-spacing: 8px;
            background: linear-gradient(90deg, var(--primary), var(--secondary));
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        }

        [data-testid="stVerticalBlockBorderWrapper"] > div:has(> div.element-container) {
            background: var(--surface) !important;
            backdrop-filter: blur(12px) !important;
            border: 1px solid var(--border) !important;
            border-radius: var(--radius) !important;
            padding: 1.5rem;
        }
        
        [data-testid="stSidebar"] {
            background-color: rgba(5, 5, 5, 0.95) !important;
            border-right: 1px solid var(--border) !important;
            backdrop-filter: blur(15px);
            box-shadow: 5px 0 15px rgba(188, 19, 254, 0.1);
        }
        [data-testid="stSidebarNav"] {
            background-color: transparent !important;
            padding-top: 2rem;
        }

        /* Back to Top Button */
        .back-to-top {
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: var(--surface);
            border: 1px solid var(--primary);
            color: var(--primary);
            width: 40px;
            height: 40px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            z-index: 9999;
            transition: all 0.3s;
            text-decoration: none !important;
            box-shadow: 0 0 10px var(--primary-glow);
        }
        .back-to-top:hover {
            background: var(--primary);
            color: #000;
            box-shadow: 0 0 20px var(--primary-glow);
            transform: translateY(-3px);
        }
        </style>
        <a href="#lagent-settings" class="back-to-top">↑</a>
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
    st.set_page_config(page_title="Settings - Lagent", layout="wide")
    apply_theme()

    st.markdown(
        '<div class="brand" id="lagent-settings">'
        "<h1>Lagent<b>Settings</b></h1>"
        '<p style="font-size:0.65rem; color:#8b949e; letter-spacing:2px; text-transform:uppercase;">BYOK & Engine Configuration</p>'
        "</div>",
        unsafe_allow_html=True,
    )

    # Initialize session state if not set
    if "OPENROUTER_API_KEY" not in st.session_state:
        st.session_state.OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
    if "OPENROUTER_MODEL" not in st.session_state:
        st.session_state.OPENROUTER_MODEL = "openrouter/free"
    if "HF_API_TOKEN" not in st.session_state:
        st.session_state.HF_API_TOKEN = os.getenv("HF_API_TOKEN", "")

    tab_byok, tab_system = st.tabs(["Bring Your Own Key", "System Info"])

    with tab_byok:
        col_form, col_help = st.columns([1.5, 1], gap="large")

        with col_form:
            # ── OpenRouter ──
            with st.container(border=True):
                st.subheader("OpenRouter Configuration")
                st.markdown('<p class="sec-desc">Used for product descriptions and reasoning.</p>', unsafe_allow_html=True)
                
                new_key = st.text_input(
                    "OpenRouter API Key", 
                    value=st.session_state.OPENROUTER_API_KEY, 
                    type="password",
                    help="Find or create your key at https://openrouter.ai/keys"
                )
                
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
                
                current_model = st.session_state.OPENROUTER_MODEL
                if current_model not in models:
                    models.insert(0, current_model)
                
                new_model = st.selectbox(
                    "Primary AI Model", 
                    options=models,
                    index=models.index(current_model)
                )

                if st.button("Save OpenRouter Settings", use_container_width=True):
                    st.session_state.OPENROUTER_API_KEY = new_key
                    st.session_state.OPENROUTER_MODEL = new_model
                    st.success("OpenRouter settings saved!")

            st.markdown("<br>", unsafe_allow_html=True)

            # ── Hugging Face ──
            with st.container(border=True):
                st.subheader("Hugging Face Configuration")
                st.markdown('<p class="sec-desc">Used for Deep AI Image Enhancement (SwinIR).</p>', unsafe_allow_html=True)
                
                new_hf_token = st.text_input(
                    "Hugging Face Access Token", 
                    value=st.session_state.HF_API_TOKEN, 
                    type="password",
                    help="Get a free token at https://huggingface.co/settings/tokens"
                )

                if st.button("Save Hugging Face Settings", use_container_width=True):
                    st.session_state.HF_API_TOKEN = new_hf_token
                    st.success("Hugging Face token saved!")


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
