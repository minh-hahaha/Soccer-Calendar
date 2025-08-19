"""Utilities for building feature sets used by the machine learning pipeline.

Historically this module relied on a number of imports that were missing
from the file, leading to ``NameError`` or ``ImportError`` exceptions as
soon as it was imported.  The test-suite imports the
``get_features_for_match`` function from here, so it's important that the
module can be imported without issues.  The patch adds the required
typing, SQLAlchemy, and third‑party imports as well as a module level
``typer.Typer`` application instance.
"""

from typing import Any, Dict, List
import json
import typer
from sqlalchemy.orm import Session

from database.db import SessionLocal
from database.models import FeaturesMatch, Match
from ml.features.rolling import get_match_form_features
from ml.features.standings import get_match_standings_features
from ml.features.h2h import get_match_h2h_features
from config import settings

app = typer.Typer()


def build_match_features(db: Session, match: Match) -> Dict[str, Any]:
    """Build all features for a single match using prioritized approach"""
    from ml.features.prioritized_features import get_prioritized_match_features
    
    # Get prioritized features
    all_features = get_prioritized_match_features(db, match)
    
    # Add match metadata
    all_features['match_id'] = match.id
    all_features['season'] = match.season
    all_features['matchday'] = match.matchday
    all_features['home_team_id'] = match.home_team_id
    all_features['away_team_id'] = match.away_team_id
    
    return all_features


def save_features_to_db(db: Session, match_id: int, features: Dict[str, Any]):
    """Save features to database"""
    # Check if features already exist
    existing = db.query(FeaturesMatch).filter(FeaturesMatch.match_id == match_id).first()
    
    if existing:
        # Update existing features
        existing.feature_json = features
    else:
        # Create new features record
        features_record = FeaturesMatch(
            match_id=match_id,
            feature_json=features
        )
        db.add(features_record)
    
    db.commit()


@app.command()
def build_features(season: int = typer.Option(2024, help="Season to build features for")):
    """Build features for all matches in a season"""
    typer.echo(f"Building features for season {season}...")
    
    db = SessionLocal()
    
    try:
        # Get all matches for the season
        matches = db.query(Match).filter(Match.season == season).all()
        
        typer.echo(f"Found {len(matches)} matches")
        
        for i, match in enumerate(matches):
            try:
                features = build_match_features(db, match)
                save_features_to_db(db, match.id, features)
                
                if (i + 1) % 10 == 0:
                    typer.echo(f"Processed {i + 1}/{len(matches)} matches")
                    
            except Exception as e:
                typer.echo(f"Error building features for match {match.id}: {e}")
                continue
        
        typer.echo(f"Successfully built features for {len(matches)} matches")
        
    except Exception as e:
        typer.echo(f"Error building features: {e}")
        raise
    finally:
        db.close()


@app.command()
def build_single(match_id: int):
    """Build features for a single match"""
    typer.echo(f"Building features for match {match_id}...")
    
    db = SessionLocal()
    
    try:
        match = db.query(Match).filter(Match.id == match_id).first()
        if not match:
            typer.echo(f"Match {match_id} not found")
            return
        
        features = build_match_features(db, match)
        save_features_to_db(db, match.id, features)
        
        typer.echo(f"Successfully built features for match {match_id}")
        typer.echo(f"Features: {json.dumps(features, indent=2, default=str)}")
        
    except Exception as e:
        typer.echo(f"Error building features: {e}")
        raise
    finally:
        db.close()


def get_features_for_match(db: Session, match_id: int) -> Dict[str, Any]:
    """Get features for a match (from cache or build on demand)"""
    # Try to get from database first
    features_record = db.query(FeaturesMatch).filter(FeaturesMatch.match_id == match_id).first()
    
    if features_record:
        return features_record.feature_json
    
    # Build features if not found
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match:
        raise ValueError(f"Match {match_id} not found")
    
    features = build_match_features(db, match)
    save_features_to_db(db, match_id, features)
    
    return features


if __name__ == "__main__":
    app()
