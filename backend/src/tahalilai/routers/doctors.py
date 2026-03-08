"""Doctor browsing, search, and recommendation endpoints."""

from __future__ import annotations

import math

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from tahalilai.database import get_db
from tahalilai.models import Doctor
from tahalilai.schemas import (
    CityCount,
    DoctorListResponse,
    DoctorResponse,
    SpecialityCount,
)

router = APIRouter(prefix="/doctors", tags=["doctors"])


# ---------------------------------------------------------------------------
# List / Search
# ---------------------------------------------------------------------------


@router.get("", response_model=DoctorListResponse)
def list_doctors(
    city: str | None = Query(None, description="Filter by city"),
    speciality: str | None = Query(None, description="Filter by primary speciality"),
    q: str | None = Query(None, description="Search name/address/description"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = db.query(Doctor)

    if city:
        query = query.filter(Doctor.city.ilike(city))
    if speciality:
        query = query.filter(Doctor.primary_speciality.ilike(speciality))
    if q:
        pattern = f"%{q}%"
        query = query.filter(
            Doctor.name.ilike(pattern)
            | Doctor.address.ilike(pattern)
            | Doctor.description.ilike(pattern)
        )

    total = query.count()
    doctors = query.offset((page - 1) * page_size).limit(page_size).all()

    return DoctorListResponse(
        doctors=[DoctorResponse.model_validate(d, from_attributes=True) for d in doctors],
        total=total,
        page=page,
        page_size=page_size,
    )


# ---------------------------------------------------------------------------
# Filter options
# ---------------------------------------------------------------------------


@router.get("/cities", response_model=list[CityCount])
def list_cities(db: Session = Depends(get_db)):
    results = (
        db.query(Doctor.city, func.count(Doctor.id).label("count"))
        .group_by(Doctor.city)
        .order_by(func.count(Doctor.id).desc())
        .all()
    )
    return [CityCount(city=r.city, count=r.count) for r in results]


@router.get("/specialities", response_model=list[SpecialityCount])
def list_specialities(db: Session = Depends(get_db)):
    results = (
        db.query(Doctor.primary_speciality, func.count(Doctor.id).label("count"))
        .group_by(Doctor.primary_speciality)
        .order_by(func.count(Doctor.id).desc())
        .all()
    )
    return [SpecialityCount(speciality=r.primary_speciality, count=r.count) for r in results]


# ---------------------------------------------------------------------------
# Recommendation (by speciality list + optional city)
# ---------------------------------------------------------------------------


@router.get("/recommend")
def recommend_doctors(
    specialities: str = Query(..., description="Comma-separated speciality list"),
    city: str | None = Query(None),
    limit: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db),
):
    spec_list = [s.strip() for s in specialities.split(",") if s.strip()]
    results: list[dict] = []

    for spec in spec_list:
        query = db.query(Doctor).filter(Doctor.primary_speciality.ilike(f"%{spec}%"))

        if city:
            city_docs = query.filter(Doctor.city.ilike(city)).limit(limit).all()
            if len(city_docs) < limit:
                other_docs = (
                    query.filter(~Doctor.city.ilike(city))
                    .limit(limit - len(city_docs))
                    .all()
                )
                doctors = city_docs + other_docs
            else:
                doctors = city_docs
        else:
            doctors = query.limit(limit).all()

        for doc in doctors:
            results.append(
                DoctorResponse.model_validate(doc, from_attributes=True).model_dump()
            )

    return results


# ---------------------------------------------------------------------------
# Nearby (requires geocoded doctors)
# ---------------------------------------------------------------------------


def _haversine(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Great-circle distance in km between two points."""
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng / 2) ** 2
    )
    return R * 2 * math.asin(math.sqrt(a))


@router.get("/nearby")
def nearby_doctors(
    lat: float = Query(..., description="User latitude"),
    lng: float = Query(..., description="User longitude"),
    speciality: str | None = Query(None),
    radius_km: float = Query(10.0, ge=0.1, le=100),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    query = db.query(Doctor).filter(
        Doctor.latitude.isnot(None),
        Doctor.longitude.isnot(None),
    )
    if speciality:
        query = query.filter(Doctor.primary_speciality.ilike(f"%{speciality}%"))

    all_docs = query.all()
    with_distance = []
    for doc in all_docs:
        dist = _haversine(lat, lng, doc.latitude, doc.longitude)
        if dist <= radius_km:
            with_distance.append((doc, dist))

    with_distance.sort(key=lambda x: x[1])
    return [
        {
            **DoctorResponse.model_validate(d, from_attributes=True).model_dump(),
            "distance_km": round(dist, 1),
        }
        for d, dist in with_distance[:limit]
    ]


# ---------------------------------------------------------------------------
# Single doctor detail
# ---------------------------------------------------------------------------


@router.get("/{doctor_id}", response_model=DoctorResponse)
def get_doctor(doctor_id: int, db: Session = Depends(get_db)):
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    return DoctorResponse.model_validate(doctor, from_attributes=True)
