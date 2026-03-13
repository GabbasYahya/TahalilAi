"""SQLAlchemy ORM models."""

from __future__ import annotations

from sqlalchemy import Column, Float, Index, Integer, String

from tahalilai.database import Base


class HealthFacility(Base):
    """Moroccan public health facilities (hospitals + primary care centres)."""

    __tablename__ = "health_facilities"

    id            = Column(Integer, primary_key=True, autoincrement=True)
    name          = Column(String, nullable=False, index=True)
    region        = Column(String, nullable=False, index=True)
    delegation    = Column(String, nullable=False, index=True)   # province / préfecture
    commune       = Column(String, default="")
    category_code = Column(String, nullable=False, index=True)   # e.g. HP, HIR, CSU-1
    category_name = Column(String, nullable=False)               # full French label
    facility_type = Column(String, nullable=False, index=True)   # Hôpital | Soins primaires
    departments   = Column(String, default="")                   # comma-separated medical depts
    phone         = Column(String, default="")
    address       = Column(String, default="")
    latitude      = Column(Float, nullable=True)
    longitude     = Column(Float, nullable=True)

    __table_args__ = (
        Index("ix_hf_region_type", "region", "facility_type"),
        Index("ix_hf_delegation_cat", "delegation", "category_code"),
    )


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
