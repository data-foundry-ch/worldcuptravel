import duckdb

c = duckdb.connect("data/worldcup.duckdb", read_only=True)
print("Brazil 1990 appearances:")
print(
    c.execute(
        """
        select match_id, sequence_number, match_date, opponent_name, raw_ground
        from fct_team_match_appearances
        where tournament_year=1990 and team_id='brazil'
        order by sequence_number
        """
    ).fetchdf()
)
print("Brazil 1990 legs:")
print(
    c.execute(
        """
        select leg_number, from_match_id, to_match_id, distance_km
        from fct_team_travel_legs
        where tournament_year=1990 and team_id='brazil'
        """
    ).fetchdf()
)
print("Brazil int_match_locations count:")
print(
    c.execute(
        """
        select match_id, team_id, raw_ground, resolved_raw_ground, venue_id
        from int_match_locations
        where tournament_year=1990 and team_id='brazil'
        order by match_id
        """
    ).fetchdf()
)
print("Source matches duplicates 1990:")
print(
    c.execute(
        """
        select match_id, team1_name, team2_name, raw_ground, source_match_index
        from stg_world_cup_matches where tournament_year=1990
        order by source_match_index
        """
    ).fetchdf()
)
