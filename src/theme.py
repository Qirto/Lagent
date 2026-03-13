import streamlit as st
import html
import re

def sanitize_html(text):
    """Basic HTML sanitization to prevent XSS when injecting user strings into markdown."""
    if not text:
        return ""
    # Remove HTML tags entirely
    clean = re.sub(r'<[^>]*>', '', str(text))
    # Escape special characters
    return html.escape(clean)

def apply_theme():
    """Unified CSS theme for all pages."""
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700&family=Orbitron:wght@400;500;700;900&family=Inter:wght@300;400;500;600;700;900&display=swap');

        :root {
            /* Color Palette */
            --primary: #00f3ff;
            --primary-glow: rgba(0, 243, 255, 0.4);
            --secondary: #ff47ff; /* Adjusted for better contrast WCAG AA */
            --secondary-glow: rgba(255, 71, 255, 0.4);
            --bg: #09090b;
            --bg-elevated: #111115;
            --surface: rgba(17, 17, 21, 0.65);
            --border: #27272a;
            --border-neon: rgba(0, 243, 255, 0.6);
            --text: #f8fafc;
            --text-secondary: #94a3b8;
            --text-muted: #8b95a5; /* Adjusted for WCAG AA contrast (5.2:1) */
            --green: #10b981;
            --red: #ef4444;
            
            /* Shapes & Shadows */
            --radius: 4px; /* Subtle rounding for better touch targets and feel */
            --radius-btn: 4px;
            --neu-shadow: 6px 6px 12px #040405, -6px -6px 12px #0e0e11;
            --neu-inset: inset 4px 4px 8px #040405, inset -4px -4px 8px #0e0e11;
            
            /* Spacing Scale */
            --space-1: 4px;
            --space-2: 8px;
            --space-3: 16px;
            --space-4: 24px;
            --space-5: 32px;
            --space-6: 48px;
        }

        /* Reduced Motion */
        @media (prefers-reduced-motion: reduce) {
            * {
                animation-duration: 0.01ms !important;
                animation-iteration-count: 1 !important;
                transition-duration: 0.01ms !important;
                scroll-behavior: auto !important;
            }
        }

        /* Base App Styling */
        html, body, [data-testid="stAppViewContainer"],
        .stApp, [data-testid="stMainBlockContainer"] {
            font-family: 'Inter', sans-serif;
            background-color: var(--bg) !important;
            background-image: 
                linear-gradient(rgba(0, 243, 255, 0.03) 1px, transparent 1px),
                linear-gradient(90deg, rgba(0, 243, 255, 0.03) 1px, transparent 1px);
            background-size: 40px 40px;
            color: var(--text);
            scroll-behavior: smooth;
        }

        /* Typography */
        h1, h2, h3, .sec-title, .brand h1 {
            font-family: 'Orbitron', sans-serif !important;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        /* Brutalist / Neumorphic Cards */
        div[data-testid="stVerticalBlockBorderWrapper"] > div {
            background-color: var(--bg-elevated) !important;
            border: 1px solid var(--border) !important;
            border-radius: var(--radius) !important;
            box-shadow: var(--neu-shadow) !important;
            padding: var(--space-4) !important;
            transition: all 0.3s ease;
        }
        
        div[data-testid="stVerticalBlockBorderWrapper"] > div:hover {
            border-color: var(--border-neon) !important;
            box-shadow: 0 0 15px var(--primary-glow), var(--neu-shadow) !important;
        }

        /* Inputs & Textareas */
        .stTextInput input, .stTextArea textarea, .stSelectbox > div[data-baseweb="select"] {
            background-color: var(--bg) !important;
            border: 1px solid var(--border) !important;
            color: var(--text) !important;
            border-radius: var(--radius) !important;
            box-shadow: var(--neu-inset) !important;
            font-family: 'JetBrains Mono', monospace !important;
            transition: border-color 0.2s, box-shadow 0.2s;
            padding: var(--space-2) var(--space-3) !important;
        }
        
        .stTextInput input:focus, .stTextArea textarea:focus, .stSelectbox > div[data-baseweb="select"]:focus-within {
            border-color: var(--primary) !important;
            box-shadow: 0 0 8px var(--primary-glow), var(--neu-inset) !important;
            outline: none !important;
        }

        /* Buttons */
        .stButton > button, [data-testid="baseButton-secondary"] {
            background-color: var(--bg-elevated) !important;
            color: var(--primary) !important;
            border: 1px solid var(--primary) !important;
            border-radius: var(--radius-btn) !important;
            text-transform: uppercase;
            font-family: 'Orbitron', sans-serif !important;
            font-weight: 700 !important;
            letter-spacing: 1px;
            box-shadow: var(--neu-shadow) !important;
            transition: all 0.2s cubic-bezier(0.25, 0.8, 0.25, 1) !important;
            min-height: 44px; /* Touch target minimum */
            padding: var(--space-2) var(--space-4) !important;
            position: relative;
            overflow: hidden;
        }
        
        /* Focus State for Accessibility */
        .stButton > button:focus-visible, [data-testid="baseButton-secondary"]:focus-visible {
            outline: 2px solid var(--primary) !important;
            outline-offset: 2px !important;
        }

        .stButton > button::before {
            content: '';
            position: absolute;
            top: 0; left: -100%; width: 50%; height: 100%;
            background: linear-gradient(90deg, transparent, rgba(0, 243, 255, 0.2), transparent);
            transform: skewX(-25deg);
            transition: left 0.5s;
        }
        
        .stButton > button:hover::before {
            left: 200%;
        }
        
        .stButton > button:hover {
            box-shadow: 0 0 15px var(--primary-glow), var(--neu-shadow) !important;
            transform: translateY(-2px);
            color: #fff !important;
        }
        
        .stButton > button:active {
            transform: translateY(1px);
            box-shadow: var(--neu-inset) !important;
        }

        /* Ghost Buttons */
        .ghost-btn .stButton > button {
            background: transparent !important;
            border: 1px dashed var(--border) !important;
            color: var(--text-muted) !important;
            box-shadow: none !important;
        }
        .ghost-btn .stButton > button:hover {
            border-color: var(--secondary) !important;
            color: var(--secondary) !important;
            box-shadow: 0 0 10px var(--secondary-glow) !important;
        }

        /* Sidebar */
        [data-testid="stSidebar"] {
            background-color: var(--surface) !important;
            border-right: 1px solid var(--border) !important;
            backdrop-filter: blur(12px) !important;
            -webkit-backdrop-filter: blur(12px) !important;
        }

        /* Title & Desc */
        .sec-title {
            font-size: 1.8rem;
            color: var(--text);
            margin-bottom: var(--space-2);
            padding-bottom: var(--space-2);
            border-bottom: 1px solid var(--border);
            text-shadow: 0 0 10px rgba(0,243,255,0.2);
        }
        .sec-desc {
            font-size: 0.95rem;
            color: var(--text-secondary);
            margin-bottom: var(--space-4);
            max-width: 800px;
            line-height: 1.6;
        }

        /* Stepper Navigation */
        .stepper {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: var(--space-6);
            padding: var(--space-4);
            background: var(--bg-elevated);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            box-shadow: var(--neu-shadow);
        }
        .step {
            display: flex;
            align-items: center;
            color: var(--text-muted);
            font-family: 'Orbitron', sans-serif;
            font-size: 0.85rem;
            font-weight: 600;
            letter-spacing: 1px;
            text-transform: uppercase;
            transition: color 0.3s;
        }
        .step.active {
            color: var(--primary);
            text-shadow: 0 0 8px var(--primary-glow);
        }
        .step.done {
            color: var(--secondary);
        }
        .step-num {
            display: flex;
            align-items: center;
            justify-content: center;
            width: 28px;
            height: 28px;
            border-radius: 50%;
            background: var(--bg);
            border: 1px solid var(--border);
            margin-right: var(--space-2);
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.8rem;
            transition: all 0.3s;
        }
        .step.active .step-num {
            border-color: var(--primary);
            background: rgba(0, 243, 255, 0.1);
            box-shadow: 0 0 10px var(--primary-glow);
        }
        .step.done .step-num {
            border-color: var(--secondary);
            background: rgba(255, 71, 255, 0.1);
            color: var(--secondary);
        }
        .step-line {
            flex-grow: 1;
            height: 2px;
            background: var(--border);
            margin: 0 var(--space-3);
            transition: background 0.3s, box-shadow 0.3s;
        }
        .step-line.done {
            background: var(--secondary);
            box-shadow: 0 0 8px var(--secondary-glow);
        }

        /* Processing Logs */
        .st-item {
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.85rem;
            padding: var(--space-2) var(--space-3);
            margin-bottom: var(--space-1);
            border-radius: var(--radius);
            background: var(--bg-elevated);
            border-left: 3px solid var(--border);
            display: flex;
            align-items: center;
            transition: all 0.2s;
        }
        .st-item:hover { transform: translateX(2px); }
        .st-item.proc { border-color: var(--primary); color: var(--text); }
        .st-item.ok { border-color: var(--green); color: var(--green); }
        .st-item.fail { border-color: var(--red); color: var(--red); }

        /* Meta Badges */
        .meta-row { margin: var(--space-2) 0; display: flex; flex-wrap: wrap; gap: var(--space-2); }
        .meta-badge {
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.75rem;
            padding: 2px 8px;
            background: var(--bg);
            border: 1px solid var(--border);
            border-radius: 12px;
            color: var(--text-secondary);
        }
        
        .price-tag {
            font-family: 'Orbitron', sans-serif;
            font-size: 1.5rem;
            font-weight: 700;
            color: var(--secondary);
            text-shadow: 0 0 10px var(--secondary-glow);
            margin: var(--space-2) 0;
            padding: var(--space-2) var(--space-3);
            background: rgba(255, 71, 255, 0.05);
            border: 1px solid rgba(255, 71, 255, 0.2);
            border-radius: var(--radius);
            display: inline-block;
        }

        /* Descriptions */
        .desc-hdr {
            font-family: 'Orbitron', sans-serif;
            font-size: 1.1rem;
            color: var(--primary);
            border-bottom: 1px solid var(--border);
            padding-bottom: var(--space-2);
            margin-bottom: var(--space-3);
        }
        .desc-content {
            font-family: 'Inter', sans-serif !important;
            font-size: 0.95rem;
            line-height: 1.6;
            color: var(--text);
            background: var(--bg);
            padding: var(--space-3);
            border-radius: var(--radius);
            border: 1px solid var(--border);
            max-height: 400px;
            overflow-y: auto;
        }
        .desc-content h3, .desc-content h4 {
            font-family: 'Inter', sans-serif !important;
            color: var(--text);
            margin-top: var(--space-3);
            font-size: 1.1rem;
        }

        /* Result Reference */
        .result-ref {
            font-family: 'Orbitron', sans-serif;
            font-size: 1.2rem;
            font-weight: 700;
            color: var(--text);
            padding-bottom: var(--space-2);
            border-bottom: 1px dashed var(--border);
            margin-bottom: var(--space-3);
        }

        /* Thumb Gallery */
        .thumb-btn .stButton > button {
            min-height: 32px;
            padding: 0.1rem 0 !important;
            font-size: 0.65rem;
            margin-top: -10px;
            border-radius: 2px !important;
        }

        /* Scrollbar */
        ::-webkit-scrollbar { width: 8px; height: 8px; }
        ::-webkit-scrollbar-track { background: var(--bg); }
        ::-webkit-scrollbar-thumb {
            background: var(--border);
            border-radius: 4px;
        }
        ::-webkit-scrollbar-thumb:hover { background: var(--text-muted); }

        /* Mobile Adjustments (Responsive) */
        @media (max-width: 768px) {
            .stepper { flex-direction: column; align-items: flex-start; gap: var(--space-2); }
            .step-line { display: none; }
            .sec-title { font-size: 1.4rem; }
            .price-tag { font-size: 1.2rem; }
            div[data-testid="stVerticalBlockBorderWrapper"] > div { padding: var(--space-3) !important; }
        }
        </style>
    """, unsafe_allow_html=True)
