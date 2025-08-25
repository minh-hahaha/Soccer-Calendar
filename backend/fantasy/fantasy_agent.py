import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import requests
from dataclasses import dataclass, asdict
from enum import Enum
import joblib
import logging
from sqlalchemy import create_engine, text
import warnings
warnings.filterwarnings('ignore')

# ML imports
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import Pipeline
import xgboost as xgb

# ENUMS AND DATACLASSES
class FantasyAdviceType(str, Enum):
    TRANSFER = "transfers"
    CAPTAIN = "captain"
    DIFFERENTIAL = "differential"
    BUDGET_OPTIMIZATION = "budget_optimization"
    BENCH_STRATEGY = "bench_strategy"
    FIXTURE_PLANNING = "fixture_planning"


class Position (str, Enum):
    GKP = "Goalkeeper"
    DEF = "Defender"
    MID = "Midfielder"
    FWD = "Forward"

@dataclass
class PlayerPrediction:
    player_id: int
    name: str
    predicted_points: float
    predicted_goals: float
    predicted_assists: float
    predicted_clean_sheets: float
    prediction_confidence: float
    next_5_gameweeks: List[float]
    risk_score: float
    value_score: float

@dataclass
class TransferRecommendation:
    player_out: str
    player_in: str
    predicted_points_gain: float
    confidence: float
    risk_level: str
    reasoning: str
    cost_impact: float

class FantasyFootballAgent:
    """ AI Agent for Fantasy Football Analysis and Recommendations"""

    def __init__(self, db_connection_string: str, fpl_api_base: str = "https://fantasy.premierleague.com/api/"):
        self.db_engine = create_engine(db_connection_string)
        self.fpl_api_base = fpl_api_base

        self.models = {}
        self.scalers = {}
        self.encoders = {}
        self.model_performance = {}

        self.current_gameweek = None
        self.bootstrap_data = None
        self.fixtures_data = None
        self.historical_data = None
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def initialize_data(self):
        """Initialize both historical and current FPL data"""
        try:
            self.logger.info("Initializing AI Fantasy Agent...")
            
            # Load historical data from database
            self._load_historical_data()
            
            # Fetch current season data
            self._fetch_current_data()
            
            # Train ML models if not already trained
            if not self.models:
                self.train_prediction_models()
                
            return True
        except Exception as e:
            self.logger.error(f"Error initializing AI agent: {e}")
            return False
    
    def _load_historical_data(self):
        """Load historical player data from PostgreSQL database"""
        query = """
        SELECT 
            first_name,
            second_name,
            goals_scored,
            assists,
            total_points,
            minutes,
            goals_conceded,
            creativity,
            influence,
            threat,
            bonus,
            bps,
            ict_index,
            clean_sheets,
            red_cards,
            yellow_cards,
            selected_by_percent,
            now_cost,
            element_type,
            season_year
        FROM player_historical_data 
        WHERE season_year BETWEEN '2016-17' AND '2024-25'
        ORDER BY season_year, first_name, second_name
        """
        
        self.historical_data = pd.read_sql(query, self.db_engine)
        self.logger.info(f"Loaded {len(self.historical_data)} historical records")


    def _fetch_current_data(self):
        """Fetch current season data from FPL API"""
        try:
            # Get bootstrap data
            bootstrap_response = requests.get(f"{self.fpl_api_base}/bootstrap-static/")
            if bootstrap_response.status_code == 200:
                self.bootstrap_data = bootstrap_response.json()
                self.current_gameweek = self._find_current_gameweek()
            
            # Get fixtures data
            fixtures_response = requests.get(f"{self.fpl_api_base}/fixtures/")
            if fixtures_response.status_code == 200:
                self.fixtures_data = fixtures_response.json()
                
        except Exception as e:
            self.logger.error(f"Error fetching current data: {e}")

    def _find_current_gameweek(self) -> Optional[int]:
        """Find current gameweek from bootstrap data"""
        if not self.bootstrap_data:
            return None
        
        for gw in self.bootstrap_data["events"]:
            if gw["is_current"]:
                return gw["id"]
        return None
    
    def prepare_training_data(self) -> pd.DataFrame:
        """Prepare training data with feature engineering"""
        if self.historical_data is None:
            raise ValueError("Historical data not loaded")
        
        df = self.historical_data.copy()
        
        # Feature engineering
        df['points_per_90'] = (df['total_points'] / df['minutes'] * 90).fillna(0)
        df['goals_per_90'] = (df['goals_scored'] / df['minutes'] * 90).fillna(0)
        df['assists_per_90'] = (df['assists'] / df['minutes'] * 90).fillna(0)
        df['value_score'] = df['total_points'] / (df['now_cost'] / 10)
        df['form_score'] = df['total_points'] / df['total_points'].rolling(5, min_periods=1).mean()
        
        # Position encoding
        position_encoder = LabelEncoder()
        df['position_encoded'] = position_encoder.fit_transform(df['element_type'])
        self.encoders['position'] = position_encoder
        
        # Create lagged features (previous season performance)
        df = df.sort_values(['first_name', 'second_name', 'season_year'])
        for col in ['total_points', 'goals_scored', 'assists', 'minutes']:
            df[f'{col}_prev'] = df.groupby(['first_name', 'second_name'])[col].shift(1)
        
        # Fill NaN values
        numeric_columns = df.select_dtypes(include=[np.number]).columns
        df[numeric_columns] = df[numeric_columns].fillna(0)
        
        return df

    def train_prediction_models(self):
        """Train ML models for different prediction tasks"""
        self.logger.info("Training ML models...")
        
        df = self.prepare_training_data()
        
        # Define features for training
        feature_columns = [
            'minutes', 'creativity', 'influence', 'threat', 'ict_index',
            'selected_by_percent', 'now_cost', 'position_encoded',
            'points_per_90', 'goals_per_90', 'assists_per_90', 'value_score',
            'total_points_prev', 'goals_scored_prev', 'assists_prev', 'minutes_prev'
        ]
        
        X = df[feature_columns].fillna(0)
        X = X.replace([np.inf, -np.inf], 0)
        
        # print("Any inf in X?", np.isinf(X).any().any())
        # print("Any NaN in X?", np.isnan(X).any().any())
        # print("Max value in X:", X.max().max())
        # print("Min value in X:", X.min().min())      
        
        # Train models for different targets
        targets = {
            'total_points': df['total_points'],
            'goals_scored': df['goals_scored'],
            'assists': df['assists'],
            'clean_sheets': df['clean_sheets']
        }
        
        for target_name, y in targets.items():
            self.logger.info(f"Training model for {target_name}")

            # Split data
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            
            # Create ensemble model
            models = {
                'rf': RandomForestRegressor(n_estimators=100, random_state=42),
                'gb': GradientBoostingRegressor(n_estimators=100, random_state=42),
                'xgb': xgb.XGBRegressor(n_estimators=100, random_state=42)
            }
            
            best_model = None
            best_score = -np.inf
            
            for model_name, model in models.items():
                # Create pipeline with scaler
                pipeline = Pipeline([
                    ('scaler', StandardScaler()),
                    ('model', model)
                ])
                
                # Cross-validation
                cv_scores = cross_val_score(pipeline, X_train, y_train, cv=5, scoring='r2')
                avg_score = cv_scores.mean()
                
                if avg_score > best_score:
                    best_score = avg_score
                    best_model = pipeline
                    
                self.logger.info(f"{target_name} - {model_name}: CV R2 = {avg_score:.3f}")
            
            # Train best model on full training set
            best_model.fit(X_train, y_train)
            
            # Test performance
            y_pred = best_model.predict(X_test)
            mae = mean_absolute_error(y_test, y_pred)
            mse = mean_squared_error(y_test, y_pred)
            r2 = r2_score(y_test, y_pred)
            
            self.models[target_name] = best_model
            self.model_performance[target_name] = {
                'mae': mae,
                'mse': mse,
                'r2': r2,
                'cv_score': best_score
            }
            
            self.logger.info(f"{target_name} final model - MAE: {mae:.3f}, R2: {r2:.3f}")
        
        # Save models
        self._save_models()

    def predict_player_performance(self, player_data: Dict) -> PlayerPrediction:
        """Predict individual player performance"""
        if not self.models:
            raise ValueError("Models not trained. Call train_prediction_models() first.")
        
        # Prepare features for prediction
        features = self._extract_features_from_current_data(player_data)
        
        # Make predictions
        predictions = {}
        confidences = {}
        
        for target, model in self.models.items():
            pred = model.predict([features])[0]
            predictions[target] = max(0, pred)  # Ensure non-negative predictions
            
            # Calculate confidence based on model performance
            r2_score = self.model_performance[target]['r2']
            confidences[target] = min(0.95, max(0.1, r2_score))
        
        # Calculate risk and value scores
        risk_score = self._calculate_risk_score(player_data, predictions)
        value_score = predictions['total_points'] / (player_data['now_cost'] / 10)
        
        # Predict next 5 gameweeks (simplified)
        next_5_gws = [predictions['total_points'] / 38 * (i + 1) for i in range(5)]
        
        return PlayerPrediction(
            player_id=player_data['id'],
            name=f"{player_data['first_name']} {player_data['second_name']}",
            predicted_points=predictions['total_points'],
            predicted_goals=predictions['goals_scored'],
            predicted_assists=predictions['assists'],
            predicted_clean_sheets=predictions['clean_sheets'],
            prediction_confidence=np.mean(list(confidences.values())),
            next_5_gameweeks=next_5_gws,
            risk_score=risk_score,
            value_score=value_score
        )
    
    def _extract_features_from_current_data(self, player_data: Dict) -> List[float]:
        """Extract features from current player data for prediction"""
        # Map element_type to encoded position
        position_mapping = {1: 'GKP', 2: 'DEF', 3: 'MID', 4: 'FWD'}
        position = position_mapping.get(player_data['element_type'], 'MID')
        
        # Calculate derived features
        minutes = player_data.get('minutes', 0)
        points_per_90 = (player_data['total_points'] / minutes * 90) if minutes > 0 else 0
        goals_per_90 = (player_data.get('goals_scored', 0) / minutes * 90) if minutes > 0 else 0
        assists_per_90 = (player_data.get('assists', 0) / minutes * 90) if minutes > 0 else 0
        value_score = player_data['total_points'] / (player_data['now_cost'] / 10) if player_data['now_cost'] > 0 else 0
        
        features = [
            minutes,
            float(player_data.get('creativity', 0)),
            float(player_data.get('influence', 0)),
            float(player_data.get('threat', 0)),
            float(player_data.get('ict_index', 0)),
            float(player_data.get('selected_by_percent', 0)),
            player_data['now_cost'],
            player_data['element_type'] - 1,  # 0-indexed
            points_per_90,
            goals_per_90,
            assists_per_90,
            value_score,
            # Previous season data (would need to query from historical data)
            0, 0, 0, 0  # Placeholder for prev season stats
        ]
        
        return features

    def _calculate_risk_score(self, player_data: Dict, predictions: Dict) -> float:
        """Calculate risk score for a player"""
        risk_factors = []
        
        # Injury risk
        if player_data.get('chance_of_playing_next_round'):
            injury_risk = (100 - player_data['chance_of_playing_next_round']) / 100
            risk_factors.append(injury_risk * 0.4)
        
        # Minutes consistency
        minutes = player_data.get('minutes', 0)
        if minutes < 500:  # Less than ~13 games worth
            risk_factors.append(0.3)
        
        # Price volatility
        cost_change = abs(player_data.get('cost_change_event', 0))
        if cost_change > 2:
            risk_factors.append(0.2)
        
        return min(1.0, sum(risk_factors))

    def get_ai_transfer_recommendations(self, current_team: List[int], budget: float) -> List[TransferRecommendation]:
        """Get AI-powered transfer recommendations"""
        if not self.bootstrap_data:
            self.initialize_data()
        
        recommendations = []
        players = self.bootstrap_data['elements']
        
        # Get predictions for all players
        player_predictions = {}
        for player in players:
            if player['minutes'] > 50:  # Only consider players with some playing time
                pred = self.predict_player_performance(player)
                player_predictions[player['id']] = pred
        
        # Analyze current team
        current_team_predictions = {pid: player_predictions.get(pid) for pid in current_team if pid in player_predictions}
        
        # Find improvement opportunities
        for current_player_id in current_team:
            if current_player_id not in current_team_predictions:
                continue
                
            current_pred = current_team_predictions[current_player_id]
            current_player = next(p for p in players if p['id'] == current_player_id)
            
            # Find better alternatives in same position
            same_position_players = [p for p in players if p['element_type'] == current_player['element_type']]
            
            for alt_player in same_position_players:
                if alt_player['id'] == current_player_id or alt_player['id'] not in player_predictions:
                    continue
                
                alt_pred = player_predictions[alt_player['id']]
                cost_diff = (alt_player['now_cost'] - current_player['now_cost']) / 10
                
                # Check if transfer is viable
                if cost_diff <= budget and alt_pred.predicted_points > current_pred.predicted_points + 5:
                    points_gain = alt_pred.predicted_points - current_pred.predicted_points
                    confidence = (alt_pred.prediction_confidence + current_pred.prediction_confidence) / 2
                    
                    recommendation = TransferRecommendation(
                        player_out=f"{current_player['first_name']} {current_player['second_name']}",
                        player_in=f"{alt_player['first_name']} {alt_player['second_name']}",
                        predicted_points_gain=points_gain,
                        confidence=confidence,
                        risk_level="LOW" if alt_pred.risk_score < 0.3 else "MEDIUM" if alt_pred.risk_score < 0.6 else "HIGH",
                        reasoning=f"AI predicts {points_gain:.1f} more points. Value score: {alt_pred.value_score:.2f}",
                        cost_impact=cost_diff
                    )
                    
                    recommendations.append(recommendation)
        
        # Sort by predicted points gain and confidence
        recommendations.sort(key=lambda x: x.predicted_points_gain * x.confidence, reverse=True)
        return recommendations[:5]
    
    def get_ai_captain_recommendations(self, gameweeks_ahead: int = 1) -> List[Dict]:
        """Get AI-powered captain recommendations"""
        if not self.bootstrap_data:
            self.initialize_data()
        
        players = self.bootstrap_data['elements']
        captain_candidates = []
        
        # Focus on premium players
        premium_players = [p for p in players if p['now_cost'] >= 80 and float(p['selected_by_percent']) >= 10]
        
        for player in premium_players:
            pred = self.predict_player_performance(player)
            
            # Get next fixture info
            next_fixture = self._get_next_fixture(player['team'])
            fixture_difficulty = 3  # Default, would calculate based on fixtures
            
            # Adjust prediction based on fixture
            adjusted_points = pred.predicted_points * (6 - fixture_difficulty) / 3 / 38 * gameweeks_ahead
            
            captain_candidates.append({
                'player': f"{player['first_name']} {player['second_name']}",
                'team': self._get_team_name(player['team']),
                'predicted_points': adjusted_points,
                'confidence': pred.prediction_confidence,
                'risk_score': pred.risk_score,
                'ownership': float(player['selected_by_percent']),
                'reasoning': f"AI predicts {adjusted_points:.1f} points with {pred.prediction_confidence:.1%} confidence"
            })
        
        return sorted(captain_candidates, key=lambda x: x['predicted_points'] * x['confidence'], reverse=True)[:6]
    
    def _get_market_insights(self) -> Dict[str, Any]:
        """Analyze current FPL market trends"""
        if not self.bootstrap_data:
            return {}

        players = self.bootstrap_data["elements"]

        # price risers and fallers
        price_changes = []
        for player in players:
            if abs(player["cost_change_event"]) > 0:
                price_changes.append({
                    "name": f"{player['first_name']} {player['second_name']}",
                    "team": self._get_team_name(player["team"]),
                    "change": player["cost_change_event"] / 10, 
                    "new_price": player["now_cost"] / 10,
                    "selected_by_percent": player["selected_by_percent"],
                })

        # most transferred in/out
        transfers_in = sorted(players, key = lambda x: x.get("transfers_in_event",0), reverse = True) [:5]
        transfers_out = sorted(players, key = lambda x: x.get("transfers_out_event",0), reverse = True) [:5]

        # top scorers
        top_scorers = sorted(players, key = lambda x: x.get("total_points",0), reverse = True) [:5]

        return {
            "price_changes": sorted(price_changes, key=lambda x: abs(x["change"]), reverse=True)[:10],
            "transfers_in": [self._player_summary(p) for p in transfers_in],
            "transfers_out": [self._player_summary(p) for p in transfers_out],
            "top_scorers": [self._player_summary(p) for p in top_scorers]
        }

    def _player_summary(self, player: Dict) -> Dict[str, Any]:
        """Create player summary"""
        return {
            "name": f"{player['first_name']} {player['second_name']}",
            "team": self._get_team_name(player["team"]),
            "position": self._get_position_name(player["element_type"]),
            "price": player["now_cost"] / 10,
            "points": player["total_points"],
            "form": player.get("form", 0),
            "selected_by": player["selected_by_percent"]
        }

    def _save_models(self):
        """Save trained models to disk"""
        model_data = {
            'models': self.models,
            'performance': self.model_performance,
            'encoders': self.encoders,
            'timestamp': datetime.now().isoformat()
        }
        joblib.dump(model_data, 'fantasy_ai_models.pkl')
        self.logger.info("Models saved successfully")

    def load_models(self):
        """Load pre-trained models from disk"""
        try:
            model_data = joblib.load('fantasy_ai_models.pkl')
            self.models = model_data['models']
            self.model_performance = model_data['performance']
            self.encoders = model_data['encoders']
            self.logger.info("Models loaded successfully")
            return True
        except FileNotFoundError:
            self.logger.warning("No saved models found. Need to train models first.")
            return False
        
    # Helper methods 
    def _get_team_name(self, team_id: int) -> str:
        """Get team name from team ID"""
        if self.bootstrap_data:
            for team in self.bootstrap_data["teams"]:
                if team["id"] == team_id:
                    return team["short_name"]
        return f"Team {team_id}"
    
    def _get_position_name(self, element_type: int) -> str:
        """Get position name from element type"""
        position_map = {1: "Goalkeeper", 2: "Defender", 3: "Midfielder", 4: "Forward"}
        return position_map.get(element_type, "Unknown")
    
    def _get_next_fixture(self, team_id: int) -> Optional[Dict]:
        """Get next fixture for a team"""
        if not self.fixtures_data:
            return None
        
        upcoming = [f for f in self.fixtures_data 
                   if (f["team_h"] == team_id or f["team_a"] == team_id) 
                   and not f["finished"] and f["event"] is not None]
        
        return sorted(upcoming, key=lambda x: x["event"])[0] if upcoming else None
    
    def _get_team_fixtures(self, team_id: int, gameweeks_ahead: int) -> List[Dict]:
        """Get upcoming fixtures for a team"""
        if not self.fixtures_data:
            return []
        
        current_gw = self.current_gameweek or 1
        upcoming = [f for f in self.fixtures_data 
                   if (f["team_h"] == team_id or f["team_a"] == team_id) 
                   and not f["finished"] 
                   and f["event"] is not None
                   and current_gw <= f["event"] <= current_gw + gameweeks_ahead]
        
        return sorted(upcoming, key=lambda x: x["event"])
    

    def get_ai_differential_picks(self, risk_tolerance: str = "medium") -> List[Dict]:
        """Get AI-powered differential pick recommendations"""
        if not self.bootstrap_data:
            self.initialize_data()
        
        players = self.bootstrap_data['elements']
        differentials = []

        ### Risk Tolerance Levels:
        # Low Risk: Max 3% ownership, high confidence (70%+), low risk score
        # Medium Risk: Max 8% ownership, medium confidence (50%+), moderate risk
        # High Risk: Max 15% ownership, lower confidence thresholds, higher risk tolerance
                
        # Risk tolerance thresholds
        risk_thresholds = {
            "low": {"max_ownership": 3.0, "min_confidence": 0.7, "max_risk": 0.3},
            "medium": {"max_ownership": 8.0, "min_confidence": 0.5, "max_risk": 0.6},
            "high": {"max_ownership": 15.0, "min_confidence": 0.3, "max_risk": 1.0}
        }


        threshold = risk_thresholds.get(risk_tolerance, risk_thresholds["medium"])
        
        for player in players:
            ownership = float(player.get('selected_by_percent', 0))
            
            # Only consider low-owned players with decent minutes
            if ownership <= threshold["max_ownership"] and player.get('minutes', 0) > 200:
                try:
                    pred = self.predict_player_performance(player)
                    
                    # Filter by confidence and risk
                    if (pred.prediction_confidence >= threshold["min_confidence"] and 
                        pred.risk_score <= threshold["max_risk"] and
                        pred.value_score > 1.5):
                        
                        differentials.append({
                            "name": f"{player['first_name']} {player['second_name']}",
                            "team": self._get_team_name(player['team']),
                            "position": self._get_position_name(player['element_type']),
                            "price": player['now_cost'] / 10,
                            "ownership": ownership,
                            "predicted_points": round(pred.predicted_points, 1),
                            "value_score": round(pred.value_score, 2),
                            "risk_score": round(pred.risk_score, 3),
                            "confidence": round(pred.prediction_confidence, 3),
                            "differential_potential": round((threshold["max_ownership"] - ownership) / threshold["max_ownership"], 2),
                            "reasoning": f"Low ownership ({ownership}%) with strong AI prediction ({pred.predicted_points:.0f} pts). Value score: {pred.value_score:.2f}",
                            "risk_level": "LOW" if pred.risk_score < 0.3 else "MEDIUM" if pred.risk_score < 0.6 else "HIGH"
                        })
                except Exception:
                    continue
        
        # Sort by combination of predicted points and differential potential
        differentials.sort(key=lambda x: x['predicted_points'] * x['differential_potential'], reverse=True)
        
        return differentials[:8]  # Return top 8 differential picks
    

    def get_model_performance_report(self) -> Dict:
        """Get detailed model performance report"""
        return {
            'model_performance': self.model_performance,
            'training_data_size': len(self.historical_data) if self.historical_data is not None else 0,
            'models_trained': list(self.models.keys()),
            'last_trained': datetime.now().isoformat()
        }
    
    

    


