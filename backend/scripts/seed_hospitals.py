#!/usr/bin/env python3
"""Seed the SQLite database from health_facilities_clean.csv.

Run from repo root *after* running clean_hospitals_csv.py:
    python backend/scripts/clean_hospitals_csv.py
    python backend/scripts/seed_hospitals.py
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

_BACKEND_SRC = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(_BACKEND_SRC))

from tahalilai.database import Base, SessionLocal, engine   # noqa: E402
from tahalilai.models import HealthFacility                 # noqa: E402

CSV_PATH = Path(__file__).resolve().parent.parent / "health_facilities_clean.csv"


def seed() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        existing = db.query(HealthFacility).count()
        if existing > 0:
            print(f"Database already has {existing:,} health facilities. Skipping seed.")
            print("To re-seed: DELETE FROM health_facilities; then re-run this script.")
            return

        if not CSV_PATH.is_file():
            print(f"ERROR: CSV not found: {CSV_PATH}", file=sys.stderr)
            print("Run clean_hospitals_csv.py first.", file=sys.stderr)
            sys.exit(1)

        facilities: list[HealthFacility] = []
        with open(CSV_PATH, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                facilities.append(
                    HealthFacility(
                        name          = row["name"],
                        region        = row["region"],
                        delegation    = row["delegation"],
                        commune       = row.get("commune", ""),
                        category_code = row["category_code"],
                        category_name = row["category_name"],
                        facility_type = row["facility_type"],
                        departments   = row.get("departments", ""),
                    )
                )

        db.bulk_save_objects(facilities)
        db.commit()
        print(f"Seeded {len(facilities):,} health facilities into the database.")

        # Summary
        from collections import Counter
        by_type = Counter(f.facility_type for f in facilities)
        for t, n in sorted(by_type.items()):
            print(f"  {t}: {n:,}")

    finally:
        db.close()


if __name__ == "__main__":
    seed()
