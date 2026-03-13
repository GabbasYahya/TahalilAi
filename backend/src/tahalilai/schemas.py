"""Pydantic request / response schemas for the TahalilAI API."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, EmailStr, Field


# ---------------------------------------------------------------------------
# Structured analysis output schemas
# ---------------------------------------------------------------------------


class OverallStatus(str, Enum):
    normal = "normal"
    mostly_normal = "mostly_normal"
    abnormal = "abnormal"
    critical = "critical"


class ConfidenceLevel(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class GenderInferred(str, Enum):
    male = "male"
    female = "female"
    unknown = "unknown"


class AgeGroupInferred(str, Enum):
    child = "child"
    adolescent = "adolescent"
    adult = "adult"
    elderly = "elderly"
    unknown = "unknown"


class BiomarkerStatus(str, Enum):
    low = "low"
    normal = "normal"
    high = "high"
    borderline = "borderline"


class ReportSummary(BaseModel):
    overall_status: OverallStatus
    short_explanation: str
    confidence_level: ConfidenceLevel


class PatientContext(BaseModel):
    gender_inferred: GenderInferred
    age_group_inferred: AgeGroupInferred
    inference_confidence: ConfidenceLevel


class BiomarkerAnalysis(BaseModel):
    marker_name: str
    measured_value: str
    reference_range: str
    status: BiomarkerStatus
    clinical_significance: str


class AbnormalFinding(BaseModel):
    marker: str
    issue: str
    possible_meanings: list[str] = []
    recommended_followup_tests: list[str] = []


class RecommendedSpecialty(BaseModel):
    specialty: str
    reason: str


class MissingInformation(BaseModel):
    needs_age: bool = False
    needs_gender: bool = False
    additional_questions: list[str] = []


class StructuredAnalysis(BaseModel):
    """Full structured JSON output from the medical analyzer."""

    report_summary: ReportSummary
    patient_context: PatientContext
    biomarker_analysis: list[BiomarkerAnalysis] = []
    abnormal_findings: list[AbnormalFinding] = []
    recommended_specialties: list[RecommendedSpecialty] = []
    health_recommendations: list[str] = []
    missing_information: MissingInformation = MissingInformation()
    system_feedback: list[str] = []


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
    recipient_email: EmailStr = Field(
        ..., description="Recipient email address"
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


# ---------------------------------------------------------------------------
# Health-facility schemas
# ---------------------------------------------------------------------------


class HealthFacilityResponse(BaseModel):
    """Single public health facility record."""

    model_config = {"from_attributes": True}

    id: int
    name: str
    region: str
    delegation: str
    commune: str = ""
    category_code: str
    category_name: str
    facility_type: str
    departments: str = ""
    phone: str = ""
    address: str = ""
    latitude: float | None = None
    longitude: float | None = None


class HealthFacilityListResponse(BaseModel):
    """Paginated list of health facilities."""

    facilities: list[HealthFacilityResponse]
    total: int
    page: int
    page_size: int


class RegionCount(BaseModel):
    region: str
    count: int


class FacilityTypeCount(BaseModel):
    facility_type: str
    count: int


class CategoryCount(BaseModel):
    category_code: str
    category_name: str
    count: int
