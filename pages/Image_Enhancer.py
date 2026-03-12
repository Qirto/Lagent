import streamlit as st
import sys
import os
import io
import time
import zipfile
import requests
from PIL import Image
from streamlit_image_comparison import image_comparison

# Path setup
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    from image_enhancer import ImageEnhancer
    from n8n_bridge import N8NBridge
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
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

        :root {
            --primary: #7c6aef;
            --primary-hover: #9586f5;
            --primary-dim: rgba(124, 106, 239, 0.10);
            --bg: #0e1117;
            --surface: #161b22;
            --surface-raised: #1c2333;
            --border: #21262d;
            --border-light: #30363d;
            --text: #e6edf3;
            --text-secondary: #8b949e;
            --text-muted: #484f58;
            --green: #3fb950;
            --green-dim: rgba(63, 185, 80, 0.10);
            --amber: #d29922;
            --red: #f85149;
            --red-dim: rgba(248, 81, 73, 0.10);
            --radius: 6px;
            --radius-lg: 10px;
        }

        html, body, [data-testid="stAppViewContainer"],
        .stApp, [data-testid="stMainBlockContainer"] {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background-color: var(--bg) !important;
            color: var(--text);
        }

        #MainMenu, footer { display: none !important; }
        [data-testid="stSidebar"] {
            background-color: var(--surface) !important;
            border-right: 1px solid var(--border) !important;
        }
        [data-testid="stSidebarNav"] {
            background-color: var(--surface) !important;
        }

        /* ─── Compact Section headings ─── */
        .sec-title {
            font-size: 1rem; font-weight: 600; color: var(--text);
            margin: 0 0 1px 0;
        }
        .sec-desc {
            font-size: 0.78rem; color: var(--text-secondary);
            margin: 0 0 1rem 0; line-height: 1.4;
        }
        .card-hdr {
            font-size: 0.65rem; font-weight: 600; text-transform: uppercase;
            letter-spacing: 1px; color: var(--text-secondary);
            padding-bottom: 0.5rem; margin-bottom: 0.6rem;
            border-bottom: 1px solid var(--border);
        }

        /* ─── Flat Buttons ─── */
        .stButton > button {
            border-radius: var(--radius) !important;
            font-family: 'Inter', sans-serif !important;
            font-weight: 500 !important; font-size: 0.8rem !important;
            padding: 0.4rem 1rem !important;
            transition: all 0.1s ease !important;
            text-transform: none !important;
            background: var(--primary) !important;
            color: #fff !important; border: none !important;
            box-shadow: none !important;
        }
        .stButton > button:hover {
            background: var(--primary-hover) !important;
        }

        .ghost-btn button {
            background: var(--border) !important;
            color: var(--text-secondary) !important;
            border: none !important;
        }
        .ghost-btn button:hover {
            color: var(--text) !important;
            background: var(--border-light) !important;
        }

        .stDownloadButton > button {
            background: var(--surface-raised) !important;
            color: var(--text-secondary) !important;
            border: 1px solid var(--border-light) !important;
            font-size: 0.75rem !important;
            padding: 0.3rem 0.8rem !important;
        }

        /* ─── Compact Inputs ─── */
        .stTextInput > div > div, .stNumberInput > div > div, .stSelectbox > div > div {
            background-color: var(--surface) !important;
            border: 1px solid var(--border) !important;
            border-radius: var(--radius) !important;
            min-height: 32px !important;
        }
        
        .stSelectbox label, .stTextInput label, .stNumberInput label {
            font-size: 0.75rem !important;
            margin-bottom: 2px !important;
        }

        [data-testid="stFileUploader"] section {
            border: 1px dashed var(--border-light) !important;
            border-radius: var(--radius) !important;
            padding: 1rem !important;
        }

        .stProgress > div > div > div > div {
            background: var(--primary) !important;
            height: 4px !important;
        }

        .brand {
            text-align: left; padding: 0.5rem 0 1rem 0;
            display: flex; align-items: center; gap: 10px;
        }
        .brand h1 {
            font-size: 1.2rem; font-weight: 300; letter-spacing: 2px;
            color: var(--text); margin: 0; line-height: 1;
        }
        .brand h1 b { font-weight: 700; color: var(--primary); }

        .analysis-chip {
            padding: 4px 10px; border-radius: 4px; font-size: 0.7rem;
            font-family: 'JetBrains Mono', monospace;
            background: var(--surface-raised); border: 1px solid var(--border);
            color: var(--text-secondary); display: inline-block; margin-right: 5px;
        }

        ::-webkit-scrollbar { width: 4px; }
        ::-webkit-scrollbar-track { background: var(--bg); }
        ::-webkit-scrollbar-thumb { background: var(--border-light); border-radius: 2px; }
        </style>
    """, unsafe_allow_html=True)


# ──────────────────────────────────────────────
# IMAGE ENHANCER PAGE
# ──────────────────────────────────────────────

try:
    LANCZOS = Image.Resampling.LANCZOS
except (AttributeError, NameError):
    try:
        LANCZOS = Image.LANCZOS
    except (AttributeError, NameError):
        LANCZOS = 1


def main():
    st.set_page_config(
        page_title="Image Enhancer",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    apply_theme()

    col_brand, col_nav = st.columns([1, 2])
    with col_brand:
        st.markdown(
            '<div class="brand">'
            "<h1>Neural<b>Enhance</b></h1>"
            "</div>",
            unsafe_allow_html=True,
        )

    if not HAS_MODULES:
        st.error(f"Failed to load modules: {_ERR}")
        return

    # Session defaults
    if "enh_pairs" not in st.session_state:
        st.session_state.enh_pairs = [] # List of (filename, original_pil, enhanced_pil)

    # ── Tabs ──
    tab_upload, tab_url, tab_batch, tab_cloud, tab_n8n = st.tabs([
        "Manual", "URL", "From Scraper", "AI Cloud", "n8n"
    ])

    enhancer = ImageEnhancer()

    # ──────────── TAB: Upload ────────────
    with tab_upload:
        c_up, c_cfg = st.columns([2, 1], gap="medium")
        
        with c_up:
            st.markdown('<p class="sec-title">Upload Images</p>', unsafe_allow_html=True)
            files = st.file_uploader(
                "Select images to enhance",
                type=["png", "jpg", "jpeg", "webp"],
                accept_multiple_files=True,
                key="enh_upload",
                label_visibility="collapsed"
            )

        with c_cfg:
            st.markdown('<div class="card-hdr">Processing Settings</div>', unsafe_allow_html=True)
            profile = st.selectbox(
                "Enhancement Profile",
                ["balanced", "screenshot", "photography", "print", "social"],
                help="screenshot: Max clarity for text. photography: Natural look. social: Vibrant colors."
            )
            t_col1, t_col2 = st.columns(2)
            with t_col1:
                target_w = st.number_input("Target Width", value=1024, step=128)
            with t_col2:
                target_h = st.number_input("Target Height", value=1024, step=128)
            
            output_fmt = st.selectbox("Output Format", ["PNG", "JPEG", "WEBP"])

            if st.button("Enhance All", use_container_width=True) and files:
                enhancer.target_size = (target_w, target_h)
                bar = st.progress(0)
                pairs = []

                for i, f in enumerate(files):
                    raw = f.getvalue()
                    orig_img = Image.open(io.BytesIO(raw)).convert("RGB")
                    
                    # Enhancement phase
                    enhanced_img = enhancer.enhance(orig_img, profile=profile)
                    if enhanced_img:
                        pairs.append((f.name, orig_img, enhanced_img))
                    
                    bar.progress((i + 1) / len(files))
                
                st.session_state.enh_pairs = pairs
                st.rerun()

        _render_comparison_list(output_fmt)

    # ──────────── TAB: URL ────────────
    with tab_url:
        url_input = st.text_input("Image URL", placeholder="https://...", key="enh_url")
        if url_input and st.button("Download & Enhance", key="btn_enh_url"):
            with st.spinner("Processing..."):
                resp = requests.get(url_input, timeout=15)
                if resp.status_code == 200:
                    orig_img = Image.open(io.BytesIO(resp.content)).convert("RGB")
                    enhanced_img = enhancer.enhance(orig_img)
                    if enhanced_img:
                        fname = url_input.split("/")[-1].split("?")[0] or "image"
                        st.session_state.enh_pairs = [(fname, orig_img, enhanced_img)]
                        st.rerun()

    # ──────────── TAB: Batch (Scraper) ────────────
    with tab_batch:
        out = st.session_state.get("out", [])
        if not out:
            st.info("No scraped products found. Process products on the main page first.")
        else:
            ok_products = [r for r in out if not r.get("failed")]
            total_imgs = sum(len(r.get("data", {}).get("images", [])) for r in ok_products)
            
            st.markdown(f"Found **{len(ok_products)}** products with **{total_imgs}** total images.")
            
            with st.container(border=True):
                b_engine = st.radio("Engine", ["Local (Fast)", "Cloud (AI)"], horizontal=True, key="b_engine_tab")
                b_mod = None
                b_prof = "balanced"
                if b_engine == "Local (Fast)":
                    b_prof = st.selectbox("Profile", ["balanced", "screenshot", "photography", "social"], key="b_prof_tab")
                else:
                    b_mod = st.selectbox("Cloud Model", ["falai/topaz-image-upscaler@latest", "infsh/real-esrgan@latest"], key="b_mod_tab")

            if st.button(f"Enhance All {total_imgs} Images", use_container_width=True):
                bar = st.progress(0)
                all_pairs = []
                processed = 0
                for prod in ok_products:
                    for j, url in enumerate(prod.get("data", {}).get("images", [])):
                        processed += 1
                        try:
                            # Use requests directly to get original for comparison
                            r = requests.get(url, timeout=10)
                            if r.status_code == 200:
                                orig = Image.open(io.BytesIO(r.content)).convert("RGB")
                                
                                enhanced = None
                                if b_engine == "Cloud (AI)" and b_mod:
                                    enhanced = enhancer.enhance_cloud(url, app_id=b_mod)
                                
                                if not enhanced:
                                    enhanced = enhancer.enhance(orig, profile=b_prof)
                                
                                if enhanced:
                                    all_pairs.append((f"{prod['id']}_{j+1}", orig, enhanced))
                        except: pass
                        bar.progress(processed / total_imgs)
                st.session_state.enh_pairs = all_pairs
                st.rerun()

    # ──────────── TAB: Cloud ────────────
    with tab_cloud:
        cloud_key = st.text_input("inference.sh API Key", value=os.getenv("INFSH_API_KEY", ""), type="password")
        if st.button("Save API Key"):
            _save_env_key("INFSH_API_KEY", cloud_key)
        
        c_url = st.text_input("Public URL for Cloud AI", placeholder="https://...")
        if c_url and st.button("Upscale via Topaz AI"):
            with st.spinner("AI processing..."):
                os.environ["INFSH_API_KEY"] = cloud_key
                enhanced = enhancer.enhance_cloud(c_url)
                if enhanced:
                    r = requests.get(c_url)
                    orig = Image.open(io.BytesIO(r.content)).convert("RGB")
                    st.session_state.enh_pairs = [("cloud_ai", orig, enhanced)]
                    st.rerun()

    # ──────────── TAB: n8n ────────────
    with tab_n8n:
        n8n_url = st.text_input("Webhook URL", value=os.getenv("N8N_WEBHOOK_URL", ""))
        if st.button("Save n8n Config"):
            _save_env_key("N8N_WEBHOOK_URL", n8n_url)


def _render_comparison_list(fmt="PNG"):
    pairs = st.session_state.get("enh_pairs", [])
    if not pairs:
        return

    st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)
    st.markdown(f'<div class="card-hdr">Processed Results ({len(pairs)})</div>', unsafe_allow_html=True)

    # Multi-image download as ZIP
    if len(pairs) > 1:
        zip_buf = io.BytesIO()
        with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for name, _, enhanced in pairs:
                buf = io.BytesIO()
                enhanced.save(buf, format=fmt)
                zf.writestr(f"enhanced_{name}.{fmt.lower()}", buf.getvalue())
        
        st.download_button(
            f"Download All {len(pairs)} as ZIP",
            data=zip_buf.getvalue(),
            file_name="enhanced_batch.zip",
            mime="application/zip",
            use_container_width=True
        )
        st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

    # Render each pair with a slider
    for i, (name, orig, enhanced) in enumerate(pairs):
        # Header with info and individual download
        col_info, col_dl = st.columns([3, 1])
        with col_info:
            st.markdown(
                f'<div style="font-size:0.8rem; font-weight:600; color:var(--text);">{name}</div>'
                f'<div class="analysis-chip">Original: {orig.size[0]}x{orig.size[1]}</div>'
                f'<div class="analysis-chip" style="color:var(--primary);">Enhanced: {enhanced.size[0]}x{enhanced.size[1]}</div>',
                unsafe_allow_html=True
            )
        with col_dl:
            img_bytes = io.BytesIO()
            enhanced.save(img_bytes, format=fmt)
            st.download_button(
                "Download",
                data=img_bytes.getvalue(),
                file_name=f"enhanced_{name}.{fmt.lower()}",
                mime=f"image/{fmt.lower()}",
                key=f"dl_indiv_{i}",
                use_container_width=True
            )
        
        # The Slider
        orig_resized = orig.resize(enhanced.size, LANCZOS)
        
        image_comparison(
            img1=orig_resized,
            img2=enhanced,
            label1="Before",
            label2="After",
            show_labels=True,
            make_responsive=True,
            in_memory=True
        )
        
        st.markdown("<hr style='border:0; border-top:1px solid var(--border); margin: 1.5rem 0;'>", unsafe_allow_html=True)



def _save_env_key(key, value):
    env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    try:
        lines = []
        if os.path.exists(env_path):
            with open(env_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        
        found = False
        new_lines = []
        for line in lines:
            if line.startswith(f"{key}="):
                new_lines.append(f"{key}={value}\n")
                found = True
            else:
                new_lines.append(line)
        
        if not found:
            new_lines.append(f"{key}={value}\n")
            
        with open(env_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        st.success(f"Saved {key}")
    except Exception as e:
        st.error(f"Save failed: {e}")

if __name__ == "__main__":
    main()
