# CLAUDE.md — TahalilAI Project Guidelines

## Project Overview
TahalilAI is a privacy-first medical lab report analysis platform. It processes sensitive health data (uploaded PDFs/images) via OCR + Gemini AI, and provides structured explanations, PDF reports, audio summaries, and doctor recommendations.

## Architecture
- **Backend**: FastAPI (Python 3.11) at `backend/src/tahalilai/`
- **Frontend**: Next.js 15 (React 19, Tailwind 4) at `frontend/src/`
- **Database**: SQLite via SQLAlchemy ORM at `backend/data/tahalilai.db`
- **AI**: Google Gemini API (primary), local llama.cpp (fallback, dev only)
- **Deployment**: Docker containers on Railway (two services)

## Security Rules (MANDATORY)

### Never Do
- Never commit `.env` files or any file containing real API keys, passwords, or tokens
- Never add `eval()`, `exec()`, `os.system()`, or `subprocess.call(shell=True)`
- Never use raw SQL strings — always use SQLAlchemy ORM with parameterized queries
- Never expose internal file paths, stack traces, or debug info in API error responses
- Never run `rm -rf` on `uploads/`, `data/`, or any directory without explicit user confirmation
- Never hardcode credentials, API keys, or secrets in source code
- Never serve the `data/` directory via StaticFiles or any public mount
- Never disable CORS validation or set `cors_origins = ["*"]` in production
- Never skip the pre-commit secret scanning hook (`--no-verify`)

### Always Do
- Always validate uploaded file types via magic bytes (`utils/security.py`)
- Always enforce the 10MB upload size limit server-side
- Always use `sanitize_filename()` on user-provided filenames
- Always return generic error messages to clients; log details server-side
- Always use `EmailStr` for email address validation
- Always run the backend Docker container as non-root user (`appuser`)
- Always set `CORS_ORIGINS` to specific frontend domains in production

## Key File Paths
- Config: `backend/src/tahalilai/config.py`
- Main app: `backend/src/tahalilai/app.py`
- Database: `backend/src/tahalilai/database.py`
- Security utils: `backend/src/tahalilai/utils/security.py`
- Schemas: `backend/src/tahalilai/schemas.py`
- Translations: `frontend/src/context/LanguageContext.tsx`

## Conventions
- All backend services return structured dicts, never raise to the caller
- Error strings are prefixed with `"Error:"` by convention
- The `_jobs` dict is in-memory only — lost on server restart
- OCR text, age, gender flow into Gemini prompts — be mindful of prompt injection
- Arabic UI uses Tajawal font (Google Fonts), applied via `[dir="rtl"]` CSS selector
