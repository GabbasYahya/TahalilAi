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

_SYSTEM_INSTRUCTIONS: dict[str, str] = {
    "ar": """\
You are an expert medical translator specializing in English to Arabic translation.
Your task is to translate medical laboratory reports with the highest accuracy.

CRITICAL RULES:
1. Preserve ALL formatting (markdown bold **, bullet points -, line breaks)
2. Use standard medical Arabic terminology
3. Maintain the exact structure and sections
4. Translate section headers accurately:
   - "Summary" → "الملخص"
   - "Patient Profile" → "ملف المريض"
   - "Detailed Analysis" → "التحليل المفصل"
   - "Abnormal Findings" → "النتائج غير الطبيعية"
   - "Health Recommendations" → "التوصيات الصحية"
   - "Recommended Medical Consultation" → "الاستشارة الطبية الموصى بها"
   - "Additional Information Needed" → "معلومات إضافية مطلوبة"
   - "Overall Status:" → "الحالة العامة:"
   - "Reference Range:" → "النطاق المرجعي:"
   - "Meaning:" → "المعنى:"
   - "Gender:" → "الجنس:"
   - "Age Group:" → "الفئة العمرية:"
5. Keep ALL section headers (**Header**) on their OWN separate line
6. Keep numerical values, units, and lab marker names EXACTLY as they appear
7. Do NOT add explanations, comments, or extra text
8. Output ONLY the translated Arabic text
""",
    "fr": """\
You are an expert medical translator specializing in English to French translation.
Your task is to translate medical laboratory reports with the highest accuracy.

CRITICAL RULES:
1. Preserve ALL formatting (markdown bold **, bullet points -, line breaks)
2. Use standard medical French terminology
3. Maintain the exact structure and sections
4. Translate section headers accurately:
   - "Summary" → "Résumé"
   - "Patient Profile" → "Profil du Patient"
   - "Detailed Analysis" → "Analyse Détaillée"
   - "Abnormal Findings" → "Résultats Anormaux"
   - "Health Recommendations" → "Recommandations Santé"
   - "Recommended Medical Consultation" → "Consultation Médicale Recommandée"
   - "Additional Information Needed" → "Informations Supplémentaires Requises"
   - "Overall Status:" → "Statut général :"
   - "Reference Range:" → "Valeur de référence :"
   - "Meaning:" → "Signification :"
   - "Gender:" → "Sexe :"
   - "Age Group:" → "Groupe d'âge :"
5. Keep ALL section headers (**Header**) on their OWN separate line
6. Keep numerical values, units, and lab marker names EXACTLY as they appear
7. Do NOT add explanations, comments, or extra text
8. Output ONLY the translated French text
""",
}

_PROMPTS: dict[str, str] = {
    "ar": "Translate this medical report to Arabic:",
    "fr": "Translate this medical report to French:",
}


def translate_medical_report(text: str, target_lang: str = "ar") -> str:
    """Translate an English medical report to the target language using Gemini.

    Args:
        text: English medical report text.
        target_lang: ``"ar"`` for Arabic or ``"fr"`` for French.

    Returns:
        Translated text, or an error string prefixed with ``Error:``.
    """
    if target_lang not in _SYSTEM_INSTRUCTIONS:
        return f"Error: unsupported target language '{target_lang}'. Use 'ar' or 'fr'."

    if not _GEMINI_AVAILABLE:
        return "Error: google-genai SDK not installed. Run: pip install google-genai"

    settings = get_settings()
    if not settings.gemini_api_key:
        return "Error: GEMINI_API_KEY not set in .env file"

    try:
        print(f"Sending translation request to Gemini API (→ {target_lang})...", file=sys.stderr)

        client = genai.Client(api_key=settings.gemini_api_key)
        response = client.models.generate_content(
            model=settings.gemini_model,
            contents=f"{_PROMPTS[target_lang]}\n\n{text}",
            config=genai_types.GenerateContentConfig(
                system_instruction=_SYSTEM_INSTRUCTIONS[target_lang],
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
