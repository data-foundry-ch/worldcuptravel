{{ config(materialized='view') }}

select
    *,
    row_number() over (
        partition by tournament_year, team_id
        order by
            match_date nulls last,
            kickoff_time_raw nulls last,
            source_match_index
    ) as sequence_number
from {{ ref('int_match_locations') }}
