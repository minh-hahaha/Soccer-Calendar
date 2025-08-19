from typing import Dict, Optional
from sqlalchemy.orm import Session
from database.models import Match, StandingsSnapshot, Team


def get_standings_at_matchday(db: Session, season: int, matchday: int, 
                            team_id: int) -> Optional[Dict[str, float]]:
    """Get team's standings as of a specific matchday (leakage-safe)"""
    # Get standings from previous matchday
    prev_matchday = max(1, matchday - 1)
    
    snapshot = db.query(StandingsSnapshot).filter(
        StandingsSnapshot.season == season,
        StandingsSnapshot.matchday == prev_matchday,
        StandingsSnapshot.team_id == team_id
    ).first()
    
    if snapshot:
        return {
            'position': float(snapshot.position),
            'played_games': float(snapshot.played_games),
            'points': float(snapshot.points),
            'goals_for': float(snapshot.goals_for),
            'goals_against': float(snapshot.goals_against),
            'goal_diff': float(snapshot.goal_diff),
            'cold_start': False
        }
    else:
        # Return default values for new teams or missing data
        return {
            'position': 10.0,  # Default to middle position
            'played_games': 0.0,
            'points': 0.0,
            'goals_for': 0.0,
            'goals_against': 0.0,
            'goal_diff': 0.0,
            'cold_start': True
        }


def get_rank_delta(db: Session, season: int, matchday: int, team_id: int, 
                  window: int = 5) -> float:
    """Get team's rank change over recent matchdays"""
    if matchday <= window:
        return 0.0  # Not enough history
    
    current_snapshot = db.query(StandingsSnapshot).filter(
        StandingsSnapshot.season == season,
        StandingsSnapshot.matchday == matchday - 1,
        StandingsSnapshot.team_id == team_id
    ).first()
    
    past_snapshot = db.query(StandingsSnapshot).filter(
        StandingsSnapshot.season == season,
        StandingsSnapshot.matchday == matchday - 1 - window,
        StandingsSnapshot.team_id == team_id
    ).first()
    
    if current_snapshot and past_snapshot:
        return float(past_snapshot.position - current_snapshot.position)  # Positive = improving
    else:
        return 0.0


def get_match_standings_features(db: Session, match: Match) -> Dict[str, float]:
    """Get standings features for both teams in a match"""
    home_standings = get_standings_at_matchday(db, match.season, match.matchday, match.home_team_id)
    away_standings = get_standings_at_matchday(db, match.season, match.matchday, match.away_team_id)
    
    home_rank_delta = get_rank_delta(db, match.season, match.matchday, match.home_team_id)
    away_rank_delta = get_rank_delta(db, match.season, match.matchday, match.away_team_id)
    
    standings_features = {
        # Home team standings
        'home_position': home_standings['position'],
        'home_points': home_standings['points'],
        'home_goal_diff': home_standings['goal_diff'],
        'home_rank_delta': home_rank_delta,
        'home_cold_start': home_standings['cold_start'],
        
        # Away team standings
        'away_position': away_standings['position'],
        'away_points': away_standings['points'],
        'away_goal_diff': away_standings['goal_diff'],
        'away_rank_delta': away_rank_delta,
        'away_cold_start': away_standings['cold_start'],
        
        # Difference features
        'diff_position': home_standings['position'] - away_standings['position'],
        'diff_points': home_standings['points'] - away_standings['points'],
        'diff_goal_diff': home_standings['goal_diff'] - away_standings['goal_diff'],
        'diff_rank_delta': home_rank_delta - away_rank_delta,
        
        # Table strength features
        'home_table_strength': 1.0 / home_standings['position'],  # Higher position = lower strength
        'away_table_strength': 1.0 / away_standings['position'],
        'diff_table_strength': (1.0 / home_standings['position']) - (1.0 / away_standings['position'])
    }
    
    return standings_features
