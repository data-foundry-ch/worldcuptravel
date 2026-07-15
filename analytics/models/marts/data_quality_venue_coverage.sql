{{ config(materialized='table') }}

with venues as (
    select
        tournament_year,
        raw_ground,
        has_coordinates,
        coordinate_precision
    from {{ ref('int_match_locations') }}
),

distinct_venues as (
    select distinct
        tournament_year,
        raw_ground,
        max(has_coordinates) as has_coordinates,
        max(coordinate_precision) as coordinate_precision
    from venues
    group by 1, 2
)

select
    tournament_year,
    count(*) as total_venues,
    sum(case when has_coordinates then 1 else 0 end) as resolved_venues,
    sum(case when not has_coordinates or coordinate_precision = 'unresolved' then 1 else 0 end) as unresolved_venues,
    round(
        100.0 * sum(case when has_coordinates then 1 else 0 end) / nullif(count(*), 0),
        2
    ) as coverage_pct
from distinct_venues
group by tournament_year

union all

select
    0 as tournament_year,
    count(*) as total_venues,
    sum(case when has_coordinates then 1 else 0 end) as resolved_venues,
    sum(case when not has_coordinates or coordinate_precision = 'unresolved' then 1 else 0 end) as unresolved_venues,
    round(
        100.0 * sum(case when has_coordinates then 1 else 0 end) / nullif(count(*), 0),
        2
    ) as coverage_pct
from distinct_venues
