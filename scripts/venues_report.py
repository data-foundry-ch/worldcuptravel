#!/usr/bin/env python3
"""Run venue coverage report."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.services.venue_enrichment import build_venue_coverage_report  # noqa: E402
from app.settings import get_settings  # noqa: E402

if __name__ == "__main__":
    settings = get_settings()
    coverage = build_venue_coverage_report(
        settings.working_data_dir / "matches.parquet",
        settings.analytics_dir / "seeds" / "venue_coordinates.csv",
        settings.analytics_dir / "seeds" / "venue_aliases.csv",
        settings.reports_dir,
    )
    print(f"Coverage: {coverage['coverage_pct']}% ({coverage['resolved_count']}/{coverage['total_distinct_venues']})")
