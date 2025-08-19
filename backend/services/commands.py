import typer
from typing import Optional
from sqlalchemy.orm import Session
from backend.database.db import SessionLocal, engine
from backend.database.models import Base, Team, Match, StandingsSnapshot
from backend.services.client import FootballDataClient
from backend.services.mappers import map_team, map_match, map_standings_snapshot
from backend.config import settings

app = typer.Typer()


def get_db() -> Session:
    db = SessionLocal()
    try:
        return db
    except Exception:
        db.close()
        raise


@app.command()
def ingest_teams():
    """Ingest teams from football-data.org"""
    typer.echo("Ingesting teams...")
    
    client = FootballDataClient()
    db = get_db()
    
    try:
        # Get teams data
        teams_data = client.get_teams()
        
        # Map and save teams
        for team_data in teams_data["teams"]:
            team = map_team(team_data)
            
            # Check if team already exists
            existing_team = db.query(Team).filter(Team.id == team.id).first()
            if existing_team:
                # Update existing team
                existing_team.name = team.name
                existing_team.tla = team.tla
                existing_team.area_name = team.area_name
            else:
                # Add new team
                db.add(team)
        
        db.commit()
        typer.echo(f"Successfully ingested {len(teams_data['teams'])} teams")
        
    except Exception as e:
        db.rollback()
        typer.echo(f"Error ingesting teams: {e}")
        raise
    finally:
        db.close()


@app.command()
def ingest_matches(season: int = typer.Option(2024, help="Season to ingest")):
    """Ingest matches for a season"""
    typer.echo(f"Ingesting matches for season {season}...")
    
    client = FootballDataClient()
    db = get_db()
    
    try:
        # Get matches data
        matches_data = client.get_matches(season)
        
        # Track teams we need to create
        teams_to_create = {}
        
        # First pass: collect all team information from matches
        for match_data in matches_data["matches"]:
            # Extract home team info
            home_team = match_data["homeTeam"]
            home_team_id = home_team["id"]
            if home_team_id not in teams_to_create:
                teams_to_create[home_team_id] = {
                    "id": home_team_id,
                    "name": home_team["name"],
                    "tla": home_team.get("tla", ""),
                    "area_name": home_team.get("area", {}).get("name", "England")
                }
            
            # Extract away team info
            away_team = match_data["awayTeam"]
            away_team_id = away_team["id"]
            if away_team_id not in teams_to_create:
                teams_to_create[away_team_id] = {
                    "id": away_team_id,
                    "name": away_team["name"],
                    "tla": away_team.get("tla", ""),
                    "area_name": away_team.get("area", {}).get("name", "England")
                }
        
        # Create teams that don't exist
        for team_data in teams_to_create.values():
            existing_team = db.query(Team).filter(Team.id == team_data["id"]).first()
            if not existing_team:
                team = Team(
                    id=team_data["id"],
                    name=team_data["name"],
                    tla=team_data["tla"],
                    area_name=team_data["area_name"]
                )
                db.add(team)
                typer.echo(f"Creating team: {team_data['name']} (ID: {team_data['id']})")
        
        db.commit()
        typer.echo(f"Created {len(teams_to_create)} teams from match data")
        
        # Second pass: ingest matches
        matches_created = 0
        matches_updated = 0
        
        for match_data in matches_data["matches"]:
            match = map_match(match_data)
            
            # Check if match already exists
            existing_match = db.query(Match).filter(Match.id == match.id).first()
            if existing_match:
                # Update existing match
                existing_match.status = match.status
                existing_match.home_score = match.home_score
                existing_match.away_score = match.away_score
                matches_updated += 1
            else:
                # Add new match
                db.add(match)
                matches_created += 1
        
        db.commit()
        typer.echo(f"Successfully processed {len(matches_data['matches'])} matches")
        typer.echo(f"  - Created: {matches_created}")
        typer.echo(f"  - Updated: {matches_updated}")
        
    except Exception as e:
        db.rollback()
        typer.echo(f"Error ingesting matches: {e}")
        raise
    finally:
        db.close()


@app.command()
def ingest_standings(season: int = typer.Option(2024, help="Season to ingest")):
    """Ingest standings for a season"""
    typer.echo(f"Ingesting standings for season {season}...")
    
    client = FootballDataClient()
    db = get_db()
    
    try:
        # Get standings data
        standings_data = client.get_standings(season)
        
        # For now, we'll create a snapshot for matchday 1
        # In a real implementation, you'd want to get standings for each matchday
        snapshots = map_standings_snapshot(standings_data, season, 1)
        
        # Save snapshots
        for snapshot in snapshots:
            # Check if snapshot already exists
            existing = db.query(StandingsSnapshot).filter(
                StandingsSnapshot.season == season,
                StandingsSnapshot.matchday == 1,
                StandingsSnapshot.team_id == snapshot.team_id
            ).first()
            
            if existing:
                # Update existing snapshot
                existing.position = snapshot.position
                existing.played_games = snapshot.played_games
                existing.points = snapshot.points
                existing.goals_for = snapshot.goals_for
                existing.goals_against = snapshot.goals_against
                existing.goal_diff = snapshot.goal_diff
            else:
                # Add new snapshot
                db.add(snapshot)
        
        db.commit()
        typer.echo(f"Successfully ingested standings for {len(snapshots)} teams")
        
    except Exception as e:
        db.rollback()
        typer.echo(f"Error ingesting standings: {e}")
        raise
    finally:
        db.close()


@app.command()
def setup_db():
    """Create database tables"""
    typer.echo("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    typer.echo("Database tables created successfully")


if __name__ == "__main__":
    app()
