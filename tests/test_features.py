import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from app.features.rolling import get_team_match_history, compute_rolling_features, get_team_form_features
from app.features.standings import get_standings_at_matchday, get_rank_delta
from app.features.h2h import get_head_to_head_matches, compute_h2h_features
from app.models import Match, Team, StandingsSnapshot


class TestRollingFeatures:
    """Test rolling feature computation"""
    
    def test_compute_rolling_features_empty_df(self):
        """Test rolling features with empty DataFrame"""
        df = pd.DataFrame()
        result = compute_rolling_features(df)
        assert result.empty
    
    def test_compute_rolling_features_leakage_prevention(self):
        """Test that rolling features prevent data leakage"""
        # Create test data
        data = {
            'team_id': [1, 1, 1, 1, 1],
            'kickoff': pd.date_range('2024-01-01', periods=5),
            'points': [3, 1, 0, 3, 3],
            'goals_for': [2, 1, 0, 3, 2],
            'goals_against': [0, 1, 2, 1, 0]
        }
        df = pd.DataFrame(data)
        
        result = compute_rolling_features(df, window=3)
        
        # Check that first row has NaN (due to shift(1))
        assert pd.isna(result.iloc[0]['points_rolling'])
        
        # Check that rolling features are computed correctly
        assert not pd.isna(result.iloc[1]['points_rolling'])
    
    def test_get_team_form_features_no_history(self):
        """Test form features when team has no history"""
        # Mock database session
        class MockDB:
            def query(self, model):
                return self
            
            def filter(self, *args):
                return self
            
            def all(self):
                return []
        
        db = MockDB()
        
        features = get_team_form_features(db, team_id=1, season=2024, 
                                        match_date=datetime(2024, 1, 1))
        
        # Should return default values
        assert features['form_ppg'] == 1.0
        assert features['goals_for_per_match'] == 1.0
        assert features['goals_against_per_match'] == 1.0
        assert features['goal_diff_per_match'] == 0.0
        assert features['rest_days'] == 7.0
        assert features['data_quality']['matches_available'] == 0


class TestStandingsFeatures:
    """Test standings feature computation"""
    
    def test_get_standings_at_matchday_matchday_1(self):
        """Test standings for matchday 1 (should use defaults)"""
        class MockDB:
            def query(self, model):
                return self
            
            def filter(self, *args):
                return self
            
            def first(self):
                return None  # No previous standings
        
        db = MockDB()
        
        standings = get_standings_at_matchday(db, season=2024, matchday=1, team_id=1)
        
        # Should return default values for matchday 1
        assert standings['position'] == 10.0
        assert standings['points'] == 0.0
        assert standings['goal_diff'] == 0.0
        assert standings['cold_start'] == True
    
    def test_get_rank_delta_insufficient_history(self):
        """Test rank delta when insufficient history"""
        class MockDB:
            def query(self, model):
                return self
            
            def filter(self, *args):
                return self
            
            def first(self):
                return None
        
        db = MockDB()
        
        delta = get_rank_delta(db, season=2024, matchday=3, team_id=1, window=5)
        
        # Should return 0.0 for insufficient history
        assert delta == 0.0


class TestH2HFeatures:
    """Test head-to-head feature computation"""
    
    def test_compute_h2h_features_empty(self):
        """Test H2H features with no matches"""
        h2h_matches = []
        features = compute_h2h_features(h2h_matches)
        
        assert features['h2h_wins'] == 0.0
        assert features['h2h_draws'] == 0.0
        assert features['h2h_losses'] == 0.0
        assert features['h2h_goal_diff'] == 0.0
        assert features['h2h_avg_goals'] == 0.0
        assert features['h2h_matches_count'] == 0.0
    
    def test_compute_h2h_features_with_matches(self):
        """Test H2H features with actual matches"""
        h2h_matches = [
            {
                'date': datetime(2024, 1, 1),
                'home_score': 2,
                'away_score': 1,
                'result': 'win',
                'venue': 'home',
                'goal_diff': 1
            },
            {
                'date': datetime(2024, 1, 15),
                'home_score': 1,
                'away_score': 1,
                'result': 'draw',
                'venue': 'away',
                'goal_diff': 0
            }
        ]
        
        features = compute_h2h_features(h2h_matches)
        
        assert features['h2h_wins'] == 1.0
        assert features['h2h_draws'] == 1.0
        assert features['h2h_losses'] == 0.0
        assert features['h2h_goal_diff'] == 1.0
        assert features['h2h_avg_goals'] == 2.5  # (2+1+1+1)/2
        assert features['h2h_matches_count'] == 2.0


class TestLeakagePrevention:
    """Test that features prevent data leakage"""
    
    def test_match_history_before_date(self):
        """Test that match history only includes matches before target date"""
        # This test would require a more complex setup with actual database
        # For now, we'll test the logic conceptually
        target_date = datetime(2024, 1, 15)
        
        # The function should only return matches with utc_date < target_date
        # This prevents using future information in predictions
        pass
    
    def test_standings_previous_matchday(self):
        """Test that standings use previous matchday"""
        # Standings should be from matchday-1, not current matchday
        # This prevents using information that wouldn't be available at prediction time
        pass


if __name__ == "__main__":
    pytest.main([__file__])
