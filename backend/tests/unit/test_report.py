"""Unit tests for the PDF report generator."""

from __future__ import annotations

from pathlib import Path

from tahalilai.services.report import generate_arabic_pdf_report, generate_pdf_report

# ---------------------------------------------------------------------------
# English PDF
# ---------------------------------------------------------------------------


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
        text = "**Summary**\n---\n- **Test**: Value (Normal)\nRegular text line\n"
        output = tmp_path / "formatted.pdf"
        generate_pdf_report(text, output)
        assert output.exists()
        assert output.stat().st_size > 100

    def test_handles_unicode_gracefully(self, tmp_path: Path) -> None:
        text = "المريض: بعض النص العربي للاختبار"
        output = tmp_path / "unicode.pdf"
        generate_pdf_report(text, output)
        assert output.exists()


# ---------------------------------------------------------------------------
# Arabic PDF
# ---------------------------------------------------------------------------


class TestGenerateArabicPdfReport:
    """Tests for ``generate_arabic_pdf_report``."""

    def test_creates_pdf_file(self, tmp_path: Path) -> None:
        arabic_text = "**ملخص**\n- الهيموغلوبين: 14.5 غ/ديسيلتر (طبيعي)\nنتائجك ضمن المعدل الطبيعي.\n"
        output = tmp_path / "report_ar.pdf"
        result = generate_arabic_pdf_report(arabic_text, output)

        assert result == output
        assert output.exists()
        assert output.stat().st_size > 0

    def test_pdf_header_signature(self, tmp_path: Path) -> None:
        output = tmp_path / "ar_header.pdf"
        generate_arabic_pdf_report("نص تجريبي", output)

        with open(output, "rb") as f:
            sig = f.read(5)
        assert sig == b"%PDF-"

    def test_handles_empty_content(self, tmp_path: Path) -> None:
        output = tmp_path / "ar_empty.pdf"
        generate_arabic_pdf_report("", output)
        assert output.exists()

    def test_handles_section_headers(self, tmp_path: Path) -> None:
        text = "**تحليل الدم الكامل**\n- كريات الدم الحمراء: طبيعية\n---\n**ملخص**\nكل شيء طبيعي.\n"
        output = tmp_path / "ar_sections.pdf"
        generate_arabic_pdf_report(text, output)
        assert output.exists()
        assert output.stat().st_size > 100
