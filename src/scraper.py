import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import quote
from concurrent.futures import ThreadPoolExecutor, as_completed


class TunisianScraper:
    """Scrapes product details and ALL multi-angle images from 7 Tunisian retailers."""

    SITES = [
        "MyTek", "Tunisianet", "Wiki", "MegaPC",
        "SBS Informatique", "Spacenet", "Scoop", "Zoom",
    ]

    def __init__(self):
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        }

    # ──────────────────────────────────────────
    # UTILS
    # ──────────────────────────────────────────

    def format_price(self, price_str):
        """Standardizes price display to Tunisian Dinar (DT) with 3 decimals."""
        if not price_str or price_str == "N/A":
            return "N/A"
        price_str = price_str.replace('\xa0', ' ').replace('\u202f', ' ').strip()
        match = re.search(r'(\d[\d\s,.]*)', price_str)
        if match:
            numeric_part = match.group(1).replace(" ", "").replace(",", ".")
            try:
                val = float(numeric_part)
                return f"{val:,.3f} DT".replace(',', ' ')
            except Exception:
                return f"{numeric_part} DT"
        return price_str

    def _get_soup(self, url):
        try:
            response = requests.get(url, headers=self.headers, timeout=15)
            if response.status_code == 200:
                return BeautifulSoup(response.content, 'html.parser')
        except Exception:
            pass
        return None

    def _clean_images(self, image_list):
        """Deduplicates and prioritizes high-res images."""
        seen = set()
        cleaned = []
        for url in image_list:
            if not url or not isinstance(url, str) or not url.startswith("http"):
                continue
            base_url = url.split('?')[0]
            if base_url not in seen:
                low = base_url.lower()
                if "thumb" not in low or any(
                    x in low for x in ["1000x1000", "large", "full", "media", "zoom", "high", "max"]
                ):
                    cleaned.append(base_url)
                    seen.add(base_url)
        return cleaned

    def _verify_match(self, ref, color, details):
        """Leniently verifies if the product matches the Reference or Title."""
        def normalize(s):
            return re.sub(r'[^A-Z0-9]', '', str(s).upper())

        clean_sku = normalize(details.get('sku', ''))
        clean_ref = normalize(ref)

        # 1. Exact SKU match after stripping non-alphanumeric
        if clean_ref and clean_sku and (clean_ref in clean_sku or clean_sku in clean_ref):
            pass # SKU matches
        else:
            # 2. Check if reference is in the title
            clean_title = details.get('title', '').upper()
            
            # SOG alias handling
            ref_aliased = clean_ref.replace("SOG", "SPIRITOFGAMER")
            title_aliased = normalize(clean_title).replace("SOG", "SPIRITOFGAMER")

            if clean_ref not in normalize(clean_title) and ref_aliased not in title_aliased:
                # 3. Fuzzy split check (if ref is "PRO X", check "PRO" and "X")
                ref_parts = [normalize(p) for p in str(ref).split() if normalize(p)]
                if not ref_parts or not all(p in normalize(clean_title) for p in ref_parts):
                    return False

        # Color match if specified
        if color:
            c_upper = color.upper()
            search_space = (str(details.get('title', '')) + " " + str(details.get('specs', ''))).upper()
            color_variants = [c_upper]
            if c_upper == "NOIR":
                color_variants.extend(["BLACK", "BLK"])
            elif c_upper == "BLANC":
                color_variants.extend(["WHITE", "WHT", "ARTIC", "SNOW"])
            elif c_upper == "ROUGE":
                color_variants.extend(["RED"])
            elif c_upper == "BLEU":
                color_variants.extend(["BLUE"])
                
            if not any(v in search_space for v in color_variants):
                return False
                
        return True

    # ──────────────────────────────────────────
    # PRESTASHOP GENERIC HELPER
    # ──────────────────────────────────────────

    def _search_prestashop(self, base_url, source_name, ref, color="",
                           search_path="/recherche?s={query}",
                           item_sel=".product-miniature",
                           link_sel=".product-title a",
                           title_sel="h1[itemprop='name'], h1[prop='name'], h1.product-detail-name, h1",
                           sku_sel=".product-reference span, span[itemprop='sku']",
                           price_sel=".current-price span[itemprop='price'], .current-price .price, .current-price, .price",
                           specs_sel="#description, .product-description",
                           img_sels=None):
        """Generic PrestaShop product search. Most Tunisian sites run PrestaShop."""
        if img_sels is None:
            img_sels = [
                ".js-qv-product-cover",
                ".product-cover img",
                "img.js-thumb",
                ".images-container img",
                ".product-images img",
            ]

        query = ref.upper().replace("SOG", "SPIRIT OF GAMER")
        url = base_url + search_path.format(query=quote(query))
        soup = self._get_soup(url)
        if not soup:
            return None

        for item in soup.select(item_sel):
            link = item.select_one(link_sel)
            if not link or not link.has_attr('href'):
                continue

            href = link.get('href')
            if not href or not isinstance(href, str):
                continue

            if not href.startswith("http"):
                href = base_url + href

            psoup = self._get_soup(href)
            if not psoup:
                continue

            sku_el = psoup.select_one(sku_sel)
            sku = sku_el.get_text(strip=True) if sku_el else "N/A"

            title_el = psoup.select_one(title_sel)
            title = title_el.get_text(strip=True) if title_el else ""

            # Try to find price more robustly
            price_val = "N/A"
            price_el = psoup.select_one(price_sel)
            if price_el:
                price_val = price_el.get_text(strip=True)
            else:
                meta_price = psoup.find(itemprop="price")
                if meta_price:
                    content = meta_price.get("content")
                    price_val = content if content else meta_price.get_text(strip=True)

            price = self.format_price(price_val) if price_val != "N/A" else "N/A"

            specs_el = psoup.select_one(specs_sel)
            specs = specs_el.get_text(strip=True) if specs_el else ""

            details = {
                "source": source_name, "sku": sku, "title": title,
                "url": href, "price": price, "specs": specs, "images": [],
            }

            if self._verify_match(ref, color, details):
                # OG image
                og = psoup.find("meta", property="og:image")
                if og and og.get("content"):
                    details['images'].append(og["content"])

                # Scrape all product images
                for sel in img_sels:
                    for img in psoup.select(sel):
                        src = (
                            img.get('data-image-large-src')
                            or img.get('data-full-size-image-url')
                            or img.get('data-zoom-image')
                            or img.get('src')
                            or img.get('data-src')
                        )
                        if src and isinstance(src, str):
                            if not src.startswith("http"):
                                src = base_url + src
                            details['images'].append(src)

                details['images'] = self._clean_images(details['images'])
                return details
        return None

    # ──────────────────────────────────────────
    # INDIVIDUAL SITE SCRAPERS
    # ──────────────────────────────────────────

    def search_mytek(self, ref, color=""):
        """MyTek.tn - Magento-based."""
        query = ref.upper().replace("SOG", "SPIRIT OF GAMER")
        url = f"https://www.mytek.tn/catalogsearch/result/?q={quote(query)}"
        soup = self._get_soup(url)
        if not soup:
            return None

        for item in soup.select(".product-item"):
            link = item.select_one(".product-item-link")
            if not link or not link.has_attr('href'):
                continue

            psoup = self._get_soup(link['href'])
            if not psoup:
                continue

            sku_el = (
                psoup.select_one(".product.attribute.sku .value")
                or psoup.find(itemprop="sku")
            )
            sku = sku_el.get_text(strip=True) if sku_el else "N/A"
            title_el = psoup.select_one(".page-title")
            title = title_el.get_text(strip=True) if title_el else ""

            # More robust price extraction for MyTek
            price_val = "N/A"
            price_attr_el = psoup.find(attrs={"data-price-amount": True})
            if price_attr_el:
                price_val = price_attr_el.get('data-price-amount', '')
            else:
                price_el = (
                    psoup.select_one("[data-price-type='finalPrice'] .price")
                    or psoup.select_one(".price-wrapper .price")
                    or psoup.select_one(".price")
                )
                if price_el:
                    price_val = price_el.get_text(strip=True)

            # Re-format price safely
            price = self.format_price(price_val) if price_val != "N/A" else "N/A"

            specs_el = psoup.select_one("#description") or psoup.select_one(".product-info-main")
            specs = specs_el.get_text(strip=True) if specs_el else ""

            details = {
                "source": "MyTek", "sku": sku, "title": title,
                "url": link['href'], "price": price, "specs": specs, "images": [],
            }

            if self._verify_match(ref, color, details):
                scripts = psoup.find_all("script", type="text/x-magento-init")
                for s in scripts:
                    if 'mage/gallery/gallery' in s.text:
                        found = re.findall(r'"full":"(https:[^"]+)"', s.text)
                        details['images'].extend([f.replace('\\/', '/') for f in found])
                og = psoup.find("meta", property="og:image")
                if og:
                    details['images'].insert(0, og.get("content"))
                details['images'] = self._clean_images(details['images'])
                return details
        return None

    def search_tunisianet(self, ref, color=""):
        """Tunisianet.com.tn - PrestaShop."""
        return self._search_prestashop(
            base_url="https://www.tunisianet.com.tn",
            source_name="Tunisianet",
            ref=ref, color=color,
            search_path="/recherche?s={query}&post_type=product",
            item_sel=".item-product, .product-miniature",
            link_sel=".product-title a",
        )

    def search_wiki(self, ref, color=""):
        """Wiki.tn - PrestaShop."""
        return self._search_prestashop(
            base_url="https://www.wiki.tn",
            source_name="Wiki",
            ref=ref, color=color,
            search_path="/recherche?controller=search&search_query={query}",
            item_sel=".ajax_block_product, .product-miniature",
            link_sel="a.product-name, .product-title a",
            price_sel=".price.product-price, .current-price, .price"
        )

    def search_megapc(self, ref, color=""):
        """MegaPC.tn - PrestaShop."""
        return self._search_prestashop(
            base_url="https://www.megapc.tn",
            source_name="MegaPC",
            ref=ref, color=color,
        )

    def search_sbs(self, ref, color=""):
        """SBS Informatique - PrestaShop."""
        return self._search_prestashop(
            base_url="https://www.sbsinformatique.com",
            source_name="SBS Informatique",
            ref=ref, color=color,
        )

    def search_spacenet(self, ref, color=""):
        """Spacenet.tn - PrestaShop."""
        return self._search_prestashop(
            base_url="https://www.spacenet.tn",
            source_name="Spacenet",
            ref=ref, color=color,
        )

    def search_scoop(self, ref, color=""):
        """Scoop.com.tn - PrestaShop."""
        return self._search_prestashop(
            base_url="https://www.scoop.com.tn",
            source_name="Scoop",
            ref=ref, color=color,
        )

    def search_zoom(self, ref, color=""):
        """Zoom.com.tn - PrestaShop."""
        return self._search_prestashop(
            base_url="https://www.zoom.com.tn",
            source_name="Zoom",
            ref=ref, color=color,
        )

    # ──────────────────────────────────────────
    # AGGREGATOR
    # ──────────────────────────────────────────

    def fetch_all(self, ref, designation="", color=""):
        """Search ALL 7 Tunisian retailer sites in parallel, aggregate results."""
        print(f"[LOG] Fetching across 7 sites for: {ref}")

        search_fns = [
            self.search_mytek,
            self.search_tunisianet,
            self.search_wiki,
            self.search_megapc,
            self.search_sbs,
            self.search_spacenet,
            self.search_scoop,
            self.search_zoom,
        ]

        results = []
        with ThreadPoolExecutor(max_workers=8) as executor:
            site_names = [
                "MyTek", "Tunisianet", "Wiki", "MegaPC",
                "SBS", "Spacenet", "Scoop", "Zoom",
            ]
            futures = {
                executor.submit(fn, ref, color): name
                for fn, name in zip(search_fns, site_names)
            }
            for future in as_completed(futures):
                site = futures[future]
                try:
                    result = future.result()
                    if result:
                        print(f"[LOG]   Found on {site}")
                        results.append(result)
                except Exception as e:
                    print(f"[LOG]   Error on {site}: {e}")

        # --- FALLBACK: Search "Any Website" via Google if not found on primary sites ---
        if not results:
            print("[LOG]   Not found on primary sites. Trying global search fallback...")
            global_res = self.search_global(ref, color)
            if global_res:
                results.append(global_res)

        if not results:
            return None

        # Aggregation: use first result as base, merge images from all
        base = results[0]
        combined_imgs = list(base['images'])
        all_sources = [base['source']]

        for r in results[1:]:
            all_sources.append(r['source'])
            for img in r['images']:
                if img not in combined_imgs:
                    combined_imgs.append(img)

        base['images'] = combined_imgs
        base['all_sources'] = all_sources
        base['color_tag'] = color # Keep for renaming
        return base

    def search_global(self, ref, color=""):
        """Fallback search using Google to find any Tunisian retailer."""
        query = f'"{ref}" site:.tn'
        if color:
            query += f' "{color}"'
        
        search_url = f"https://www.google.com/search?q={quote(query)}"
        soup = self._get_soup(search_url)
        if not soup:
            return None

        # Look for potential retailer links in search results
        links = []
        for a in soup.select('a'):
            href = a.get('href')
            if href and isinstance(href, str) and '/url?q=' in href:
                url = href.split('/url?q=')[1].split('&')[0]
                if '.tn' in url and 'google' not in url:
                    links.append(url)

        # Try to scrape the first 3 relevant links
        for url in links[:3]:
            try:
                print(f"[LOG]   Trying external site: {url}")
                page_soup = self._get_soup(url)
                if not page_soup:
                    continue

                # Heuristic extraction for unknown sites
                h1 = page_soup.find('h1')
                title = h1.get_text(strip=True) if h1 else page_soup.title.string if page_soup.title else ""
                
                # Simple price detection
                price_text = ""
                price_candidates = page_soup.find_all(string=re.compile(r'\d[\d\s,.]*(DT|TND)', re.I))
                if price_candidates:
                    price_text = self.format_price(str(price_candidates[0]))

                # Simple description detection
                desc = ""
                desc_el = (
                    page_soup.find(id=re.compile(r'desc', re.I)) or 
                    page_soup.find(class_=re.compile(r'desc|specs', re.I)) or
                    page_soup.find('article')
                )
                if desc_el:
                    desc = desc_el.get_text(strip=True, separator='\n')

                # Simple image detection
                imgs = []
                for img in page_soup.find_all('img'):
                    src = img.get('src') or img.get('data-src')
                    if src and isinstance(src, str):
                        low_src = src.lower()
                        if 'product' in low_src or 'catalog' in low_src or 'media' in low_src:
                            if not src.startswith('http'):
                                domain = url.split('//')[-1].split('/')[0]
                                src = f"https://{domain}/{src.lstrip('/')}"
                            imgs.append(src)

                details = {
                    "source": url.split('//')[-1].split('/')[0],
                    "sku": ref,
                    "title": str(title) if title else "",
                    "url": url,
                    "price": price_text or "N/A",
                    "specs": desc,
                    "images": self._clean_images(imgs),
                }

                # If it looks like a real product page, return it
                if title and (ref.upper() in str(title).upper() or ref.upper() in desc.upper()):
                    return details
            except Exception as e:
                print(f"[LOG]   Failed global fallback link {url}: {e}")
        
        return None
