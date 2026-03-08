#!/usr/bin/env python3
"""Enrich doctor records with Google Maps ratings via Places API.

Searches each doctor on Google Places and stores their rating and review count.
Run once after seeding the DB. Requires ``GOOGLE_MAPS_API_KEY`` in ``.env``.

Usage:
    python backend/scripts/enrich_ratings.py

Cost: ~$32 per 1,000 requests (Places Text Search).
      For 9K doctors, this costs approximately $295 one-time.
      Run selectively (e.g., top cities) to reduce cost.
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


def search_place_rating(
    name: str, city: str, api_key: str
) -> tuple[float, int] | None:
    """Search Google Places for a doctor and return (rating, review_count)."""
    query = f"Dr {name} {city} Morocco"
    url = (
        "https://maps.googleapis.com/maps/api/place/textsearch/json?"
        f"query={urllib.parse.quote(query)}&key={api_key}"
    )
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
        if data["status"] == "OK" and data["results"]:
            place = data["results"][0]
            rating = place.get("rating")
            reviews = place.get("user_ratings_total", 0)
            if rating:
                return (float(rating), int(reviews))
    except Exception as exc:
        print(f"  Places API error: {exc}")
    return None


def main() -> None:
    settings = get_settings()
    api_key = settings.google_maps_api_key
    if not api_key:
        print("ERROR: Set GOOGLE_MAPS_API_KEY in .env to use ratings enrichment.")
        print("This script is optional. The app works without ratings.")
        sys.exit(1)

    # Optional: filter by city to reduce cost
    city_filter = None
    if len(sys.argv) > 1:
        city_filter = sys.argv[1]
        print(f"Filtering to city: {city_filter}")

    db = SessionLocal()
    try:
        query = db.query(Doctor).filter(Doctor.google_rating.is_(None))
        if city_filter:
            query = query.filter(Doctor.city.ilike(city_filter))
        doctors = query.all()

        print(f"Enriching {len(doctors)} doctors with Google ratings...")

        enriched = 0
        for i, doc in enumerate(doctors):
            result = search_place_rating(doc.name, doc.city, api_key)
            if result:
                doc.google_rating, doc.google_review_count = result
                enriched += 1

            if (i + 1) % 50 == 0:
                db.commit()
                print(f"  {i + 1}/{len(doctors)} processed ({enriched} rated)")
                time.sleep(0.2)  # respect rate limits

        db.commit()
        total_rated = db.query(Doctor).filter(Doctor.google_rating.isnot(None)).count()
        print(f"Done. {total_rated} doctors now have Google ratings.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
