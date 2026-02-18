# TahalilAI — Architecture & Developer Documentation

> **Version**: 1.0.0  
> **Author**: Gabbas Yahya  
> **Last Updated**: February 2026

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Repository Structure](#2-repository-structure)
3. [Backend Architecture](#3-backend-architecture)
   - [Package Layout](#31-package-layout)
   - [Configuration System](#32-configuration-system)
   - [Service Layer](#33-service-layer)
   - [API Endpoints](#34-api-endpoints)
   - [Security Utilities](#35-security-utilities)
4. [Frontend Architecture](#4-frontend-architecture)
   - [Pages](#41-pages)
   - [Components](#42-components)
   - [Internationalisation](#43-internationalisation)
5. [Test Suite](#5-test-suite)
   - [Test Structure](#51-test-structure)
   - [Fixtures](#52-fixtures)
   - [Unit Tests](#53-unit-tests)
   - [Integration Tests](#54-integration-tests)
   - [Running Tests](#55-running-tests)
6. [CI/CD Pipeline](#6-cicd-pipeline)
7. [Developer Tooling](#7-developer-tooling)
8. [Deployment Notes](#8-deployment-notes)

---

## 1. Project Overview

**TahalilAI** is a privacy-first medical laboratory report analyser. Users upload
an image or PDF of their lab results and receive a patient-friendly English
explanation, with optional Arabic translation and text-to-speech audio.

**Key design principles:**
- **Local-first privacy** — OCR and AI inference run entirely on the user's machine.
- **Modular services** — each concern (OCR, analysis, translation, TTS, PDF) is an independent module.
- **Modern Python packaging** — `pyproject.toml`, `src/` layout, strict type checking.
- **Async by default** — analysis runs in background tasks; the UI polls for progress.

**Technology stack:**

| Layer       | Technology                                              |
|-------------|---------------------------------------------------------|
| Frontend    | Next.js 16, React 19, Tailwind CSS 4, TypeScript       |
| Backend     | FastAPI, Pydantic v2, uvicorn, Python 3.11+             |
| AI/LLM      | llama.cpp (Ministral 3B GGUF), CPU inference            |
| Translation | Google Gemini API via `google-genai` SDK                |
| OCR         | Tesseract via `pytesseract`                             |
| TTS         | Qwen3-TTS (optional GPU) + gTTS fallback                |
| PDF         | fpdf2                                                   |

---

## 2. Repository Structure

```
tahalilai/
├── .github/workflows/ci.yml     # GitHub Actions CI pipeline
├── .pre-commit-config.yaml       # Pre-commit hooks (ruff, mypy)
├── .env.example                  # Environment variable template
├── .gitignore                    # Comprehensive ignore rules
├── LICENSE                       # MIT licence
├── README.md                     # User-facing project overview
│
├── backend/
│   ├── pyproject.toml            # Build config, deps, tool settings
│   ├── src/tahalilai/            # 📦 Python package
│   │   ├── __init__.py           # Package version
│   │   ├── __main__.py           # `python -m tahalilai` entry point
│   │   ├── app.py                # FastAPI application (factory pattern)
│   │   ├── config.py             # Centralised pydantic-settings config
│   │   ├── schemas.py            # Pydantic request/response models
│   │   ├── py.typed              # PEP 561 type marker
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── ocr.py            # Tesseract OCR extraction
│   │   │   ├── analyzer.py       # Local LLM analysis (llama-cli)
│   │   │   ├── translator.py     # Gemini API translation
│   │   │   ├── tts.py            # Text-to-speech (Qwen3/gTTS)
│   │   │   └── report.py         # PDF report generation
│   │   └── utils/
│   │       ├── __init__.py
│   │       └── security.py       # File validation & filename sanitisation
│   ├── tests/                    # pytest test suite
│   │   ├── conftest.py           # Shared fixtures
│   │   ├── unit/                 # Unit tests per service module
│   │   ├── integration/          # API endpoint tests
│   │   └── e2e/                  # End-to-end tests (reserved)
│   ├── scripts/
│   │   └── benchmark.py          # Pipeline performance benchmark
│   ├── bin/                      # llama-cli binary (gitignored)
│   ├── Models/                   # GGUF model files (gitignored)
│   ├── assets/                   # Static assets (TTS ref audio)
│   └── uploads/                  # Runtime upload directory (gitignored)
│
├── frontend/
│   ├── package.json
│   ├── next.config.ts
│   ├── tsconfig.json
│   ├── eslint.config.mjs
│   ├── postcss.config.mjs
│   └── src/
│       ├── app/
│       │   ├── layout.tsx        # Root layout (header, footer, providers)
│       │   ├── page.tsx          # Landing page
│       │   ├── upload/page.tsx   # File upload & processing page
│       │   ├── results/page.tsx  # Results display (EN/AR, audio, PDF)
│       │   └── globals.css       # Tailwind + custom CSS
│       ├── components/
│       │   ├── Header.tsx        # Sticky navigation bar
│       │   ├── Footer.tsx        # Disclaimer & privacy note
│       │   ├── LanguageSwitcher.tsx  # EN/FR/AR language toggle
│       │   └── ProcessingLoader.tsx  # Step-based loading indicator
│       ├── context/
│       │   └── LanguageContext.tsx   # i18n context + translations
│       └── lib/                  # Utility functions (reserved)
│
├── docs/                         # This documentation
│   ├── ARCHITECTURE.md           # ← You are here
│   └── REFACTORING_REPORT.tex    # LaTeX change report
│
└── images/                       # Screenshots, diagrams
```

---

## 3. Backend Architecture

### 3.1 Package Layout

The backend uses Python's modern **src layout** pattern:

```
backend/
└── src/
    └── tahalilai/       ← importable as `import tahalilai`
```

This is configured in `pyproject.toml` under `[tool.hatch.build.targets.wheel]` and
installed via `pip install -e ".[dev]"` for development.

**Entry points:**
- `python -m tahalilai` — runs the `__main__.py` CLI (auto-detects port conflicts)
- `uvicorn tahalilai.app:app` — standard ASGI server start
- `tahalilai` command — installed via `[project.scripts]` in pyproject.toml

### 3.2 Configuration System

**File:** `src/tahalilai/config.py`

All settings are managed through a single `Settings` class based on `pydantic-settings.BaseSettings`:

| Setting            | Env Variable       | Default                                          | Description                       |
|--------------------|--------------------|-------------------------------------------------|-----------------------------------|
| `backend_dir`      | `BACKEND_DIR`      | Auto-detected from package path                 | Root of the backend directory     |
| `llama_cli`        | `LLAMA_CLI`        | `bin/llama-cli.exe`                             | Path to llama.cpp binary          |
| `llm_model`        | `LLM_MODEL`        | `Models/Ministral-3-3B-Instruct-...Q5_K_M.gguf` | GGUF model file                   |
| `model_timeout`    | `MODEL_TIMEOUT`    | `600`                                           | LLM inference timeout (seconds)   |
| `gemini_api_key`   | `GEMINI_API_KEY`   | `""`                                            | Google Gemini API key             |
| `gemini_model`     | `GEMINI_MODEL`     | `gemini-2.5-flash`                              | Gemini model name                 |
| `host`             | `HOST`             | `0.0.0.0`                                       | Server bind address               |
| `port`             | `PORT`             | `8000`                                          | Server port                       |
| `cors_origins`     | `CORS_ORIGINS`     | `["*"]`                                         | Allowed CORS origins              |
| `tesseract_cmd`    | `TESSERACT_CMD`    | `""` (system PATH)                              | Tesseract binary path             |
| `ocr_languages`    | `OCR_LANGUAGES`    | `fra+eng+ara`                                   | Tesseract language packs          |

**Singleton pattern:** `get_settings()` returns a cached instance via `@lru_cache`.

**Computed properties:** `uploads_dir`, `llama_cli_path`, `model_path`, `assets_dir` —
derived from `backend_dir` automatically.

### 3.3 Service Layer

Each service module follows the same pattern:
- Public functions with full type annotations and Google-style docstrings
- Internal helpers prefixed with `_`
- Dependencies injected via `get_settings()` (no global state)
- Graceful error handling returning `"Error: ..."` strings instead of raising

#### `services/ocr.py` — OCR Service

**Function:** `perform_ocr(image_path, lang) → str`

- Opens the image with Pillow, passes to Tesseract via `pytesseract`
- Supports configurable language packs (`fra+eng+ara`)
- Returns extracted text or `"Error: ..."` on failure

#### `services/analyzer.py` — LLM Analysis

**Function:** `analyze_text(ocr_text, age, gender) → str`

- Builds a structured medical prompt with system instruction
- Invokes `llama-cli` as a subprocess with timeout protection
- Cleans LLM output via `_clean_llm_output()` (strips banners, speed stats, prompt echoes)
- Returns patient-friendly English explanation

**Internal:** `_clean_llm_output(raw)` — removes llama.cpp noise lines (build info,
token stats, `[INST]` markers, `Exiting...`).

#### `services/translator.py` — Gemini Translation

**Function:** `translate_medical_report(text) → str`

- Uses the `google.genai` SDK (modern, not deprecated `google.generativeai`)
- Sends English analysis to Gemini with medical translation system prompt
- Preserves formatting, numerical values, and medical terminology
- Feature-flagged: `_GEMINI_AVAILABLE` guards against missing SDK

#### `services/tts.py` — Text-to-Speech

**Function:** `generate_audio(text, output_path, lang) → bool`

- **Primary engine:** Qwen3-TTS (GPU-optional, lazily loaded on first call)
- **Fallback:** gTTS (always available, no GPU needed)
- Strips markdown before speaking via `_strip_markdown()`
- Lazy model loading means server startup is instant
- Returns `True`/`False` instead of raising

**Internal helpers:**
- `_get_qwen_model()` — singleton lazy-loader
- `_try_qwen()` — attempts neural TTS, returns `False` on failure
- `_fallback_gtts()` — lightweight Google TTS

#### `services/report.py` — PDF Generation

**Function:** `generate_pdf_report(text_content, output_path) → Path`

- Uses `fpdf2` with a custom `_PDFReport` subclass (branded footer with disclaimer)
- Handles pseudo-markdown: `---` headers, `**bold**`, bullet lists
- Loads Arial font for Unicode/Arabic support on Windows
- Graceful fallback to Helvetica + Latin-1 encoding

### 3.4 API Endpoints

All endpoints are defined inside `create_app()` (factory pattern):

| Method | Path                      | Description                           | Response         |
|--------|---------------------------|---------------------------------------|------------------|
| `GET`  | `/`                       | Health check                          | `{"status": "online"}` |
| `POST` | `/analyze`                | Upload file → OCR → AI → PDF         | Job ID (async) or full result (sync) |
| `GET`  | `/status/{job_id}`        | Poll analysis progress                | Job status + result when complete |
| `POST` | `/generate-audio`         | On-demand TTS for completed job       | Status message   |
| `GET`  | `/audio-status/{job_id}`  | Poll TTS generation progress          | Audio URL when ready |
| `POST` | `/translate`              | Translate analysis to Arabic          | Arabic text      |

**Analysis modes:**
- **Async (default):** Returns immediately with `job_id`, client polls `/status/{job_id}`
- **Sync:** Set `wait_for_result=true` in the form data; blocks until completion

**Pipeline (`_run_pipeline`):** OCR → AI analysis → PDF generation → update job store.

### 3.5 Security Utilities

**File:** `utils/security.py`

| Function             | Purpose                                           |
|----------------------|---------------------------------------------------|
| `validate_file(path)` | Checks file magic bytes against allow-list (PDF, JPEG, PNG). Uses `python-magic` with header-byte fallback. Raises `ValueError` on rejection. |
| `sanitize_filename(name)` | Strips path components, restricts to `[a-zA-Z0-9_.-]` |

---

## 4. Frontend Architecture

### 4.1 Pages

| Page              | File                      | Description                                    |
|-------------------|---------------------------|------------------------------------------------|
| Landing (`/`)     | `app/page.tsx`            | Hero section with CTA, 3-step process diagram  |
| Upload (`/upload`)| `app/upload/page.tsx`     | Drag-and-drop file upload, optional age/gender, polling loader |
| Results (`/results`)| `app/results/page.tsx`  | Markdown-rendered analysis, EN/AR tabs, audio player, PDF download |

**Data flow:**
1. User uploads file on `/upload`
2. Frontend `POST`s to `/analyze`, receives `job_id`
3. Polls `/status/{job_id}` every 2.5s
4. On completion, stores result in `localStorage`, navigates to `/results`
5. Results page reads from `localStorage`, offers translate/audio/PDF actions

### 4.2 Components

| Component            | File                        | Description                          |
|----------------------|-----------------------------|--------------------------------------|
| `Header`             | `components/Header.tsx`     | Sticky nav bar with logo + language switcher |
| `Footer`             | `components/Footer.tsx`     | Disclaimer, privacy note, copyright  |
| `LanguageSwitcher`   | `components/LanguageSwitcher.tsx` | EN/FR/AR pill-style toggle      |
| `ProcessingLoader`   | `components/ProcessingLoader.tsx` | 3-step animated progress (OCR → AI → Report) |

### 4.3 Internationalisation

**File:** `context/LanguageContext.tsx`

- Supports three languages: English, French, Arabic
- All UI strings stored in a central `translations` dictionary
- `useLanguage()` hook provides `t("key")` for string lookup
- Language state managed via React Context + `useState`

---

## 5. Test Suite

### 5.1 Test Structure

```
tests/
├── conftest.py              # Shared fixtures
├── unit/
│   ├── test_security.py     # 9 tests — sanitize_filename, validate_file
│   ├── test_ocr.py          # 3 tests — OCR with mocked pytesseract
│   ├── test_analyzer.py     # 8 tests — LLM output cleaning, subprocess mocking
│   ├── test_translator.py   # 4 tests — Gemini SDK mocking
│   ├── test_report.py       # 5 tests — PDF generation, Unicode, markdown
│   └── test_tts.py          # 6 tests — markdown stripping, gTTS mocking
├── integration/
│   └── test_api.py          # 8 tests — all API endpoints via TestClient
└── e2e/                     # Reserved for end-to-end tests
```

**Total: 43 tests** | All passing | Execution time: ~1.8s

### 5.2 Fixtures

Defined in `tests/conftest.py`:

| Fixture                | Scope    | Description                                   |
|------------------------|----------|-----------------------------------------------|
| `client`               | function | FastAPI `TestClient` with fresh `create_app()` |
| `tmp_image`            | function | Minimal valid 1×1 PNG file (67 bytes)         |
| `sample_analysis_text` | function | Representative AI output text for testing     |

### 5.3 Unit Tests

Each service module has a dedicated test file with mocked external dependencies:

**`test_security.py`** (9 tests)
- `TestSanitizeFilename`: basic names, path stripping, unsafe char replacement, safe char preservation
- `TestValidateFile`: valid PNG/JPEG/PDF, rejects text files, rejects empty files

**`test_ocr.py`** (3 tests)
- File not found → error string
- Successful OCR → mocked pytesseract returns expected text
- OCR exception → error string

**`test_analyzer.py`** (8 tests)
- `TestCleanLlmOutput`: strips speed stats, exiting markers, `[INST]` tags, build lines; preserves explanation headers
- `TestAnalyzeText`: successful analysis (mocked subprocess), timeout handling (mocked `TimeoutExpired`), empty output detection

**`test_translator.py`** (4 tests)
- Missing API key → error
- SDK not installed → error
- Successful translation → mocked Gemini client returns Arabic
- API exception → error string

**`test_report.py`** (5 tests)
- Creates valid PDF file with `%PDF-` header
- Handles empty content gracefully
- Processes markdown formatting (bold, headers, bullets)
- Handles Unicode/Arabic without crashing

**`test_tts.py`** (6 tests)
- `TestStripMarkdown`: bold removal, header removal, link stripping, plain text preservation
- `TestGenerateAudio`: gTTS fallback success (Qwen disabled), gTTS failure returns `False`

### 5.4 Integration Tests

**`test_api.py`** — Tests API endpoints with mocked service layer:

| Test Class            | Tests | What's Tested                                    |
|-----------------------|-------|--------------------------------------------------|
| `TestHealthCheck`     | 1     | `GET /` returns `{"status": "online"}`           |
| `TestStatusEndpoint`  | 1     | Non-existent job returns `not_found`             |
| `TestAnalyzeEndpoint` | 3     | Sync mode, async mode with polling, invalid file rejection |
| `TestTranslateEndpoint`| 1    | Missing job returns 404                          |
| `TestAudioEndpoints`  | 2     | Audio status not found, generate-audio with missing job |

### 5.5 Running Tests

```bash
cd backend

# Run all tests
pytest

# With coverage report
pytest --cov=tahalilai --cov-report=term-missing

# Run only unit tests
pytest tests/unit/

# Run only integration tests
pytest tests/integration/

# Run a specific test file
pytest tests/unit/test_security.py -v

# Run with verbose + short traceback (configured default)
pytest -v --tb=short
```

---

## 6. CI/CD Pipeline

**File:** `.github/workflows/ci.yml`

Triggered on push/PR to `main`. Two parallel jobs:

### Backend Job
1. Checkout + setup Python 3.11
2. `pip install -e ".[dev]"` — install package with dev tools
3. `ruff check src tests` — lint (pycodestyle, pyflakes, isort, bugbear, simplify)
4. `ruff format --check src tests` — verify formatting
5. `mypy src` — strict type checking
6. `pytest --cov=tahalilai --cov-report=term-missing` — run tests with coverage

### Frontend Job
1. Checkout + setup Node.js 20
2. `npm ci` — deterministic install
3. `npm run lint` — ESLint
4. `npm run build` — production build verification

---

## 7. Developer Tooling

### Ruff (Linter + Formatter)

Configured in `pyproject.toml` under `[tool.ruff]`:

- **Line length:** 100
- **Target:** Python 3.11
- **Rules enabled:** E, W, F (core), I (isort), B (bugbear), UP (pyupgrade), RUF, SIM (simplify)
- **Ignored:** E501 (line too long — handled by formatter)

```bash
ruff check src tests       # Lint
ruff format src tests      # Auto-format
```

### Mypy (Type Checker)

Configured under `[tool.mypy]`:

- **Strict mode** enabled
- `disallow_untyped_defs = true`
- `warn_return_any = true`
- `ignore_missing_imports = true` (for optional deps like torch, qwen_tts)

```bash
mypy -p tahalilai          # Type check the full package
```

### Pre-commit Hooks

Configured in `.pre-commit-config.yaml`:

1. **Trailing whitespace** — auto-trim
2. **Ruff** — lint + format on commit
3. **Mypy** — type check on commit

```bash
pre-commit install          # Install hooks
pre-commit run --all-files  # Run on all files
```

---

## 8. Deployment Notes

### Environment Variables

Copy `.env.example` to `.env` and configure:

```env
GEMINI_API_KEY=your-key-here
TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe
PORT=8000
```

### Prerequisites

- Python 3.11+ with `pip install -e ".[dev]"`
- Node.js 20+ with `npm install` (frontend)
- Tesseract OCR installed and on PATH (or configured via `TESSERACT_CMD`)
- llama-cli binary in `backend/bin/`
- GGUF model in `backend/Models/`
- (Optional) `GEMINI_API_KEY` for Arabic translation
- (Optional) CUDA GPU for Qwen3-TTS

### Starting the Application

```bash
# Backend
cd backend
python -m tahalilai          # or: uvicorn tahalilai.app:app --reload

# Frontend
cd frontend
npm run dev
```

Open http://localhost:3000 — the frontend proxies API calls to http://127.0.0.1:8000.
