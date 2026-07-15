{{ config(materialized='table') }}

select
    match_id,
    tournament_year,
    round_name,
    match_date,
    kickoff_time_raw,
    team1_name,
    team2_name,
    group_name,
    raw_ground,
    goals_team1_ft,
    goals_team2_ft,
    is_played,
    source_match_index
from {{ ref('stg_world_cup_matches') }}
