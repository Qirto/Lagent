import streamlit as st
import os
import sys
import requests
import time
import re
import io
import zipfile
from dotenv import load_dotenv

import math
from src.theme import apply_theme, sanitize_html

# Path Config
sys.path.append(os.path.join(os.path.dirname(__file__)))

# Core Modules
_CORE_ERROR = ""
try:
    from src.pdf_processor import ProductPDFExtractor
    from src.scraper import TunisianScraper
    from src.desc_writer import DescriptionWriter
    from src.n8n_bridge import N8NBridge
    from src.image_enhancer import ImageEnhancer
    HAS_CORE = True
except Exception as e:
    # Try alternate path for local dev
    try:
        from pdf_processor import ProductPDFExtractor
        from scraper import TunisianScraper
        from desc_writer import DescriptionWriter
        from n8n_bridge import N8NBridge
        from image_enhancer import ImageEnhancer
        HAS_CORE = True
    except Exception as e2:
        HAS_CORE = False
        _CORE_ERROR = f"Path1: {e} | Path2: {e2}"

load_dotenv()


# ──────────────────────────────────────────────
# UTILS
# ──────────────────────────────────────────────

def clean_cache():
    st.cache_data.clear()
    st.cache_resource.clear()


# ──────────────────────────────────────────────
# MAIN UI ORCHESTRATION
# ──────────────────────────────────────────────

# ──────────────────────────────────────────────
# MAIN UI ORCHESTRATION (Cont.)
# ──────────────────────────────────────────────




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
            if st.button("Upload Catalog", width="stretch"):
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

            # ── Image Enhancement Toggle ──
            st.divider()
            st.markdown('<div style="font-family: \'Orbitron\', sans-serif; font-size: 0.9rem; margin-bottom: 10px;">Deep AI Enhancement</div>', unsafe_allow_html=True)
            
            st.session_state["auto_enhance"] = st.checkbox(
                "Enable Hugging Face AI Upscale",
                value=st.session_state.get("auto_enhance", True),
                help="Deep AI provides professional quality using Hugging Face SwinIR 4x."
            )
            st.session_state["hf_active"] = st.session_state["auto_enhance"]

            if st.session_state["auto_enhance"]:
                hf_token = st.session_state.get("HF_API_TOKEN") or os.getenv("HF_API_TOKEN")
                if not hf_token:
                    st.warning("HF Token missing. Go to Settings to add it.")
                else:
                    st.success("Hugging Face AI Active")
            
            st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

            st.checkbox(
                "Use n8n pipeline",
                value=st.session_state.get("use_n8n", False),
                key="use_n8n",
                help="Send data and images to n8n webhook for external processing.",
            )

            st.markdown("<div style='height:0.25rem'></div>", unsafe_allow_html=True)
            st.markdown('<div class="ghost-btn">', unsafe_allow_html=True)
            if st.button("Back to Upload", width='stretch', key="btn_back"):
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
                            width='stretch',
                            key="btn_synth",
                        ):
                            st.session_state.out = []
                            st.session_state.queue = targets
                            st.session_state.active_dna = dna
                            st.session_state.results_page = 0
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
        hf_active = st.session_state.get("hf_active", False)
        hf_token = st.session_state.get("HF_API_TOKEN")
        use_n8n = st.session_state.get("use_n8n", False)
        enhancer = ImageEnhancer(api_token=hf_token) if do_enhance else None
        bridge = N8NBridge() if use_n8n else None

        statuses = []
        waiting_box = st.empty() # For HF pacing messages

        for i, target in enumerate(st.session_state.queue):
            ref = target["reference"]

            # Update live log
            entries = list(statuses)
            entries.append(f'<div class="st-item proc">Fetching: <strong>{ref}</strong> (9 sites)</div>')
            log.markdown("".join(entries), unsafe_allow_html=True)

            web = scraper.fetch_all(ref, target["designation"], target.get("color"))

            if web:
                # NEW: Track category
                category_name = st.session_state.get("_active_cat", "GENERAL")
                
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
                    
                    for img_url in web["images"][:6]:
                        enh_data = None
                        
                        if enhancer:
                            if hf_active and hf_token:
                                # Deep AI Mode: We need to handle the generator for pacing messages
                                result_gen = enhancer.enhance_hf_api(img_url, hf_token)
                                
                                # Since it might yield dicts for waiting or return an Image
                                for res_packet in result_gen:
                                    if isinstance(res_packet, dict):
                                        if res_packet.get("status") == "waiting":
                                            waiting_box.warning(res_packet["msg"])
                                        elif res_packet.get("status") == "back":
                                            waiting_box.success(res_packet["msg"])
                                            time.sleep(1)
                                    elif res_packet is not None:
                                        # It's the PIL image
                                        enh_data = enhancer.to_bytes(res_packet, fmt="PNG")
                                        waiting_box.empty() # Clear waiting msg
                        
                        if enh_data:
                            enhanced_imgs.append(enh_data)
                    
                    web["enhanced_images"] = enhanced_imgs

                    # NEW: Generate tiny thumbnails for gallery to save bandwidth/lag
                    thumbnails = []
                    for img_bytes in enhanced_imgs:
                        try:
                            from PIL import Image
                            timg = Image.open(io.BytesIO(img_bytes))
                            timg.thumbnail((150, 150), Image.Resampling.LANCZOS)
                            tbuf = io.BytesIO()
                            timg.save(tbuf, format="JPEG", quality=70)
                            thumbnails.append(tbuf.getvalue())
                        except Exception:
                            pass
                    web["thumbnails"] = thumbnails


                # NEW: Separate short and long descriptions
                desc_short = writer.write_short_description(web)
                desc_long = writer.write_long_description(web, category_name)
                combined_desc = f"## Description Courte\n\n{desc_short}\n\n---\n\n## Description Longue\n\n{desc_long}"

                st.session_state.out.append({
                    "id": ref, 
                    "data": web, 
                    "desc_short": desc_short,
                    "desc_long": desc_long,
                    "desc": combined_desc,
                    "designation": target.get("designation", "") # For better diagnostics
                })
                st.session_state.img_ptr[ref] = 0
                st.session_state.zip_dirty = True # Mark ZIP for rebuild

                sources = web.get("all_sources", [web.get("source", "")])
                src_str = ", ".join(sources) if len(sources) > 1 else sources[0] if sources else ""
                statuses.append(f'<div class="st-item ok">Done: {ref} ({src_str})</div>')
            else:
                st.session_state.out.append({
                    "id": ref, 
                    "failed": True,
                    "designation": target.get("designation", "")
                })
                statuses.append(f'<div class="st-item fail">Failed: {ref}</div>')

            bar.progress((i + 1) / total, text=f"{i + 1} / {total} products completed")

        # Final log
        log.markdown("".join(statuses), unsafe_allow_html=True)
        # removed artificial delay

        st.session_state.ui = "results"
        st.rerun()


# ──────────────────────────────────────────────
# VIEW: RESULTS
# ──────────────────────────────────────────────

def _set_img_ptr(ref, idx):
    st.session_state.img_ptr[ref] = idx

def view_results():
    ok_results = [r for r in st.session_state.out if not r.get("failed")]
    fail_results = [r for r in st.session_state.out if r.get("failed")]
    
    ok = len(ok_results)
    fail = len(fail_results)

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
        if st.button("New Batch", width='stretch', key="btn_new", type="secondary"):
            st.session_state.ui = "config"
            st.rerun()
    with c2:
        if ok > 0:
            # NEW: ZIP Caching
            if "zip_cache" not in st.session_state or st.session_state.get("zip_dirty", True):
                with st.spinner("Compiling Neural Export..."):
                    st.session_state.zip_cache = _prepare_download_zip()
                    st.session_state.zip_dirty = False
            
            st.download_button(
                "Download All (ZIP)",
                data=st.session_state.zip_cache,
                file_name=f"product_export_{int(time.time())}.zip",
                mime="application/zip",
                width='stretch',
                key="btn_download_zip",
                type="primary"
            )

    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

    # NEW: Pagination for large lists
    PAGE_SIZE = 10
    total_pages = max(1, math.ceil(ok / PAGE_SIZE))
    
    if ok > PAGE_SIZE:
        if "results_page" not in st.session_state:
            st.session_state.results_page = 0
        
        col_p1, col_p2, col_p3 = st.columns([1, 2, 1])
        with col_p1:
            if st.button("<< Previous", disabled=st.session_state.results_page == 0, width='stretch'):
                st.session_state.results_page -= 1
                st.rerun()
        with col_p2:
            st.markdown(f'<div style="text-align:center; padding-top:10px; font-family:JetBrains Mono">Page {st.session_state.results_page + 1} / {total_pages}</div>', unsafe_allow_html=True)
        with col_p3:
            if st.button("Next >>", disabled=st.session_state.results_page >= total_pages - 1, width='stretch'):
                st.session_state.results_page += 1
                st.rerun()
        
        start_idx = st.session_state.results_page * PAGE_SIZE
        display_items = ok_results[start_idx : start_idx + PAGE_SIZE]
    else:
        display_items = ok_results

    # ── Product cards ──
    for item in display_items:
        ref = item["id"]
        res = item["data"]
        
        with st.container(border=True):
            st.markdown(f'<div class="result-ref">{sanitize_html(ref)}</div>', unsafe_allow_html=True)

            img_col, desc_col = st.columns([1, 1.6], gap="large")

            # ── Images + price ──
            with img_col:
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
                            'AI Enhanced 1024x1024</div>',
                            unsafe_allow_html=True
                        )

                    # Thumbnail navigation
                    if len(imgs) > 1:
                        thumbs = res.get("thumbnails", imgs)
                        max_thumbs = min(len(thumbs), 6)
                        
                        if max_thumbs > 0:
                            st.markdown('<div style="font-size: 0.75rem; color: var(--text-muted); margin-bottom: 5px; font-family: \'JetBrains Mono\', monospace;">GALLERY:</div>', unsafe_allow_html=True)
                            thumb_cols = st.columns(max_thumbs)
                            for idx in range(max_thumbs):
                                with thumb_cols[idx]:
                                    is_active = idx == ptr
                                    st.image(thumbs[idx], use_container_width=True)
                                    st.markdown('<div class="thumb-btn">', unsafe_allow_html=True)
                                    btn_type = "primary" if is_active else "secondary"
                                    label = "SEL" if is_active else "View"
                                    st.button(
                                        label,
                                        key=f"t_{ref}_{idx}",
                                        width='stretch',
                                        type=btn_type,
                                        on_click=_set_img_ptr,
                                        args=(ref, idx)
                                    )
                                    st.markdown('</div>', unsafe_allow_html=True)

                st.markdown(f'<div class="price-tag">{sanitize_html(res["price"])}</div>', unsafe_allow_html=True)
                
                sources = res.get("all_sources", [res.get("source", "Unknown")])
                src_badges = "".join([f'<span class="meta-badge">{sanitize_html(s)}</span>' for s in sources])
                st.markdown(f'<div class="meta-row"><span class="meta-badge">SKU: {sanitize_html(res["sku"])}</span>{src_badges}</div>', unsafe_allow_html=True)

                if res.get("url"):
                    st.markdown(f'<a href="{res["url"]}" target="_blank" style="font-size:0.78rem;color:var(--primary);text-decoration:none;">View Source</a>', unsafe_allow_html=True)

            # ── Description ──
            with desc_col:
                tab_short, tab_long = st.tabs(["Description Courte", "Description Longue"])
                with tab_short:
                    st.markdown(f'<div class="desc-content">{item.get("desc_short", item["desc"])}</div>', unsafe_allow_html=True)
                with tab_long:
                    st.markdown(f'<div class="desc-content">{item.get("desc_long", item["desc"])}</div>', unsafe_allow_html=True)

                dl1, dl2, dl3 = st.columns([1, 1, 1])
                with dl1:
                    st.download_button("Text (.txt)", item["desc"], f"{ref}_desc.txt", "text/plain", width='stretch', key=f"dl_{ref}")
                with dl2:
                    st.download_button("MD (.md)", item["desc"], f"{ref}_desc.md", "text/markdown", width='stretch', key=f"dlmd_{ref}")
                with dl3:
                    if has_enhanced:
                        ptr = st.session_state.img_ptr.get(ref, 0)
                        st.download_button("Img (.png)", res["enhanced_images"][ptr], f"{ref}_enhanced.png", "image/png", width='stretch', key=f"dlimg_{ref}", type="primary")
                    else:
                        st.button("No Enhanced", disabled=True, width='stretch', key=f"noimg_{ref}")

    # ── Failed items at the bottom ──
    if fail > 0:
        st.markdown("---")
        st.subheader("Failed to Match")
        for item in fail_results:
            with st.container(border=True):
                st.markdown(f'<div style="color:var(--red)"><strong>{sanitize_html(item["id"])}</strong> - {sanitize_html(item.get("designation", "Unknown Product"))}</div>', unsafe_allow_html=True)
                st.caption("Product not found on retailer sites. Verify reference.")


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
            
            # Save descriptions
            z.writestr(f"{folder_path}description_courte.txt", res_item.get("desc_short", res_item["desc"]))
            z.writestr(f"{folder_path}description_longue.txt", res_item.get("desc_long", res_item["desc"]))
            z.writestr(f"{folder_path}combined_description.txt", res_item["desc"])
            
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
        '<div class="brand" id="lagent-ai" style="text-align: center; margin-bottom: 2rem; padding: 2rem; border-bottom: 2px solid var(--border); box-shadow: var(--neu-shadow); background: var(--bg-elevated);">'
        '<h1 style="font-size: 3.5rem; margin-bottom: 0; color: #f8fafc; text-shadow: 0 0 15px rgba(0, 243, 255, 0.4); font-family: \'Orbitron\', sans-serif; letter-spacing: 2px;">'
        'LAGENT<b style="color: #00f3ff;">//AI</b></h1>'
        '<p class="sub" style="font-family: \'JetBrains Mono\', monospace; color: #ff00ff; font-size: 1rem; letter-spacing: 4px; text-transform: uppercase; margin-top: 5px; text-shadow: 0 0 8px rgba(255, 0, 255, 0.4);">'
        '>> Catalog_Processing_Agent_v2.0</p>'
        '</div>',
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
        ("zip_dirty", True),
        ("results_page", 0),
        ("OPENROUTER_API_KEY", os.getenv("OPENROUTER_API_KEY", "")),
        ("OPENROUTER_MODEL", os.getenv("OPENROUTER_MODEL", "openrouter/free")),
        ("HF_API_TOKEN", os.getenv("HF_API_TOKEN", ""))
    ]
    for key, default in defaults:
        if key not in st.session_state:
            st.session_state[key] = default

    # NEW: Browser localStorage bridge (Pull keys from browser if session is empty)
    import streamlit.components.v1 as components
    components.html("""
        <script>
        const keys = {
            'lagent_openrouter_key': 'OPENROUTER_API_KEY',
            'lagent_openrouter_model': 'OPENROUTER_MODEL',
            'lagent_hf_token': 'HF_API_TOKEN'
        };
        const params = new URLSearchParams(window.location.search);
        let needsUpdate = false;
        for (const [lsKey, stKey] of Object.entries(keys)) {
            const val = localStorage.getItem(lsKey);
            if (val && !params.has(stKey)) {
                params.set(stKey, val);
                needsUpdate = true;
            }
        }
        if (needsUpdate) {
            window.location.search = params.toString();
        }
        </script>
    """, height=0)

    # Sync query params to session state
    qp = st.query_params
    if "OPENROUTER_API_KEY" in qp:
        st.session_state.OPENROUTER_API_KEY = qp["OPENROUTER_API_KEY"]
    if "OPENROUTER_MODEL" in qp:
        st.session_state.OPENROUTER_MODEL = qp["OPENROUTER_MODEL"]
    if "HF_API_TOKEN" in qp:
        st.session_state.HF_API_TOKEN = qp["HF_API_TOKEN"]

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
