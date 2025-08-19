import typer
import joblib
import os
from datetime import datetime
from typing import Dict, Any, Optional
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, log_loss
import xgboost as xgb
from config import settings
from ml.training.dataset import prepare_training_data, prepare_features, prepare_labels, create_sample_dataset
from ml.evaluation.metrics import calculate_brier_score
import warnings
warnings.filterwarnings('ignore')

app = typer.Typer()


def train_logistic_regression(X_train: np.ndarray, y_train: np.ndarray, 
                            X_val: np.ndarray, y_val: np.ndarray) -> Dict[str, Any]:
    """Train logistic regression model"""
    print("Training Logistic Regression...")
    
    model = LogisticRegression(
        multi_class='multinomial',
        solver='lbfgs',
        max_iter=1000,
        random_state=settings.random_seed
    )
    
    model.fit(X_train, y_train)
    
    # Evaluate
    train_pred = model.predict(X_train)
    val_pred = model.predict(X_val)
    
    train_acc = accuracy_score(y_train, train_pred)
    val_acc = accuracy_score(y_val, val_pred)
    
    train_proba = model.predict_proba(X_train)
    val_proba = model.predict_proba(X_val)
    
    train_logloss = log_loss(y_train, train_proba)
    val_logloss = log_loss(y_val, val_proba)
    
    train_brier = calculate_brier_score(y_train, train_proba)
    val_brier = calculate_brier_score(y_val, val_proba)
    
    return {
        'model': model,
        'train_accuracy': train_acc,
        'val_accuracy': val_acc,
        'train_logloss': train_logloss,
        'val_logloss': val_logloss,
        'train_brier': train_brier,
        'val_brier': val_brier
    }


def train_random_forest(X_train: np.ndarray, y_train: np.ndarray, 
                       X_val: np.ndarray, y_val: np.ndarray) -> Dict[str, Any]:
    """Train random forest model"""
    print("Training Random Forest...")
    
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=settings.random_seed
    )
    
    model.fit(X_train, y_train)
    
    # Evaluate
    train_pred = model.predict(X_train)
    val_pred = model.predict(X_val)
    
    train_acc = accuracy_score(y_train, train_pred)
    val_acc = accuracy_score(y_val, val_pred)
    
    train_proba = model.predict_proba(X_train)
    val_proba = model.predict_proba(X_val)
    
    train_logloss = log_loss(y_train, train_proba)
    val_logloss = log_loss(y_val, val_proba)
    
    train_brier = calculate_brier_score(y_train, train_proba)
    val_brier = calculate_brier_score(y_val, val_proba)
    
    return {
        'model': model,
        'train_accuracy': train_acc,
        'val_accuracy': val_acc,
        'train_logloss': train_logloss,
        'val_logloss': val_logloss,
        'train_brier': train_brier,
        'val_brier': val_brier
    }


def train_xgboost(X_train: np.ndarray, y_train: np.ndarray, 
                  X_val: np.ndarray, y_val: np.ndarray) -> Dict[str, Any]:
    """Train XGBoost model"""
    print("Training XGBoost...")
    
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
    
    model.fit(
        X_train, y_train,
        eval_set=[(X_val, y_val)],
        verbose=False
    )
    
    # Evaluate
    train_pred = model.predict(X_train)
    val_pred = model.predict(X_val)
    
    train_acc = accuracy_score(y_train, train_pred)
    val_acc = accuracy_score(y_val, val_pred)
    
    train_proba = model.predict_proba(X_train)
    val_proba = model.predict_proba(X_val)
    
    train_logloss = log_loss(y_train, train_proba)
    val_logloss = log_loss(y_val, val_proba)
    
    train_brier = calculate_brier_score(y_train, train_proba)
    val_brier = calculate_brier_score(y_val, val_proba)
    
    return {
        'model': model,
        'train_accuracy': train_acc,
        'val_accuracy': val_acc,
        'train_logloss': train_logloss,
        'val_logloss': val_logloss,
        'train_brier': train_brier,
        'val_brier': val_brier
    }


def get_feature_importance(model, feature_names: list) -> list:
    """Get feature importance from model"""
    if hasattr(model, 'feature_importances_'):
        # Tree-based models
        importances = model.feature_importances_
    elif hasattr(model, 'coef_'):
        # Linear models
        importances = np.abs(model.coef_).mean(axis=0)
    else:
        return []
    
    # Sort by importance
    feature_importance = list(zip(feature_names, importances))
    feature_importance.sort(key=lambda x: x[1], reverse=True)
    
    return feature_importance


@app.command()
def fit(algo: str = typer.Option("xgb", help="Algorithm: lr, rf, xgb"),
        seasons: str = typer.Option("2020,2021,2022,2023", help="Training seasons"),
        valid: int = typer.Option(2024, help="Validation season"),
        use_sample: bool = typer.Option(False, help="Use sample dataset")):
    """Train a prediction model"""
    
    # Parse seasons
    train_seasons = [int(s.strip()) for s in seasons.split(",")]
    
    print(f"Training {algo.upper()} model...")
    print(f"Training seasons: {train_seasons}")
    print(f"Validation season: {valid}")
    
    # Prepare data
    if use_sample:
        print("Using sample dataset...")
        train_df, valid_df = create_sample_dataset()
    else:
        print("Preparing real dataset...")
        train_df, valid_df = prepare_training_data(train_seasons, valid)
    
    if train_df.empty or valid_df.empty:
        print("No data available for training")
        return
    
    # Prepare features
    X_train, scaler = prepare_features(train_df)
    X_val, _ = prepare_features(valid_df, scaler)
    
    # Prepare labels
    y_train = prepare_labels(train_df, one_hot=False)
    y_val = prepare_labels(valid_df, one_hot=False)
    
    print(f"Training features shape: {X_train.shape}")
    print(f"Validation features shape: {X_val.shape}")
    
    # Train model
    if algo.lower() == "lr":
        results = train_logistic_regression(X_train, y_train, X_val, y_val)
    elif algo.lower() == "rf":
        results = train_random_forest(X_train, y_train, X_val, y_val)
    elif algo.lower() == "xgb":
        results = train_xgboost(X_train, y_train, X_val, y_val)
    else:
        print(f"Unknown algorithm: {algo}")
        return
    
    # Print results
    print("\nTraining Results:")
    print(f"Train Accuracy: {results['train_accuracy']:.4f}")
    print(f"Val Accuracy: {results['val_accuracy']:.4f}")
    print(f"Train LogLoss: {results['train_logloss']:.4f}")
    print(f"Val LogLoss: {results['val_logloss']:.4f}")
    print(f"Train Brier Score: {results['train_brier']:.4f}")
    print(f"Val Brier Score: {results['val_brier']:.4f}")
    
    # Get feature importance using prioritized feature names
    from ml.features.prioritized_features import get_prioritized_feature_columns
    feature_names = get_prioritized_feature_columns()
    
    feature_importance = get_feature_importance(results['model'], feature_names)
    
    print("\nTop 10 Feature Importance:")
    for name, importance in feature_importance[:10]:
        print(f"{name}: {importance:.4f}")
    
    # Save model and scaler
    os.makedirs(settings.model_dir, exist_ok=True)
    
    model_version = f"{algo}_{datetime.now().strftime('%Y-%m-%d')}"
    
    # Save model
    model_path = os.path.join(settings.model_dir, "model.pkl")
    joblib.dump(results['model'], model_path)
    
    # Save scaler
    scaler_path = os.path.join(settings.model_dir, "scaler.pkl")
    joblib.dump(scaler, scaler_path)
    
    # Save metadata
    metadata = {
        'model_version': model_version,
        'algorithm': algo,
        'train_seasons': train_seasons,
        'valid_season': valid,
        'train_samples': len(train_df),
        'valid_samples': len(valid_df),
        'feature_names': feature_names,
        'feature_importance': feature_importance,
        'metrics': {
            'train_accuracy': results['train_accuracy'],
            'val_accuracy': results['val_accuracy'],
            'train_logloss': results['train_logloss'],
            'val_logloss': results['val_logloss'],
            'train_brier': results['train_brier'],
            'val_brier': results['val_brier']
        },
        'trained_at': datetime.now().isoformat()
    }
    
    metadata_path = os.path.join(settings.model_dir, "metadata.json")
    import json
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2, default=str)
    
    print(f"\nModel saved to {model_path}")
    print(f"Scaler saved to {scaler_path}")
    print(f"Metadata saved to {metadata_path}")
    print(f"Model version: {model_version}")


if __name__ == "__main__":
    app()
