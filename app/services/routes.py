"""Route and tournament query services."""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Literal

from app.database import fetch_all, fetch_one, read_connection
from app.schemas.api import (
    AllTournamentMovementLeg,
    AllTournamentMovementPoint,
    AllTournamentMovementsResponse,
    CoordinateCoverage,
    DataQualityDetails,
    LeaderboardEntry,
    LeaderboardResponse,
    MatchLocation,
    MetaResponse,
    RouteBounds,
    RouteLeg,
    RouteResponse,
    SourceFreshness,
    TeamSummary,
    TournamentMovementLeg,
    TournamentMovementPoint,
    TournamentMovementsResponse,
    TournamentSummary,
    TournamentTravelTotal,
    VenueDetail,
    VenueMatch,
)
from app.settings import Settings, get_settings

logger = logging.getLogger(__name__)

METRIC_DEFINITION = (
    "Approximate match-location travel: the minimum great-circle distance "
    "between consecutive match locations in chronological order."
)
PLACEHOLDER_TEAM_ID_PATTERN = "^[LlWw][0-9]+$"


def _real_team_predicate(column: str) -> str:
    return f"not regexp_matches(cast({column} as varchar), '{PLACEHOLDER_TEAM_ID_PATTERN}')"


def _load_json_meta(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
        return data
    except json.JSONDecodeError:
        return None


def _parse_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def get_meta(settings: Settings | None = None) -> MetaResponse:
    settings = settings or get_settings()
    ingestion_meta = _load_json_meta(settings.manifest_path)
    dbt_meta = _load_json_meta(settings.dbt_build_meta_path)

    with read_connection(settings) as conn:
        coverage_row = fetch_one(
            conn,
            """
            select total_venues, resolved_venues, unresolved_venues, coverage_pct
            from data_quality_venue_coverage
            where tournament_year = 0
            """,
        )
        years = fetch_all(
            conn,
            "select tournament_year from dim_tournaments order by tournament_year",
        )

    last_download = None
    if ingestion_meta:
        downloads = ingestion_meta.get("downloads", [])
        timestamps = [d.get("retrieved_at_utc") for d in downloads if d.get("retrieved_at_utc")]
        if timestamps:
            last_download = max(timestamps)

    last_build = dbt_meta.get("built_at_utc") if dbt_meta else None
    download_dt = _parse_timestamp(last_download)
    stale_threshold = timedelta(hours=settings.data_freshness_warning_hours)
    is_stale = download_dt is None or (datetime.now(UTC) - download_dt) > stale_threshold

    coverage = CoordinateCoverage(
        total_venues=int(coverage_row["total_venues"]) if coverage_row else 0,
        resolved_venues=int(coverage_row["resolved_venues"]) if coverage_row else 0,
        unresolved_venues=int(coverage_row["unresolved_venues"]) if coverage_row else 0,
        coverage_pct=float(coverage_row["coverage_pct"]) if coverage_row else 0.0,
    )

    year_list = [int(y["tournament_year"]) for y in years]

    return MetaResponse(
        application_version=settings.app_version,
        source_name="OpenFootball worldcup.json",
        source_ref=settings.openfootball_github_ref,
        last_successful_download_timestamp=last_download,
        last_successful_dbt_build_timestamp=last_build,
        available_tournament_range=year_list,
        coordinate_coverage=coverage,
        metric_definition=METRIC_DEFINITION,
        data_freshness_warning_hours=settings.data_freshness_warning_hours,
        is_data_stale=is_stale,
    )


def get_tournaments(settings: Settings | None = None) -> list[TournamentSummary]:
    settings = settings or get_settings()
    team_filter = _real_team_predicate("tm.team_id")
    with read_connection(settings) as conn:
        rows = fetch_all(
            conn,
            f"""
            select
                t.tournament_year,
                t.tournament_name,
                t.match_count,
                t.played_match_count,
                count(distinct tm.team_id) as team_count,
                coalesce(dq.coverage_pct, 0) as coordinate_coverage_pct,
                coalesce(dq.unresolved_venues, 0) as unresolved_venue_count
            from dim_tournaments t
            left join dim_teams tm
                on t.tournament_year = tm.tournament_year
                and {team_filter}
            left join data_quality_venue_coverage dq
                on t.tournament_year = dq.tournament_year
            group by 1, 2, 3, 4, 6, 7
            order by t.tournament_year
            """,
        )
    return [
        TournamentSummary(
            year=int(r["tournament_year"]),
            name=r.get("tournament_name"),
            match_count=int(r["match_count"]),
            played_match_count=int(r["played_match_count"]),
            team_count=int(r["team_count"]),
            coordinate_coverage_pct=float(r["coordinate_coverage_pct"]),
            unresolved_venue_count=int(r["unresolved_venue_count"]),
        )
        for r in rows
    ]


def get_teams(year: int, settings: Settings | None = None) -> list[TeamSummary]:
    settings = settings or get_settings()
    team_filter = _real_team_predicate("a.team_id")
    with read_connection(settings) as conn:
        rows = fetch_all(
            conn,
            f"""
            select
                a.team_id,
                a.team_name,
                count(*) as match_count,
                sum(case when a.is_played then 1 else 0 end) as played_match_count
            from fct_team_match_appearances a
            where a.tournament_year = ?
              and {team_filter}
            group by 1, 2
            order by a.team_name
            """,
            [year],
        )
    return [
        TeamSummary(
            team_id=r["team_id"],
            team_name=r["team_name"],
            match_count=int(r["match_count"]),
            played_match_count=int(r["played_match_count"]),
        )
        for r in rows
    ]


def get_route(
    year: int,
    team_id: str,
    scope: Literal["played", "all"] = "played",
    settings: Settings | None = None,
) -> RouteResponse | None:
    settings = settings or get_settings()
    scope_filter = "and a.is_played = true" if scope == "played" else ""
    scope_clause = (
        "and exists (select 1 from fct_team_match_appearances a "
        "where a.match_id = l.to_match_id and a.is_played = true)"
        if scope == "played"
        else ""
    )
    appearance_team_filter = _real_team_predicate("a.team_id")
    leg_team_filter = _real_team_predicate("l.team_id")
    aggregate_team_filter = _real_team_predicate("agg.team_id")

    with read_connection(settings) as conn:
        team_row = fetch_one(
            conn,
            f"""
            select team_name
            from fct_team_match_appearances a
            where a.tournament_year = ? and a.team_id = ?
            and {appearance_team_filter}
            {scope_filter}
            limit 1
            """,
            [year, team_id],
        )
        if not team_row:
            return None

        matches = fetch_all(
            conn,
            f"""
            select
                a.match_id, a.sequence_number, a.match_date, a.kickoff_time_raw,
                a.round_name, a.opponent_name, a.result, a.raw_ground,
                a.venue_id, v.canonical_venue_name, v.city, v.country,
                a.latitude, a.longitude, a.coordinate_precision,
                a.cumulative_distance_km, a.is_played,
                case when a.coordinate_precision = 'unresolved'
                    or a.latitude is null or a.longitude is null
                then true else false end as excluded_from_total
            from fct_team_match_appearances a
            left join dim_venues v on a.venue_id = v.venue_id
            where a.tournament_year = ? and a.team_id = ?
            and {appearance_team_filter}
            {scope_filter}
            order by a.sequence_number
            """,
            [year, team_id],
        )

        legs = fetch_all(
            conn,
            f"""
            select
                l.leg_number, l.from_match_id, l.to_match_id,
                l.from_venue_id, l.to_venue_id,
                l.from_latitude, l.from_longitude,
                l.to_latitude, l.to_longitude,
                l.from_date, l.to_date,
                l.distance_km, l.cumulative_distance_km,
                l.is_projected, l.is_coordinate_complete,
                case when not l.is_coordinate_complete then true else false end as excluded_from_total
            from fct_team_travel_legs l
            where l.tournament_year = ? and l.team_id = ?
            and {leg_team_filter}
            {scope_clause}
            order by l.leg_number
            """,
            [year, team_id],
        )

        agg = fetch_one(
            conn,
            f"""
            select total_distance_km, completed_distance_km,
                   projected_additional_distance_km, match_count, route_leg_count,
                   unresolved_match_count, excluded_leg_count
            from agg_team_tournament_travel agg
            where agg.tournament_year = ? and agg.team_id = ?
              and {aggregate_team_filter}
            """,
            [year, team_id],
        )

    leg_by_to_match = {leg["to_match_id"]: leg for leg in legs}

    match_locations: list[MatchLocation] = []
    warnings: list[str] = []
    unresolved_count = 0
    lats: list[float] = []
    lngs: list[float] = []

    for m in matches:
        leg = leg_by_to_match.get(m["match_id"])
        leg_distance = round(float(leg["distance_km"]), 1) if leg and leg["distance_km"] is not None else None
        excluded = bool(m["excluded_from_total"])
        exclusion_reason = None
        is_projected = not bool(m["is_played"])

        if excluded:
            unresolved_count += 1
            exclusion_reason = "Unresolved venue coordinates"
            warnings.append(f"Match at {m.get('raw_ground')} excluded from distance total")

        if m["latitude"] is not None and m["longitude"] is not None and not excluded:
            lats.append(float(m["latitude"]))
            lngs.append(float(m["longitude"]))

        match_locations.append(
            MatchLocation(
                match_id=m["match_id"],
                sequence_number=int(m["sequence_number"]),
                match_date=str(m["match_date"]) if m["match_date"] else None,
                kickoff_time_raw=m.get("kickoff_time_raw"),
                round_name=m.get("round_name"),
                opponent_name=m.get("opponent_name"),
                result=m.get("result"),
                raw_ground=m.get("raw_ground"),
                venue_id=m.get("venue_id"),
                canonical_venue_name=m.get("canonical_venue_name"),
                city=m.get("city"),
                country=m.get("country"),
                latitude=float(m["latitude"]) if m["latitude"] is not None else None,
                longitude=float(m["longitude"]) if m["longitude"] is not None else None,
                coordinate_precision=m.get("coordinate_precision"),
                leg_distance_km=leg_distance,
                cumulative_distance_km=float(m["cumulative_distance_km"] or 0),
                is_played=bool(m["is_played"]),
                is_projected=is_projected,
                excluded_from_total=excluded,
                exclusion_reason=exclusion_reason,
            )
        )

    route_legs: list[RouteLeg] = []
    excluded_legs = 0
    for leg in legs:
        excluded = not bool(leg["is_coordinate_complete"])
        if excluded:
            excluded_legs += 1
            warnings.append(
                f"Leg {leg['leg_number']} excluded: incomplete coordinates"
            )
        route_legs.append(
            RouteLeg(
                leg_number=int(leg["leg_number"]),
                from_match_id=leg["from_match_id"],
                to_match_id=leg["to_match_id"],
                from_venue_id=leg.get("from_venue_id"),
                to_venue_id=leg.get("to_venue_id"),
                from_latitude=float(leg["from_latitude"]) if leg["from_latitude"] is not None else None,
                from_longitude=float(leg["from_longitude"]) if leg["from_longitude"] is not None else None,
                to_latitude=float(leg["to_latitude"]) if leg["to_latitude"] is not None else None,
                to_longitude=float(leg["to_longitude"]) if leg["to_longitude"] is not None else None,
                from_date=str(leg["from_date"]) if leg.get("from_date") else None,
                to_date=str(leg["to_date"]) if leg.get("to_date") else None,
                distance_km=round(float(leg["distance_km"]), 1) if leg["distance_km"] is not None else None,
                cumulative_distance_km=float(leg["cumulative_distance_km"] or 0),
                is_projected=bool(leg["is_projected"]),
                is_coordinate_complete=bool(leg["is_coordinate_complete"]),
                excluded_from_total=excluded,
                exclusion_reason="Incomplete coordinates" if excluded else None,
            )
        )

    if year == 2026 and scope == "all":
        warnings.append("2026 includes scheduled fixtures; distances are projected itinerary travel")

    meta = get_meta(settings)
    bounds = RouteBounds(
        min_lat=min(lats) if lats else None,
        max_lat=max(lats) if lats else None,
        min_lng=min(lngs) if lngs else None,
        max_lng=max(lngs) if lngs else None,
    )

    return RouteResponse(
        tournament_year=year,
        team_id=team_id,
        team_name=team_row["team_name"],
        scope=scope,
        metric_definition=METRIC_DEFINITION,
        total_distance_km=round(float(agg["total_distance_km"] or 0), 1) if agg else 0.0,
        completed_distance_km=round(float(agg["completed_distance_km"] or 0), 1) if agg else 0.0,
        projected_additional_distance_km=round(float(agg["projected_additional_distance_km"] or 0), 1) if agg else 0.0,
        match_count=len(match_locations),
        route_leg_count=len(route_legs),
        bounds=bounds,
        matches=match_locations,
        legs=route_legs,
        source_freshness=SourceFreshness(
            last_download_timestamp=meta.last_successful_download_timestamp,
            last_dbt_build_timestamp=meta.last_successful_dbt_build_timestamp,
            is_stale=meta.is_data_stale,
        ),
        data_quality=DataQualityDetails(
            unresolved_match_count=unresolved_count,
            excluded_leg_count=excluded_legs,
            warnings=list(dict.fromkeys(warnings)),
        ),
    )


def get_tournament_movements(
    year: int,
    scope: Literal["played", "all"] = "played",
    settings: Settings | None = None,
) -> TournamentMovementsResponse:
    settings = settings or get_settings()
    leg_scope_filter = "and l.is_projected = false" if scope == "played" else ""
    point_scope_filter = "and a.is_played = true" if scope == "played" else ""
    appearance_team_filter = _real_team_predicate("a.team_id")
    leg_team_filter = _real_team_predicate("l.team_id")

    with read_connection(settings) as conn:
        point_rows = fetch_all(
            conn,
            f"""
            select distinct
                a.venue_id,
                coalesce(v.canonical_venue_name, a.raw_ground) as label,
                a.latitude,
                a.longitude,
                a.coordinate_precision
            from fct_team_match_appearances a
            left join dim_venues v on a.venue_id = v.venue_id
            where a.tournament_year = ?
              and a.venue_id is not null
              and a.latitude is not null
              and a.longitude is not null
              and {appearance_team_filter}
              {point_scope_filter}
            order by label
            """,
            [year],
        )
        leg_rows = fetch_all(
            conn,
            f"""
            select
                l.team_id,
                l.team_name,
                l.leg_number,
                l.from_match_id,
                l.to_match_id,
                l.from_latitude,
                l.from_longitude,
                l.to_latitude,
                l.to_longitude,
                l.distance_km,
                l.is_projected
            from fct_team_travel_legs l
            where l.tournament_year = ?
              and l.is_coordinate_complete = true
              and {leg_team_filter}
              {leg_scope_filter}
            order by l.team_name, l.leg_number
            """,
            [year],
        )

    points = [
        TournamentMovementPoint(
            venue_id=row["venue_id"],
            label=row["label"],
            latitude=float(row["latitude"]),
            longitude=float(row["longitude"]),
            coordinate_precision=row.get("coordinate_precision"),
        )
        for row in point_rows
    ]
    legs = [
        TournamentMovementLeg(
            team_id=row["team_id"],
            team_name=row["team_name"],
            leg_number=int(row["leg_number"]),
            from_match_id=row["from_match_id"],
            to_match_id=row["to_match_id"],
            from_latitude=float(row["from_latitude"]),
            from_longitude=float(row["from_longitude"]),
            to_latitude=float(row["to_latitude"]),
            to_longitude=float(row["to_longitude"]),
            distance_km=round(float(row["distance_km"]), 1) if row["distance_km"] is not None else None,
            is_projected=bool(row["is_projected"]),
        )
        for row in leg_rows
    ]

    return TournamentMovementsResponse(
        tournament_year=year,
        scope=scope,
        total_distance_km=round(
            sum(leg.distance_km or 0 for leg in legs),
            1,
        ),
        point_count=len(points),
        leg_count=len(legs),
        points=points,
        legs=legs,
    )


def get_all_tournament_movements(
    scope: Literal["played", "all"] = "played",
    settings: Settings | None = None,
) -> AllTournamentMovementsResponse:
    settings = settings or get_settings()
    leg_scope_filter = "and l.is_projected = false" if scope == "played" else ""
    point_scope_filter = "and a.is_played = true" if scope == "played" else ""
    appearance_team_filter = _real_team_predicate("a.team_id")
    leg_team_filter = _real_team_predicate("l.team_id")

    with read_connection(settings) as conn:
        point_rows = fetch_all(
            conn,
            f"""
            select distinct
                a.tournament_year,
                a.venue_id,
                coalesce(v.canonical_venue_name, a.raw_ground) as label,
                a.latitude,
                a.longitude,
                a.coordinate_precision
            from fct_team_match_appearances a
            left join dim_venues v on a.venue_id = v.venue_id
            where a.venue_id is not null
              and a.latitude is not null
              and a.longitude is not null
              and {appearance_team_filter}
              {point_scope_filter}
            order by a.tournament_year, label
            """,
        )
        leg_rows = fetch_all(
            conn,
            f"""
            select
                l.tournament_year,
                l.team_id,
                l.team_name,
                l.leg_number,
                l.from_match_id,
                l.to_match_id,
                l.from_latitude,
                l.from_longitude,
                l.to_latitude,
                l.to_longitude,
                l.distance_km,
                l.is_projected
            from fct_team_travel_legs l
            where l.is_coordinate_complete = true
              and {leg_team_filter}
              {leg_scope_filter}
            order by l.tournament_year, l.team_name, l.leg_number
            """,
        )

    points = [
        AllTournamentMovementPoint(
            tournament_year=int(row["tournament_year"]),
            venue_id=row["venue_id"],
            label=row["label"],
            latitude=float(row["latitude"]),
            longitude=float(row["longitude"]),
            coordinate_precision=row.get("coordinate_precision"),
        )
        for row in point_rows
    ]
    legs = [
        AllTournamentMovementLeg(
            tournament_year=int(row["tournament_year"]),
            team_id=row["team_id"],
            team_name=row["team_name"],
            leg_number=int(row["leg_number"]),
            from_match_id=row["from_match_id"],
            to_match_id=row["to_match_id"],
            from_latitude=float(row["from_latitude"]),
            from_longitude=float(row["from_longitude"]),
            to_latitude=float(row["to_latitude"]),
            to_longitude=float(row["to_longitude"]),
            distance_km=round(float(row["distance_km"]), 1) if row["distance_km"] is not None else None,
            is_projected=bool(row["is_projected"]),
        )
        for row in leg_rows
    ]

    return AllTournamentMovementsResponse(
        scope=scope,
        total_distance_km=round(
            sum(leg.distance_km or 0 for leg in legs),
            1,
        ),
        tournament_count=len({leg.tournament_year for leg in legs}),
        point_count=len(points),
        leg_count=len(legs),
        team_count=len({leg.team_id for leg in legs}),
        points=points,
        legs=legs,
    )


def get_tournament_travel_totals(
    scope: Literal["played", "all"] = "played",
    settings: Settings | None = None,
) -> list[TournamentTravelTotal]:
    settings = settings or get_settings()
    conditions = [_real_team_predicate("team_id")]
    if scope == "played":
        conditions.append("is_projected = false")
    where_clause = "where " + " and ".join(conditions)

    with read_connection(settings) as conn:
        rows = fetch_all(
            conn,
            f"""
            select
                tournament_year,
                sum(distance_km) as total_distance_km,
                sum(case when not is_projected then distance_km else 0 end) as completed_distance_km,
                sum(case when is_projected then distance_km else 0 end) as projected_additional_distance_km,
                count(distinct team_id) as team_count,
                count(*) as leg_count
            from fct_team_travel_legs
            {where_clause}
            group by tournament_year
            order by tournament_year
            """,
        )

    return [
        TournamentTravelTotal(
            tournament_year=int(row["tournament_year"]),
            total_distance_km=round(float(row["total_distance_km"] or 0), 1),
            completed_distance_km=round(float(row["completed_distance_km"] or 0), 1),
            projected_additional_distance_km=round(
                float(row["projected_additional_distance_km"] or 0),
                1,
            ),
            team_count=int(row["team_count"]),
            leg_count=int(row["leg_count"]),
        )
        for row in rows
    ]


def get_leaderboard(
    year: int,
    scope: Literal["played", "all"] = "played",
    settings: Settings | None = None,
) -> LeaderboardResponse:
    settings = settings or get_settings()
    total_expr = "completed_distance_km" if scope == "played" else "total_distance_km"
    team_filter = _real_team_predicate("agg.team_id")
    with read_connection(settings) as conn:
        rows = fetch_all(
            conn,
            f"""
            select
                row_number() over (order by {total_expr} desc, team_name) as travel_rank,
                team_id,
                team_name,
                {total_expr} as total_distance_km,
                completed_distance_km,
                projected_additional_distance_km,
                match_count
            from agg_team_tournament_travel agg
            where agg.tournament_year = ?
              and {team_filter}
            order by travel_rank
            """,
            [year],
        )
    return LeaderboardResponse(
        tournament_year=year,
        entries=[
            LeaderboardEntry(
                rank=int(r["travel_rank"]),
                team_id=r["team_id"],
                team_name=r["team_name"],
                total_distance_km=round(float(r["total_distance_km"]), 1),
                completed_distance_km=round(float(r["completed_distance_km"]), 1),
                projected_additional_distance_km=round(float(r["projected_additional_distance_km"]), 1),
                match_count=int(r["match_count"]),
            )
            for r in rows
        ],
    )


def get_venue(venue_id: str, settings: Settings | None = None) -> VenueDetail | None:
    settings = settings or get_settings()
    appearance_team_filter = _real_team_predicate("a.team_id")
    placeholder_team_filter = _real_team_predicate("placeholder.team_id")
    with read_connection(settings) as conn:
        venue = fetch_one(
            conn,
            """
            select venue_id, tournament_year, canonical_venue_name, city, country,
                   country_code, latitude, longitude, coordinate_precision, raw_ground
            from dim_venues where venue_id = ?
            """,
            [venue_id],
        )
        if not venue:
            return None
        matches = fetch_all(
            conn,
            f"""
            select m.match_id, m.tournament_year, m.match_date, m.team1_name, m.team2_name, m.round_name
            from fct_matches m
            where m.match_id in (
                select a.match_id
                from fct_team_match_appearances a
                where a.venue_id = ?
                  and {appearance_team_filter}
            )
            and not exists (
                select 1
                from fct_team_match_appearances placeholder
                where placeholder.match_id = m.match_id
                  and not ({placeholder_team_filter})
            )
            order by m.match_date, m.source_match_index
            """,
            [venue_id],
        )
    return VenueDetail(
        venue_id=venue["venue_id"],
        tournament_year=int(venue["tournament_year"]),
        canonical_venue_name=venue.get("canonical_venue_name"),
        city=venue.get("city"),
        country=venue.get("country"),
        country_code=venue.get("country_code"),
        latitude=float(venue["latitude"]) if venue.get("latitude") is not None else None,
        longitude=float(venue["longitude"]) if venue.get("longitude") is not None else None,
        coordinate_precision=venue.get("coordinate_precision"),
        raw_ground=venue.get("raw_ground"),
        matches=[
            VenueMatch(
                match_id=m["match_id"],
                tournament_year=int(m["tournament_year"]),
                match_date=str(m["match_date"]) if m.get("match_date") else None,
                team1_name=m.get("team1_name"),
                team2_name=m.get("team2_name"),
                round_name=m.get("round_name"),
            )
            for m in matches
        ],
    )
