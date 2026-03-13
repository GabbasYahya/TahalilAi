"""Centralized application configuration via pydantic-settings.

Settings are loaded from environment variables and the project-root ``.env`` file.
Override any setting by exporting the corresponding environment variable
(e.g. ``GEMINI_API_KEY``, ``TESSERACT_CMD``).
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/ root — three levels up from src/tahalilai/config.py
_BACKEND_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    """Application settings, auto-populated from env vars / ``.env``."""

    model_config = SettingsConfigDict(
        env_file=str(_BACKEND_DIR.parent / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── Directories ────────────────────────────────────────────────────────
    backend_dir: Path = _BACKEND_DIR

    # ── LLM Inference ──────────────────────────────────────────────────────
    llama_cli: str = "bin/llama-cli.exe"
    llm_model: str = "Models/Ministral-3-3B-Instruct-2512-Q5_K_M.gguf"
    model_timeout: int = 600

    # ── Gemini Translation ─────────────────────────────────────────────────
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"

    # ── Server ─────────────────────────────────────────────────────────────
    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: list[str] = []

    # ── Environment ──────────────────────────────────────────────────────
    environment: str = "development"  # development | staging | production

    # ── Upload limits ────────────────────────────────────────────────────
    max_upload_bytes: int = 10 * 1024 * 1024  # 10 MB

    # ── Tesseract OCR ──────────────────────────────────────────────────────
    tesseract_cmd: str = ""
    ocr_languages: str = "fra+eng+ara"

    # ── Email (Gmail SMTP) ──────────────────────────────────────────────────
    # Why SMTP_SSL on port 465: it's always encrypted from the start,
    # simpler than STARTTLS on port 587 which starts plain then upgrades.
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 465
    smtp_sender_email: str = ""       # your Gmail address
    smtp_app_password: str = ""       # 16-char App Password (NOT your Gmail password)

    # ── WhatsApp (Cloud API) ────────────────────────────────────────────────
    # Get these from https://developers.facebook.com > WhatsApp > API Setup
    whatsapp_access_token: str = ""
    whatsapp_phone_number_id: str = ""
    whatsapp_api_version: str = "v19.0"

    # ── Google Maps (optional, for geocoding / ratings) ──────────────────────
    google_maps_api_key: str = ""

    # ── Upload cleanup ────────────────────────────────────────────────────────
    # Files older than this many hours are deleted by the background sweep.
    uploads_max_age_hours: float = 24.0
    # How often (in seconds) the cleanup sweep runs. Default: 3600 (every hour).
    uploads_cleanup_interval_seconds: int = 3600

    # ── Computed paths ─────────────────────────────────────────────────────
    @property
    def uploads_dir(self) -> Path:
        """Runtime directory for uploaded files and generated artifacts."""
        path = self.backend_dir / "uploads"
        path.mkdir(exist_ok=True)
        return path

    @property
    def data_dir(self) -> Path:
        """Directory for persistent data (SQLite DB). NOT web-accessible."""
        path = self.backend_dir / "data"
        path.mkdir(exist_ok=True)
        return path

    @property
    def llama_cli_path(self) -> Path:
        """Absolute path to the llama-cli binary."""
        return self.backend_dir / self.llama_cli

    @property
    def model_path(self) -> Path:
        """Absolute path to the GGUF model file."""
        return self.backend_dir / self.llm_model

    @property
    def assets_dir(self) -> Path:
        """Directory for static assets (e.g. TTS reference audio)."""
        return self.backend_dir / "assets"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached :class:`Settings` instance (singleton)."""
    return Settings()
