-- Unique team sequence numbers within tournament
select tournament_year, team_id, sequence_number, count(*) as cnt
from {{ ref('fct_team_match_appearances') }}
group by 1, 2, 3
having count(*) > 1
