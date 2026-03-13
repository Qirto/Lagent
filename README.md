# Lagent: Agentic AI & Cloud Synthesis 🚀

Lagent is a high-performance **Agentic AI** designed to automate the transition from physical PDF catalogs to digital-ready content. It combines agentic web scraping, diffusion-based neural image enhancement, and robust category-based structural synthesis to deliver a complete product discovery and optimization pipeline.

![Streamlit](https://img.shields.io/badge/Frontend-Streamlit-FF4B4B?style=for-the-badge&logo=Streamlit&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![HuggingFace](https://img.shields.io/badge/%F0%9F%A4%97%20Hugging%20Face-Inference-FFD21E?style=for-the-badge)

## ✨ Key Features

- **Agentic PDF Extraction:** Robust parsing of complex PDF catalog tables into structured product databases.
- **Parallel Tunisian Scraper:** High-speed parallel scraping across 9+ major Tunisian retailers (MyTek, Tunisianet, Wiki, MegaPC, etc.) with advanced price extraction and regex-based alias matching.
- **Global Fallback Engine:** Advanced Google-backed fallback that finds products on *any* Tunisian website if primary retailers fail.
- **Finegrain Neural Enhancer:** Integrated state-of-the-art diffusion-based upscaling via Hugging Face Spaces. Performs physical **4x Neural Upscaling** with high-clarity supersampling and multi-pass sharpening for professional 1024x1024 results optimized for product text and detail.
- **Automated Structural Synthesis:** Automatically generates clean, highly readable, category-specific product descriptions using OpenRouter (Gemini/Llama) or high-speed local templates.
- **Cyberpunk Neo-Brutalist UI:** A striking, highly-polished user interface featuring Orbitron typography, glassmorphism overlays, and neural scanline effects for maximum workflow immersion.
- **Batch ZIP Export:** One-click download of entire catalogs with smart renaming (`[Product] - [Color].png`) and formatted markdown descriptions.

## 🛠️ Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Qirto/Lagent.git
   cd Lagent
   ```

2. **Set up the environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configure Secrets:**
   Create a `.env` file in the root directory or use the **Settings** page in the app.
   ```env
   OPENROUTER_API_KEY=your_openrouter_key
   HF_API_TOKEN=your_huggingface_token
   ```

## 🚀 Usage

Run the application using Streamlit:
```bash
streamlit run app.py
```

1. **Upload:** Drop your product catalog PDF.
2. **Configure:** Select categories and trigger the extraction pipeline.
3. **Process:** Watch the agent scrape 9 parallel sites and apply Neural enhancements in real-time.
4. **Results:** Review the extracted pricing, descriptions, and upscaled thumbnails before exporting.

## 📁 Project Structure

- `app.py`: Main Streamlit entry point featuring a custom Cyberpunk design system.
- `src/`:
  - `scraper.py`: Agentic multi-site scraping logic with fallback discovery and fuzzy text matching.
  - `desc_writer.py`: AI-powered structural format generator.
  - `image_enhancer.py`: Professional upscaling pipeline powered by Finegrain Diffusion (Gradio).
  - `pdf_processor.py`: PDF table extraction engine.
  - `n8n_bridge.py`: Integration module for external automation workflows.
- `pages/`:
  - `Image_Enhancer.py`: Dedicated deep-dive tool for manual neural upscaling.
  - `4_Settings.py`: Persistent configuration and neural link testing.

---
*Built by the Advanced Agentic Coding Team.*
