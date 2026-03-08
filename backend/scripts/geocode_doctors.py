#!/usr/bin/env python3
"""Batch geocode doctor addresses using Google Maps Geocoding API.

Populates the ``latitude`` and ``longitude`` columns in the database.
Run once after seeding the DB. Requires ``GOOGLE_MAPS_API_KEY`` in ``.env``.

Usage:
    python backend/scripts/geocode_doctors.py

Cost: ~$5 per 1,000 requests ($200/month free tier covers ~40K).
"""

from __future__ import annotations

import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

_BACKEND_SRC = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(_BACKEND_SRC))

from tahalilai.config import get_settings  # noqa: E402
from tahalilai.database import SessionLocal  # noqa: E402
from tahalilai.models import Doctor  # noqa: E402


def geocode_address(address: str, city: str, api_key: str) -> tuple[float, float] | None:
    """Geocode an address using Google Maps Geocoding API."""
    query = f"{address}, {city}, Morocco"
    url = (
        "https://maps.googleapis.com/maps/api/geocode/json?"
        f"address={urllib.parse.quote(query)}&key={api_key}"
    )
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
        if data["status"] == "OK" and data["results"]:
            loc = data["results"][0]["geometry"]["location"]
            return (loc["lat"], loc["lng"])
    except Exception as exc:
        print(f"  Geocoding error: {exc}")
    return None


def main() -> None:
    settings = get_settings()
    api_key = settings.google_maps_api_key
    if not api_key:
        print("ERROR: Set GOOGLE_MAPS_API_KEY in .env to use geocoding.")
        print("This script is optional. City-based filtering works without it.")
        sys.exit(1)

    db = SessionLocal()
    try:
        doctors = (
            db.query(Doctor)
            .filter(Doctor.latitude.is_(None), Doctor.address != "")
            .all()
        )
        print(f"Geocoding {len(doctors)} doctors without coordinates...")

        success = 0
        for i, doc in enumerate(doctors):
            coords = geocode_address(doc.address, doc.city, api_key)
            if coords:
                doc.latitude, doc.longitude = coords
                success += 1

            if (i + 1) % 50 == 0:
                db.commit()
                print(f"  {i + 1}/{len(doctors)} processed ({success} geocoded)")
                time.sleep(0.1)  # respect rate limits

        db.commit()
        total_geocoded = db.query(Doctor).filter(Doctor.latitude.isnot(None)).count()
        print(f"Done. {total_geocoded} doctors now have coordinates.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
