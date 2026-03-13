"""PDF report generation using fpdf2.

Generates branded, print-ready PDF reports from AI analysis text.
Supports both English (LTR) and Arabic (RTL) layouts.

Arabic rendering uses ``arabic-reshaper`` + ``python-bidi`` to pre-shape
characters into visual order so they display correctly in any PDF viewer.
"""

from __future__ import annotations

import os
import re
from datetime import datetime
from pathlib import Path

from fpdf import FPDF
from fpdf.enums import XPos, YPos  # noqa: F401 – kept for fpdf2 compatibility

# ---------------------------------------------------------------------------
# Colour palette
# ---------------------------------------------------------------------------
_NAVY    = (19,  82, 118)    # header background
_BLUE    = (36, 113, 163)    # section-header strip
_BGBLUE  = (234, 242, 248)   # section body tint
_DARK    = (28,  40,  51)    # body text
_MUTED   = (120, 130, 140)   # footer / meta
_WHITE   = (255, 255, 255)
_RULE    = (189, 195, 199)   # thin divider
_ACCENT  = (93, 173, 226)    # bright accent line under banner

# Status colours for structured report
_GREEN     = (39, 174,  96)   # normal
_GREENTINT = (235, 251, 238)
_SKYTINT   = (232, 246, 253)
_AMBERTEXT = (126, 82,   0)
_AMBERTIN  = (255, 249, 219)
_ORANGE    = (211, 84,   0)
_RED       = (192, 57,  43)
_REDTINT   = (253, 237, 236)

# ---------------------------------------------------------------------------
# Layout constants
# ---------------------------------------------------------------------------
_MARGIN   = 18   # left + right page margin (mm)
_LH       = 6    # body line height (mm)
_HDR_H    = 40   # header band height (mm)
_INDENT   = 6    # bullet indent (mm)

# ---------------------------------------------------------------------------
# Font paths — tried in order; first existing file wins
# ---------------------------------------------------------------------------

def _find_font(*candidates: str) -> str:
    """Return the first path that exists, or the last one as a placeholder."""
    for p in candidates:
        if os.path.exists(p):
            return p
    return candidates[-1]

_SEGOE = _find_font(
    r"C:\Windows\Fonts\segoeui.ttf",                                            # Windows
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",          # Linux (fonts-liberation)
    "/usr/share/fonts/truetype/freefont/FreeSans.ttf",                          # Linux fallback
)
_SEGOE_B = _find_font(
    r"C:\Windows\Fonts\segoeuib.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
)
_ARABIC = _find_font(
    r"C:\Windows\Fonts\arabtype.ttf",                                            # Windows
    "/usr/share/fonts/truetype/arabeyes/ae_AlArabiya.ttf",                      # Linux (fonts-arabeyes)
    "/usr/share/fonts/truetype/noto/NotoNaskhArabic-Regular.ttf",               # Linux (fonts-noto)
    r"C:\Windows\Fonts\segoeui.ttf",                                             # Windows last resort
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",          # Linux last resort
)


# ---------------------------------------------------------------------------
# FPDF subclass
# ---------------------------------------------------------------------------

class _PDFReport(FPDF):  # type: ignore[misc]
    """Branded FPDF document — header band + footer with disclaimer."""

    # These attributes are set externally *before* add_page() is called
    _font: str = "Helvetica"
    _font_bold: str = "Helvetica"   # may equal _font when no bold registered
    _is_rtl: bool = False
    _subtitle: str = "Medical Lab Report Analysis"
    _size_body: int = 10
    _size_section: int = 11

    # -- Header ----------------------------------------------------------------

    def header(self) -> None:  # noqa: D401
        # ── Navy background band ──────────────────────────────────────────────
        self.set_fill_color(*_NAVY)
        self.rect(0, 0, self.w, _HDR_H, style="F")

        # ── Brand name (always Latin, Helvetica) ──────────────────────────────
        self.set_text_color(*_WHITE)
        self.set_font("Helvetica", "B", 22)
        self.set_xy(_MARGIN, 8)
        self.cell(0, 11, "TahalilAI", align="L")

        # ── Date top-right ────────────────────────────────────────────────────
        date_str = datetime.now().strftime("%d %b %Y")
        self.set_font("Helvetica", "", 8)
        self.set_xy(0, 10)
        self.cell(self.w - _MARGIN, 7, date_str, align="R")

        # ── Sub-title line ────────────────────────────────────────────────────
        self.set_xy(_MARGIN, 22)
        if self._is_rtl:
            # Switch to the registered Arabic font before rendering Arabic text
            try:
                self.set_font(self._font, "", 10)
            except Exception:
                pass  # stay on Helvetica — subtitle may be blank
            sub = _prepare_arabic(self._subtitle)
            try:
                self.cell(0, 7, sub, align="R")
            except Exception:
                pass  # swallow encoding errors for edge cases
        else:
            self.set_font("Helvetica", "", 10)
            self.cell(0, 7, self._subtitle, align="L")

        # ── Accent underline ──────────────────────────────────────────────────
        self.set_draw_color(*_ACCENT)
        self.set_line_width(0.8)
        self.line(_MARGIN, _HDR_H, self.w - _MARGIN, _HDR_H)
        self.set_line_width(0.2)

        # ── Reset cursor below header ─────────────────────────────────────────
        self.set_y(_HDR_H + 5)
        self.set_text_color(*_DARK)

    # -- Footer ----------------------------------------------------------------

    def footer(self) -> None:  # noqa: D401
        self.set_y(-16)
        self.set_draw_color(*_RULE)
        self.set_line_width(0.3)
        self.line(_MARGIN, self.get_y(), self.w - _MARGIN, self.get_y())
        self.ln(1)
        self.set_font("Helvetica", "I", 7)
        self.set_text_color(*_MUTED)
        self.cell(
            0, 5,
            f"Page {self.page_no()}  |  TahalilAI  |  "
            "AI-generated report - always consult a qualified physician.",
            align="C",
        )


# ---------------------------------------------------------------------------
# Font setup
# ---------------------------------------------------------------------------

def _setup_english_fonts(pdf: _PDFReport) -> None:
    """Register Segoe UI (or fall back to Helvetica) and configure pdf."""
    if os.path.exists(_SEGOE) and os.path.exists(_SEGOE_B):
        try:
            pdf.add_font("Segoe", "",  _SEGOE)
            pdf.add_font("Segoe", "B", _SEGOE_B)
            pdf._font      = "Segoe"
            pdf._font_bold = "Segoe"
            pdf._size_body    = 10
            pdf._size_section = 11
            return
        except Exception:
            pass
    # Helvetica is built-in — always available
    pdf._font      = "Helvetica"
    pdf._font_bold = "Helvetica"
    pdf._size_body    = 10
    pdf._size_section = 11


def _setup_arabic_fonts(pdf: _PDFReport) -> None:
    """Register Arabic font (or fall back to Segoe / Helvetica)."""
    for path, name in ((_ARABIC, "Arabic"), (_SEGOE, "Segoe")):
        if os.path.exists(path):
            try:
                pdf.add_font(name, "", path)
                pdf._font      = name
                pdf._font_bold = name   # no separate bold for these fonts
                pdf._size_body    = 12  # Arabic glyphs read better at 12 pt
                pdf._size_section = 13
                return
            except Exception:
                continue
    pdf._font      = "Helvetica"
    pdf._font_bold = "Helvetica"
    pdf._size_body    = 10
    pdf._size_section = 11


# ---------------------------------------------------------------------------
# Line classification
# ---------------------------------------------------------------------------

_RE_SECTION = re.compile(r"^\*\*(.+?)\*\*\s*:?\s*$")
_RE_RULE    = re.compile(r"^-{3,}$")
_RE_BULLET  = re.compile(r"^-\s+(.+)")


def _classify(raw: str) -> tuple[str, str]:
    """Return *(kind, cleaned_text)* for a single markdown line.

    Kinds: ``"blank"`` | ``"rule"`` | ``"section"`` | ``"bullet"`` | ``"normal"``
    """
    line = raw.strip()
    if not line:
        return "blank", ""
    if _RE_RULE.match(line):
        return "rule", ""
    m = _RE_SECTION.match(line)
    if m:
        return "section", m.group(1).strip()
    m = _RE_BULLET.match(line)
    if m:
        return "bullet", re.sub(r"\*\*(.+?)\*\*", r"\1", m.group(1))
    return "normal", re.sub(r"\*\*(.+?)\*\*", r"\1", line)


# ---------------------------------------------------------------------------
# English renderer
# ---------------------------------------------------------------------------

def _render_english(pdf: _PDFReport, text: str) -> None:
    """Write the English analysis into *pdf*."""
    font  = pdf._font
    fontb = pdf._font_bold
    sb    = pdf._size_body
    ss    = pdf._size_section
    cw    = pdf.w - 2 * _MARGIN   # usable content width

    for raw in text.split("\n"):
        kind, content = _classify(raw)

        if kind == "blank":
            pdf.ln(2)

        elif kind == "rule":
            pdf.ln(3)
            pdf.set_draw_color(*_RULE)
            pdf.set_line_width(0.3)
            pdf.line(_MARGIN, pdf.get_y(), pdf.w - _MARGIN, pdf.get_y())
            pdf.ln(4)

        elif kind == "section":
            pdf.ln(4)
            # Filled blue banner for section header
            pdf.set_fill_color(*_BLUE)
            pdf.set_text_color(*_WHITE)
            try:
                pdf.set_font(fontb, "B", ss)
            except Exception:
                pdf.set_font("Helvetica", "B", ss)
            pdf.multi_cell(0, 8, f"  {content}", fill=True, align="L")
            pdf.set_text_color(*_DARK)
            pdf.ln(1)

        elif kind == "bullet":
            try:
                pdf.set_font(font, "", sb)
            except Exception:
                pdf.set_font("Helvetica", "", sb)
            pdf.set_text_color(*_DARK)
            # Bullet symbol + text with indent
            pdf.set_x(_MARGIN + _INDENT)
            try:
                pdf.multi_cell(cw - _INDENT, _LH, f"\u2022  {content}", align="L")
            except Exception:
                _safe_cell(pdf, content)

        else:  # normal
            try:
                pdf.set_font(font, "", sb)
            except Exception:
                pdf.set_font("Helvetica", "", sb)
            pdf.set_text_color(*_DARK)
            try:
                pdf.multi_cell(0, _LH, content, align="J")
            except Exception:
                _safe_cell(pdf, content)


# ---------------------------------------------------------------------------
# Arabic renderer
# ---------------------------------------------------------------------------

def _render_arabic(pdf: _PDFReport, text: str) -> None:
    """Write Arabic (RTL) analysis into *pdf*."""
    font = pdf._font
    ss   = pdf._size_section
    sb   = pdf._size_body

    for raw in text.split("\n"):
        kind, content = _classify(raw)

        if kind == "blank":
            pdf.ln(2)

        elif kind == "rule":
            pdf.ln(3)
            pdf.set_draw_color(*_RULE)
            pdf.set_line_width(0.3)
            pdf.line(_MARGIN, pdf.get_y(), pdf.w - _MARGIN, pdf.get_y())
            pdf.ln(4)

        elif kind == "section":
            pdf.ln(4)
            visual = _prepare_arabic(content)
            pdf.set_fill_color(*_BLUE)
            pdf.set_text_color(*_WHITE)
            try:
                pdf.set_font(font, "", ss)
            except Exception:
                pdf.set_font("Helvetica", "", ss)
            pdf.multi_cell(0, 9, f"  {visual}", fill=True, align="R")
            pdf.set_text_color(*_DARK)
            pdf.ln(1)

        elif kind == "bullet":
            visual = _prepare_arabic(content)
            try:
                pdf.set_font(font, "", sb)
            except Exception:
                pdf.set_font("Helvetica", "", sb)
            pdf.set_text_color(*_DARK)
            try:
                pdf.multi_cell(0, _LH + 1, f"{visual}  \u2022", align="R")
            except Exception:
                _safe_cell_r(pdf, visual)

        else:  # normal
            visual = _prepare_arabic(content)
            try:
                pdf.set_font(font, "", sb)
            except Exception:
                pdf.set_font("Helvetica", "", sb)
            pdf.set_text_color(*_DARK)
            try:
                pdf.multi_cell(0, _LH + 1, visual, align="R")
            except Exception:
                _safe_cell_r(pdf, visual)


# ---------------------------------------------------------------------------
# Arabic text preparation
# ---------------------------------------------------------------------------

def _prepare_arabic(text: str) -> str:
    """Reshape + apply bidi so Arabic text renders correctly in LTR PDF engines."""
    if not text:
        return text
    try:
        import arabic_reshaper            # type: ignore[import-untyped]
        from bidi.algorithm import get_display  # type: ignore[import-untyped]
        return get_display(arabic_reshaper.reshape(text))
    except ImportError:
        return text


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_pdf_report(
    text_content: str,
    output_path: str | Path,
    recommended_doctors: list[dict] | None = None,
    urgency: str = "routine",
    structured: object | None = None,
) -> Path:
    """Generate a styled English PDF report from analysis text.

    When *structured* (a ``StructuredAnalysis`` instance) is provided the
    report renders a rich layout with a status banner, biomarker table,
    abnormal findings, and recommendations.  Falls back to plain-text
    Markdown rendering when *structured* is ``None``.

    Args:
        text_content: Analysis text (may contain light markdown).
        output_path: Destination path for the ``.pdf`` file.
        recommended_doctors: Optional list of doctor dicts to append.
        urgency: Urgency level – ``"urgent"`` adds a critical-values notice.
        structured: Optional ``StructuredAnalysis`` for rich rendering.

    Returns:
        The :class:`~pathlib.Path` to the generated file.
    """
    output_path = Path(output_path)

    pdf = _PDFReport()
    pdf._subtitle = "Medical Lab Report Analysis"
    pdf._is_rtl   = False
    _setup_english_fonts(pdf)
    pdf.set_margins(_MARGIN, _HDR_H + 8, _MARGIN)
    pdf.set_auto_page_break(auto=True, margin=22)
    pdf.add_page()

    if structured is not None:
        _render_structured_en(pdf, structured)
    else:
        _render_english(pdf, text_content)

    if urgency == "urgent":
        _render_urgency_notice_en(pdf)

    if recommended_doctors:
        _render_doctors_en(pdf, recommended_doctors)

    pdf.output(str(output_path))
    return output_path


def generate_arabic_pdf_report(
    text_content: str,
    output_path: str | Path,
    recommended_doctors: list[dict] | None = None,
    urgency: str = "routine",
) -> Path:
    """Generate a styled Arabic (RTL) PDF report from translated analysis text.

    Args:
        text_content: Arabic analysis text (may contain light markdown).
        output_path: Destination path for the ``.pdf`` file.
        recommended_doctors: Optional list of doctor dicts to append.
        urgency: Urgency level – ``"urgent"`` adds a critical-values notice.

    Returns:
        The :class:`~pathlib.Path` to the generated file.
    """
    output_path = Path(output_path)

    pdf = _PDFReport()
    pdf._subtitle = "تحليل نتائج الفحوصات المخبرية"  # processed once in header()
    pdf._is_rtl   = True
    _setup_arabic_fonts(pdf)
    pdf.set_margins(_MARGIN, _HDR_H + 8, _MARGIN)
    pdf.set_auto_page_break(auto=True, margin=22)
    pdf.add_page()

    _render_arabic(pdf, text_content)

    if urgency == "urgent":
        _render_urgency_notice_ar(pdf)

    if recommended_doctors:
        _render_doctors_ar(pdf, recommended_doctors)

    pdf.output(str(output_path))
    return output_path


# ---------------------------------------------------------------------------
# Urgency notice renderers
# ---------------------------------------------------------------------------

def _render_urgency_notice_en(pdf: _PDFReport) -> None:
    """Render a red critical-values warning box (English)."""
    pdf.ln(6)
    pdf.set_fill_color(*_REDTINT)
    pdf.set_draw_color(*_RED)
    pdf.set_line_width(0.5)
    try:
        pdf.set_font(pdf._font_bold, "B", 11)
    except Exception:
        pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(*_RED)
    pdf.multi_cell(0, 8, "  \u26a0  Critical Values Detected", fill=True, align="L")
    try:
        pdf.set_font(pdf._font, "", 9)
    except Exception:
        pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*_RED)
    pdf.multi_cell(
        0, 6,
        "  Some results require prompt medical attention. "
        "Please consult a doctor as soon as possible.",
        fill=True, align="L",
    )
    pdf.set_line_width(0.2)
    pdf.set_text_color(*_DARK)


def _render_urgency_notice_ar(pdf: _PDFReport) -> None:
    """Render a red critical-values warning box (Arabic)."""
    pdf.ln(6)
    pdf.set_fill_color(*_REDTINT)
    pdf.set_draw_color(*_RED)
    pdf.set_line_width(0.5)
    try:
        pdf.set_font(pdf._font, "", 12)
    except Exception:
        pdf.set_font("Helvetica", "", 12)
    pdf.set_text_color(*_RED)
    pdf.multi_cell(0, 9, _prepare_arabic("قيم حرجة تستوجب العناية الفورية  \u26a0"), fill=True, align="R")
    pdf.multi_cell(
        0, 8,
        _prepare_arabic("بعض النتائج تستدعي مراجعة طبية عاجلة. يُرجى استشارة الطبيب في أقرب وقت ممكن."),
        fill=True, align="R",
    )
    pdf.set_line_width(0.2)
    pdf.set_text_color(*_DARK)


# ---------------------------------------------------------------------------
# Recommended-doctors renderers
# ---------------------------------------------------------------------------

def _render_doctors_en(pdf: _PDFReport, doctors: list[dict]) -> None:
    """Append a Recommended Doctors section (English)."""
    pdf.ln(6)
    # Section header
    pdf.set_fill_color(*_BLUE)
    pdf.set_text_color(*_WHITE)
    try:
        pdf.set_font(pdf._font_bold, "B", pdf._size_section)
    except Exception:
        pdf.set_font("Helvetica", "B", 11)
    pdf.multi_cell(0, 8, "  Recommended Doctors", fill=True, align="L")
    pdf.set_x(pdf.l_margin)  # fpdf2 2.8.x: reset x after fill multi_cell
    pdf.set_text_color(*_DARK)
    pdf.ln(2)

    for doc in doctors:
        try:
            pdf.set_font(pdf._font_bold, "B", pdf._size_body)
        except Exception:
            pdf.set_font("Helvetica", "B", 10)
        name = f"{doc.get('title', '')} {doc.get('name', '')}".strip()
        pdf.multi_cell(0, 6, name, align="L")
        pdf.set_x(pdf.l_margin)  # reset after name

        try:
            pdf.set_font(pdf._font, "", pdf._size_body - 1)
        except Exception:
            pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(*_MUTED)

        speciality = doc.get("speciality", "")
        if speciality:
            pdf.multi_cell(0, 5, f"  Specialty: {speciality}", align="L")
            pdf.set_x(pdf.l_margin)
        phone = doc.get("phone", "")
        if phone:
            pdf.multi_cell(0, 5, f"  Phone: {phone}", align="L")
            pdf.set_x(pdf.l_margin)
        address = doc.get("address", "")
        city    = doc.get("city", "")
        location = ", ".join(filter(None, [address, city]))
        if location:
            # Keep English report clean: strip chars not renderable in current font
            safe_location = location.encode("latin-1", "replace").decode("latin-1")
            pdf.multi_cell(0, 5, f"  Address: {safe_location}", align="L")
            pdf.set_x(pdf.l_margin)

        pdf.set_text_color(*_DARK)
        pdf.ln(3)


def _render_doctors_ar(pdf: _PDFReport, doctors: list[dict]) -> None:
    """Append a Recommended Doctors section (Arabic)."""
    pdf.ln(6)
    pdf.set_fill_color(*_BLUE)
    pdf.set_text_color(*_WHITE)
    try:
        pdf.set_font(pdf._font, "", pdf._size_section)
    except Exception:
        pdf.set_font("Helvetica", "", 12)
    pdf.multi_cell(0, 9, _prepare_arabic("الأطباء الموصى بهم  "), fill=True, align="R")
    pdf.set_x(pdf.l_margin)  # fpdf2 2.8.x: reset x after fill multi_cell
    pdf.set_text_color(*_DARK)
    pdf.ln(2)

    for doc in doctors:
        try:
            pdf.set_font(pdf._font, "", pdf._size_body)
        except Exception:
            pdf.set_font("Helvetica", "", 11)
        name = f"{doc.get('title', '')} {doc.get('name', '')}".strip()
        pdf.multi_cell(0, 7, _prepare_arabic(name), align="R")
        pdf.set_x(pdf.l_margin)  # reset after name

        try:
            pdf.set_font(pdf._font, "", pdf._size_body - 1)
        except Exception:
            pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(*_MUTED)

        speciality = doc.get("speciality", "")
        if speciality:
            pdf.multi_cell(0, 6, _prepare_arabic(f"التخصص: {speciality}  "), align="R")
            pdf.set_x(pdf.l_margin)
        phone = doc.get("phone", "")
        if phone:
            pdf.multi_cell(0, 6, _prepare_arabic(f"الهاتف: {phone}  "), align="R")
            pdf.set_x(pdf.l_margin)
        address = doc.get("address", "")
        city    = doc.get("city", "")
        location = ", ".join(filter(None, [address, city]))
        if location:
            pdf.multi_cell(0, 6, _prepare_arabic(f"العنوان: {location}  "), align="R")
            pdf.set_x(pdf.l_margin)

        pdf.set_text_color(*_DARK)
        pdf.ln(3)


# ---------------------------------------------------------------------------
# Internal utilities
# ---------------------------------------------------------------------------

def _safe_cell(pdf: _PDFReport, text: str) -> None:
    """Render *text* as a plain cell, silently truncating if needed."""
    try:
        safe = text.encode("latin-1", "ignore").decode("latin-1")
        pdf.multi_cell(0, _LH, safe, align="L")
    except Exception:
        pass


def _safe_cell_r(pdf: _PDFReport, text: str) -> None:
    """Render *text* right-aligned, silently truncating if needed."""
    try:
        pdf.multi_cell(0, _LH + 1, text, align="R")
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Structured PDF rendering helpers
# ---------------------------------------------------------------------------

_STATUS_COLORS = {
    "normal":        (_GREEN,  _GREENTINT, "All Normal"),
    "mostly_normal": (_BLUE,   _SKYTINT,   "Mostly Normal"),
    "abnormal":      (_ORANGE, _AMBERTIN,  "Abnormal Results"),
    "critical":      (_RED,    _REDTINT,   "Critical Values Detected"),
}

_BIOMARKER_STATUS_LABEL = {
    "normal":     "Normal",
    "high":       "High",
    "low":        "Low",
    "borderline": "Borderline",
}


def _section_header(pdf: _PDFReport, title: str) -> None:
    """Draw a blue filled section header bar."""
    pdf.ln(5)
    pdf.set_fill_color(*_BLUE)
    pdf.set_text_color(*_WHITE)
    try:
        pdf.set_font(pdf._font_bold, "B", pdf._size_section)
    except Exception:
        pdf.set_font("Helvetica", "B", 11)
    pdf.multi_cell(0, 8, f"  {title}", fill=True, align="L")
    pdf.set_x(pdf.l_margin)
    pdf.set_text_color(*_DARK)
    pdf.ln(2)


def _render_status_banner(pdf: _PDFReport, structured) -> None:  # type: ignore[no-untyped-def]
    """Render colored overall-status banner + short explanation."""
    status = structured.report_summary.overall_status.value
    fg, bg, label = _STATUS_COLORS.get(status, (_BLUE, _SKYTINT, status.replace("_", " ").title()))
    confidence = structured.report_summary.confidence_level.value.capitalize()
    explanation = structured.report_summary.short_explanation

    pdf.ln(4)
    pdf.set_fill_color(*bg)
    pdf.set_draw_color(*fg)
    pdf.set_line_width(0.6)

    # Status label line
    pdf.set_text_color(*fg)
    try:
        pdf.set_font(pdf._font_bold, "B", 13)
    except Exception:
        pdf.set_font("Helvetica", "B", 13)
    pdf.multi_cell(0, 9, f"  {label}  \u2014  {confidence} confidence", fill=True, align="L")
    pdf.set_x(pdf.l_margin)

    # Explanation line(s)
    pdf.set_text_color(*_DARK)
    try:
        pdf.set_font(pdf._font, "", pdf._size_body)
    except Exception:
        pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 6, f"  {explanation}", fill=True, align="L")
    pdf.set_x(pdf.l_margin)
    pdf.set_line_width(0.2)
    pdf.ln(3)


def _render_patient_context(pdf: _PDFReport, structured) -> None:  # type: ignore[no-untyped-def]
    """Render patient context row (gender / age group)."""
    ctx = structured.patient_context
    gender = ctx.gender_inferred.value.capitalize()
    age_group = ctx.age_group_inferred.value.replace("_", " ").capitalize()
    if gender == "Unknown" and age_group == "Unknown":
        return

    _section_header(pdf, "Patient Profile")
    try:
        pdf.set_font(pdf._font, "", pdf._size_body)
    except Exception:
        pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*_DARK)
    row = [f"Gender: {gender}", f"Age Group: {age_group}"]
    pdf.multi_cell(0, 6, "  " + "    \u2022    ".join(row), align="L")
    pdf.set_x(pdf.l_margin)


def _render_biomarker_table(pdf: _PDFReport, biomarkers: list) -> None:  # type: ignore[no-untyped-def]
    """Render a formatted biomarker table."""
    if not biomarkers:
        return

    _section_header(pdf, "Biomarker Analysis")

    cw = pdf.w - 2 * _MARGIN
    # Column widths: Marker 38%, Value 15%, Reference 22%, Status 12%, Note 13%
    col_w = [cw * 0.32, cw * 0.14, cw * 0.20, cw * 0.13, cw * 0.21]
    headers = ["Marker", "Value", "Ref. Range", "Status", "Significance"]

    # Header row
    pdf.set_fill_color(*_BGBLUE)
    pdf.set_text_color(*_DARK)
    try:
        pdf.set_font(pdf._font_bold, "B", 8)
    except Exception:
        pdf.set_font("Helvetica", "B", 8)

    for i, h in enumerate(headers):
        pdf.cell(col_w[i], 7, h, border=1, fill=True, align="C")
    pdf.ln()

    # Data rows
    try:
        pdf.set_font(pdf._font, "", 8)
    except Exception:
        pdf.set_font("Helvetica", "", 8)

    status_fg = {
        "normal": _GREEN,
        "high": _ORANGE,
        "low": _BLUE,
        "borderline": _AMBERTEXT,
    }

    for bm in biomarkers:
        status_val = bm.status.value
        fg = status_fg.get(status_val, _DARK)
        label = _BIOMARKER_STATUS_LABEL.get(status_val, status_val.capitalize())

        # Truncate long strings for table fit
        sig = bm.clinical_significance
        if len(sig) > 55:
            sig = sig[:52] + "..."

        pdf.set_text_color(*_DARK)
        pdf.cell(col_w[0], 6, _trunc(bm.marker_name, 28), border=1)
        pdf.cell(col_w[1], 6, _trunc(bm.measured_value, 12), border=1, align="C")
        pdf.cell(col_w[2], 6, _trunc(bm.reference_range, 18), border=1, align="C")
        pdf.set_text_color(*fg)
        pdf.cell(col_w[3], 6, label, border=1, align="C")
        pdf.set_text_color(*_MUTED)
        pdf.cell(col_w[4], 6, sig, border=1)
        pdf.set_text_color(*_DARK)
        pdf.ln()

    pdf.set_x(pdf.l_margin)
    pdf.ln(2)


def _render_abnormal_findings(pdf: _PDFReport, findings: list) -> None:  # type: ignore[no-untyped-def]
    """Render abnormal findings as boxed entries."""
    if not findings:
        return

    _section_header(pdf, "Abnormal Findings")

    for finding in findings:
        try:
            pdf.set_font(pdf._font_bold, "B", pdf._size_body)
        except Exception:
            pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(*_RED)
        pdf.multi_cell(0, 6, f"  {finding.marker}: {finding.issue}", align="L")
        pdf.set_x(pdf.l_margin)

        try:
            pdf.set_font(pdf._font, "", pdf._size_body - 1)
        except Exception:
            pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(*_DARK)

        if finding.possible_meanings:
            pdf.multi_cell(0, 5, "  Possible meanings:", align="L")
            pdf.set_x(pdf.l_margin)
            for m in finding.possible_meanings:
                pdf.multi_cell(0, 5, f"    \u2022 {m}", align="L")
                pdf.set_x(pdf.l_margin)

        if finding.recommended_followup_tests:
            pdf.set_text_color(*_MUTED)
            tests = ", ".join(finding.recommended_followup_tests)
            pdf.multi_cell(0, 5, f"  Follow-up tests: {tests}", align="L")
            pdf.set_x(pdf.l_margin)
            pdf.set_text_color(*_DARK)

        pdf.ln(2)


def _render_health_recommendations(pdf: _PDFReport, recs: list) -> None:  # type: ignore[no-untyped-def]
    """Render health recommendations as a bullet list."""
    if not recs:
        return

    _section_header(pdf, "Health Recommendations")
    try:
        pdf.set_font(pdf._font, "", pdf._size_body)
    except Exception:
        pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*_DARK)

    for rec in recs:
        pdf.multi_cell(0, 6, f"  \u2022  {rec}", align="L")
        pdf.set_x(pdf.l_margin)
    pdf.ln(1)


def _render_specialty_recommendations(pdf: _PDFReport, specialties: list) -> None:  # type: ignore[no-untyped-def]
    """Render recommended specialties with reasons."""
    if not specialties:
        return

    _section_header(pdf, "Recommended Medical Consultation")
    try:
        pdf.set_font(pdf._font, "", pdf._size_body)
    except Exception:
        pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*_DARK)

    for sp in specialties:
        try:
            pdf.set_font(pdf._font_bold, "B", pdf._size_body)
        except Exception:
            pdf.set_font("Helvetica", "B", 10)
        pdf.multi_cell(0, 6, f"  \u27a4  {sp.specialty}", align="L")
        pdf.set_x(pdf.l_margin)
        try:
            pdf.set_font(pdf._font, "", pdf._size_body - 1)
        except Exception:
            pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(*_MUTED)
        pdf.multi_cell(0, 5, f"     {sp.reason}", align="L")
        pdf.set_x(pdf.l_margin)
        pdf.set_text_color(*_DARK)
        pdf.ln(1)


def _render_structured_en(pdf: _PDFReport, structured) -> None:  # type: ignore[no-untyped-def]
    """Master renderer: writes all structured sections in order."""
    _render_status_banner(pdf, structured)
    _render_patient_context(pdf, structured)
    _render_biomarker_table(pdf, structured.biomarker_analysis)
    _render_abnormal_findings(pdf, structured.abnormal_findings)
    _render_health_recommendations(pdf, structured.health_recommendations)
    _render_specialty_recommendations(pdf, structured.recommended_specialties)


def _trunc(text: str, max_len: int) -> str:
    """Truncate text to max_len characters."""
    return text if len(text) <= max_len else text[:max_len - 1] + "\u2026"
