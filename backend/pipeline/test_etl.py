from datetime import datetime
import os
import sys

import pytest

# Ensure project root is on the Python path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.pipeline.etl import (
    Match,
    Player,
    clean_match_data,
    clean_player_data,
    get_session,
    store_matches,
    store_players,
)


def test_clean_match_data():
    raw = [
        {
            "id": 497412,
            "utcDate": "2024-05-04T14:00:00Z",
            "homeTeam": {"name": "ARSENAL FC"},
            "awayTeam": {"name": "chelsea fc"},
            "score": {"fullTime": {"home": 2, "away": 1}},
        }
    ]
    cleaned = clean_match_data(raw)
    match = cleaned[0]
    assert match["home_team"] == "Arsenal"
    assert match["away_team"] == "Chelsea"
    assert isinstance(match["date"], datetime)

test_clean_match_data()

def test_clean_player_data():
    raw = {
        "teams": [{"id": 1, "name": "Arsenal FC"}],
        "elements": [
            {
                "id": 10,
                "web_name": "Saka",
                "team": 1,
                "element_type": "MID",
                "now_cost": 85,
            }
        ],
    }
    players = clean_player_data(raw)
    player = players[0]
    assert player["team"] == "Arsenal"
    assert player["price"] == 8.5

test_clean_player_data()

def test_store_data_with_sqlalchemy():
    session = get_session("sqlite:///:memory:")
    matches = [
        {
            "id": 1,
            "date": datetime(2024, 5, 4),
            "home_team": "Arsenal",
            "away_team": "Chelsea",
            "home_score": 2,
            "away_score": 1,
        }
    ]
    players = [
        {
            "id": 10,
            "name": "Saka",
            "team": "Arsenal",
            "position": "MID",
            "price": 8.5,
        }
    ]
    store_matches(session, matches)
    store_players(session, players)
    assert session.query(Match).count() == 1
    assert session.query(Player).count() == 1

test_store_data_with_sqlalchemy()