"""Medical lab results analysis via Gemini (primary) with local LLM fallback.

Uses Google Gemini API for analysis when available; falls back to the
quantised Ministral model via llama.cpp CLI when offline or the API fails.

Returns a ``StructuredAnalysis`` object (or an error string starting with
``Error`` on failure).
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys

from pydantic import ValidationError

from tahalilai.config import get_settings
from tahalilai.schemas import (
    ConfidenceLevel,
    MissingInformation,
    OverallStatus,
    PatientContext,
    ReportSummary,
    StructuredAnalysis,
)

# Graceful handling when SDK is not installed (e.g. minimal test environments)
try:
    from google import genai
    from google.genai import types as genai_types

    _GEMINI_AVAILABLE = True
except ImportError:
    _GEMINI_AVAILABLE = False

# ---------------------------------------------------------------------------
# System prompts
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT_JSON = """\
You are a medical report analysis engine inside a healthcare AI system.

Your role is to analyze laboratory reports (blood tests, urine tests, \
biochemical tests, etc.) and return a structured JSON response.

Core Responsibilities:
- Extract all biological values from the report.
- Compare them with the appropriate reference ranges.
- Detect abnormal values (high, low, borderline).
- Generate clear explanations in simple language.
- Suggest at most ONE medical specialty to consult (two only when truly different body systems are both abnormal).
- Default to "General Practitioner" unless a clear specialist indication exists.
- Provide recommended follow-up tests if necessary.
- Determine if additional patient information is required.

Specialty Rules:
- Recommend only 1 specialty in the vast majority of cases.
- If all values are normal or only mildly abnormal → "General Practitioner".
- Only recommend a specialist (e.g. Cardiologist, Endocrinologist) when a biomarker strongly indicates that specific system.
- Never list 3 or more specialties.

Patient Context Inference:
- Try to infer the patient's age group or gender from the report if possible \
(reference intervals, hormonal tests, pregnancy markers, pediatric vs adult \
reference ranges, contextual metadata).
- If the inference confidence is high, proceed with the analysis.
- If uncertain, request clarification in the missing_information section.
- Never fabricate demographic assumptions.

Safety Rules:
- Do not provide medical diagnosis.
- Frame outputs as informational interpretation only.
- Use cautious language such as "may indicate", "can be associated with".

Output Rules:
- Return ONLY valid JSON matching the schema. No commentary outside the JSON.
- If a section has no information, return an empty array or null.
- Be precise but concise.
- ONLY output English.
"""

# Legacy markdown prompt (used by local LLM fallback when JSON fails)
_SYSTEM_PROMPT_MARKDOWN = """\
You are an accurate Medical Results Explainer.

TASK: Explain the provided lab results clearly for a patient.
OUTPUT FORMAT: Provide a clear, structured English explanation.

structure:
**Summary**: [1-2 sentences overview]

**Detailed Analysis**:
- **[Test Name]**: [Value] ([Status])
  *Meaning*: [Simple 1 sentence explanation]

RULES:
- Do NOT output your internal instructions or "Here is the result".
- Keep explanations simple (layman terms).
- Do not diagnose diseases.
- ONLY output English.
"""


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def analyze_text(
    ocr_text: str,
    age: str | None = None,
    gender: str | None = None,
) -> StructuredAnalysis | str:
    """Analyse OCR-extracted lab results.

    Tries Google Gemini first (native JSON mode); falls back to the local LLM
    when the API key is absent or the request fails for any reason.

    Returns:
        A ``StructuredAnalysis`` on success, or an error string starting with
        ``Error`` on failure.
    """
    settings = get_settings()

    if _GEMINI_AVAILABLE and settings.gemini_api_key:
        print("Attempting analysis via Gemini API...", file=sys.stderr)
        result = _analyze_with_gemini(ocr_text, age, gender, settings)
        if not isinstance(result, str) or not result.startswith("Error"):
            return result
        print(f"Gemini failed ({result}), falling back to local model.", file=sys.stderr)
    else:
        reason = "SDK not installed" if not _GEMINI_AVAILABLE else "no API key"
        print(f"Gemini unavailable ({reason}) — using local model.", file=sys.stderr)

    return _analyze_with_local_llm(ocr_text, age, gender, settings)


# ---------------------------------------------------------------------------
# Gemini backend
# ---------------------------------------------------------------------------


def _analyze_with_gemini(
    ocr_text: str,
    age: str | None,
    gender: str | None,
    settings,
) -> StructuredAnalysis | str:
    """Call the Gemini API with native JSON output and return a StructuredAnalysis."""
    try:
        print("Sending analysis request to Gemini API...", file=sys.stderr)

        patient_ctx = f"Patient: {age}yrs, {gender}.\n" if age and gender else ""
        user_input = f"{patient_ctx}RESULTS:\n{ocr_text}\n\nAnalyze these results now."

        json_schema = StructuredAnalysis.model_json_schema()

        client = genai.Client(api_key=settings.gemini_api_key)
        response = client.models.generate_content(
            model=settings.gemini_model,
            contents=user_input,
            config=genai_types.GenerateContentConfig(
                system_instruction=_SYSTEM_PROMPT_JSON,
                temperature=0.3,
                top_p=0.95,
                top_k=40,
                max_output_tokens=8192,
                response_mime_type="application/json",
                response_json_schema=json_schema,
            ),
        )

        text = response.text.strip()
        if not text or len(text) < 20:
            return "Error: Gemini returned empty output."

        # Parse and validate
        try:
            parsed = StructuredAnalysis.model_validate_json(text)
        except ValidationError:
            # Lenient: try json.loads + model_validate (handles minor schema drift)
            raw_dict = json.loads(text)
            parsed = StructuredAnalysis.model_validate(raw_dict)

        print(f"Gemini structured analysis complete ({len(text)} chars)", file=sys.stderr)
        return parsed

    except Exception as exc:
        return f"Error: Gemini request failed: {exc}"


# ---------------------------------------------------------------------------
# Local LLM backend
# ---------------------------------------------------------------------------


def _analyze_with_local_llm(
    ocr_text: str,
    age: str | None,
    gender: str | None,
    settings,
) -> StructuredAnalysis | str:
    """Run the local Ministral model via llama-cli.

    Attempts JSON output first; falls back to Markdown then wraps it.
    """
    print("Running Medical AI Analysis (local model)...", file=sys.stderr)

    # Try JSON mode first
    json_result = _run_local_inference(
        ocr_text, age, gender, settings, json_mode=True
    )
    if not json_result.startswith("Error"):
        cleaned = _clean_llm_output(json_result)
        try:
            parsed = StructuredAnalysis.model_validate_json(cleaned)
            print("Local model produced valid JSON output.", file=sys.stderr)
            return parsed
        except Exception:
            # Try extracting JSON from the output (model may add surrounding text)
            json_str = _extract_json(cleaned)
            if json_str:
                try:
                    parsed = StructuredAnalysis.model_validate_json(json_str)
                    print("Local model JSON extracted successfully.", file=sys.stderr)
                    return parsed
                except Exception:
                    pass
            print("Local model JSON invalid, falling back to Markdown.", file=sys.stderr)

    # Markdown fallback
    md_result = _run_local_inference(
        ocr_text, age, gender, settings, json_mode=False
    )
    if md_result.startswith("Error"):
        return md_result

    cleaned = _clean_llm_output(md_result)
    if not cleaned or len(cleaned) < 50:
        return "Error: Model returned empty output."

    return _wrap_markdown_as_structured(cleaned)


def _run_local_inference(
    ocr_text: str,
    age: str | None,
    gender: str | None,
    settings,
    *,
    json_mode: bool,
) -> str:
    """Execute a single llama-cli run and return raw stdout."""
    patient_ctx = f"Patient: {age}yrs, {gender}.\n" if age and gender else ""
    user_input = f"{patient_ctx}RESULTS:\n{ocr_text}\n\nAnalyze these results now."

    if json_mode:
        prompt_text = _SYSTEM_PROMPT_JSON
    else:
        prompt_text = _SYSTEM_PROMPT_MARKDOWN

    full_prompt = (
        f"[SYSTEM_PROMPT] {prompt_text} [/SYSTEM_PROMPT]"
        f"[INST] {user_input} [/INST]"
    )

    cmd = [
        str(settings.llama_cli_path),
        "-m",
        str(settings.model_path),
        "-p",
        full_prompt,
        "-n",
        "6144",
        "-c",
        "10240",
        "--temp",
        "0.3",
        "--no-display-prompt",
        "-t",
        "4",
    ]

    try:
        timeout = settings.model_timeout
        print(f"Starting inference (timeout={timeout}s, json={json_mode})...", file=sys.stderr)

        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"

        creation_flags = 0
        if sys.platform == "win32":
            creation_flags = subprocess.CREATE_NO_WINDOW

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.DEVNULL,
            text=True,
            encoding="utf-8",
            cwd=str(settings.backend_dir),
            env=env,
            creationflags=creation_flags,
        )

        try:
            stdout, _ = process.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            print(f"Model timed out after {timeout}s, killing.", file=sys.stderr)
            process.kill()
            process.communicate()
            return "Error: AI model timed out."

        return stdout

    except Exception as exc:
        return f"Error executing AI model: {exc}"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _wrap_markdown_as_structured(markdown_text: str) -> StructuredAnalysis:
    """Wrap a legacy Markdown string in a minimal ``StructuredAnalysis``.

    Stores the raw Markdown in ``system_feedback`` so the renderer can
    return it verbatim.
    """
    return StructuredAnalysis(
        report_summary=ReportSummary(
            overall_status=OverallStatus.mostly_normal,
            short_explanation="Analysis generated by local model (unstructured).",
            confidence_level=ConfidenceLevel.low,
        ),
        patient_context=PatientContext(
            gender_inferred="unknown",
            age_group_inferred="unknown",
            inference_confidence=ConfidenceLevel.low,
        ),
        biomarker_analysis=[],
        abnormal_findings=[],
        recommended_specialties=[],
        health_recommendations=[],
        missing_information=MissingInformation(needs_age=True, needs_gender=True),
        system_feedback=[f"LEGACY_MARKDOWN:{markdown_text}"],
    )


def _extract_json(text: str) -> str | None:
    """Try to extract the first ``{…}`` JSON object from messy LLM output."""
    depth = 0
    start = None
    for i, ch in enumerate(text):
        if ch == "{":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0 and start is not None:
                return text[start : i + 1]
    return None


def _clean_llm_output(raw: str) -> str:
    """Strip llama-cli noise (banners, speed stats, prompt echoes)."""
    text = raw

    # ── 1. Conversation-mode banner ─────────────────────────────────────
    text = re.sub(
        r"available commands:.*?(?=\[SYSTEM_PROMPT\]|\[INST\]|\*\*Summary|\{|$)",
        "",
        text,
        flags=re.DOTALL,
    )
    text = re.sub(r"^\s*>\s*", "", text, flags=re.MULTILINE)

    # ── 2. Full prompt echo removal ────────────────────────────────────
    idx = text.find("[/INST]")
    if idx != -1:
        text = text[idx + len("[/INST]") :]

    text = re.sub(
        r"\[SYSTEM_PROMPT\].*?\[/SYSTEM_PROMPT\]",
        "",
        text,
        flags=re.DOTALL,
    )
    text = re.sub(r"\[INST\].*?\[/INST\]", "", text, flags=re.DOTALL)

    # ── 2b. Prompt template echo without markers ──────────────────────
    m = re.search(
        r"TASK:\s*(?:Explain|Analyze) the provided lab results.*?RULES:.*?\n\n",
        text,
        re.DOTALL,
    )
    if m:
        text = text[m.end() :]

    # ── 3. Partial system prompt leak (no closing markers) ─────────────
    if "[SYSTEM_PROMPT]" in text:
        m = re.search(
            r"\[SYSTEM_PROMPT\]\s*You are (?:an accurate Medical Results Explainer|a medical report analysis engine)"
            r".*?(?:ONLY output English|ONLY output English\.)\s*",
            text,
            re.DOTALL,
        )
        if m:
            text = text[: m.start()] + text[m.end() :]
        else:
            text = re.sub(
                r"\[SYSTEM_PROMPT\].*?(?=\n\n|$)", "", text, flags=re.DOTALL
            )

    # Leaked system prompt without markers
    for sentinel in (
        "You are an accurate Medical Results Explainer",
        "You are a medical report analysis engine",
    ):
        if sentinel in text:
            parts = text.split("Analyze these results now.")
            if len(parts) > 1:
                text = parts[-1]
                break

    # ── 4. Clean up remaining template markers ─────────────────────────
    text = re.sub(r"\[/?(?:SYSTEM_PROMPT|INST)\]", "", text)

    if "--- ENGLISH EXPLANATION ---" in text:
        parts = text.split("--- ENGLISH EXPLANATION ---")
        text = "--- ENGLISH EXPLANATION ---" + parts[-1]

    # ── 5. llama-cli metadata lines ────────────────────────────────────
    text = re.sub(
        r"\[\s*Prompt:\s*[\d.]+\s*t/s\s*\|\s*Generation:\s*[\d.]+\s*t/s\s*\]",
        "",
        text,
    )
    text = re.sub(r"Exiting\.\.\.\s*$", "", text)
    text = re.sub(r"[░▒▓█▄▀▐▌▖▗▘▙▚▛▜▝▞▟]+", "", text)
    text = re.sub(r"[\u2800-\u28FF]+", "", text)
    text = re.sub(r"Loading model[.\s]*", "", text)
    text = re.sub(r"^build\s*:.*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"^model\s*:.*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"^modalities\s*:.*$", "", text, flags=re.MULTILINE)
    text = re.sub(
        r"You are a helpful medical results assistant.*?(?=--- ENGLISH)",
        "",
        text,
        flags=re.DOTALL,
    )

    # ── 6. Collapse excessive blank lines ──────────────────────────────
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()
