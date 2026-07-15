-- Valid latitude range
select *
from {{ ref('stg_venue_coordinates') }}
where latitude is not null
  and (latitude < -90 or latitude > 90)
