import streamlit as st
import sys
import os

# Path setup
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

try:
    from src.web_content_optimizer import WebContentOptimizer
    HAS_MODULES = True
except Exception as e:
    try:
        from web_content_optimizer import WebContentOptimizer
        HAS_MODULES = True
    except Exception as e2:
        HAS_MODULES = False
        _ERR = f"P1: {e} | P2: {e2}"


from src.theme import apply_theme

# ──────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────

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
                
                if st.button("Generate Product Schema", width='stretch'):
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

        if st.button("Apply GEO Wrapper", width='stretch'):
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
