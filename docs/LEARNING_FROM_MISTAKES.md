# Learning from Mistakes: Model Improvement Guide

This guide explains how to use the learning from mistakes functionality to improve your prediction model's performance over time.

## Overview

The system automatically tracks prediction errors and provides tools to:
- Analyze prediction performance
- Retrain models with new data
- Learn from prediction mistakes
- Continuously improve accuracy

## Quick Start

### 1. Analyze Recent Predictions

```bash
# Analyze predictions from the last 7 days
make learn-analyze

# Analyze specific matchday
make analyze-matchday

# Analyze current season
make analyze-season
```

### 2. Retrain Model with New Data

```bash
# Retrain with matches from last 30 days
make learn-retrain

# Compare old vs new performance
make learn-compare
```

### 3. Monitor Performance Continuously

```bash
# Monitor every 24 hours with auto-retraining
make learn-monitor
```

## CLI Commands

### Analysis Commands

```bash
# Basic analysis
python -m backend.ml.training.learn analyze --days-back 7

# Analyze specific matchday
python -m backend.ml.training.learn analyze --matchday 1

# Analyze specific season
python -m backend.ml.training.learn analyze --season 2024

# Save analysis to file
python -m backend.ml.training.learn analyze --output-file analysis.json
```

### Retraining Commands

```bash
# Retrain with XGBoost (default)
python -m backend.ml.training.learn retrain --algorithm xgb --days-back 30

# Retrain with Random Forest
python -m backend.ml.training.learn retrain --algorithm rf --days-back 30

# Retrain without error weighting
python -m backend.ml.training.learn retrain --error-weighting false

# Force retraining even with no new data
python -m backend.ml.training.learn retrain --force
```

### Comparison Commands

```bash
# Compare old vs new model performance
python -m backend.ml.training.learn compare --days-back 7 --algorithm xgb
```

### Monitoring Commands

```bash
# Monitor every 12 hours
python -m backend.ml.training.learn monitor --interval-hours 12

# Monitor with auto-retraining when accuracy drops below 40%
python -m backend.ml.training.learn monitor --auto-retrain --min-matches 5
```

## API Endpoints

### Get Prediction Analysis

```http
GET /ml/analysis?days_back=7&season=2024&matchday=1
```

Response:
```json
{
  "total_matches": 10,
  "overall_accuracy": 0.6,
  "average_log_loss": 0.6931,
  "error_distribution": {
    "correct_predictions": 6,
    "incorrect_predictions": 4
  },
  "outcome_analysis": {
    "home_wins": 4,
    "draws": 2,
    "away_wins": 4
  },
  "confidence_analysis": {
    "high_confidence_errors": 2,
    "low_confidence_correct": 1,
    "average_confidence": 0.45
  },
  "worst_predictions": [...],
  "best_predictions": [...]
}
```

### Retrain Model

```http
POST /ml/retrain?algorithm=xgb&days_back=30&error_weighting=true
```

Response:
```json
{
  "success": true,
  "algorithm": "xgb",
  "original_samples": 1000,
  "new_samples": 10,
  "metrics": {
    "train_accuracy": 0.65,
    "val_accuracy": 0.62,
    "train_logloss": 0.68,
    "val_logloss": 0.71
  }
}
```

### Compare Models

```http
GET /ml/compare?days_back=7&algorithm=xgb
```

Response:
```json
{
  "current_performance": {...},
  "new_performance": {...},
  "improvement": {
    "accuracy_improvement": 0.05,
    "logloss_improvement": 0.02
  }
}
```

## How It Works

### 1. Error Tracking

The system automatically tracks:
- **Prediction errors**: When predictions are wrong
- **Log loss**: How confident the model was in wrong predictions
- **Confidence analysis**: High confidence errors vs low confidence correct predictions
- **Outcome distribution**: Actual vs predicted results

### 2. Error Weighting

When retraining, the system can apply **error weighting**:
- Matches where the model made bigger mistakes get higher weight
- This focuses the model on learning from its worst predictions
- Formula: `sample_weight = 1 + log_loss_error`

### 3. Continuous Learning

The system supports:
- **Incremental learning**: Add new data without retraining from scratch
- **Performance monitoring**: Track accuracy over time
- **Auto-retraining**: Automatically retrain when performance drops
- **Model versioning**: Keep track of model improvements

## Best Practices

### 1. Regular Analysis

```bash
# Check performance weekly
make learn-analyze

# Analyze after each matchday
python -m backend.ml.training.learn analyze --matchday 1
```

### 2. Strategic Retraining

```bash
# Retrain after accumulating 10+ new matches
python -m backend.ml.training.learn retrain --days-back 30

# Use error weighting for better learning
python -m backend.ml.training.learn retrain --error-weighting true
```

### 3. Performance Monitoring

```bash
# Monitor daily during active season
python -m backend.ml.training.learn monitor --interval-hours 24 --auto-retrain
```

### 4. Model Comparison

```bash
# Compare before and after retraining
python -m backend.ml.training.learn compare --days-back 7
```

## Understanding the Metrics

### Accuracy
- **Overall accuracy**: Percentage of correct predictions
- **Target**: >50% for 3-way classification (home/draw/away)

### Log Loss
- **Log loss**: Measures prediction confidence and accuracy
- **Lower is better**: 0.693 is random guessing
- **Target**: <0.7 for good performance

### Confidence Analysis
- **High confidence errors**: Model was very sure but wrong
- **Low confidence correct**: Model was unsure but right
- **Average confidence**: Overall prediction confidence

### Error Distribution
- **Correct predictions**: Where model got it right
- **Incorrect predictions**: Where model made mistakes
- **Outcome analysis**: Distribution of actual results

## Troubleshooting

### No Data for Analysis
```bash
# Check if matches have finished and have predictions
python -m backend.ml.training.learn analyze --days-back 30
```

### Retraining Fails
```bash
# Check for sufficient data
python -m backend.ml.training.learn retrain --force

# Check error logs
tail -f /tmp/ml_api_error.log
```

### Poor Performance
```bash
# Analyze specific issues
python -m backend.ml.training.learn analyze --output-file debug.json

# Retrain with more data
python -m backend.ml.training.learn retrain --days-back 60
```

## Advanced Features

### Custom Error Weighting
```python
# In your own scripts
from ml.evaluation.learn_from_mistakes import ModelRetrainer

retrainer = ModelRetrainer(db)
result = retrainer.retrain_model(
    algorithm="xgb",
    error_weighting=True,
    custom_weights=your_custom_weights
)
```

### Batch Analysis
```python
# Analyze multiple time periods
for matchday in range(1, 6):
    analysis = analyze_recent_predictions(matchday=matchday)
    print(f"Matchday {matchday}: {analysis['overall_accuracy']:.2%}")
```

### Performance Tracking
```python
# Track performance over time
import json
from datetime import datetime

analysis = analyze_recent_predictions(days_back=7)
tracking_data = {
    "date": datetime.now().isoformat(),
    "accuracy": analysis['overall_accuracy'],
    "log_loss": analysis['average_log_loss']
}

with open("performance_tracking.json", "a") as f:
    f.write(json.dumps(tracking_data) + "\n")
```

## Integration with Frontend

The frontend includes a `PredictionAnalysis` component that provides:
- Real-time analysis display
- One-click model retraining
- Visual performance metrics
- Error breakdown charts

To use in your React app:
```tsx
import PredictionAnalysis from './components/PredictionAnalysis';

<PredictionAnalysis 
  daysBack={7} 
  season={2024} 
  matchday={1} 
/>
```

This creates a comprehensive system for continuously improving your prediction model by learning from its mistakes!
