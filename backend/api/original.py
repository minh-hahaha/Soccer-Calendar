import os
from datetime import datetime
from typing import Optional

import requests
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from ..database import get_db, db_manager

# Load environment variables from .env file
load_dotenv()

router = APIRouter()

API_FOOTBALL_KEY = os.getenv("FD_API_KEY")
BASE_URL = "https://api.football-data.org/v4"

# ============================================================================
# EXISTING ENDPOINTS (Unchanged)
# ============================================================================


@router.get("/fixtures")
def get_fixtures(
    # Query parameters for documentation and Type Checking
    team: Optional[str] = Query(None),  # use shortName
    matchday: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    season: Optional[str] = Query(2025),
    db: Session = Depends(get_db),
):
    # Check for cached data first
    cached_fixtures = db_manager.get_football_fixtures(
        db, season=str(season), matchday=matchday, status=status, team_filter=team
    )
    
    if cached_fixtures and cached_fixtures.is_fresh(max_age_hours=2):
        print("Using cached fixtures data from database")
        return cached_fixtures.data
    
    # Get data from API
    print("Fetching fresh fixtures data from football-data.org API...")
    headers = {"X-Auth-Token": API_FOOTBALL_KEY}

    url = f"{BASE_URL}/competitions/PL/matches?season={season}"

    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        return HTTPException(status_code=response.status_code, detail=response.text)

    data = response.json()["matches"]

    # filter data based on query parameters
    filtered_data = []
    for match in data:
        # matchday, status, team are inputs
        if matchday and match["matchday"] != matchday:
            continue  # go to the next match
        if status and match["status"] != status:
            continue  # go to the next match
        if team and (
            team.lower() not in match["homeTeam"]["shortName"].lower()
            and team.lower() not in match["awayTeam"]["shortName"].lower()
        ):
            continue  # go to the next match

        # Get score information for finished matches
        home_score = match.get("score", {}).get("fullTime", {}).get("home")
        away_score = match.get("score", {}).get("fullTime", {}).get("away")

        # Create display time/score based on match status
        if (
            match["status"] == "FINISHED"
            and home_score is not None
            and away_score is not None
        ):
            display_time = f"{home_score} - {away_score}"
        else:
            # Format the UTC date to show time
            try:
                match_date = datetime.fromisoformat(
                    match["utcDate"].replace("Z", "+00:00")
                )
                display_time = match_date.strftime("%H:%M")
            except:
                display_time = match["utcDate"]

        filtered_data.append(
            {
                "id": match["id"],
                "utcDate": match["utcDate"],
                "displayTime": display_time,
                "homeTeam": match["homeTeam"]["shortName"],
                "awayTeam": match["awayTeam"]["shortName"],
                "matchday": match["matchday"],
                "status": match["status"],
                "homeTeamCrest": match["homeTeam"]["crest"],
                "awayTeamCrest": match["awayTeam"]["crest"],
                "homeScore": home_score,
                "awayScore": away_score,
            }
        )

    result = {"fixtures": filtered_data}
    
    # Cache the result
    db_manager.save_football_fixtures(
        db, season=str(season), data=result, 
        matchday=matchday, status=status, team_filter=team
    )
    print(f"Saved fixtures data to database for season {season}")
    
    return result


@router.get("/finished-matches")
def get_finished_matches(
    team: Optional[str] = Query(None),  # use shortName
    matchday: Optional[int] = Query(None),
    season: Optional[str] = Query(2025),
    db: Session = Depends(get_db),
):
    # Check for cached data first
    cached_fixtures = db_manager.get_football_fixtures(
        db, season=str(season), status="FINISHED", team_filter=team
    )
    
    if cached_fixtures and cached_fixtures.is_fresh(max_age_hours=2):
        print("Using cached finished matches data from database")
        return cached_fixtures.data
    
    # Get data from API
    print("Fetching fresh finished matches data from football-data.org API...")
    headers = {"X-Auth-Token": API_FOOTBALL_KEY}

    url = f"{BASE_URL}/competitions/PL/matches?season={season}&status=FINISHED"

    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        return HTTPException(status_code=response.status_code, detail=response.text)

    data = response.json()["matches"]

    # filter data based on query parameters
    filtered_data = []
    for match in data:
        # matchday, team are inputs
        if matchday and match["matchday"] != matchday:
            continue  # go to the next match
        if team and (
            team.lower() not in match["homeTeam"]["shortName"].lower()
            and team.lower() not in match["awayTeam"]["shortName"].lower()
        ):
            continue  # go to the next match

        # Get score information for finished matches
        home_score = match.get("score", {}).get("fullTime", {}).get("home")
        away_score = match.get("score", {}).get("fullTime", {}).get("away")

        filtered_data.append(
            {
                "id": match["id"],
                "utcDate": match["utcDate"],
                "homeTeam": match["homeTeam"]["shortName"],
                "awayTeam": match["awayTeam"]["shortName"],
                "matchday": match["matchday"],
                "status": match["status"],
                "homeTeamCrest": match["homeTeam"]["crest"],
                "awayTeamCrest": match["awayTeam"]["crest"],
                "homeScore": home_score,
                "awayScore": away_score,
            }
        )

    result = {"finished_matches": filtered_data}
    
    # Cache the result
    db_manager.save_football_fixtures(
        db, season=str(season), data=result, 
        status="FINISHED", team_filter=team
    )
    print(f"Saved finished matches data to database for season {season}")
    
    return result


@router.get("/teams")
def get_teams(season: str = Query(2025), db: Session = Depends(get_db)):
    # Check for cached data first
    cached_teams = db_manager.get_football_teams(db, season=str(season))
    
    if cached_teams and cached_teams.is_fresh(max_age_hours=24):
        print("Using cached teams data from database")
        return cached_teams.data
    
    # Get data from API
    print("Fetching fresh teams data from football-data.org API...")
    headers = {"X-Auth-Token": API_FOOTBALL_KEY}

    url = f"{BASE_URL}/competitions/PL/teams?season={season}"

    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        return HTTPException(status_code=response.status_code, detail=response.text)

    data = response.json()["teams"]

    # Return simplified teams data
    result = {
        "teams": [
            {
                "id": team["id"],
                "name": team["name"],
                "shortName": team["shortName"],
                "crest": team["crest"],
                "tla": team["tla"],
            }
            for team in data
        ]
    }
    
    # Cache the result
    db_manager.save_football_teams(db, season=str(season), data=result)
    print(f"Saved teams data to database for season {season}")
    
    return result


@router.get("/standings")
def get_standings(
    season: int = Query(2025),
    matchday: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    # Check for cached data first
    cached_standings = db_manager.get_football_standings(db, season=str(season), matchday=matchday)
    
    if cached_standings and cached_standings.is_fresh(max_age_hours=4):
        print("Using cached standings data from database")
        return cached_standings.data
    
    # Get data from API
    print("Fetching fresh standings data from football-data.org API...")
    headers = {"X-Auth-Token": API_FOOTBALL_KEY}

    url = f"{BASE_URL}/competitions/PL/standings/?season={season}"
    if matchday:
        url += f"&matchday={matchday}"

    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        return HTTPException(status_code=response.status_code, detail=response.text)

    data = response.json()["standings"]

    # Get the first standings table (usually "TOTAL")
    table = data[0]["table"]

    # Return simplified standings
    result = {
        "season": season,
        "matchday": matchday,
        "standings": [
            {
                "position": t["position"],
                "team": t["team"]["shortName"],
                "crest": t["team"]["crest"],
                "playedGames": t["playedGames"],
                "won": t["won"],
                "draw": t["draw"],
                "lost": t["lost"],
                "points": t["points"],
                "goalDifference": t["goalDifference"],
                "form": t["form"],
            }
            for t in table
        ],
    }
    
    # Cache the result
    db_manager.save_football_standings(db, season=str(season), data=result, matchday=matchday)
    print(f"Saved standings data to database for season {season}")
    
    return result


@router.get("/head2head")
def get_head2head(matchId: int, db: Session = Depends(get_db)):
    # Check for cached data first
    cached_head2head = db_manager.get_football_head2head(db, matchId)
    
    if cached_head2head and not cached_head2head.is_expired():
        print("Using cached head2head data from database")
        return cached_head2head.data
    
    # Get data from API
    print("Fetching fresh head2head data from football-data.org API...")
    headers = {"X-Auth-Token": API_FOOTBALL_KEY}

    url = f"{BASE_URL}/matches/{matchId}/head2head"

    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        return HTTPException(status_code=response.status_code, detail=response.text)

    data = response.json()
    
    # Cache the result
    db_manager.save_football_head2head(db, matchId, data, cache_duration_hours=24)
    print(f"Saved head2head data to database for match {matchId}")
    
    return data


@router.get("/health")
def health_check():
    """Health check for general football API"""
    return {"status": "ok", "api_version": "1.0.0"}

@router.get("/cache-status")
def get_cache_status(db: Session = Depends(get_db)):
    """Get cache status and statistics for football data"""
    from ..database import FootballFixtures, FootballTeams, FootballStandings, FootballHead2Head
    
    # Get cache statistics
    fixtures_count = db.query(FootballFixtures).filter(FootballFixtures.is_current == True).count()
    teams_count = db.query(FootballTeams).filter(FootballTeams.is_current == True).count()
    standings_count = db.query(FootballStandings).filter(FootballStandings.is_current == True).count()
    head2head_count = db.query(FootballHead2Head).count()
    expired_head2head_count = db.query(FootballHead2Head).filter(FootballHead2Head.expires_at < datetime.utcnow()).count()
    
    return {
        "football_cache": {
            "fixtures": {
                "cached_seasons": fixtures_count,
                "fresh_data_available": fixtures_count > 0
            },
            "teams": {
                "cached_seasons": teams_count,
                "fresh_data_available": teams_count > 0
            },
            "standings": {
                "cached_seasons": standings_count,
                "fresh_data_available": standings_count > 0
            },
            "head2head": {
                "total_entries": head2head_count,
                "expired_entries": expired_head2head_count,
                "active_entries": head2head_count - expired_head2head_count
            }
        },
        "cache_freshness": {
            "fixtures": "2 hours",
            "teams": "24 hours", 
            "standings": "4 hours",
            "head2head": "24 hours"
        },
        "timestamp": datetime.utcnow().isoformat()
    }
