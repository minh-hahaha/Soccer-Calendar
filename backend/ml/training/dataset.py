import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from sqlalchemy.orm import Session
from database.db import SessionLocal
from database.models import Match, FeaturesMatch
from ml.features.build import get_features_for_match
from config import settings
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')


def create_labels(match: Match) -> Tuple[int, List[int]]:
    """Create labels for a match (2=home win, 1=draw, 0=away win)"""
    if match.home_score is None or match.away_score is None:
        return None, None
    
    if match.home_score > match.away_score:
        label = 2  # Home win
        one_hot = [0, 0, 1]  # [away, draw, home]
    elif match.home_score == match.away_score:
        label = 1  # Draw
        one_hot = [0, 1, 0]  # [away, draw, home]
    else:
        label = 0  # Away win
        one_hot = [1, 0, 0]  # [away, draw, home]
    
    return label, one_hot


def prepare_training_data(seasons: List[int], valid_season: Optional[int] = None) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Prepare training and validation datasets"""
    db = SessionLocal()
    
    try:
        all_data = []
        
        for season in seasons:
            # Get all finished matches for the season
            matches = db.query(Match).filter(
                Match.season == season,
                Match.status == "FINISHED",
                Match.home_score.isnot(None),
                Match.away_score.isnot(None)
            ).order_by(Match.utc_date).all()
            
            for match in matches:
                try:
                    # Get features
                    features = get_features_for_match(db, match.id)
                    
                    # Create labels
                    label, one_hot = create_labels(match)
                    if label is None:
                        continue
                    
                    # Add to dataset
                    row = {
                        'match_id': match.id,
                        'season': match.season,
                        'utc_date': match.utc_date,
                        'label': label,
                        'one_hot_away': one_hot[0],
                        'one_hot_draw': one_hot[1],
                        'one_hot_home': one_hot[2],
                        **features
                    }
                    all_data.append(row)
                    
                except Exception as e:
                    print(f"Error processing match {match.id}: {e}")
                    continue
        
        # Convert to DataFrame
        df = pd.DataFrame(all_data)
        
        if df.empty:
            raise ValueError("No training data found")
        
        # Split into train and validation
        if valid_season:
            train_df = df[df['season'] != valid_season].copy()
            valid_df = df[df['season'] == valid_season].copy()
        else:
            # Use time-based split (80% train, 20% validation)
            df = df.sort_values('utc_date')
            split_idx = int(len(df) * 0.8)
            train_df = df.iloc[:split_idx].copy()
            valid_df = df.iloc[split_idx:].copy()
        
        print(f"Training set: {len(train_df)} matches")
        print(f"Validation set: {len(valid_df)} matches")
        
        return train_df, valid_df
        
    finally:
        db.close()


def get_feature_columns() -> List[str]:
    """Get the feature columns to use for training - now using prioritized features"""
    from ml.features.prioritized_features import get_prioritized_feature_columns
    return get_prioritized_feature_columns()


def prepare_features(df: pd.DataFrame, scaler: Optional[StandardScaler] = None) -> Tuple[np.ndarray, StandardScaler]:
    """Prepare features for training/prediction"""
    feature_cols = get_feature_columns()
    
    # Select features and handle missing values
    X = df[feature_cols].fillna(0.0).values
    
    # Scale features
    if scaler is None:
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
    else:
        X_scaled = scaler.transform(X)
    
    return X_scaled, scaler


def prepare_labels(df: pd.DataFrame, one_hot: bool = True) -> np.ndarray:
    """Prepare labels for training"""
    if one_hot:
        return df[['one_hot_away', 'one_hot_draw', 'one_hot_home']].values
    else:
        return df['label'].values


def get_feature_importance_names() -> List[str]:
    """Get feature names for importance analysis"""
    return get_feature_columns()


def create_sample_dataset() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Create a small sample dataset for testing"""
    # This creates synthetic data for demonstration
    np.random.seed(settings.random_seed)
    
    n_samples = 1000
    
    # Generate synthetic features
    data = {
        'match_id': range(1, n_samples + 1),
        'season': np.random.choice([2022, 2023, 2024], n_samples),
        'diff_form_ppg': np.random.normal(0, 1, n_samples),
        'diff_goals_for_per_match': np.random.normal(0, 0.5, n_samples),
        'diff_goals_against_per_match': np.random.normal(0, 0.5, n_samples),
        'diff_goal_diff_per_match': np.random.normal(0, 1, n_samples),
        'diff_rest_days': np.random.normal(0, 2, n_samples),
        'diff_position': np.random.normal(0, 5, n_samples),
        'diff_points': np.random.normal(0, 10, n_samples),
        'diff_goal_diff': np.random.normal(0, 15, n_samples),
        'diff_rank_delta': np.random.normal(0, 2, n_samples),
        'diff_table_strength': np.random.normal(0, 0.1, n_samples),
        'h2h_wins': np.random.poisson(1, n_samples),
        'h2h_draws': np.random.poisson(1, n_samples),
        'h2h_losses': np.random.poisson(1, n_samples),
        'h2h_goal_diff': np.random.normal(0, 2, n_samples),
        'h2h_avg_goals': np.random.normal(2.5, 0.5, n_samples),
        'h2h_win_rate': np.random.uniform(0, 1, n_samples),
        'h2h_home_venue_win_rate': np.random.uniform(0, 1, n_samples),
        'home_flag': 1,
        'same_city': np.random.choice([0, 1], n_samples, p=[0.8, 0.2])
    }
    
    df = pd.DataFrame(data)
    
    # Generate synthetic labels based on features
    home_advantage = 0.3
    form_effect = df['diff_form_ppg'] * 0.2
    position_effect = -df['diff_position'] * 0.05
    h2h_effect = (df['h2h_wins'] - df['h2h_losses']) * 0.1
    
    # Combined effect
    combined_effect = home_advantage + form_effect + position_effect + h2h_effect
    
    # Generate probabilities
    home_prob = 1 / (1 + np.exp(-combined_effect))
    away_prob = 1 / (1 + np.exp(combined_effect))
    draw_prob = 1 - home_prob - away_prob
    
    # Ensure valid probabilities
    draw_prob = np.maximum(draw_prob, 0.1)
    total = home_prob + draw_prob + away_prob
    home_prob /= total
    draw_prob /= total
    away_prob /= total
    
    # Generate labels
    labels = []
    one_hot_data = []
    
    for i in range(n_samples):
        probs = [away_prob[i], draw_prob[i], home_prob[i]]
        label = np.random.choice([0, 1, 2], p=probs)
        labels.append(label)
        
        if label == 0:
            one_hot = [1, 0, 0]
        elif label == 1:
            one_hot = [0, 1, 0]
        else:
            one_hot = [0, 0, 1]
        one_hot_data.append(one_hot)
    
    df['label'] = labels
    df['one_hot_away'] = [row[0] for row in one_hot_data]
    df['one_hot_draw'] = [row[1] for row in one_hot_data]
    df['one_hot_home'] = [row[2] for row in one_hot_data]
    
    # Split into train and validation
    train_df = df[df['season'] != 2024].copy()
    valid_df = df[df['season'] == 2024].copy()
    
    return train_df, valid_df
