"""API route handlers."""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, HTTPException, Query, Response

from app.schemas.api import (
    AllTournamentMovementsResponse,
    LeaderboardResponse,
    MetaResponse,
    RouteResponse,
    TeamSummary,
    TournamentMovementsResponse,
    TournamentSummary,
    TournamentTravelTotal,
    VenueDetail,
)
from app.services.routes import (
    get_all_tournament_movements,
    get_leaderboard,
    get_meta,
    get_route,
    get_teams,
    get_tournament_movements,
    get_tournament_travel_totals,
    get_tournaments,
    get_venue,
)

router = APIRouter(prefix="/api/v1")


@router.get("/meta", response_model=MetaResponse)
def meta_endpoint(response: Response) -> MetaResponse:
    response.headers["Cache-Control"] = "public, max-age=300"
    return get_meta()


@router.get("/tournaments", response_model=list[TournamentSummary])
def tournaments_endpoint(response: Response) -> list[TournamentSummary]:
    response.headers["Cache-Control"] = "public, max-age=600"
    return get_tournaments()


@router.get("/tournaments/travel-totals", response_model=list[TournamentTravelTotal])
def tournament_travel_totals_endpoint(
    response: Response,
    scope: Literal["played", "all"] = Query(default="played"),
) -> list[TournamentTravelTotal]:
    response.headers["Cache-Control"] = "public, max-age=300"
    return get_tournament_travel_totals(scope)


@router.get("/tournaments/movements", response_model=AllTournamentMovementsResponse)
def all_tournament_movements_endpoint(
    response: Response,
    scope: Literal["played", "all"] = Query(default="played"),
) -> AllTournamentMovementsResponse:
    response.headers["Cache-Control"] = "public, max-age=120"
    return get_all_tournament_movements(scope)


@router.get("/tournaments/{year}/teams", response_model=list[TeamSummary])
def teams_endpoint(year: int, response: Response) -> list[TeamSummary]:
    if year < 1930 or year > 2100:
        raise HTTPException(status_code=422, detail="Invalid tournament year")
    teams = get_teams(year)
    if not teams:
        raise HTTPException(status_code=404, detail=f"No teams found for {year}")
    response.headers["Cache-Control"] = "public, max-age=600"
    return teams


@router.get("/routes", response_model=RouteResponse)
def route_endpoint(
    response: Response,
    year: int = Query(..., ge=1930, le=2100),
    team: str = Query(..., min_length=1),
    scope: Literal["played", "all"] = Query(default="played"),
) -> RouteResponse:
    route = get_route(year, team, scope)
    if not route:
        raise HTTPException(
            status_code=404,
            detail=f"No route found for team '{team}' in {year} with scope '{scope}'",
        )
    response.headers["Cache-Control"] = "public, max-age=120"
    return route


@router.get("/tournaments/{year}/movements", response_model=TournamentMovementsResponse)
def tournament_movements_endpoint(
    year: int,
    response: Response,
    scope: Literal["played", "all"] = Query(default="played"),
) -> TournamentMovementsResponse:
    if year < 1930 or year > 2100:
        raise HTTPException(status_code=422, detail="Invalid tournament year")
    response.headers["Cache-Control"] = "public, max-age=120"
    return get_tournament_movements(year, scope)


@router.get("/tournaments/{year}/leaderboard", response_model=LeaderboardResponse)
def leaderboard_endpoint(
    year: int,
    response: Response,
    scope: Literal["played", "all"] = Query(default="played"),
) -> LeaderboardResponse:
    if year < 1930 or year > 2100:
        raise HTTPException(status_code=422, detail="Invalid tournament year")
    response.headers["Cache-Control"] = "public, max-age=300"
    return get_leaderboard(year, scope)


@router.get("/venues/{venue_id}", response_model=VenueDetail)
def venue_endpoint(venue_id: str) -> VenueDetail:
    venue = get_venue(venue_id)
    if not venue:
        raise HTTPException(status_code=404, detail=f"Venue '{venue_id}' not found")
    return venue
