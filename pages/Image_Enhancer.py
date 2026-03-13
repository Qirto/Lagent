import streamlit as st
import sys
import os
import io
import requests
from PIL import Image
from streamlit_image_comparison import image_comparison

# Path setup
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    from image_enhancer import ImageEnhancer
    HAS_MODULES = True
except Exception as e:
    HAS_MODULES = False
    _ERR = str(e)


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
            font-size: 1.1rem; font-weight: 600; color: var(--text);
            text-transform: uppercase; letter-spacing: 2px;
        }
        .sec-desc {
            font-size: 0.8rem; color: var(--text-secondary); line-height: 1.5;
        }
        
        .brand {
            text-align: left; padding: 1rem 0;
        }
        .brand h1 {
            font-family: 'Orbitron', sans-serif !important;
            font-size: 1.5rem; font-weight: 900; letter-spacing: 4px;
            background: linear-gradient(90deg, var(--primary), var(--secondary));
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        }

        [data-testid="stVerticalBlockBorderWrapper"] > div:has(> div.element-container) {
            background: var(--surface) !important;
            backdrop-filter: blur(12px) !important;
            border: 1px solid var(--border) !important;
            border-radius: var(--radius) !important;
        }

        .analysis-chip {
            padding: 4px 10px; border-radius: 2px; font-size: 0.7rem;
            font-family: 'JetBrains Mono', monospace;
            background: rgba(0, 243, 255, 0.05); border: 1px solid rgba(0, 243, 255, 0.2);
            color: var(--secondary); display: inline-block; margin-right: 5px;
        }

        .stButton > button {
            border-radius: var(--radius) !important;
            font-family: 'Orbitron', sans-serif !important;
            background: transparent !important;
            color: var(--secondary) !important;
            border: 1px solid var(--secondary) !important;
            text-transform: uppercase;
            letter-spacing: 1.5px;
            transition: all 0.3s;
        }
        .stButton > button:hover {
            background: var(--secondary) !important;
            color: var(--bg) !important;
            box-shadow: 0 0 20px var(--secondary-glow) !important;
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
        <a href="#lagent-enhance" class="back-to-top">↑</a>
    """, unsafe_allow_html=True)


def main():
    st.set_page_config(
        page_title="Deep AI Enhancer",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    apply_theme()

    st.markdown(
        '<div class="brand" id="lagent-enhance">'
        "<h1>Deep AI<b>Enhance</b></h1>"
        "</div>",
        unsafe_allow_html=True,
    )

    if not HAS_MODULES:
        st.error(f"Failed to load modules: {_ERR}")
        return

    # Session defaults
    if "HF_API_TOKEN" not in st.session_state:
        st.session_state.HF_API_TOKEN = os.getenv("HF_API_TOKEN", "")
    if "enh_pairs" not in st.session_state:
        st.session_state.enh_pairs = []

    enhancer = ImageEnhancer()

    # Layout
    c_up, c_cfg = st.columns([2, 1], gap="medium")
    
    with c_up:
        st.markdown('<p class="sec-title">Upload Product Images</p>', unsafe_allow_html=True)
        files = st.file_uploader(
            "Select images to enhance via Hugging Face AI",
            type=["png", "jpg", "jpeg", "webp"],
            accept_multiple_files=True,
            key="enh_upload",
            label_visibility="collapsed"
        )

    with c_cfg:
        st.markdown('<div class="card-hdr">AI Configuration</div>', unsafe_allow_html=True)
        
        # Pull token from session/env instead of input
        hf_token = st.session_state.get("HF_API_TOKEN") or os.getenv("HF_API_TOKEN")
        
        if hf_token:
            st.success("Hugging Face Token Active (from Settings)")
        else:
            st.warning("HF Token missing. Go to Settings to add it.")

        output_fmt = st.selectbox("Output Format", ["PNG", "JPEG", "WEBP"])

        if st.button("✨ Deep AI Enhance All", use_container_width=True) and files:
            if not hf_token:
                st.error("Please provide a Hugging Face Token in the Settings page.")
            else:
                bar = st.progress(0)
                status_box = st.empty()
                pairs = []

                for i, f in enumerate(files):
                    raw = f.getvalue()
                    orig_img = Image.open(io.BytesIO(raw)).convert("RGB")
                    
                    status_box.info(f"Processing {f.name} via Deep AI (4x Upscale)...")
                    
                    # Call HF API
                    enhanced_img = enhancer.enhance_pil(orig_img, token=hf_token)
                    
                    if enhanced_img:
                        pairs.append((f.name, orig_img, enhanced_img))
                    
                    bar.progress((i + 1) / len(files))
                
                status_box.success("4x Deep AI Enhancement complete!")
                st.session_state.enh_pairs = pairs
                st.rerun()

    # Results display
    _render_comparison_list(output_fmt)


def _render_comparison_list(fmt="PNG"):
    pairs = st.session_state.get("enh_pairs", [])
    if not pairs:
        return

    st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)
    st.markdown(f'<div class="card-hdr">AI Processed Results ({len(pairs)})</div>', unsafe_allow_html=True)

    for i, (name, orig, enhanced) in enumerate(pairs):
        col_info, col_dl = st.columns([3, 1])
        with col_info:
            st.markdown(
                f'<div style="font-size:0.8rem; font-weight:600; color:var(--text);">{name}</div>'
                f'<div class="analysis-chip">Before: {orig.size[0]}x{orig.size[1]}</div>'
                f'<div class="analysis-chip" style="color:var(--primary);">After: {enhanced.size[0]}x{enhanced.size[1]} (Deep AI)</div>',
                unsafe_allow_html=True
            )
        with col_dl:
            img_bytes = io.BytesIO()
            enhanced.save(img_bytes, format=fmt)
            st.download_button(
                "Download",
                data=img_bytes.getvalue(),
                file_name=f"ai_enhanced_{name}.{fmt.lower()}",
                mime=f"image/{fmt.lower()}",
                key=f"dl_indiv_{i}",
                use_container_width=True
            )
        
        # Comparison
        image_comparison(
            img1=orig,
            img2=enhanced,
            label1="Original",
            label2="Deep AI (SwinIR)",
            show_labels=True,
            make_responsive=True,
            in_memory=True
        )
        st.markdown("<hr style='border:0; border-top:1px solid var(--border); margin: 1.5rem 0;'>", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
