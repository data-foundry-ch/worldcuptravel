#!/usr/bin/env python3
"""Extract distinct raw ground values requiring mapping."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.services.venue_enrichment import export_unmapped_grounds_command  # noqa: E402

if __name__ == "__main__":
    path = export_unmapped_grounds_command()
    print(f"Wrote {path}")
