"""Medical report translation via Google Gemini API.

Uses the modern ``google.genai`` SDK exclusively.  The deprecated
``google.generativeai`` package is **not** supported — install
``google-genai`` instead.
"""

from __future__ import annotations

import sys

from tahalilai.config import get_settings

# Graceful handling when SDK is not installed (e.g. in test environments)
try:
    from google import genai
    from google.genai import types as genai_types

    _GEMINI_AVAILABLE = True
except ImportError:
    _GEMINI_AVAILABLE = False

_SYSTEM_INSTRUCTION = """\
You are an expert medical translator specializing in English to Arabic translation.
Your task is to translate medical laboratory reports with the highest accuracy.

CRITICAL RULES:
1. Preserve ALL formatting (markdown bold **, bullet points, line breaks)
2. Use standard medical Arabic terminology
3. Maintain the exact structure and sections
4. Translate section headers accurately:
   - "Summary" → "الملخص"
   - "Detailed Analysis" → "التحليل المفصل"
   - "Recommendations" → "التوصيات"
5. Keep numerical values and units EXACTLY as they appear
6. Do NOT add explanations, comments, or extra text
7. Output ONLY the translated Arabic text
"""


def translate_medical_report(text: str) -> str:
    """Translate an English medical report to Arabic using Gemini.

    Args:
        text: English medical report text.

    Returns:
        Arabic translation, or an error string prefixed with ``Error:``.
    """
    if not _GEMINI_AVAILABLE:
        return "Error: google-genai SDK not installed. Run: pip install google-genai"

    settings = get_settings()
    if not settings.gemini_api_key:
        return "Error: GEMINI_API_KEY not set in .env file"

    try:
        print("Sending translation request to Gemini API...", file=sys.stderr)

        client = genai.Client(api_key=settings.gemini_api_key)
        response = client.models.generate_content(
            model=settings.gemini_model,
            contents=f"Translate this medical report to Arabic:\n\n{text}",
            config=genai_types.GenerateContentConfig(
                system_instruction=_SYSTEM_INSTRUCTION,
                temperature=0.2,
                top_p=0.95,
                top_k=40,
                max_output_tokens=8192,
            ),
        )

        result = response.text.strip()
        if not result or len(result) < 20:
            return "Error: Gemini returned empty or very short translation."

        print(f"Translation complete ({len(result)} chars)", file=sys.stderr)
        return result

    except Exception as exc:
        error_msg = f"Error translating with Gemini: {exc}"
        print(error_msg, file=sys.stderr)
        return error_msg
