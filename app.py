import streamlit as st
import os
import sys
import requests
import time
import re
import io
import zipfile
from dotenv import load_dotenv

# Path Config
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Core Modules
_CORE_ERROR = ""
try:
    from pdf_processor import ProductPDFExtractor
    from scraper import TunisianScraper
    from desc_writer import DescriptionWriter
    from n8n_bridge import N8NBridge
    from image_enhancer import ImageEnhancer
    HAS_CORE = True
except Exception as e:
    HAS_CORE = False
    _CORE_ERROR = str(e)

load_dotenv()


# ──────────────────────────────────────────────
# UTILS
# ──────────────────────────────────────────────

def clean_cache():
    st.cache_data.clear()
    st.cache_resource.clear()


# ──────────────────────────────────────────────
# THEME - Professional dark design system
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
            --accent: #ff00ff;
            --bg: #050505;
            --surface: rgba(16, 16, 24, 0.7);
            --surface-bright: rgba(26, 26, 36, 0.8);
            --border: rgba(188, 19, 254, 0.3);
            --border-bright: rgba(0, 243, 255, 0.5);
            --text: #e6edf3;
            --text-secondary: #8b949e;
            --text-muted: #484f58;
            --green: #3fb950;
            --red: #f85149;
            --radius: 4px;
            --radius-lg: 8px;
        }

        /* Base App Styling */
        html, body, [data-testid="stAppViewContainer"],
        .stApp, [data-testid="stMainBlockContainer"] {
            font-family: 'Inter', sans-serif;
            background-color: var(--bg) !important;
            background-image: 
                radial-gradient(circle at 50% 50%, rgba(188, 19, 254, 0.05) 0%, transparent 50%),
                linear-gradient(rgba(188, 19, 254, 0.02) 1px, transparent 1px),
                linear-gradient(90deg, rgba(188, 19, 254, 0.02) 1px, transparent 1px);
            background-size: 100% 100%, 30px 30px, 30px 30px;
            color: var(--text);
        }

        #MainMenu, footer { display: none !important; }

        /* Sidebar Styling */
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
        [data-testid="stSidebarNav"] li {
            margin-bottom: 5px;
            border-radius: 4px;
            transition: all 0.3s;
        }
        [data-testid="stSidebarNav"] li:hover {
            background: rgba(188, 19, 254, 0.1);
            box-shadow: inset 0 0 10px rgba(188, 19, 254, 0.2);
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
        <a href="#lagent-ai" class="back-to-top">↑</a>
    """, unsafe_allow_html=True)



# ──────────────────────────────────────────────
# STEPPER NAVIGATION
# ──────────────────────────────────────────────

STEPS = [("1", "Upload"), ("2", "Configure"), ("3", "Process"), ("4", "Results")]
STEP_INDEX = {"import": 0, "config": 1, "exec": 2, "results": 3}


def render_stepper(current_ui):
    idx = STEP_INDEX.get(current_ui, 0)
    parts = []
    for i, (num, label) in enumerate(STEPS):
        if i > 0:
            line_cls = "done" if i <= idx else ""
            parts.append(f'<div class="step-line {line_cls}"></div>')
        if i < idx:
            cls = "done"
        elif i == idx:
            cls = "active"
        else:
            cls = ""
        parts.append(
            f'<div class="step {cls}">'
            f'<div class="step-num">{num}</div>{label}</div>'
        )
    st.markdown(f'<div class="stepper">{"".join(parts)}</div>', unsafe_allow_html=True)


# ──────────────────────────────────────────────
# VIEW: UPLOAD
# ──────────────────────────────────────────────

def view_import():
    _, center, _ = st.columns([1, 2, 1])
    with center:
        st.markdown('<p class="sec-title">Upload Catalog</p>', unsafe_allow_html=True)
        st.markdown(
            '<p class="sec-desc">Import a product catalog PDF to extract references and specifications.</p>',
            unsafe_allow_html=True,
        )

        pdf = st.file_uploader(
            "Drag and drop a PDF catalog",
            type=["pdf"],
            help="Supported: PDF product catalogs with tabular data",
        )

        if pdf:
            size_kb = pdf.size / 1024
            st.markdown(
                f'<div class="file-chip"><strong>{pdf.name}</strong> &mdash; {size_kb:,.0f} KB ready</div>',
                unsafe_allow_html=True,
            )
            if st.button("Download", use_container_width=True):
                with open("temp_catalog.pdf", "wb") as f:
                    f.write(pdf.getvalue())
                with st.status("Scanning catalog...", expanded=True) as status:
                    st.write("Parsing PDF pages and extracting product tables...")
                    extractor = ProductPDFExtractor("temp_catalog.pdf")
                    st.session_state.db = extractor.extract_all()
                    total = sum(len(v) for v in st.session_state.db.values())
                    status.update(
                        label=f"Done -- {total} products in {len(st.session_state.db)} categories",
                        state="complete",
                    )
                    time.sleep(0.6)
                st.session_state.ui = "config"
                st.rerun()


# ──────────────────────────────────────────────
# VIEW: CONFIGURE
# ──────────────────────────────────────────────

def _on_select_all_change():
    """Callback: sync all individual checkboxes when Select All toggles."""
    items = st.session_state.db.get(st.session_state.get("_active_cat", ""), [])
    val = st.session_state.get("select_all", False)
    for n in items:
        st.session_state[f"cb_{n['reference']}"] = val


def view_config():
    st.markdown('<p class="sec-title">Configure Synthesis</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="sec-desc">'
        'Choose a category, select products, and optionally paste a style reference for the AI writer.'
        '</p>',
        unsafe_allow_html=True,
    )

    col_settings, col_products = st.columns([1, 2], gap="large")

    # ── Left: settings ──
    with col_settings:
        with st.container(border=True):
            st.markdown('<div class="card-hdr">Settings</div>', unsafe_allow_html=True)

            categories = [c for c in st.session_state.db.keys() if c.strip()]
            if not categories:
                categories = ["GENERAL"]
            
            cat = st.selectbox("Category", categories)
            st.session_state["_active_cat"] = cat

            dna = st.text_area(
                "Style reference (optional)",
                height=170,
                placeholder="Paste an example product description here to guide the AI tone and structure...",
                help="The AI will mimic this text's tone and structure when writing descriptions.",
            )

            auto_enhance = st.checkbox(
                "Auto-enhance images (1024x1024)",
                value=st.session_state.get("auto_enhance", False),
                key="auto_enhance",
                help="Automatically upscale scraped images to 1024x1024.",
            )
            
            if auto_enhance:
                enh_engine = st.radio("Engine", ["Local (Fast)", "Cloud (AI)"], horizontal=True, key="enh_engine")
                if enh_engine == "Local (Fast)":
                    st.selectbox(
                        "Enhancement Profile",
                        ["balanced", "screenshot", "photography", "print", "social"],
                        index=0,
                        key="enh_profile",
                        help="Choose the style of enhancement. 'screenshot' is best for sharp UI/text."
                    )
                else:
                    st.selectbox(
                        "Cloud Model",
                        ["falai/topaz-image-upscaler@latest", "infsh/real-esrgan@latest"],
                        index=0,
                        key="cloud_model",
                        help="Professional AI models via inference.sh. Requires INFSH_API_KEY."
                    )

            st.checkbox(
                "Use n8n pipeline",
                value=st.session_state.get("use_n8n", False),
                key="use_n8n",
                help="Send data and images to n8n webhook for external processing.",
            )

            st.markdown("<div style='height:0.25rem'></div>", unsafe_allow_html=True)
            st.markdown('<div class="ghost-btn">', unsafe_allow_html=True)
            if st.button("Back to Upload", use_container_width=True, key="btn_back"):
                clean_cache()
                st.session_state.ui = "import"
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

    # ── Right: product selection ──
    with col_products:
        with st.container(border=True):
            items = st.session_state.db.get(cat, [])
            st.markdown(
                f'<div class="card-hdr">Products -- {cat} ({len(items)} items)</div>',
                unsafe_allow_html=True,
            )

            if not items:
                st.info("No products found in this category.")
            else:
                st.checkbox(
                    "Select all products",
                    key="select_all",
                    on_change=_on_select_all_change,
                )

                targets = []
                for n in items:
                    ref = n["reference"]
                    desig = n.get("designation", "")
                    color = n.get("color", "")
                    label = ref
                    if desig:
                        label += f" -- {desig}"
                    if color:
                        label += f" ({color})"

                    # Default to False unless session already has a value
                    if f"cb_{ref}" not in st.session_state:
                        st.session_state[f"cb_{ref}"] = False

                    checked = st.checkbox(label, key=f"cb_{ref}")
                    if checked:
                        targets.append(n)

                st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

                col_action, col_count = st.columns([3, 1])
                with col_action:
                    if targets:
                        if st.button(
                            f"Generate Descriptions ({len(targets)})",
                            use_container_width=True,
                            key="btn_synth",
                        ):
                            st.session_state.out = []
                            st.session_state.queue = targets
                            st.session_state.active_dna = dna
                            st.session_state.ui = "exec"
                            st.rerun()
                    else:
                        st.caption("Select at least one product to continue.")
                with col_count:
                    st.markdown(
                        f'<div style="text-align:right;padding-top:8px;font-size:0.78rem;'
                        f'color:var(--text-secondary);font-family:JetBrains Mono,monospace">'
                        f'{len(targets)}/{len(items)}</div>',
                        unsafe_allow_html=True,
                    )


# ──────────────────────────────────────────────
# VIEW: PROCESSING
# ──────────────────────────────────────────────

def view_exec():
    _, center, _ = st.columns([1, 3, 1])
    with center:
        st.markdown('<p class="sec-title">Processing Products</p>', unsafe_allow_html=True)
        st.markdown(
            '<p class="sec-desc">'
            'Scraping 7 Tunisian retailer sites and generating AI descriptions. This may take a few minutes.'
            '</p>',
            unsafe_allow_html=True,
        )

        total = len(st.session_state.queue)
        bar = st.progress(0, text=f"0 / {total} products completed")
        log = st.empty()

        scraper = TunisianScraper()
        writer = DescriptionWriter(
            api_key=st.session_state.get("OPENROUTER_API_KEY"),
            model=st.session_state.get("OPENROUTER_MODEL")
        )

        # Auto-enhance + n8n integration
        do_enhance = st.session_state.get("auto_enhance", False)
        use_n8n = st.session_state.get("use_n8n", False)
        enhancer = ImageEnhancer() if do_enhance else None
        bridge = N8NBridge() if use_n8n else None

        statuses = []
        for i, target in enumerate(st.session_state.queue):
            ref = target["reference"]

            # Update live log
            entries = list(statuses)
            entries.append(f'<div class="st-item proc">Fetching: <strong>{ref}</strong> (7 sites)</div>')
            log.markdown("".join(entries), unsafe_allow_html=True)

            web = scraper.fetch_all(ref, target["designation"], target.get("color"))

            if web:
                # n8n: send product data to webhook if configured
                if bridge and bridge.is_configured:
                    entries_n8n = list(statuses)
                    entries_n8n.append(
                        f'<div class="st-item proc">Sending to n8n: <strong>{ref}</strong></div>'
                    )
                    log.markdown("".join(entries_n8n), unsafe_allow_html=True)
                    bridge.send_product_data(web)

                # Auto-enhance images if enabled
                if do_enhance and web.get("images"):
                    entries_enh = list(statuses)
                    entries_enh.append(
                        f'<div class="st-item proc">Enhancing images: <strong>{ref}</strong></div>'
                    )
                    log.markdown("".join(entries_enh), unsafe_allow_html=True)

                    enhanced_imgs = []
                    # If n8n is also enabled, we could potentially get enhanced images FROM n8n
                    # but for now let's stick to local enhancement or n8n enhancement logic
                    
                    profile = st.session_state.get("enh_profile", "balanced")
                    engine = st.session_state.get("enh_engine", "Local (Fast)")
                    cloud_model = st.session_state.get("cloud_model", "falai/topaz-image-upscaler@latest")
                    
                    for img_url in web["images"][:6]:
                        enh_data = None
                        if bridge and bridge.is_configured:
                            # Try n8n first if selected
                            enh_data = bridge.send_image_for_enhancement(img_url, ref, web.get("source", ""))
                        
                        if not enh_data and enhancer:
                            if engine == "Cloud (AI)":
                                # Try cloud
                                enh = enhancer.enhance_cloud(img_url, app_id=cloud_model)
                                if enh:
                                    enh_data = enhancer.to_bytes(enh, fmt="PNG")
                            
                            # Fallback to local if cloud fails or Local is selected
                            if not enh_data:
                                enh = enhancer.enhance_from_url(img_url, profile=profile)
                                if enh:
                                    enh_data = enhancer.to_bytes(enh, fmt="PNG")
                        
                        if enh_data:
                            enhanced_imgs.append(enh_data)
                    
                    web["enhanced_images"] = enhanced_imgs

                desc = ""
                for chunk in writer.write_description_stream(web, st.session_state.active_dna):
                    desc += chunk
                
                # --- AI FALLBACK: If API fails, use raw site description ---
                if not desc or "❌ ERROR" in desc or len(desc) < 50:
                    print(f"[LOG]   AI failed or returned error. Falling back to site description for {ref}")
                    desc = web.get("specs", "Description non disponible.")
                    if web.get("url"):
                        desc += f"\n\n🔗 **Source:** [{web.get('source', 'Site Web')}]({web.get('url')})"

                st.session_state.out.append({"id": ref, "data": web, "desc": desc})
                st.session_state.img_ptr[ref] = 0

                sources = web.get("all_sources", [web.get("source", "")])
                src_str = ", ".join(sources) if len(sources) > 1 else sources[0] if sources else ""
                statuses.append(f'<div class="st-item ok">Done: {ref} ({src_str})</div>')
            else:
                st.session_state.out.append({"id": ref, "failed": True})
                statuses.append(f'<div class="st-item fail">Failed: {ref}</div>')

            bar.progress((i + 1) / total, text=f"{i + 1} / {total} products completed")

        # Final log
        log.markdown("".join(statuses), unsafe_allow_html=True)
        time.sleep(0.5)

        st.session_state.ui = "results"
        st.rerun()


# ──────────────────────────────────────────────
# VIEW: RESULTS
# ──────────────────────────────────────────────

def view_results():
    ok = sum(1 for r in st.session_state.out if not r.get("failed"))
    fail = sum(1 for r in st.session_state.out if r.get("failed"))

    st.markdown('<p class="sec-title">Results</p>', unsafe_allow_html=True)
    st.markdown(
        f'<p class="sec-desc">'
        f'{ok} product{"s" if ok != 1 else ""} processed successfully'
        f'{f", {fail} failed" if fail else ""}.'
        f'</p>',
        unsafe_allow_html=True,
    )

    # ── Action bar ──
    c1, c2, _ = st.columns([1, 1.2, 4])
    with c1:
        st.markdown('<div class="ghost-btn">', unsafe_allow_html=True)
        if st.button("New Batch", use_container_width=True, key="btn_new"):
            st.session_state.ui = "config"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    with c2:
        if ok > 0:
            zip_data = _prepare_download_zip()
            st.download_button(
                "Download All (ZIP)",
                data=zip_data,
                file_name=f"product_export_{int(time.time())}.zip",
                mime="application/zip",
                use_container_width=True,
                key="btn_download_zip"
            )

    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

    # ── Product cards ──
    for item in st.session_state.out:
        ref = item["id"]

        # Failed product
        if item.get("failed"):
            with st.container(border=True):
                st.markdown(f'<div class="result-ref">{ref}</div>', unsafe_allow_html=True)
                st.error(
                    "Could not find this product on any retailer site. "
                    "Verify the reference and try again."
                )
            continue

        # Successful product
        res = item["data"]
        with st.container(border=True):
            st.markdown(f'<div class="result-ref">{ref}</div>', unsafe_allow_html=True)

            img_col, desc_col = st.columns([1, 1.6], gap="large")

            # ── Images + price ──
            with img_col:
                # Use enhanced images if they exist and we are viewing them
                has_enhanced = "enhanced_images" in res and res["enhanced_images"]
                imgs = res["enhanced_images"] if has_enhanced else res.get("images", [])
                
                if imgs:
                    ptr = st.session_state.img_ptr.get(ref, 0)
                    if ptr >= len(imgs):
                        ptr = 0

                    st.image(imgs[ptr], use_container_width=True)
                    if has_enhanced:
                        st.markdown(
                            '<div style="font-size:0.65rem;color:var(--green);margin-top:-10px;margin-bottom:10px">'
                            '✨ Enhanced 1024x1024 LANCZOS</div>',
                            unsafe_allow_html=True
                        )

                    # Thumbnail navigation
                    if len(imgs) > 1:
                        max_thumbs = min(len(imgs), 6)
                        thumb_cols = st.columns(max_thumbs)
                        for idx in range(max_thumbs):
                            with thumb_cols[idx]:
                                is_active = idx == ptr
                                st.markdown('<div class="thumb-btn">', unsafe_allow_html=True)
                                if st.button(
                                    f"View {idx + 1}" if not is_active else f"[{idx + 1}]",
                                    key=f"t_{ref}_{idx}",
                                    use_container_width=True,
                                ):
                                    st.session_state.img_ptr[ref] = idx
                                    st.rerun()
                                st.markdown('</div>', unsafe_allow_html=True)

                st.markdown(f'<div class="price-tag">{res["price"]}</div>', unsafe_allow_html=True)
                
                # Show all sources
                sources = res.get("all_sources", [res.get("source", "Unknown")])
                src_badges = "".join([f'<span class="meta-badge">{s}</span>' for s in sources])
                
                st.markdown(
                    f'<div class="meta-row">'
                    f'<span class="meta-badge">SKU: {res["sku"]}</span>'
                    f'{src_badges}'
                    f'</div>',
                    unsafe_allow_html=True,
                )

                if res.get("url"):
                    st.markdown(
                        f'<a href="{res["url"]}" target="_blank" '
                        f'style="font-size:0.78rem;color:var(--primary);text-decoration:none;">'
                        f'View Original Source</a>',
                        unsafe_allow_html=True,
                    )

            # ── Description ──
            with desc_col:
                st.markdown('<div class="desc-hdr">Generated Description</div>', unsafe_allow_html=True)
                st.markdown(item["desc"])

                st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

                dl1, dl2, dl3 = st.columns([1, 1, 1.2])
                with dl1:
                    st.download_button(
                        "Text",
                        data=item["desc"],
                        file_name=f"{ref}_description.txt",
                        mime="text/plain",
                        use_container_width=True,
                        key=f"dl_{ref}",
                    )
                with dl2:
                    st.download_button(
                        "Markdown",
                        data=item["desc"],
                        file_name=f"{ref}_description.md",
                        mime="text/markdown",
                        use_container_width=True,
                        key=f"dlmd_{ref}",
                    )
                with dl3:
                    if has_enhanced:
                        ptr = st.session_state.img_ptr.get(ref, 0)
                        st.download_button(
                            "Enhanced Image",
                            data=res["enhanced_images"][ptr],
                            file_name=f"{ref}_enhanced_{ptr+1}.png",
                            mime="image/png",
                            use_container_width=True,
                            key=f"dlimg_{ref}",
                        )
                    else:
                        st.markdown('<div class="ghost-btn">', unsafe_allow_html=True)
                        st.button("No Enhanced Img", disabled=True, use_container_width=True, key=f"noimg_{ref}")
                        st.markdown('</div>', unsafe_allow_html=True)



def _prepare_download_zip():
    """Create a ZIP archive in memory containing all successful results."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for res_item in st.session_state.out:
            if res_item.get("failed"):
                continue
            
            res = res_item["data"]
            # Naming: [Product Name] - [Color]
            title = res.get("title", res_item["id"])
            color = res.get("color_tag", "")
            base_name = title
            if color:
                base_name += f" - {color}"
            
            # Sanitize for filename
            safe_base = re.sub(r'[<>:"/\\|?*]', '_', base_name).strip()
            folder_path = f"{safe_base}/"
            
            # Save description
            z.writestr(f"{folder_path}description.txt", res_item["desc"])
            
            # Enhanced images if they exist, otherwise originals
            has_enhanced = "enhanced_images" in res and res["enhanced_images"]
            imgs = res["enhanced_images"] if has_enhanced else []
            
            if imgs:
                for idx, img_bytes in enumerate(imgs):
                    ext = "png"
                    z.writestr(f"{folder_path}{safe_base} - {idx + 1}.{ext}", img_bytes)
            else:
                # Fallback to downloading originals if no enhancement was done
                for idx, url in enumerate(res.get("images", [])):
                    try:
                        r = requests.get(url, timeout=5)
                        if r.status_code == 200:
                            ext = url.split('.')[-1].split('?')[0] or "jpg"
                            z.writestr(f"{folder_path}{safe_base} - {idx + 1}.{ext}", r.content)
                    except Exception:
                        pass
                        
    buf.seek(0)
    return buf.getvalue()


# ──────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────

def main():
    st.set_page_config(
        page_title="Lagent Agent",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    apply_theme()

    # Brand header
    st.markdown(
        '<div class="brand" id="lagent-ai">'
        "<h1>Lagent<b>AI</b></h1>"
        '<p class="sub">Catalog Processing Agent</p>'
        "</div>",
        unsafe_allow_html=True,
    )

    if not HAS_CORE:
        st.error(f"Failed to load core modules. Check `src/` directory.\n\n{_CORE_ERROR}")
        return

    # Session state defaults
    defaults = [
        ("ui", "import"),
        ("db", {}),
        ("out", []),
        ("img_ptr", {}),
        ("OPENROUTER_API_KEY", os.getenv("OPENROUTER_API_KEY", "")),
        ("OPENROUTER_MODEL", "openrouter/free")
    ]
    for key, default in defaults:
        if key not in st.session_state:
            st.session_state[key] = default

    # Navigation stepper
    render_stepper(st.session_state.ui)

    # Route to current view
    views = {
        "import": view_import,
        "config": view_config,
        "exec": view_exec,
        "results": view_results,
    }
    views.get(st.session_state.ui, view_import)()


if __name__ == "__main__":
    main()
