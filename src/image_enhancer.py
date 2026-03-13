import io
import os
import requests
from PIL import Image, ImageFilter


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
        Refined enhancement pipeline using AdvancedImageEnhancer logic if available.
        Focuses on clean upscaling without destructive cropping.
        """
        if not isinstance(img, Image.Image):
            return None

        analysis = self.analyze(img)
        orig_w, orig_h = img.size
        target_w, target_h = self.target_size
        
        print(f"[LOG] Enhancing: {orig_w}x{orig_h} -> {target_w}x{target_h}")

        try:
            # Try to use the advanced image enhancer
            import cv2
            import numpy as np
            import sys
            import os
            
            # Make sure we can import advanced_enhancer
            sys.path.append(os.path.dirname(__file__))
            from advanced_enhancer import AdvancedImageEnhancer, EnhancementConfig, EnhancementMode
            
            # Convert PIL Image to OpenCV format (BGR)
            open_cv_image = np.array(img)
            # Convert RGB to BGR 
            open_cv_image = open_cv_image[:, :, ::-1].copy()
            
            # Use advanced enhancer config
            config = EnhancementConfig(
                target_size=self.target_size,
                mode=EnhancementMode.NATURAL,
                denoise_strength=2.0,
                sharpening_strength=1.1,
            )
            adv_enhancer = AdvancedImageEnhancer(config=config)
            
            # Process using advanced methods
            # Use the correct pipeline method
            result = adv_enhancer.process_image_array(open_cv_image)
            if result is not None:
                # Convert back to PIL
                enhanced_rgb = cv2.cvtColor(result, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(enhanced_rgb)
                print("[LOG] Advanced enhancement successful.")
                return img
                
        except ImportError as e:
            print(f"[LOG] AdvancedImageEnhancer not fully available, using standard PIL pipeline. ({e})")
        except Exception as e:
            print(f"[LOG] Error in advanced enhancement: {e}. Falling back to standard PIL pipeline.")

        # Step 1: Clean upscale using LANCZOS
        # We don't want to over-filter as it causes artifacts.
        if orig_w < target_w or orig_h < target_h:
            img = self._resize_contain(img, self.target_size)
        else:
            # If it's already larger, just downsample smoothly
            img.thumbnail(self.target_size, LANCZOS)
            img = self._resize_contain(img, self.target_size)
            
        # Very light sharpening to recover edges lost in resize
        img = img.filter(ImageFilter.UnsharpMask(radius=0.5, percent=50, threshold=5))

        return img

    def _resize_contain(self, img, target_size, bg_color=(255, 255, 255)):
        """
        Resize to fit within target_size while maintaining aspect ratio,
        then pad the rest with background color.
        Prevents cutting off product edges (unlike center crop).
        """
        tw, th = target_size
        img.thumbnail((tw, th), LANCZOS)
        
        iw, ih = img.size
        # Create a new image with the target size and background color
        new_img = Image.new("RGB", (tw, th), bg_color)
        
        # Paste the resized image into the center
        left = (tw - iw) // 2
        top = (th - ih) // 2
        new_img.paste(img, (left, top))

        return new_img

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
