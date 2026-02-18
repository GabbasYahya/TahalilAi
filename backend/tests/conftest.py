"""Shared test fixtures for TahalilAI."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from tahalilai.app import create_app


@pytest.fixture()
def client() -> TestClient:  # type: ignore[misc]
    """FastAPI test client with a fresh app instance."""
    application = create_app()
    with TestClient(application) as tc:
        yield tc  # type: ignore[misc]


@pytest.fixture()
def tmp_image(tmp_path: Path) -> Path:
    """Create a minimal valid PNG file for upload tests."""
    # Minimal 1x1 white PNG (67 bytes)
    png_bytes = (
        b"\x89PNG\r\n\x1a\n"  # signature
        b"\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02"
        b"\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx"
        b"\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N"
        b"\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    path = tmp_path / "test.png"
    path.write_bytes(png_bytes)
    return path


@pytest.fixture()
def sample_analysis_text() -> str:
    """Representative AI analysis text for testing."""
    return (
        "**Summary**: Your blood test results are within normal ranges.\n\n"
        "**Detailed Analysis**:\n"
        "- **Hemoglobin**: 14.5 g/dL (Normal)\n"
        "  *Meaning*: Healthy oxygen-carrying capacity.\n"
    )
