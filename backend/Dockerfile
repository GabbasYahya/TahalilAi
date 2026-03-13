# ── Stage 1: builder — install Python deps ──────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build tools needed to compile some wheels
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
COPY src/ ./src/

# Install the package and all runtime deps into /app/.venv
RUN pip install --no-cache-dir --prefix=/install -e .


# ── Stage 2: runtime ─────────────────────────────────────────────────────────
FROM python:3.11-slim

WORKDIR /app

# System deps:
#   tesseract-ocr        — OCR engine
#   tesseract-ocr-eng/fra/ara — language packs
#   libmagic1            — file-type detection (python-magic on Linux)
#   fonts-liberation     — free Liberation Sans (replaces Segoe UI for PDFs)
#   fonts-arabeyes       — open-source Arabic fonts for PDF Arabic rendering
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-fra \
    tesseract-ocr-ara \
    libmagic1 \
    fonts-liberation \
    fonts-arabeyes \
    && rm -rf /var/lib/apt/lists/*

# Copy installed Python packages from builder
COPY --from=builder /install /usr/local

# Copy application source
COPY src/ ./src/
COPY pyproject.toml ./

# Seed data — CSV files used to populate doctors and hospitals on first startup
COPY doctors_data_clean.csv health_facilities_clean.csv ./

# Re-install in editable mode so the package is importable
RUN pip install --no-cache-dir -e .

# Create a non-root user (mirrors frontend Dockerfile pattern)
RUN addgroup --system --gid 1001 appgroup \
    && adduser --system --uid 1001 --ingroup appgroup appuser

# Directories for runtime data — owned by appuser
#   uploads/  = temporary user files + generated PDFs/audio (StaticFiles mount)
#   data/     = SQLite DB (NOT web-accessible)
RUN mkdir -p uploads data \
    && chown -R appuser:appgroup uploads data

USER appuser

EXPOSE 8080

# TESSERACT_CMD is not needed — tesseract is on PATH via apt-get
CMD ["python", "-m", "tahalilai"]
