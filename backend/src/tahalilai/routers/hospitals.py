"""Public health-facility browsing, search, and recommendation endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from tahalilai.database import get_db
from tahalilai.models import HealthFacility
from tahalilai.schemas import (
    CategoryCount,
    FacilityTypeCount,
    HealthFacilityListResponse,
    HealthFacilityResponse,
    RegionCount,
)

router = APIRouter(prefix="/hospitals", tags=["hospitals"])


# ---------------------------------------------------------------------------
# List / Search
# ---------------------------------------------------------------------------


@router.get("", response_model=HealthFacilityListResponse)
def list_facilities(
    region: str | None = Query(None, description="Filter by region"),
    delegation: str | None = Query(None, description="Filter by delegation / province"),
    facility_type: str | None = Query(None, description="'Hôpital' or 'Soins primaires'"),
    category_code: str | None = Query(None, description="e.g. HP, HR, HIR, CSU-1"),
    q: str | None = Query(None, description="Search by name or department"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = db.query(HealthFacility)

    if region:
        query = query.filter(HealthFacility.region.ilike(f"%{region}%"))
    if delegation:
        query = query.filter(HealthFacility.delegation.ilike(f"%{delegation}%"))
    if facility_type:
        query = query.filter(HealthFacility.facility_type.ilike(f"%{facility_type}%"))
    if category_code:
        query = query.filter(HealthFacility.category_code == category_code)
    if q:
        pattern = f"%{q}%"
        query = query.filter(
            HealthFacility.name.ilike(pattern)
            | HealthFacility.departments.ilike(pattern)
            | HealthFacility.delegation.ilike(pattern)
        )

    # Default ordering: hospitals first, then primary care, then alphabetical
    query = query.order_by(
        HealthFacility.facility_type.desc(),  # "Soins primaires" < "Hôpital" alphabetically reversed
        HealthFacility.name,
    )

    total = query.count()
    facilities = query.offset((page - 1) * page_size).limit(page_size).all()

    return HealthFacilityListResponse(
        facilities=[HealthFacilityResponse.model_validate(f, from_attributes=True) for f in facilities],
        total=total,
        page=page,
        page_size=page_size,
    )


# ---------------------------------------------------------------------------
# Filter options
# ---------------------------------------------------------------------------


@router.get("/regions", response_model=list[RegionCount])
def list_regions(db: Session = Depends(get_db)):
    results = (
        db.query(HealthFacility.region, func.count(HealthFacility.id).label("count"))
        .group_by(HealthFacility.region)
        .order_by(HealthFacility.region)
        .all()
    )
    return [RegionCount(region=r.region, count=r.count) for r in results]


@router.get("/types", response_model=list[FacilityTypeCount])
def list_types(db: Session = Depends(get_db)):
    results = (
        db.query(HealthFacility.facility_type, func.count(HealthFacility.id).label("count"))
        .group_by(HealthFacility.facility_type)
        .order_by(func.count(HealthFacility.id).desc())
        .all()
    )
    return [FacilityTypeCount(facility_type=r.facility_type, count=r.count) for r in results]


@router.get("/categories", response_model=list[CategoryCount])
def list_categories(db: Session = Depends(get_db)):
    results = (
        db.query(
            HealthFacility.category_code,
            HealthFacility.category_name,
            func.count(HealthFacility.id).label("count"),
        )
        .group_by(HealthFacility.category_code, HealthFacility.category_name)
        .order_by(func.count(HealthFacility.id).desc())
        .all()
    )
    return [
        CategoryCount(category_code=r.category_code, category_name=r.category_name, count=r.count)
        for r in results
    ]


# ---------------------------------------------------------------------------
# Recommendation (by speciality list + optional region/delegation)
# ---------------------------------------------------------------------------


@router.get("/recommend", response_model=list[HealthFacilityResponse])
def recommend_hospitals(
    specialities: str = Query(..., description="Comma-separated speciality list"),
    delegation: str | None = Query(None, description="Preferred delegation / city"),
    region: str | None = Query(None, description="Preferred region"),
    limit: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db),
):
    from tahalilai.services.recommender import find_recommended_hospitals

    spec_list = [s.strip() for s in specialities.split(",") if s.strip()]
    results = find_recommended_hospitals(
        specialities=spec_list,
        delegation=delegation,
        region=region,
        db=db,
        limit_per_speciality=limit,
    )
    return [HealthFacilityResponse.model_validate(r, from_attributes=True) for r in results]


# ---------------------------------------------------------------------------
# Single facility detail
# ---------------------------------------------------------------------------


@router.get("/{facility_id}", response_model=HealthFacilityResponse)
def get_facility(facility_id: int, db: Session = Depends(get_db)):
    facility = db.query(HealthFacility).filter(HealthFacility.id == facility_id).first()
    if not facility:
        raise HTTPException(status_code=404, detail="Health facility not found")
    return HealthFacilityResponse.model_validate(facility, from_attributes=True)
