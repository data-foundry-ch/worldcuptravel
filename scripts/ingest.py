#!/usr/bin/env python3
"""Run OpenFootball ingestion."""

import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.services.ingestion import IngestionService  # noqa: E402

logging.basicConfig(level=logging.INFO)

if __name__ == "__main__":
    use_local = "--local-only" in sys.argv
    service = IngestionService()
    manifest = service.run(use_local_only=use_local)
    failed = [d for d in manifest.downloads if d.error]
    print(f"Ingested {manifest.total_matches} matches; {len(failed)} download errors")
    sys.exit(1 if failed and manifest.total_matches == 0 else 0)
