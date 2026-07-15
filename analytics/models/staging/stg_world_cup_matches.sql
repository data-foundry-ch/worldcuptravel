{{ config(materialized='view') }}

select
    match_id,
    tournament_year,
    tournament_name,
    source_match_index,
    round_name,
    cast(match_date as date) as match_date,
    kickoff_time_raw,
    team1_name,
    team2_name,
    group_name,
    raw_ground,
    goals_team1_ft,
    goals_team2_ft,
    goals_team1_ht,
    goals_team2_ht,
    goals_team1_et,
    goals_team2_et,
    goals_team1_pen,
    goals_team2_pen,
    is_played,
    metadata_json
from {{ ref('src_openfootball_matches') }}
