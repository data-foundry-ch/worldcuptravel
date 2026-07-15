{{ config(materialized='table') }}

select
    tournament_year,
    min(tournament_name) as tournament_name,
    count(distinct match_id) as match_count,
    count(distinct case when is_played then match_id end) as played_match_count,
    min(match_date) as first_match_date,
    max(match_date) as last_match_date
from {{ ref('stg_world_cup_matches') }}
group by tournament_year
