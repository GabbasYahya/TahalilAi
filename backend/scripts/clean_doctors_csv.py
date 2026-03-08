#!/usr/bin/env python3
"""
clean_doctors_csv.py
====================
Reads the raw ``doctors_data.csv``, applies every cleaning / normalisation
step identified during profiling, and writes a production-ready
``doctors_data_clean.csv`` next to the original.

Run from the repo root:
    python backend/scripts/clean_doctors_csv.py

What this script does
---------------------
 1. Strips the UTF-8 BOM from the header row.
 2. Drops useless columns (email, neighborhood, coordinates).
 3. Normalises doctor names — strips "Dr " / "Dr. " prefix into ``title``.
 4. Standardises phone numbers to ``+212XXXXXXXXX`` format.
 5. Replaces known placeholder phones (+212522000000) with empty.
 6. Extracts ``primary_speciality`` from multi-speciality strings.
 7. Normalises city names (accent variants ->canonical).
 8. Normalises speciality names (130 variants ->~80 canonical French names).
 9. Cleans description and placeholder image URLs.
10. Drops near-empty columns (timetable, cabinet_name).
11. Deduplicates rows (name + city ->keep richest row).
12. Clears shared image_url / profile_url (same URL on 2+ doctors = fake data).
13. Writes ``doctors_data_clean.csv`` with a tidy column order.
"""

from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

# ── paths ─────────────────────────────────────────────────
HERE = Path(__file__).resolve().parent.parent          # backend/
RAW  = HERE / "doctors_data.csv"
OUT  = HERE / "doctors_data_clean.csv"

# ── known Cloudinary placeholder images ───────────────────
# These identical thumbnails are shared across thousands of rows and carry
# zero information about the individual doctor.
_PLACEHOLDER_IMAGES: frozenset[str] = frozenset({
    "https://res.cloudinary.com/hh9gnin1v/image/upload/c_thumb,dpr_auto,f_webp,g_face,h_115,q_auto,w_115,z_0.6/v1697502747/54ff5217353231007b5e0100_photo_1.jpg",
    "https://res.cloudinary.com/hh9gnin1v/image/upload/c_thumb,dpr_auto,f_webp,g_face,h_115,q_auto,w_115,z_0.6/v1615152680/5aaae3cd4578b300045fda9a_photo_1.jpg",
    "https://res.cloudinary.com/hh9gnin1v/image/upload/c_thumb,dpr_auto,f_webp,g_face,h_115,q_auto,w_115,z_0.6/v1726380953/52484bcf6bef8a7d10000004_photo_1.jpg",
    "https://res.cloudinary.com/hh9gnin1v/image/upload/c_thumb,dpr_auto,f_webp,g_face,h_115,q_auto,w_115,z_0.6/v1667519374/6334b3050ecaf400270b0496_photo_1.jpg",
    "https://res.cloudinary.com/hh9gnin1v/image/upload/c_thumb,dpr_auto,f_webp,g_face,h_115,q_auto,w_115,z_0.6/v1757510525/68bec617fb0e9b00325a3bca_photo_1_1fd47329-4636-407d-a343-f8b2fba11d7e.jpg",
    "https://res.cloudinary.com/hh9gnin1v/image/upload/c_thumb,dpr_auto,f_webp,g_face,h_115,q_auto,w_115,z_0.6/v1766067179/6943a024bbf5700076f6f61f_photo_1_4403e416-9ffc-48e6-9ab8-2b544dec8c32.jpg",
    "https://res.cloudinary.com/hh9gnin1v/image/upload/c_thumb,dpr_auto,f_webp,g_face,h_115,q_auto,w_115,z_0.6/v1762852852/541963313137356c88000000_photo_1_9c097fa8-c4fb-4df1-8bb7-9cd6fc79a50e.jpg",
    "https://res.cloudinary.com/hh9gnin1v/image/upload/c_thumb,dpr_auto,f_webp,g_face,h_115,q_auto,w_115,z_0.6/v1751376523/681da525fb4ae00047978775_photo_1_64a96eec-f114-46e2-8c84-7fe74fafbf4d.jpg",
    "https://res.cloudinary.com/hh9gnin1v/image/upload/c_thumb,dpr_auto,f_webp,g_face,h_115,q_auto,w_115,z_0.6/v1489055297/58c04026192b69000ef6b227_photo_1.jpg",
    "https://res.cloudinary.com/hh9gnin1v/image/upload/c_thumb,dpr_auto,f_webp,g_face,h_115,q_auto,w_115,z_0.6/v1553010136/55cc4a013630630081000024_photo_1.jpg",
    "https://res.cloudinary.com/hh9gnin1v/image/upload/c_thumb,dpr_auto,f_webp,g_face,h_115,q_auto,w_115,z_0.6/v1574801982/52543404b295931782000001_photo_1.jpg",
    "https://res.cloudinary.com/hh9gnin1v/image/upload/c_thumb,dpr_auto,f_webp,g_face,h_115,q_auto,w_115,z_0.6/v1654683588/624efaca0d18180038b30a90_photo_1.jpg",
    "https://res.cloudinary.com/hh9gnin1v/image/upload/c_thumb,dpr_auto,f_webp,g_face,h_115,q_auto,w_115,z_0.6/v1664874364/55d1f9bc3137350081000022_photo_1.jpg",
    "https://res.cloudinary.com/hh9gnin1v/image/upload/c_thumb,dpr_auto,f_webp,g_face,h_115,q_auto,w_115,z_0.6/v1678375097/6409ec2021b226002a5bb0c8_photo_1.jpg",
    "https://res.cloudinary.com/hh9gnin1v/image/upload/c_thumb,dpr_auto,f_webp,g_face,h_115,q_auto,w_115,z_0.6/v1698679735/6072146648c0f2003808fc83_photo_1.jpg",
    "https://res.cloudinary.com/hh9gnin1v/image/upload/c_thumb,dpr_auto,f_webp,g_face,h_115,q_auto,w_115,z_0.6/v1729068161/56dd7191787c6d0003000342_photo_1_ed923560-44c7-43b1-b1a2-8b8c8d2ee8c6.png",
    "https://res.cloudinary.com/hh9gnin1v/image/upload/c_thumb,dpr_auto,f_webp,g_face,h_115,q_auto,w_115,z_0.6/v1744735947/67c1d4724eda51002b289bd3_photo_1_bf18cb68-ba0d-49f9-b61e-0bf68d0571f1.jpg",
    "https://res.cloudinary.com/hh9gnin1v/image/upload/c_thumb,dpr_auto,f_webp,g_face,h_115,q_auto,w_115,z_0.6/v1547830398/566e03b87992060088000010_photo_1.jpg",
    "https://res.cloudinary.com/hh9gnin1v/image/upload/c_thumb,dpr_auto,f_webp,g_face,h_115,q_auto,w_115,z_0.6/52455bc7e9a791d8c0000001_photo_1.jpg",
    "https://res.cloudinary.com/hh9gnin1v/image/upload/c_thumb,dpr_auto,f_webp,g_face,h_115,q_auto,w_115,z_0.6/v1489055297/58c04026192b69000ef6b227_photo_1.jpg",
})

# ── placeholder / junk phone numbers ─────────────────────
_PLACEHOLDER_PHONES: frozenset[str] = frozenset({
    "+212522000000",
})

# ── city normalisation ───────────────────────────────────
_CITY_NORMALIZE: dict[str, str] = {
    "Témara": "Temara",
    "Laâyoune": "Laayoune",
}

# ── speciality normalisation ─────────────────────────────
# Maps variant/English/duplicate names ->canonical French name.
_SPECIALITY_NORMALIZE: dict[str, str] = {
    # Médecin généraliste
    "Médecine générale": "Médecin généraliste",
    "General practitioner": "Médecin généraliste",
    "Omnipraticien": "Médecin généraliste",

    # Dentiste
    "Dentaire": "Dentiste",
    "Chirurgie dentaire": "Dentiste",

    # Ophtalmologue
    "Ophthalmologist": "Ophtalmologue",
    "Chirurgien ophtalmologue": "Ophtalmologue",
    "Ophtalmologue pédiatrique": "Ophtalmologue",

    # Kinésithérapeute
    "Kinésithérapie": "Kinésithérapeute",

    # Psychiatre
    "Psychiatrie": "Psychiatre",

    # Pédiatre
    "Pédiatrie": "Pédiatre",

    # Gynécologue
    "Gynecologist": "Gynécologue",

    # Gynécologue obstétricien
    "Gynécologue-obstétricien": "Gynécologue obstétricien",

    # Gastro-entérologue
    "Hépatogastroentérologue": "Gastro-entérologue",
    "Hépato-gastro-entérologue": "Gastro-entérologue",
    "Gastroentérologue": "Gastro-entérologue",
    "Gastro-entérologue pédiatrique": "Gastro-entérologue",

    # Radiologue
    "Radiologie - Echographie": "Radiologue",
    "Radiologie - IRM": "Radiologue",
    "Radiologie - Scanner": "Radiologue",
    "Radiologie - Mammographie": "Radiologue",
    "Radiology - MRI": "Radiologue",

    # Oto-rhino-laryngologue
    "Oto-rhino-laryngologiste et chirurgien cervico-facial": "Oto-rhino-laryngologue",
    "Oto-rhino-laryngologiste (ORL)": "Oto-rhino-laryngologue",

    # Rhumatologue
    "Rhumatologie": "Rhumatologue",

    # Néphrologue
    "Néphrologue pédiatrique": "Néphrologue",

    # Pneumologue
    "Pneumologie": "Pneumologue",

    # Médecin interniste
    "Interniste": "Médecin interniste",

    # Dermatologue
    "Dermatologue-vénérologue": "Dermatologue",
    "Dermatologue pédiatrique": "Dermatologue",

    # Allergologue
    "Allergologue-pédiatrique": "Allergologue",

    # Psychologue
    "Psychologist": "Psychologue",

    # Oncologue
    "Oncologue - Cancérologue": "Oncologue",
    "Cancérologue": "Oncologue",

    # Gérontologue
    "Gérontologue - Gériatre": "Gérontologue",

    # Médecine esthétique
    "Médecin esthétique": "Médecine esthétique",

    # Traumatologue-orthopédiste
    "Traumatologue": "Traumatologue-orthopédiste",
    "Traumatologue - orthopédiste": "Traumatologue-orthopédiste",
    "Chirurgien orthopédiste et traumatologue": "Traumatologue-orthopédiste",
    "Chirurgien traumatologue-orthopédiste": "Traumatologue-orthopédiste",
    "Chirurgien orthopédiste pédiatrique": "Traumatologue-orthopédiste",

    # Chirurgien général
    "Chirurgien généraliste": "Chirurgien général",

    # Cardiologue
    "Cardiologue interventionniste": "Cardiologue",
    "Cardiologue rythmologue": "Cardiologue",
    "Rythmologue interventionnel": "Cardiologue",
    "Cardiologue pédiatrique": "Cardiologue",

    # Diététicien / Nutritionniste
    "Diététicien": "Nutritionniste",

    # Diabétologue nutritionniste ->Diabétologue
    "Diabétologue nutritionniste": "Diabétologue",

    # Algologue
    "Algologue - Traitement de la douleur": "Algologue",

    # Parodontologue
    "Parodontologiste": "Parodontologue",

    # Pédodontiste (keep as Pédodontiste — different from Pédiatre)
    # Occlusodontiste (keep)
    # Endodontiste (keep)

    # Chirurgien viscéral ->Chirurgien digestif
    "Chirurgien viscéral": "Chirurgien digestif",

    # Chirurgien de l'obésité ->Chirurgien digestif
    "Chirurgien de l'obésité": "Chirurgien digestif",

    # Neuropsychiatre ->keep separate (it's a real speciality)
    # Neuropsychologue ->keep separate

    # Hépatologue ->Gastro-entérologue (hepatology is a sub of gastro)
    "Hépatologue": "Gastro-entérologue",

    # Phtisiologue ->Pneumologue (TB specialist = pulmonologist)
    "Phtisiologue": "Pneumologue",

    # Radiothérapeute ->Oncologue
    "Radiothérapeute": "Oncologue",
}


# ── helpers ───────────────────────────────────────────────
_DR_RE = re.compile(r"^Dr\.?\s+", re.IGNORECASE)


def _strip_title(name: str) -> tuple[str, str]:
    """Return (title, clean_name).  title is 'Dr' or ''."""
    name = name.strip()
    if _DR_RE.match(name):
        return "Dr", _DR_RE.sub("", name).strip()
    return "", name


def _normalise_phone(raw: str) -> str:
    """Convert a raw Moroccan phone string to +212XXXXXXXXX or '' if invalid."""
    digits = re.sub(r"\D", "", raw.strip())
    if not digits:
        return ""
    # Already has full international prefix
    if digits.startswith("212") and len(digits) == 12:
        return f"+{digits}"
    # 9-digit local number (most common)
    if len(digits) == 9:
        return f"+212{digits}"
    # 10-digit starting with 0 (e.g. 0522…)
    if len(digits) == 10 and digits.startswith("0"):
        return f"+212{digits[1:]}"
    # fallback: keep original digits prefixed, mark uncertain
    return f"+212{digits}" if 8 <= len(digits) <= 11 else ""


def _primary_speciality(raw: str) -> str:
    """Return the first speciality from a potentially comma-separated list."""
    parts = [s.strip() for s in raw.split(",") if s.strip()]
    return parts[0] if parts else ""


def _clean_description(raw: str) -> str:
    """Remove || separators, collapse whitespace, strip."""
    text = raw.replace("||", " ").replace("|", " — ")
    text = re.sub(r"\s{2,}", " ", text)
    return text.strip()


def _clean_image_url(url: str) -> str:
    """Return empty string for known placeholder images."""
    url = url.strip()
    return "" if url in _PLACEHOLDER_IMAGES else url


def _row_richness(row: dict) -> int:
    """Score a row by how many useful fields are filled (for dedup)."""
    score = 0
    for key in ("phone", "description", "image_url", "languages"):
        if row.get(key, "").strip():
            score += 1
    # Extra weight for description length
    desc = row.get("description", "")
    if len(desc) > 100:
        score += 2
    return score


# ── main ──────────────────────────────────────────────────
def main() -> None:
    if not RAW.is_file():
        print(f"ERROR: source file not found: {RAW}", file=sys.stderr)
        sys.exit(1)

    # 1. Read raw CSV (BOM-safe)
    with RAW.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        raw_rows: list[dict[str, str]] = list(reader)

    print(f"[1/13] Loaded {len(raw_rows):,} raw rows.")

    # 2. Drop useless columns
    drop_cols = {"email", "neighborhood", "coordinates"}
    for row in raw_rows:
        for col in drop_cols:
            row.pop(col, None)
    print(f"[2/13] Dropped columns: {', '.join(sorted(drop_cols))}")

    # 3. Normalise names ->(title, name)
    for row in raw_rows:
        title, clean_name = _strip_title(row["name"])
        row["title"] = title
        row["name"] = clean_name
    titled = sum(1 for r in raw_rows if r["title"])
    print(f"[3/13] Extracted title for {titled:,} doctors (Dr ->title column).")

    # 4. Standardise phone numbers
    invalid_phones = 0
    for row in raw_rows:
        original = row["phone"].strip()
        row["phone"] = _normalise_phone(original)
        if original and not row["phone"]:
            invalid_phones += 1
    print(f"[4/13] Standardised phones to +212XXXXXXXXX. {invalid_phones} invalid dropped.")

    # 5. Replace placeholder phones
    placeholder_count = 0
    for row in raw_rows:
        if row["phone"] in _PLACEHOLDER_PHONES:
            row["phone"] = ""
            placeholder_count += 1
    print(f"[5/13] Cleared {placeholder_count:,} placeholder phones.")

    # 6. Split speciality
    for row in raw_rows:
        row["primary_speciality"] = _primary_speciality(row["speciality"])
        # keep original as "specialities" (full list)
        row["specialities"] = row.pop("speciality")
    multi = sum(1 for r in raw_rows if "," in r["specialities"])
    print(f"[6/13] Extracted primary_speciality. {multi:,} multi-speciality entries preserved.")

    # 7. Normalise city names
    city_fixed = 0
    for row in raw_rows:
        city = row["city"].strip()
        normalised = _CITY_NORMALIZE.get(city, city)
        if normalised != city:
            city_fixed += 1
        row["city"] = normalised
    print(f"[7/13] Normalised city names. Fixed {city_fixed:,} entries.")

    # 8. Normalise speciality names
    spec_fixed = 0
    unique_before = len({r["primary_speciality"] for r in raw_rows})
    for row in raw_rows:
        ps = row["primary_speciality"].strip()
        normalised = _SPECIALITY_NORMALIZE.get(ps, ps)
        if normalised != ps:
            spec_fixed += 1
        row["primary_speciality"] = normalised
        # Also normalise each entry in the full specialities list
        parts = [s.strip() for s in row["specialities"].split(",") if s.strip()]
        row["specialities"] = ", ".join(
            _SPECIALITY_NORMALIZE.get(s, s) for s in parts
        )
    unique_after = len({r["primary_speciality"] for r in raw_rows})
    print(f"[8/13] Normalised specialities: {unique_before} ->{unique_after} unique. Fixed {spec_fixed:,} entries.")

    # 9. Clean description and image_url
    placeholder_cleared = 0
    for row in raw_rows:
        row["description"] = _clean_description(row["description"])
        cleaned_url = _clean_image_url(row["image_url"])
        if row["image_url"].strip() and not cleaned_url:
            placeholder_cleared += 1
        row["image_url"] = cleaned_url
    print(f"[9/13] Cleaned descriptions. Cleared {placeholder_cleared:,} placeholder images.")

    # 10. Drop near-empty columns (timetable 90.6%, cabinet_name 85.2%)
    drop_sparse = {"timetable", "cabinet_name"}
    for row in raw_rows:
        for col in drop_sparse:
            row.pop(col, None)
    print(f"[10/13] Dropped near-empty columns: {', '.join(sorted(drop_sparse))}")

    # 11. Deduplicate (name + city) — keep the richest row
    seen: dict[tuple[str, str], dict] = {}
    dupes_removed = 0
    for row in raw_rows:
        key = (row["name"].lower().strip(), row["city"].lower().strip())
        if key in seen:
            existing = seen[key]
            if _row_richness(row) > _row_richness(existing):
                seen[key] = row
            dupes_removed += 1
        else:
            seen[key] = row

    clean_rows = list(seen.values())
    print(f"[11/13] Deduplicated: removed {dupes_removed:,} duplicates ->{len(clean_rows):,} unique doctors.")

    # 12. Clear shared image_url / profile_url (same URL on multiple doctors = fake data)
    from collections import Counter as _Counter
    image_counts   = _Counter(r["image_url"]   for r in clean_rows if r.get("image_url",   "").strip())
    profile_counts = _Counter(r["profile_url"] for r in clean_rows if r.get("profile_url", "").strip())
    shared_images   = {url for url, n in image_counts.items()   if n > 1}
    shared_profiles = {url for url, n in profile_counts.items() if n > 1}
    img_cleared = prof_cleared = 0
    for row in clean_rows:
        if row.get("image_url", "") in shared_images:
            row["image_url"] = ""
            img_cleared += 1
        if row.get("profile_url", "") in shared_profiles:
            row["profile_url"] = ""
            prof_cleared += 1
    print(
        f"[12/13] Cleared {img_cleared:,} shared image_urls "
        f"({len(shared_images)} unique duplicated URLs) and "
        f"{prof_cleared:,} shared profile_urls "
        f"({len(shared_profiles)} unique duplicated URLs)."
    )

    # 13. Strip all remaining fields and write
    output_columns = [
        "title",
        "name",
        "primary_speciality",
        "specialities",
        "phone",
        "address",
        "city",
        "description",
        "languages",
        "image_url",
        "profile_url",
        "source_site",
    ]

    with OUT.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=output_columns, extrasaction="ignore")
        writer.writeheader()
        for row in clean_rows:
            stripped = {k: row.get(k, "").strip() for k in output_columns}
            writer.writerow(stripped)

    print(f"[13/13] Wrote {len(clean_rows):,} rows ->{OUT.name}")
    print()

    # ── summary stats ─────────────────────────────────────
    print("=" * 55)
    print("  CLEAN DATA SUMMARY")
    print("=" * 55)
    print(f"  Rows            : {len(clean_rows):,}")
    print(f"  Columns         : {len(output_columns)}")

    for col in output_columns:
        filled = sum(1 for r in clean_rows if r.get(col, "").strip())
        pct = round(100 * filled / len(clean_rows), 1)
        print(f"  {col:22s}: {filled:>5,} filled ({pct:>5}%)")

    from collections import Counter
    cities = Counter(r["city"] for r in clean_rows)
    print(f"\n  Top 5 cities: {', '.join(f'{c} ({n})' for c, n in cities.most_common(5))}")
    specs = Counter(r["primary_speciality"] for r in clean_rows)
    print(f"  Top 5 specialities: {', '.join(f'{s} ({n})' for s, n in specs.most_common(5))}")
    print("=" * 55)


if __name__ == "__main__":
    main()
