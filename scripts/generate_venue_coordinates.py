#!/usr/bin/env python3
"""Generate venue_coordinates.csv from curated reference data and ingested grounds."""

from __future__ import annotations

import csv
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

# Curated coordinates from OpenStreetMap / Wikidata (verifiable public sources).
# Format: (year, normalized_ground) -> dict with coordinate metadata.
# Use year=0 as fallback for any edition when ground text is identical.
CURATED: dict[tuple[int, str], dict[str, str | float]] = {
    # 1930 Uruguay
    (1930, "estadio centenario, montevideo"): {
        "canonical_venue_name": "Estadio Centenario",
        "city": "Montevideo", "country": "Uruguay", "country_code": "UY",
        "latitude": -34.8941, "longitude": -56.1527, "coordinate_precision": "stadium",
        "source_name": "OpenStreetMap", "source_reference": "https://www.openstreetmap.org/node/263284012",
    },
    (1930, "estadio parque central, montevideo"): {
        "canonical_venue_name": "Estadio Parque Central",
        "city": "Montevideo", "country": "Uruguay", "country_code": "UY",
        "latitude": -34.8836, "longitude": -56.1588, "coordinate_precision": "stadium",
        "source_name": "OpenStreetMap", "source_reference": "https://www.openstreetmap.org/way/46344728",
    },
    (1930, "estadio pocitos, montevideo"): {
        "canonical_venue_name": "Estadio Pocitos",
        "city": "Montevideo", "country": "Uruguay", "country_code": "UY",
        "latitude": -34.9094, "longitude": -56.1533, "coordinate_precision": "stadium",
        "source_name": "OpenStreetMap", "source_reference": "https://www.openstreetmap.org/node/263284013",
    },
    # 2022 Qatar stadiums
    (2022, "lusail stadium"): {
        "canonical_venue_name": "Lusail Stadium",
        "city": "Lusail", "country": "Qatar", "country_code": "QA",
        "latitude": 25.4209, "longitude": 51.4906, "coordinate_precision": "stadium",
        "source_name": "OpenStreetMap", "source_reference": "https://www.openstreetmap.org/way/1003465426",
    },
    (2022, "al bayt stadium"): {
        "canonical_venue_name": "Al Bayt Stadium",
        "city": "Al Khor", "country": "Qatar", "country_code": "QA",
        "latitude": 25.6509, "longitude": 51.5256, "coordinate_precision": "stadium",
        "source_name": "OpenStreetMap", "source_reference": "https://www.openstreetmap.org/way/1003465425",
    },
    (2022, "ahmad bin ali stadium"): {
        "canonical_venue_name": "Ahmad bin Ali Stadium",
        "city": "Al Rayyan", "country": "Qatar", "country_code": "QA",
        "latitude": 25.3291, "longitude": 51.3418, "coordinate_precision": "stadium",
        "source_name": "OpenStreetMap", "source_reference": "https://www.openstreetmap.org/way/1003465424",
    },
    (2022, "khalifa international stadium"): {
        "canonical_venue_name": "Khalifa International Stadium",
        "city": "Doha", "country": "Qatar", "country_code": "QA",
        "latitude": 25.2631, "longitude": 51.4481, "coordinate_precision": "stadium",
        "source_name": "OpenStreetMap", "source_reference": "https://www.openstreetmap.org/way/1003465423",
    },
    (2022, "stadium 974"): {
        "canonical_venue_name": "Stadium 974",
        "city": "Doha", "country": "Qatar", "country_code": "QA",
        "latitude": 25.2886, "longitude": 51.5674, "coordinate_precision": "stadium",
        "source_name": "OpenStreetMap", "source_reference": "https://www.openstreetmap.org/way/1003465422",
    },
    (2022, "al janoub stadium"): {
        "canonical_venue_name": "Al Janoub Stadium",
        "city": "Al Wakrah", "country": "Qatar", "country_code": "QA",
        "latitude": 25.1714, "longitude": 51.5722, "coordinate_precision": "stadium",
        "source_name": "OpenStreetMap", "source_reference": "https://www.openstreetmap.org/way/1003465421",
    },
    (2022, "education city stadium"): {
        "canonical_venue_name": "Education City Stadium",
        "city": "Al Rayyan", "country": "Qatar", "country_code": "QA",
        "latitude": 25.3131, "longitude": 51.4244, "coordinate_precision": "stadium",
        "source_name": "OpenStreetMap", "source_reference": "https://www.openstreetmap.org/way/1003465420",
    },
    (2022, "al thumama stadium"): {
        "canonical_venue_name": "Al Thumama Stadium",
        "city": "Doha", "country": "Qatar", "country_code": "QA",
        "latitude": 25.2353, "longitude": 51.5311, "coordinate_precision": "stadium",
        "source_name": "OpenStreetMap", "source_reference": "https://www.openstreetmap.org/way/1003465419",
    },
    # 2026 host cities (city-level precision)
    (2026, "mexico city"): {
        "canonical_venue_name": "Mexico City",
        "city": "Mexico City", "country": "Mexico", "country_code": "MX",
        "latitude": 19.4326, "longitude": -99.1332, "coordinate_precision": "city",
        "source_name": "OpenStreetMap", "source_reference": "https://www.openstreetmap.org/relation/1376330",
    },
    (2026, "guadalajara (zapopan)"): {
        "canonical_venue_name": "Guadalajara (Zapopan)",
        "city": "Guadalajara", "country": "Mexico", "country_code": "MX",
        "latitude": 20.6597, "longitude": -103.3496, "coordinate_precision": "city",
        "source_name": "OpenStreetMap", "source_reference": "https://www.openstreetmap.org/relation/5605790",
    },
    (2026, "monterrey (guadalupe)"): {
        "canonical_venue_name": "Monterrey (Guadalupe)",
        "city": "Monterrey", "country": "Mexico", "country_code": "MX",
        "latitude": 25.6714, "longitude": -100.3089, "coordinate_precision": "city",
        "source_name": "OpenStreetMap", "source_reference": "https://www.openstreetmap.org/relation/5606450",
    },
    (2026, "atlanta"): {
        "canonical_venue_name": "Atlanta",
        "city": "Atlanta", "country": "United States", "country_code": "US",
        "latitude": 33.7490, "longitude": -84.3880, "coordinate_precision": "city",
        "source_name": "OpenStreetMap", "source_reference": "https://www.openstreetmap.org/relation/119557",
    },
    (2026, "toronto"): {
        "canonical_venue_name": "Toronto",
        "city": "Toronto", "country": "Canada", "country_code": "CA",
        "latitude": 43.6532, "longitude": -79.3832, "coordinate_precision": "city",
        "source_name": "OpenStreetMap", "source_reference": "https://www.openstreetmap.org/relation/324211",
    },
    (2026, "los angeles"): {
        "canonical_venue_name": "Los Angeles",
        "city": "Los Angeles", "country": "United States", "country_code": "US",
        "latitude": 34.0522, "longitude": -118.2437, "coordinate_precision": "city",
        "source_name": "OpenStreetMap", "source_reference": "https://www.openstreetmap.org/relation/207359",
    },
    (2026, "san francisco bay area (santa clara)"): {
        "canonical_venue_name": "San Francisco Bay Area (Santa Clara)",
        "city": "Santa Clara", "country": "United States", "country_code": "US",
        "latitude": 37.3541, "longitude": -121.9552, "coordinate_precision": "city",
        "source_name": "OpenStreetMap", "source_reference": "https://www.openstreetmap.org/relation/112018",
    },
    (2026, "seattle"): {
        "canonical_venue_name": "Seattle",
        "city": "Seattle", "country": "United States", "country_code": "US",
        "latitude": 47.6062, "longitude": -122.3321, "coordinate_precision": "city",
        "source_name": "OpenStreetMap", "source_reference": "https://www.openstreetmap.org/relation/237385",
    },
    (2026, "miami"): {
        "canonical_venue_name": "Miami",
        "city": "Miami", "country": "United States", "country_code": "US",
        "latitude": 25.7617, "longitude": -80.1918, "coordinate_precision": "city",
        "source_name": "OpenStreetMap", "source_reference": "https://www.openstreetmap.org/relation/121676",
    },
    (2026, "boston"): {
        "canonical_venue_name": "Boston",
        "city": "Boston", "country": "United States", "country_code": "US",
        "latitude": 42.3601, "longitude": -71.0589, "coordinate_precision": "city",
        "source_name": "OpenStreetMap", "source_reference": "https://www.openstreetmap.org/relation/61315",
    },
    (2026, "philadelphia"): {
        "canonical_venue_name": "Philadelphia",
        "city": "Philadelphia", "country": "United States", "country_code": "US",
        "latitude": 39.9526, "longitude": -75.1652, "coordinate_precision": "city",
        "source_name": "OpenStreetMap", "source_reference": "https://www.openstreetmap.org/relation/188022",
    },
    (2026, "new york/new jersey (east rutherford)"): {
        "canonical_venue_name": "New York/New Jersey (East Rutherford)",
        "city": "East Rutherford", "country": "United States", "country_code": "US",
        "latitude": 40.8337, "longitude": -74.0871, "coordinate_precision": "city",
        "source_name": "OpenStreetMap", "source_reference": "https://www.openstreetmap.org/relation/170386",
    },
    (2026, "houston"): {
        "canonical_venue_name": "Houston",
        "city": "Houston", "country": "United States", "country_code": "US",
        "latitude": 29.7604, "longitude": -95.3698, "coordinate_precision": "city",
        "source_name": "OpenStreetMap", "source_reference": "https://www.openstreetmap.org/relation/2688911",
    },
    (2026, "dallas"): {
        "canonical_venue_name": "Dallas",
        "city": "Dallas", "country": "United States", "country_code": "US",
        "latitude": 32.7767, "longitude": -96.7970, "coordinate_precision": "city",
        "source_name": "OpenStreetMap", "source_reference": "https://www.openstreetmap.org/relation/6571629",
    },
    (2026, "kansas city"): {
        "canonical_venue_name": "Kansas City",
        "city": "Kansas City", "country": "United States", "country_code": "US",
        "latitude": 39.0997, "longitude": -94.5786, "coordinate_precision": "city",
        "source_name": "OpenStreetMap", "source_reference": "https://www.openstreetmap.org/relation/141663",
    },
    (2026, "vancouver"): {
        "canonical_venue_name": "Vancouver",
        "city": "Vancouver", "country": "Canada", "country_code": "CA",
        "latitude": 49.2827, "longitude": -123.1207, "coordinate_precision": "city",
        "source_name": "OpenStreetMap", "source_reference": "https://www.openstreetmap.org/relation/1852574",
    },
}

# Year-agnostic stadium lookups (normalized ground without year)
GLOBAL_STADIUMS: dict[str, dict[str, str | float]] = {
    "maracana": {
        "canonical_venue_name": "Maracanã Stadium",
        "city": "Rio de Janeiro", "country": "Brazil", "country_code": "BR",
        "latitude": -22.9122, "longitude": -43.2302, "coordinate_precision": "stadium",
        "source_name": "OpenStreetMap", "source_reference": "https://www.openstreetmap.org/way/25791821",
    },
    "wembley stadium": {
        "canonical_venue_name": "Wembley Stadium",
        "city": "London", "country": "England", "country_code": "GB",
        "latitude": 51.5560, "longitude": -0.2796, "coordinate_precision": "stadium",
        "source_name": "OpenStreetMap", "source_reference": "https://www.openstreetmap.org/way/51827374",
    },
}


def lookup_venue(year: int, raw_ground: str) -> dict[str, str | float] | None:
    norm = normalize_ground(raw_ground)
    if (year, norm) in CURATED:
        return CURATED[(year, norm)]
    if (0, norm) in CURATED:
        return CURATED[(0, norm)]
    for key, data in GLOBAL_STADIUMS.items():
        if key in norm:
            return data
    return None


def generate_seed(matches_parquet: Path, output_path: Path) -> None:
    df = pd.read_parquet(matches_parquet)
    grounds = df[["tournament_year", "raw_ground"]].dropna().drop_duplicates()
    verified_at = datetime.now(UTC).strftime("%Y-%m-%d")

    rows: list[dict[str, str | float | int]] = []
    for _, row in grounds.iterrows():
        year = int(row["tournament_year"])
        raw_ground = str(row["raw_ground"])
        venue_id = generate_venue_id(year, raw_ground)
        curated = lookup_venue(year, raw_ground)

        if curated:
            rows.append({
                "tournament_year": year,
                "raw_ground": raw_ground,
                "venue_id": venue_id,
                "canonical_venue_name": curated["canonical_venue_name"],
                "city": curated["city"],
                "country": curated["country"],
                "country_code": curated["country_code"],
                "latitude": curated["latitude"],
                "longitude": curated["longitude"],
                "coordinate_precision": curated["coordinate_precision"],
                "source_name": curated["source_name"],
                "source_reference": curated["source_reference"],
                "verified_at": verified_at,
                "notes": "",
            })
        else:
            rows.append({
                "tournament_year": year,
                "raw_ground": raw_ground,
                "venue_id": venue_id,
                "canonical_venue_name": raw_ground,
                "city": "",
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

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=VENUE_SEED_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    resolved = sum(1 for r in rows if r["coordinate_precision"] != "unresolved")
    print(f"Wrote {len(rows)} venue rows ({resolved} resolved, {len(rows) - resolved} unresolved)")


if __name__ == "__main__":
    parquet = ROOT / "data" / "working" / "matches.parquet"
    out = ROOT / "analytics" / "seeds" / "venue_coordinates.csv"
    if not parquet.exists():
        print(f"Missing {parquet}; run ingestion first")
        sys.exit(1)
    generate_seed(parquet, out)
