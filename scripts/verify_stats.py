import duckdb

c = duckdb.connect("data/worldcup.duckdb", read_only=True)
uruguay = c.execute(
    """
    select total_distance_km, match_count, route_leg_count
    from agg_team_tournament_travel
    where tournament_year=1930 and team_id='uruguay'
    """
).fetchone()
print("Uruguay 1930:", uruguay)
print("\nUnresolved venues by tournament:")
print(
    c.execute(
        """
        select tournament_year, unresolved_venues, coverage_pct
        from data_quality_venue_coverage
        where tournament_year > 0
        order by tournament_year
        """
    ).fetchdf().to_string()
)
