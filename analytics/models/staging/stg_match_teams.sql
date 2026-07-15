{{ config(materialized='view') }}

with matches as (
    select * from {{ ref('stg_world_cup_matches') }}
),

team1_rows as (
    select
        match_id,
        tournament_year,
        team1_name as team_name_raw,
        team2_name as opponent_name_raw,
        match_date,
        kickoff_time_raw,
        round_name,
        group_name,
        raw_ground,
        source_match_index,
        is_played,
        goals_team1_ft as goals_for,
        goals_team2_ft as goals_against,
        case
            when not is_played then 'scheduled'
            when goals_team1_ft > goals_team2_ft then 'win'
            when goals_team1_ft < goals_team2_ft then 'loss'
            else 'draw'
        end as result
    from matches
    where team1_name is not null
),

team2_rows as (
    select
        match_id,
        tournament_year,
        team2_name as team_name_raw,
        team1_name as opponent_name_raw,
        match_date,
        kickoff_time_raw,
        round_name,
        group_name,
        raw_ground,
        source_match_index,
        is_played,
        goals_team2_ft as goals_for,
        goals_team1_ft as goals_against,
        case
            when not is_played then 'scheduled'
            when goals_team2_ft > goals_team1_ft then 'win'
            when goals_team2_ft < goals_team1_ft then 'loss'
            else 'draw'
        end as result
    from matches
    where team2_name is not null
)

select * from team1_rows
union all
select * from team2_rows
