{{ config(materialized='view') }}

with matches as (
    select * from {{ ref('stg_match_teams') }}
),

aliases as (
    select * from {{ ref('stg_team_aliases') }}
),

venue_coords as (
    select * from {{ ref('stg_venue_coordinates') }}
),

venue_aliases as (
    select * from {{ ref('venue_aliases') }}
),

resolved_grounds as (
    select
        m.*,
        coalesce(va.raw_ground_canonical, m.raw_ground) as resolved_raw_ground,
        {{ normalize_ground('coalesce(va.raw_ground_canonical, m.raw_ground)') }} as normalized_ground
    from matches m
    left join venue_aliases va
        on m.tournament_year = cast(va.tournament_year as integer)
        and {{ normalize_ground('m.raw_ground') }} = {{ normalize_ground('va.raw_ground_alias') }}
),

with_venues as (
    select
        rg.*,
        vc.venue_id,
        vc.canonical_venue_name,
        vc.city,
        vc.country,
        vc.country_code,
        vc.latitude,
        vc.longitude,
        vc.coordinate_precision,
        coalesce(cast(ta.team_id as varchar), {{ normalize_ground('rg.team_name_raw') }}) as team_id,
        coalesce(cast(ta.team_name_canonical as varchar), rg.team_name_raw) as team_name,
        coalesce(cast(oa.team_id as varchar), {{ normalize_ground('rg.opponent_name_raw') }}) as opponent_id,
        coalesce(cast(oa.team_name_canonical as varchar), rg.opponent_name_raw) as opponent_name
    from resolved_grounds rg
    left join venue_coords vc
        on rg.tournament_year = vc.tournament_year
        and rg.normalized_ground = vc.normalized_ground
    left join aliases ta
        on rg.tournament_year = ta.tournament_year
        and {{ normalize_ground('rg.team_name_raw') }} = {{ normalize_ground('ta.team_name_raw') }}
    left join aliases oa
        on rg.tournament_year = oa.tournament_year
        and {{ normalize_ground('rg.opponent_name_raw') }} = {{ normalize_ground('oa.team_name_raw') }}
)

select
    match_id,
    tournament_year,
    team_id,
    team_name,
    team_name_raw,
    opponent_id,
    opponent_name,
    opponent_name_raw,
    match_date,
    kickoff_time_raw,
    round_name,
    group_name,
    raw_ground,
    resolved_raw_ground,
    venue_id,
    canonical_venue_name,
    city,
    country,
    country_code,
    latitude,
    longitude,
    coordinate_precision,
    source_match_index,
    is_played,
    goals_for,
    goals_against,
    result,
    case
        when latitude is not null
            and longitude is not null
            and coordinate_precision is not null
            and coordinate_precision != 'unresolved'
        then true
        else false
    end as has_coordinates
from with_venues
