{{ config(materialized='view') }}

select
    cast(tournament_year as integer) as tournament_year,
    team_name_raw,
    team_name_canonical,
    team_id,
    notes
from {{ ref('team_aliases') }}
