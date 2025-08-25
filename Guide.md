# AI Fantasy Football Agent - Setup & Usage Guide

## Overview

This AI-powered Fantasy Football agent replaces your rule-based system with machine learning models trained on historical player data (2016-2025). It provides intelligent predictions for player points, transfer recommendations, captain suggestions, and market analysis.

## Key Features

🤖 **AI-Powered Predictions**: ML models predict player points, goals, assists, and clean sheets
📊 **Smart Transfer Recommendations**: AI suggests optimal transfers based on predicted performance
🎯 **Captain Analysis**: Intelligent captain picks with confidence scores
💰 **Market Intelligence**: Identify undervalued and overvalued players
📈 **Risk Assessment**: Built-in risk scoring for all recommendations
🔮 **Multi-gameweek Planning**: Forward-looking fixture analysis

## Requirements

### Python Dependencies

Create a `requirements.txt` file:

```text
# Core framework
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0

# Database
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
alembic==1.12.1

# Machine Learning
scikit-learn==1.3.2
xgboost==2.0.2
numpy==1.25.2
pandas==2.1.4

# Model persistence
joblib==1.3.2

# API requests
requests==2.31.0
httpx==0.25.2

# Utilities
python-multipart==0.0.6
python-dateutil==2.8.2
```

### System Requirements

- Python 3.9+
- PostgreSQL 13+ database
- 4GB+ RAM (for model training)
- Internet connection (for FPL API)

## Installation & Setup

### 1. Database Setup

First, set up your PostgreSQL database:

```sql
-- Create database
CREATE DATABASE fantasy_ai_db;

-- Create user (optional)
CREATE USER fantasy_ai_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE fantasy_ai_db TO fantasy_ai_user;
```

### 2. Environment Setup

```bash
# Clone or create your project directory
mkdir fantasy-ai-agent
cd fantasy-ai-agent

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Historical Data Preparation

Organize your historical CSV files in this structure:

```
data/
├── 2016-17_players.csv
├── 2017-18_players.csv
├── 2018-19_players.csv
├── 2019-20_players.csv
├── 2020-21_players.csv
├── 2021-22_players.csv
├── 2022-23_players.csv
├── 2023-24_players.csv
└── 2024-25_players.csv
```

Each CSV should have these columns (minimum):
- `first_name`, `second_name`
- `goals_scored`, `assists`, `total_points`
- `minutes`, `creativity`, `influence`, `threat`
- `element_type` (position: GKP, DEF, MID, FWD)

### 4. Initial Setup

Run the setup script for complete initialization:

```bash
# Full setup (recommended for first time)
python setup.py --db-url "postgresql://user:password@localhost/fantasy_ai_db" \
                --data-dir "./data" \
                --full-setup

# OR step by step:

# 1. Create database schema
python setup.py --db-url "postgresql://your_db_url" --create-schema

# 2. Load historical data
python setup.py --db-url "postgresql://your_db_url" --data-dir "./data" --load-data

# 3. Train AI models
python setup.py --db-url "postgresql://your_db_url" --train-models

# 4. Fetch current season data
python setup.py --db-url "postgresql://your_db_url" --fetch-current
```

### 5. Start the API Server

Create a `main.py` file:

```python
from fastapi import FastAPI
from ai_fantasy_routes import router
import os

app = FastAPI(title="AI Fantasy Football Agent", version="2.0.0")

# Include AI routes
app.include_router(router, prefix="/api/v2/fantasy-ai", tags=["AI Fantasy"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
```

Start the server:

```bash
python main.py
```

## Usage Examples

### 1. Check AI Model Status

```bash
curl http://localhost:8000/api/v2/fantasy-ai/health
```

### 2. Get Player Predictions

```bash
# Get predictions for specific players
curl "http://localhost:8000/api/v2/fantasy-ai/player-predictions?player_ids=1,2,3"

# Get top midfielders
curl "http://localhost:8000/api/v2/fantasy-ai/player-predictions?position=MID&limit=10"
```

### 3. AI Transfer Recommendations

```bash
curl "http://localhost:8000/api/v2/fantasy-ai/ai-analyze?current_team=1,2,3,4,5,6,7,8,9,10,11,12,13,14,15&analysis_types=transfers&budget=2.0"
```

### 4. Captain Analysis

```bash
curl "http://localhost:8000/api/v2/fantasy-ai/captain-analysis?gameweeks_ahead=1"
```

### 5. Market Analysis

```bash
curl "http://localhost:8000/api/v2/fantasy-ai/market-analysis"
```

## Integration with Your Existing System

### Replace Your FantasyFootballAgent

```python
# OLD (rule-based)
from fantasy_agent import FantasyFootballAgent
agent = FantasyFootballAgent()

# NEW (AI-powered)
from ai_fantasy_agent import AIFantasyFootballAgent
ai_agent = AIFantasyFootballAgent("postgresql://your_db_url")
ai_agent.initialize_data()

# Get AI recommendations instead of rule-based ones
transfers = ai_agent.get_ai_transfer_recommendations(current_team, budget)
captains = ai_agent.get_ai_captain_recommendations()
```

### Update Your Routes

```python
# Replace your existing routes with the new AI-powered ones
from ai_fantasy_routes import router as ai_router

app.include_router(ai_router, prefix="/api/v2/fantasy-ai")
```

## Model Training & Updates

### Retrain Models

The AI models should be retrained periodically as new data becomes available:

```bash
# Retrain all models
curl -X POST "http://localhost:8000/api/v2/fantasy-ai/train-models" \
     -H "Content-Type: application/json" \
     -d '{"retrain": true}'
```

### Monitor Model Performance

```bash
curl "http://localhost:8000/api/v2/fantasy-ai/model-status"
```

Expected output:
```json
{
  "status": "ready",
  "models_available": ["total_points", "goals_scored", "assists", "clean_sheets"],
  "performance": {
    "total_points": {"mae": 15.2, "r2": 0.65},
    "goals_scored": {"mae": 1.8, "r2": 0.45}
  }
}
```

## Performance Optimization

### 1. Database Indexing

Ensure your database has proper indexes:

```sql
-- Add custom indexes for better performance
CREATE INDEX idx_player_performance ON player_historical_data(total_points DESC, minutes DESC);
CREATE INDEX idx_position_season ON player_historical_data(element_type, season_year);
```

### 2. Model Caching

Models are automatically cached after training. For production:

```python
# Load pre-trained models on startup
if not ai_agent.load_models():
    ai_agent.train_prediction_models()
```

### 3. API Caching

Consider implementing response caching for frequently accessed endpoints:

```python
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend

# Add caching decorators to your routes
@cache(expire=3600)  # Cache for 1 hour
async def get_player_predictions():
    # Your endpoint logic
```

## Troubleshooting

### Common Issues

1. **Models not training**: Check database connection and data quality
2. **Low prediction accuracy**: Ensure you have sufficient historical data (3+ seasons minimum)
3. **API timeouts**: Model prediction can be slow on first run; consider async processing
4. **Memory issues**: Reduce batch sizes or train models separately

### Data Quality Checks

```sql
-- Check data completeness
SELECT 
    season_year,
    COUNT(*) as players,
    AVG(total_points) as avg_points,
    COUNT(CASE WHEN minutes > 1000 THEN 1 END) as regular_players
FROM player_historical_data
GROUP BY season_year;

-- Identify data issues
SELECT first_name, second_name, season_year, total_points, minutes
FROM player_historical_data
WHERE total_points > 300 OR minutes > 3500 OR total_points < 0;
```

### Model Performance Monitoring

Monitor model performance over time:

```python
# Get detailed performance metrics
performance = ai_agent.get_model_performance_report()
print(f"Points prediction R²: {performance['model_performance']['total_points']['r2']:.3f}")

# Models with R² > 0.6 are considered good for fantasy football
```

## Advanced Configuration

### Custom Model Parameters

```python
# Customize model training
ai_agent.train_prediction_models(
    test_size=0.25,  # Use 25% for testing
    cv_folds=10,     # 10-fold cross-validation
    random_state=42  # Reproducible results
)
```

### Feature Engineering

Add custom features in `_extract_features_from_current_data()`:

```python
# Add fixture difficulty
fixture_difficulty = self._get_next_fixture_difficulty(player_data['team'])
features.append(fixture_difficulty)

# Add team strength rating
team_strength = self._get_team_strength(player_data['team'])
features.append(team_strength)
```

## API Documentation

Once running, visit `http://localhost:8000/docs` for interactive API documentation.

## Support & Contributing

- Check model performance regularly
- Update historical data each season
- Monitor prediction accuracy vs actual results
- Consider ensemble methods for improved accuracy

The AI agent provides significant improvements over rule-based systems by learning from historical patterns and making data-driven predictions rather than relying on static thresholds.