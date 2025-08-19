import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
import json
from app.api import app
from app.models import Match, Team

client = TestClient(app)


class TestHealthEndpoint:
    """Test health check endpoint"""
    
    def test_health_check_success(self):
        """Test successful health check"""
        with patch('app.api.load_model'):
            response = client.get("/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert data["database_connected"] == True
    
    def test_health_check_model_not_found(self):
        """Test health check when model is not found"""
        with patch('app.api.load_model', side_effect=Exception("Model not found")):
            response = client.get("/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "unhealthy"
            assert data["model_version"] is None


class TestPredictEndpoint:
    """Test prediction endpoint"""
    
    @patch('app.api.load_model')
    @patch('app.api.get_db')
    def test_predict_match_success(self, mock_get_db, mock_load_model):
        """Test successful match prediction"""
        # Mock database session
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        
        # Mock match
        mock_match = Mock()
        mock_match.id = 12345
        mock_match.status = "SCHEDULED"
        mock_match.utc_date = "2024-01-15T19:00:00Z"
        mock_match.home_team_id = 64
        mock_match.away_team_id = 65
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_match
        
        # Mock features
        mock_features = {
            'diff_form_ppg': 0.5,
            'diff_goals_for_per_match': 0.2,
            'home_flag': 1.0,
            'data_quality': {'home_matches': 5, 'away_matches': 5}
        }
        
        with patch('app.api.get_features_for_match', return_value=mock_features):
            with patch('app.api.model') as mock_model:
                with patch('app.api.scaler') as mock_scaler:
                    # Mock model prediction
                    mock_model.predict_proba.return_value = [[0.3, 0.25, 0.45]]
                    mock_scaler.transform.return_value = [[0.1, 0.2, 0.3, 0.4]]
                    
                    response = client.get("/predict?match_id=12345")
                    
                    assert response.status_code == 200
                    data = response.json()
                    assert data["match_id"] == 12345
                    assert data["probs"]["home"] == 0.45
                    assert data["probs"]["draw"] == 0.25
                    assert data["probs"]["away"] == 0.3
                    assert len(data["top_features"]) > 0
    
    @patch('app.api.load_model')
    @patch('app.api.get_db')
    def test_predict_match_not_found(self, mock_get_db, mock_load_model):
        """Test prediction for non-existent match"""
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        response = client.get("/predict?match_id=99999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    
    @patch('app.api.load_model')
    @patch('app.api.get_db')
    def test_predict_finished_match(self, mock_get_db, mock_load_model):
        """Test prediction for finished match"""
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        
        mock_match = Mock()
        mock_match.id = 12345
        mock_match.status = "FINISHED"
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_match
        
        response = client.get("/predict?match_id=12345")
        assert response.status_code == 400
        assert "finished" in response.json()["detail"]
    
    @patch('app.api.load_model')
    @patch('app.api.get_db')
    def test_predict_insufficient_history(self, mock_get_db, mock_load_model):
        """Test prediction with insufficient history"""
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        
        mock_match = Mock()
        mock_match.id = 12345
        mock_match.status = "SCHEDULED"
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_match
        
        with patch('app.api.get_features_for_match', side_effect=Exception("Insufficient history")):
            response = client.get("/predict?match_id=12345")
            assert response.status_code == 422
            assert "Insufficient history" in response.json()["detail"]


class TestBatchPredictEndpoint:
    """Test batch prediction endpoint"""
    
    @patch('app.api.load_model')
    @patch('app.api.get_db')
    def test_batch_predict_success(self, mock_get_db, mock_load_model):
        """Test successful batch prediction"""
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        
        # Mock matches
        mock_match = Mock()
        mock_match.id = 12345
        mock_match.status = "SCHEDULED"
        mock_match.utc_date = "2024-01-15T19:00:00Z"
        mock_match.home_team_id = 64
        mock_match.away_team_id = 65
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_match
        
        # Mock features
        mock_features = {
            'diff_form_ppg': 0.5,
            'home_flag': 1.0,
            'data_quality': {'home_matches': 5, 'away_matches': 5}
        }
        
        with patch('app.api.get_features_for_match', return_value=mock_features):
            with patch('app.api.model') as mock_model:
                with patch('app.api.scaler') as mock_scaler:
                    mock_model.predict_proba.return_value = [[0.3, 0.25, 0.45]]
                    mock_scaler.transform.return_value = [[0.1, 0.2, 0.3, 0.4]]
                    
                    response = client.post("/batch/predict", json={"match_ids": [12345]})
                    
                    assert response.status_code == 200
                    data = response.json()
                    assert len(data["predictions"]) == 1
                    assert data["predictions"][0]["match_id"] == 12345


class TestFeaturesEndpoint:
    """Test features endpoint"""
    
    @patch('app.api.get_db')
    def test_get_features_success(self, mock_get_db):
        """Test successful features retrieval"""
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        
        mock_match = Mock()
        mock_match.id = 12345
        mock_db.query.return_value.filter.return_value.first.return_value = mock_match
        
        mock_features = {
            'diff_form_ppg': 0.5,
            'home_flag': 1.0,
            'data_quality': {'home_matches': 5, 'away_matches': 5}
        }
        
        with patch('app.api.get_features_for_match', return_value=mock_features):
            response = client.get("/features?match_id=12345")
            
            assert response.status_code == 200
            data = response.json()
            assert data["match_id"] == 12345
            assert data["features"]["diff_form_ppg"] == 0.5
            assert data["features"]["home_flag"] == 1.0
    
    @patch('app.api.get_db')
    def test_get_features_match_not_found(self, mock_get_db):
        """Test features for non-existent match"""
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        response = client.get("/features?match_id=99999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]


if __name__ == "__main__":
    pytest.main([__file__])
