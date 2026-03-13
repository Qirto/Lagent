import pdfplumber
import os
import re

class ProductPDFExtractor:
    """Robust extractor for multiple product PDF formats."""

    def __init__(self, pdf_path):
        self.pdf_path = pdf_path
        self.colors_map = {
            "NOIR": "NOIR", "BLACK": "NOIR", "DARK": "NOIR",
            "BLANC": "BLANC", "WHITE": "BLANC", "ARTIC": "BLANC", "SNOW": "BLANC",
            "ROUGE": "ROUGE", "RED": "ROUGE",
            "BLEU": "BLEU", "BLUE": "BLEU",
            "VERT": "VERT", "GREEN": "VERT",
            "ROSE": "ROSE", "PINK": "ROSE",
            "GRIS": "GRIS", "GREY": "GRIS", "GRAY": "GRIS", "SILVER": "GRIS"
        }

    def extract_all(self):
        """Extracts products using table detection and block heuristics."""
        products_by_category = {}
        
        with pdfplumber.open(self.pdf_path) as pdf:
            for page in pdf.pages:
                page_prods = self._parse_page(page)
                for p in page_prods:
                    cat = p.get('category', 'GENERAL')
                    if cat not in products_by_category:
                        products_by_category[cat] = []
                    products_by_category[cat].append(p)
        
        return products_by_category

    def _parse_page(self, page):
        """Tries table extraction, falls back to block parsing."""
        prods = []
        tables = page.find_tables()
        
        if tables:
            for table in tables:
                data = table.extract()
                if not data or len(data) < 1: continue
                
                header = [str(c).upper() if c else "" for c in data[0]]
                
                # Identify column indices
                idx_ref = self._find_col(header, ["MODÈLE", "REF", "RÉFÉRENCE", "REFERENCE", "ID"])
                idx_name = self._find_col(header, ["DÉSIGNATION", "DESIGNATION", "NOM", "CATÉGORIE", "CATEGORIE"])
                idx_price = self._find_col(header, ["PRIX", "PX TTC", "PRICE", "MONTANT"])
                
                # If we couldn't find a clear header, skip row 0 or treat as data
                start_row = 1
                if idx_ref == -1 and idx_name == -1:
                    # Heuristic: if no header found, maybe this table has no header row
                    idx_ref = 0
                    idx_name = 1
                    idx_price = len(data[0]) - 1
                    start_row = 0
                
                for row in data[start_row:]:
                    if not row or not any(row): continue
                    
                    ref = str(row[idx_ref]).strip() if idx_ref != -1 and row[idx_ref] else ""
                    # Clean ref (remove newlines)
                    ref = ref.replace('\n', '').strip()
                    
                    if not ref or ref.lower() in ["none", "modèle", "référence"]: continue
                    
                    name = str(row[idx_name]).strip() if idx_name != -1 and row[idx_name] else ""
                    price = str(row[idx_price]).strip() if idx_price != -1 and row[idx_price] else ""
                    
                    # Detect color from name
                    color = self._detect_color(name)
                    
                    prods.append({
                        "reference": ref,
                        "designation": name,
                        "price_ttc": price,
                        "color": color,
                        "category": self._detect_category(page, table.bbox)
                    })
        
        # If no products found via tables, try block parsing (for Consoles layout)
        if not prods:
            prods = self._parse_blocks(page)
            
        return prods

    def _find_col(self, header, keywords):
        for i, col in enumerate(header):
            for kw in keywords:
                if kw in col: return i
        return -1

    def _detect_color(self, text):
        upper = text.upper()
        for k, v in self.colors_map.items():
            if f" {k} " in f" {upper} " or upper.endswith(k):
                return v
        return ""

    def _detect_category(self, page, table_bbox):
        """Finds the full line of text above the table to use as category."""
        words = page.extract_words(extra_attrs=["size"])
        # Filter words that are above the table and significantly large
        candidate_words = [w for w in words if w['size'] > 12 and w['bottom'] < table_bbox[1]]
        
        if candidate_words:
            # Find the word closest to the table
            closest_word = max(candidate_words, key=lambda x: x['bottom'])
            # Find all words on the same line (approximate y-coordinate)
            line_words = [w for w in candidate_words if abs(w['top'] - closest_word['top']) < 5]
            # Sort words by left position to reconstruct the line
            line_words.sort(key=lambda x: x['x0'])
            return " ".join([w['text'] for w in line_words]).strip().upper()
        
        return "GENERAL"

    def _parse_blocks(self, page):
        """Heuristic for unstructured layouts like the Consoles PDF."""
        prods = []
        text = page.extract_text()
        if not text: return []
        
        # Looking for patterns: Name (multiline), Ref (digits or model), Price (digits + DT/DHT)
        # In the Consoles PDF:
        # Title: PS5 DUALSENSE BLANCHE+ FC 24
        # Ref: 78779000006
        # Price: 479 DHT
        
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        
        # Simple sliding window search
        for i in range(len(lines)):
            line = lines[i]
            # Check if current line looks like a price
            if "DHT" in line or "DT" in line or re.search(r'\d+,\d+\s*(DT|DHT)', line):
                # Price found. Look back for Ref and Title.
                price = line
                ref = ""
                title = ""
                
                # Ref is usually right above price or 2 lines above
                if i > 0:
                    prev = lines[i-1]
                    if prev.isdigit() or len(prev) > 5: # Likely a SKU
                        ref = prev
                        if i > 1: title = lines[i-2]
                    else:
                        # Maybe line above is title and ref is missing?
                        title = prev
                
                if title and (ref or price):
                    prods.append({
                        "reference": ref if ref else title[:10],
                        "designation": title,
                        "price_ttc": price,
                        "color": self._detect_color(title),
                        "category": "PRODUCTS"
                    })
        return prods

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        ext = ProductPDFExtractor(sys.argv[1])
        print(ext.extract_all())
