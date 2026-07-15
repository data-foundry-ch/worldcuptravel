#!/usr/bin/env python3
"""Build full venue_coordinates.csv from curated stadium and city reference data."""

from __future__ import annotations

import csv
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.services.venue_enrichment import (  # noqa: E402
    VENUE_SEED_COLUMNS,
    generate_venue_id,
    normalize_ground,
)

DATA_FILE = Path(__file__).parent / "venue_reference_data.json"


def load_reference() -> dict:
    return json.loads(DATA_FILE.read_text(encoding="utf-8"))


def extract_city(raw_ground: str) -> str | None:
    if "," in raw_ground:
        return raw_ground.split(",")[-1].strip()
    return None


def lookup(ref: dict, year: int, raw_ground: str) -> dict | None:
    norm = normalize_ground(raw_ground)
    stadiums = ref.get("stadiums", {})
    cities = ref.get("cities", {})

    for key in [f"{year}|{norm}", f"0|{norm}", norm]:
        if key in stadiums:
            data = dict(stadiums[key])
            data["coordinate_precision"] = data.get("coordinate_precision", "stadium")
            return data

    city = extract_city(raw_ground)
    if city:
        city_norm = normalize_ground(city)
        if city_norm in cities:
            data = dict(cities[city_norm])
            data["coordinate_precision"] = "city"
            data["canonical_venue_name"] = raw_ground
            return data

    if norm in cities:
        data = dict(cities[norm])
        data["coordinate_precision"] = "city"
        data["canonical_venue_name"] = raw_ground
        return data

    return None


def main() -> None:
    ref = load_reference()
    parquet = ROOT / "data" / "working" / "matches.parquet"
    out = ROOT / "analytics" / "seeds" / "venue_coordinates.csv"
    verified_at = datetime.now(UTC).strftime("%Y-%m-%d")

    df = pd.read_parquet(parquet)
    grounds = df[["tournament_year", "raw_ground"]].dropna().drop_duplicates()

    rows: list[dict] = []
    for _, row in grounds.iterrows():
        year = int(row["tournament_year"])
        raw_ground = str(row["raw_ground"])
        venue_id = generate_venue_id(year, raw_ground)
        match = lookup(ref, year, raw_ground)

        if match:
            rows.append({
                "tournament_year": year,
                "raw_ground": raw_ground,
                "venue_id": venue_id,
                "canonical_venue_name": match.get("canonical_venue_name", raw_ground),
                "city": match.get("city", ""),
                "country": match.get("country", ""),
                "country_code": match.get("country_code", ""),
                "latitude": match["latitude"],
                "longitude": match["longitude"],
                "coordinate_precision": match.get("coordinate_precision", "stadium"),
                "source_name": match.get("source_name", "OpenStreetMap"),
                "source_reference": match.get("source_reference", ""),
                "verified_at": verified_at,
                "notes": match.get("notes", ""),
            })
        else:
            rows.append({
                "tournament_year": year,
                "raw_ground": raw_ground,
                "venue_id": venue_id,
                "canonical_venue_name": raw_ground,
                "city": extract_city(raw_ground) or "",
                "country": "",
                "country_code": "",
                "latitude": "",
                "longitude": "",
                "coordinate_precision": "unresolved",
                "source_name": "",
                "source_reference": "",
                "verified_at": "",
                "notes": "Requires manual coordinate mapping",
            })

    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=VENUE_SEED_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    resolved = sum(1 for r in rows if r["coordinate_precision"] != "unresolved")
    print(f"Wrote {len(rows)} rows: {resolved} resolved, {len(rows)-resolved} unresolved")


if __name__ == "__main__":
    main()
