{{ config(materialized='table') }}

select
    tournament_year,
    team_id,
    team_name,
    total_distance_km,
    completed_distance_km,
    projected_additional_distance_km,
    match_count,
    route_leg_count,
    row_number() over (
        partition by tournament_year
        order by total_distance_km desc, team_name
    ) as travel_rank
from {{ ref('agg_team_tournament_travel') }}
order by tournament_year, travel_rank
