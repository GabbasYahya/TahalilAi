# TahalilAI — ClickUp Task List

---

## EPIC 1 — Project Setup & Infrastructure

### Task 1.1 — Repository Initialisation
- [ ] Create GitHub repository
- [ ] Add `.gitignore` (Python, Node, env files, model files)
- [ ] Add `LICENSE` (MIT)
- [ ] Add base `README.md`
- [ ] Create top-level folder structure (`backend/`, `frontend/`, `docs/`)

### Task 1.2 — Backend Packaging
- [ ] Set up `src/tahalilai/` Python package with `__init__.py`
- [ ] Create `pyproject.toml` using Hatchling build backend
- [ ] Define all production dependencies with minimum-version bounds
- [ ] Define optional dependency groups (`dev`, `tts-gpu`)
- [ ] Add `py.typed` marker for PEP 561 compliance
- [ ] Add `__main__.py` CLI entry point
- [ ] Test editable install with `pip install -e ".[dev]"`

### Task 1.3 — Environment Configuration
- [ ] Create `.env.example` with all required variables documented
- [ ] Create `config.py` using `pydantic-settings`
- [ ] Centralise all settings (LLM path, Gemini key, Tesseract path, host/port)
- [ ] Use `@lru_cache` singleton for settings access
- [ ] Verify `.env` is in `.gitignore`

### Task 1.4 — Developer Tooling
- [ ] Configure Ruff (lint + format) in `pyproject.toml`
- [ ] Configure Mypy (strict mode) in `pyproject.toml`
- [ ] Create `.pre-commit-config.yaml` with Ruff and Mypy hooks
- [ ] Run `pre-commit install` and verify hooks fire on commit

---

## EPIC 2 — Backend Services

### Task 2.1 — OCR Service (`services/ocr.py`)
- [ ] Accept image file path and language string as parameters
- [ ] Call `pytesseract.image_to_string()` with configurable `tesseract_cmd`
- [ ] Support multi-language: `fra+eng+ara`
- [ ] Return extracted text string; return error message string on failure
- [ ] Add full type annotations and docstring

### Task 2.2 — LLM Analyser Service (`services/analyzer.py`)
- [ ] Accept OCR text, optional patient age and gender
- [ ] Invoke local `llama-cli.exe` subprocess with Ministral-3B GGUF model
- [ ] Apply structured prompt for French medical report interpretation
- [ ] Clean raw LLM output (remove inference stats, `[INST]` markers, build lines)
- [ ] Handle subprocess timeout and empty output gracefully
- [ ] Add full type annotations and docstring

### Task 2.3 — Translation Service (`services/translator.py`)
- [ ] Accept analysed text string; translate to Arabic using Gemini API
- [ ] Use `google-genai` SDK exclusively (not deprecated `google-generativeai`)
- [ ] Detect missing API key and return informative error string
- [ ] Detect missing `google-genai` SDK and return informative error string
- [ ] Add full type annotations and docstring

### Task 2.4 — TTS Service (`services/tts.py`)
- [ ] Accept text, output file path, and language code
- [ ] Strip markdown formatting before synthesis
- [ ] Attempt Qwen3-TTS (GPU) as primary engine; lazy-load on first request
- [ ] Fall back to gTTS automatically if Qwen is unavailable
- [ ] Return boolean success flag
- [ ] Add full type annotations and docstring

### Task 2.5 — PDF Report Service (`services/report.py`)
- [ ] Accept analysed text and output file path
- [ ] Generate styled PDF using `fpdf2` with Arabic/French font support
- [ ] Add header, footer with page number, and formatted body
- [ ] Use modern `fpdf2` API (`XPos`/`YPos` enums)
- [ ] Handle Unicode/Arabic text gracefully
- [ ] Return `Path` to generated file
- [ ] Add full type annotations and docstring

### Task 2.6 — Security Utilities (`utils/security.py`)
- [ ] Validate uploaded file by magic-byte inspection (PNG, JPEG, PDF)
- [ ] Reject text files, empty files, and unsupported types
- [ ] Sanitise uploaded filenames (strip paths, replace unsafe characters)
- [ ] Add full type annotations and docstring

---

## EPIC 3 — FastAPI Application

### Task 3.1 — Application Factory
- [ ] Create `create_app()` factory function returning `FastAPI` instance
- [ ] Configure CORS middleware using settings
- [ ] Configure static file serving for generated audio
- [ ] Use `@asynccontextmanager` lifespan (not deprecated `on_event`)
- [ ] Register all route handlers

### Task 3.2 — Schemas
- [ ] Define `AudioRequest` Pydantic model (job_id, language)
- [ ] Define `TranslationRequest` Pydantic model (job_id)
- [ ] Ensure all fields are validated and documented

### Task 3.3 — Endpoints
- [ ] `GET /` — health check, returns server status and version
- [ ] `POST /analyze` — accept image upload, age, gender, mode (sync/async)
- [ ] `GET /status/{job_id}` — return job status and result
- [ ] `POST /translate` — translate analysis result via Gemini
- [ ] `POST /generate-audio` — generate TTS audio for a completed job
- [ ] `GET /audio-status/{job_id}` — return audio generation status

### Task 3.4 — Pipeline Orchestration
- [ ] Implement `_run_pipeline()`: OCR → LLM Analysis → PDF generation
- [ ] Log timing for each stage
- [ ] Store results in in-memory job store with unique UUIDs
- [ ] Support synchronous and asynchronous (background task) modes

---

## EPIC 4 — Frontend (Next.js)

### Task 4.1 — Project Bootstrap
- [ ] Initialise Next.js 16 with TypeScript and Tailwind CSS v4
- [ ] Configure `next.config.ts` (API proxy to backend)
- [ ] Set up ESLint with `eslint-config-next`
- [ ] Verify `npm run build` passes cleanly

### Task 4.2 — Internationalisation (i18n)
- [ ] Create `LanguageContext` supporting EN / FR / AR
- [ ] Implement `useLanguage()` hook
- [ ] Support RTL layout for Arabic
- [ ] Add all UI string translations per language

### Task 4.3 — Shared Components
- [ ] `Header` — logo, navigation links, language switcher
- [ ] `Footer` — copyright and links
- [ ] `LanguageSwitcher` — flag/code buttons, updates context
- [ ] `ProcessingLoader` — animated spinner with status message

### Task 4.4 — Landing Page (`/`)
- [ ] Hero section with project description
- [ ] Feature cards (OCR, AI Analysis, PDF, TTS, Translation)
- [ ] Call-to-action button linking to upload page
- [ ] Fully responsive, supports RTL

### Task 4.5 — Upload Page (`/upload`)
- [ ] Drag-and-drop / click file input for image upload
- [ ] Patient age and gender form fields (optional)
- [ ] Language selection for TTS
- [ ] Submit to `POST /analyze` with loading state
- [ ] Error handling and user feedback

### Task 4.6 — Results Page (`/results`)
- [ ] Display analysis text rendered as Markdown
- [ ] PDF download button
- [ ] Translate to Arabic button (calls `POST /translate`)
- [ ] Play Audio button (calls `POST /generate-audio`, polls status)
- [ ] Handle loading and error states for each action

---

## EPIC 5 — Testing

### Task 5.1 — Test Infrastructure
- [ ] Configure pytest in `pyproject.toml` (`testpaths`, `addopts`)
- [ ] Create `conftest.py` with `client`, `tmp_image`, and `sample_analysis_text` fixtures

### Task 5.2 — Unit Tests: Security (9 tests)
- [ ] Test filename sanitisation with path separators
- [ ] Test filename sanitisation with unsafe characters
- [ ] Test PNG file validation (accepted)
- [ ] Test JPEG file validation (accepted)
- [ ] Test PDF file validation (accepted)
- [ ] Test text file validation (rejected)
- [ ] Test empty file validation (rejected)
- [ ] Test file not found handling
- [ ] Test binary blob rejection

### Task 5.3 — Unit Tests: OCR (3 tests)
- [ ] Test file not found returns error string
- [ ] Test successful OCR with mocked pytesseract
- [ ] Test pytesseract exception handling

### Task 5.4 — Unit Tests: Analyser (8 tests)
- [ ] Test cleaning of LLM speed statistics lines
- [ ] Test cleaning of `[INST]` markers
- [ ] Test cleaning of build/platform lines
- [ ] Test successful subprocess invocation (mocked)
- [ ] Test subprocess timeout returns error string
- [ ] Test empty LLM output returns error string
- [ ] Test subprocess `OSError` handling
- [ ] Test full output cleaning pipeline

### Task 5.5 — Unit Tests: Translator (4 tests)
- [ ] Test missing API key returns error string
- [ ] Test missing `google-genai` SDK returns error string
- [ ] Test successful translation with mocked Gemini client
- [ ] Test Gemini API exception returns error string

### Task 5.6 — Unit Tests: Report (5 tests)
- [ ] Test PDF file is created at specified path
- [ ] Test PDF header contains project name
- [ ] Test empty content produces valid PDF
- [ ] Test markdown formatting characters are handled
- [ ] Test Arabic/Unicode text does not crash PDF generation

### Task 5.7 — Unit Tests: TTS (6 tests)
- [ ] Test markdown bold stripping
- [ ] Test markdown header stripping
- [ ] Test markdown link stripping
- [ ] Test gTTS success (mocked)
- [ ] Test gTTS exception returns False
- [ ] Test Qwen unavailable falls back to gTTS

### Task 5.8 — Integration Tests: API (8 tests)
- [ ] `GET /` returns `{"status": "online"}`
- [ ] `GET /status/{unknown_id}` returns `not_found`
- [ ] `POST /analyze` sync mode returns analysis result (mocked pipeline)
- [ ] `POST /analyze` async mode returns job_id immediately
- [ ] `POST /analyze` with non-image returns 400
- [ ] `POST /translate` with unknown job_id returns 404
- [ ] `POST /generate-audio` with unknown job_id returns 404
- [ ] `GET /audio-status/{unknown_id}` returns `not_found`

---

## EPIC 6 — CI/CD & Deployment

### Task 6.1 — GitHub Actions Workflow
- [ ] Create `.github/workflows/ci.yml`
- [ ] Backend job: checkout → Python 3.11 → install deps → ruff lint → ruff format check → mypy → pytest
- [ ] Frontend job: checkout → Node 20 → `npm ci` → ESLint → `npm run build`
- [ ] Trigger on push and pull_request to `main`

### Task 6.2 — Pre-commit Hooks
- [ ] Create `.pre-commit-config.yaml`
- [ ] Add Ruff lint hook
- [ ] Add Ruff format hook
- [ ] Add Mypy hook
- [ ] Document setup: `pre-commit install`

### Task 6.3 — Deployment Preparation
- [ ] Document Tesseract installation per OS (Windows / Linux / macOS)
- [ ] Document llama-cli setup and GGUF model placement
- [ ] Add `uploads/` and `Models/` to `.gitignore` with `.gitkeep`
- [ ] Test production build (`npm run build` + `uvicorn tahalilai.app:app`)

---

## EPIC 7 — Documentation

### Task 7.1 — README.md
- [ ] Project overview and feature list
- [ ] Prerequisites table
- [ ] Step-by-step installation guide (backend + frontend)
- [ ] Configuration table (all `.env` variables)
- [ ] API endpoint reference
- [ ] Contributing guidelines and license section

### Task 7.2 — Architecture Documentation (`docs/ARCHITECTURE.md`)
- [ ] Repository structure diagram
- [ ] Backend package layout and configuration system
- [ ] Service layer: each module's public API documented
- [ ] Endpoint reference table
- [ ] Test suite structure and coverage description
- [ ] CI/CD pipeline and developer tooling guide

### Task 7.3 — Refactoring / Final Report (`docs/REFACTORING_REPORT.tex`)
- [ ] Executive summary with validation result table
- [ ] Problem statement (issues before refactoring)
- [ ] Detailed changes section (package structure, config, deps, services, typing)
- [ ] Test suite documentation
- [ ] Dead code removal log
- [ ] CI/CD pipeline description
- [ ] Lint / format / mypy fix log
- [ ] Summary metrics table (before vs after)
- [ ] Compile to PDF with `pdflatex`

---

> **Total: 7 Epics — 28 Tasks — ~130 Subtasks**
