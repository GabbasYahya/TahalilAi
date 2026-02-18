"""Unit tests for security utilities."""

from __future__ import annotations

from pathlib import Path

import pytest

from tahalilai.utils.security import sanitize_filename, validate_file


class TestSanitizeFilename:
    """Tests for ``sanitize_filename``."""

    def test_basic_filename(self) -> None:
        assert sanitize_filename("report.pdf") == "report.pdf"

    def test_strips_path_components(self) -> None:
        assert sanitize_filename("/etc/passwd") == "passwd"
        assert sanitize_filename("C:\\Users\\file.png") == "file.png"

    def test_replaces_unsafe_characters(self) -> None:
        assert sanitize_filename("my file (1).pdf") == "my_file__1_.pdf"
        assert sanitize_filename("café.jpg") == "caf_.jpg"

    def test_preserves_safe_characters(self) -> None:
        assert sanitize_filename("report-2024_v2.pdf") == "report-2024_v2.pdf"


class TestValidateFile:
    """Tests for ``validate_file``."""

    def test_valid_png(self, tmp_path: Path) -> None:
        png = tmp_path / "test.png"
        png.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 50)
        assert validate_file(png) is True

    def test_valid_jpeg(self, tmp_path: Path) -> None:
        jpg = tmp_path / "test.jpg"
        jpg.write_bytes(b"\xff\xd8\xff\xe0" + b"\x00" * 50)
        assert validate_file(jpg) is True

    def test_valid_pdf(self, tmp_path: Path) -> None:
        pdf = tmp_path / "test.pdf"
        pdf.write_bytes(b"%PDF-1.4" + b"\x00" * 50)
        assert validate_file(pdf) is True

    def test_rejects_text_file(self, tmp_path: Path) -> None:
        txt = tmp_path / "test.txt"
        txt.write_text("hello world", encoding="utf-8")
        with pytest.raises(ValueError, match=r"[Ss]ecurity"):
            validate_file(txt)

    def test_rejects_empty_file(self, tmp_path: Path) -> None:
        empty = tmp_path / "empty.bin"
        empty.write_bytes(b"")
        with pytest.raises(ValueError):
            validate_file(empty)
