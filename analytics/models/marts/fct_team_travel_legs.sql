{{ config(materialized='table') }}

select
    tournament_year,
    team_id,
    team_name,
    leg_number,
    from_match_id,
    to_match_id,
    from_venue_id,
    to_venue_id,
    from_latitude,
    from_longitude,
    to_latitude,
    to_longitude,
    from_date,
    to_date,
    distance_km,
    cumulative_distance_km,
    is_projected,
    is_coordinate_complete
from {{ ref('int_team_travel_legs') }}
where leg_number > 0
