{{ config(materialized='view') }}

with sequenced as (
    select * from {{ ref('int_team_match_sequence') }}
),

legs as (
    select
        curr.tournament_year,
        curr.team_id,
        curr.team_name,
        curr.sequence_number - 1 as leg_number,
        prev.match_id as from_match_id,
        curr.match_id as to_match_id,
        prev.venue_id as from_venue_id,
        curr.venue_id as to_venue_id,
        prev.latitude as from_latitude,
        prev.longitude as from_longitude,
        curr.latitude as to_latitude,
        curr.longitude as to_longitude,
        prev.match_date as from_date,
        curr.match_date as to_date,
        prev.is_played as from_is_played,
        curr.is_played as to_is_played,
        case
            when curr.sequence_number = 1 then 0.0
            when not prev.has_coordinates or not curr.has_coordinates then null
            when prev.latitude = curr.latitude and prev.longitude = curr.longitude then 0.0
            else {{ haversine_km('prev.latitude', 'prev.longitude', 'curr.latitude', 'curr.longitude') }}
        end as distance_km,
        case
            when prev.has_coordinates and curr.has_coordinates then true
            else false
        end as is_coordinate_complete,
        case
            when curr.is_played = false or prev.is_played = false then true
            else false
        end as is_projected
    from sequenced curr
    inner join sequenced prev
        on curr.tournament_year = prev.tournament_year
        and curr.team_id = prev.team_id
        and curr.sequence_number = prev.sequence_number + 1
)

select
    *,
    sum(case when is_coordinate_complete and distance_km is not null then distance_km else 0 end)
        over (
            partition by tournament_year, team_id
            order by leg_number
            rows between unbounded preceding and current row
        ) as cumulative_distance_km
from legs
