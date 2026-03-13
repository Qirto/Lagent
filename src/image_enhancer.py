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
    Optimized for product images and text clarity using SwinIR 4x.
    """

    DEFAULT_SIZE = (1024, 1024)
    # caidas/swinir-real-sr-x4 is specifically for 4x upscale and noise removal
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
            print("[LOG] HF_API_TOKEN missing. Performing high-quality local upscale.")
            return self._local_high_quality_upscale_from_url(image_url)
            
        # For simple calls, we consume the generator and return the final image
        result = self.enhance_hf_api(image_url, token)
        final_img = None
        for item in result:
            if not isinstance(item, dict):
                final_img = item
        return final_img

    def enhance_hf_api(self, image_url, token):
        """
        Deep AI enhancement via Hugging Face Inference API with 4x focus and pacing.
        """
        # X-Wait-For-Model tells HF to wait until the model is loaded instead of returning 503
        headers = {
            "Authorization": f"Bearer {token}",
            "X-Wait-For-Model": "true"
        }
        
        try:
            # 1. Download original image
            img_resp = requests.get(image_url, timeout=15)
            if img_resp.status_code != 200:
                yield self._local_high_quality_upscale_from_url(image_url)
                return
            
            # 2. Call HF API with pacing/retry logic
            print(f"[LOG] Triggering Deep AI 4x Upscale: {self.HF_MODEL}")
            
            max_retries = 3
            for attempt in range(max_retries):
                response = requests.post(self.HF_API_URL, headers=headers, data=img_resp.content)
                
                if response.status_code == 200:
                    ai_img = Image.open(io.BytesIO(response.content)).convert("RGB")
                    # Force 1024x1024 output format for the UI
                    return self._force_target_format(ai_img)
                
                elif response.status_code == 503 or response.status_code == 429:
                    wait_time = 60 if response.status_code == 429 else 20
                    yield {"status": "waiting", "msg": f"⏳ Pacing AI request ({response.status_code})... Resuming in {wait_time}s", "wait": wait_time}
                    time.sleep(wait_time)
                
                else:
                    print(f"[LOG] HF API Error {response.status_code}: {response.text}")
                    break
                    
            yield self._local_high_quality_upscale_from_url(image_url)
            
        except Exception as e:
            print(f"[LOG] Enhancement Exception: {e}")
            yield self._local_high_quality_upscale_from_url(image_url)

    def enhance_pil(self, img_pil, token=None):
        """
        Enhance an existing PIL Image using HF API and force target size.
        """
        token = token or self.api_token
        if not token:
            return self._force_target_format(img_pil)
            
        headers = {
            "Authorization": f"Bearer {token}",
            "X-Wait-For-Model": "true"
        }
        buf = io.BytesIO()
        img_pil.save(buf, format="PNG")
        
        try:
            response = requests.post(self.HF_API_URL, headers=headers, data=buf.getvalue())
            if response.status_code == 200:
                ai_img = Image.open(io.BytesIO(response.content)).convert("RGB")
                return self._force_target_format(ai_img)
        except:
            pass
        return self._force_target_format(img_pil)

    def _force_target_format(self, img):
        """Ensures image is high quality and fits exactly 1024x1024."""
        if not img: return None
        # 1. Resize to fit inside 1024x1024 while preserving 4x upscale quality
        img.thumbnail(self.target_size, Image.Resampling.LANCZOS)
        # 2. Center on white background
        bg = Image.new("RGB", self.target_size, (255, 255, 255))
        offset = ((self.target_size[0] - img.size[0]) // 2, (self.target_size[1] - img.size[1]) // 2)
        bg.paste(img, offset)
        return bg

    def _local_high_quality_upscale_from_url(self, image_url):
        """Local fallback that performs high-quality 4x upscale then format."""
        try:
            resp = requests.get(image_url, timeout=10)
            img = Image.open(io.BytesIO(resp.content)).convert("RGB")
            # Create high quality 4x upscale locally before formatting
            upscaled_size = (img.size[0] * 4, img.size[1] * 4)
            img = img.resize(upscaled_size, Image.Resampling.LANCZOS)
            return self._force_target_format(img)
        except:
            return None

    def to_bytes(self, img, fmt="PNG"):
        if not img or not isinstance(img, Image.Image): return None
        buf = io.BytesIO()
        img.save(buf, format=fmt, quality=100) # Maximum quality for PNG/JPEG
        return buf.getvalue()
