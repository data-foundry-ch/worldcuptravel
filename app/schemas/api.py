"""Pydantic API response schemas."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    database_available: bool
    data_timestamp: str | None = None
    version: str


class CoordinateCoverage(BaseModel):
    total_venues: int
    resolved_venues: int
    unresolved_venues: int
    coverage_pct: float


class MetaResponse(BaseModel):
    application_version: str
    source_name: str
    source_ref: str
    last_successful_download_timestamp: str | None
    last_successful_dbt_build_timestamp: str | None
    available_tournament_range: list[int]
    coordinate_coverage: CoordinateCoverage
    metric_definition: str
    data_freshness_warning_hours: int
    is_data_stale: bool


class TournamentSummary(BaseModel):
    year: int
    name: str | None = None
    match_count: int
    played_match_count: int
    team_count: int
    coordinate_coverage_pct: float
    unresolved_venue_count: int


class TeamSummary(BaseModel):
    team_id: str
    team_name: str
    match_count: int
    played_match_count: int


class MatchLocation(BaseModel):
    match_id: str
    sequence_number: int
    match_date: str | None
    kickoff_time_raw: str | None
    round_name: str | None
    opponent_name: str | None
    result: str | None
    raw_ground: str | None
    venue_id: str | None
    canonical_venue_name: str | None
    city: str | None
    country: str | None
    latitude: float | None
    longitude: float | None
    coordinate_precision: str | None
    leg_distance_km: float | None = None
    cumulative_distance_km: float
    is_played: bool
    is_projected: bool = False
    excluded_from_total: bool = False
    exclusion_reason: str | None = None


class RouteLeg(BaseModel):
    leg_number: int
    from_match_id: str
    to_match_id: str
    from_venue_id: str | None
    to_venue_id: str | None
    from_latitude: float | None
    from_longitude: float | None
    to_latitude: float | None
    to_longitude: float | None
    from_date: str | None
    to_date: str | None
    distance_km: float | None
    cumulative_distance_km: float
    is_projected: bool
    is_coordinate_complete: bool
    excluded_from_total: bool = False
    exclusion_reason: str | None = None


class RouteBounds(BaseModel):
    min_lat: float | None
    max_lat: float | None
    min_lng: float | None
    max_lng: float | None


class DataQualityDetails(BaseModel):
    unresolved_match_count: int
    excluded_leg_count: int
    warnings: list[str]


class SourceFreshness(BaseModel):
    last_download_timestamp: str | None
    last_dbt_build_timestamp: str | None
    is_stale: bool


class RouteResponse(BaseModel):
    tournament_year: int
    team_id: str
    team_name: str
    scope: Literal["played", "all"]
    metric_definition: str
    total_distance_km: float
    completed_distance_km: float
    projected_additional_distance_km: float
    match_count: int
    route_leg_count: int
    bounds: RouteBounds
    matches: list[MatchLocation]
    legs: list[RouteLeg]
    source_freshness: SourceFreshness
    data_quality: DataQualityDetails


class TournamentMovementPoint(BaseModel):
    venue_id: str
    label: str
    latitude: float
    longitude: float
    coordinate_precision: str | None


class TournamentMovementLeg(BaseModel):
    team_id: str
    team_name: str
    leg_number: int
    from_match_id: str
    to_match_id: str
    from_latitude: float
    from_longitude: float
    to_latitude: float
    to_longitude: float
    distance_km: float | None
    is_projected: bool


class AllTournamentMovementPoint(TournamentMovementPoint):
    tournament_year: int


class AllTournamentMovementLeg(TournamentMovementLeg):
    tournament_year: int


class TournamentMovementsResponse(BaseModel):
    tournament_year: int
    scope: Literal["played", "all"]
    total_distance_km: float
    point_count: int
    leg_count: int
    points: list[TournamentMovementPoint]
    legs: list[TournamentMovementLeg]


class AllTournamentMovementsResponse(BaseModel):
    scope: Literal["played", "all"]
    total_distance_km: float
    tournament_count: int
    point_count: int
    leg_count: int
    team_count: int
    points: list[AllTournamentMovementPoint]
    legs: list[AllTournamentMovementLeg]


class TournamentTravelTotal(BaseModel):
    tournament_year: int
    total_distance_km: float
    completed_distance_km: float
    projected_additional_distance_km: float
    team_count: int
    leg_count: int


class LeaderboardEntry(BaseModel):
    rank: int
    team_id: str
    team_name: str
    total_distance_km: float
    completed_distance_km: float
    projected_additional_distance_km: float
    match_count: int


class LeaderboardResponse(BaseModel):
    tournament_year: int
    entries: list[LeaderboardEntry]


class VenueMatch(BaseModel):
    match_id: str
    tournament_year: int
    match_date: str | None
    team1_name: str | None
    team2_name: str | None
    round_name: str | None


class VenueDetail(BaseModel):
    venue_id: str
    tournament_year: int
    canonical_venue_name: str | None
    city: str | None
    country: str | None
    country_code: str | None
    latitude: float | None
    longitude: float | None
    coordinate_precision: str | None
    raw_ground: str | None
    matches: list[VenueMatch]


class ErrorResponse(BaseModel):
    detail: str
    errors: list[dict[str, Any]] = Field(default_factory=list)
