import logging
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import duckdb

from app.settings import Settings, get_settings

logger = logging.getLogger(__name__)


def ensure_runtime_database(settings: Settings | None = None) -> Path:
    """Copy baseline DuckDB to writable runtime path if needed."""
    settings = settings or get_settings()
    runtime_path = settings.duckdb_path
    baseline = settings.duckdb_baseline_path

    runtime_path.parent.mkdir(parents=True, exist_ok=True)

    if not runtime_path.exists():
        if baseline.exists():
            import shutil

            shutil.copy2(baseline, runtime_path)
            logger.info("Copied baseline database to %s", runtime_path)
        else:
            logger.warning("No baseline or runtime database at %s", runtime_path)

    return runtime_path


@contextmanager
def read_connection(settings: Settings | None = None) -> Generator[duckdb.DuckDBPyConnection, None, None]:
    settings = settings or get_settings()
    db_path = ensure_runtime_database(settings)
    if not db_path.exists():
        raise FileNotFoundError(f"Database not found: {db_path}")

    conn = duckdb.connect(str(db_path), read_only=True)
    try:
        yield conn
    finally:
        conn.close()


@contextmanager
def write_connection(db_path: Path) -> Generator[duckdb.DuckDBPyConnection, None, None]:
    conn = duckdb.connect(str(db_path))
    try:
        yield conn
    finally:
        conn.close()


def fetch_all(conn: duckdb.DuckDBPyConnection, sql: str, params: list[Any] | None = None) -> list[dict[str, Any]]:
    params = params or []
    result = conn.execute(sql, params)
    columns = [desc[0] for desc in result.description]
    return [dict(zip(columns, row, strict=True)) for row in result.fetchall()]


def fetch_one(conn: duckdb.DuckDBPyConnection, sql: str, params: list[Any] | None = None) -> dict[str, Any] | None:
    rows = fetch_all(conn, sql, params)
    return rows[0] if rows else None
