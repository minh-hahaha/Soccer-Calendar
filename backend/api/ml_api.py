from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import joblib
import os
import json
import pandas as pd
import numpy as np
from datetime import datetime

from database.db import get_db
from database.models import Match, FeaturesMatch, Prediction
from database.schemas import (
    PredictionResponse, BatchPredictionResponse, FeaturesResponse, 
    HealthResponse, TopFeature
)
from ml.features.build import get_features_for_match
from ml.training.dataset import prepare_features, get_feature_columns
from config import settings

router = APIRouter()

# Global variables for loaded model
model = None
scaler = None
metadata = None


def load_model():
    """Load the trained model and scaler"""
    global model, scaler, metadata
    
    if model is None:
        model_path = os.path.join(settings.model_dir, "model.pkl")
        scaler_path = os.path.join(settings.model_dir, "scaler.pkl")
        metadata_path = os.path.join(settings.model_dir, "metadata.json")
        
        if not os.path.exists(model_path):
            raise HTTPException(status_code=500, detail="Model not found. Please train a model first.")
        
        model = joblib.load(model_path)
        scaler = joblib.load(scaler_path)
        
        if os.path.exists(metadata_path):
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)


def get_top_features(features: dict, model_version: str) -> List[TopFeature]:
    """Get top contributing features for prediction"""
    # This is a simplified feature contribution calculation
    # In a real implementation, you'd use SHAP or similar methods
    
    feature_cols = get_feature_columns()
    top_features = []
    
    # Simple heuristic: use feature values as contributions
    for col in feature_cols:
        if col in features:
            value = features[col]
            # Normalize contribution to reasonable range
            contribution = max(-0.3, min(0.3, value * 0.1))
            top_features.append(TopFeature(name=col, contribution=round(contribution, 3)))
    
    # Sort by absolute contribution and take top 5
    top_features.sort(key=lambda x: abs(x.contribution), reverse=True)
    return top_features[:5]


@router.get("/health", response_model=HealthResponse)
def health_check():
    """Health check endpoint"""
    try:
        load_model()
        return HealthResponse(
            status="healthy",
            model_version=metadata.get('model_version') if metadata else None,
            database_connected=True
        )
    except Exception as e:
        return HealthResponse(
            status="unhealthy",
            model_version=None,
            database_connected=False
        )


@router.get("/predict", response_model=PredictionResponse)
def predict_match(
    match_id: int = Query(..., description="Match ID to predict"),
    db: Session = Depends(get_db)
):
    """Predict match outcome"""
    try:
        load_model()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    # Get match
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail=f"Match {match_id} not found")
    
    # Check if match is finished
    if match.status == "FINISHED":
        raise HTTPException(status_code=400, detail="Cannot predict finished matches")
    
    # Get or build features
    try:
        features = get_features_for_match(db, match_id)
    except Exception as e:
        import traceback
        # Log to file for debugging
        with open('/tmp/ml_api_error.log', 'w') as f:
            f.write(f"Error: {str(e)}\n")
            f.write(f"Traceback: {traceback.format_exc()}\n")
        raise HTTPException(status_code=422, detail=f"Insufficient history for prediction: {str(e)}")
    
    # Prepare features for prediction
    feature_cols = get_feature_columns()
    feature_values = []
    
    for col in feature_cols:
        value = features.get(col, 0.0)
        if pd.isna(value):
            value = 0.0
        feature_values.append(value)
    
    X = np.array([feature_values])
    X_scaled = scaler.transform(X)
    
    # Make prediction
    probabilities = model.predict_proba(X_scaled)[0]
    
    # Format probabilities
    probs = {
        "away": float(probabilities[0]),
        "draw": float(probabilities[1]),
        "home": float(probabilities[2])
    }
    
    # Get top features
    top_features = get_top_features(features, metadata.get('model_version', 'unknown'))
    
    # Save prediction to database
    prediction_record = Prediction(
        match_id=match_id,
        p_home=probs["home"],
        p_draw=probs["draw"],
        p_away=probs["away"],
        model_version=metadata.get('model_version', 'unknown'),
        calibrated=False
    )
    
    # Check if prediction already exists
    existing = db.query(Prediction).filter(Prediction.match_id == match_id).first()
    if existing:
        existing.p_home = probs["home"]
        existing.p_draw = probs["draw"]
        existing.p_away = probs["away"]
        existing.model_version = metadata.get('model_version', 'unknown')
    else:
        db.add(prediction_record)
    
    db.commit()
    
    return PredictionResponse(
        match_id=match_id,
        competition=settings.competition_code,
        kickoff=match.utc_date,
        home_team_id=match.home_team_id,
        away_team_id=match.away_team_id,
        probs=probs,
        top_features=top_features,
        model_version=metadata.get('model_version', 'unknown'),
        calibrated=False,
        data_quality=features.get('data_quality')
    )


@router.post("/batch/predict", response_model=BatchPredictionResponse)
def batch_predict_matches(
    match_ids: List[int],
    db: Session = Depends(get_db)
):
    """Predict multiple matches"""
    try:
        global model, scaler, metadata
        model, scaler, metadata = load_model()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    predictions = []
    
    for match_id in match_ids:
        try:
            # Get match
            match = db.query(Match).filter(Match.id == match_id).first()
            if not match:
                continue
            
            # Check if match is finished
            if match.status == "FINISHED":
                continue
            
            # Get features
            try:
                features = get_features_for_match(db, match_id)
            except:
                continue
            
            # Prepare features
            feature_cols = get_feature_columns()
            feature_values = []
            
            for col in feature_cols:
                value = features.get(col, 0.0)
                if pd.isna(value):
                    value = 0.0
                feature_values.append(value)
            
            X = np.array([feature_values])
            X_scaled = scaler.transform(X)
            
            # Make prediction
            probabilities = model.predict_proba(X_scaled)[0]
            
            probs = {
                "away": float(probabilities[0]),
                "draw": float(probabilities[1]),
                "home": float(probabilities[2])
            }
            
            # Get top features
            top_features = get_top_features(features, metadata.get('model_version', 'unknown'))
            
            prediction = PredictionResponse(
                match_id=match_id,
                competition=settings.competition_code,
                kickoff=match.utc_date,
                home_team_id=match.home_team_id,
                away_team_id=match.away_team_id,
                probs=probs,
                top_features=top_features,
                model_version=metadata.get('model_version', 'unknown'),
                calibrated=False,
                data_quality=features.get('data_quality')
            )
            
            predictions.append(prediction)
            
        except Exception as e:
            print(f"Error predicting match {match_id}: {e}")
            continue
    
    return BatchPredictionResponse(predictions=predictions)


@router.get("/features", response_model=FeaturesResponse)
def get_match_features(
    match_id: int = Query(..., description="Match ID to get features for"),
    db: Session = Depends(get_db)
):
    """Get features for a match (debug endpoint)"""
    # Get match
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail=f"Match {match_id} not found")
    
    # Get features
    try:
        features = get_features_for_match(db, match_id)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Error getting features: {str(e)}")
    
    # Get features record for built_at timestamp
    features_record = db.query(FeaturesMatch).filter(FeaturesMatch.match_id == match_id).first()
    built_at = features_record.built_at if features_record else datetime.now()
    
    return FeaturesResponse(
        match_id=match_id,
        features=features,
        built_at=built_at
    )
