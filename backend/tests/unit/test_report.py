"""Unit tests for the PDF report generator."""

from __future__ import annotations

from pathlib import Path

from tahalilai.services.report import generate_pdf_report


class TestGeneratePdfReport:
    """Tests for ``generate_pdf_report``."""

    def test_creates_pdf_file(self, tmp_path: Path, sample_analysis_text: str) -> None:
        output = tmp_path / "report.pdf"
        result = generate_pdf_report(sample_analysis_text, output)

        assert result == output
        assert output.exists()
        assert output.stat().st_size > 0

    def test_pdf_header(self, tmp_path: Path) -> None:
        output = tmp_path / "header_test.pdf"
        generate_pdf_report("Simple test content", output)

        with open(output, "rb") as f:
            header = f.read(5)
        assert header == b"%PDF-"

    def test_handles_empty_content(self, tmp_path: Path) -> None:
        output = tmp_path / "empty.pdf"
        generate_pdf_report("", output)
        assert output.exists()

    def test_handles_markdown_formatting(self, tmp_path: Path) -> None:
        text = "**Summary**: Results overview\n---\n- **Test**: Value (Normal)\nRegular text line\n"
        output = tmp_path / "formatted.pdf"
        generate_pdf_report(text, output)
        assert output.exists()
        assert output.stat().st_size > 100

    def test_handles_unicode_gracefully(self, tmp_path: Path) -> None:
        text = "العربية: بعض النص العربي للاختبار"
        output = tmp_path / "unicode.pdf"
        generate_pdf_report(text, output)
        assert output.exists()
