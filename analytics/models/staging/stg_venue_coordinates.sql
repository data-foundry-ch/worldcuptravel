{{ config(materialized='view') }}

with seed as (
    select
        cast(tournament_year as integer) as tournament_year,
        raw_ground,
        venue_id,
        canonical_venue_name,
        city,
        country,
        country_code,
        cast(latitude as double) as latitude,
        cast(longitude as double) as longitude,
        coordinate_precision,
        source_name,
        source_reference,
        verified_at,
        notes,
        {{ normalize_ground('raw_ground') }} as normalized_ground
    from {{ ref('venue_coordinates') }}
),

deduped as (
    select *
    from (
        select
            *,
            row_number() over (
                partition by tournament_year, normalized_ground
                order by raw_ground
            ) as row_num
        from seed
    ) ranked
    where row_num = 1
)

select
    tournament_year,
    raw_ground,
    venue_id,
    canonical_venue_name,
    city,
    country,
    country_code,
    latitude,
    longitude,
    coordinate_precision,
    source_name,
    source_reference,
    verified_at,
    notes,
    normalized_ground,
    concat(cast(tournament_year as varchar), '|', normalized_ground) as venue_lookup_key
from deduped
