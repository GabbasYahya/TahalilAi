"""Post-analysis follow-up Q&A service.

Allows patients to ask questions about their lab results after the
initial analysis has been completed. Uses Gemini as primary and the
local Ministral model as fallback, exactly like the analyzer.
"""

from __future__ import annotations

import os
import subprocess
import sys

from tahalilai.config import get_settings
from tahalilai.services.analyzer import _GEMINI_AVAILABLE

try:
    from google import genai
    from google.genai import types as genai_types
except ImportError:
    pass  # _GEMINI_AVAILABLE handles this

_CHAT_SYSTEM_PROMPT = """\
You are a friendly Medical Lab Results Assistant helping a patient
understand their lab report. The patient has already received an initial
AI-generated analysis. Your role is to answer their follow-up questions.

RULES:
- Use plain, non-technical language appropriate for a patient.
- Be concise: answer in 150 words or fewer unless more detail is needed.
- Do NOT diagnose diseases, prescribe medications, or recommend treatments.
- If a question is outside the scope of the provided lab results, say so politely.
- Never repeat the entire initial analysis; reference specific parts when relevant.
- Be reassuring, clear, and professional.
"""

# Maximum number of previous messages kept in context (10 turns = 20 messages)
_MAX_HISTORY = 20


def answer_question(
    ocr_text: str,
    initial_analysis: str,
    history: list[dict[str, str]],
    question: str,
) -> str:
    """Answer a patient's follow-up question about their lab results.

    Tries Gemini first; falls back to the local LLM on any failure.

    Args:
        ocr_text: Raw OCR text of the original lab report.
        initial_analysis: The AI-generated analysis already shown to the patient.
        history: Previous messages [{"role": "user"/"assistant", "content": "..."}].
        question: The patient's new question.

    Returns:
        The assistant's answer, or an error string starting with ``Error``.
    """
    settings = get_settings()
    trimmed_history = history[-_MAX_HISTORY:]

    if _GEMINI_AVAILABLE and settings.gemini_api_key:
        result = _chat_with_gemini(
            ocr_text, initial_analysis, trimmed_history, question, settings
        )
        if not result.startswith("Error"):
            return result
        print(f"Gemini chat failed ({result}), falling back to local model.", file=sys.stderr)
    else:
        reason = "SDK not installed" if not _GEMINI_AVAILABLE else "no API key"
        print(f"Gemini unavailable ({reason}) — using local model for chat.", file=sys.stderr)

    return _chat_with_local_llm(
        ocr_text, initial_analysis, trimmed_history, question, settings
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _build_context_prompt(
    ocr_text: str,
    initial_analysis: str,
    history: list[dict[str, str]],
    question: str,
) -> str:
    """Format OCR text, analysis, history, and question into a single prompt."""
    conversation = ""
    for msg in history:
        label = "Patient" if msg["role"] == "user" else "Assistant"
        conversation += f"{label}: {msg['content']}\n\n"
    conversation += f"Patient: {question}"

    return (
        f"ORIGINAL LAB RESULTS:\n{ocr_text}\n\n"
        f"INITIAL ANALYSIS:\n{initial_analysis}\n\n"
        f"CONVERSATION:\n{conversation}\n\n"
        f"Provide a clear, concise answer to the Patient's latest question."
    )


# ---------------------------------------------------------------------------
# Gemini backend
# ---------------------------------------------------------------------------


def _chat_with_gemini(
    ocr_text: str,
    initial_analysis: str,
    history: list[dict[str, str]],
    question: str,
    settings,
) -> str:
    """Send the follow-up question to Gemini with full conversation context."""
    try:
        prompt = _build_context_prompt(ocr_text, initial_analysis, history, question)

        client = genai.Client(api_key=settings.gemini_api_key)
        response = client.models.generate_content(
            model=settings.gemini_model,
            contents=prompt,
            config=genai_types.GenerateContentConfig(
                system_instruction=_CHAT_SYSTEM_PROMPT,
                temperature=0.4,
                top_p=0.95,
                max_output_tokens=1024,
            ),
        )

        text = response.text.strip()
        if not text or len(text) < 10:
            return "Error: Gemini returned an empty response."

        return text

    except Exception as exc:
        return f"Error: Gemini chat failed: {exc}"


# ---------------------------------------------------------------------------
# Local LLM backend
# ---------------------------------------------------------------------------


def _chat_with_local_llm(
    ocr_text: str,
    initial_analysis: str,
    history: list[dict[str, str]],
    question: str,
    settings,
) -> str:
    """Run the follow-up question through the local Ministral model."""
    print("Running follow-up Q&A via local model...", file=sys.stderr)

    # Truncate context to avoid exceeding the 4096-token context window
    ocr_short = ocr_text[:800] if len(ocr_text) > 800 else ocr_text
    analysis_short = (
        initial_analysis[:1500] if len(initial_analysis) > 1500 else initial_analysis
    )

    prompt_body = _build_context_prompt(ocr_short, analysis_short, history, question)
    full_prompt = (
        f"[SYSTEM_PROMPT] {_CHAT_SYSTEM_PROMPT} [/SYSTEM_PROMPT]"
        f"[INST] {prompt_body} [/INST]"
    )

    cmd = [
        str(settings.llama_cli_path),
        "-m", str(settings.model_path),
        "-p", full_prompt,
        "-n", "512",
        "-c", "4096",
        "--temp", "0.4",
        "--no-display-prompt",
        "-t", "4",
    ]

    try:
        # Cap chat timeout at 2 minutes so the user is not left waiting
        timeout = min(settings.model_timeout, 120)

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
            process.kill()
            process.communicate()
            return "Error: Local model timed out answering the question."

        # Strip the prompt echo — keep only what comes after [/INST]
        idx = stdout.rfind("[/INST]")
        text = stdout[idx + len("[/INST]"):].strip() if idx != -1 else stdout.strip()

        if not text or len(text) < 5:
            return "Error: Local model returned an empty response."

        return text

    except Exception as exc:
        return f"Error: Local model failed: {exc}"
