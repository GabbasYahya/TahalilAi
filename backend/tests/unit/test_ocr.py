"""Unit tests for the OCR service."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from tahalilai.services.ocr import perform_ocr


class TestPerformOcr:
    """Tests for ``perform_ocr``."""

    def test_file_not_found(self, tmp_path: Path) -> None:
        result = perform_ocr(tmp_path / "nonexistent.png")
        assert result.startswith("Error:")
        assert "not found" in result

    @patch("tahalilai.services.ocr.pytesseract")
    @patch("tahalilai.services.ocr.Image")
    def test_successful_ocr(
        self, mock_image: MagicMock, mock_tess: MagicMock, tmp_path: Path
    ) -> None:
        img_file = tmp_path / "lab.png"
        img_file.write_bytes(b"\x89PNG" + b"\x00" * 50)

        mock_tess.image_to_string.return_value = "Hemoglobin: 14.5 g/dL"

        result = perform_ocr(img_file, lang="eng")

        assert result == "Hemoglobin: 14.5 g/dL"
        mock_image.open.assert_called_once()

    @patch("tahalilai.services.ocr.pytesseract")
    @patch("tahalilai.services.ocr.Image")
    def test_ocr_exception(
        self, mock_image: MagicMock, mock_tess: MagicMock, tmp_path: Path
    ) -> None:
        img_file = tmp_path / "bad.png"
        img_file.write_bytes(b"\x89PNG" + b"\x00" * 50)

        mock_image.open.side_effect = OSError("corrupt image data")

        result = perform_ocr(img_file)
        assert result.startswith("Error during OCR:")
