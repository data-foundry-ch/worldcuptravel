-- No duplicate tournament/team/leg-number
select tournament_year, team_id, leg_number, count(*) as cnt
from {{ ref('fct_team_travel_legs') }}
group by 1, 2, 3
having count(*) > 1
