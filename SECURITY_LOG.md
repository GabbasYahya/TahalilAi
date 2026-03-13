# Security Hardening Changelog — TahalilAI

All changes made during the security hardening session are logged here.

---

## Phase 3 — Code Security Fixes

### [CRITICAL] Moved SQLite DB out of StaticFiles mount
- **File**: `backend/src/tahalilai/database.py`
- **Change**: DB path moved from `uploads/tahalilai.db` to `data/tahalilai.db`
- **File**: `backend/src/tahalilai/config.py`
- **Change**: Added `data_dir` property pointing to `backend/data/` (not web-accessible)
- **Risk mitigated**: Anyone could download the full doctor/hospital database at `/uploads/tahalilai.db`

### [HIGH] Backend Dockerfile now runs as non-root user
- **File**: `backend/Dockerfile`
- **Change**: Added `appuser:appgroup` (UID 1001), `USER appuser` directive, `chown` on `uploads/` and `data/`
- **Risk mitigated**: Container escape would grant root access to host

### [HIGH] CORS origins restricted
- **File**: `backend/src/tahalilai/config.py`
- **Change**: `cors_origins` default changed from `["*"]` to `[]`. Must be explicitly set via `CORS_ORIGINS` env var.
- **File**: `.env.example`
- **Change**: Added `CORS_ORIGINS` and `ENVIRONMENT` variables
- **Risk mitigated**: Any website could call the API (credential abuse, data exfiltration)

### [HIGH] Rate limiting on sensitive endpoints
- **File**: `backend/src/tahalilai/app.py`
- **Change**: Added in-memory per-IP rate limiter. Limits: email 3/min, whatsapp 3/min, translate 10/min, analyze 5/min
- **Endpoints affected**: `POST /send-email`, `POST /send-whatsapp`
- **Risk mitigated**: Unlimited email/WhatsApp spam using server credentials

### [MEDIUM] Server-side file upload size limit
- **File**: `backend/src/tahalilai/app.py`
- **Change**: Added `file_path.stat().st_size > settings.max_upload_bytes` check (10MB default)
- **File**: `backend/src/tahalilai/config.py`
- **Change**: Added `max_upload_bytes: int = 10 * 1024 * 1024`
- **Risk mitigated**: DoS via large file uploads

### [MEDIUM] Error message sanitization
- **File**: `backend/src/tahalilai/services/email_sender.py`
- **Change**: Removed server filesystem path from PDF-not-found error. Replaced with generic message; path logged server-side.
- **Risk mitigated**: Information leakage of internal paths

### [MEDIUM] Email format validation
- **File**: `backend/src/tahalilai/schemas.py`
- **Change**: `recipient_email` field changed from `str` with `min_length=5` to `EmailStr` (Pydantic built-in)
- **Risk mitigated**: Invalid email addresses triggering SMTP errors

---

## Phase 6 — Environment Isolation

### Hardened .dockerignore files
- **File**: `backend/.dockerignore`
- **Change**: Expanded to exclude `.env`, `.env.*`, `.git`, `.vscode`, `data/`, CSVs, scripts, debug files
- **File**: `frontend/.dockerignore`
- **Change**: Expanded to exclude `.env`, `.env.*`, `.git`, `.vscode`
- **Risk mitigated**: Secrets or dev artifacts accidentally baked into Docker images

### Environment variable for deployment mode
- **File**: `backend/src/tahalilai/config.py`
- **Change**: Added `environment: str = "development"` setting
- **File**: `.env.example`
- **Change**: Added `ENVIRONMENT=development` and `CORS_ORIGINS` variables

---

## Phase 1 — Secret Scanning

### Pre-commit hook installed
- **File**: `scripts/pre-commit` (new)
- **Installed to**: `.git/hooks/pre-commit`
- **Change**: Blocks commits containing Google API key patterns, AWS keys, Slack tokens, SMTP passwords, WhatsApp tokens, or `.env` files
- **Risk mitigated**: Accidental credential commit

---

## Phase 5 — Claude Code Hardening

### CLAUDE.md security policy created
- **File**: `CLAUDE.md` (new)
- **Content**: Project overview, architecture, mandatory security rules (Never/Always lists), key file paths, conventions

---

## Phase 7 — Security Documentation

### SECURITY.md created
- **File**: `SECURITY.md` (new)
- **Content**: Supported versions, vulnerability disclosure policy, threat model diagram, trust boundaries table, mitigations list, known limitations, contributor security checklist

---

## Phase 2 — Dependency Audit Results

### Frontend (npm audit)
- **ajv < 6.14.0** — ReDoS (moderate). Dev dependency only. Fix: `npm audit fix`
- **minimatch <= 3.1.3** — ReDoS (high). Dev dependency only. Fix: `npm audit fix`
- **Action**: Both fixable with `npm audit fix`. Neither affects production runtime.

### Backend (pip-audit)
- Django 4.2.13 and cryptography 45.0.5 flagged — these are **not TahalilAI dependencies**. They exist in the global Python environment from other projects.
- TahalilAI's actual deps (FastAPI, SQLAlchemy, google-genai, Pydantic, etc.) have **no known vulnerabilities**.

---

## Files Created
| File | Purpose |
|------|---------|
| `SECURITY_LOG.md` | This changelog |
| `SECURITY.md` | Vulnerability disclosure + threat model |
| `CLAUDE.md` | Claude Code security policy |
| `scripts/pre-commit` | Secret scanning git hook |

## Files Modified
| File | Change |
|------|--------|
| `backend/src/tahalilai/database.py` | DB path: `uploads/` → `data/` |
| `backend/src/tahalilai/config.py` | Added `data_dir`, `environment`, `max_upload_bytes`; CORS default `[]` |
| `backend/src/tahalilai/app.py` | Rate limiter, file size check, `Request` import |
| `backend/src/tahalilai/schemas.py` | `EmailStr` for email validation |
| `backend/src/tahalilai/services/email_sender.py` | Sanitized error message |
| `backend/Dockerfile` | Non-root user, `data/` directory |
| `backend/.dockerignore` | Expanded exclusions |
| `frontend/.dockerignore` | Expanded exclusions |
| `.env.example` | Added `ENVIRONMENT`, `CORS_ORIGINS` |
| `.git/hooks/pre-commit` | Installed secret scanning hook |
