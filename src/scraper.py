import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import quote
from concurrent.futures import ThreadPoolExecutor, as_completed


class TunisianScraper:
    """Scrapes product details and ALL multi-angle images from 7 Tunisian retailers."""

    SITES = [
        "MyTek", "Tunisianet", "Wiki", "MegaPC",
        "SBS Informatique", "Spacenet", "Scoop", "Zoom", "BestBuy",
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
            
            # Clean up prestashop duplicate formats (e.g. -large_default.jpg vs -medium_default.jpg)
            base_url = url.split('?')[0]
            
            # Strip standard size suffixes to check for base image duplicates
            core_name = re.sub(r'-(large_default|medium_default|small_default|home_default|thickbox_default)\.jpg', '', base_url)
            
            if core_name not in seen:
                low = base_url.lower()
                # Accept if it's not explicitly a thumbnail, or if it has a high-res indicator, or if it's our only option
                if "thumb" not in low or any(
                    x in low for x in ["1000x1000", "large", "full", "media", "zoom", "high", "max"]
                ):
                    cleaned.append(base_url)
                    seen.add(core_name)
        return cleaned

    @staticmethod
    def _normalize(s):
        return re.sub(r'[^A-Z0-9]', '', str(s).upper())

    @staticmethod
    def _tokenize(s):
        return [TunisianScraper._normalize(t) for t in re.split(r'[\s\-_/]+', str(s)) if TunisianScraper._normalize(t)]

    def _score_match(self, ref, color, details):
        """Scores how well a product matches the reference. Returns 0 for no match."""
        clean_sku = self._normalize(details.get('sku', ''))
        clean_ref = self._normalize(ref)
        clean_title = self._normalize(details.get('title', ''))

        if not clean_ref:
            return 0

        # Alias handling
        ref_aliased = clean_ref.replace("SOG", "SPIRITOFGAMER")
        title_aliased = clean_title.replace("SOG", "SPIRITOFGAMER")

        score = 0

        # 1. Exact Match
        if clean_sku and clean_ref == clean_sku:
            score += 100
        elif clean_ref == clean_title:
            score += 90

        # 2. Word-boundary token match
        ref_tokens = self._tokenize(ref)
        title_tokens = self._tokenize(details.get('title', ''))
        sku_tokens = self._tokenize(details.get('sku', ''))

        if ref_tokens:
            title_hits = sum(1 for t in ref_tokens if t in title_tokens)
            sku_hits = sum(1 for t in ref_tokens if t in sku_tokens)
            if title_hits == len(ref_tokens) or sku_hits == len(ref_tokens):
                score += 60

        # 3. Contiguous substring with boundary check
        if len(clean_ref) >= 4:
            if clean_sku and clean_sku.startswith(clean_ref):
                score += 40
            
            for haystack, needle in [(clean_title, clean_ref), (title_aliased, ref_aliased)]:
                pos = haystack.find(needle)
                if pos >= 0:
                    end = pos + len(needle)
                    if end >= len(haystack) or not haystack[end].isdigit():
                        score += 30
                        break

        # 4. Color Check
        if color and score > 0:
            c_upper = color.upper()
            search_space = (details.get('title', '') + " " + str(details.get('specs', ''))[:500]).upper()
            
            constraints = {
                "NOIR": {"pos": ["NOIR", "BLACK", "BLK"], "neg": ["BLANC", "WHITE", "ROUGE", "RED", "BLEU", "BLUE", "ROSE", "PINK", "VERT", "GREEN"]},
                "BLANC": {"pos": ["BLANC", "WHITE", "WHT", "ARTIC", "SNOW"], "neg": ["NOIR", "BLACK", "ROUGE", "RED", "BLEU", "BLUE", "ROSE", "PINK", "VERT", "GREEN"]},
                "ROUGE": {"pos": ["ROUGE", "RED"], "neg": ["NOIR", "BLACK", "BLANC", "WHITE", "BLEU", "BLUE"]},
                "BLEU": {"pos": ["BLEU", "BLUE"], "neg": ["NOIR", "BLACK", "BLANC", "WHITE", "ROUGE", "RED"]},
                "ROSE": {"pos": ["ROSE", "PINK"], "neg": ["NOIR", "BLACK", "BLANC", "WHITE", "BLEU", "BLUE", "ROUGE", "RED"]},
                "VERT": {"pos": ["VERT", "GREEN"], "neg": ["NOIR", "BLACK", "BLANC", "WHITE", "BLEU", "BLUE", "ROUGE", "RED"]},
            }

            if c_upper in constraints:
                cfg = constraints[c_upper]
                if not any(v in search_space for v in cfg["pos"]):
                    return 0
                if any(v in clean_title for v in cfg["neg"]):
                    score -= 20
            else:
                if c_upper not in search_space:
                    return 0
                
        return score

    def _scrape_short_desc(self, psoup, platform="prestashop"):
        short_desc = ""
        if platform == "prestashop":
            for sel in ["#product-description-short", ".product-description-short", ".short-description"]:
                el = psoup.select_one(sel)
                if el:
                    short_desc = el.get_text(strip=True)
                    break
        elif platform == "magento":
            el = psoup.select_one(".product.attribute.overview .value") or psoup.select_one(".product-info-main .overview")
            if el:
                short_desc = el.get_text(strip=True)
        elif platform == "woocommerce":
            el = psoup.select_one(".woocommerce-product-details__short-description")
            if el:
                short_desc = el.get_text(strip=True)
        
        if not short_desc:
            meta = psoup.find("meta", attrs={"name": "description"})
            if meta and meta.get("content"):
                content = meta.get("content")
                short_desc = str(content[0] if isinstance(content, list) else content).strip()
                
        return short_desc[:600]

    # ──────────────────────────────────────────
    # PRESTASHOP GENERIC HELPER
    # ──────────────────────────────────────────

    def _search_prestashop(self, base_url, source_name, ref, color="",
                           search_path="/recherche?s={query}",
                           item_sel=".product-miniature",
                           link_sel=".product-title a",
                           title_sel="h1[itemprop='name'], h1[prop='name'], h1.product-detail-name, h1",
                           sku_sel=".product-reference span, span[itemprop='sku']",
                           price_sel=".current-price span[itemprop='price'], .current-price .price, .current-price, .price, .product-price",
                           specs_sel="#description, .product-description, div[itemprop='description'], .product-information, .description",
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

        candidates = []
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
            short_desc = self._scrape_short_desc(psoup, "prestashop")

            details = {
                "source": source_name, "sku": sku, "title": title,
                "url": href, "price": price, "specs": specs[:2000], "short_description": short_desc, "images": [],
            }

            score = self._score_match(ref, color, details)
            if score > 0:
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
                details['_match_score'] = score
                candidates.append(details)

        if candidates:
            candidates.sort(key=lambda x: x['_match_score'], reverse=True)
            best = candidates[0]
            best.pop('_match_score', None)
            return best
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

        candidates = []
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
            short_desc = self._scrape_short_desc(psoup, "magento")

            details = {
                "source": "MyTek", "sku": sku, "title": title,
                "url": link['href'], "price": price, "specs": specs[:2000], "short_description": short_desc, "images": [],
            }

            score = self._score_match(ref, color, details)
            if score > 0:
                scripts = psoup.find_all("script", type="text/x-magento-init")
                for s in scripts:
                    if 'mage/gallery/gallery' in s.text:
                        found = re.findall(r'"full":"(https:[^"]+)"', s.text)
                        details['images'].extend([f.replace('\\/', '/') for f in found])
                og = psoup.find("meta", property="og:image")
                if og:
                    details['images'].insert(0, og.get("content"))
                details['images'] = self._clean_images(details['images'])
                details['_match_score'] = score
                candidates.append(details)

        if candidates:
            candidates.sort(key=lambda x: x['_match_score'], reverse=True)
            best = candidates[0]
            best.pop('_match_score', None)
            return best
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
            search_path="/recherche?controller=search&s={query}",
        )

    def search_sbs(self, ref, color=""):
        """SBS Informatique - PrestaShop."""
        return self._search_prestashop(
            base_url="https://www.sbsinformatique.com",
            source_name="SBS Informatique",
            ref=ref, color=color,
            search_path="/recherche?controller=search&s={query}",
        )

    def search_spacenet(self, ref, color=""):
        """Spacenet.tn - PrestaShop."""
        return self._search_prestashop(
            base_url="https://www.spacenet.tn",
            source_name="Spacenet",
            ref=ref, color=color,
            search_path="/recherche?controller=search&s={query}",
            item_sel=".item-product, .product-miniature",
            link_sel=".product-title a, h2 a, h3 a",
        )

    def search_bestbuy(self, ref, color=""):
        """BestBuyTunisie.tn - WooCommerce."""
        query = ref.upper().replace("SOG", "SPIRIT OF GAMER")
        url = f"https://bestbuytunisie.tn/?s={quote(query)}&post_type=product"
        soup = self._get_soup(url)
        if not soup:
            return None

        candidates = []
        # WooCommerce typically uses .product or .type-product
        for item in soup.select(".product, .type-product"):
            link = item.select_one("a[href]")
            if not link:
                continue

            href = link['href']
            psoup = self._get_soup(href)
            if not psoup:
                continue

            sku_el = psoup.select_one(".sku")
            sku = sku_el.get_text(strip=True) if sku_el else ref
            
            title_el = psoup.select_one(".product_title, h1")
            title = title_el.get_text(strip=True) if title_el else ""

            price_el = psoup.select_one(".price, .woocommerce-Price-amount")
            price = self.format_price(price_el.get_text(strip=True)) if price_el else "N/A"

            specs_el = psoup.select_one("#tab-description, .description")
            specs = specs_el.get_text(strip=True, separator='\n') if specs_el else ""
            short_desc = self._scrape_short_desc(psoup, "woocommerce")

            details = {
                "source": "BestBuy", "sku": sku, "title": title,
                "url": href, "price": price, "specs": specs[:2000], "short_description": short_desc, "images": [],
            }

            score = self._score_match(ref, color, details)
            if score > 0:
                # Images
                og = psoup.find("meta", property="og:image")
                if og:
                    details['images'].append(og.get("content"))
                
                # Gallery
                for img in psoup.select(".woocommerce-product-gallery img, .images img"):
                    src = img.get('data-src') or img.get('src')
                    if src:
                        details['images'].append(src)
                
                details['images'] = self._clean_images(details['images'])
                details['_match_score'] = score
                candidates.append(details)

        if candidates:
            candidates.sort(key=lambda x: x['_match_score'], reverse=True)
            best = candidates[0]
            best.pop('_match_score', None)
            return best
        return None

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
        """Search ALL 9 Tunisian retailer sites in parallel, aggregate results."""
        print(f"[LOG] Fetching across 9 sites for: {ref}")

        search_fns = [
            self.search_mytek,
            self.search_tunisianet,
            self.search_wiki,
            self.search_megapc,
            self.search_sbs,
            self.search_spacenet,
            self.search_scoop,
            self.search_zoom,
            self.search_bestbuy,
        ]

        results = []
        site_names = [
            "MyTek", "Tunisianet", "Wiki", "MegaPC",
            "SBS", "Spacenet", "Scoop", "Zoom", "BestBuy"
        ]

        def _run_parallel(query_term):
            res = []
            with ThreadPoolExecutor(max_workers=9) as executor:
                futures = {
                    executor.submit(fn, query_term, color): name
                    for fn, name in zip(search_fns, site_names)
                }
                for future in as_completed(futures):
                    site = futures[future]
                    try:
                        result = future.result()
                        if result:
                            print(f"[LOG]   Found on {site}")
                            res.append(result)
                    except Exception as e:
                        print(f"[LOG]   Error on {site}: {e}")
            return res

        results = _run_parallel(ref)

        # Fallback to designation if reference yields nothing
        if not results and designation:
            # try to create a clean query term from designation
            fallback_query = str(designation).strip()
            if len(fallback_query) > 5:
                print(f"[LOG]   Ref '{ref}' not found. Trying designation fallback: {fallback_query}")
                results = _run_parallel(fallback_query)

        # Fallback: Search "Any Website" via Google
        if not results:
            print("[LOG]   Not found on primary sites. Trying global search fallback...")
            global_res = self.search_global(ref, color)
            if global_res:
                results.append(global_res)

        if not results:
            return None

        # Aggregation: 
        # 1. Use the result with the highest score, then most specs as the base
        results.sort(key=lambda x: (x.get('_match_score', 0), len(x.get('specs', ''))), reverse=True)
        base = results[0]
        
        combined_imgs = []
        all_sources = []
        
        # Keep all descriptions for cross-verification
        all_descriptions = []

        for r in results:
            all_sources.append(r['source'])
            all_descriptions.append({
                "source": r['source'],
                "short": r.get('short_description', ''),
                "specs": r.get('specs', '')
            })
            for img in r['images']:
                # Deduplication logic
                core_img = re.sub(r'-(large_default|medium_default|small_default|home_default|thickbox_default)\.jpg', '', img)
                if not any(core_img in e for e in combined_imgs):
                    combined_imgs.append(img)

        base['images'] = self._clean_images(combined_imgs)
        base['all_sources'] = list(set(all_sources))
        base['all_descriptions'] = all_descriptions
        base['color_tag'] = color 
        
        # Pick the best short_description (longest non-empty across sources)
        short_descs = [r.get('short_description', '') for r in results if r.get('short_description')]
        if short_descs:
            base['short_description'] = max(short_descs, key=len)
        elif not base.get('short_description'):
            base['short_description'] = ''

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
                    
                meta_desc = page_soup.find("meta", attrs={"name": "description"})
                short_desc = ""
                if meta_desc and meta_desc.get("content"):
                    content = meta_desc.get("content")
                    short_desc = str(content[0] if isinstance(content, list) else content).strip()

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
                    "specs": desc[:2000],
                    "short_description": short_desc[:600],
                    "images": self._clean_images(imgs),
                    "_match_score": 50 # Base score for global fallback
                }

                # If it looks like a real product page, return it
                if title and (ref.upper() in str(title).upper() or ref.upper() in desc.upper()):
                    return details
            except Exception as e:
                print(f"[LOG]   Failed global fallback link {url}: {e}")
        
        return None
