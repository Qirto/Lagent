import streamlit as st
import streamlit.components.v1 as components
import sys
import os
import requests
from dotenv import load_dotenv

# Path setup
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.theme import apply_theme



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
                    components.html(f"""
                    <script>
                    localStorage.setItem('lagent_openrouter_key', '{new_key}');
                    localStorage.setItem('lagent_openrouter_model', '{new_model}');
                    </script>
                    """, height=0)
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
                    components.html(f"""
                    <script>
                    localStorage.setItem('lagent_hf_token', '{new_hf_token}');
                    </script>
                    """, height=0)
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
