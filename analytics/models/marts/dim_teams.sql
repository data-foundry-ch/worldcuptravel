{{ config(materialized='table') }}

select distinct
    team_id,
    team_name,
    tournament_year
from {{ ref('int_match_locations') }}
order by tournament_year, team_name
