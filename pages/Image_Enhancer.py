import streamlit as st
import sys
import os
import io
import zipfile
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
            '<div class="brand" id="lagent-enhance">'
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
                        except Exception: 
                            pass
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
