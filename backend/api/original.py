import os
from datetime import datetime
from typing import Optional

import requests
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

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
):
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
    
    return result


@router.get("/finished-matches")
def get_finished_matches(
    team: Optional[str] = Query(None),  # use shortName
    matchday: Optional[int] = Query(None),
    season: Optional[str] = Query(2025),
):
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
    
    return result


@router.get("/teams")
def get_teams(season: str = Query(2025)):
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
    
    return result


@router.get("/standings")
def get_standings(
    season: int = Query(2025),
    matchday: Optional[int] = Query(None),
):
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
    
    return result


@router.get("/head2head")
def get_head2head(matchId: int):
    # Get data from API
    print("Fetching fresh head2head data from football-data.org API...")
    headers = {"X-Auth-Token": API_FOOTBALL_KEY}

    url = f"{BASE_URL}/matches/{matchId}/head2head"

    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        return HTTPException(status_code=response.status_code, detail=response.text)

    data = response.json()
    
    return data


@router.get("/health")
def health_check():
    """Health check for general football API"""
    return {"status": "ok", "api_version": "1.0.0"}


