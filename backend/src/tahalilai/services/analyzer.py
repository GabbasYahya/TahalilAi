"""Medical lab results analysis via Gemini (primary) with local LLM fallback.

Uses Google Gemini API for analysis when available; falls back to the
quantised Ministral model via llama.cpp CLI when offline or the API fails.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys

from tahalilai.config import get_settings

# Graceful handling when SDK is not installed (e.g. minimal test environments)
try:
    from google import genai
    from google.genai import types as genai_types

    _GEMINI_AVAILABLE = True
except ImportError:
    _GEMINI_AVAILABLE = False

_SYSTEM_PROMPT = """\
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


def analyze_text(
    ocr_text: str,
    age: str | None = None,
    gender: str | None = None,
) -> str:
    """Analyse OCR-extracted lab results.

    Tries Google Gemini first; falls back to the local LLM when the API key
    is absent or the request fails for any reason (network error, quota, etc.).

    Args:
        ocr_text: Raw text obtained from OCR.
        age: Optional patient age for contextual analysis.
        gender: Optional patient gender for contextual analysis.

    Returns:
        English analysis text, or an error string starting with ``Error``.
    """
    settings = get_settings()

    if _GEMINI_AVAILABLE and settings.gemini_api_key:
        print("Attempting analysis via Gemini API...", file=sys.stderr)
        result = _analyze_with_gemini(ocr_text, age, gender, settings)
        if not result.startswith("Error"):
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
) -> str:
    """Call the Gemini API and return the analysis text."""
    try:
        print("Sending analysis request to Gemini API...", file=sys.stderr)

        patient_ctx = f"Patient: {age}yrs, {gender}.\n" if age and gender else ""
        user_input = f"{patient_ctx}RESULTS:\n{ocr_text}\n\nExplain these results now."

        client = genai.Client(api_key=settings.gemini_api_key)
        response = client.models.generate_content(
            model=settings.gemini_model,
            contents=user_input,
            config=genai_types.GenerateContentConfig(
                system_instruction=_SYSTEM_PROMPT,
                temperature=0.3,
                top_p=0.95,
                top_k=40,
                max_output_tokens=8192,
            ),
        )

        text = response.text.strip()
        if not text or len(text) < 50:
            return "Error: Gemini returned empty output."

        print(f"Gemini analysis complete ({len(text)} chars)", file=sys.stderr)
        return text

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
) -> str:
    """Run the local Ministral model via llama-cli."""
    print("Running Medical AI Analysis (local model)...", file=sys.stderr)

    patient_ctx = f"Patient: {age}yrs, {gender}.\n" if age and gender else ""
    user_input = f"{patient_ctx}RESULTS:\n{ocr_text}\n\nExplain these results now."
    full_prompt = f"[SYSTEM_PROMPT] {_SYSTEM_PROMPT} [/SYSTEM_PROMPT][INST] {user_input} [/INST]"

    cmd = [
        str(settings.llama_cli_path),
        "-m",
        str(settings.model_path),
        "-p",
        full_prompt,
        "-n",
        "2048",
        "-c",
        "6144",
        "--temp",
        "0.3",
        "--no-display-prompt",
        "-t",
        "4",
    ]

    try:
        timeout = settings.model_timeout
        print(f"Starting inference (timeout={timeout}s)...", file=sys.stderr)

        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"

        # On Windows, isolate the child process from the parent's console
        # group so that llama-cli's console events (CTRL_C_EVENT on exit)
        # do not propagate to uvicorn and crash the server.
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

        result = _clean_llm_output(stdout)
        if not result or len(result) < 50:
            return "Error: Model returned empty output."
        return result

    except Exception as exc:
        return f"Error executing AI model: {exc}"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _clean_llm_output(raw: str) -> str:
    """Strip llama-cli noise (banners, speed stats, prompt echoes)."""
    text = raw

    # ── 1. Conversation-mode banner ─────────────────────────────────────
    # --single-turn / conversation mode prints an "available commands" block
    text = re.sub(
        r"available commands:.*?(?=\[SYSTEM_PROMPT\]|\[INST\]|\*\*Summary|$)",
        "",
        text,
        flags=re.DOTALL,
    )
    # Strip "> " prefixes the conversation mode adds
    text = re.sub(r"^\s*>\s*", "", text, flags=re.MULTILINE)

    # ── 2. Full prompt echo removal ────────────────────────────────────
    # If the prompt was echoed, strip everything up to [/INST]
    idx = text.rfind("[/INST]")
    if idx != -1:
        text = text[idx + len("[/INST]") :]

    # Strip complete [SYSTEM_PROMPT]...[/SYSTEM_PROMPT] blocks
    text = re.sub(
        r"\[SYSTEM_PROMPT\].*?\[/SYSTEM_PROMPT\]",
        "",
        text,
        flags=re.DOTALL,
    )
    # Strip complete [INST]...[/INST] blocks
    text = re.sub(r"\[INST\].*?\[/INST\]", "", text, flags=re.DOTALL)

    # ── 2b. Prompt template echo without markers ──────────────────────
    # --no-display-prompt strips marker tokens but model may still
    # regenerate the prompt template as part of its output.
    # The model sometimes abbreviates (e.g. "ONLY ... (truncated)")
    # so we match structurally: TASK → RULES → double-newline boundary
    m = re.search(
        r"TASK:\s*Explain the provided lab results.*?RULES:.*?\n\n",
        text,
        re.DOTALL,
    )
    if m:
        text = text[m.end() :]

    # ── 3. Partial system prompt leak (no closing markers) ─────────────
    # Model may regenerate the system prompt without proper closing tags
    if "[SYSTEM_PROMPT]" in text:
        # Try finding known end of system prompt content
        m = re.search(
            r"\[SYSTEM_PROMPT\]\s*You are an accurate Medical Results Explainer"
            r".*?ONLY output English\.\s*",
            text,
            re.DOTALL,
        )
        if m:
            text = text[: m.start()] + text[m.end() :]
        else:
            # Nuclear: remove from [SYSTEM_PROMPT] to next double-newline
            text = re.sub(
                r"\[SYSTEM_PROMPT\].*?(?=\n\n|$)", "", text, flags=re.DOTALL
            )

    # If the system prompt leaked without any markers at all
    if "You are an accurate Medical Results Explainer" in text:
        parts = text.split("Explain these results now.")
        if len(parts) > 1:
            text = parts[-1]
        else:
            text = re.sub(
                r"You are an accurate Medical Results Explainer.*?ONLY output English\.\s*",
                "",
                text,
                flags=re.DOTALL,
            )

    # ── 4. Clean up remaining template markers ─────────────────────────
    text = re.sub(r"\[/?(?:SYSTEM_PROMPT|INST)\]", "", text)

    # Also try the English explanation marker
    if "--- ENGLISH EXPLANATION ---" in text:
        parts = text.split("--- ENGLISH EXPLANATION ---")
        text = "--- ENGLISH EXPLANATION ---" + parts[-1]

    # ── 5. llama-cli metadata lines ────────────────────────────────────
    # Speed stats
    text = re.sub(
        r"\[\s*Prompt:\s*[\d.]+\s*t/s\s*\|\s*Generation:\s*[\d.]+\s*t/s\s*\]",
        "",
        text,
    )
    text = re.sub(r"Exiting\.\.\.\s*$", "", text)

    # ASCII art / braille spinners
    text = re.sub(r"[░▒▓█▄▀▐▌▖▗▘▙▚▛▜▝▞▟]+", "", text)
    text = re.sub(r"[\u2800-\u28FF]+", "", text)
    text = re.sub(r"Loading model[.\s]*", "", text)

    # Build/model info lines
    text = re.sub(r"^build\s*:.*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"^model\s*:.*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"^modalities\s*:.*$", "", text, flags=re.MULTILINE)

    # Leaked system prompt (legacy pattern)
    text = re.sub(
        r"You are a helpful medical results assistant.*?(?=--- ENGLISH)",
        "",
        text,
        flags=re.DOTALL,
    )

    # ── 6. Collapse excessive blank lines ──────────────────────────────
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()
