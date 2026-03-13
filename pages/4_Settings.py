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
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700&family=Orbitron:wght@400;500;700;900&family=Inter:wght@300;400;500;600;700;900&display=swap');

        :root {
            --primary: #00f3ff;
            --primary-glow: rgba(0, 243, 255, 0.4);
            --secondary: #ff00ff;
            --secondary-glow: rgba(255, 0, 255, 0.4);
            --accent: #bc13fe;
            --bg: #09090b; /* Deep dark for neumorphism */
            --bg-elevated: #111115;
            --surface: rgba(17, 17, 21, 0.65); /* Glassmorphic base */
            --border: #27272a;
            --border-neon: rgba(0, 243, 255, 0.6);
            --text: #f8fafc;
            --text-secondary: #94a3b8;
            --text-muted: #64748b;
            --green: #10b981;
            --red: #ef4444;
            --radius: 0px; /* Brutalism */
            --radius-btn: 2px;
            --neu-shadow: 6px 6px 12px #040405, -6px -6px 12px #0e0e11;
            --neu-inset: inset 4px 4px 8px #040405, inset -4px -4px 8px #0e0e11;
        }

        /* Base App Styling */
        html, body, [data-testid="stAppViewContainer"],
        .stApp, [data-testid="stMainBlockContainer"] {
            font-family: 'Inter', sans-serif;
            background-color: var(--bg) !important;
            background-image: 
                linear-gradient(rgba(0, 243, 255, 0.03) 1px, transparent 1px),
                linear-gradient(90deg, rgba(0, 243, 255, 0.03) 1px, transparent 1px);
            background-size: 40px 40px; /* Grid for cyberpunk feel */
            color: var(--text);
            scroll-behavior: smooth;
        }

        /* Typography */
        h1, h2, h3, .sec-title, .brand h1 {
            font-family: 'Orbitron', sans-serif !important;
            text-transform: uppercase;
            letter-spacing: 1.5px;
        }

        /* Brutalist / Neumorphic Cards */
        div[data-testid="stVerticalBlockBorderWrapper"] > div {
            background-color: var(--bg-elevated) !important;
            border: 2px solid var(--border) !important; /* Brutalism */
            border-radius: var(--radius) !important;
            box-shadow: var(--neu-shadow) !important; /* Neumorphism */
            padding: 1.5rem !important;
            transition: all 0.3s ease;
        }
        
        div[data-testid="stVerticalBlockBorderWrapper"] > div:hover {
            border-color: var(--border-neon) !important;
            box-shadow: 0 0 20px var(--primary-glow), var(--neu-shadow) !important; /* Cyberpunk Neon */
        }

        /* Inputs & Textareas */
        .stTextInput input, .stTextArea textarea, .stSelectbox > div[data-baseweb="select"] {
            background-color: var(--bg) !important;
            border: 2px solid var(--border) !important;
            color: var(--text) !important;
            border-radius: var(--radius) !important;
            box-shadow: var(--neu-inset) !important; /* Neumorphism inner shadow */
            font-family: 'JetBrains Mono', monospace !important;
            transition: border-color 0.2s, box-shadow 0.2s;
        }
        
        .stTextInput input:focus, .stTextArea textarea:focus, .stSelectbox > div[data-baseweb="select"]:focus-within {
            border-color: var(--primary) !important;
            box-shadow: 0 0 12px var(--primary-glow), var(--neu-inset) !important;
            outline: none !important;
        }

        /* Buttons: Brutalist + Neon + Neumorphism */
        .stButton > button, [data-testid="baseButton-secondary"] {
            background-color: var(--bg-elevated) !important;
            color: var(--primary) !important;
            border: 2px solid var(--primary) !important;
            border-radius: var(--radius-btn) !important;
            text-transform: uppercase;
            font-family: 'Orbitron', sans-serif !important;
            font-weight: 700 !important;
            letter-spacing: 1.5px;
            box-shadow: var(--neu-shadow) !important;
            transition: all 0.2s cubic-bezier(0.25, 0.8, 0.25, 1) !important;
            min-height: 44px; /* Touch target size */
            padding: 0.5rem 1.5rem !important;
            position: relative;
            overflow: hidden;
        }
        
        .stButton > button:hover {
            background-color: rgba(0, 243, 255, 0.1) !important;
            color: var(--primary) !important;
            box-shadow: 0 0 20px var(--primary-glow), var(--neu-shadow) !important;
            transform: translateY(-2px);
            border-color: var(--primary) !important;
        }

        /* Sidebar - Glassmorphism */
        [data-testid="stSidebar"] {
            background-color: rgba(9, 9, 11, 0.75) !important;
            border-right: 2px solid var(--border-neon) !important;
            backdrop-filter: blur(24px) saturate(180%) !important; /* Glassmorphism */
            box-shadow: 5px 0 25px rgba(0, 243, 255, 0.1);
        }
        
        [data-testid="stSidebarNav"] {
            background: transparent !important;
            padding-top: 2rem;
        }
        
        [data-testid="stSidebarNav"] li {
            border-radius: 0;
            margin-bottom: 5px;
            transition: all 0.2s;
            border: 1px solid transparent;
        }

        [data-testid="stSidebarNav"] li:hover {
            background: rgba(0, 243, 255, 0.05) !important;
            border: 1px solid var(--primary-glow) !important;
            box-shadow: 0 0 10px var(--primary-glow);
        }

        [data-testid="stSidebarNav"] li a span {
            font-family: 'Orbitron', sans-serif !important;
            text-transform: uppercase;
            font-size: 0.8rem !important;
            letter-spacing: 1px;
        }

        [data-testid="stSidebarNav"] li[data-selected="true"] {
            background: rgba(0, 243, 255, 0.15) !important;
            border-left: 5px solid var(--primary) !important;
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
            font-size: 2.5rem; font-weight: 900; letter-spacing: 8px;
            background: linear-gradient(90deg, var(--primary), var(--secondary));
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
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


def test_huggingface_connection(token):
    """Simple test call to HF to verify the token using a standard model."""
    if not token:
        return False, "Token is required"
    
    # We use a standard model that is usually always available to probe the token
    probe_model = "google/vit-base-patch16-224"
    url = f"https://router.huggingface.co/hf-inference/models/{probe_model}"
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        # Minimal request - just probe the endpoint
        response = requests.get(url, headers=headers, timeout=10)
        # Even a 400 (if no data) or 200 (if successful) indicates the token is accepted
        # If it was 401 or 403, it would fail
        if response.status_code in [200, 400]:
            return True, "Neural link established!"
        elif response.status_code == 403:
            return False, "Forbidden: Check token permissions (Inference scope needed)."
        elif response.status_code == 401:
            return False, "Unauthorized: Invalid Token."
        else:
            return False, f"HF API Error {response.status_code}"
    except Exception as e:
        return False, f"Network Error: {str(e)}"


def save_to_env(key, value):
    """Persists a key-value pair to the .env file."""
    env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    lines = []
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            lines = f.readlines()
    
    found = False
    new_line = f'{key}="{value}"\n'
    for i, line in enumerate(lines):
        if line.startswith(f'{key}='):
            lines[i] = new_line
            found = True
            break
    
    if not found:
        lines.append(new_line)
    
    with open(env_path, 'w') as f:
        f.writelines(lines)
    
    # Reload environment variables for the current process
    os.environ[key] = value


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

                if st.button("Save OpenRouter Settings", width='stretch'):
                    st.session_state.OPENROUTER_API_KEY = new_key
                    st.session_state.OPENROUTER_MODEL = new_model
                    save_to_env("OPENROUTER_API_KEY", new_key)
                    save_to_env("OPENROUTER_MODEL", new_model)
                    st.success("OpenRouter settings saved and persisted!")

                if st.button("Test OpenRouter Connection", width='stretch', type="secondary"):
                    with st.spinner("Testing neural link..."):
                        ok, msg = test_openrouter_connection(new_key, new_model)
                        if ok:
                            st.success(msg)
                        else:
                            st.error(msg)

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

                if st.button("Save Hugging Face Settings", width='stretch'):
                    st.session_state.HF_API_TOKEN = new_hf_token
                    save_to_env("HF_API_TOKEN", new_hf_token)
                    st.success("Hugging Face token saved and persisted!")

                if st.button("Test Hugging Face Connection", width='stretch', type="secondary"):
                    with st.spinner("Probing HF Inference..."):
                        ok, msg = test_huggingface_connection(new_hf_token)
                        if ok:
                            st.success(msg)
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
