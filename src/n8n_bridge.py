import requests
import json
import base64
import os
from dotenv import load_dotenv

load_dotenv()


class N8NBridge:
    """
    Bridge between the scraper pipeline and n8n workflows.
    Sends scraped images to n8n webhook for auto-enhancement,
    and receives enhanced images back.

    n8n Workflow Setup:
    1. Create a Webhook node (POST) in n8n
    2. Add an "HTTP Request" or "Code" node to process images
    3. Connect to the ImageEnhancer API endpoint or use built-in processing
    4. Return enhanced images as base64 in the response

    Environment:
        N8N_WEBHOOK_URL  - Your n8n webhook trigger URL
        N8N_API_KEY      - Optional API key for n8n auth
    """

    def __init__(self, webhook_url=None, api_key=None):
        self.webhook_url = webhook_url or os.getenv("N8N_WEBHOOK_URL", "")
        self.api_key = api_key or os.getenv("N8N_API_KEY", "")
        self.timeout = 120  # Image processing can be slow

    @property
    def is_configured(self):
        return bool(self.webhook_url)

    def send_image_for_enhancement(self, image_url, ref="", source=""):
        """
        Send a single image URL to n8n for enhancement.
        Returns enhanced image bytes or None on failure.
        """
        if not self.is_configured:
            print("[LOG] n8n not configured, skipping webhook")
            return None

        payload = {
            "action": "enhance_image",
            "image_url": image_url,
            "reference": ref,
            "source": source,
            "target_size": 1024,
            "upscale_factor": 4,
        }

        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        try:
            print(f"[LOG] Sending to n8n: {image_url[:60]}...")
            resp = requests.post(
                self.webhook_url,
                headers=headers,
                json=payload,
                timeout=self.timeout,
            )

            if resp.status_code == 200:
                data = resp.json()

                # n8n can return base64 image or a URL to the enhanced image
                if data.get("enhanced_base64"):
                    img_bytes = base64.b64decode(data["enhanced_base64"])
                    print(f"[LOG] Received enhanced image from n8n ({len(img_bytes)} bytes)")
                    return img_bytes
                elif data.get("enhanced_url"):
                    img_resp = requests.get(data["enhanced_url"], timeout=30)
                    if img_resp.status_code == 200:
                        return img_resp.content
                else:
                    print("[LOG] n8n response has no image data")
                    return None
            else:
                print(f"[LOG] n8n error: {resp.status_code} - {resp.text[:200]}")
                return None

        except Exception as e:
            print(f"[LOG] n8n request failed: {e}")
            return None

    def send_batch(self, image_urls, ref="", source="", callback=None):
        """
        Send multiple image URLs to n8n as a batch.
        Returns list of (url, enhanced_bytes_or_None).
        """
        if not self.is_configured:
            return [(url, None) for url in image_urls]

        # Try batch endpoint first
        payload = {
            "action": "enhance_batch",
            "images": [
                {"url": url, "reference": ref, "source": source}
                for url in image_urls
            ],
            "target_size": 1024,
            "upscale_factor": 4,
        }

        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        try:
            resp = requests.post(
                self.webhook_url,
                headers=headers,
                json=payload,
                timeout=self.timeout * 2,
            )

            if resp.status_code == 200:
                data = resp.json()
                results = data.get("results", [])
                output = []
                for i, url in enumerate(image_urls):
                    if i < len(results) and results[i].get("enhanced_base64"):
                        img_bytes = base64.b64decode(results[i]["enhanced_base64"])
                        output.append((url, img_bytes))
                    else:
                        output.append((url, None))
                    if callback:
                        callback(i + 1, len(image_urls), url)
                return output
        except Exception as e:
            print(f"[LOG] n8n batch failed, falling back to individual: {e}")

        # Fallback: send one by one
        results = []
        for i, url in enumerate(image_urls):
            enhanced = self.send_image_for_enhancement(url, ref, source)
            results.append((url, enhanced))
            if callback:
                callback(i + 1, len(image_urls), url)
        return results

    def send_product_data(self, product_data):
        """
        Send full product data to n8n for any custom workflow.
        Useful for triggering description generation, price alerts, etc.
        """
        if not self.is_configured:
            return None

        payload = {
            "action": "process_product",
            "product": {
                "reference": product_data.get("sku", ""),
                "title": product_data.get("title", ""),
                "price": product_data.get("price", ""),
                "source": product_data.get("source", ""),
                "url": product_data.get("url", ""),
                "image_count": len(product_data.get("images", [])),
                "images": product_data.get("images", [])[:5],
            },
        }

        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        try:
            resp = requests.post(
                self.webhook_url,
                headers=headers,
                json=payload,
                timeout=30,
            )
            if resp.status_code == 200:
                return resp.json()
        except Exception as e:
            print(f"[LOG] n8n product push failed: {e}")
        return None

    def test_connection(self):
        """Test if the n8n webhook is reachable."""
        if not self.is_configured:
            return False, "N8N_WEBHOOK_URL not set"

        try:
            resp = requests.post(
                self.webhook_url,
                headers={"Content-Type": "application/json"},
                json={"action": "ping"},
                timeout=10,
            )
            if resp.status_code == 200:
                return True, "Connected"
            else:
                return False, f"HTTP {resp.status_code}: {resp.text[:100]}"
        except Exception as e:
            return False, str(e)


# ──────────────────────────────────────────
# LOCAL ENHANCEMENT API SERVER (for n8n to call back)
# ──────────────────────────────────────────

def create_enhancement_api():
    """
    Creates a simple Flask-like endpoint that n8n can call
    to enhance images using the local ImageEnhancer.

    This runs as a separate process alongside the Streamlit app.
    n8n workflow: Webhook -> HTTP Request to this API -> Return result

    Usage:
        python -m src.n8n_bridge
    """
    try:
        from http.server import HTTPServer, BaseHTTPRequestHandler
        import json as _json
        from image_enhancer import ImageEnhancer
    except ImportError:
        import sys
        sys.path.append(os.path.dirname(__file__))
        from image_enhancer import ImageEnhancer
        from http.server import BaseHTTPRequestHandler

    enhancer = ImageEnhancer()

    class EnhanceHandler(BaseHTTPRequestHandler):
        def do_POST(self):
            content_len = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_len)
            data = json.loads(body)

            image_url = data.get("image_url", "")
            if not image_url:
                self._respond(400, {"error": "image_url required"})
                return

            enhanced = enhancer.enhance_from_url(image_url)
            if enhanced:
                img_bytes = enhancer.to_bytes(enhanced, fmt="PNG")
                b64 = base64.b64encode(img_bytes).decode("utf-8")
                self._respond(200, {
                    "enhanced_base64": b64,
                    "size": f"{enhanced.size[0]}x{enhanced.size[1]}",
                })
            else:
                self._respond(500, {"error": "Enhancement failed"})

        def _respond(self, code, data):
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(data).encode())

        def log_message(self, fmt, *args):
            print(f"[ENHANCE_API] {fmt % args}")

    return EnhanceHandler


if __name__ == "__main__":
    from http.server import HTTPServer
    port = int(os.getenv("ENHANCE_API_PORT", "8502"))
    handler = create_enhancement_api()
    server = HTTPServer(("0.0.0.0", port), handler)
    print(f"[LOG] Enhancement API running on http://localhost:{port}")
    print("[LOG] n8n can POST to http://localhost:{port}/ with {{\"image_url\": \"...\"}}")
    server.serve_forever()
