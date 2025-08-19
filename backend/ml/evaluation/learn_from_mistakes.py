import pandas as pd
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Dict, Tuple, Optional
from datetime import datetime, timedelta
import joblib
import os
from sklearn.metrics import log_loss, accuracy_score
from sklearn.calibration import CalibratedClassifierCV
import warnings
warnings.filterwarnings('ignore')

from database.db import get_db
from database.models import Match, Prediction, FeaturesMatch
from ml.training.dataset import prepare_features, prepare_labels, get_feature_columns
from ml.training.train import train_xgboost, train_random_forest, train_logistic_regression
from config import settings


class PredictionErrorAnalyzer:
    """Analyze prediction errors and learn from mistakes"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_finished_matches_with_predictions(self, 
                                            season: Optional[int] = None,
                                            matchday: Optional[int] = None,
                                            days_back: Optional[int] = None) -> pd.DataFrame:
        """Get finished matches that have predictions"""
        
        query = self.db.query(Match, Prediction).join(Prediction).filter(
            Match.status == "FINISHED",
            Match.home_score.isnot(None),
            Match.away_score.isnot(None)
        )
        
        if season:
            query = query.filter(Match.season == season)
        
        if matchday:
            query = query.filter(Match.matchday == matchday)
        
        if days_back:
            cutoff_date = datetime.now() - timedelta(days=days_back)
            query = query.filter(Match.utc_date >= cutoff_date)
        
        results = query.all()
        
        if not results:
            return pd.DataFrame()
        
        data = []
        for match, prediction in results:
            # Determine actual outcome
            if match.home_score > match.away_score:
                actual_outcome = 2  # Home win
            elif match.home_score < match.away_score:
                actual_outcome = 0  # Away win
            else:
                actual_outcome = 1  # Draw
            
            # Calculate prediction error
            predicted_probs = [prediction.p_away, prediction.p_draw, prediction.p_home]
            log_loss_error = log_loss([actual_outcome], [predicted_probs])
            
            # Get predicted outcome
            predicted_outcome = np.argmax(predicted_probs)
            accuracy = 1 if predicted_outcome == actual_outcome else 0
            
            data.append({
                'match_id': match.id,
                'season': match.season,
                'matchday': match.matchday,
                'utc_date': match.utc_date,
                'home_team_id': match.home_team_id,
                'away_team_id': match.away_team_id,
                'home_score': match.home_score,
                'away_score': match.away_score,
                'actual_outcome': actual_outcome,
                'predicted_outcome': predicted_outcome,
                'p_home': prediction.p_home,
                'p_draw': prediction.p_draw,
                'p_away': prediction.p_away,
                'log_loss_error': log_loss_error,
                'accuracy': accuracy,
                'model_version': prediction.model_version,
                'confidence': max(predicted_probs),
                'prediction_error': abs(actual_outcome - predicted_outcome)
            })
        
        return pd.DataFrame(data)
    
    def analyze_prediction_errors(self, df: pd.DataFrame) -> Dict:
        """Analyze prediction errors and patterns"""
        
        if df.empty:
            return {"error": "No data available for analysis"}
        
        analysis = {
            'total_matches': len(df),
            'overall_accuracy': df['accuracy'].mean(),
            'average_log_loss': df['log_loss_error'].mean(),
            'error_distribution': {
                'correct_predictions': (df['accuracy'] == 1).sum(),
                'incorrect_predictions': (df['accuracy'] == 0).sum()
            },
            'outcome_analysis': {
                'home_wins': (df['actual_outcome'] == 2).sum(),
                'draws': (df['actual_outcome'] == 1).sum(),
                'away_wins': (df['actual_outcome'] == 0).sum()
            },
            'confidence_analysis': {
                'high_confidence_errors': len(df[df['confidence'] > 0.6][df['accuracy'] == 0]),
                'low_confidence_correct': len(df[df['confidence'] < 0.4][df['accuracy'] == 1]),
                'average_confidence': df['confidence'].mean()
            },
            'worst_predictions': df.nlargest(10, 'log_loss_error')[['match_id', 'log_loss_error', 'confidence', 'accuracy']].to_dict('records'),
            'best_predictions': df.nsmallest(10, 'log_loss_error')[['match_id', 'log_loss_error', 'confidence', 'accuracy']].to_dict('records')
        }
        
        return analysis
    
    def get_features_for_finished_matches(self, match_ids: List[int]) -> pd.DataFrame:
        """Get features for finished matches"""
        
        features_data = []
        for match_id in match_ids:
            features_record = self.db.query(FeaturesMatch).filter(
                FeaturesMatch.match_id == match_id
            ).first()
            
            if features_record:
                features = features_record.feature_json
                features['match_id'] = match_id
                features_data.append(features)
        
        return pd.DataFrame(features_data)


class ModelRetrainer:
    """Retrain model with new data including prediction errors"""
    
    def __init__(self, db: Session):
        self.db = db
        self.error_analyzer = PredictionErrorAnalyzer(db)
    
    def prepare_retraining_data(self, 
                               original_seasons: List[int],
                               new_matches_days_back: int = 30) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Prepare data for retraining including new finished matches"""
        
        # Get original training data
        from ml.training.dataset import prepare_training_data
        original_train_df, original_valid_df = prepare_training_data(original_seasons, 2024)
        
        # Get new finished matches with predictions
        new_matches_df = self.error_analyzer.get_finished_matches_with_predictions(
            days_back=new_matches_days_back
        )
        
        if new_matches_df.empty:
            print("No new finished matches found for retraining")
            return original_train_df, original_valid_df
        
        # Get features for new matches
        new_features_df = self.error_analyzer.get_features_for_finished_matches(
            new_matches_df['match_id'].tolist()
        )
        
        if new_features_df.empty:
            print("No features found for new matches")
            return original_train_df, original_valid_df
        
        # Merge new matches with their features
        new_data = new_matches_df.merge(new_features_df, on='match_id', how='inner')
        
        # Add new data to training set
        combined_train_df = pd.concat([original_train_df, new_data], ignore_index=True)
        
        print(f"Original training data: {len(original_train_df)} matches")
        print(f"New finished matches: {len(new_data)} matches")
        print(f"Combined training data: {len(combined_train_df)} matches")
        
        return combined_train_df, original_valid_df
    
    def retrain_model(self, 
                     algorithm: str = "xgb",
                     original_seasons: List[int] = None,
                     new_matches_days_back: int = 30,
                     error_weighting: bool = True) -> Dict:
        """Retrain model with new data and optional error weighting"""
        
        if original_seasons is None:
            original_seasons = [2020, 2021, 2022, 2023]
        
        print(f"Retraining {algorithm.upper()} model with new data...")
        
        # Prepare retraining data
        train_df, valid_df = self.prepare_retraining_data(original_seasons, new_matches_days_back)
        
        if train_df.empty:
            return {"error": "No training data available"}
        
        # Prepare features and labels
        X_train, scaler = prepare_features(train_df)
        X_val, _ = prepare_features(valid_df, scaler)
        y_train = prepare_labels(train_df, one_hot=False)
        y_val = prepare_labels(valid_df, one_hot=False)
        
        # Apply error weighting if requested
        if error_weighting and 'log_loss_error' in train_df.columns:
            # Give higher weight to matches where we made bigger errors
            sample_weights = 1 + train_df['log_loss_error'].fillna(0)
            print(f"Applied error weighting to {len(sample_weights)} samples")
        else:
            sample_weights = None
        
        # Train model
        if algorithm.lower() == "xgb":
            results = self._train_xgboost_with_weights(X_train, y_train, X_val, y_val, sample_weights)
        elif algorithm.lower() == "rf":
            results = self._train_random_forest_with_weights(X_train, y_train, X_val, y_val, sample_weights)
        elif algorithm.lower() == "lr":
            results = self._train_logistic_regression_with_weights(X_train, y_train, X_val, y_val, sample_weights)
        else:
            return {"error": f"Unknown algorithm: {algorithm}"}
        
        # Save retrained model
        self._save_retrained_model(results, scaler, algorithm, train_df, valid_df)
        
        return {
            "success": True,
            "algorithm": algorithm,
            "original_samples": len(train_df) - len(train_df[train_df['log_loss_error'].notna()]),
            "new_samples": len(train_df[train_df['log_loss_error'].notna()]),
            "metrics": {
                "train_accuracy": results['train_accuracy'],
                "val_accuracy": results['val_accuracy'],
                "train_logloss": results['train_logloss'],
                "val_logloss": results['val_logloss']
            }
        }
    
    def _train_xgboost_with_weights(self, X_train, y_train, X_val, y_val, sample_weights):
        """Train XGBoost with sample weights"""
        import xgboost as xgb
        
        model = xgb.XGBClassifier(
            n_estimators=100,
            max_depth=6,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=settings.random_seed,
            eval_metric='mlogloss',
            early_stopping_rounds=10
        )
        
        if sample_weights is not None:
            model.fit(X_train, y_train, sample_weight=sample_weights, eval_set=[(X_val, y_val)], verbose=False)
        else:
            model.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=False)
        
        return self._evaluate_model(model, X_train, y_train, X_val, y_val)
    
    def _train_random_forest_with_weights(self, X_train, y_train, X_val, y_val, sample_weights):
        """Train Random Forest with sample weights"""
        from sklearn.ensemble import RandomForestClassifier
        
        model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=settings.random_seed
        )
        
        if sample_weights is not None:
            model.fit(X_train, y_train, sample_weight=sample_weights)
        else:
            model.fit(X_train, y_train)
        
        return self._evaluate_model(model, X_train, y_train, X_val, y_val)
    
    def _train_logistic_regression_with_weights(self, X_train, y_train, X_val, y_val, sample_weights):
        """Train Logistic Regression with sample weights"""
        from sklearn.linear_model import LogisticRegression
        
        model = LogisticRegression(
            multi_class='multinomial',
            solver='lbfgs',
            max_iter=1000,
            random_state=settings.random_seed
        )
        
        if sample_weights is not None:
            model.fit(X_train, y_train, sample_weight=sample_weights)
        else:
            model.fit(X_train, y_train)
        
        return self._evaluate_model(model, X_train, y_train, X_val, y_val)
    
    def _evaluate_model(self, model, X_train, y_train, X_val, y_val):
        """Evaluate model performance"""
        from sklearn.metrics import accuracy_score, log_loss
        
        train_pred = model.predict(X_train)
        val_pred = model.predict(X_val)
        
        train_acc = accuracy_score(y_train, train_pred)
        val_acc = accuracy_score(y_val, val_pred)
        
        train_proba = model.predict_proba(X_train)
        val_proba = model.predict_proba(X_val)
        
        train_logloss = log_loss(y_train, train_proba)
        val_logloss = log_loss(y_val, val_proba)
        
        return {
            'model': model,
            'train_accuracy': train_acc,
            'val_accuracy': val_acc,
            'train_logloss': train_logloss,
            'val_logloss': val_logloss
        }
    
    def _save_retrained_model(self, results, scaler, algorithm, train_df, valid_df):
        """Save the retrained model"""
        import json
        from datetime import datetime
        
        os.makedirs(settings.model_dir, exist_ok=True)
        
        # Save model
        model_path = os.path.join(settings.model_dir, "model.pkl")
        joblib.dump(results['model'], model_path)
        
        # Save scaler
        scaler_path = os.path.join(settings.model_dir, "scaler.pkl")
        joblib.dump(scaler, scaler_path)
        
        # Update metadata
        model_version = f"{algorithm}_retrained_{datetime.now().strftime('%Y-%m-%d_%H%M')}"
        
        metadata = {
            'model_version': model_version,
            'algorithm': algorithm,
            'retrained_at': datetime.now().isoformat(),
            'retraining_reason': 'learning_from_mistakes',
            'train_samples': len(train_df),
            'valid_samples': len(valid_df),
            'metrics': {
                'train_accuracy': results['train_accuracy'],
                'val_accuracy': results['val_accuracy'],
                'train_logloss': results['train_logloss'],
                'val_logloss': results['val_logloss']
            }
        }
        
        metadata_path = os.path.join(settings.model_dir, "metadata.json")
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2, default=str)
        
        print(f"Retrained model saved as version: {model_version}")


def analyze_recent_predictions(days_back: int = 7) -> Dict:
    """Analyze recent prediction performance"""
    db = next(get_db())
    analyzer = PredictionErrorAnalyzer(db)
    
    df = analyzer.get_finished_matches_with_predictions(days_back=days_back)
    analysis = analyzer.analyze_prediction_errors(df)
    
    return analysis


def retrain_with_new_data(algorithm: str = "xgb", days_back: int = 30) -> Dict:
    """Retrain model with new finished matches"""
    db = next(get_db())
    retrainer = ModelRetrainer(db)
    
    return retrainer.retrain_model(algorithm=algorithm, new_matches_days_back=days_back)


if __name__ == "__main__":
    # Example usage
    print("Analyzing recent prediction errors...")
    analysis = analyze_recent_predictions(days_back=7)
    print(analysis)
    
    print("\nRetraining model with new data...")
    result = retrain_with_new_data(algorithm="xgb", days_back=30)
    print(result)
