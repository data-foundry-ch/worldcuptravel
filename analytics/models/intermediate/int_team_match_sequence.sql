{{ config(materialized='view') }}

select
    tournament_year,
    team_id,
    team_name,
    match_id,
    match_date,
    kickoff_time_raw,
    source_match_index,
    sequence_number,
    venue_id,
    latitude,
    longitude,
    coordinate_precision,
    has_coordinates,
    is_played,
    round_name,
    opponent_name,
    result,
    raw_ground,
    canonical_venue_name
from {{ ref('int_team_match_history') }}
