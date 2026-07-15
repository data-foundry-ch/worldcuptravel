{{ config(materialized='table') }}

select distinct
    venue_id,
    tournament_year,
    canonical_venue_name,
    city,
    country,
    country_code,
    latitude,
    longitude,
    coordinate_precision,
    raw_ground
from {{ ref('int_match_locations') }}
where venue_id is not null
