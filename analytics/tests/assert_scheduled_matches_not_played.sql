-- Scheduled matches must be marked not played
select *
from {{ ref('fct_team_match_appearances') }}
where is_played = false
  and result != 'scheduled'
