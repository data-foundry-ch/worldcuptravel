from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = Field(default="development", alias="APP_ENV")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    app_version: str = Field(default="1.0.0", alias="APP_VERSION")

    data_dir: Path = Field(default=Path("data"), alias="DATA_DIR")
    duckdb_path: Path = Field(default=Path("data/worldcup.duckdb"), alias="DUCKDB_PATH")
    duckdb_baseline_path: Path = Field(
        default=Path("data/bootstrap/worldcup.duckdb"),
        alias="DUCKDB_BASELINE_PATH",
    )
    raw_data_dir: Path = Field(default=Path("data/raw/worldcups"), alias="RAW_DATA_DIR")
    working_data_dir: Path = Field(default=Path("data/working"), alias="WORKING_DATA_DIR")

    openfootball_github_ref: str = Field(default="master", alias="OPENFOOTBALL_GITHUB_REF")
    openfootball_base_url: str = Field(
        default="https://raw.githubusercontent.com/openfootball/worldcup.json",
        alias="OPENFOOTBALL_BASE_URL",
    )

    refresh_data_on_start: bool = Field(default=False, alias="REFRESH_DATA_ON_START")
    data_freshness_warning_hours: int = Field(default=36, alias="DATA_FRESHNESS_WARNING_HOURS")

    http_timeout_seconds: float = 30.0
    http_max_retries: int = 3
    http_max_response_bytes: int = 10 * 1024 * 1024

    metric_definition: str = (
        "The minimum great-circle distance between consecutive match locations "
        "in chronological order."
    )

    @property
    def project_root(self) -> Path:
        return Path(__file__).resolve().parent.parent

    @property
    def frontend_dist(self) -> Path:
        return self.project_root / "frontend" / "dist"

    @property
    def analytics_dir(self) -> Path:
        return self.project_root / "analytics"

    @property
    def reports_dir(self) -> Path:
        return self.project_root / "reports"

    @property
    def manifest_path(self) -> Path:
        return self.working_data_dir / "ingestion_manifest.json"

    @property
    def dbt_build_meta_path(self) -> Path:
        return self.working_data_dir / "dbt_build_meta.json"


@lru_cache
def get_settings() -> Settings:
    return Settings()
