import io
import os
import time
import requests
from PIL import Image, ImageFilter, ImageEnhance
from dotenv import load_dotenv
from gradio_client import Client, handle_file

load_dotenv()

class ImageEnhancer:
    """
    Agentic Image Enhancer focused strictly on Finegrain Image Enhancer (Hugging Face Space).
    Optimized for professional 1024x1024 output with 4x Neural detail.
    """

    DEFAULT_SIZE = (1024, 1024)
    SPACE_ID = "finegrain/finegrain-image-enhancer"

    def __init__(self, target_size=None, api_token=None):
        self.target_size = target_size or self.DEFAULT_SIZE
        self.api_token = api_token or os.getenv("HF_API_TOKEN")
        try:
            self.client = Client(self.SPACE_ID, token=self.api_token)
        except Exception as e:
            print(f"[LOG] Gradio Client Init Error: {e}")
            self.client = None

    def enhance_from_url(self, image_url, hf_token=None):
        """Main entry point for single URL enhancement."""
        token = hf_token or self.api_token
        try:
            resp = requests.get(image_url, timeout=15)
            if resp.status_code != 200: return None
            temp_in = os.path.abspath("temp_input_url.png")
            with open(temp_in, "wb") as f:
                f.write(resp.content)
            
            # Consume generator
            final_img = None
            for item in self.enhance_hf_api(temp_in, token):
                if isinstance(item, Image.Image):
                    final_img = item
            return final_img
        except Exception as e:
            print(f"[LOG] enhance_from_url Error: {e}")
            return None

    def _enhance_core_generator(self, image_path, token):
        """Calls Finegrain Space via Gradio with physical 4x upscale."""
        abs_image_path = os.path.abspath(image_path)
        if not self.client:
            try:
                self.client = Client(self.SPACE_ID, token=token)
            except Exception as e:
                yield {"status": "error", "msg": f"Neural Link Error: {str(e)}"}
                return

        yield {"status": "waiting", "msg": "⏳ Initializing Finegrain Neural Engine...", "wait": 5}
        
        try:
            img = Image.open(abs_image_path).convert("RGB")
            # For 4x upscale to be stable, we ensure input is around 256-512px.
            # 256 * 4 = 1024 (Exact)
            # 512 * 4 = 2048 (Downsampled to 1024)
            if max(img.size) > 512:
                img.thumbnail((512, 512), Image.Resampling.LANCZOS)
                img.save(abs_image_path, quality=100)

            print(f"[LOG] Processing image for 4x Neural Upscale: {abs_image_path}")

            # Using exact parameter types (ints for counts/seeds) to avoid RuntimeError
            result = self.client.predict(
                input_image=handle_file(abs_image_path),
                prompt="extremely detailed product photography, sharp focus, professional lighting, crisp text, high definition",
                negative_prompt="blurry, distorted, low quality, noise, grain, fuzzy, lowres",
                seed=42,             # int
                upscale_factor=4,    # int (x4 as requested)
                controlnet_scale=0.6,
                controlnet_decay=1.0,
                condition_scale=6.0,
                tile_width=112,      # int
                tile_height=144,     # int
                denoise_strength=0.35,
                num_inference_steps=18, # int
                solver="DDIM",
                api_name="/process"
            )
            
            if result and isinstance(result, (list, tuple)) and len(result) > 1:
                # result[1] is the enhanced image path
                after_path = result[1]
                enh_img = Image.open(after_path).convert("RGB")
                yield self._force_target_format(enh_img)
            else:
                print(f"[LOG] Neural engine returned invalid result: {result}")
                yield None
        except Exception as e:
            print(f"[LOG] Finegrain API Error: {str(e)}")
            yield None

    def enhance_hf_api(self, image_input, token):
        """Adapter for existing UI code."""
        if isinstance(image_input, str) and image_input.startswith("http"):
            try:
                resp = requests.get(image_input, timeout=15)
                temp_in = os.path.abspath("temp_input_hf.png")
                with open(temp_in, "wb") as f:
                    f.write(resp.content)
                yield from self._enhance_core_generator(temp_in, token)
            except:
                yield None
        else:
            yield from self._enhance_core_generator(image_input, token)

    def enhance_pil_generator(self, img_pil, token=None):
        """Enhances a PIL image via generator."""
        token = token or self.api_token
        try:
            temp_path = os.path.abspath("temp_input_pil.png")
            img_pil.save(temp_path, quality=100)
            yield from self._enhance_core_generator(temp_path, token)
        except Exception as e:
            print(f"[LOG] enhance_pil_generator Error: {e}")
            yield None

    def enhance_pil(self, img_pil, token=None):
        """Blocking wrapper for PIL enhancement."""
        gen = self.enhance_pil_generator(img_pil, token)
        final_img = None
        for item in gen:
            if isinstance(item, Image.Image):
                final_img = item
        return final_img

    def _force_target_format(self, img):
        """Supersampling finish: High-detail downscale to 1024x1024 with sharpness pass."""
        if not img: return None
        
        # 1. Resize to 1024x1024 (LANCZOS preserves neural details from 4x upscale)
        img = img.resize(self.target_size, Image.Resampling.LANCZOS)
        
        # 2. Precision definition pass
        img = img.filter(ImageFilter.UnsharpMask(radius=0.7, percent=150, threshold=1))
        
        # 3. Micro-detail enhancement
        enhancer_s = ImageEnhance.Sharpness(img)
        img = enhancer_s.enhance(1.5)
        
        return img

    def to_bytes(self, img, fmt="PNG"):
        if not img or not isinstance(img, Image.Image): return None
        buf = io.BytesIO()
        img.save(buf, format=fmt, quality=100)
        return buf.getvalue()
