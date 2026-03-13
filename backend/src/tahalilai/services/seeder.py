"""Auto-seed doctors and health facilities from CSV on first startup."""

from __future__ import annotations

import csv
from pathlib import Path

from tahalilai.database import SessionLocal
from tahalilai.models import Doctor, HealthFacility


def _seed_doctors(backend_dir: Path) -> None:
    csv_path = backend_dir / "doctors_data_clean.csv"
    db = SessionLocal()
    try:
        if db.query(Doctor).count() > 0:
            print("[seeder] Doctors already seeded — skipping.")
            return
        if not csv_path.is_file():
            print(f"[seeder] Doctors CSV not found: {csv_path} — skipping.")
            return
        with open(csv_path, encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        doctors = [
            Doctor(
                title=r.get("title", ""),
                name=r["name"],
                primary_speciality=r["primary_speciality"],
                specialities=r.get("specialities", ""),
                phone=r.get("phone", ""),
                address=r.get("address", ""),
                city=r["city"],
                description=r.get("description", ""),
                languages=r.get("languages", ""),
                image_url=r.get("image_url", ""),
                profile_url=r.get("profile_url", ""),
                source_site=r.get("source_site", ""),
            )
            for r in rows
        ]
        db.bulk_save_objects(doctors)
        db.commit()
        print(f"[seeder] Seeded {len(doctors):,} doctors.")
    finally:
        db.close()


def _seed_hospitals(backend_dir: Path) -> None:
    csv_path = backend_dir / "health_facilities_clean.csv"
    db = SessionLocal()
    try:
        if db.query(HealthFacility).count() > 0:
            print("[seeder] Hospitals already seeded — skipping.")
            return
        if not csv_path.is_file():
            print(f"[seeder] Hospitals CSV not found: {csv_path} — skipping.")
            return
        with open(csv_path, encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        facilities = [
            HealthFacility(
                name=r["name"],
                region=r["region"],
                delegation=r["delegation"],
                commune=r.get("commune", ""),
                category_code=r["category_code"],
                category_name=r["category_name"],
                facility_type=r["facility_type"],
                departments=r.get("departments", ""),
            )
            for r in rows
        ]
        db.bulk_save_objects(facilities)
        db.commit()
        print(f"[seeder] Seeded {len(facilities):,} health facilities.")
    finally:
        db.close()


def seed_all(backend_dir: Path) -> None:
    """Seed all tables on startup. Safe to call repeatedly — skips if already populated."""
    _seed_doctors(backend_dir)
    _seed_hospitals(backend_dir)
