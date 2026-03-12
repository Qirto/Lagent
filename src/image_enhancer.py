import io
import os
import requests
from PIL import Image, ImageFilter, ImageEnhance


try:
    LANCZOS = Image.Resampling.LANCZOS
except (AttributeError, NameError):
    try:
        LANCZOS = Image.LANCZOS
    except (AttributeError, NameError):
        # Fallback to high quality resampling
        LANCZOS = 1 


class ImageEnhancer:
    """
    High-quality image upscaler and enhancer.
    Uses Pillow LANCZOS resampling with sharpening passes
    to produce clean 1024x1024 product images.
    Supports cloud enhancement via inference.sh.
    """

    DEFAULT_SIZE = (1024, 1024)
    UPSCALE_FACTOR = 4

    def __init__(self, target_size=None):
        self.target_size = target_size or self.DEFAULT_SIZE

    def enhance_cloud(self, image_url, app_id="falai/topaz-image-upscaler"):
        """
        Upscale image using inference.sh cloud models.
        Requires INFSH_API_KEY in .env.
        """
        api_key = os.getenv("INFSH_API_KEY")
        if not api_key:
            print("[LOG] INFSH_API_KEY not found in .env")
            return None
        
        try:
            from inferencesh import Inference
            client = Inference(api_key=api_key)
            
            # The SDK requires a pinned version (short ID)
            # If user provides a full ID with @, use it. Otherwise, we might need to find one.
            # For now, we'll try running it and handle errors.
            print(f"[LOG] Running cloud upscale: {app_id}")
            result = client.run({
                "app": app_id,
                "input": {"image_url": image_url}
            })
            
            # The result is expected to be a dict when wait=True (default)
            if not isinstance(result, dict):
                print(f"[LOG] Cloud upscale unexpected return type: {type(result)}")
                return None

            output = result.get("output")
            if output:
                # Topaz usually returns {'image': 'url'} or {'url': 'url'}
                url = None
                if isinstance(output, dict):
                    url = output.get("image") or output.get("url") or output.get("output_url")
                elif isinstance(output, str) and output.startswith("http"):
                    url = output
                
                if url:
                    print(f"[LOG] Cloud upscale success: {url}")
                    resp = requests.get(url, timeout=30)
                    if resp.status_code == 200:
                        return Image.open(io.BytesIO(resp.content)).convert("RGB")
            
            print(f"[LOG] Cloud upscale returned no image URL: {result}")
            return None
        except Exception as e:
            print(f"[LOG] Cloud enhancement failed: {e}")
            return None

    def enhance_from_url(self, url, profile="balanced", timeout=15):
        """Download an image from a URL and enhance it."""
        try:
            resp = requests.get(url, timeout=timeout)
            resp.raise_for_status()
            img = Image.open(io.BytesIO(resp.content)).convert("RGB")
            return self.enhance(img, profile=profile)
        except Exception as e:
            print(f"[LOG] Image download failed: {e}")
            return None

    def enhance_from_bytes(self, data):
        """Enhance an image from raw bytes."""
        try:
            img = Image.open(io.BytesIO(data)).convert("RGB")
            return self.enhance(img)
        except Exception as e:
            print(f"[LOG] Image load failed: {e}")
            return None

    def analyze(self, img):
        """Analyzes image properties to determine the best enhancement strategy."""
        w, h = img.size
        # Simple heuristic for quality/blur
        # Higher values usually mean more edges/detail
        edge_data = img.filter(ImageFilter.FIND_EDGES).getextrema()
        # This is a very basic proxy for 'noise' or 'complexity'
        complexity = sum(e[1] for e in edge_data) / 3
        
        return {
            "resolution": f"{w}x{h}",
            "is_low_res": w < 800 or h < 600,
            "complexity": round(complexity, 2),
            "suggested_upscale": 4 if w < 500 else 2
        }

    def enhance(self, img, profile="balanced"):
        """
        Refined enhancement pipeline with specialized profiles.
        Focuses on clarity and natural look, avoiding over-sharpening.
        """
        if not isinstance(img, Image.Image):
            return None

        analysis = self.analyze(img)
        orig_w, orig_h = img.size
        target_w, target_h = self.target_size
        
        print(f"[LOG] Enhancing ({profile}): {orig_w}x{orig_h} -> {target_w}x{target_h}")

        # --- Profile Specific Configurations ---
        # Values tuned for clarity without artifacts
        cfg_map = {
            "balanced":    {"denoise": True,  "sharp": 1.05, "contrast": 1.02, "unsharp_r": 0.5, "unsharp_p": 100},
            "screenshot":  {"denoise": False, "sharp": 1.15, "contrast": 1.05, "unsharp_r": 1.0, "unsharp_p": 120},
            "photography": {"denoise": True,  "sharp": 1.0,  "contrast": 1.0,  "unsharp_r": 0.3, "unsharp_p": 80},
            "print":       {"denoise": True,  "sharp": 1.2,  "contrast": 1.1,  "unsharp_r": 1.2, "unsharp_p": 140},
            "social":      {"denoise": True,  "sharp": 1.1,  "contrast": 1.05, "unsharp_r": 0.8, "unsharp_p": 100},
        }
        cfg = cfg_map.get(profile, cfg_map["balanced"])

        # Step 1: Subtle noise reduction for low-res sources
        if cfg["denoise"] or analysis["is_low_res"]:
            # SMOOTH is less aggressive than SMOOTH_MORE
            img = img.filter(ImageFilter.SMOOTH)
        
        # Step 2: Multi-stage upscale (Super-Sampling)
        # Scale to 1.5x target instead of 2x to reduce blur from extreme downscaling later
        mid_w, mid_h = int(target_w * 1.5), int(target_h * 1.5)
        img = img.resize((mid_w, mid_h), LANCZOS)
        
        # Step 3: Targeted Sharpening (Unsharp Mask)
        # Using smaller radius and lower percent for natural clarity
        img = img.filter(ImageFilter.UnsharpMask(radius=cfg["unsharp_r"], percent=cfg["unsharp_p"], threshold=3))
        
        if profile == "screenshot":
            # DETAIL adds local contrast without haloing too much
            img = img.filter(ImageFilter.DETAIL)

        # Step 4: Visual optimization
        img = ImageEnhance.Contrast(img).enhance(cfg["contrast"])
        img = ImageEnhance.Sharpness(img).enhance(cfg["sharp"])
        img = ImageEnhance.Color(img).enhance(1.02) # Very subtle color boost

        # Step 5: Final resize to target with center crop
        img = self._resize_cover(img, self.target_size)
        
        # Step 6: Final crispness pass (Removed EDGE_ENHANCE as it creates halos)
        # Instead, use a very subtle sharpen on the final size
        img = img.filter(ImageFilter.SHARPEN) if profile == "screenshot" else img

        return img

    def _resize_cover(self, img, target_size):
        """
        Resize to fill the target size while maintaining aspect ratio,
        then center-crop to exact dimensions. Produces clean square output.
        """
        tw, th = target_size
        iw, ih = img.size

        # Calculate scale to cover
        scale = max(tw / iw, th / ih)
        new_w = int(iw * scale)
        new_h = int(ih * scale)

        img = img.resize((new_w, new_h), LANCZOS)

        # Center crop
        left = (new_w - tw) // 2
        top = (new_h - th) // 2
        img = img.crop((left, top, left + tw, top + th))

        return img

    def to_bytes(self, img, fmt="PNG", quality=95):
        """Convert a PIL Image to bytes."""
        buf = io.BytesIO()
        img.save(buf, format=fmt, quality=quality)
        buf.seek(0)
        return buf.getvalue()

    def save(self, img, path, fmt="PNG", quality=95):
        """Save an enhanced image to disk."""
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        img.save(path, format=fmt, quality=quality)
        print(f"[LOG] Saved enhanced image: {path}")

    def batch_enhance_urls(self, urls, callback=None):
        """
        Enhance a list of image URLs.
        Returns list of (url, enhanced_image) tuples.
        callback(i, total, url) is called after each image.
        """
        results = []
        total = len(urls)
        for i, url in enumerate(urls):
            enhanced = self.enhance_from_url(url)
            results.append((url, enhanced))
            if callback:
                callback(i + 1, total, url)
        return results


if __name__ == "__main__":
    print("[LOG] ImageEnhancer module ready.")
