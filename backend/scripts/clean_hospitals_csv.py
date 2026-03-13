#!/usr/bin/env python3
"""Clean and unify Moroccan public health facility CSVs.

Reads:
  - backend/repartition-des-hopitaux-par-region-et-province-2024.csv
  - backend/etablissements-de-soins-de-sante-primaire-2024.csv

Writes:
  - backend/health_facilities_clean.csv

Run from repo root:
    python backend/scripts/clean_hospitals_csv.py
"""

from __future__ import annotations

import csv
import re
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
_BACKEND = Path(__file__).resolve().parent.parent
HOSPITALS_CSV = _BACKEND / "repartition-des-hopitaux-par-region-et-province-2024.csv"
PRIMARY_CSV   = _BACKEND / "etablissements-de-soins-de-sante-primaire-2024.csv"
OUTPUT_CSV    = _BACKEND / "health_facilities_clean.csv"

# ---------------------------------------------------------------------------
# Category code → full French name
# ---------------------------------------------------------------------------
CATEGORY_NAMES: dict[str, str] = {
    # Hospitals
    "HP":     "Hôpital Préfectoral",
    "HPr":    "Hôpital de Proximité",
    "HR":     "Hôpital Régional",
    "HIR":    "Hôpital Intégré de Référence",
    "CPU":    "Centre Psychiatrique Universitaire",
    "HPsyR":  "Hôpital Psychiatrique Régional",
    "HPsyP":  "Hôpital Psychiatrique Préfectoral",
    "CRO":    "Centre Régional d'Oncologie",
    # Primary care
    "CSU-1":  "Centre de Santé Urbain niveau 1",
    "CSU-2":  "Centre de Santé Urbain niveau 2",
    "CSR-1":  "Centre de Santé Rural niveau 1",
    "CSR-2":  "Centre de Santé Rural niveau 2",
    "DR":     "Dispensaire Rural",
    "LSP":    "Laboratoire de Santé Publique",
    "CRSR":   "Centre de Référence en Santé de Reproduction",
    "CDTMR":  "Centre de Diagnostic et de Traitement des Maladies Respiratoires",
}

# ---------------------------------------------------------------------------
# Category code → relevant medical departments (for RAG matching)
# ---------------------------------------------------------------------------
CATEGORY_DEPARTMENTS: dict[str, str] = {
    "HR":    "Médecine générale,Chirurgie,Pédiatrie,Gynécologie,Cardiologie,Neurologie,Urgences,Radiologie,Laboratoire,Maternité",
    "HIR":   "Médecine générale,Chirurgie,Pédiatrie,Gynécologie,Cardiologie,Neurologie,Urgences,Radiologie,Laboratoire,Réanimation,Maternité",
    "HP":    "Médecine générale,Chirurgie,Pédiatrie,Gynécologie,Urgences,Laboratoire,Radiologie",
    "HPr":   "Médecine générale,Soins d'urgence,Laboratoire,Pédiatrie",
    "CRO":   "Oncologie,Chimiothérapie,Radiothérapie,Hématologie oncologie",
    "CPU":   "Psychiatrie,Santé mentale,Addictologie",
    "HPsyR": "Psychiatrie,Santé mentale,Addictologie",
    "HPsyP": "Psychiatrie,Santé mentale",
    "CRSR":  "Gynécologie,Santé de la reproduction,Planification familiale,Maternité",
    "CDTMR": "Pneumologie,Maladies respiratoires,Tuberculose,CDTMR",
    "LSP":   "Laboratoire d'analyses médicales",
    "CSU-1": "Médecine générale,Soins de base,Vaccination,Planning familial,Consultation infirmière",
    "CSU-2": "Médecine générale,Soins de base,Vaccination,Planning familial,Consultation infirmière",
    "CSR-1": "Médecine générale,Soins de base,Vaccination,Soins infirmiers",
    "CSR-2": "Médecine générale,Soins de base,Vaccination,Soins infirmiers",
    "DR":    "Soins de base,Soins d'urgence élémentaires",
}

# ---------------------------------------------------------------------------
# facility_type bucket
# ---------------------------------------------------------------------------
HOSPITAL_CODES = {"HP", "HPr", "HR", "HIR", "CPU", "HPsyR", "HPsyP", "CRO"}
PRIMARY_CODES  = {"CSU-1", "CSU-2", "CSR-1", "CSR-2", "DR", "LSP", "CRSR", "CDTMR"}


def _clean_str(s: str) -> str:
    """Strip whitespace and remove trailing junk like (Mun.) / (Arrond.)."""
    s = s.strip()
    s = re.sub(r"\s*\(Mun\.\)|\s*\(Arrond\.\)", "", s)
    return s.strip()


def _facility_type(code: str) -> str:
    if code in HOSPITAL_CODES:
        return "Hôpital"
    if code in PRIMARY_CODES:
        return "Soins primaires"
    return "Établissement de santé"


def _read_raw_csv(path: Path) -> list[dict]:
    """Read a raw ministry CSV, skipping the first 3 junk rows.

    The files have:
      row 0 – long title
      row 1 – blank
      row 2 – real header (Région, Délegation, Commune, Nom, Catégorie, ...)
      row 3+ – data
    """
    rows: list[dict] = []
    with open(path, encoding="utf-8-sig") as f:
        # Skip rows 0 and 1
        next(f)
        next(f)
        reader = csv.DictReader(f)
        for row in reader:
            # Skip blank rows (all key values empty)
            values = [v.strip() for v in row.values()]
            if not any(values):
                continue
            rows.append(row)
    return rows


def _ascii(s: str) -> str:
    """Lowercase + strip common French accents for fuzzy header matching."""
    s = s.lower()
    for accented, plain in [
        ("éèêë", "e"), ("àâä", "a"), ("îï", "i"), ("ôö", "o"), ("ùûü", "u"), ("ç", "c"),
    ]:
        for ch in accented:
            s = s.replace(ch, plain)
    return s


def _normalise_row(row: dict) -> dict | None:
    """Return a clean, normalised facility record or None to skip."""
    def get(*keys: str) -> str:
        for k in keys:
            k_ascii = _ascii(k)
            for rk in row:
                if rk and k_ascii in _ascii(rk):
                    return _clean_str(row[rk])
        return ""

    region      = get("région", "region")
    delegation  = get("déleg", "delegation")
    commune     = get("commune")
    name        = get("établissement", "nom établissement", "nom")
    category    = get("catégorie", "categorie")

    # Skip rows where name or category is missing/junk
    if not name or not category or name.lower() in ("établissement hospitalier", "nom établissement"):
        return None

    category = category.strip()
    cat_name = CATEGORY_NAMES.get(category, category)
    departments = CATEGORY_DEPARTMENTS.get(category, "Soins de santé")
    ftype = _facility_type(category)

    return {
        "name":          name,
        "region":        region,
        "delegation":    delegation,
        "commune":       commune,
        "category_code": category,
        "category_name": cat_name,
        "facility_type": ftype,
        "departments":   departments,
    }


def clean() -> None:
    records: list[dict] = []
    seen: set[tuple] = set()

    for path in (HOSPITALS_CSV, PRIMARY_CSV):
        if not path.is_file():
            print(f"WARNING: file not found, skipping: {path}")
            continue
        raw = _read_raw_csv(path)
        print(f"  {path.name}: {len(raw)} raw rows")
        for row in raw:
            rec = _normalise_row(row)
            if rec is None:
                continue
            key = (rec["name"].lower(), rec["delegation"].lower(), rec["category_code"])
            if key in seen:
                continue
            seen.add(key)
            records.append(rec)

    fieldnames = [
        "name", "region", "delegation", "commune",
        "category_code", "category_name", "facility_type", "departments",
    ]
    with open(OUTPUT_CSV, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)

    print(f"\nWrote {len(records):,} facilities → {OUTPUT_CSV}")

    # --- summary by type ---
    from collections import Counter
    by_type = Counter(r["facility_type"] for r in records)
    by_cat  = Counter(r["category_code"] for r in records)
    print("\nBy type:")
    for t, n in sorted(by_type.items()):
        print(f"  {t:30s} {n:>5}")
    print("\nBy category code:")
    for c, n in sorted(by_cat.items(), key=lambda x: -x[1]):
        print(f"  {c:10s} {CATEGORY_NAMES.get(c, c):50s} {n:>5}")


if __name__ == "__main__":
    clean()
