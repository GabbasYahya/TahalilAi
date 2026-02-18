"""Pydantic request / response schemas for the TahalilAI API."""

from __future__ import annotations

from pydantic import BaseModel, Field


class AudioRequest(BaseModel):
    """Body for ``POST /generate-audio``."""

    job_id: str = Field(..., description="UUID of the completed analysis job")


class TranslationRequest(BaseModel):
    """Body for ``POST /translate``."""

    text: str = Field(..., min_length=1, description="English text to translate")
    job_id: str = Field(..., description="UUID of the analysis job")
