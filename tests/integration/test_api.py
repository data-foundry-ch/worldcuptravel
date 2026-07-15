import os
import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.settings import get_settings

ROOT = Path(__file__).resolve().parent.parent.parent


@pytest.fixture(scope="module")
def client() -> TestClient:
    os.environ["DUCKDB_PATH"] = str(ROOT / "data" / "worldcup.duckdb")
    get_settings.cache_clear()
    return TestClient(app)


def test_healthz(client: TestClient) -> None:
    res = client.get("/healthz")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] in {"ok", "degraded"}
    assert "version" in body


def test_meta(client: TestClient) -> None:
    res = client.get("/api/v1/meta")
    assert res.status_code == 200
    body = res.json()
    assert body["source_name"]
    assert len(body["available_tournament_range"]) > 0


def test_tournaments(client: TestClient) -> None:
    res = client.get("/api/v1/tournaments")
    assert res.status_code == 200
    tournaments = res.json()
    assert any(t["year"] == 1930 for t in tournaments)


def test_route_uruguay_1930(client: TestClient) -> None:
    teams = client.get("/api/v1/tournaments/1930/teams").json()
    uruguay = next(t for t in teams if t["team_name"] == "Uruguay")
    res = client.get(f"/api/v1/routes?year=1930&team={uruguay['team_id']}&scope=played")
    assert res.status_code == 200
    route = res.json()
    assert route["match_count"] >= 1
    assert route["total_distance_km"] >= 0
    assert len(route["matches"]) == route["match_count"]


def test_all_tournament_movements(client: TestClient) -> None:
    res = client.get("/api/v1/tournaments/movements?scope=played")
    assert res.status_code == 200
    body = res.json()
    assert body["tournament_count"] > 1
    assert body["team_count"] > 1
    assert body["leg_count"] == len(body["legs"])
    assert body["point_count"] == len(body["points"])
    assert "tournament_year" in body["legs"][0]


def test_2026_placeholder_teams_are_filtered(client: TestClient) -> None:
    placeholder_pattern = re.compile(r"^[LW]\d+$", re.IGNORECASE)

    teams_res = client.get("/api/v1/tournaments/2026/teams")
    assert teams_res.status_code == 200
    teams = teams_res.json()
    assert not any(placeholder_pattern.match(team["team_id"]) for team in teams)

    leaderboard_res = client.get("/api/v1/tournaments/2026/leaderboard?scope=all")
    assert leaderboard_res.status_code == 200
    leaderboard = leaderboard_res.json()
    assert not any(placeholder_pattern.match(entry["team_id"]) for entry in leaderboard["entries"])

    movements_res = client.get("/api/v1/tournaments/2026/movements?scope=all")
    assert movements_res.status_code == 200
    movements = movements_res.json()
    assert not any(placeholder_pattern.match(leg["team_id"]) for leg in movements["legs"])

    route_res = client.get("/api/v1/routes?year=2026&team=w101&scope=all")
    assert route_res.status_code == 404
