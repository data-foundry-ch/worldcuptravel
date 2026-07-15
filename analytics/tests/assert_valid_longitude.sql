-- Valid longitude range
select *
from {{ ref('stg_venue_coordinates') }}
where longitude is not null
  and (longitude < -180 or longitude > 180)
