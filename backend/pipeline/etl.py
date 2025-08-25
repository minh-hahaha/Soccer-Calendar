# Ingesting football-data and bootstrap data

from datetime import datetime
from typing import List, Dict, Any, Optional
import requests
from sqlalchemy import (
    Column, DateTime, Float, Integer, String, create_engine, Boolean, Text
)
import re

from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()

class Match(Base):
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True)
    date = Column(DateTime, nullable=False)
    home_team = Column(String, nullable=False)
    away_team = Column(String, nullable=False)
    home_score = Column(Integer)
    away_score = Column(Integer)
    matchday = Column(Integer)
    status = Column(String)
    home_team_crest = Column(String)
    away_team_crest = Column(String)
    season = Column(Integer)

class Standing(Base):
    __tablename__ = "standings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    season = Column(String, nullable=False)
    matchday = Column(Integer)
    position = Column(Integer, nullable=False)
    team = Column(String, nullable=False)
    crest = Column(String)
    played_games = Column(Integer)
    won = Column(Integer)
    draw = Column(Integer)
    lost = Column(Integer)
    points = Column(Integer)
    goal_difference = Column(Integer)
    form = Column(String)

class Head2Head(Base):
    __tablename__ = "head2head"

    id = Column(Integer, primary_key=True, autoincrement=True)
    match_id = Column(Integer, nullable=False)
    home_team = Column(String, nullable=False)
    away_team = Column(String, nullable=False)
    # Store aggregated stats
    total_matches = Column(Integer)
    home_wins = Column(Integer)
    draws = Column(Integer)
    away_wins = Column(Integer)
    last_winner = Column(String)  # Winner of the most recent match
    # Store raw data as JSON text for flexibility
    raw_matches = Column(Text)  # JSON string of historical matches

class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    short_name = Column(String, nullable=False)
    tla = Column(String)  # Three Letter Abbreviation
    crest = Column(String)
    season = Column(String)

class Player(Base):
    __tablename__ = "players"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    team = Column(String, nullable=False)
    position = Column(String)
    price = Column(Float)

### FETCH DATA ###
def fetch_football_matches(api_key: str, season: str = "2024") -> List[Dict[str, Any]]:
    """Fetch raw match data from football-data.org."""
    headers = {"X-Auth-Token": api_key}
    url = f"https://api.football-data.org/v4/competitions/PL/matches?season={season}"
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    return response.json().get("matches", [])


def fetch_standings(api_key: str, season: str = "2024", matchday: Optional[int] = None) -> Dict[str, Any]:
    """Fetch standings from football-data.org."""
    headers = {"X-Auth-Token": api_key}
    url = f"https://api.football-data.org/v4/competitions/PL/standings?season={season}"
    if matchday:
        url += f"&matchday={matchday}"
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    return response.json()

def fetch_teams(api_key: str, season: str = "2024") -> Dict[str, Any]:
    """Fetch teams from football-data.org."""
    headers = {"X-Auth-Token": api_key}
    url = f"https://api.football-data.org/v4/competitions/PL/teams?season={season}"
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    return response.json()

# def fetch_head2head(api_key: str, match_id: int) -> Dict[str, Any]:
#     """Fetch head-to-head data for a specific match."""
#     headers = {"X-Auth-Token": api_key}
#     url = f"https://api.football-data.org/v4/matches/{match_id}/head2head"
#     response = requests.get(url, headers=headers, timeout=30)
#     response.raise_for_status()
#     return response.json()

def fetch_fantasy_bootstrap() -> Dict[str, Any]:
    """Fetch raw fantasy bootstrap data."""
    url = "https://fantasy.premierleague.com/api/bootstrap-static/"
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.json()

def normalize_team_name(name: str) -> str:
    """Normalize team names by removing common suffixes and title-casing."""
    if not name:
        return name
    # Remove ' FC' or 'Fc' at the end, ignore case, and strip
    name = re.sub(r"\s+FC$", "", name.strip(), flags=re.IGNORECASE)
    return name.title()


### CLEAN DATA ####
def clean_match_data(raw_matches: List[Dict[str, Any]], season: Integer = 2025) -> List[Dict[str, Any]]:
    """Clean raw match data - combines fixtures and finished matches."""
    cleaned = []
    for match in raw_matches:
        date_str = match.get("utcDate")
        try:
            date = datetime.fromisoformat(date_str.replace("Z", "+00:00")) if date_str else None
        except Exception:
            date = None
        
        # Get scores (will be None for future matches)
        home_score = match.get("score", {}).get("fullTime", {}).get("home")
        away_score = match.get("score", {}).get("fullTime", {}).get("away")
        
        cleaned.append({
            "id": match.get("id"),
            "date": date,
            "home_team": normalize_team_name(match.get("homeTeam", {}).get("shortName", "")),
            "away_team": normalize_team_name(match.get("awayTeam", {}).get("shortName", "")),
            "home_score": home_score,
            "away_score": away_score,
            "matchday": match.get("matchday"),
            "status": match.get("status"),
            "home_team_crest": match.get("homeTeam", {}).get("crest"),
            "away_team_crest": match.get("awayTeam", {}).get("crest"),
            "season": season
        })
    return cleaned

def clean_standings_data(raw_standings: Dict[str, Any], season: str = "2024", matchday: Optional[int] = None) -> List[Dict[str, Any]]:
    """Clean raw standings data."""
    cleaned = []
    
    # Get the standings table (usually the first one for "TOTAL")
    standings_data = raw_standings.get("standings", [])
    if not standings_data:
        return cleaned
    
    table = standings_data[0].get("table", [])
    
    for team_standing in table:
        team_info = team_standing.get("team", {})
        cleaned.append({
            "season": season,
            "matchday": matchday,
            "position": team_standing.get("position"),
            "team": normalize_team_name(team_info.get("shortName", "")),
            "crest": team_info.get("crest"),
            "played_games": team_standing.get("playedGames"),
            "won": team_standing.get("won"),
            "draw": team_standing.get("draw"),
            "lost": team_standing.get("lost"),
            "points": team_standing.get("points"),
            "goal_difference": team_standing.get("goalDifference"),
            "form": team_standing.get("form")
        })
    
    return cleaned

def clean_head2head_data(raw_h2h: Dict[str, Any], match_id: int) -> Dict[str, Any]:
    """Clean raw head-to-head data."""
    import json
    
    # Get aggregated stats
    aggregated = raw_h2h.get("aggregates", {})
    
    # Get match info
    matches = raw_h2h.get("matches", [])
    
    # Calculate basic stats
    home_wins = aggregated.get("homeTeam", {}).get("wins", 0)
    away_wins = aggregated.get("awayTeam", {}).get("wins", 0)
    draws = aggregated.get("draws", 0)
    total_matches = aggregated.get("numberOfMatches", 0)
    
    # Get team names from the first match if available
    home_team = ""
    away_team = ""
    last_winner = None
    
    if matches:
        # Get team names from most recent match
        recent_match = matches[0]  # Assuming matches are ordered by date
        home_team = normalize_team_name(recent_match.get("homeTeam", {}).get("shortName", ""))
        away_team = normalize_team_name(recent_match.get("awayTeam", {}).get("shortName", ""))
        
        # Determine last winner
        score = recent_match.get("score", {}).get("fullTime", {})
        if score:
            home_score = score.get("home")
            away_score = score.get("away")
            if home_score is not None and away_score is not None:
                if home_score > away_score:
                    last_winner = home_team
                elif away_score > home_score:
                    last_winner = away_team
                else:
                    last_winner = "Draw"
    
    return {
        "match_id": match_id,
        "home_team": home_team,
        "away_team": away_team,
        "total_matches": total_matches,
        "home_wins": home_wins,
        "draws": draws,
        "away_wins": away_wins,
        "last_winner": last_winner,
        "raw_matches": json.dumps(matches)  # Store as JSON string
    }

def clean_teams_data(raw_teams: Dict[str, Any], season: str = "2024") -> List[Dict[str, Any]]:
    """Clean raw teams data."""
    cleaned = []
    
    teams = raw_teams.get("teams", [])
    for team in teams:
        cleaned.append({
            "id": team.get("id"),
            "name": normalize_team_name(team.get("name", "")),
            "short_name": normalize_team_name(team.get("shortName", "")),
            "tla": team.get("tla"),
            "crest": team.get("crest"),
            "season": season
        })
    
    return cleaned

def clean_player_data(raw_bootstrap: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Clean raw player data from fantasy bootstrap."""
    teams = {
        team["id"]: normalize_team_name(team["name"])
        for team in raw_bootstrap.get("teams", [])
    }
    players = []
    for element in raw_bootstrap.get("elements", []):
        players.append({
            "id": element.get("id"),
            "name": f"{element.get('first_name', '')} {element.get('web_name', '')}".strip(),
            "team": teams.get(element.get("team")),
            "position": str(element.get("element_type")),
            "price": element.get("now_cost", 0) / 10.0,
        })
    return players

def get_session(database_url: str):
    """Create a database session and initialize tables."""
    engine = create_engine(database_url)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()

### STORE DATA ####
def store_matches(session, matches: List[Dict[str, Any]]):
    """Store cleaned match data using SQLAlchemy."""
    # Clear existing matches for the season to avoid duplicates
    if matches:
        season = matches[0].get("season")
        if season:
            session.query(Match).filter(Match.season == season).delete()
    
    session.bulk_insert_mappings(Match, matches)
    session.commit()

def store_standings(session, standings: List[Dict[str, Any]]):
    """Store cleaned standings data using SQLAlchemy."""
    # Clear existing standings for the season/matchday to avoid duplicates
    if standings:
        season = standings[0].get("season")
        matchday = standings[0].get("matchday")
        
        query = session.query(Standing).filter(Standing.season == season)
        if matchday:
            query = query.filter(Standing.matchday == matchday)
        query.delete()
    
    session.bulk_insert_mappings(Standing, standings)
    session.commit()

def store_head2head(session, h2h_data: Dict[str, Any]):
    """Store cleaned head-to-head data using SQLAlchemy."""
    # Check if record exists and update, otherwise insert
    existing = session.query(Head2Head).filter(
        Head2Head.match_id == h2h_data["match_id"]
    ).first()
    
    if existing:
        # Update existing record
        for key, value in h2h_data.items():
            setattr(existing, key, value)
    else:
        # Insert new record
        session.add(Head2Head(**h2h_data))
    
    session.commit()

def store_teams(session, teams: List[Dict[str, Any]]):
    """Store cleaned teams data using SQLAlchemy."""
    # Clear existing teams for the season to avoid duplicates
    if teams:
        season = teams[0].get("season")
        if season:
            session.query(Team).filter(Team.season == season).delete()
    
    session.bulk_insert_mappings(Team, teams)
    session.commit()

def store_players(session, players: List[Dict[str, Any]]):
    """Store cleaned player data using SQLAlchemy."""
    # Clear existing players to avoid duplicates
    session.query(Player).delete()
    session.bulk_insert_mappings(Player, players)
    session.commit()



# Complete data ingestion function
def ingest_all_football_data(api_key: str, database_url: str, season: str = "2025"):
    """Complete function to ingest all football data."""
    session = get_session(database_url)
    
    try:
        # 1. Fetch and store teams
        print("Fetching teams data...")
        raw_teams = fetch_teams(api_key, season)
        clean_teams = clean_teams_data(raw_teams, season)
        store_teams(session, clean_teams)
        print(f"Stored {len(clean_teams)} teams")
        
        # 2. Fetch and store all matches (combines fixtures and finished matches)
        print("Fetching matches data...")
        raw_matches = fetch_football_matches(api_key, season)
        clean_matches = clean_match_data(raw_matches, season)
        store_matches(session, clean_matches)
        print(f"Stored {len(clean_matches)} matches")
        
        # 3. Fetch and store current standings
        print("Fetching standings data...")
        raw_standings = fetch_standings(api_key, season)
        clean_standings = clean_standings_data(raw_standings, season)
        store_standings(session, clean_standings)
        print(f"Stored {len(clean_standings)} standings entries")
        
        # 4. Fetch head-to-head data for recent matches (optional - can be resource intensive)
        # print("Fetching head-to-head data for recent matches...")
        # recent_matches = [m for m in clean_matches if m["status"] in ["SCHEDULED", "TIMED", "IN_PLAY"]][:5]  # Limit to 5 recent matches
        # for match in recent_matches:
        #     try:
        #         raw_h2h = fetch_head2head(api_key, match["id"])
        #         clean_h2h = clean_head2head_data(raw_h2h, match["id"])
        #         store_head2head(session, clean_h2h)
        #     except Exception as e:
        #         print(f"Failed to fetch H2H for match {match['id']}: {e}")
        
        # # 5. Fetch and store fantasy players
        # print("Fetching fantasy players data...")
        # raw_bootstrap = fetch_fantasy_bootstrap()
        # clean_players = clean_player_data(raw_bootstrap)
        # store_players(session, clean_players)
        # print(f"Stored {len(clean_players)} players")
        
        # print("Data ingestion completed successfully!")
        
    except Exception as e:
        session.rollback()
        print(f"Error during data ingestion: {e}")
        raise
    finally:
        session.close()
def ingest_players(database_url: str):
    """Complete function to ingest all football data."""
    session = get_session(database_url)
    
    try:
        # 5. Fetch and store fantasy players
        print("Fetching fantasy players data...")
        raw_bootstrap = fetch_fantasy_bootstrap()
        clean_players = clean_player_data(raw_bootstrap)
        store_players(session, clean_players)
        print(f"Stored {len(clean_players)} players")
        
        print("Data ingestion completed successfully!")
        
    except Exception as e:
        session.rollback()
        print(f"Error during data ingestion: {e}")
        raise
    finally:
        session.close()

# Usage example:
# ingest_all_football_data("your_api_key", "postgresql://user:pass@localhost/db", "2025")