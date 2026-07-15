-- Cumulative distance should never decrease
select *
from (
    select
        tournament_year,
        team_id,
        leg_number,
        cumulative_distance_km,
        lag(cumulative_distance_km) over (
            partition by tournament_year, team_id order by leg_number
        ) as prev_cumulative
    from {{ ref('fct_team_travel_legs') }}
) t
where prev_cumulative is not null
  and cumulative_distance_km < prev_cumulative
