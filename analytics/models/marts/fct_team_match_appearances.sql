{{ config(materialized='table') }}

with legs as (
    select
        tournament_year,
        team_id,
        to_match_id as match_id,
        max(cumulative_distance_km) as cumulative_distance_km
    from {{ ref('int_team_travel_legs') }}
    where leg_number > 0
    group by 1, 2, 3
)

select
    h.match_id,
    h.tournament_year,
    h.team_id,
    h.team_name,
    h.opponent_id,
    h.opponent_name,
    h.match_date,
    h.kickoff_time_raw,
    h.round_name,
    h.group_name,
    h.raw_ground,
    h.venue_id,
    h.latitude,
    h.longitude,
    h.coordinate_precision,
    h.source_match_index,
    h.is_played,
    h.goals_for,
    h.goals_against,
    h.result,
    h.sequence_number,
    coalesce(l.cumulative_distance_km, 0) as cumulative_distance_km
from {{ ref('int_team_match_history') }} h
left join legs l
    on h.tournament_year = l.tournament_year
    and h.team_id = l.team_id
    and h.match_id = l.match_id
