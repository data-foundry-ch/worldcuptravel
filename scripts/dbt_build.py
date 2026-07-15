#!/usr/bin/env python3
"""Run dbt build."""

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.services.data_refresh import run_dbt_build  # noqa: E402
from app.settings import get_settings  # noqa: E402

if __name__ == "__main__":
    settings = get_settings()
    settings.duckdb_path.parent.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("DUCKDB_PATH", str(settings.duckdb_path.resolve()))
    os.environ.setdefault(
        "MATCHES_PARQUET_PATH", str((settings.working_data_dir / "matches.parquet").resolve())
    )
    meta = run_dbt_build(settings)
    print(f"dbt build {'succeeded' if meta['success'] else 'failed'}")
    sys.exit(0 if meta["success"] else 1)
