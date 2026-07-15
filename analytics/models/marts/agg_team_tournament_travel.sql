{{ config(materialized='table') }}

with appearances as (
    select * from {{ ref('fct_team_match_appearances') }}
),

legs as (
    select
        tournament_year,
        team_id,
        sum(case when is_coordinate_complete and distance_km is not null then distance_km else 0 end) as total_distance_km,
        sum(case when is_coordinate_complete and distance_km is not null and not is_projected then distance_km else 0 end) as completed_distance_km,
        sum(case when is_coordinate_complete and distance_km is not null and is_projected then distance_km else 0 end) as projected_additional_distance_km,
        count(*) as route_leg_count,
        sum(case when not is_coordinate_complete then 1 else 0 end) as excluded_leg_count
    from {{ ref('fct_team_travel_legs') }}
    group by 1, 2
),

match_stats as (
    select
        tournament_year,
        team_id,
        count(*) as match_count,
        sum(case when not is_played then 1 else 0 end) as scheduled_match_count,
        sum(case when latitude is null or longitude is null or coordinate_precision = 'unresolved' then 1 else 0 end) as unresolved_match_count
    from appearances
    group by 1, 2
)

select
    m.tournament_year,
    m.team_id,
    a.team_name,
    m.match_count,
    coalesce(l.route_leg_count, 0) as route_leg_count,
    coalesce(l.total_distance_km, 0) as total_distance_km,
    coalesce(l.completed_distance_km, 0) as completed_distance_km,
    coalesce(l.projected_additional_distance_km, 0) as projected_additional_distance_km,
    m.scheduled_match_count,
    m.unresolved_match_count,
    coalesce(l.excluded_leg_count, 0) as excluded_leg_count
from match_stats m
inner join (
    select distinct tournament_year, team_id, team_name from appearances
) a using (tournament_year, team_id)
left join legs l using (tournament_year, team_id)
