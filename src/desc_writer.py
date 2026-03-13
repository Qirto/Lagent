import re

class DescriptionWriter:
    """Local generator that creates short and long descriptions from scraped data."""

    def __init__(self, api_key=None, model=None):
        # Kept for compatibility with existing instantiation
        pass

    def write_short_description(self, product_info):
        """Extracts or builds a short summary of the product."""
        # Prefer the best scraped short description
        short_desc = product_info.get('short_description', '')
        if short_desc:
            # Clean up whitespace
            return re.sub(r'\s+', ' ', short_desc).strip()

        # Fallback: Try to grab the first meaningful sentence from raw specs
        specs = product_info.get('specs', '')
        if specs:
            sentences = [s.strip() for s in re.split(r'[.!?\n]', specs) if len(s.strip()) > 20]
            if sentences:
                return sentences[0] + "."

        # Last resort
        category = product_info.get('category', 'Produit')
        return f"Ce produit de la gamme {category} est conçu pour offrir des performances optimales."

    def write_long_description(self, product_info, category="GENERAL"):
        """Generates a structured long description based on intelligent specs parsing."""
        title = product_info.get('title', 'Produit')
        price = product_info.get('price', 'N/A')
        sku = product_info.get('sku', 'N/A')
        url = product_info.get('url', '#')
        
        # Merge specs from all sources to get the richest text
        all_specs_texts = []
        if 'all_descriptions' in product_info:
            for desc in product_info['all_descriptions']:
                if desc.get('specs'):
                    all_specs_texts.append(desc['specs'])
        else:
            all_specs_texts.append(product_info.get('specs', ''))

        combined_specs = " ".join(all_specs_texts)
        
        # Extract features via Regex
        features = []
        
        if re.search(r'(bluetooth|sans fil|wireless|wifi|wi-fi)', combined_specs, re.I):
            features.append("Connectivité sans fil (Bluetooth/Wi-Fi)")
        elif re.search(r'(filaire|câble|wired|usb)', combined_specs, re.I):
            features.append("Connexion filaire pour une latence minimale")
            
        if re.search(r'(rvb|rgb|led|lumineux)', combined_specs, re.I):
            features.append("Éclairage RGB personnalisable")
            
        if re.search(r'(ergonomique|confortable|repose-poignet)', combined_specs, re.I):
            features.append("Conception ergonomique pour un confort optimal")
            
        if re.search(r'(mécanique|mecanique|switches|interrupteurs)', combined_specs, re.I):
            features.append("Interrupteurs mécaniques haute précision")

        if re.search(r'(gamer|gaming|jeu)', combined_specs, re.I):
            features.append("Optimisé pour le gaming et la haute performance")

        # Clean specs for the technical section
        raw_specs = product_info.get('specs', '')
        specs_clean = re.sub(r'\n{3,}', '\n\n', raw_specs).strip()
        if not specs_clean:
            specs_clean = "Aucune spécification détaillée n'est disponible pour le moment."
        
        # Formatting the description
        desc = f"### {title}\n\n"
        
        desc += "**Vue d'ensemble**\n"
        desc += f"Ce modèle issu de la catégorie **{category}** s'adresse aux utilisateurs exigeants. "
        desc += f"Reconnu sous la référence **{sku}**, il allie fiabilité et design soigné.\n\n"
        
        if features:
            desc += "**Caractéristiques principales**\n"
            for f in features:
                desc += f"- {f}\n"
            desc += "\n"
        
        desc += "**Spécifications techniques**\n"
        # Only show the first 1000 characters of specs to avoid massive text dumps
        desc += f"{specs_clean[:1000]}{'...' if len(specs_clean) > 1000 else ''}\n\n"
        
        sources_count = len(product_info.get('all_sources', []))
        source_text = "Vérifié sur plusieurs sites" if sources_count > 1 else "Vérifié"
        
        desc += "**Informations d'achat**\n"
        desc += f"- **Prix constaté** : {price}\n"
        desc += f"- **Disponibilité** : {source_text} (Source principale : [{product_info.get('source', 'Lien')}]({url}))\n"
        
        return desc

    def write_description_stream(self, product_info, category="GENERAL"):
        """Generates both descriptions and simulates a stream for the UI."""
        # Compute descriptions
        short_desc = self.write_short_description(product_info)
        long_desc = self.write_long_description(product_info, category)

        # Build combined output
        desc = "## Description Courte\n\n"
        desc += short_desc + "\n\n"
        desc += "---\n\n"
        desc += "## Description Longue\n\n"
        desc += long_desc

        # Simulate streaming for the UI
        chunk_size = 50
        for i in range(0, len(desc), chunk_size):
            yield desc[i:i+chunk_size]

if __name__ == "__main__":
    print("[LOG] DescriptionWriter Node Active.")