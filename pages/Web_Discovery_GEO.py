import streamlit as st
import sys
import os

# Path setup
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    from web_content_optimizer import WebContentOptimizer
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
            font-size: 1.25rem; font-weight: 600; color: var(--text); margin-bottom: 0.5rem;
            text-transform: uppercase; letter-spacing: 2px;
        }
        .sec-desc {
            font-size: 0.85rem; color: var(--text-secondary); margin-bottom: 1.5rem;
        }
        
        .brand {
            text-align: center; padding: 1.5rem 0;
        }
        .brand h1 {
            font-family: 'Orbitron', sans-serif !important;
            font-size: 2rem; font-weight: 900; letter-spacing: 8px;
            background: linear-gradient(90deg, var(--primary), var(--secondary));
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        }

        [data-testid="stVerticalBlockBorderWrapper"] > div:has(> div.element-container) {
            background: var(--surface) !important;
            backdrop-filter: blur(12px) !important;
            border: 1px solid var(--border) !important;
            border-radius: var(--radius) !important;
            padding: 1.5rem;
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
        <a href="#lagent-discovery" class="back-to-top">↑</a>
    """, unsafe_allow_html=True)



def main():
    st.set_page_config(page_title="Web Content & GEO", layout="wide")
    apply_theme()

    st.markdown(
        '<div class="brand" id="lagent-discovery">'
        "<h1>Web<b>Discovery</b></h1>"
        '<p style="font-size:0.65rem; color:#8b949e; letter-spacing:2px; text-transform:uppercase;">SEO & AI Discovery Optimization (GEO)</p>'
        "</div>",
        unsafe_allow_html=True,
    )

    if not HAS_MODULES:
        st.error(f"Failed to load modules: {_ERR}")
        return

    optimizer = WebContentOptimizer()

    tab_schema, tab_geo, tab_analytics = st.tabs(["Schema Generator", "GEO Enhancer", "Analytics Setup"])

    # ──────────── TAB: Schema Generator ────────────
    with tab_schema:
        st.markdown('<p class="sec-title">Structured Data (JSON-LD)</p>', unsafe_allow_html=True)
        st.markdown('<p class="sec-desc">Generate Google-friendly schema markup for AI assistants to parse your data accurately.</p>', unsafe_allow_html=True)

        col1, col2 = st.columns([1, 1], gap="large")

        with col1:
            with st.container(border=True):
                st.subheader("Product Details")
                p_name = st.text_input("Product Name", placeholder="e.g. Spirit of Gamer MK3")
                p_desc = st.text_area("Description", height=100)
                p_price = st.text_input("Price (DT)", placeholder="e.g. 129.500")
                p_sku = st.text_input("SKU/Reference")
                p_url = st.text_input("Product URL")
                
                if st.button("Generate Product Schema", use_container_width=True):
                    info = {"title": p_name, "desc": p_desc, "price": p_price, "sku": p_sku, "url": p_url}
                    st.session_state.current_schema = optimizer.generate_product_schema(info)

        with col2:
            if "current_schema" in st.session_state:
                st.subheader("JSON-LD Result")
                st.code(st.session_state.current_schema, language="json")
                st.download_button("Download Schema", st.session_state.current_schema, file_name="product_schema.jsonld", mime="application/ld+json")
            else:
                st.info("Fill the form to generate schema.")

    # ──────────── TAB: GEO Enhancer ────────────
    with tab_geo:
        st.markdown('<p class="sec-title">GEO Optimization Engine</p>', unsafe_allow_html=True)
        st.markdown('<p class="sec-desc">Enhance content with TL;DR boxes and visible timestamps for AI discovery.</p>', unsafe_allow_html=True)

        raw_content = st.text_area("Paste Content Here", height=300, placeholder="Paste your generated product description...")
        
        c1, c2, c3 = st.columns(3)
        p1 = c1.text_input("Key Point 1", "Performance haut de gamme")
        p2 = c2.text_input("Key Point 2", "Excellent rapport qualité/prix")
        p3 = c3.text_input("Key Point 3", "Disponible immédiatement")

        if st.button("Apply GEO Wrapper", use_container_width=True):
            analysis = {"key_point_1": p1, "key_point_2": p2, "key_point_3": p3}
            enhanced = optimizer.wrap_geo_content(raw_content, analysis)
            st.markdown("### Optimized Result Preview")
            st.markdown(enhanced, unsafe_allow_html=True)
            st.divider()
            st.subheader("HTML/Markdown for Site")
            st.code(enhanced, language="html")

    # ──────────── TAB: Analytics ────────────
    with tab_analytics:
        st.markdown('<p class="sec-title">Track AI Discovery</p>', unsafe_allow_html=True)
        st.markdown('<p class="sec-desc">Tools to measure how many visitors are coming from AI assistants.</p>', unsafe_allow_html=True)
        
        st.subheader("GA4 Regex Filter")
        st.info("Use this regex in GA4 to filter for AI Referrals (ChatGPT, Perplexity, etc.)")
        st.code(r".*chatgpt\.com.*|.*perplexity\.ai.*|.*gemini\.google\.com.*|.*copilot\.microsoft\.com.*|.*openai\.com.*|.*claude\.ai.*|.*poe\.com.*|.*you\.com.*|.*phind\.com.*", language="regex")

        st.subheader("Referrer Tracking Script")
        st.code("""
// AI Referrer Check
const aiReferrers = ['chatgpt.com', 'perplexity.ai', 'claude.ai', 'gemini.google.com'];
const isAI = aiReferrers.some(ai => document.referrer.includes(ai));
if (isAI) {
    console.log("Visitor arrived via AI Assistant:", document.referrer);
}
        """, language="javascript")


if __name__ == "__main__":
    main()
