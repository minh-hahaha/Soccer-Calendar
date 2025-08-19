#!/usr/bin/env python3
"""Debug script to find the None comparison error"""

from database.db import SessionLocal, get_db
from database.models import Match
from ml.features.build import get_features_for_match
import traceback

def debug_prediction(match_id: int):
    """Debug the prediction for a specific match"""
    # Try both session methods
    print("=== Testing with SessionLocal ===")
    db = SessionLocal()
    test_with_session(db, match_id)
    db.close()
    
    print("\n=== Testing with get_db dependency ===")
    db_gen = get_db()
    db = next(db_gen)
    test_with_session(db, match_id)
    db.close()

def test_with_session(db, match_id: int):
    
    try:
        print(f"Debugging match {match_id}...")
        
        # Get match
        match = db.query(Match).filter(Match.id == match_id).first()
        if not match:
            print(f"Match {match_id} not found")
            return
            
        print(f"Match found: {match.home_team_id} vs {match.away_team_id}, Season: {match.season}")
        
        # Try to get features using the EXACT same method as the API
        from ml.features.build import get_features_for_match
        features = get_features_for_match(db, match_id)
        print(f"Features calculated successfully: {len(features)} features")
        
        # Print some sample features to debug
        print("Sample features:")
        for i, (key, value) in enumerate(features.items()):
            if i < 5:  # Show first 5 features
                print(f"  {key}: {value}")
            if value is None:
                print(f"  WARNING: None value found in feature '{key}'")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        print("Full traceback:")
        traceback.print_exc()
    
    finally:
        db.close()

if __name__ == "__main__":
    debug_prediction(537845)
