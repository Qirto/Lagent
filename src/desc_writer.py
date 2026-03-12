import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

class DescriptionWriter:
    """Cloud-only generator using OpenRouter with reasoning logic."""

    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.url = "https://openrouter.ai/api/v1/chat/completions"
        self.model = "openrouter/free"

    def write_description_stream(self, product_info, style_example=None):
        """Generates content using user-provided multi-call reasoning logic."""
        
        # LOG: INIT
        print(f"[LOG] >>> INITIALIZING SYNTHESIS FOR: {product_info.get('title')}")
        
        if not self.api_key:
            print("[LOG] !!! ERROR: API KEY MISSING !!!")
            yield "❌ ERROR: API KEY MISSING"
            return

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:8501",
            "X-Title": "NeuralAgent",
        }

        # LOG: CONSTRUCTING PROMPT
        prompt = self._build_prompt(product_info, style_example)
        print("[LOG] >>> NEURAL PROMPT CONSTRUCTED.")

        # LOG: HANDSHAKE
        print(f"[LOG] >>> DISPATCHING TO NODE: {self.model} (REASONING: ENABLED)")
        
        # Using the EXACT structure from user's example
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "reasoning": {"enabled": True},
            "stream": True
        }

        try:
            # LOG: POST REQUEST
            print("[LOG] >>> SENDING REQUEST PACKET...")
            response = requests.post(
                url=self.url,
                headers=headers,
                data=json.dumps(payload),
                stream=True,
                timeout=60
            )
            
            # LOG: STATUS
            print(f"[LOG] >>> STATUS CODE: {response.status_code}")
            
            if response.status_code == 200:
                print("[LOG] >>> CONNECTION ESTABLISHED. STREAMING DNA...")
                full_content = ""
                for line in response.iter_lines():
                    if line:
                        line_text = line.decode('utf-8')
                        if line_text.startswith("data: "):
                            data_str = line_text[6:]
                            if data_str == "[DONE]": 
                                print("[LOG] >>> PACKET STREAM FINISHED.")
                                break
                            try:
                                chunk = json.loads(data_str)
                                delta = chunk['choices'][0]['delta'].get('content', '')
                                if delta:
                                    full_content += delta
                                    yield delta
                            except:
                                continue
                
                print(f"[LOG] >>> SYNTHESIS COMPLETE. {len(full_content)} chars generated.")
                source_url = product_info.get('url')
                if source_url:
                    yield f"\n\n🔗 **Source:** [{product_info.get('source', 'Site Web')}]({source_url})"
            else:
                err_msg = response.text
                print(f"[LOG] !!! API REJECTION: {response.status_code} - {err_msg} !!!")
                if response.status_code == 401:
                    yield "❌ AUTH ERROR: Invalid or expired API key. Go to https://openrouter.ai/keys and generate a new key, then update your .env file."
                elif response.status_code == 429:
                    yield "❌ RATE LIMIT: Too many requests. Wait a moment and retry."
                else:
                    yield f"❌ API_ERROR_{response.status_code}: {err_msg}"
                
        except Exception as e:
            print(f"[LOG] !!! NETWORK CRASH: {e} !!!")
            yield f"❌ NETWORK_ERROR: {e}"

    def _build_prompt(self, info, style):
        dna = style if style else "Technical marketing with a focus on SEO and AI discovery (GEO)."
        return f"""
Act as a professional technical copywriter and SEO/GEO specialist.
Style to follow: {dna}
Language: French.

Product: {info.get('title')}
Price: {info.get('price')}
Specs: {info.get('specs')}

Your goal is to create content optimized for both Google (SEO) and AI discovery engines like Perplexity/ChatGPT (GEO).

STRUCTURE:
1. TL;DR Section: 3 concise bullet points summarizing the primary value. (Start with "## TL;DR")
2. Product Overview: Narrative description focusing on problem/solution.
3. Key Features List: Bullet points with specific technical advantages.
4. Specs Table: Clean markdown table.
5. FAQ Section: 3 common questions and direct answers about this product. (Start with "## FAQ")

GUIDELINES:
- Use clear, declarative statements.
- Ensure stand-alone sections that AI can quote.
- Include a definition box "Qu'est-ce que [Product Name]?"
- Optimize for citations by being factual and direct.

Synthesize:
"""

if __name__ == "__main__":
    print("[LOG] DescriptionWriter Node Active.")
