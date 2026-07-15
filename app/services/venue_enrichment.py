"""Venue coordinate enrichment utilities."""

from __future__ import annotations

import hashlib
import json
import logging
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from app.settings import Settings, get_settings

logger = logging.getLogger(__name__)

VENUE_SEED_COLUMNS = [
    "tournament_year",
    "raw_ground",
    "venue_id",
    "canonical_venue_name",
    "city",
    "country",
    "country_code",
    "latitude",
    "longitude",
    "coordinate_precision",
    "source_name",
    "source_reference",
    "verified_at",
    "notes",
]

ALLOWED_PRECISION = {"stadium", "city", "metro", "approximate", "unresolved"}


def normalize_ground(raw_ground: str | None) -> str:
    if not raw_ground:
        return ""
    text = raw_ground.strip().lower()
    text = re.sub(r"\s+", " ", text)
    text = text.replace("–", "-").replace("—", "-")
    return text


def make_venue_key(tournament_year: int, raw_ground: str | None) -> str:
    return f"{tournament_year}|{normalize_ground(raw_ground)}"


def generate_venue_id(tournament_year: int, raw_ground: str) -> str:
    key = make_venue_key(tournament_year, raw_ground)
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]


def load_venue_seed(seed_path: Path) -> pd.DataFrame:
    if not seed_path.exists():
        return pd.DataFrame(columns=VENUE_SEED_COLUMNS)
    df = pd.read_csv(seed_path, dtype=str)
    for col in VENUE_SEED_COLUMNS:
        if col not in df.columns:
            df[col] = None
    return df[VENUE_SEED_COLUMNS]


def load_venue_aliases(alias_path: Path) -> pd.DataFrame:
    columns = ["tournament_year", "raw_ground_alias", "raw_ground_canonical", "notes"]
    if not alias_path.exists():
        return pd.DataFrame(columns=columns)
    return pd.read_csv(alias_path, dtype=str)


def extract_distinct_grounds(matches_parquet: Path) -> pd.DataFrame:
    df = pd.read_parquet(matches_parquet)
    grounds = (
        df[["tournament_year", "raw_ground"]]
        .dropna(subset=["raw_ground"])
        .drop_duplicates()
        .sort_values(["tournament_year", "raw_ground"])
        .reset_index(drop=True)
    )
    return grounds


def build_venue_coverage_report(
    matches_parquet: Path,
    seed_path: Path,
    alias_path: Path,
    reports_dir: Path,
) -> dict[str, Any]:
    reports_dir.mkdir(parents=True, exist_ok=True)
    grounds_df = extract_distinct_grounds(matches_parquet)
    seed_df = load_venue_seed(seed_path)
    alias_df = load_venue_aliases(alias_path)

    seed_df["lookup_key"] = seed_df.apply(
        lambda r: make_venue_key(int(r["tournament_year"]), r["raw_ground"]), axis=1
    )
    seed_lookup: dict[str, dict[str, Any]] = {}
    for _, srow in seed_df.iterrows():
        seed_lookup[str(srow["lookup_key"])] = {str(k): v for k, v in srow.to_dict().items()}

    alias_lookup: dict[str, str] = {}
    for _, row in alias_df.iterrows():
        alias_key = make_venue_key(int(row["tournament_year"]), row["raw_ground_alias"])
        alias_lookup[alias_key] = row["raw_ground_canonical"]

    unmapped_rows: list[dict[str, Any]] = []
    per_edition: dict[str, dict[str, int]] = {}
    resolved = 0
    unresolved = 0

    for _, row in grounds_df.iterrows():
        year = int(row["tournament_year"])
        raw_ground = row["raw_ground"]
        key = make_venue_key(year, raw_ground)

        canonical_ground = raw_ground
        if key in alias_lookup:
            canonical_ground = alias_lookup[key]
            key = make_venue_key(year, canonical_ground)

        edition_key = str(year)
        if edition_key not in per_edition:
            per_edition[edition_key] = {"total": 0, "resolved": 0, "unresolved": 0}
        per_edition[edition_key]["total"] += 1

        seed_row = seed_lookup.get(key)
        if seed_row and seed_row.get("coordinate_precision") != "unresolved":
            lat = seed_row.get("latitude")
            lon = seed_row.get("longitude")
            if lat and lon and str(lat).strip() and str(lon).strip():
                resolved += 1
                per_edition[edition_key]["resolved"] += 1
                continue

        unresolved += 1
        per_edition[edition_key]["unresolved"] += 1
        unmapped_rows.append(
            {
                "tournament_year": year,
                "raw_ground": raw_ground,
                "normalized_ground": normalize_ground(raw_ground),
                "venue_id": generate_venue_id(year, canonical_ground),
            }
        )

    unmapped_path = reports_dir / "unmapped_venues.csv"
    pd.DataFrame(unmapped_rows).to_csv(unmapped_path, index=False)

    coverage = {
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "total_distinct_venues": len(grounds_df),
        "resolved_count": resolved,
        "unresolved_count": unresolved,
        "coverage_pct": round(100 * resolved / len(grounds_df), 2) if len(grounds_df) else 0,
        "per_edition": per_edition,
    }

    coverage_path = reports_dir / "venue_coverage.json"
    coverage_path.write_text(json.dumps(coverage, indent=2), encoding="utf-8")
    logger.info(
        "Venue coverage: %s resolved, %s unresolved of %s",
        resolved,
        unresolved,
        len(grounds_df),
    )
    return coverage


def export_unmapped_grounds_command(
    matches_parquet: Path | None = None,
    output_path: Path | None = None,
    settings: Settings | None = None,
) -> Path:
    settings = settings or get_settings()
    matches_parquet = matches_parquet or settings.working_data_dir / "matches.parquet"
    output_path = output_path or settings.reports_dir / "grounds_to_map.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    grounds = extract_distinct_grounds(matches_parquet)
    grounds["normalized_ground"] = grounds["raw_ground"].map(normalize_ground)
    grounds["venue_id"] = grounds.apply(
        lambda r: generate_venue_id(int(r["tournament_year"]), r["raw_ground"]), axis=1
    )
    grounds.to_csv(output_path, index=False)
    return output_path
