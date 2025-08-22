import os
from datetime import datetime

from typing import Optional

import requests
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from sqlalchemy import create_engine, text

# Load environment variables from .env file
load_dotenv()

router = APIRouter()

API_FOOTBALL_KEY = os.getenv("FD_API_KEY")
BASE_URL = "https://api.football-data.org/v4"
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL) # database

@router.get("/fixtures")
def get_fixtures(
    # Get data from database. Data already ingested
    # Query parameters
    team: Optional[str] = Query(None),  # use shortName
    matchday: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    season: Optional[str] = Query(2025),
):
    
    query = "SELECT * FROM matches WHERE 1=1"
    params = {}

    if team:
        query += " AND (LOWER(home_team) LIKE :team OR LOWER(away_team) LIKE :team)"
        params["team"] = f"%{team.lower()}%"
    
    if matchday: 
        query += " AND matchday = :matchday"
        params["matchday"] = matchday

    if status: 
        query += " AND status = :status"
        params["status"] = status

    if matchday: 
        query += " AND season = :season"
        params["season"] = season

    with engine.connect() as conn:
        result = conn.execute(text(query), params)
        fixtures = [dict(row) for row in result.mappings()]

    #print(fixtures)

    filtered_data = []

    # Create display time/score based on match status
    for fixture in fixtures:
        if (
            fixture["status"] == "FINISHED" and fixture["home_score"] is not None and fixture["away_score"] is not None
        ):
            display_time = f"{fixture["home_score"]} - {fixture["away_score"]}"
        else:
                # Format the UTC date to show time
            try:
                # fixture["date"] is a datetime object if loaded by SQLAlchemy, else string
                match_date = fixture["date"]
                if isinstance(match_date, str):
                    match_date = datetime.fromisoformat(match_date)
                display_time = match_date.strftime("%H:%M")
            except:
                display_time = str(fixture.get("date", ""))

        filtered_data.append(
            {
                "id": fixture["id"],
                "utcDate": fixture["date"],
                "displayTime": display_time,
                "homeTeam": fixture["home_team"],
                "awayTeam": fixture["away_team"],
                "matchday": fixture["matchday"],
                "status": fixture["status"],
                "homeTeamCrest": fixture["home_team_crest"],
                "awayTeamCrest": fixture["away_team_crest"],
                "homeScore": fixture["home_score"],
                "awayScore": fixture["away_score"],
            }
            )

    return {"fixtures": filtered_data}


# @router.get("/finished-matches")
# def get_finished_matches(
#     team: Optional[str] = Query(None),  # use shortName
#     matchday: Optional[int] = Query(None),
#     season: Optional[str] = Query(2025),
# ):
#     # Get data from API
#     print("Fetching fresh finished matches data from football-data.org API...")
#     headers = {"X-Auth-Token": API_FOOTBALL_KEY}

#     url = f"{BASE_URL}/competitions/PL/matches?season={season}&status=FINISHED"

#     response = requests.get(url, headers=headers)

#     if response.status_code != 200:
#         return HTTPException(status_code=response.status_code, detail=response.text)

#     data = response.json()["matches"]

#     # filter data based on query parameters
#     filtered_data = []
#     for match in data:
#         # matchday, team are inputs
#         if matchday and match["matchday"] != matchday:
#             continue  # go to the next match
#         if team and (
#             team.lower() not in match["homeTeam"]["shortName"].lower()
#             and team.lower() not in match["awayTeam"]["shortName"].lower()
#         ):
#             continue  # go to the next match

#         # Get score information for finished matches
#         home_score = match.get("score", {}).get("fullTime", {}).get("home")
#         away_score = match.get("score", {}).get("fullTime", {}).get("away")

#         filtered_data.append(
#             {
#                 "id": match["id"],
#                 "utcDate": match["utcDate"],
#                 "homeTeam": match["homeTeam"]["shortName"],
#                 "awayTeam": match["awayTeam"]["shortName"],
#                 "matchday": match["matchday"],
#                 "status": match["status"],
#                 "homeTeamCrest": match["homeTeam"]["crest"],
#                 "awayTeamCrest": match["awayTeam"]["crest"],
#                 "homeScore": home_score,
#                 "awayScore": away_score,
#             }
#         )

#     result = {"finished_matches": filtered_data}
    
#     return result


@router.get("/teams")
def get_teams(season: str = Query(2025)):
    query = "SELECT * FROM teams"

    with engine.connect() as conn:
        result = conn.execute(text(query))
        teams = [dict(row) for row in result.mappings()]


    # Return simplified teams data
    result = {
        "teams": [
            {
                "id": team["id"],
                "name": team["name"],
                "shortName": team["short_name"],
                "crest": team["crest"],
                "tla": team["tla"],
            }
            for team in teams
        ]
    }
    
    return result


@router.get("/standings")
def get_standings(
    season: int = Query(2025),
    matchday: Optional[int] = Query(None),
):
    query = "SELECT * FROM standings"

    with engine.connect() as conn:
        result = conn.execute(text(query))
        standings = [dict(row) for row in result.mappings()]



    # Return simplified standings
    result = {
        "season": season,
        "matchday": matchday,
        "standings": [
            {
                "position": standing["position"],
                "team": standing["team"],
                "crest": standing["crest"],
                "playedGames": standing["played_games"],
                "won": standing["won"],
                "draw": standing["draw"],
                "lost": standing["lost"],
                "points": standing["points"],
                "goalDifference": standing["goal_difference"],
                "form": standing["form"],
            }
            for standing in standings
        ],
    }
    
    return result


@router.get("/head2head") # need to fix
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


