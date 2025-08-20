#!/usr/bin/env python3
"""
Test script for database setup and caching functionality
"""

import os
import sys
from datetime import datetime

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from database import db_manager, SessionLocal
from api.ai_agent import FantasyFootballAgent

def test_database_connection():
    """Test database connection"""
    print("Testing database connection...")
    
    try:
        db = SessionLocal()
        db.execute("SELECT 1")
        print("✅ Database connection successful!")
        db.close()
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def test_data_loading():
    """Test data loading from FPL API"""
    print("\nTesting data loading from FPL API...")
    
    try:
        db = SessionLocal()
        agent = FantasyFootballAgent()
        
        if agent.initialize_data(db):
            print(f"✅ Data loaded successfully!")
            print(f"   Current gameweek: {agent.current_gameweek}")
            print(f"   Players loaded: {len(agent.bootstrap_data.get('elements', []))}")
            print(f"   Teams loaded: {len(agent.bootstrap_data.get('teams', []))}")
            print(f"   Fixtures loaded: {len(agent.fixtures_data)}")
        else:
            print("❌ Failed to load data")
            return False
        
        db.close()
        return True
    except Exception as e:
        print(f"❌ Data loading failed: {e}")
        return False

def test_caching():
    """Test caching functionality"""
    print("\nTesting caching functionality...")
    
    try:
        db = SessionLocal()
        
        # Test bootstrap data caching
        bootstrap = db_manager.get_current_bootstrap_data(db)
        if bootstrap:
            print(f"✅ Bootstrap data cached: Gameweek {bootstrap.gameweek}")
            print(f"   Fresh: {bootstrap.is_fresh()}")
        else:
            print("❌ No bootstrap data in cache")
        
        # Test fixtures data caching
        fixtures = db_manager.get_current_fixtures_data(db)
        if fixtures:
            print(f"✅ Fixtures data cached: Gameweek {fixtures.gameweek}")
            print(f"   Fresh: {fixtures.is_fresh()}")
        else:
            print("❌ No fixtures data in cache")
        
        db.close()
        return True
    except Exception as e:
        print(f"❌ Caching test failed: {e}")
        return False

def test_analysis_caching():
    """Test analysis result caching"""
    print("\nTesting analysis result caching...")
    
    try:
        db = SessionLocal()
        agent = FantasyFootballAgent()
        
        # Ensure data is loaded
        if not agent.bootstrap_data:
            agent.initialize_data(db)
        
        # Run analysis
        from api.ai_agent import FantasyAdviceType
        result = agent.analyze_fantasy_strategy(
            analysis_types=[FantasyAdviceType.TRANSFER, FantasyAdviceType.CAPTAIN],
            budget=100.0,
            gameweeks_ahead=3,
            db=db
        )
        
        print(f"✅ Analysis completed successfully!")
        print(f"   Gameweek: {result.get('gameweek')}")
        print(f"   Recommendations: {len(result.get('recommendations', {}))}")
        
        # Check if result was cached
        cache_key = {
            "analysis_types": ["transfers", "captain"],
            "budget": 100.0,
            "current_team": None,
            "gameweeks_ahead": 3
        }
        
        cached_result = db_manager.get_cached_analysis(
            db, "fantasy_strategy", result.get('gameweek'), cache_key
        )
        
        if cached_result:
            print("✅ Analysis result cached successfully!")
        else:
            print("❌ Analysis result not found in cache")
        
        db.close()
        return True
    except Exception as e:
        print(f"❌ Analysis caching test failed: {e}")
        return False

def test_football_data_caching():
    """Test football data caching"""
    print("\nTesting football data caching...")
    
    try:
        db = SessionLocal()
        
        # Test teams data caching
        teams = db_manager.get_football_teams(db, "2025")
        if teams:
            print(f"✅ Football teams data cached: Season {teams.season}")
            print(f"   Fresh: {teams.is_fresh()}")
        else:
            print("❌ No football teams data in cache")
        
        # Test standings data caching
        standings = db_manager.get_football_standings(db, "2025")
        if standings:
            print(f"✅ Football standings data cached: Season {standings.season}")
            print(f"   Fresh: {standings.is_fresh()}")
        else:
            print("❌ No football standings data in cache")
        
        # Test fixtures data caching
        fixtures = db_manager.get_football_fixtures(db, "2025")
        if fixtures:
            print(f"✅ Football fixtures data cached: Season {fixtures.season}")
            print(f"   Fresh: {fixtures.is_fresh()}")
        else:
            print("❌ No football fixtures data in cache")
        
        db.close()
        return True
    except Exception as e:
        print(f"❌ Football data caching test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing Fantasy Football Database Setup")
    print("=" * 50)
    
    tests = [
        test_database_connection,
        test_data_loading,
        test_caching,
        test_analysis_caching,
        test_football_data_caching
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
    
    print("\n" + "=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Database setup is working correctly.")
    else:
        print("⚠️  Some tests failed. Please check the setup.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
