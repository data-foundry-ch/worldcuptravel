"""Data refresh and dbt build orchestration."""

from __future__ import annotations

import json
import logging
import shutil
import subprocess
import tempfile
from datetime import UTC, datetime
from pathlib import Path

from app.services.ingestion import IngestionService
from app.services.venue_enrichment import build_venue_coverage_report
from app.settings import Settings, get_settings

logger = logging.getLogger(__name__)


def _dbt_executable() -> str:
    """Return the dbt CLI path installed by dbt-core (not runnable via python -m dbt)."""
    dbt = shutil.which("dbt")
    if dbt:
        return dbt
    raise RuntimeError(
        "dbt executable not found on PATH. Install dbt-core and dbt-duckdb."
    )


def run_dbt_build(settings: Settings | None = None) -> dict[str, object]:
    settings = settings or get_settings()
    analytics_dir = settings.analytics_dir
    env = {
        **dict(__import__("os").environ),
        "DBT_PROFILES_DIR": str(analytics_dir),
        "DUCKDB_PATH": str(settings.duckdb_path.resolve()),
        "MATCHES_PARQUET_PATH": str(
            (settings.working_data_dir / "matches.parquet").resolve()
        ),
    }

    result = subprocess.run(
        [
            _dbt_executable(),
            "build",
            "--project-dir",
            str(analytics_dir),
            "--profiles-dir",
            str(analytics_dir),
        ],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )

    meta = {
        "built_at_utc": datetime.now(UTC).isoformat(),
        "success": result.returncode == 0,
        "returncode": result.returncode,
        "stdout_tail": result.stdout[-4000:] if result.stdout else "",
        "stderr_tail": result.stderr[-4000:] if result.stderr else "",
    }

    settings.working_data_dir.mkdir(parents=True, exist_ok=True)
    settings.dbt_build_meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")

    if result.returncode != 0:
        raise RuntimeError(f"dbt build failed:\n{result.stderr}")

    return meta


def refresh_pipeline(settings: Settings | None = None) -> bool:
    """Download, ingest, build dbt, and atomically replace runtime database."""
    settings = settings or get_settings()
    ingestion = IngestionService(settings)

    try:
        manifest = ingestion.run()
        failed = [d for d in manifest.downloads if d.error]
        if failed and len(failed) == len(manifest.downloads):
            raise RuntimeError("All tournament downloads failed")

        seed_path = settings.analytics_dir / "seeds" / "venue_coordinates.csv"
        alias_path = settings.analytics_dir / "seeds" / "venue_aliases.csv"
        parquet_path = settings.working_data_dir / "matches.parquet"
        build_venue_coverage_report(parquet_path, seed_path, alias_path, settings.reports_dir)

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_db = Path(tmpdir) / "worldcup.duckdb"
            original_path = settings.duckdb_path
            settings.duckdb_path = tmp_db
            try:
                run_dbt_build(settings)
            finally:
                settings.duckdb_path = original_path

            runtime_path = original_path
            runtime_path.parent.mkdir(parents=True, exist_ok=True)
            backup = runtime_path.with_suffix(".duckdb.bak")
            if runtime_path.exists():
                shutil.copy2(runtime_path, backup)
            shutil.copy2(tmp_db, runtime_path)
            logger.info("Database refreshed at %s", runtime_path)

        return True
    except Exception:
        logger.exception("Data refresh failed; keeping existing database")
        return False


def initialize_runtime(settings: Settings | None = None) -> None:
    settings = settings or get_settings()
    runtime_path = settings.duckdb_path
    baseline = settings.duckdb_baseline_path

    runtime_path.parent.mkdir(parents=True, exist_ok=True)

    if not runtime_path.exists() and baseline.exists():
        shutil.copy2(baseline, runtime_path)
        logger.info("Initialized runtime database from baseline")

    if settings.refresh_data_on_start:
        logger.info("REFRESH_DATA_ON_START enabled")
        refresh_pipeline(settings)
