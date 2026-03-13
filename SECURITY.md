# Security Policy — TahalilAI

## Supported Versions

| Version | Supported |
|---------|-----------|
| 1.1.x   | Yes       |
| < 1.1   | No        |

## Reporting a Vulnerability

If you discover a security vulnerability in TahalilAI, please report it responsibly:

1. **Do NOT** open a public GitHub issue
2. Email: **security@tahalilai.com** (or contact the maintainers directly)
3. Include: description, steps to reproduce, and potential impact
4. We will acknowledge within **48 hours** and provide a fix timeline within **7 days**

## Threat Model

### Data Flow
```
User browser  -->  Next.js frontend  -->  FastAPI backend  -->  Gemini API
                                          |                     |
                                          +-- OCR (Tesseract)   +-- Translation
                                          +-- SQLite (doctors)  +-- Chat Q&A
                                          +-- PDF generation
                                          +-- TTS audio
                                          +-- Email (SMTP)
                                          +-- WhatsApp (Meta API)
```

### Trust Boundaries
| Boundary | Input | Risk |
|----------|-------|------|
| User -> Backend | File uploads, form fields, chat messages | Malicious files, prompt injection, XSS via filenames |
| Backend -> Gemini | OCR text + user context | Prompt injection via crafted PDFs |
| Backend -> SMTP | Recipient email | Email abuse, credential leak |
| Backend -> WhatsApp | Phone number | Message spam, credential leak |
| Backend -> StaticFiles | Generated PDFs/audio | Path traversal, DB exposure |

### Mitigations in Place
- File type validation via magic bytes (PDF/JPEG/PNG only)
- Server-side 10MB upload size limit
- Filename sanitization (alphanumeric + dot/dash/underscore only)
- SQLite DB stored outside the StaticFiles mount (`data/` not `uploads/`)
- Rate limiting on email/WhatsApp/translate/analyze endpoints
- Email format validation via Pydantic `EmailStr`
- Non-root Docker container user
- CORS restricted to configured origins only
- Pre-commit hook blocks accidental secret commits
- Error messages never expose internal file paths

### Known Limitations
- **No authentication**: All endpoints are public. Rate limiting provides basic abuse protection but not access control.
- **Prompt injection**: User-controlled text flows into Gemini prompts. Input length limits are enforced but full prompt injection defense is not feasible at the application layer.
- **In-memory job store**: `_jobs` dict is lost on restart. Not suitable for multi-instance deployments without a shared store (Redis/DB).
- **SQLite concurrency**: Single-writer limitation. Acceptable for current traffic but not horizontally scalable.

## Security Checklist for Contributors

Before submitting a PR:
- [ ] No hardcoded secrets or API keys in source
- [ ] All user input validated and sanitized
- [ ] Error messages don't leak internal paths or stack traces
- [ ] Database queries use ORM (no raw SQL)
- [ ] File uploads validated by magic bytes, not just extension
- [ ] New endpoints include rate limiting if they call external services
