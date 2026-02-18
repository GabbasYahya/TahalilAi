"""OCR service using Tesseract.

Extracts text from medical report images (PDF, PNG, JPEG) supporting
English, French, and Arabic scripts.
"""

from __future__ import annotations

from pathlib import Path

import pytesseract
from PIL import Image

from tahalilai.config import get_settings


def perform_ocr(image_path: str | Path, lang: str | None = None) -> str:
    """Extract text from an image using Tesseract OCR.

    Args:
        image_path: Path to the image file.
        lang: Tesseract language string (e.g. ``fra+eng+ara``).
            Defaults to the value in :class:`~tahalilai.config.Settings`.

    Returns:
        Extracted text, or an error message prefixed with ``Error:``.
    """
    settings = get_settings()
    path = Path(image_path)

    if not path.exists():
        return f"Error: File not found at {path}"

    if lang is None:
        lang = settings.ocr_languages

    if settings.tesseract_cmd:
        pytesseract.pytesseract.tesseract_cmd = settings.tesseract_cmd

    try:
        image = Image.open(path)
        return pytesseract.image_to_string(image, lang=lang)  # type: ignore[no-any-return]
    except Exception as exc:
        return f"Error during OCR: {exc}"
