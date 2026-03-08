"""Doctor recommendation service.

After analysis, uses Gemini to extract which medical specialities the patient
should consult, then queries the doctors database for matches.
"""

from __future__ import annotations

import json
import sys

from sqlalchemy import func
from sqlalchemy.orm import Session

from tahalilai.config import get_settings
from tahalilai.models import Doctor

try:
    from google import genai
    from google.genai import types as genai_types

    _GEMINI_AVAILABLE = True
except ImportError:
    _GEMINI_AVAILABLE = False


# Canonical speciality list — must match normalised DB values.
CANONICAL_SPECIALITIES: list[str] = [
    "Médecin généraliste",
    "Cardiologue",
    "Dermatologue",
    "Endocrinologue",
    "Gastro-entérologue",
    "Gynécologue",
    "Gynécologue obstétricien",
    "Néphrologue",
    "Neurologue",
    "Ophtalmologue",
    "Oto-rhino-laryngologue",
    "Pédiatre",
    "Pneumologue",
    "Psychiatre",
    "Radiologue",
    "Rhumatologue",
    "Urologue",
    "Diabétologue",
    "Allergologue",
    "Médecin interniste",
    "Dentiste",
    "Chirurgien dentiste",
    "Oncologue",
    "Hématologue",
    "Nutritionniste",
    "Kinésithérapeute",
    "Psychologue",
    "Anesthésiste-réanimateur",
    "Neurochirurgien",
    "Chirurgien général",
    "Chirurgien digestif",
    "Chirurgien cardiaque",
    "Traumatologue-orthopédiste",
    "Médecine esthétique",
    "Addictologue",
    "Algologue",
]

_EXTRACT_PROMPT = """\
You are a medical routing assistant. Given the AI analysis of a patient's lab \
results below, determine which medical specialities the patient should consult.

Return ONLY a JSON object with this exact format:
{{"specialities": ["Speciality1", "Speciality2"], "urgency": "routine|soon|urgent"}}

Pick specialities ONLY from this list:
{specialities_list}

Rules:
- Return 1-3 specialities maximum.
- Only include "Médecin généraliste" if the results are truly non-specific or \
no specialist is clearly indicated.
- "urgency" = "routine" for normal results, "soon" for mild abnormalities, \
"urgent" for critical values.
- Return ONLY the JSON, no explanation.

ANALYSIS:
{analysis}
"""


def extract_recommended_specialities(analysis: str) -> dict:
    """Extract recommended specialities from an analysis text.

    Returns: {"specialities": [...], "urgency": "routine|soon|urgent"}
    """
    settings = get_settings()
    default = {"specialities": ["Médecin généraliste"], "urgency": "routine"}

    if not (_GEMINI_AVAILABLE and settings.gemini_api_key):
        return default

    try:
        prompt = _EXTRACT_PROMPT.format(
            specialities_list=", ".join(CANONICAL_SPECIALITIES),
            analysis=analysis[:3000],
        )

        client = genai.Client(api_key=settings.gemini_api_key)
        response = client.models.generate_content(
            model=settings.gemini_model,
            contents=prompt,
            config=genai_types.GenerateContentConfig(
                temperature=0.1,
                max_output_tokens=256,
            ),
        )

        text = response.text.strip()
        # Strip markdown code fences if present
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()

        result = json.loads(text)
        if "specialities" in result:
            return result
        return default

    except Exception as exc:
        print(f"Speciality extraction failed: {exc}", file=sys.stderr)
        return default


def find_recommended_doctors(
    specialities: list[str],
    city: str | None,
    db: Session,
    limit_per_speciality: int = 3,
) -> list[dict]:
    """Query doctors matching the recommended specialities.

    If city is provided, prioritize doctors in that city.
    """
    results: list[dict] = []
    seen_ids: set[int] = set()

    for spec in specialities:
        query = db.query(Doctor).filter(Doctor.primary_speciality.ilike(f"%{spec}%"))

        if city:
            city_doctors = (
                query.filter(Doctor.city.ilike(city))
                .order_by(func.random())
                .limit(limit_per_speciality)
                .all()
            )
            if len(city_doctors) < limit_per_speciality:
                other_doctors = (
                    query.filter(~Doctor.city.ilike(city))
                    .order_by(func.random())
                    .limit(limit_per_speciality - len(city_doctors))
                    .all()
                )
                doctors = city_doctors + other_doctors
            else:
                doctors = city_doctors
        else:
            doctors = query.order_by(func.random()).limit(limit_per_speciality).all()

        for doc in doctors:
            if doc.id not in seen_ids:
                seen_ids.add(doc.id)
                results.append(
                    {
                        "id": doc.id,
                        "title": doc.title or "",
                        "name": doc.name,
                        "speciality": doc.primary_speciality,
                        "phone": doc.phone or "",
                        "address": doc.address or "",
                        "city": doc.city,
                        "image_url": doc.image_url or "",
                        "profile_url": doc.profile_url or "",
                    }
                )

    return results
