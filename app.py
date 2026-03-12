import streamlit as st
import os
import sys
import requests
import time
import re
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
            --radius: 8px;
            --radius-lg: 12px;
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

        /* ─── Stepper ─── */
        .stepper {
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 0;
            margin: 0 auto 2.25rem auto;
            max-width: 640px;
            padding: 0.75rem 0;
        }
        .step {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 6px 16px;
            font-size: 0.78rem;
            font-weight: 500;
            color: var(--text-muted);
            white-space: nowrap;
        }
        .step-num {
            width: 28px; height: 28px;
            border-radius: 50%;
            border: 1.5px solid var(--border-light);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.72rem;
            font-weight: 600;
            flex-shrink: 0;
            transition: all 0.2s;
        }
        .step.active { color: var(--primary-hover); }
        .step.active .step-num {
            background: var(--primary);
            border-color: var(--primary);
            color: #fff;
            box-shadow: 0 0 12px rgba(124, 106, 239, 0.35);
        }
        .step.done { color: var(--green); }
        .step.done .step-num {
            background: var(--green-dim);
            border-color: var(--green);
            color: var(--green);
        }
        .step-line {
            width: 36px; height: 1.5px;
            background: var(--border);
            flex-shrink: 0;
        }
        .step-line.done { background: var(--green); }

        /* ─── Section headings ─── */
        .sec-title {
            font-size: 1.15rem;
            font-weight: 600;
            color: var(--text);
            margin: 0 0 2px 0;
        }
        .sec-desc {
            font-size: 0.82rem;
            color: var(--text-secondary);
            margin: 0 0 1.5rem 0;
            line-height: 1.5;
        }

        /* ─── Card header ─── */
        .card-hdr {
            font-size: 0.68rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1.5px;
            color: var(--text-secondary);
            padding-bottom: 0.6rem;
            margin-bottom: 0.8rem;
            border-bottom: 1px solid var(--border);
        }

        /* ─── Buttons ─── */
        .stButton > button {
            border-radius: var(--radius) !important;
            font-family: 'Inter', sans-serif !important;
            font-weight: 600 !important;
            font-size: 0.82rem !important;
            padding: 0.55rem 1.4rem !important;
            transition: all 0.15s ease !important;
            text-transform: none !important;
            letter-spacing: 0.2px !important;
            background: var(--primary) !important;
            color: #fff !important;
            border: 1px solid var(--primary) !important;
        }
        .stButton > button:hover {
            background: var(--primary-hover) !important;
            border-color: var(--primary-hover) !important;
            box-shadow: 0 4px 14px rgba(124, 106, 239, 0.25) !important;
        }
        .stButton > button:active {
            transform: scale(0.98);
        }

        /* Secondary / ghost buttons */
        .ghost-btn button {
            background: transparent !important;
            color: var(--text-secondary) !important;
            border: 1px solid var(--border-light) !important;
        }
        .ghost-btn button:hover {
            color: var(--text) !important;
            border-color: var(--text-secondary) !important;
            background: var(--surface-raised) !important;
            box-shadow: none !important;
        }

        /* Thumb buttons for gallery */
        .thumb-btn button {
            background: var(--surface) !important;
            color: var(--text-secondary) !important;
            border: 1px solid var(--border) !important;
            padding: 0.3rem 0.5rem !important;
            font-size: 0.72rem !important;
            min-height: 0 !important;
        }
        .thumb-btn button:hover {
            border-color: var(--primary) !important;
            color: var(--primary) !important;
            box-shadow: none !important;
        }

        /* ─── Inputs ─── */
        .stTextInput > div > div,
        .stTextArea > div > textarea,
        .stSelectbox > div > div {
            background-color: var(--surface) !important;
            border: 1px solid var(--border) !important;
            border-radius: var(--radius) !important;
            color: var(--text) !important;
            font-family: 'Inter', sans-serif !important;
            font-size: 0.85rem !important;
        }
        .stTextInput > div > div:focus-within,
        .stTextArea > div > textarea:focus,
        .stSelectbox > div > div:focus-within {
            border-color: var(--primary) !important;
            box-shadow: 0 0 0 3px var(--primary-dim) !important;
        }

        /* Labels */
        .stTextInput label, .stTextArea label, .stSelectbox label,
        .stFileUploader label, .stCheckbox label {
            font-family: 'Inter', sans-serif !important;
            font-size: 0.82rem !important;
        }

        /* ─── File uploader ─── */
        [data-testid="stFileUploader"] section {
            border: 2px dashed var(--border-light) !important;
            border-radius: var(--radius-lg) !important;
            padding: 2rem !important;
            transition: border-color 0.2s !important;
        }
        [data-testid="stFileUploader"] section:hover {
            border-color: var(--primary) !important;
        }

        /* ─── Progress ─── */
        .stProgress > div > div > div > div {
            background: linear-gradient(90deg, var(--primary), var(--primary-hover)) !important;
            border-radius: 4px !important;
        }

        /* ─── Container borders ─── */
        [data-testid="stExpander"],
        div[data-testid="stVerticalBlockBorderWrapper"]:has(> div[data-testid="stVerticalBlock"] > div.element-container) {
            border-radius: var(--radius-lg) !important;
        }

        /* ─── Price tag ─── */
        .price-tag {
            font-size: 1.5rem;
            font-weight: 700;
            color: var(--green);
            font-family: 'JetBrains Mono', monospace;
            margin: 0.75rem 0 0.25rem 0;
        }

        /* ─── Meta badges ─── */
        .meta-row {
            display: flex;
            gap: 0.5rem;
            flex-wrap: wrap;
            margin-top: 0.5rem;
        }
        .meta-badge {
            font-size: 0.7rem;
            font-family: 'JetBrains Mono', monospace;
            color: var(--text-secondary);
            background: var(--bg);
            border: 1px solid var(--border);
            padding: 3px 10px;
            border-radius: 4px;
            display: inline-block;
        }

        /* ─── Result reference ─── */
        .result-ref {
            font-family: 'JetBrains Mono', monospace;
            font-weight: 600;
            font-size: 0.95rem;
            color: var(--primary-hover);
            margin-bottom: 0.5rem;
        }

        /* ─── Desc header ─── */
        .desc-hdr {
            font-size: 0.68rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: var(--text-secondary);
            margin-bottom: 0.75rem;
        }

        /* ─── File info chip ─── */
        .file-chip {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 10px 14px;
            background: var(--green-dim);
            border: 1px solid rgba(63,185,80,0.15);
            border-radius: var(--radius);
            margin: 0.75rem 0;
            font-size: 0.82rem;
            color: var(--green);
        }

        /* ─── Status items ─── */
        .st-item {
            padding: 6px 12px;
            border-radius: 6px;
            font-size: 0.8rem;
            margin-bottom: 3px;
        }
        .st-item.proc { background: var(--primary-dim); color: var(--primary-hover); }
        .st-item.ok   { background: var(--green-dim); color: var(--green); }
        .st-item.fail { background: var(--red-dim); color: var(--red); }

        /* ─── Brand ─── */
        .brand {
            text-align: center;
            padding: 1.25rem 0 0.5rem 0;
        }
        .brand h1 {
            font-size: 1.5rem;
            font-weight: 300;
            letter-spacing: 5px;
            color: var(--text);
            margin: 0;
            line-height: 1;
        }
        .brand h1 b {
            font-weight: 700;
            color: var(--primary);
        }
        .brand .sub {
            font-size: 0.65rem;
            color: var(--text-muted);
            letter-spacing: 2.5px;
            text-transform: uppercase;
            margin-top: 4px;
        }

        /* ─── Download button ─── */
        .stDownloadButton > button {
            background: transparent !important;
            color: var(--text-secondary) !important;
            border: 1px solid var(--border-light) !important;
        }
        .stDownloadButton > button:hover {
            color: var(--text) !important;
            border-color: var(--text-secondary) !important;
            box-shadow: none !important;
        }

        /* ─── Scrollbar ─── */
        ::-webkit-scrollbar { width: 6px; }
        ::-webkit-scrollbar-track { background: var(--bg); }
        ::-webkit-scrollbar-thumb { background: var(--border-light); border-radius: 3px; }
        </style>
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
            if st.button("Extract Products", use_container_width=True):
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

            categories = list(st.session_state.db.keys())
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
    c1, c2, _ = st.columns([1, 1, 4])
    with c1:
        st.markdown('<div class="ghost-btn">', unsafe_allow_html=True)
        if st.button("New Batch", use_container_width=True, key="btn_new"):
            st.session_state.ui = "config"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    with c2:
        if ok > 0:
            if st.button("Export All", use_container_width=True, key="btn_export"):
                _export_results()

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



def _export_results():
    """Export all successful results to disk."""
    with st.spinner("Exporting files..."):
        path = "synthesis_output"
        os.makedirs(path, exist_ok=True)
        exported = 0
        for res_item in st.session_state.out:
            if res_item.get("failed"):
                continue
            
            res = res_item["data"]
            safe_id = re.sub(r"[^A-Z0-9-]", "_", res_item["id"].upper())
            p_dir = os.path.join(path, safe_id)
            os.makedirs(p_dir, exist_ok=True)
            
            with open(os.path.join(p_dir, "description.txt"), "w", encoding="utf-8") as f:
                f.write(res_item["desc"])
            
            # Images
            i_dir = os.path.join(p_dir, "images")
            os.makedirs(i_dir, exist_ok=True)
            
            # Save enhanced if they exist
            if "enhanced_images" in res and res["enhanced_images"]:
                for idx, img_bytes in enumerate(res["enhanced_images"]):
                    with open(os.path.join(i_dir, f"enhanced_{idx + 1}.png"), "wb") as f:
                        f.write(img_bytes)
            
            # Save originals
            orig_dir = os.path.join(i_dir, "originals")
            os.makedirs(orig_dir, exist_ok=True)
            for idx, url in enumerate(res.get("images", [])):
                try:
                    r = requests.get(url, timeout=10)
                    if r.status_code == 200:
                        with open(os.path.join(orig_dir, f"view_{idx + 1}.jpg"), "wb") as f:
                            f.write(r.content)
                except Exception:
                    pass
            exported += 1
        st.success(f"Exported {exported} products to: {os.path.abspath(path)}")


# ──────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────

def main():
    st.set_page_config(
        page_title="Product AI Agent",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    apply_theme()

    # Brand header
    st.markdown(
        '<div class="brand">'
        "<h1>Product<b>AI</b></h1>"
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
