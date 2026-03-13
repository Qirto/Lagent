import streamlit as st
import sys
import os
import io
import requests
from PIL import Image
from streamlit_image_comparison import image_comparison

# Path setup
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

try:
    from src.image_enhancer import ImageEnhancer
    HAS_MODULES = True
except Exception as e:
    HAS_MODULES = False
    _ERR = str(e)


from src.theme import apply_theme

# ──────────────────────────────────────────────
# THEME & UI
# ──────────────────────────────────────────────

def clean_cache():
    st.cache_data.clear()
    st.cache_resource.clear()

def apply_custom_css():
    st.markdown("""
        <style>
        .analysis-chip {
            background: rgba(0, 243, 255, 0.1);
            border: 1px solid var(--primary);
            border-radius: 20px;
            padding: 4px 12px;
            font-size: 0.7rem;
            color: var(--primary);
            display: inline-block;
            margin-right: 10px;
            margin-bottom: 10px;
            font-family: 'JetBrains Mono', monospace;
        }
        </style>
    """, unsafe_allow_html=True)


def main():
    st.set_page_config(
        page_title="Deep AI Enhancer",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    apply_theme()
    apply_custom_css()

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
    hf_token = st.session_state.get("HF_API_TOKEN") or os.getenv("HF_API_TOKEN")

    # ── Tabs ──
    tab_upload, tab_url, tab_batch = st.tabs(["Manual Upload", "Image URL", "From Scraper"])

    # ──────────── TAB: Upload ────────────
    with tab_upload:
        c_up, c_cfg = st.columns([2, 1], gap="medium")
        
        with c_up:
            st.markdown('<p class="sec-title">Upload Product Images</p>', unsafe_allow_html=True)
            files = st.file_uploader(
                "Select images to enhance via Finegrain Neural AI (4x Upscale)",
                type=["png", "jpg", "jpeg", "webp"],
                accept_multiple_files=True,
                key="enh_upload",
                label_visibility="collapsed"
            )
            
            if files:
                st.markdown('<div style="margin-top: 1rem;"></div>', unsafe_allow_html=True)
                cols = st.columns(4)
                for idx, f in enumerate(files):
                    with cols[idx % 4]:
                        st.image(f, width="stretch", caption=f.name)

        with c_cfg:
            st.markdown('<div class="card-hdr">AI Configuration</div>', unsafe_allow_html=True)
            if hf_token:
                st.success("HF Token Active (from Settings)")
            else:
                st.warning("HF Token missing. Go to Settings to add it.")

            output_fmt = st.selectbox("Output Format", ["PNG", "JPEG", "WEBP"], key="fmt_up")

            if st.button("✨ Deep AI Enhance All", width="stretch", key="btn_up") and files:
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
                        
                        # Use generator for pacing feedback
                        result_gen = enhancer.enhance_pil_generator(orig_img, token=hf_token)
                        enhanced_img = None
                        
                        for res_packet in result_gen:
                            if isinstance(res_packet, dict):
                                if res_packet.get("status") == "waiting":
                                    status_box.warning(res_packet["msg"])
                                elif res_packet.get("status") == "back":
                                    status_box.success(res_packet["msg"])
                            elif res_packet is not None:
                                enhanced_img = res_packet
                        
                        if enhanced_img:
                            pairs.append((f.name, orig_img, enhanced_img))
                        else:
                            status_box.error(f"Finegrain AI processing failed for {f.name}.")
                        
                        bar.progress((i + 1) / len(files))
                    
                    status_box.success("4x Deep AI Enhancement complete!")
                    st.session_state.enh_pairs = pairs
                    st.rerun()

    # ──────────── TAB: URL ────────────
    with tab_url:
        url_input = st.text_input("Image URL", placeholder="https://...", key="enh_url")
        if url_input and st.button("Download & Enhance", key="btn_enh_url"):
            if not hf_token:
                st.error("Please provide a Hugging Face Token in the Settings page.")
            else:
                status_box = st.empty()
                with st.spinner("Processing via Hugging Face..."):
                    result_gen = enhancer.enhance_from_url(url_input, hf_token=hf_token)
                    enhanced_img = None
                    for res_packet in result_gen:
                        if isinstance(res_packet, dict):
                            if res_packet.get("status") == "waiting":
                                status_box.warning(res_packet["msg"])
                            elif res_packet.get("status") == "back":
                                status_box.success(res_packet["msg"])
                        elif res_packet is not None:
                            enhanced_img = res_packet

                    if enhanced_img:
                        resp = requests.get(url_input, timeout=10)
                        orig_img = Image.open(io.BytesIO(resp.content)).convert("RGB")
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
            
            if st.button(f"Enhance All {total_imgs} Images via Deep AI", width="stretch", key="btn_batch"):
                if not hf_token:
                    st.error("Please provide a Hugging Face Token in the Settings page.")
                else:
                    bar = st.progress(0)
                    status_box = st.empty()
                    all_pairs = []
                    processed = 0
                    for prod in ok_products:
                        for j, url in enumerate(prod.get("data", {}).get("images", [])):
                            processed += 1
                            status_box.info(f"Neural Upscaling: {prod['id']} (Img {j+1})")
                            
                            result_gen = enhancer.enhance_from_url(url, hf_token=hf_token)
                            enhanced = None
                            for res_packet in result_gen:
                                if isinstance(res_packet, dict):
                                    if res_packet.get("status") == "waiting":
                                        status_box.warning(res_packet["msg"])
                                    elif res_packet.get("status") == "back":
                                        status_box.success(res_packet["msg"])
                                elif res_packet is not None:
                                    enhanced = res_packet

                            if enhanced:
                                try:
                                    r = requests.get(url, timeout=10)
                                    orig = Image.open(io.BytesIO(r.content)).convert("RGB")
                                    all_pairs.append((f"{prod['id']}_{j+1}", orig, enhanced))
                                except: pass
                            bar.progress(processed / total_imgs)
                    st.session_state.enh_pairs = all_pairs
                    st.rerun()

    # Results display
    _render_comparison_list("PNG")


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
                f'<div class="analysis-chip">Original: {orig.size[0]}x{orig.size[1]}</div>'
                f'<div class="analysis-chip" style="color:var(--primary);">Enhanced: {enhanced.size[0]}x{enhanced.size[1]} (4x Deep AI)</div>',
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
            width="stretch"
            )
        
        # Comparison
        image_comparison(
            img1=orig,
            img2=enhanced,
            label1="Original",
            label2="Finegrain AI (4x)",
            show_labels=True,
            make_responsive=True,
            in_memory=True
        )
        st.markdown("<hr style='border:0; border-top:1px solid var(--border); margin: 1.5rem 0;'>", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
