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
from tahalilai.models import Doctor, HealthFacility

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
            city_pattern = f"%{city}%"
            city_doctors = (
                query.filter(Doctor.city.ilike(city_pattern))
                .order_by(func.random())
                .limit(limit_per_speciality)
                .all()
            )
            if len(city_doctors) < limit_per_speciality:
                other_doctors = (
                    query.filter(~Doctor.city.ilike(city_pattern))
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


# ---------------------------------------------------------------------------
# Public hospital / health-facility recommendation
# ---------------------------------------------------------------------------

# Maps doctor speciality keywords → hospital department keywords to search for
_SPEC_TO_DEPT: dict[str, str] = {
    "cardiologue": "Cardiologie",
    "cardiaque": "Cardiologie",
    "neurologue": "Neurologie",
    "neurochirurgien": "Neurologie",
    "gastro": "Gastro-entérologie",
    "gastroentérologue": "Gastro-entérologie",
    "gynécologue": "Gynécologie",
    "gynécologie": "Gynécologie",
    "pédiatre": "Pédiatrie",
    "pneumologue": "Pneumologie",
    "oncologue": "Oncologie",
    "hématologue": "Hématologie",
    "psychiatre": "Psychiatrie",
    "psychologue": "Psychiatrie",
    "néphrologue": "Néphrologie",  # not in most hospital depts, fallback general
    "urologue": "Chirurgie",
    "chirurgien": "Chirurgie",
    "traumatologue": "Chirurgie",
    "rhumatologue": "Médecine générale",
    "endocrinologue": "Médecine générale",
    "diabétologue": "Médecine générale",
    "ophtalmologue": "Médecine générale",
    "dermatologue": "Médecine générale",
    "allergologue": "Médecine générale",
    "médecin": "Médecine générale",
    "radiologue": "Radiologie",
    "maternité": "Maternité",
    "obstétricien": "Maternité",
    "reproduction": "Santé de la reproduction",
    "tuberculose": "Tuberculose",
    "respiratoire": "Maladies respiratoires",
}


def _speciality_to_dept_keyword(speciality: str) -> str:
    """Map a doctor speciality string to a hospital department keyword."""
    s_lower = speciality.lower()
    for key, dept in _SPEC_TO_DEPT.items():
        if key in s_lower:
            return dept
    # Default: general medicine covers almost everything
    return "Médecine générale"


def find_recommended_hospitals(
    specialities: list[str],
    delegation: str | None,
    region: str | None,
    db: Session,
    limit_per_speciality: int = 3,
) -> list[HealthFacility]:
    """Find public health facilities relevant to the recommended specialities.

    Prioritises:
    1. Hospitals (HIR/HR/HP) in the same delegation/city, matching department
    2. Hospitals in the same region if delegation doesn't have enough
    3. Specialised centres (CRO for oncology, CDTMR for pneumology, CPU for psychiatry)
    """
    seen_ids: set[int] = set()
    results: list[HealthFacility] = []
    hospital_types = ("Hôpital",)

    for spec in specialities:
        dept_kw = _speciality_to_dept_keyword(spec)

        # Base query: hospitals with matching department
        base = (
            db.query(HealthFacility)
            .filter(
                HealthFacility.facility_type.in_(hospital_types),
                HealthFacility.departments.ilike(f"%{dept_kw}%"),
            )
        )

        # Priority 1: same delegation
        if delegation:
            prio1 = (
                base.filter(HealthFacility.delegation.ilike(f"%{delegation}%"))
                .limit(limit_per_speciality)
                .all()
            )
        else:
            prio1 = []

        # Priority 2: same region, fill remaining slots
        remaining = limit_per_speciality - len(prio1)
        prio1_ids = {f.id for f in prio1}
        if remaining > 0 and region:
            prio2 = (
                base.filter(
                    HealthFacility.region.ilike(f"%{region}%"),
                    ~HealthFacility.id.in_(prio1_ids),
                )
                .limit(remaining)
                .all()
            )
        else:
            prio2 = []

        # Priority 3: anywhere in Morocco, fill remaining
        combined = prio1 + prio2
        remaining = limit_per_speciality - len(combined)
        combined_ids = {f.id for f in combined}
        if remaining > 0:
            prio3 = (
                base.filter(~HealthFacility.id.in_(combined_ids))
                .limit(remaining)
                .all()
            )
            combined = combined + prio3

        for fac in combined:
            if fac.id not in seen_ids:
                seen_ids.add(fac.id)
                results.append(fac)

    return results

