from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from database.models import Match, StandingsSnapshot
from datetime import datetime
import pandas as pd
import numpy as np


def get_extended_h2h_features(db: Session, home_team_id: int, away_team_id: int, 
                             match_date: datetime, limit: int = 10) -> Dict[str, float]:
    """Get comprehensive head-to-head features with more historical data"""
    
    # Get more historical head-to-head matches
    matches = db.query(Match).filter(
        Match.utc_date < match_date,
        Match.status == "FINISHED",
        Match.home_score.isnot(None),
        Match.away_score.isnot(None),
        ((Match.home_team_id == home_team_id) & (Match.away_team_id == away_team_id)) |
        ((Match.home_team_id == away_team_id) & (Match.away_team_id == home_team_id))
    ).order_by(Match.utc_date.desc()).limit(limit).all()
    
    if not matches:
        return get_default_h2h_features()
    
    # Analyze each match from home team's perspective
    h2h_data = []
    for match in matches:
        is_home_team_home = match.home_team_id == home_team_id
        
        if is_home_team_home:
            home_score = match.home_score
            away_score = match.away_score
            venue = "home"
        else:
            home_score = match.away_score
            away_score = match.home_score
            venue = "away"
        
        # Determine result (with None check)
        if home_score is None or away_score is None:
            continue  # Skip matches with missing scores
        
        if home_score > away_score:
            result = "win"
        elif home_score == away_score:
            result = "draw"
        else:
            result = "loss"
        
        h2h_data.append({
            'date': match.utc_date,
            'home_score': home_score,
            'away_score': away_score,
            'result': result,
            'venue': venue,
            'goal_diff': home_score - away_score,
            'total_goals': home_score + away_score,
            'season': match.season
        })
    
    return compute_extended_h2h_features(h2h_data)


def compute_extended_h2h_features(h2h_data: List[Dict]) -> Dict[str, float]:
    """Compute comprehensive head-to-head features"""
    
    if not h2h_data:
        return get_default_h2h_features()
    
    # Basic counts
    total_matches = len(h2h_data)
    wins = sum(1 for match in h2h_data if match['result'] == 'win')
    draws = sum(1 for match in h2h_data if match['result'] == 'draw')
    losses = sum(1 for match in h2h_data if match['result'] == 'loss')
    
    # Goal statistics
    total_goals = sum(match['total_goals'] for match in h2h_data)
    goal_diff = sum(match['goal_diff'] for match in h2h_data)
    avg_goals = total_goals / total_matches
    
    # Venue-specific analysis
    home_venue_matches = [m for m in h2h_data if m['venue'] == 'home']
    away_venue_matches = [m for m in h2h_data if m['venue'] == 'away']
    
    home_venue_wins = sum(1 for match in home_venue_matches if match['result'] == 'win')
    away_venue_wins = sum(1 for match in away_venue_matches if match['result'] == 'win')
    
    # Recent form (last 3 matches)
    recent_matches = h2h_data[:3]
    recent_wins = sum(1 for match in recent_matches if match['result'] == 'win')
    recent_goal_diff = sum(match['goal_diff'] for match in recent_matches)
    
    # Season-specific analysis
    current_season_matches = [m for m in h2h_data if m['season'] == h2h_data[0]['season']]
    current_season_wins = sum(1 for match in current_season_matches if match['result'] == 'win')
    
    return {
        # Primary H2H features (highest priority)
        'h2h_total_matches': float(total_matches),
        'h2h_wins': float(wins),
        'h2h_draws': float(draws),
        'h2h_losses': float(losses),
        'h2h_win_rate': float(wins) / total_matches,
        'h2h_draw_rate': float(draws) / total_matches,
        'h2h_loss_rate': float(losses) / total_matches,
        
        # Goal-based features
        'h2h_goal_diff': float(goal_diff),
        'h2h_avg_goals': float(avg_goals),
        'h2h_avg_goal_diff': float(goal_diff) / total_matches,
        
        # Venue-specific features
        'h2h_home_venue_matches': float(len(home_venue_matches)),
        'h2h_home_venue_wins': float(home_venue_wins),
        'h2h_home_venue_win_rate': float(home_venue_wins) / max(len(home_venue_matches), 1),
        'h2h_away_venue_matches': float(len(away_venue_matches)),
        'h2h_away_venue_wins': float(away_venue_wins),
        'h2h_away_venue_win_rate': float(away_venue_wins) / max(len(away_venue_matches), 1),
        
        # Recent form features
        'h2h_recent_wins': float(recent_wins),
        'h2h_recent_goal_diff': float(recent_goal_diff),
        'h2h_recent_win_rate': float(recent_wins) / len(recent_matches),
        
        # Season-specific features
        'h2h_current_season_matches': float(len(current_season_matches)),
        'h2h_current_season_wins': float(current_season_wins),
        'h2h_current_season_win_rate': float(current_season_wins) / max(len(current_season_matches), 1),
        
        # Dominance indicators
        'h2h_dominance': float(wins - losses) / total_matches,  # -1 to 1 scale
        'h2h_goal_dominance': float(goal_diff) / max(total_goals, 1),  # Goal efficiency
    }


def get_default_h2h_features() -> Dict[str, float]:
    """Return default values when no H2H data is available"""
    return {
        'h2h_total_matches': 0.0,
        'h2h_wins': 0.0,
        'h2h_draws': 0.0,
        'h2h_losses': 0.0,
        'h2h_win_rate': 0.5,  # Neutral
        'h2h_draw_rate': 0.0,
        'h2h_loss_rate': 0.5,  # Neutral
        'h2h_goal_diff': 0.0,
        'h2h_avg_goals': 2.5,  # League average
        'h2h_avg_goal_diff': 0.0,
        'h2h_home_venue_matches': 0.0,
        'h2h_home_venue_wins': 0.0,
        'h2h_home_venue_win_rate': 0.5,
        'h2h_away_venue_matches': 0.0,
        'h2h_away_venue_wins': 0.0,
        'h2h_away_venue_win_rate': 0.5,
        'h2h_recent_wins': 0.0,
        'h2h_recent_goal_diff': 0.0,
        'h2h_recent_win_rate': 0.5,
        'h2h_current_season_matches': 0.0,
        'h2h_current_season_wins': 0.0,
        'h2h_current_season_win_rate': 0.5,
        'h2h_dominance': 0.0,
        'h2h_goal_dominance': 0.0,
    }


def get_previous_season_standings(db: Session, home_team_id: int, away_team_id: int, 
                                 current_season: int) -> Dict[str, float]:
    """Get previous season standings for both teams"""
    
    prev_season = current_season - 1
    
    # Get final standings from previous season
    home_prev_standings = db.query(StandingsSnapshot).filter(
        StandingsSnapshot.season == prev_season,
        StandingsSnapshot.team_id == home_team_id,
        StandingsSnapshot.matchday == 38  # Final matchday
    ).first()
    
    away_prev_standings = db.query(StandingsSnapshot).filter(
        StandingsSnapshot.season == prev_season,
        StandingsSnapshot.team_id == away_team_id,
        StandingsSnapshot.matchday == 38  # Final matchday
    ).first()
    
    # If no previous season data, try to get any available standings for these teams
    if not home_prev_standings:
        home_prev_standings = db.query(StandingsSnapshot).filter(
            StandingsSnapshot.team_id == home_team_id
        ).order_by(StandingsSnapshot.season.desc()).first()
    
    if not away_prev_standings:
        away_prev_standings = db.query(StandingsSnapshot).filter(
            StandingsSnapshot.team_id == away_team_id
        ).order_by(StandingsSnapshot.season.desc()).first()
    
    # Default values if no previous season data
    home_default = {
        'position': 10, 'points': 50, 'goal_diff': 0, 'played_games': 38
    }
    away_default = {
        'position': 10, 'points': 50, 'goal_diff': 0, 'played_games': 38
    }
    
    home_data = {
        'position': home_prev_standings.position if home_prev_standings else home_default['position'],
        'points': home_prev_standings.points if home_prev_standings else home_default['points'],
        'goal_diff': home_prev_standings.goal_diff if home_prev_standings else home_default['goal_diff'],
        'played_games': home_prev_standings.played_games if home_prev_standings else home_default['played_games']
    }
    
    away_data = {
        'position': away_prev_standings.position if away_prev_standings else away_default['position'],
        'points': away_prev_standings.points if away_prev_standings else away_default['points'],
        'goal_diff': away_prev_standings.goal_diff if away_prev_standings else away_default['goal_diff'],
        'played_games': away_prev_standings.played_games if away_prev_standings else away_default['played_games']
    }
    
    # Calculate derived features
    return {
        # Previous season standings (second priority)
        'prev_season_home_position': float(home_data['position']),
        'prev_season_away_position': float(away_data['position']),
        'prev_season_home_points': float(home_data['points']),
        'prev_season_away_points': float(away_data['points']),
        'prev_season_home_goal_diff': float(home_data['goal_diff']),
        'prev_season_away_goal_diff': float(away_data['goal_diff']),
        
        # Difference features
        'prev_season_diff_position': float(home_data['position'] - away_data['position']),
        'prev_season_diff_points': float(home_data['points'] - away_data['points']),
        'prev_season_diff_goal_diff': float(home_data['goal_diff'] - away_data['goal_diff']),
        
        # Normalized features
        'prev_season_home_points_per_game': float(home_data['points']) / home_data['played_games'],
        'prev_season_away_points_per_game': float(away_data['points']) / away_data['played_games'],
        'prev_season_diff_points_per_game': float(home_data['points'] - away_data['points']) / 38,
        
        # Quality indicators
        'prev_season_home_quality': 1.0 / home_data['position'],  # Higher position = lower quality
        'prev_season_away_quality': 1.0 / away_data['position'],
        'prev_season_diff_quality': (1.0 / home_data['position']) - (1.0 / away_data['position']),
    }


def get_prioritized_match_features(db: Session, match: Match) -> Dict[str, float]:
    """Get features prioritized by importance: H2H > Previous Season > Current Form"""
    
    # 1. HEAD-TO-HEAD FEATURES (Highest Priority)
    h2h_features = get_extended_h2h_features(db, match.home_team_id, match.away_team_id, match.utc_date)
    
    # 2. PREVIOUS SEASON STANDINGS (Second Priority)
    prev_season_features = get_previous_season_standings(db, match.home_team_id, match.away_team_id, match.season)
    
    # 3. CURRENT FORM FEATURES (Third Priority) - Import from existing module
    from ml.features.rolling import get_match_form_features
    from ml.features.standings import get_match_standings_features
    
    current_form_features = get_match_form_features(db, match)
    current_standings_features = get_match_standings_features(db, match)
    
    # Combine all features with priority ordering
    all_features = {
        # Head-to-Head (Priority 1)
        **h2h_features,
        
        # Previous Season (Priority 2)
        **prev_season_features,
        
        # Current Form (Priority 3)
        **current_form_features,
        **current_standings_features,
        
        # Context features
        'home_flag': 1.0,
        'same_city': 1.0 if match.city and match.city in ['London', 'Manchester', 'Liverpool'] else 0.0,
    }
    
    return all_features


def get_prioritized_feature_columns() -> List[str]:
    """Get feature columns in priority order"""
    return [
        # 1. HEAD-TO-HEAD FEATURES (Highest Priority)
        'h2h_total_matches', 'h2h_wins', 'h2h_draws', 'h2h_losses', 'h2h_win_rate',
        'h2h_draw_rate', 'h2h_loss_rate', 'h2h_goal_diff', 'h2h_avg_goals',
        'h2h_avg_goal_diff', 'h2h_home_venue_matches', 'h2h_home_venue_wins',
        'h2h_home_venue_win_rate', 'h2h_away_venue_matches', 'h2h_away_venue_wins',
        'h2h_away_venue_win_rate', 'h2h_recent_wins', 'h2h_recent_goal_diff',
        'h2h_recent_win_rate', 'h2h_current_season_matches', 'h2h_current_season_wins',
        'h2h_current_season_win_rate', 'h2h_dominance', 'h2h_goal_dominance',
        
        # 2. PREVIOUS SEASON FEATURES (Second Priority)
        'prev_season_home_position', 'prev_season_away_position', 'prev_season_home_points',
        'prev_season_away_points', 'prev_season_home_goal_diff', 'prev_season_away_goal_diff',
        'prev_season_diff_position', 'prev_season_diff_points', 'prev_season_diff_goal_diff',
        'prev_season_home_points_per_game', 'prev_season_away_points_per_game',
        'prev_season_diff_points_per_game', 'prev_season_home_quality', 'prev_season_away_quality',
        'prev_season_diff_quality',
        
        # 3. CURRENT FORM FEATURES (Third Priority)
        'diff_form_ppg', 'diff_goals_for_per_match', 'diff_goals_against_per_match',
        'diff_goal_diff_per_match', 'diff_rest_days', 'diff_position', 'diff_points',
        'diff_goal_diff', 'diff_rank_delta', 'diff_table_strength',
        
        # 4. CONTEXT FEATURES
        'home_flag', 'same_city'
    ]
