#!/usr/bin/env python3
"""Seed the SQLite database from doctors_data_clean.csv.

Run from repo root:
    python backend/scripts/seed_db.py
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

# Ensure the backend package is importable
_BACKEND_SRC = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(_BACKEND_SRC))

from tahalilai.database import Base, SessionLocal, engine  # noqa: E402
from tahalilai.models import Doctor  # noqa: E402

CSV_PATH = Path(__file__).resolve().parent.parent / "doctors_data_clean.csv"


def seed() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        existing = db.query(Doctor).count()
        if existing > 0:
            print(f"Database already has {existing:,} doctors. Skipping seed.")
            return

        if not CSV_PATH.is_file():
            print(f"ERROR: CSV not found: {CSV_PATH}", file=sys.stderr)
            sys.exit(1)

        with open(CSV_PATH, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            doctors = []
            for row in reader:
                doctors.append(
                    Doctor(
                        title=row.get("title", ""),
                        name=row["name"],
                        primary_speciality=row["primary_speciality"],
                        specialities=row.get("specialities", ""),
                        phone=row.get("phone", ""),
                        address=row.get("address", ""),
                        city=row["city"],
                        description=row.get("description", ""),
                        languages=row.get("languages", ""),
                        image_url=row.get("image_url", ""),
                        profile_url=row.get("profile_url", ""),
                        source_site=row.get("source_site", ""),
                    )
                )

        db.bulk_save_objects(doctors)
        db.commit()
        print(f"Seeded {len(doctors):,} doctors into the database.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
