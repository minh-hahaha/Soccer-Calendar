"""
Enhanced Machine Learning Service
Combines the best of both FantasyFootballAgent and the new architecture
"""
import asyncio
import logging
import joblib
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
import requests

# ML imports
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.pipeline import Pipeline
import xgboost as xgb

from ..core.config import get_settings
from ..core.database import get_db_session
from ..core.exceptions import ModelError
from ..api.v2.fantasy_agent import FantasyFootballAgent, PlayerPrediction, TransferRecommendation

logger = logging.getLogger(__name__)
settings = get_settings()


class MLService:
    """
    Enhanced ML Service that combines pure ML operations with Fantasy Football logic
    This replaces both the basic ml_service.py and integrates your FantasyFootballAgent
    """
    
    def __init__(self, db_connection_string: str = None):
        self.settings = settings
        self.db_connection = db_connection_string or settings.DATABASE_URL
        
        # Initialize the existing FantasyFootballAgent (your working code)
        self.fantasy_agent = FantasyFootballAgent(self.db_connection)
        
        # ML-specific attributes
        self.model_path = Path(settings.MODEL_PATH)
        self.model_path.mkdir(parents=True, exist_ok=True)
        
    # ==========================================
    # ML SERVICE METHODS (for the new architecture)
    # ==========================================
    
    async def train_all_models(self, force_retrain: bool = False) -> bool:
        """Train all ML models (async wrapper for your existing training)"""
        try:
            logger.info("Starting ML model training...")
            
            # Initialize data
            success = self.fantasy_agent.initialize_data()
            if not success:
                raise ModelError("Failed to initialize fantasy agent data")
            
            # Train models using your existing logic
            self.fantasy_agent.train_prediction_models()
            
            logger.info("Model training completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Model training failed: {str(e)}")
            return False
    
    async def load_models(self) -> bool:
        """Load pre-trained models (async wrapper)"""
        try:
            # Try to load models using your existing method
            success = self.fantasy_agent.load_models()
            return success
        except Exception as e:
            logger.error(f"Failed to load models: {str(e)}")
            return False
    
    def get_model_status(self) -> Dict[str, Any]:
        """Get current model status"""
        return {
            'models_available': list(self.fantasy_agent.models.keys()) if self.fantasy_agent.models else [],
            'model_performance': self.fantasy_agent.model_performance,
            'data_initialized': self.fantasy_agent.bootstrap_data is not None,
            'current_gameweek': self.fantasy_agent.current_gameweek
        }
    
    # ==========================================
    # FANTASY FOOTBALL METHODS (your existing functionality)
    # ==========================================
    
    def predict_player_performance(self, player_data: Dict) -> PlayerPrediction:
        """Predict player performance using your existing logic"""
        return self.fantasy_agent.predict_player_performance(player_data)
    
    def get_transfer_recommendations(self, current_team: List[int], budget: float) -> List[TransferRecommendation]:
        """Get AI transfer recommendations"""
        return self.fantasy_agent.get_ai_transfer_recommendations(current_team, budget)
    
    def get_captain_recommendations(self, gameweeks_ahead: int = 1) -> List[Dict]:
        """Get AI captain recommendations"""
        return self.fantasy_agent.get_ai_captain_recommendations(gameweeks_ahead)
    
    def get_differential_picks(self, risk_tolerance: str = "medium") -> List[Dict]:
        """Get differential pick recommendations"""
        return self.fantasy_agent.get_ai_differential_picks(risk_tolerance)
    
    def get_market_insights(self) -> Dict[str, Any]:
        """Get market insights"""
        return self.fantasy_agent._get_market_insights()
    
    def get_player_predictions_batch(self, player_ids: List[int] = None, position: str = None, limit: int = 20) -> List[Dict]:
        """Get predictions for multiple players"""
        if not self.fantasy_agent.bootstrap_data:
            if not self.fantasy_agent.initialize_data():
                raise ModelError("Failed to initialize data")
        
        players = self.fantasy_agent.bootstrap_data['elements']
        
        # Filter players
        if player_ids:
            players = [p for p in players if p['id'] in player_ids]
        
        if position:
            position_map = {"GKP": 1, "DEF": 2, "MID": 3, "FWD": 4}
            if position in position_map:
                players = [p for p in players if p['element_type'] == position_map[position]]
        
        # Filter by minimum minutes
        players = [p for p in players if p.get('minutes', 0) >= 200]
        
        predictions = []
        for player in players[:limit]:
            try:
                pred = self.fantasy_agent.predict_player_performance(player)
                predictions.append({
                    "player_id": pred.player_id,
                    "name": pred.name,
                    "team": self.fantasy_agent._get_team_name(player['team']),
                    "position": self.fantasy_agent._get_position_name(player['element_type']),
                    "current_price": player['now_cost'] / 10,
                    "predicted_points": round(pred.predicted_points, 1),
                    "predicted_goals": round(pred.predicted_goals, 1),
                    "predicted_assists": round(pred.predicted_assists, 1),
                    "prediction_confidence": round(pred.prediction_confidence, 3),
                    "risk_score": round(pred.risk_score, 3),
                    "value_score": round(pred.value_score, 2),
                    "next_5_gameweeks": [round(x, 1) for x in pred.next_5_gameweeks],
                    "current_form": player.get('form', 0),
                    "ownership": player.get('selected_by_percent', 0)
                })
            except Exception as e:
                logger.warning(f"Prediction failed for player {player.get('id')}: {str(e)}")
                continue
        
        # Sort by predicted points
        predictions.sort(key=lambda x: x['predicted_points'], reverse=True)
        return predictions
    
    def get_model_performance_report(self) -> Dict:
        """Get detailed model performance report"""
        return self.fantasy_agent.get_model_performance_report()
    
    # ==========================================
    # PIPELINE INTEGRATION METHODS
    # ==========================================
    
    async def initialize_for_pipeline(self) -> bool:
        """Initialize the service for pipeline operations"""
        try:
            success = self.fantasy_agent.initialize_data()
            return success
        except Exception as e:
            logger.error(f"Pipeline initialization failed: {str(e)}")
            return False
    
    def refresh_current_data(self) -> bool:
        """Refresh current season data from FPL API"""
        try:
            self.fantasy_agent._fetch_current_data()
            return True
        except Exception as e:
            logger.error(f"Failed to refresh current data: {str(e)}")
            return False
    
    # ==========================================
    # HEALTH CHECK METHODS
    # ==========================================
    
    def health_check(self) -> Dict[str, Any]:
        """Comprehensive health check for ML service"""
        try:
            model_files = list(self.model_path.glob("*.pkl"))
            
            return {
                'healthy': len(self.fantasy_agent.models) > 0,
                'models_trained': list(self.fantasy_agent.models.keys()),
                'model_files_on_disk': [f.name for f in model_files],
                'data_initialized': self.fantasy_agent.bootstrap_data is not None,
                'historical_data_loaded': self.fantasy_agent.historical_data is not None,
                'current_gameweek': self.fantasy_agent.current_gameweek,
            }
        except Exception as e:
            return {
                'healthy': False,
                'error': str(e)
            }


