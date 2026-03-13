"""Render a StructuredAnalysis as Markdown for backward-compatible consumers."""

from __future__ import annotations

from tahalilai.schemas import StructuredAnalysis

_STATUS_LABEL = {
    "normal": "All Normal",
    "mostly_normal": "Mostly Normal",
    "abnormal": "Abnormal Results",
    "critical": "Critical Values Detected",
}


def render_markdown(analysis: StructuredAnalysis) -> str:
    """Convert a *StructuredAnalysis* to readable Markdown.

    If the analysis was produced by the legacy local-LLM fallback, its raw
    Markdown is stored in ``system_feedback`` as ``LEGACY_MARKDOWN:…`` and
    is returned verbatim.
    """
    # Legacy passthrough (local LLM couldn't produce JSON)
    for fb in analysis.system_feedback:
        if fb.startswith("LEGACY_MARKDOWN:"):
            return fb[len("LEGACY_MARKDOWN:"):]

    lines: list[str] = []

    # Summary
    status_label = _STATUS_LABEL.get(
        analysis.report_summary.overall_status.value, "Unknown"
    )
    lines.append(f"**Summary** — {status_label}")
    lines.append("")
    lines.append(analysis.report_summary.short_explanation)
    lines.append("")

    # Detailed Analysis (biomarkers)
    if analysis.biomarker_analysis:
        lines.append("**Detailed Analysis**")
        lines.append("")
        for bm in analysis.biomarker_analysis:
            status = bm.status.value.capitalize()
            lines.append(f"- **{bm.marker_name}**: {bm.measured_value} ({status})")
            lines.append(f"  *Reference Range*: {bm.reference_range}")
            lines.append(f"  *Meaning*: {bm.clinical_significance}")
        lines.append("")

    # Abnormal Findings
    if analysis.abnormal_findings:
        lines.append("**Abnormal Findings**")
        lines.append("")
        for af in analysis.abnormal_findings:
            lines.append(f"- **{af.marker}** ({af.issue})")
            if af.possible_meanings:
                lines.append(f"  Possible meanings: {', '.join(af.possible_meanings)}")
            if af.recommended_followup_tests:
                lines.append(
                    f"  Recommended follow-up: {', '.join(af.recommended_followup_tests)}"
                )
        lines.append("")

    # Health Recommendations
    if analysis.health_recommendations:
        lines.append("**Recommendations**")
        lines.append("")
        for rec in analysis.health_recommendations:
            lines.append(f"- {rec}")
        lines.append("")

    # Missing Information
    if analysis.missing_information.additional_questions:
        lines.append("**Additional Information Needed**")
        lines.append("")
        for q in analysis.missing_information.additional_questions:
            lines.append(f"- {q}")

    return "\n".join(lines)
