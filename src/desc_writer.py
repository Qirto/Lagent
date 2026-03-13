import re

class DescriptionWriter:
    """Local generator that creates consistent, category-based descriptions without AI API."""

    def __init__(self, api_key=None, model=None):
        pass

    def write_description_stream(self, product_info, category="GENERAL"):
        """Generates content locally based on product category, bypassing the AI API."""
        
        # LOG: INIT
        print(f"[LOG] >>> INITIALIZING LOCAL SYNTHESIS FOR: {product_info.get('title')}")
        
        # Clean up scraped specs text
        raw_specs = product_info.get('specs', '')
        specs_clean = re.sub(r'\n{3,}', '\n\n', raw_specs).strip()
        if not specs_clean:
            specs_clean = "Aucune description détaillée n'est disponible pour le moment."

        title = product_info.get('title', 'Produit')
        price = product_info.get('price', 'N/A')
        sku = product_info.get('sku', 'N/A')
        url = product_info.get('url', '#')
        source = product_info.get('source', 'Site Web')

        # Formatting based on category
        desc = f"## {category.upper()}\n\n"
        desc += f"### {title}\n\n"
        
        desc += "#### Vue d'ensemble\n"
        desc += f"Ce produit de la gamme **{category}** est conçu pour offrir des performances optimales. "
        desc += f"Il est référencé sous le code **{sku}**.\n\n"
        
        desc += "#### Spécifications Techniques\n"
        desc += f"{specs_clean}\n\n"
        
        desc += "#### Résumé des détails\n"
        desc += f"- **Catégorie** : {category}\n"
        desc += f"- **Référence / SKU** : {sku}\n"
        desc += f"- **Prix constaté** : {price}\n"
        desc += f"- **Source principale** : [{source}]({url})\n\n"
        
        desc += "---\n\n"
        desc += "*Note : Description générée automatiquement à partir des données extraites du site marchand.*"

        # Simulate streaming for the UI
        chunk_size = 50
        for i in range(0, len(desc), chunk_size):
            yield desc[i:i+chunk_size]

if __name__ == "__main__":
    print("[LOG] DescriptionWriter Node Active.")
