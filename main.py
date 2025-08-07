from fastapi import FastAPI, Query, HTTPException
from typing import Optional
import requests, os
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

#cache
from redis_cache import get_cache, set_cache

# Load environment variables from .env file
load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

API_FOOTBALL_KEY = os.getenv("API_FOOTBALL_KEY")
BASE_URL = "https://api.football-data.org/v4"


@app.get("/fixtures")
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
        
        filtered_data.append({
            "utcDate": match["utcDate"],
            "homeTeam": match["homeTeam"]["shortName"],
            "awayTeam": match["awayTeam"]["shortName"],
            "matchday": match["matchday"],
            "status": match["status"],
            "homeTeamCrest": match["homeTeam"]["crest"],
            "awayTeamCrest": match["awayTeam"]["crest"]
        })

    return {"fixtures": filtered_data}

@app.get("/teams")
def get_teams(
):
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
            return HTTPException(status_code=response.status_code, detail=response.text)
        
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

@app.get("/standings")
def get_standings(
    season:int = Query(2025),
    matchday:int = Query(None),
):
    cache_key = f"standings"
    data = get_cache(cache_key)

    if not data:
        # if no data in cache, get data from api
        headers = {
            "X-Auth-Token": API_FOOTBALL_KEY
        }
        params = {
        "season": season
        }
        if matchday:
            params["matchday"] = matchday

        url = f"{BASE_URL}/competitions/PL/standings"

        response = requests.get(url, headers=headers, params=params)

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

@app.get("/health")
def health_check():
    return {"status": "ok"}