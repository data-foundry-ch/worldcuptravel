-- Non-negative distances
select *
from {{ ref('fct_team_travel_legs') }}
where distance_km < 0
