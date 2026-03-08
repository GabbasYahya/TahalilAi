"""SQLAlchemy ORM models."""

from __future__ import annotations

from sqlalchemy import Column, Float, Index, Integer, String

from tahalilai.database import Base


class Doctor(Base):
    __tablename__ = "doctors"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String, default="")
    name = Column(String, nullable=False, index=True)
    primary_speciality = Column(String, nullable=False, index=True)
    specialities = Column(String, default="")
    phone = Column(String, default="")
    address = Column(String, default="")
    city = Column(String, nullable=False, index=True)
    description = Column(String, default="")
    languages = Column(String, default="")
    image_url = Column(String, default="")
    profile_url = Column(String, default="")
    source_site = Column(String, default="")

    # Future: geocoding
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

    # Future: Google Maps ratings
    google_rating = Column(Float, nullable=True)
    google_review_count = Column(Integer, nullable=True)

    __table_args__ = (
        Index("ix_doctors_city_speciality", "city", "primary_speciality"),
    )
