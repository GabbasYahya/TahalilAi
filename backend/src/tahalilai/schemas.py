"""Pydantic request / response schemas for the TahalilAI API."""

from __future__ import annotations

from pydantic import BaseModel, Field


class AudioRequest(BaseModel):
    """Body for ``POST /generate-audio``."""

    job_id: str = Field(..., description="UUID of the completed analysis job")
    language: str = Field(
        "en",
        description="BCP-47 language code for TTS synthesis (e.g. 'en', 'fr', 'ar')",
    )


class TranslationRequest(BaseModel):
    """Body for ``POST /translate``."""

    text: str = Field(..., min_length=1, description="English text to translate")
    job_id: str = Field(..., description="UUID of the analysis job")


class ChatRequest(BaseModel):
    """Body for ``POST /chat``."""

    job_id: str = Field(..., description="UUID of the completed analysis job")
    message: str = Field(
        ..., min_length=1, max_length=1000, description="Patient's follow-up question"
    )


class EmailRequest(BaseModel):
    """Body for ``POST /send-email``."""

    job_id: str = Field(..., description="UUID of the completed analysis job")
    recipient_email: str = Field(
        ..., min_length=5, description="Recipient email address"
    )


class WhatsAppRequest(BaseModel):
    """Body for ``POST /send-whatsapp``."""

    job_id: str = Field(..., description="UUID of the completed analysis job")
    to_phone: str = Field(
        ...,
        min_length=7,
        max_length=15,
        description="Recipient phone in international format (digits only, e.g. '213XXXXXXXXX')",
    )


# ---------------------------------------------------------------------------
# Doctor schemas
# ---------------------------------------------------------------------------


class DoctorResponse(BaseModel):
    """Single doctor record."""

    model_config = {"from_attributes": True}

    id: int
    title: str = ""
    name: str
    primary_speciality: str
    specialities: str = ""
    phone: str = ""
    address: str = ""
    city: str
    description: str = ""
    languages: str = ""
    image_url: str = ""
    profile_url: str = ""
    source_site: str = ""
    latitude: float | None = None
    longitude: float | None = None
    google_rating: float | None = None
    google_review_count: int | None = None


class DoctorListResponse(BaseModel):
    """Paginated list of doctors."""

    doctors: list[DoctorResponse]
    total: int
    page: int
    page_size: int


class CityCount(BaseModel):
    city: str
    count: int


class SpecialityCount(BaseModel):
    speciality: str
    count: int
