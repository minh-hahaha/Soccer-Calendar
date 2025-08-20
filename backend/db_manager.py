#!/usr/bin/env python3
"""
Database management script for Fantasy Football application
"""

import os
import sys
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from database import db_manager, SessionLocal
from api.ai_agent import FantasyFootballAgent

def setup_database():
    """Create database tables"""
    print("Creating database tables...")
    db_manager.create_tables()
    print("Database tables created successfully!")

def load_initial_data():
    """Load initial FPL data into database"""
    print("Loading initial FPL data...")
    
    db = SessionLocal()
    try:
        agent = FantasyFootballAgent()
        if agent.initialize_data(db):
            print("Initial data loaded successfully!")
            print(f"Current gameweek: {agent.current_gameweek}")
        else:
            print("Failed to load initial data")
    finally:
        db.close()

def load_initial_football_data():
    """Load initial football data into database"""
    print("Loading initial football data...")
    
    import requests
    import os
    
    API_FOOTBALL_KEY = os.getenv("FD_API_KEY")
    BASE_URL = "https://api.football-data.org/v4"
    
    if not API_FOOTBALL_KEY:
        print("Error: FD_API_KEY not found in environment variables")
        return
    
    db = SessionLocal()
    try:
        headers = {"X-Auth-Token": API_FOOTBALL_KEY}
        
        # Load teams data
        print("Loading teams data...")
        teams_url = f"{BASE_URL}/competitions/PL/teams?season=2025"
        teams_response = requests.get(teams_url, headers=headers)
        if teams_response.status_code == 200:
            teams_data = teams_response.json()["teams"]
            result = {
                "teams": [
                    {
                        "id": team["id"],
                        "name": team["name"],
                        "shortName": team["shortName"],
                        "crest": team["crest"],
                        "tla": team["tla"],
                    }
                    for team in teams_data
                ]
            }
            db_manager.save_football_teams(db, "2025", result)
            print(f"Loaded {len(teams_data)} teams")
        else:
            print(f"Failed to load teams: {teams_response.status_code}")
        
        # Load standings data
        print("Loading standings data...")
        standings_url = f"{BASE_URL}/competitions/PL/standings/?season=2025"
        standings_response = requests.get(standings_url, headers=headers)
        if standings_response.status_code == 200:
            standings_data = standings_response.json()["standings"]
            table = standings_data[0]["table"]
            result = {
                "season": 2025,
                "matchday": None,
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
            db_manager.save_football_standings(db, "2025", result)
            print(f"Loaded standings for {len(table)} teams")
        else:
            print(f"Failed to load standings: {standings_response.status_code}")
        
        # Load fixtures data
        print("Loading fixtures data...")
        fixtures_url = f"{BASE_URL}/competitions/PL/matches?season=2025"
        fixtures_response = requests.get(fixtures_url, headers=headers)
        if fixtures_response.status_code == 200:
            fixtures_data = fixtures_response.json()["matches"]
            
            # Process and cache fixtures
            processed_fixtures = []
            for match in fixtures_data:
                home_score = match.get("score", {}).get("fullTime", {}).get("home")
                away_score = match.get("score", {}).get("fullTime", {}).get("away")
                
                if (match["status"] == "FINISHED" and home_score is not None and away_score is not None):
                    display_time = f"{home_score} - {away_score}"
                else:
                    try:
                        match_date = datetime.fromisoformat(match["utcDate"].replace("Z", "+00:00"))
                        display_time = match_date.strftime("%H:%M")
                    except:
                        display_time = match["utcDate"]
                
                processed_fixtures.append({
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
                })
            
            result = {"fixtures": processed_fixtures}
            db_manager.save_football_fixtures(db, "2025", result)
            print(f"Loaded {len(processed_fixtures)} fixtures")
        else:
            print(f"Failed to load fixtures: {fixtures_response.status_code}")
        
        print("Initial football data loaded successfully!")
        
    except Exception as e:
        print(f"Error loading football data: {e}")
    finally:
        db.close()

def cleanup_expired_cache():
    """Remove expired cache entries"""
    print("Cleaning up expired cache entries...")
    
    db = SessionLocal()
    try:
        db_manager.cleanup_expired_cache(db)
        db_manager.cleanup_expired_football_cache(db)
        print("Expired cache entries removed!")
    finally:
        db.close()

def show_cache_status():
    """Show current cache status"""
    print("Cache Status:")
    
    db = SessionLocal()
    try:
        from database import (
            AnalysisCache, BootstrapData, FixturesData,
            FootballFixtures, FootballTeams, FootballStandings, FootballHead2Head
        )
        
        # Fantasy Football data
        print("\n=== Fantasy Football Cache ===")
        bootstrap = db_manager.get_current_bootstrap_data(db)
        if bootstrap:
            print(f"Bootstrap data: Gameweek {bootstrap.gameweek}, Updated: {bootstrap.updated_at}")
            print(f"  Fresh: {bootstrap.is_fresh()}")
        else:
            print("Bootstrap data: Not available")
        
        fixtures = db_manager.get_current_fixtures_data(db)
        if fixtures:
            print(f"Fixtures data: Gameweek {fixtures.gameweek}, Updated: {fixtures.updated_at}")
            print(f"  Fresh: {fixtures.is_fresh()}")
        else:
            print("Fixtures data: Not available")
        
        cache_count = db.query(AnalysisCache).count()
        expired_count = db.query(AnalysisCache).filter(AnalysisCache.expires_at < datetime.utcnow()).count()
        print(f"Analysis cache: {cache_count} entries ({expired_count} expired)")
        
        # Football data
        print("\n=== Football Data Cache ===")
        fixtures_count = db.query(FootballFixtures).filter(FootballFixtures.is_current == True).count()
        teams_count = db.query(FootballTeams).filter(FootballTeams.is_current == True).count()
        standings_count = db.query(FootballStandings).filter(FootballStandings.is_current == True).count()
        head2head_count = db.query(FootballHead2Head).count()
        expired_head2head_count = db.query(FootballHead2Head).filter(FootballHead2Head.expires_at < datetime.utcnow()).count()
        
        print(f"Football fixtures: {fixtures_count} cached seasons")
        print(f"Football teams: {teams_count} cached seasons")
        print(f"Football standings: {standings_count} cached seasons")
        print(f"Football head2head: {head2head_count} entries ({expired_head2head_count} expired)")
        
    finally:
        db.close()

def refresh_data():
    """Force refresh of FPL data"""
    print("Refreshing FPL data...")
    
    db = SessionLocal()
    try:
        # Mark current data as not current
        db.query(BootstrapData).filter(BootstrapData.is_current == True).update({"is_current": False})
        db.query(FixturesData).filter(FixturesData.is_current == True).update({"is_current": False})
        db.commit()
        
        # Load fresh data
        agent = FantasyFootballAgent()
        if agent.initialize_data(db):
            print("Data refreshed successfully!")
            print(f"Current gameweek: {agent.current_gameweek}")
        else:
            print("Failed to refresh data")
    finally:
        db.close()

def main():
    """Main function to handle command line arguments"""
    if len(sys.argv) < 2:
        print("Usage: python db_manager.py <command>")
        print("Commands:")
        print("  setup     - Create database tables")
        print("  load      - Load initial FPL data")
        print("  load-football - Load initial football data")
        print("  refresh   - Refresh FPL data")
        print("  cleanup   - Clean up expired cache")
        print("  status    - Show cache status")
        return
    
    command = sys.argv[1].lower()
    
    if command == "setup":
        setup_database()
    elif command == "load":
        load_initial_data()
    elif command == "load-football":
        load_initial_football_data()
    elif command == "refresh":
        refresh_data()
    elif command == "cleanup":
        cleanup_expired_cache()
    elif command == "status":
        show_cache_status()
    else:
        print(f"Unknown command: {command}")

if __name__ == "__main__":
    main()
