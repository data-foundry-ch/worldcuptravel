"""OpenFootball World Cup data ingestion."""

from __future__ import annotations

import hashlib
import json
import logging
import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import certifi
import httpx

try:
    import truststore

    truststore.inject_into_ssl()
except ImportError:
    pass
import pandas as pd

from app.settings import Settings, get_settings

logger = logging.getLogger(__name__)

TOURNAMENT_YEARS = [
    1930, 1934, 1938, 1950, 1954, 1958, 1962, 1966, 1970, 1974,
    1978, 1982, 1986, 1990, 1994, 1998, 2002, 2006, 2010, 2014,
    2018, 2022, 2026,
]


def build_tournament_url(base_url: str, ref: str, year: int) -> str:
    return f"{base_url.rstrip('/')}/{ref}/{year}/worldcup.json"


def normalize_match_id_component(value: str | int | None) -> str:
    if value is None:
        return ""
    text = str(value).strip().lower()
    text = re.sub(r"\s+", " ", text)
    return text


def generate_match_id(
    tournament_year: int,
    match_date: str | None,
    source_match_index: int,
    team1: str | None,
    team2: str | None,
) -> str:
    components = "|".join(
        [
            str(tournament_year),
            normalize_match_id_component(match_date),
            str(source_match_index),
            normalize_match_id_component(team1),
            normalize_match_id_component(team2),
        ]
    )
    return hashlib.sha256(components.encode("utf-8")).hexdigest()[:32]


def extract_score(score: dict[str, Any] | None, key: str) -> tuple[int | None, int | None]:
    if not score or key not in score:
        return None, None
    value = score[key]
    if isinstance(value, list) and len(value) == 2:
        return int(value[0]), int(value[1])
    return None, None


def flatten_match(
    tournament_year: int,
    match: dict[str, Any],
    source_match_index: int,
    tournament_name: str | None,
) -> dict[str, Any]:
    score = match.get("score")
    ft1, ft2 = extract_score(score, "ft")
    ht1, ht2 = extract_score(score, "ht")
    et1, et2 = extract_score(score, "et")
    pen1, pen2 = extract_score(score, "pen")

    team1 = match.get("team1")
    team2 = match.get("team2")
    match_date = match.get("date")

    known_keys = {
        "round", "date", "time", "team1", "team2", "score",
        "goals1", "goals2", "group", "ground", "penalty", "extra",
    }
    metadata = {k: v for k, v in match.items() if k not in known_keys}

    is_played = ft1 is not None and ft2 is not None

    return {
        "match_id": generate_match_id(tournament_year, match_date, source_match_index, team1, team2),
        "tournament_year": tournament_year,
        "tournament_name": tournament_name,
        "source_match_index": source_match_index,
        "round_name": match.get("round"),
        "match_date": match_date,
        "kickoff_time_raw": match.get("time"),
        "team1_name": team1,
        "team2_name": team2,
        "group_name": match.get("group"),
        "raw_ground": match.get("ground"),
        "goals_team1_ft": ft1,
        "goals_team2_ft": ft2,
        "goals_team1_ht": ht1,
        "goals_team2_ht": ht2,
        "goals_team1_et": et1,
        "goals_team2_et": et2,
        "goals_team1_pen": pen1,
        "goals_team2_pen": pen2,
        "is_played": is_played,
        "metadata_json": json.dumps(metadata, ensure_ascii=False, sort_keys=True) if metadata else None,
    }


@dataclass
class DownloadResult:
    tournament_year: int
    source_url: str
    git_ref: str
    http_status: int
    retrieved_at_utc: str
    sha256: str
    raw_path: str
    match_count: int
    row_count: int
    error: str | None = None


@dataclass
class IngestionManifest:
    generated_at_utc: str
    git_ref: str
    downloads: list[DownloadResult] = field(default_factory=list)
    total_matches: int = 0
    parquet_path: str | None = None
    parquet_sha256: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "generated_at_utc": self.generated_at_utc,
            "git_ref": self.git_ref,
            "total_matches": self.total_matches,
            "parquet_path": self.parquet_path,
            "parquet_sha256": self.parquet_sha256,
            "downloads": [d.__dict__ for d in self.downloads],
        }


class IngestionService:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    def download_tournament(
        self,
        client: httpx.Client,
        year: int,
        raw_dir: Path | None = None,
    ) -> DownloadResult:
        raw_dir = raw_dir or self.settings.raw_data_dir
        url = build_tournament_url(
            self.settings.openfootball_base_url,
            self.settings.openfootball_github_ref,
            year,
        )
        retrieved_at = datetime.now(UTC).isoformat()

        for attempt in range(self.settings.http_max_retries):
            try:
                response = client.get(url)
                if response.status_code == 404:
                    return DownloadResult(
                        tournament_year=year,
                        source_url=url,
                        git_ref=self.settings.openfootball_github_ref,
                        http_status=404,
                        retrieved_at_utc=retrieved_at,
                        sha256="",
                        raw_path="",
                        match_count=0,
                        row_count=0,
                        error=f"Tournament file not found for {year}",
                    )

                response.raise_for_status()
                content = response.content
                if len(content) > self.settings.http_max_response_bytes:
                    raise ValueError(f"Response too large for {year}")

                try:
                    payload = json.loads(content)
                except json.JSONDecodeError as exc:
                    raise ValueError(f"Invalid JSON for {year}") from exc

                if "matches" not in payload or not isinstance(payload["matches"], list):
                    raise ValueError(f"Missing matches array for {year}")

                checksum = hashlib.sha256(content).hexdigest()
                year_dir = raw_dir / str(year)
                year_dir.mkdir(parents=True, exist_ok=True)
                raw_path = year_dir / "worldcup.json"
                raw_path.write_bytes(content)

                return DownloadResult(
                    tournament_year=year,
                    source_url=url,
                    git_ref=self.settings.openfootball_github_ref,
                    http_status=response.status_code,
                    retrieved_at_utc=retrieved_at,
                    sha256=checksum,
                    raw_path=str(raw_path),
                    match_count=len(payload["matches"]),
                    row_count=len(payload["matches"]),
                )
            except (httpx.HTTPError, ValueError) as exc:
                if attempt == self.settings.http_max_retries - 1:
                    logger.error("Failed to download %s after retries: %s", year, exc)
                    return DownloadResult(
                        tournament_year=year,
                        source_url=url,
                        git_ref=self.settings.openfootball_github_ref,
                        http_status=0,
                        retrieved_at_utc=retrieved_at,
                        sha256="",
                        raw_path="",
                        match_count=0,
                        row_count=0,
                        error=str(exc),
                    )
                wait = 2**attempt
                logger.warning("Retry %s for year %s in %ss: %s", attempt + 1, year, wait, exc)
                import time
                time.sleep(wait)

        raise RuntimeError("Unreachable")

    def flatten_from_raw(self, raw_path: Path, year: int) -> list[dict[str, Any]]:
        payload = json.loads(raw_path.read_text(encoding="utf-8"))
        tournament_name = payload.get("name")
        matches = payload.get("matches", [])
        rows: list[dict[str, Any]] = []
        for idx, match in enumerate(matches):
            if not isinstance(match, dict):
                continue
            rows.append(flatten_match(year, match, idx, tournament_name))
        return rows

    def run(
        self,
        years: list[int] | None = None,
        use_local_only: bool = False,
    ) -> IngestionManifest:
        years = years or TOURNAMENT_YEARS
        working_dir = self.settings.working_data_dir
        raw_dir = self.settings.raw_data_dir
        working_dir.mkdir(parents=True, exist_ok=True)
        raw_dir.mkdir(parents=True, exist_ok=True)

        manifest = IngestionManifest(
            generated_at_utc=datetime.now(UTC).isoformat(),
            git_ref=self.settings.openfootball_github_ref,
        )

        all_rows: list[dict[str, Any]] = []

        timeout = httpx.Timeout(self.settings.http_timeout_seconds)
        with httpx.Client(
            timeout=timeout,
            follow_redirects=True,
            verify=certifi.where(),
        ) as client:
            for year in years:
                if use_local_only:
                    raw_path = raw_dir / str(year) / "worldcup.json"
                    if not raw_path.exists():
                        manifest.downloads.append(
                            DownloadResult(
                                tournament_year=year,
                                source_url=build_tournament_url(
                                    self.settings.openfootball_base_url,
                                    self.settings.openfootball_github_ref,
                                    year,
                                ),
                                git_ref=self.settings.openfootball_github_ref,
                                http_status=0,
                                retrieved_at_utc=datetime.now(UTC).isoformat(),
                                sha256="",
                                raw_path="",
                                match_count=0,
                                row_count=0,
                                error="Local file missing",
                            )
                        )
                        continue
                    checksum = hashlib.sha256(raw_path.read_bytes()).hexdigest()
                    rows = self.flatten_from_raw(raw_path, year)
                    all_rows.extend(rows)
                    manifest.downloads.append(
                        DownloadResult(
                            tournament_year=year,
                            source_url=build_tournament_url(
                                self.settings.openfootball_base_url,
                                self.settings.openfootball_github_ref,
                                year,
                            ),
                            git_ref=self.settings.openfootball_github_ref,
                            http_status=200,
                            retrieved_at_utc=datetime.fromtimestamp(
                                raw_path.stat().st_mtime, tz=UTC
                            ).isoformat(),
                            sha256=checksum,
                            raw_path=str(raw_path),
                            match_count=len(rows),
                            row_count=len(rows),
                        )
                    )
                else:
                    result = self.download_tournament(client, year, raw_dir)
                    manifest.downloads.append(result)
                    if result.error or not result.raw_path:
                        continue
                    rows = self.flatten_from_raw(Path(result.raw_path), year)
                    all_rows.extend(rows)

        df = pd.DataFrame(all_rows)
        parquet_path = working_dir / "matches.parquet"
        df.to_parquet(parquet_path, index=False)
        parquet_sha = hashlib.sha256(parquet_path.read_bytes()).hexdigest()

        manifest.total_matches = len(all_rows)
        manifest.parquet_path = str(parquet_path)
        manifest.parquet_sha256 = parquet_sha

        manifest_path = self.settings.manifest_path
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(json.dumps(manifest.to_dict(), indent=2), encoding="utf-8")

        logger.info("Ingestion complete: %s matches", len(all_rows))
        return manifest
