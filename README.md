# Lagent: Agentic AI & Cloud Synthesis 🚀

Lagent is a high-performance **Agentic AI** designed to automate the transition from physical PDF catalogs to digital-ready content. It combines agentic web scraping, diffusion-based neural image enhancement, and robust category-based structural synthesis to deliver a complete product discovery and optimization pipeline.

![Streamlit](https://img.shields.io/badge/Frontend-Streamlit-FF4B4B?style=for-the-badge&logo=Streamlit&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![HuggingFace](https://img.shields.io/badge/%F0%9F%A4%97%20Hugging%20Face-Inference-FFD21E?style=for-the-badge)

## ✨ Key Features

- **Agentic PDF Extraction:** Robust parsing of complex PDF catalog tables into structured product databases.
- **Advanced Scored Matching:** New matching engine with tokenized reference scoring and digit-boundary guards to ensure high-accuracy product discovery.
- **Parallel Tunisian Scraper:** High-speed parallel scraping across 9+ major Tunisian retailers (MyTek, Tunisianet, Wiki, MegaPC, etc.) with automatic fallback to product name (**designation**) search.
- **Dual Description Synthesis:** Generates both a **Description Courte** (scraped directly from retailer highlights) and a structured **Description Longue** (intelligently synthesized from technical specs).
- **Finegrain Neural Enhancer:** Integrated diffusion-based upscaling. Performs **4x Neural Upscaling** to 1024x1024 with instant thumbnail preview generation for a lag-free gallery experience.
- **Neural Performance Engine:** Optimized UI featuring **ZIP Caching**, image thumbnails, and result pagination to handle large product batches with zero latency.
- **Unified Cyberpunk UI:** A consistent, professional design system across all pages, featuring Orbitron typography and WCAG AA-compliant accessibility.
- **Browser Persistence:** Settings and API keys are persisted via **localStorage**, ensuring they survive site updates and work seamlessly across sessions.

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
3. **Process:** Watch the agent score 9 parallel sites and apply Neural enhancements in real-time.
4. **Results:** Review dual descriptions, switch angles instantly, and export the entire batch as a structured ZIP.

## 📁 Project Structure

- `app.py`: Main Streamlit entry point with optimized orchestration.
- `src/`:
  - `scraper.py`: Advanced scored matching and multi-site extraction logic.
  - `desc_writer.py`: Smart structural description synthesizer.
  - `theme.py`: Unified design system and security sanitization.
  - `image_enhancer.py`: Professional upscaling pipeline powered by Finegrain Diffusion.
  - `pdf_processor.py`: PDF table extraction engine.
- `pages/`:
  - `Image_Enhancer.py`: Dedicated manual neural upscaling tool.
  - `4_Settings.py`: Configuration with browser localStorage integration.

---
*Built by the Advanced Agentic Coding Team.*
