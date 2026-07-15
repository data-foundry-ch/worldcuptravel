-- No travel leg from a match to itself
select *
from {{ ref('fct_team_travel_legs') }}
where from_match_id = to_match_id
