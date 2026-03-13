import io
import os
import time
import requests
from PIL import Image
from dotenv import load_dotenv

load_dotenv()

class ImageEnhancer:
    """
    Agentic Image Enhancer focused on Hugging Face Inference API.
    Optimized for product images using SwinIR or Real-ESRGAN.
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
        Main entry point that decides between local fallback or HF AI.
        """
        token = hf_token or self.api_token
        
        # If no token, we can only do local basic resize (fallback)
        if not token:
            print("[LOG] HF_API_TOKEN missing. Using basic local fallback.")
            return self._local_fallback(image_url)
            
        return self.enhance_hf_api(image_url, token)

    def enhance_hf_api(self, image_url, token):
        """
        Deep AI enhancement via Hugging Face Inference API with Pacing.
        Yields status dictionaries for UI updates, then returns PIL Image.
        """
        headers = {"Authorization": f"Bearer {token}"}
        
        try:
            # 1. Download original image
            img_resp = requests.get(image_url, timeout=15)
            if img_resp.status_code != 200:
                yield self._local_fallback(image_url)
                return
            
            # 2. Call HF API
            print(f"[LOG] Triggering HF AI Upscale: {self.HF_MODEL}")
            
            max_retries = 3
            for attempt in range(max_retries):
                response = requests.post(self.HF_API_URL, headers=headers, data=img_resp.content)
                
                if response.status_code == 200:
                    yield Image.open(io.BytesIO(response.content))
                    return
                
                elif response.status_code == 503:
                    wait_time = 20
                    yield {"status": "waiting", "msg": f"⏳ AI model is loading on Hugging Face... Resuming in {wait_time}s"}
                    time.sleep(wait_time)
                    
                elif response.status_code == 429:
                    wait_time = 60
                    yield {"status": "waiting", "msg": f"⏳ Hugging Face free limit reached. Pacing for {wait_time}s to avoid crash..."}
                    time.sleep(wait_time)
                
                else:
                    break
                    
            yield self._local_fallback(image_url)
            
        except Exception as e:
            print(f"[LOG] Enhancement Exception: {e}")
            yield self._local_fallback(image_url)

    def _local_fallback(self, image_url):
        """Basic resize if AI is unavailable."""
        try:
            resp = requests.get(image_url, timeout=10)
            img = Image.open(io.BytesIO(resp.content)).convert("RGB")
            img.thumbnail(self.target_size, Image.Resampling.LANCZOS)
            
            # Create white canvas
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
