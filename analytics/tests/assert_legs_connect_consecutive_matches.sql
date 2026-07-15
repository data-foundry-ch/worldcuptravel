-- Travel legs must connect consecutive sequence numbers
select l.*
from {{ ref('fct_team_travel_legs') }} l
inner join {{ ref('fct_team_match_appearances') }} from_match
    on l.from_match_id = from_match.match_id
    and l.team_id = from_match.team_id
inner join {{ ref('fct_team_match_appearances') }} to_match
    on l.to_match_id = to_match.match_id
    and l.team_id = to_match.team_id
where to_match.sequence_number != from_match.sequence_number + 1
