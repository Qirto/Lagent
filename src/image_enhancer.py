import io
import os
import time
import requests
from PIL import Image
from dotenv import load_dotenv

load_dotenv()

class ImageEnhancer:
    """
    Agentic Image Enhancer focused strictly on Hugging Face Inference API.
    Optimized for product images using SwinIR.
    """

    DEFAULT_SIZE = (1024, 1024)
    # caidas/swinir-real-sr-x4 is excellent for product textures
    HF_MODEL = "caidas/swinir-real-sr-x4"
    HF_API_URL = f"https://api-inference.huggingface.co/models/{HF_MODEL}"

    def __init__(self, target_size=None, api_token=None):
        self.target_size = target_size or self.DEFAULT_SIZE
        self.api_token = api_token or os.getenv("HF_API_TOKEN")

    def enhance_from_url(self, image_url, hf_token=None):
        """
        Main entry point that triggers HF AI Upscale.
        """
        token = hf_token or self.api_token
        
        if not token:
            print("[LOG] HF_API_TOKEN missing. HF Enhancement impossible.")
            # Basic fallback if no token provided
            return self._local_enhance(image_url)
            
        # For simple calls, we consume the generator and return the final image
        result = self.enhance_hf_api(image_url, token)
        final_img = None
        for item in result:
            if not isinstance(item, dict):
                final_img = item
        return final_img

    def enhance_hf_api(self, image_url, token):
        """
        Deep AI enhancement via Hugging Face Inference API with Pacing.
        Yields status dictionaries for UI updates, then yields PIL Image.
        """
        headers = {"Authorization": f"Bearer {token}"}
        
        try:
            # 1. Download original image
            img_resp = requests.get(image_url, timeout=15)
            if img_resp.status_code != 200:
                yield self._local_enhance(image_url)
                return
            
            # 2. Call HF API with retry logic
            print(f"[LOG] Triggering HF AI Upscale: {self.HF_MODEL}")
            
            max_retries = 3
            for attempt in range(max_retries):
                response = requests.post(self.HF_API_URL, headers=headers, data=img_resp.content)
                
                if response.status_code == 200:
                    yield Image.open(io.BytesIO(response.content))
                    return
                
                elif response.status_code == 503:
                    wait_time = 20
                    yield {"status": "waiting", "msg": f"⏳ Hugging Face is loading the AI model... Resuming in {wait_time}s", "wait": wait_time}
                    time.sleep(wait_time)
                    
                elif response.status_code == 429:
                    wait_time = 60
                    yield {"status": "waiting", "msg": f"⏳ HF Rate limit reached. Pacing for {wait_time}s to avoid crash...", "wait": wait_time}
                    time.sleep(wait_time)
                
                else:
                    print(f"[LOG] HF API Error {response.status_code}: {response.text}")
                    break
                    
            # Final fallback if all HF attempts fail
            yield self._local_enhance(image_url)
            
        except Exception as e:
            print(f"[LOG] Enhancement Exception: {e}")
            yield self._local_enhance(image_url)

    def enhance_pil(self, img_pil, token=None):
        """
        Enhance an existing PIL Image using HF API.
        """
        token = token or self.api_token
        if not token:
            return img_pil # No token, no AI
            
        headers = {"Authorization": f"Bearer {token}"}
        buf = io.BytesIO()
        img_pil.save(buf, format="PNG")
        
        try:
            response = requests.post(self.HF_API_URL, headers=headers, data=buf.getvalue())
            if response.status_code == 200:
                return Image.open(io.BytesIO(response.content))
        except:
            pass
        return img_pil

    def _local_enhance(self, image_url):
        """Basic resize if AI is unavailable or local mode selected."""
        try:
            resp = requests.get(image_url, timeout=10)
            img = Image.open(io.BytesIO(resp.content)).convert("RGB")
            # Simple pad to square
            img.thumbnail(self.target_size, Image.Resampling.LANCZOS)
            bg = Image.new("RGB", self.target_size, (255, 255, 255))
            offset = ((self.target_size[0] - img.size[0]) // 2, (self.target_size[1] - img.size[1]) // 2)
            bg.paste(img, offset)
            return bg
        except:
            return None

    def to_bytes(self, img, fmt="PNG"):
        if not img or not isinstance(img, Image.Image): return None
        buf = io.BytesIO()
        img.save(buf, format=fmt)
        return buf.getvalue()
