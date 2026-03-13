# Lagent: Agentic AI & Cloud Synthesis 🚀

Lagent is a high-performance **Agentic AI** designed to automate the transition from physical PDF catalogs to digital-ready content. It combines agentic web scraping, neural image enhancement (Vulkan/Volcan), and LLM-powered synthesis to deliver a complete product discovery and optimization pipeline.

![Streamlit](https://img.shields.io/badge/Frontend-Streamlit-FF4B4B?style=for-the-badge&logo=Streamlit&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![OpenRouter](https://img.shields.io/badge/AI-OpenRouter-7c6aef?style=for-the-badge)

## ✨ Key Features

- **Agentic PDF Extraction:** Robust parsing of complex PDF catalog tables into structured product databases.
- **Parallel Tunisian Scraper:** High-speed parallel scraping across 8+ major Tunisian retailers (MyTek, Tunisianet, Wiki, etc.).
- **Global Fallback Engine:** Advanced Google-backed fallback that finds products on *any* Tunisian website if primary retailers fail.
- **Volcan Neural Upscaler:** Integrated image enhancement using local processing for professional 1024x1024 product visuals.
- **BYOK (Bring Your Own Key):** Full support for OpenRouter API integration with session-based model switching (Gemini, Claude, Llama).
- **Instant MyTek-Style Gallery:** Professional e-commerce UI with instant image switching and multi-angle views.
- **Smart Synthesis Fallback:** Automatically reverts to raw site descriptions if AI reasoning is unavailable, ensuring 100% data availability.
- **Batch ZIP Export:** One-click download of entire catalogs with smart renaming (`[Product] - [Color].png`).

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
   Create a `.env` file in the root directory:
   ```env
   OPENROUTER_API_KEY=your_key_here
   ```

## 🚀 Usage

Run the application using Streamlit:
```bash
streamlit run app.py
```

1. **Upload:** Drop your product catalog PDF.
2. **Configure:** Select categories and choose your AI model in the Settings tab.
3. **Process:** Watch the agent scrape and enhance images in real-time.
4. **Results:** Download the high-res ZIP package for your e-commerce store.

## 📁 Project Structure

- `app.py`: Main Streamlit entry point and UI orchestrator.
- `src/`:
  - `scraper.py`: Agentic multi-site scraping logic with fallback discovery.
  - `desc_writer.py`: LLM-powered description synthesis.
  - `image_enhancer.py`: Image upscaling and optimization.
  - `pdf_processor.py`: PDF table extraction engine.
- `pages/`: Multi-page application modules (Settings, Discovery, Enhancer).

---
*Built by the Advanced Agentic Coding Team.*
