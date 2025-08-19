import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from database.models import Match, Team
from config import settings


def get_team_match_history(db: Session, team_id: int, season: int, 
                          before_date: datetime) -> pd.DataFrame:
    """Get team's match history before a specific date (leakage-safe)"""
    matches = db.query(Match).filter(
        Match.season == season,
        Match.utc_date < before_date,
        (Match.home_team_id == team_id) | (Match.away_team_id == team_id)
    ).order_by(Match.utc_date).all()
    
    if not matches:
        return pd.DataFrame()
    
    history_data = []
    for match in matches:
        is_home = match.home_team_id == team_id
        team_score = match.home_score if is_home else match.away_score
        opponent_score = match.away_score if is_home else match.home_score
        opponent_id = match.away_team_id if is_home else match.home_team_id
        
        # Calculate points (with None check)
        if team_score is None or opponent_score is None:
            continue  # Skip matches with missing scores
        
        if team_score > opponent_score:
            points = 3
        elif team_score == opponent_score:
            points = 1
        else:
            points = 0
        
        history_data.append({
            'team_id': team_id,
            'opponent_id': opponent_id,
            'is_home': is_home,
            'kickoff': match.utc_date,
            'goals_for': team_score,
            'goals_against': opponent_score,
            'points': points
        })
    
    return pd.DataFrame(history_data)


def compute_rolling_features(df: pd.DataFrame, window: int = 5) -> pd.DataFrame:
    """Compute rolling features with leakage prevention (shift(1))"""
    if df.empty:
        return df
    
    # Sort by kickoff time
    df = df.sort_values('kickoff').reset_index(drop=True)
    
    # Compute rolling features with shift(1) to prevent leakage
    df['points_rolling'] = df['points'].shift(1).rolling(window, min_periods=1).mean()
    df['goals_for_rolling'] = df['goals_for'].shift(1).rolling(window, min_periods=1).mean()
    df['goals_against_rolling'] = df['goals_against'].shift(1).rolling(window, min_periods=1).mean()
    df['goal_diff_rolling'] = (df['goals_for'] - df['goals_against']).shift(1).rolling(window, min_periods=1).mean()
    
    # Compute rest days
    df['rest_days'] = df['kickoff'].diff().dt.total_seconds() / 86400
    
    return df


def get_team_form_features(db: Session, team_id: int, season: int, 
                          match_date: datetime, window: int = 5) -> Dict[str, float]:
    """Get team's form features for a specific match (leakage-safe)"""
    # Get team's match history before the match date
    history_df = get_team_match_history(db, team_id, season, match_date)
    
    if history_df.empty:
        # Return default values for new teams
        return {
            'form_ppg': 1.0,  # Default to 1 point per game
            'goals_for_per_match': 1.0,
            'goals_against_per_match': 1.0,
            'goal_diff_per_match': 0.0,
            'rest_days': 7.0,  # Default to 7 days
            'data_quality': {'matches_available': 0}
        }
    
    # Compute rolling features
    rolling_df = compute_rolling_features(history_df, window)
    
    # Get the most recent values
    latest = rolling_df.iloc[-1] if not rolling_df.empty else None
    
    if latest is None or pd.isna(latest['points_rolling']):
        return {
            'form_ppg': 1.0,
            'goals_for_per_match': 1.0,
            'goals_against_per_match': 1.0,
            'goal_diff_per_match': 0.0,
            'rest_days': 7.0,
            'data_quality': {'matches_available': len(history_df)}
        }
    
    return {
        'form_ppg': float(latest['points_rolling']),
        'goals_for_per_match': float(latest['goals_for_rolling']),
        'goals_against_per_match': float(latest['goals_against_rolling']),
        'goal_diff_per_match': float(latest['goal_diff_rolling']),
        'rest_days': float(latest['rest_days']) if not pd.isna(latest['rest_days']) else 7.0,
        'data_quality': {'matches_available': len(history_df)}
    }


def get_match_form_features(db: Session, match: Match, window: int = 5) -> Dict[str, float]:
    """Get form features for both teams in a match"""
    home_form = get_team_form_features(db, match.home_team_id, match.season, match.utc_date, window)
    away_form = get_team_form_features(db, match.away_team_id, match.season, match.utc_date, window)
    
    # Compute differences
    form_features = {
        # Home team features
        'home_form_ppg': home_form['form_ppg'],
        'home_goals_for_per_match': home_form['goals_for_per_match'],
        'home_goals_against_per_match': home_form['goals_against_per_match'],
        'home_goal_diff_per_match': home_form['goal_diff_per_match'],
        'home_rest_days': home_form['rest_days'],
        
        # Away team features
        'away_form_ppg': away_form['form_ppg'],
        'away_goals_for_per_match': away_form['goals_for_per_match'],
        'away_goals_against_per_match': away_form['goals_against_per_match'],
        'away_goal_diff_per_match': away_form['goal_diff_per_match'],
        'away_rest_days': away_form['rest_days'],
        
        # Difference features
        'diff_form_ppg': home_form['form_ppg'] - away_form['form_ppg'],
        'diff_goals_for_per_match': home_form['goals_for_per_match'] - away_form['goals_for_per_match'],
        'diff_goals_against_per_match': home_form['goals_against_per_match'] - away_form['goals_against_per_match'],
        'diff_goal_diff_per_match': home_form['goal_diff_per_match'] - away_form['goal_diff_per_match'],
        'diff_rest_days': home_form['rest_days'] - away_form['rest_days'],
        
        # Context features
        'home_flag': 1.0,
        'same_city': 1.0 if match.city and match.city in ['London', 'Manchester', 'Liverpool'] else 0.0,
        
        # Data quality
        'data_quality': {
            'home_matches': home_form['data_quality']['matches_available'],
            'away_matches': away_form['data_quality']['matches_available']
        }
    }
    
    return form_features
