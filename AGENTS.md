# AGENTS.md - Project Guidelines and Standards

This project is a high-performance Lagent Agent designed for automated PDF catalog processing and cloud-based content synthesis.

---

## 1. Build, Lint, and Test Commands

### Environment Setup
- **Python Version:** 3.10+
- **Install Dependencies:** `pip install -r requirements.txt`
- **Secrets:** Store your `OPENROUTER_API_KEY` in a `.env` file.

### Commands
- **Run App:** `streamlit run app.py`
- **Linting:** `ruff check .`
- **Type Checking:** `mypy .`

---

## 2. Code Style and Conventions

### AI Architecture
- **Engine:** OpenRouter Cloud API (Free Models with Reasoning).
- **Frontend:** Streamlit for a fast, modern futuristic UI.
- **Data Gathering:** Parallel web scraping from Tunisian retailers.

### Naming Conventions
- **Files:** `snake_case` (e.g., `pdf_processor.py`).
- **Functions:** `snake_case` (e.g., `fetch_product_node`).
- **Constants:** `UPPER_SNAKE_CASE` (e.g., `API_URL = "..."`).

### Error Handling
- Use explicit `try...except` blocks for all network and API calls.
- Provide real-time logging to the console using `[LOG]` or `[NEURAL_LOG]` prefixes.
- Log full traceback only for development.

---

## 3. Deployment and Secrets

- **NEVER** commit your `.env` file or API tokens.
- **Local Proxy:** The app runs locally on `localhost:8501`.

---
*Updated: 2026-03-12*
