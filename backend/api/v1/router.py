"""V1 API Router - Football Data"""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from ...core.database import get_db
from ...models.database.football import Match, Team, Standing

router = APIRouter()


@router.get("/fixtures")
def get_fixtures(
    team: Optional[str] = Query(None),
    matchday: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    season: Optional[int] = Query(2025),
    db: Session = Depends(get_db)
):
    """Get match fixtures with filtering"""
    
    query = db.query(Match)
    
    if team:
        query = query.filter(
            (Match.home_team.ilike(f"%{team}%")) |
            (Match.away_team.ilike(f"%{team}%"))
        )
    
    if matchday:
        query = query.filter(Match.matchday == matchday)
    
    if status:
        query = query.filter(Match.status == status)
    
    if season:
        query = query.filter(Match.season == season)
    
    matches = query.all()
    
    # Format response
    fixtures = []
    for match in matches:
        if (
            match.status == "FINISHED" and match.home_score is not None and match.away_score is not None
        ):
            display_time = f'{match.home_score} - {match.away_score}'
        else:
                # Format the UTC date to show time
            try:
                # fixture["date"] is a datetime object if loaded by SQLAlchemy, else string
                match_date = match.date
                if isinstance(match_date, str):
                    match_date = datetime.fromisoformat(match_date)
                display_time = match_date.strftime("%H:%M")
            except:
                display_time = str(match.get("date", ""))

        fixtures.append({
            "id": match.id,
            "utcDate": match.date.isoformat() if match.date else None,
            "displayTime": display_time,
            "homeTeam": match.home_team,
            "awayTeam": match.away_team,
            "matchday": match.matchday,
            "status": match.status,
            "homeTeamCrest": match.home_team_crest,
            "awayTeamCrest": match.away_team_crest,
            "homeScore": match.home_score,
            "awayScore": match.away_score,
        })
    
    return {"fixtures": fixtures}


@router.get("/teams")
def get_teams(db: Session = Depends(get_db)):
    """Get all teams"""
    teams = db.query(Team).all()
    
    return {
        "teams": [
            {
                "id": team.id,
                "name": team.name,
                "shortName": team.short_name,
                "crest": team.crest,
                "tla": team.tla,
            }
            for team in teams
        ]
    }


@router.get("/standings")
def get_standings(
    season: str = Query("2025"),
    matchday: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    """Get league standings"""
    query = db.query(Standing).filter(Standing.season == season)
    
    if matchday:
        query = query.filter(Standing.matchday == matchday)
    
    standings = query.order_by(Standing.position).all()
    
    return {
        "season": season,
        "matchday": matchday,
        "standings": [
            {
                "position": standing.position,
                "team": standing.team,
                "crest": standing.crest,
                "playedGames": standing.played_games,
                "won": standing.won,
                "draw": standing.draw,
                "lost": standing.lost,
                "points": standing.points,
                "goalDifference": standing.goal_difference,
                "form": standing.form,
            }
            for standing in standings
        ],
    }