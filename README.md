# Lagent: Agentic AI & Cloud Synthesis 🚀

Lagent is a high-performance **Agentic AI** designed to automate the transition from physical PDF catalogs to digital-ready content. It combines agentic web scraping, advanced computer vision image enhancement, and robust category-based structural synthesis to deliver a complete product discovery and optimization pipeline.

![Streamlit](https://img.shields.io/badge/Frontend-Streamlit-FF4B4B?style=for-the-badge&logo=Streamlit&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![OpenCV](https://img.shields.io/badge/Vision-OpenCV-5C3EE8?style=for-the-badge&logo=opencv&logoColor=white)

## ✨ Key Features

- **Agentic PDF Extraction:** Robust parsing of complex PDF catalog tables into structured product databases.
- **Parallel Tunisian Scraper:** High-speed parallel scraping across 8+ major Tunisian retailers (MyTek, Tunisianet, Wiki, etc.) with advanced price extraction and regex-based alias matching.
- **Global Fallback Engine:** Advanced Google-backed fallback that finds products on *any* Tunisian website if primary retailers fail.
- **Professional Image Enhancer:** Integrates advanced computer vision via OpenCV (Non-Local Means Denoising, CLAHE Contrast Enhancement, and Adaptive Unsharp Masking) for crisp, professional upscaling without destroying natural edges.
- **Automated Structural Synthesis:** Automatically generates clean, highly readable, category-specific product descriptions bypassing the need for expensive API tokens, guaranteeing 100% data availability.
- **Cyberpunk Neo-Brutalist UI:** A striking, highly-polished user interface featuring glassmorphism overlays, neumorphic hardware depth, and intense neon reactive states for maximum workflow immersion.
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

3. **Configure Secrets (Optional):**
   Create a `.env` file in the root directory for external cloud modules.
   ```env
   OPENROUTER_API_KEY=your_key_here
   INFSH_API_KEY=your_key_here
   ```

## 🚀 Usage

Run the application using Streamlit:
```bash
streamlit run app.py
```

1. **Upload:** Drop your product catalog PDF.
2. **Configure:** Select categories and trigger the extraction pipeline.
3. **Process:** Watch the agent scrape 7 parallel sites and apply OpenCV contrast enhancements in real-time.
4. **Results:** Review the extracted pricing, descriptions, and upscaled thumbnails before exporting.

## 📁 Project Structure

- `app.py`: Main Streamlit entry point featuring a custom Cyberpunk design system.
- `src/`:
  - `scraper.py`: Agentic multi-site scraping logic with fallback discovery and fuzzy text matching.
  - `desc_writer.py`: Fast, localized structural format generator.
  - `image_enhancer.py`: Centralized upscaling pipeline combining PIL and OpenCV logic.
  - `advanced_enhancer.py`: Professional OpenCV module handling contrast, saturation, and edge detection.
  - `pdf_processor.py`: PDF table extraction engine.

---
*Built by the Advanced Agentic Coding Team.*
