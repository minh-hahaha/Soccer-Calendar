from typing import List, Dict, Any
from datetime import datetime
from backend.database.models import Team, Match, StandingsSnapshot, Lineup


def map_team(team_data: Dict[str, Any]) -> Team:
    """Map API team data to Team model"""
    return Team(
        id=team_data["id"],
        name=team_data["name"],
        tla=team_data.get("tla"),
        area_name=team_data.get("area", {}).get("name")
    )


def map_match(match_data: Dict[str, Any]) -> Match:
    """Map API match data to Match model"""
    return Match(
        id=match_data["id"],
        season=match_data["season"]["id"],
        utc_date=datetime.fromisoformat(match_data["utcDate"].replace("Z", "+00:00")),
        matchday=match_data["matchday"],
        status=match_data["status"],
        stage=match_data.get("stage"),
        home_team_id=match_data["homeTeam"]["id"],
        away_team_id=match_data["awayTeam"]["id"],
        home_score=match_data["score"]["fullTime"]["home"],
        away_score=match_data["score"]["fullTime"]["away"],
        venue=match_data.get("venue"),
        city=match_data.get("area", {}).get("name")
    )


def map_standings_snapshot(standings_data: Dict[str, Any], season: int, matchday: int) -> List[StandingsSnapshot]:
    """Map API standings data to StandingsSnapshot models"""
    snapshots = []
    
    for table in standings_data["standings"]:
        if table["type"] == "TOTAL":  # Use total standings
            for position, team_data in enumerate(table["table"], 1):
                snapshot = StandingsSnapshot(
                    season=season,
                    matchday=matchday,
                    team_id=team_data["team"]["id"],
                    position=team_data["position"],
                    played_games=team_data["playedGames"],
                    points=team_data["points"],
                    goals_for=team_data["goalsFor"],
                    goals_against=team_data["goalsAgainst"],
                    goal_diff=team_data["goalDifference"]
                )
                snapshots.append(snapshot)
            break
    
    return snapshots


def map_lineup(lineup_data: Dict[str, Any], match_id: int, team_id: int) -> List[Lineup]:
    """Map API lineup data to Lineup models"""
    lineups = []
    
    # Map starting lineup
    for player in lineup_data.get("startXI", []):
        lineups.append(Lineup(
            match_id=match_id,
            team_id=team_id,
            person_id=player["id"],
            started=True,
            minutes=90,  # Default for starters
            yellow_cards=0,
            red_cards=0
        ))
    
    # Map substitutes
    for player in lineup_data.get("substitutes", []):
        lineups.append(Lineup(
            match_id=match_id,
            team_id=team_id,
            person_id=player["id"],
            started=False,
            minutes=0,  # Will be updated if substitution data available
            yellow_cards=0,
            red_cards=0
        ))
    
    return lineups
