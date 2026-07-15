from app.services.ingestion import build_tournament_url, flatten_match, generate_match_id


def test_build_tournament_url() -> None:
    url = build_tournament_url("https://raw.githubusercontent.com/openfootball/worldcup.json", "master", 2022)
    assert url == "https://raw.githubusercontent.com/openfootball/worldcup.json/master/2022/worldcup.json"


def test_generate_match_id_deterministic() -> None:
    a = generate_match_id(1930, "1930-07-13", 0, "France", "Mexico")
    b = generate_match_id(1930, "1930-07-13", 0, "France", "Mexico")
    assert a == b
    assert len(a) == 32


def test_flatten_match_scheduled_without_score() -> None:
    row = flatten_match(
        2026,
        {
            "round": "Matchday 1",
            "date": "2026-06-11",
            "team1": "Mexico",
            "team2": "South Africa",
            "ground": "Mexico City",
        },
        0,
        "World Cup 2026",
    )
    assert row["is_played"] is False
    assert row["goals_team1_ft"] is None
