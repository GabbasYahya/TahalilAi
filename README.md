# TahalilAI

> **Privacy-first medical lab report analysis powered by local AI.**

Upload a medical lab report image and receive a clear, patient-friendly
explanation — all processed locally on your machine. No sensitive data
ever leaves your network.

![Status](https://img.shields.io/badge/Status-Beta-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Python](https://img.shields.io/badge/Python-3.11%2B-blue)
![Privacy](https://img.shields.io/badge/Privacy-Local--First-red)

---

## Features

| Feature | Description |
|---------|-------------|
| **Privacy First** | OCR + AI analysis run locally — no cloud uploads |
| **OCR** | Tesseract-based extraction (English, French, Arabic) |
| **Local LLM** | Ministral-3B via llama.cpp for CPU-friendly inference |
| **On-demand TTS** | Listen to your results (Qwen3-TTS / gTTS fallback) |
| **Translation** | Arabic translation via Gemini API |
| **PDF Reports** | Downloadable branded PDF of the analysis |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 16, React 19, Tailwind CSS 4, TypeScript |
| Backend | FastAPI, Pydantic v2, uvicorn |
| AI | llama.cpp (Ministral 3B GGUF), Gemini API |
| OCR | Tesseract via pytesseract |
| TTS | Qwen3-TTS (optional), gTTS |

---

## Repository Structure

```
tahalilai/
├── backend/
│   ├── src/tahalilai/        # Python package (services, utils, app)
│   ├── tests/                # pytest suite (unit / integration / e2e)
│   ├── scripts/              # Benchmarks & utilities
│   ├── bin/                  # llama.cpp binaries (gitignored)
│   ├── Models/               # GGUF model files (gitignored)
│   └── pyproject.toml        # Project config, deps, tool settings
├── frontend/                 # Next.js application
├── .github/workflows/        # CI pipeline
├── .env.example              # Environment template
├── .pre-commit-config.yaml   # Pre-commit hooks
└── README.md
```

---

## Prerequisites

- **Python 3.11+**
- **Node.js 20+**
- **Tesseract OCR** — [Windows installer](https://github.com/UB-Mannheim/tesseract/wiki) or `apt install tesseract-ocr tesseract-ocr-fra tesseract-ocr-ara`
- **llama.cpp** — Download `llama-cli` from [releases](https://github.com/ggerganov/llama.cpp/releases) → `backend/bin/`
- **GGUF model** — Download a quantised model → `backend/Models/`

---

## Quick Start

### 1. Environment

```bash
cp .env.example .env
# Edit .env — set GEMINI_API_KEY, TESSERACT_CMD, etc.
```

### 2. Backend

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/Mac: source .venv/bin/activate

pip install -e ".[dev]"       # install package + dev tools
python -m tahalilai          # start server on :8000
```

### 3. Frontend

```bash
cd frontend
npm install
npm run dev                    # start dev server on :3000
```

Open [http://localhost:3000](http://localhost:3000) and upload a report.

---

## Development

### Running Tests

```bash
cd backend
pytest --cov=tahalilai --cov-report=term-missing
```

### Linting & Formatting

```bash
ruff check src tests           # lint
ruff format src tests          # auto-format
mypy src                       # type check
```

### Pre-commit Hooks

```bash
pip install pre-commit
pre-commit install
pre-commit run --all-files
```
 
### Benchmark

```bash
# Requires a running server
python scripts/benchmark.py
```

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | Health check |
| `POST` | `/analyze` | Upload file, start OCR → AI → PDF pipeline |
| `GET` | `/status/{job_id}` | Poll analysis progress |
| `POST` | `/generate-audio` | On-demand TTS for a completed job |
| `GET` | `/audio-status/{job_id}` | Poll TTS progress |
| `POST` | `/translate` | Translate analysis to Arabic (Gemini) |

Full OpenAPI docs available at `http://localhost:8000/docs`.

---

## Configuration

All settings are configurable via environment variables or `.env`:

| Variable | Default | Description |
|----------|---------|-------------|
| `GEMINI_API_KEY` | — | Google Gemini API key |
| `GEMINI_MODEL` | `gemini-2.5-flash` | Gemini model name |
| `TESSERACT_CMD` | *(system PATH)* | Path to Tesseract binary |
| `OCR_LANGUAGES` | `fra+eng+ara` | Tesseract language packs |
| `PORT` | `8000` | Server port |
| `MODEL_TIMEOUT` | `600` | LLM inference timeout (seconds) |

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feat/my-feature`)
3. Ensure `ruff check`, `ruff format --check`, and `pytest` all pass
4. Commit with clear messages (`git commit -m "feat: add X"`)
5. Open a Pull Request

---

## License

[MIT](LICENSE) © GabbasYahya
