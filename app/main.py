"""World Cup Travel Atlas FastAPI application."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app import __version__
from app.api.v1 import router as api_v1_router
from app.database import read_connection
from app.schemas.api import HealthResponse
from app.services.data_refresh import initialize_runtime
from app.settings import get_settings

logging.basicConfig(
    level=get_settings().log_level,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    logger.info("Starting World Cup Travel Atlas v%s (%s)", __version__, settings.app_env)
    initialize_runtime(settings)
    yield
    logger.info("Shutting down gracefully")


app = FastAPI(
    title="World Cup Travel Atlas",
    version=__version__,
    lifespan=lifespan,
)
app.include_router(api_v1_router)


@app.get("/healthz", response_model=HealthResponse)
def healthz() -> HealthResponse:
    settings = get_settings()
    db_available = settings.duckdb_path.exists()
    data_timestamp = None
    if db_available:
        try:
            with read_connection(settings) as conn:
                row = conn.execute(
                    "select max(tournament_year) from dim_tournaments"
                ).fetchone()
                if row:
                    data_timestamp = str(row[0])
        except Exception:
            db_available = False

    return HealthResponse(
        status="ok" if db_available else "degraded",
        database_available=db_available,
        data_timestamp=data_timestamp,
        version=__version__,
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(_request: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


def _setup_static_files() -> None:
    settings = get_settings()
    dist = settings.frontend_dist
    if not dist.exists():
        logger.warning("Frontend dist not found at %s", dist)
        return

    assets_dir = dist / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/{full_path:path}")
    async def spa_fallback(full_path: str) -> FileResponse:
        if full_path.startswith("api/") or full_path == "healthz":
            raise HTTPException(status_code=404, detail="Not found")
        static_file = dist / full_path
        if static_file.is_file():
            return FileResponse(static_file)
        index = dist / "index.html"
        if not index.exists():
            raise HTTPException(status_code=404, detail="Frontend not built")
        return FileResponse(index)


if get_settings().app_env == "production":
    _setup_static_files()
