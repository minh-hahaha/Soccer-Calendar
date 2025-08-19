import typer
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from typing import List, Optional
import joblib
import os
from datetime import datetime

from backend.config import settings
from backend.ml.training.dataset import prepare_training_data, prepare_features, prepare_labels
from backend.ml.evaluation.metrics import calculate_multiclass_metrics, format_metrics_report

app = typer.Typer()


@app.command()
def report(seasons: str = typer.Option("2020,2021,2022,2023,2024", help="Seasons to evaluate")):
    """Generate comprehensive model evaluation report"""
    
    # Parse seasons
    season_list = [int(s.strip()) for s in seasons.split(",")]
    
    print("=" * 60)
    print("FOOTBALL MATCH PREDICTION MODEL EVALUATION")
    print("=" * 60)
    print(f"Evaluation seasons: {season_list}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Load model and metadata
    model_path = os.path.join(settings.model_dir, "model.pkl")
    metadata_path = os.path.join(settings.model_dir, "metadata.json")
    
    if not os.path.exists(model_path):
        print("❌ Model not found. Please train a model first.")
        return
    
    model = joblib.load(model_path)
    
    if os.path.exists(metadata_path):
        import json
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        print(f"Model: {metadata.get('model_version', 'Unknown')}")
        print(f"Algorithm: {metadata.get('algorithm', 'Unknown')}")
        print()
    
    # Prepare evaluation data
    print("📊 Preparing evaluation data...")
    try:
        train_df, valid_df = prepare_training_data(season_list)
        
        if valid_df.empty:
            print("❌ No validation data available")
            return
        
        print(f"Validation set size: {len(valid_df)} matches")
        print()
        
    except Exception as e:
        print(f"❌ Error preparing data: {e}")
        return
    
    # Prepare features and labels
    X_val, scaler = prepare_features(valid_df)
    y_val = prepare_labels(valid_df, one_hot=False)
    y_val_one_hot = prepare_labels(valid_df, one_hot=True)
    
    # Make predictions
    print("🔮 Making predictions...")
    y_pred = model.predict(X_val)
    y_pred_proba = model.predict_proba(X_val)
    
    # Calculate metrics
    print("📈 Calculating metrics...")
    metrics = calculate_multiclass_metrics(y_val, y_pred, y_pred_proba)
    
    # Print report
    print(format_metrics_report(metrics))
    
    # Additional analysis
    print("\n" + "=" * 60)
    print("ADDITIONAL ANALYSIS")
    print("=" * 60)
    
    # Class distribution
    print("\n📊 Class Distribution:")
    class_counts = pd.Series(y_val).value_counts().sort_index()
    class_names = ['Away Win', 'Draw', 'Home Win']
    for i, (class_idx, count) in enumerate(class_counts.items()):
        percentage = (count / len(y_val)) * 100
        print(f"  {class_names[class_idx]}: {count} ({percentage:.1f}%)")
    
    # Prediction distribution
    print("\n🎯 Prediction Distribution:")
    pred_counts = pd.Series(y_pred).value_counts().sort_index()
    for i, (class_idx, count) in enumerate(pred_counts.items()):
        percentage = (count / len(y_pred)) * 100
        print(f"  {class_names[class_idx]}: {count} ({percentage:.1f}%)")
    
    # Confidence analysis
    print("\n🎲 Confidence Analysis:")
    max_probs = np.max(y_pred_proba, axis=1)
    print(f"  Average confidence: {np.mean(max_probs):.3f}")
    print(f"  Median confidence: {np.median(max_probs):.3f}")
    print(f"  Std confidence: {np.std(max_probs):.3f}")
    
    # High confidence predictions
    high_conf_threshold = 0.7
    high_conf_mask = max_probs >= high_conf_threshold
    high_conf_count = np.sum(high_conf_mask)
    high_conf_accuracy = np.mean(y_val[high_conf_mask] == y_pred[high_conf_mask])
    
    print(f"  High confidence predictions (≥{high_conf_threshold}): {high_conf_count} ({high_conf_count/len(y_pred)*100:.1f}%)")
    print(f"  High confidence accuracy: {high_conf_accuracy:.3f}")
    
    # Feature importance (if available)
    if hasattr(model, 'feature_importances_'):
        print("\n🔍 Top 10 Feature Importance:")
        feature_names = [
            'diff_form_ppg', 'diff_goals_for_per_match', 'diff_goals_against_per_match',
            'diff_goal_diff_per_match', 'diff_rest_days', 'diff_position', 'diff_points',
            'diff_goal_diff', 'diff_rank_delta', 'diff_table_strength', 'h2h_wins',
            'h2h_draws', 'h2h_losses', 'h2h_goal_diff', 'h2h_avg_goals', 'h2h_win_rate',
            'h2h_home_venue_win_rate', 'home_flag', 'same_city'
        ]
        
        importances = model.feature_importances_
        feature_importance = list(zip(feature_names, importances))
        feature_importance.sort(key=lambda x: x[1], reverse=True)
        
        for name, importance in feature_importance[:10]:
            print(f"  {name}: {importance:.4f}")
    
    print("\n✅ Evaluation complete!")


@app.command()
def compare_models():
    """Compare different model algorithms"""
    
    algorithms = ['lr', 'rf', 'xgb']
    results = {}
    
    print("🔄 Comparing model algorithms...")
    print()
    
    for algo in algorithms:
        model_path = os.path.join(settings.model_dir, f"model_{algo}.pkl")
        
        if not os.path.exists(model_path):
            print(f"⚠️  Model for {algo.upper()} not found, skipping...")
            continue
        
        print(f"📊 Evaluating {algo.upper()}...")
        
        try:
            # Load model
            model = joblib.load(model_path)
            
            # Prepare data
            train_df, valid_df = prepare_training_data([2024])
            
            if valid_df.empty:
                print(f"❌ No validation data for {algo.upper()}")
                continue
            
            # Prepare features and labels
            X_val, scaler = prepare_features(valid_df)
            y_val = prepare_labels(valid_df, one_hot=False)
            y_val_one_hot = prepare_labels(valid_df, one_hot=True)
            
            # Make predictions
            y_pred = model.predict(X_val)
            y_pred_proba = model.predict_proba(X_val)
            
            # Calculate metrics
            metrics = calculate_multiclass_metrics(y_val, y_pred, y_pred_proba)
            
            results[algo] = {
                'accuracy': metrics['accuracy'],
                'logloss': metrics['logloss'],
                'brier_score': metrics['brier_score'],
                'macro_f1': metrics['macro_f1']
            }
            
            print(f"  Accuracy: {metrics['accuracy']:.4f}")
            print(f"  Log Loss: {metrics['logloss']:.4f}")
            print(f"  Brier Score: {metrics['brier_score']:.4f}")
            print(f"  Macro F1: {metrics['macro_f1']:.4f}")
            print()
            
        except Exception as e:
            print(f"❌ Error evaluating {algo.upper()}: {e}")
            print()
    
    # Summary table
    if results:
        print("📋 Model Comparison Summary:")
        print("-" * 80)
        print(f"{'Algorithm':<10} {'Accuracy':<10} {'Log Loss':<10} {'Brier':<10} {'Macro F1':<10}")
        print("-" * 80)
        
        for algo, metrics in results.items():
            print(f"{algo.upper():<10} {metrics['accuracy']:<10.4f} {metrics['logloss']:<10.4f} "
                  f"{metrics['brier_score']:<10.4f} {metrics['macro_f1']:<10.4f}")
        
        print("-" * 80)
        
        # Find best model
        best_algo = min(results.keys(), key=lambda x: results[x]['logloss'])
        print(f"\n🏆 Best model (lowest log loss): {best_algo.upper()}")
    
    print("\n✅ Model comparison complete!")


if __name__ == "__main__":
    app()
