import json
from datetime import datetime

class WebContentOptimizer:
    """Utility class for SEO/GEO optimization and Schema.org generation."""

    @staticmethod
    def generate_product_schema(product_info, site_name="Your Site"):
        """Generates JSON-LD Product schema."""
        schema = {
            "@context": "https://schema.org",
            "@type": "Product",
            "name": product_info.get("title", "Product"),
            "description": product_info.get("desc", ""),
            "image": product_info.get("images", [])[0] if product_info.get("images") else "",
            "brand": {
                "@type": "Brand",
                "name": site_name
            },
            "sku": product_info.get("sku", ""),
            "offers": {
                "@type": "Offer",
                "price": product_info.get("price", "0").replace(" DT", "").replace(" ", ""),
                "priceCurrency": "TND",
                "availability": "https://schema.org/InStock",
                "url": product_info.get("url", "")
            }
        }
        return json.dumps(schema, indent=2, ensure_ascii=False)

    @staticmethod
    def generate_faq_schema(qna_list):
        """Generates JSON-LD FAQPage schema."""
        if not qna_list:
            return ""
        
        schema = {
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": []
        }
        
        for q, a in qna_list:
            schema["mainEntity"].append({
                "@type": "Question",
                "name": q,
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": a
                }
            })
        return json.dumps(schema, indent=2, ensure_ascii=False)

    @staticmethod
    def wrap_geo_content(content, analysis_info=None):
        """Wraps content with GEO-optimized elements like TL;DR and metadata."""
        date_str = datetime.now().strftime("%B %d, %Y")
        
        tldr = ""
        if analysis_info:
            tldr = f"""
<div class="tldr-box" style="background: rgba(124, 106, 239, 0.05); border-left: 4px solid #7c6aef; padding: 1.5rem; margin-bottom: 2rem; border-radius: 8px;">
  <h3 style="margin-top: 0; color: #7c6aef;">TL;DR / Quick Summary</h3>
  <ul style="margin-bottom: 0;">
    <li>{analysis_info.get('key_point_1', 'High-performance product')}</li>
    <li>{analysis_info.get('key_point_2', 'Competitive pricing in Tunisia')}</li>
    <li>{analysis_info.get('key_point_3', 'Available now')}</li>
  </ul>
</div>
"""
        
        meta = f"""
<div class="meta" style="font-size: 0.8rem; color: #8b949e; margin-bottom: 1rem;">
  <span>Published: {date_str}</span> | <span>Last updated: {date_str}</span>
</div>
"""
        return f"{meta}\n{tldr}\n{content}"

if __name__ == "__main__":
    print("[LOG] WebContentOptimizer module ready.")
