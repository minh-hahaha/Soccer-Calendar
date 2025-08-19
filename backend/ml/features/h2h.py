"""Head-to-head feature helpers."""

from typing import Dict, List

from sqlalchemy.orm import Session

from database.models import Match, HeadToHeadCache
import json


def get_head_to_head_matches(db: Session, home_team_id: int, away_team_id: int, 
                            before_date, limit: int = 5) -> List[Dict]:
    """Get head-to-head matches before a specific date (leakage-safe)"""
    matches = db.query(Match).filter(
        Match.utc_date < before_date,
        ((Match.home_team_id == home_team_id) & (Match.away_team_id == away_team_id)) |
        ((Match.home_team_id == away_team_id) & (Match.away_team_id == home_team_id))
    ).order_by(Match.utc_date.desc()).limit(limit).all()
    
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
        
        # Determine result from home team's perspective
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
            'goal_diff': home_score - away_score
        })
    
    return h2h_data


def compute_h2h_features(h2h_matches: List[Dict]) -> Dict[str, float]:
    """Compute head-to-head features from match history"""
    if not h2h_matches:
        return {
            'h2h_wins': 0.0,
            'h2h_draws': 0.0,
            'h2h_losses': 0.0,
            'h2h_goal_diff': 0.0,
            'h2h_avg_goals': 0.0,
            'h2h_home_venue_wins': 0.0,
            'h2h_home_venue_matches': 0.0,
            'h2h_matches_count': 0.0
        }
    
    wins = sum(1 for match in h2h_matches if match['result'] == 'win')
    draws = sum(1 for match in h2h_matches if match['result'] == 'draw')
    losses = sum(1 for match in h2h_matches if match['result'] == 'loss')
    
    total_goals = sum(match['home_score'] + match['away_score'] for match in h2h_matches)
    goal_diff = sum(match['goal_diff'] for match in h2h_matches)
    
    home_venue_matches = [m for m in h2h_matches if m['venue'] == 'home']
    home_venue_wins = sum(1 for match in home_venue_matches if match['result'] == 'win')
    
    return {
        'h2h_wins': float(wins),
        'h2h_draws': float(draws),
        'h2h_losses': float(losses),
        'h2h_goal_diff': float(goal_diff),
        'h2h_avg_goals': float(total_goals) / len(h2h_matches),
        'h2h_home_venue_wins': float(home_venue_wins),
        'h2h_home_venue_matches': float(len(home_venue_matches)),
        'h2h_matches_count': float(len(h2h_matches))
    }


def get_h2h_features(db: Session, home_team_id: int, away_team_id: int, 
                    match_date, limit: int = 5) -> Dict[str, float]:
    """Get head-to-head features for a match (leakage-safe)"""
    # Check cache first
    cache_entry = db.query(HeadToHeadCache).filter(
        HeadToHeadCache.home_team_id == home_team_id,
        HeadToHeadCache.away_team_id == away_team_id,
        HeadToHeadCache.season == match_date.year
    ).first()
    
    if cache_entry:
        try:
            cached_data = json.loads(cache_entry.payload)
            if cached_data.get('match_date') < match_date.isoformat():
                # Cache is valid
                return cached_data['features']
        except:
            pass  # Invalid cache, recompute
    
    # Get head-to-head matches
    h2h_matches = get_head_to_head_matches(db, home_team_id, away_team_id, match_date, limit)
    
    # Compute features
    features = compute_h2h_features(h2h_matches)
    
    # Cache the result
    cache_data = {
        'match_date': match_date.isoformat(),
        'features': features
    }
    
    if cache_entry:
        cache_entry.payload = json.dumps(cache_data)
    else:
        cache_entry = HeadToHeadCache(
            home_team_id=home_team_id,
            away_team_id=away_team_id,
            season=match_date.year,
            payload=json.dumps(cache_data)
        )
        db.add(cache_entry)
    
    db.commit()
    
    return features


def get_match_h2h_features(db: Session, match: Match) -> Dict[str, float]:
    """Get head-to-head features for both teams in a match"""
    h2h_features = get_h2h_features(db, match.home_team_id, match.away_team_id, match.utc_date)
    
    # Convert to match-specific features
    match_h2h_features = {
        'h2h_wins': h2h_features['h2h_wins'],
        'h2h_draws': h2h_features['h2h_draws'],
        'h2h_losses': h2h_features['h2h_losses'],
        'h2h_goal_diff': h2h_features['h2h_goal_diff'],
        'h2h_avg_goals': h2h_features['h2h_avg_goals'],
        'h2h_home_venue_wins': h2h_features['h2h_home_venue_wins'],
        'h2h_home_venue_matches': h2h_features['h2h_home_venue_matches'],
        'h2h_matches_count': h2h_features['h2h_matches_count'],
        
        # Derived features
        'h2h_win_rate': h2h_features['h2h_wins'] / max(h2h_features['h2h_matches_count'], 1),
        'h2h_home_venue_win_rate': h2h_features['h2h_home_venue_wins'] / max(h2h_features['h2h_home_venue_matches'], 1)
    }
    
    return match_h2h_features
