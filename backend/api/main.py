from fastapi import APIRouter, Query, HTTPException
from typing import Optional
import requests, os
from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

#cache
from utils.redis_cache import get_cache, set_cache

# Load environment variables from .env file
load_dotenv()

router = APIRouter()

API_FOOTBALL_KEY = os.getenv("FD_API_KEY")
BASE_URL = "https://api.football-data.org/v4"

# ML model loading is handled by ml_api.py

# ============================================================================
# EXISTING ENDPOINTS (Unchanged)
# ============================================================================

@router.get("/fixtures")
def get_fixtures(
    #Query parameters for documentation and Type Checking
    team: Optional[str] = Query(None), # use shortName
    matchday: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    season: Optional[str] = Query(None),
):
    cache_key = f"fixtures"
    data = get_cache(cache_key)

    if not data:
        # if no data in cache, get data from api
        headers = {
            "X-Auth-Token": API_FOOTBALL_KEY
        }

        url = f"{BASE_URL}/competitions/PL/matches?season=2025"

        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            return HTTPException(status_code=response.status_code, detail=response.text)
        
        data = response.json()["matches"]
        set_cache(cache_key, data, ttl=3600)

    #filter data based on query parameters
    filtered_data = []
    for match in data:
        # matchday, status, team are inputs
        if matchday and match["matchday"] != matchday:
            continue    # go to the next match
        if status and match["status"] != status:
            continue    # go to the next match
        if team and (team.lower() not in match["homeTeam"]["shortName"].lower() and  
                    team.lower() not in match["awayTeam"]["shortName"].lower()):
            continue    # go to the next match
        
        # Get score information for finished matches
        home_score = match.get("score", {}).get("fullTime", {}).get("home")
        away_score = match.get("score", {}).get("fullTime", {}).get("away")
        
        # Create display time/score based on match status
        if match["status"] == "FINISHED" and home_score is not None and away_score is not None:
            display_time = f"{home_score} - {away_score}"
        else:
            # Format the UTC date to show time
            try:
                match_date = datetime.fromisoformat(match["utcDate"].replace('Z', '+00:00'))
                display_time = match_date.strftime("%H:%M")
            except:
                display_time = match["utcDate"]
        
        filtered_data.append({
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
            "awayScore": away_score
        })

    return {"fixtures": filtered_data}


@router.get("/finished-matches")
def get_finished_matches(
    team: Optional[str] = Query(None), # use shortName
    matchday: Optional[int] = Query(None),
    season: Optional[str] = Query(2025),
):
    """Get all finished matches with their scores"""
    cache_key = f"finished_matches_{season}"
    data = get_cache(cache_key)

    if not data:
        # if no data in cache, get data from api
        headers = {
            "X-Auth-Token": API_FOOTBALL_KEY
        }

        url = f"{BASE_URL}/competitions/PL/matches?season={season}&status=FINISHED"

        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            return HTTPException(status_code=response.status_code, detail=response.text)
        
        data = response.json()["matches"]
        set_cache(cache_key, data, ttl=3600)

    #filter data based on query parameters
    filtered_data = []
    for match in data:
        # matchday, team are inputs
        if matchday and match["matchday"] != matchday:
            continue    # go to the next match
        if team and (team.lower() not in match["homeTeam"]["shortName"].lower() and  
                    team.lower() not in match["awayTeam"]["shortName"].lower()):
            continue    # go to the next match
        
        # Get score information
        home_score = match.get("score", {}).get("fullTime", {}).get("home")
        away_score = match.get("score", {}).get("fullTime", {}).get("away")
        half_time_home = match.get("score", {}).get("halfTime", {}).get("home")
        half_time_away = match.get("score", {}).get("halfTime", {}).get("away")
        
        # Determine winner
        winner = None
        if home_score is not None and away_score is not None:
            if home_score > away_score:
                winner = "HOME"
            elif away_score > home_score:
                winner = "AWAY"
            else:
                winner = "DRAW"
        
        # Format the date
        try:
            match_date = datetime.fromisoformat(match["utcDate"].replace('Z', '+00:00'))
            formatted_date = match_date.strftime("%Y-%m-%d %H:%M")
        except:
            formatted_date = match["utcDate"]
        
        filtered_data.append({
            "id": match["id"],
            "utcDate": match["utcDate"],
            "formattedDate": formatted_date,
            "homeTeam": {
                "id": match["homeTeam"]["id"],
                "name": match["homeTeam"]["name"],
                "shortName": match["homeTeam"]["shortName"],
                "crest": match["homeTeam"]["crest"]
            },
            "awayTeam": {
                "id": match["awayTeam"]["id"],
                "name": match["awayTeam"]["name"],
                "shortName": match["awayTeam"]["shortName"],
                "crest": match["awayTeam"]["crest"]
            },
            "matchday": match["matchday"],
            "venue": match.get("venue"),
            "attendance": match.get("attendance"),
            "score": {
                "fullTime": {
                    "home": home_score,
                    "away": away_score
                },
                "halfTime": {
                    "home": half_time_home,
                    "away": half_time_away
                },
                "winner": winner
            },
            "goals": match.get("goals", []),
            "bookings": match.get("bookings", []),
            "substitutions": match.get("substitutions", [])
        })

    return {"finished_matches": filtered_data}

@router.get("/teams")
def get_teams():
    cache_key = f"teams"
    data = get_cache(cache_key)

    if not data:
        # if no data in cache, get data from api
        headers = {
            "X-Auth-Token": API_FOOTBALL_KEY
        }

        url = f"{BASE_URL}/competitions/PL/teams"

        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        
        data = response.json()["teams"]
        set_cache(cache_key, data, ttl=3600)

    #filter data based on query parameters
    filtered_data = []
    for team in data:
        filtered_data.append({
            "id": team["id"],
            "name": team["name"],
            "shortName": team["shortName"],
        })

    return {"teams": filtered_data}

@router.get("/standings")
@router.get("/standings/")
def get_standings(
    season:int = Query(2025),
    matchday:Optional[int] = Query(None),
):
    cache_key = f"standings_{season}_{matchday}"
    data = get_cache(cache_key)

    if not data:
        # if no data in cache, get data from api
        headers = {
            "X-Auth-Token": API_FOOTBALL_KEY
        }

        url = f"{BASE_URL}/competitions/PL/standings/?season={season}"
        if matchday:
            url += f"&matchday={matchday}"

        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            return HTTPException(status_code=response.status_code, detail=response.text)
        
        data = response.json()["standings"]
        set_cache(cache_key, data, ttl=3600)

    # Get the first standings table (usually "TOTAL")
    table = data[0]["table"]

    # Return simplified standings
    return {
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
                "form": t["form"]
            }
            for t in table
        ]
    }

@router.get("/head2head")
def get_head2head(matchId:int):
    cache_key = f"head2head_{matchId}"
    data = get_cache(cache_key)

    if not data:
        # if no data in cache, get data from api
        headers = {
            "X-Auth-Token": API_FOOTBALL_KEY
        }

        url = f"{BASE_URL}/matches/{matchId}/head2head"

        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            return HTTPException(status_code=response.status_code, detail=response.text)
        
        data = response.json()
        set_cache(cache_key, data, ttl=3600)

    return data



# ============================================================================
# Mock prediction endpoint for testing
# ============================================================================

@router.get("/predict")
def mock_predict(match_id: int):
    """Mock prediction endpoint for testing - DEPRECATED: Use /ml/predict for real predictions"""
    from fastapi import HTTPException
    
    raise HTTPException(
        status_code=410, 
        detail="Mock prediction endpoint is deprecated. Use /ml/predict for real ML predictions."
    )

# ============================================================================
# NOTE: ML predictions are handled by ml_api.py
# Use /ml/predict for real ML model predictions
# ============================================================================

@router.get("/health")
def health_check():
    """Health check for general football API"""
    return {
        "status": "ok",
        "api_version": "2.0.0",
        "note": "ML predictions available at /ml endpoints"
    }