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
        
        .stButton > button::before {
            content: '';
            position: absolute;
            top: 0; left: -100%; width: 50%; height: 100%;
            background: linear-gradient(90deg, transparent, rgba(0,243,255,0.4), transparent);
            transform: skewX(-20deg);
            transition: left 0.5s ease;
        }

        .stButton > button:hover::before {
            left: 150%;
        }

        .stButton > button:hover {
            background-color: rgba(0, 243, 255, 0.1) !important;
            color: var(--primary) !important;
            box-shadow: 0 0 20px var(--primary-glow), var(--neu-shadow) !important;
            transform: translateY(-2px);
            border-color: var(--primary) !important;
        }

        .stButton > button:active {
            transform: translateY(1px);
            box-shadow: var(--neu-inset) !important;
        }

        /* Specific overrides for Ghost / Secondary buttons */
        .ghost-btn .stButton > button {
            border-color: var(--text-muted) !important;
            color: var(--text-secondary) !important;
            box-shadow: none !important;
        }
        .ghost-btn .stButton > button:hover {
            border-color: var(--secondary) !important;
            color: var(--secondary) !important;
            background-color: rgba(255, 0, 255, 0.05) !important;
            box-shadow: 0 0 15px var(--secondary-glow) !important;
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
            box-shadow: 0 0 15px var(--primary-glow);
        }

        /* Scanline effect for sidebar */
        [data-testid="stSidebar"]::after {
            content: " ";
            display: block;
            position: absolute;
            top: 0; left: 0; bottom: 0; right: 0;
            background: linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.25) 50%), linear-gradient(90deg, rgba(255, 0, 0, 0.06), rgba(0, 255, 0, 0.02), rgba(0, 0, 255, 0.06));
            z-index: 2;
            background-size: 100% 2px, 3px 100%;
            pointer-events: none;
        }

        /* Headers and Typography classes */
        .sec-title {
            font-size: 2.2rem;
            color: var(--text);
            text-shadow: 0 0 12px rgba(255,255,255,0.2);
            margin-bottom: 0.2rem;
            border-bottom: 3px solid var(--border);
            display: inline-block;
            padding-bottom: 0.2rem;
            position: relative;
        }
        .sec-title::after {
            content: '';
            position: absolute;
            bottom: -3px;
            left: 0;
            width: 30%;
            height: 3px;
            background: var(--primary);
            box-shadow: 0 0 10px var(--primary-glow);
        }
        .sec-desc {
            color: var(--text-secondary);
            font-size: 1.05rem;
            margin-bottom: 2.5rem;
            line-height: 1.6;
            max-width: 800px;
        }
        
        /* Stepper - Cyberpunk / Brutalist */
        .stepper {
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 2rem 0 3.5rem 0;
            background: var(--bg-elevated);
            padding: 1.2rem;
            border: 2px solid var(--border);
            border-radius: var(--radius);
            box-shadow: var(--neu-shadow);
        }
        .step {
            display: flex;
            align-items: center;
            font-family: 'Orbitron', sans-serif;
            font-size: 0.85rem;
            font-weight: 700;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 1.5px;
            transition: color 0.3s;
        }
        .step.active {
            color: var(--primary);
            text-shadow: 0 0 10px var(--primary-glow);
        }
        .step.done {
            color: var(--secondary);
            text-shadow: 0 0 10px var(--secondary-glow);
        }
        .step-num {
            display: flex;
            align-items: center;
            justify-content: center;
            width: 30px;
            height: 30px;
            border-radius: 0; /* Brutalism */
            border: 2px solid var(--text-muted);
            margin-right: 10px;
            font-family: 'JetBrains Mono', monospace;
            font-weight: 900;
            background: var(--bg);
            box-shadow: var(--neu-inset);
            transition: all 0.3s;
        }
        .step.active .step-num {
            border-color: var(--primary);
            color: var(--bg);
            background: var(--primary);
            box-shadow: 0 0 15px var(--primary-glow), var(--neu-shadow);
        }
        .step.done .step-num {
            border-color: var(--secondary);
            color: var(--secondary);
            background: rgba(255, 0, 255, 0.1);
            box-shadow: 0 0 12px var(--secondary-glow);
        }
        .step-line {
            height: 3px;
            width: 50px;
            background: var(--border);
            margin: 0 20px;
            transition: background 0.3s, box-shadow 0.3s;
            box-shadow: var(--neu-inset);
        }
        .step-line.done {
            background: var(--secondary);
            box-shadow: 0 0 10px var(--secondary-glow);
        }

        /* Card Header */
        .card-hdr {
            font-family: 'Orbitron', sans-serif;
            font-size: 1.1rem;
            color: var(--text);
            border-bottom: 2px solid var(--border);
            padding-bottom: 0.5rem;
            margin-bottom: 1.5rem;
            text-transform: uppercase;
            letter-spacing: 2px;
            display: flex;
            align-items: center;
        }
        .card-hdr::before {
            content: '';
            display: inline-block;
            width: 8px;
            height: 8px;
            background: var(--primary);
            margin-right: 10px;
            box-shadow: 0 0 8px var(--primary-glow);
        }

        /* Checkboxes */
        div[data-testid="stCheckbox"] label span {
            font-family: 'JetBrains Mono', monospace;
            color: var(--text);
            font-size: 0.95rem;
        }
        div[data-testid="stCheckbox"] div[role="checkbox"] {
            border-radius: 0 !important;
            border: 2px solid var(--border) !important;
            transition: all 0.2s;
        }
        div[data-testid="stCheckbox"] div[role="checkbox"][aria-checked="true"] {
            background-color: var(--primary) !important;
            border-color: var(--primary) !important;
            box-shadow: 0 0 12px var(--primary-glow);
        }
        
        /* File Uploader override */
        [data-testid="stFileUploader"] > div > div {
            background-color: rgba(0, 243, 255, 0.03) !important;
            border: 2px dashed var(--primary) !important;
            border-radius: var(--radius) !important;
            box-shadow: var(--neu-inset) !important;
            transition: all 0.3s;
            padding: 3rem !important;
        }
        [data-testid="stFileUploader"] > div > div:hover {
            border-color: var(--secondary) !important;
            background-color: rgba(255, 0, 255, 0.05) !important;
            box-shadow: 0 0 20px var(--secondary-glow), var(--neu-inset) !important;
        }
        [data-testid="stFileUploader"] small {
            font-family: 'JetBrains Mono', monospace !important;
            color: var(--primary) !important;
            font-size: 1rem !important;
        }

        /* Status & Log Items */
        .st-item {
            padding: 12px 18px;
            margin-bottom: 10px;
            border-radius: 0;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.9rem;
            border-left: 4px solid var(--border);
            background: var(--bg-elevated);
            box-shadow: var(--neu-shadow);
            transition: all 0.2s;
        }
        .st-item:hover {
            transform: translateX(2px);
        }
        .st-item.proc {
            border-color: var(--primary);
            color: var(--text);
            box-shadow: inset 300px 0 100px -100px rgba(0,243,255,0.08), var(--neu-shadow);
        }
        .st-item.proc strong {
            color: var(--primary);
            text-shadow: 0 0 8px var(--primary-glow);
        }
        .st-item.ok {
            border-color: var(--green);
            color: var(--text);
            box-shadow: inset 100px 0 50px -50px rgba(16,185,129,0.1), var(--neu-shadow);
        }
        .st-item.fail {
            border-color: var(--red);
            color: var(--text);
            box-shadow: inset 100px 0 50px -50px rgba(239,68,68,0.1), var(--neu-shadow);
        }
        
        /* Badges & Tags */
        .meta-badge {
            display: inline-flex;
            align-items: center;
            padding: 4px 10px;
            background: rgba(0, 243, 255, 0.05);
            border: 1px solid var(--primary);
            border-radius: 0;
            font-size: 0.75rem;
            font-weight: 700;
            font-family: 'JetBrains Mono', monospace;
            color: var(--primary);
            margin-right: 8px;
            text-transform: uppercase;
            letter-spacing: 1px;
            box-shadow: 0 0 5px rgba(0,243,255,0.2);
        }
        
        .price-tag {
            font-family: 'Orbitron', sans-serif;
            font-size: 1.8rem;
            font-weight: 900;
            color: var(--secondary);
            text-shadow: 0 0 15px var(--secondary-glow);
            margin: 15px 0;
            padding: 8px 15px;
            border: 2px solid var(--secondary);
            display: inline-block;
            background: var(--bg);
            box-shadow: var(--neu-inset);
            letter-spacing: 2px;
        }
        
        /* File Chip */
        .file-chip {
            display: inline-flex;
            align-items: center;
            background: var(--bg);
            border: 1px solid var(--primary);
            padding: 10px 20px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.9rem;
            color: var(--primary);
            margin-bottom: 2rem;
            box-shadow: 0 0 15px rgba(0,243,255,0.1), var(--neu-inset);
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .file-chip strong {
            color: var(--text);
            margin-right: 8px;
        }
        
        /* Description Header */
        .desc-hdr {
            font-family: 'Orbitron', sans-serif;
            font-size: 1.2rem;
            color: var(--secondary);
            border-bottom: 2px dashed var(--border);
            padding-bottom: 0.5rem;
            margin-bottom: 1rem;
            text-transform: uppercase;
            letter-spacing: 2px;
            text-shadow: 0 0 8px var(--secondary-glow);
        }

        /* Description Content */
        .desc-content {
            font-family: Arial, Helvetica, sans-serif !important;
            font-size: 1.05rem;
            line-height: 1.6;
            color: var(--text);
            background: rgba(0,0,0,0.2);
            padding: 1.5rem;
            border-left: 3px solid var(--primary);
            margin-bottom: 1.5rem;
        }
        .desc-content h1, .desc-content h2, .desc-content h3, .desc-content h4 {
            font-family: Arial, Helvetica, sans-serif !important;
            color: var(--primary);
            letter-spacing: normal;
            text-transform: none;
            margin-top: 1.2rem;
            margin-bottom: 0.8rem;
        }

        /* Result Reference Header */
        .result-ref {
            font-family: 'Orbitron', sans-serif;
            font-size: 1.4rem;
            font-weight: 700;
            color: var(--text);
            border-bottom: 2px solid var(--border);
            padding-bottom: 8px;
            margin-bottom: 20px;
            text-transform: uppercase;
            letter-spacing: 2.5px;
            position: relative;
        }
        .result-ref::after {
            content: '';
            position: absolute;
            bottom: -2px;
            left: 0;
            width: 50px;
            height: 2px;
            background: var(--secondary);
            box-shadow: 0 0 10px var(--secondary-glow);
        }
        
        /* Thumbnails & Images */
        .thumb-btn .stButton > button {
            padding: 0.1rem !important;
            min-height: 20px !important;
            font-size: 0.65rem !important;
            border-radius: 0 !important;
            letter-spacing: 0;
            border-width: 1px !important;
            margin-top: -15px !important;
        }
        div[data-testid="stImage"] img {
            border: 2px solid var(--border);
            border-radius: 0;
            box-shadow: var(--neu-shadow);
            transition: all 0.3s;
        }
        div[data-testid="stImage"]:hover img {
            border-color: var(--primary);
            box-shadow: 0 0 20px var(--primary-glow);
        }

        /* Alerts */
        [data-testid="stAlert"] {
            background-color: var(--bg-elevated) !important;
            border: 2px solid var(--border);
            border-radius: 0;
            box-shadow: var(--neu-inset);
            font-family: 'Inter', sans-serif;
            color: var(--text);
        }
        [data-testid="stAlert"][data-baseweb="notification"] {
            border-left: 4px solid var(--primary);
        }

        /* Progress Bar */
        .stProgress > div > div > div > div {
            background-color: var(--primary) !important;
            box-shadow: 0 0 15px var(--primary-glow) !important;
            border-radius: 0 !important;
        }
        .stProgress > div > div {
            background-color: var(--bg) !important;
            border-radius: 0 !important;
            border: 1px solid var(--border);
            box-shadow: var(--neu-inset);
            height: 12px !important;
        }

        /* Hide Default Main Menu */
        #MainMenu, footer { display: none !important; }

        /* Scrollbar styling for Cyberpunk feel */
        ::-webkit-scrollbar {
            width: 10px;
            height: 10px;
        }
        ::-webkit-scrollbar-track {
            background: var(--bg);
            border-left: 1px solid var(--border);
        }
        ::-webkit-scrollbar-thumb {
            background: var(--border);
            border-radius: 0;
            border: 1px solid var(--bg);
        }
        ::-webkit-scrollbar-thumb:hover {
            background: var(--primary);
            box-shadow: 0 0 10px var(--primary-glow);
        }

        /* Back to Top Button */
        .back-to-top {
            position: fixed;
            bottom: 30px;
            right: 30px;
            background: var(--surface);
            border: 2px solid var(--primary);
            color: var(--primary);
            width: 50px;
            height: 50px;
            border-radius: 0; /* Brutalism */
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            z-index: 9999;
            transition: all 0.2s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            text-decoration: none !important;
            box-shadow: var(--neu-shadow);
            backdrop-filter: blur(12px); /* Glassmorphism */
            font-family: 'Orbitron', sans-serif;
            font-weight: 900;
            font-size: 1.2rem;
        }
        .back-to-top:hover {
            background: var(--primary);
            color: var(--bg);
            box-shadow: 0 0 25px var(--primary-glow);
            transform: translateY(-5px) scale(1.1);
            border-color: var(--bg);
        }
        </style>
        <a href="#lagent-ai" class="back-to-top" aria-label="Back to top">▲</a>
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


                desc = ""
                # Use local description writer with category
                category_name = st.session_state.get("_active_cat", "GENERAL")
                for chunk in writer.write_description_stream(web, category=category_name):
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
    c1, c2, _ = st.columns([1, 1.2, 4])
    with c1:
        if st.button("New Batch", width='stretch', key="btn_new", type="secondary"):
            st.session_state.ui = "config"
            st.rerun()
    with c2:
        if ok > 0:
            zip_data = _prepare_download_zip()
            st.download_button(
                "Download All (ZIP)",
                data=zip_data,
                file_name=f"product_export_{int(time.time())}.zip",
                mime="application/zip",
                width='stretch',
                key="btn_download_zip",
                type="primary"
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

                    st.image(imgs[ptr], width='stretch')
                    if has_enhanced:
                        st.markdown(
                            '<div style="font-size:0.65rem;color:var(--green);margin-top:-10px;margin-bottom:10px">'
                            '✨ Enhanced 1024x1024 LANCZOS</div>',
                            unsafe_allow_html=True
                        )

                    # Thumbnail navigation
                    if len(imgs) > 1:
                        max_thumbs = min(len(imgs), 6)
                        st.markdown('<div style="font-size: 0.85rem; color: var(--text-muted); margin-bottom: 5px; font-family: \'JetBrains Mono\', monospace;">GALLERY:</div>', unsafe_allow_html=True)
                        
                        # Show visual thumbnails instead of just text buttons
                        thumb_cols = st.columns(max_thumbs)
                        for idx in range(max_thumbs):
                            with thumb_cols[idx]:
                                is_active = idx == ptr
                                
                                # First render the thumbnail image very small
                                st.image(imgs[idx], width='stretch')
                                
                                # Then a tiny selector button directly underneath
                                st.markdown('<div class="thumb-btn">', unsafe_allow_html=True)
                                btn_type = "primary" if is_active else "secondary"
                                label = f"SEL" if is_active else "View"
                                if st.button(
                                    label,
                                    key=f"t_{ref}_{idx}",
                                    width='stretch',
                                    type=btn_type
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
                
                # Use simple font for description readability (System sans-serif)
                st.markdown(f'<div class="desc-content">\n\n{item["desc"]}\n\n</div>', unsafe_allow_html=True)

                dl1, dl2, dl3 = st.columns([1, 1, 1])
                with dl1:
                    st.download_button(
                        "Download Text (.txt)",
                        data=item["desc"],
                        file_name=f"{ref}_description.txt",
                        mime="text/plain",
                        width='stretch',
                        key=f"dl_{ref}",
                        type="secondary"
                    )
                with dl2:
                    st.download_button(
                        "Download Markdown (.md)",
                        data=item["desc"],
                        file_name=f"{ref}_description.md",
                        mime="text/markdown",
                        width='stretch',
                        key=f"dlmd_{ref}",
                        type="secondary"
                    )
                with dl3:
                    if has_enhanced:
                        ptr = st.session_state.img_ptr.get(ref, 0)
                        st.download_button(
                            "Download Enhanced Image (.png)",
                            data=res["enhanced_images"][ptr],
                            file_name=f"{ref}_enhanced_{ptr+1}.png",
                            mime="image/png",
                            width='stretch',
                            key=f"dlimg_{ref}",
                            type="primary"
                        )
                    else:
                        st.button("No Enhanced Img", disabled=True, width='stretch', key=f"noimg_{ref}")



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
        ("OPENROUTER_API_KEY", os.getenv("OPENROUTER_API_KEY", "")),
        ("OPENROUTER_MODEL", "openrouter/free"),
        ("HF_API_TOKEN", os.getenv("HF_API_TOKEN", ""))
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
