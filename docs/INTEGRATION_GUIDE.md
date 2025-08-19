# How To: Integrate ML Predictions with Your Football API

This guide will walk you through integrating machine learning predictions into your existing football API. Follow these steps to add intelligent match predictions to your application.

## 🎯 What You'll Learn

By the end of this guide, you'll know how to:
- Set up the ML prediction service
- Integrate predictions with your existing API
- Use the new prediction endpoints
- Add predictions to your frontend
- Troubleshoot common issues

## 📋 Prerequisites

Before starting, make sure you have:
- Python 3.8+ installed
- A Football Data API key (get one at [football-data.org](https://www.football-data.org/))
- Basic knowledge of REST APIs
- Your existing football API running

## 🚀 How To: Quick Integration (Recommended)

### Step 1: Set Up Your Environment

First, prepare your environment variables:

```bash
# Copy the environment template
cp env.example .env

# Edit the .env file with your API key
nano .env
```

Add your Football Data API key:
```env
FD_API_KEY=your_football_data_api_key_here
```

### Step 2: Run the Integration Script

The easiest way to get started is using the automated integration script:

```bash
# Run the integration script
python scripts/integrate_ml.py
```

This script will:
- ✅ Check if you have all required dependencies
- ✅ Train a sample ML model for you
- ✅ Test that everything works correctly
- ✅ Show you how to use the new features

### Step 3: Start Your Enhanced API

Now start your API with the new ML features:

```bash
# Start the server with ML predictions enabled
uvicorn backend.main:app --reload
```

Your API now has ML predictions! 🎉

## 🔧 How To: Use the New Prediction Endpoints

### Single Match Prediction

**What it does:** Predicts the outcome of a specific match

**How to use it:**
```bash
curl "http://localhost:8000/predict?match_id=12345"
```

**What you'll get back:**
```json
{
  "matchId": 12345,
  "competition": "PL",
  "kickoff": "2024-01-20T19:00:00Z",
  "homeTeam": "Arsenal",
  "awayTeam": "Chelsea",
  "homeTeamId": 57,
  "awayTeamId": 61,
  "probs": {
    "home": 0.47,
    "draw": 0.26,
    "away": 0.27
  },
  "top_features": [
    {"name": "home_advantage", "contribution": 0.15},
    {"name": "team_form", "contribution": 0.08},
    {"name": "head_to_head", "contribution": 0.05}
  ],
  "model_version": "xgb_2024-01-15",
  "calibrated": false
}
```

**How to interpret the results:**
- `probs.home`: Probability of home team winning (47%)
- `probs.draw`: Probability of a draw (26%)
- `probs.away`: Probability of away team winning (27%)
- `top_features`: Shows which factors most influenced the prediction

### Multiple Match Predictions

**What it does:** Predicts outcomes for multiple matches at once

**How to use it:**
```bash
curl -X POST "http://localhost:8000/batch/predict" \
  -H "Content-Type: application/json" \
  -d '{"match_ids": [12345, 12346, 12347]}'
```

**When to use this:** When you need predictions for several matches (more efficient than individual calls)

### Fixtures with Predictions

**What it does:** Gets all fixtures for a matchday with predictions included

**How to use it:**
```bash
curl "http://localhost:8000/fixtures-with-predictions?matchday=1&status=SCHEDULED"
```

**Perfect for:** Displaying upcoming matches with predictions on your website

## 🎨 How To: Add Predictions to Your Frontend

### Option 1: Using the Provided React Component

**Step 1:** Import the prediction component
```tsx
import PredictionDisplay from './components/PredictionDisplay';
```

**Step 2:** Add it to your match display
```tsx
function MatchCard({ match }) {
  return (
    <div className="match-card">
      <div className="match-info">
        <h3>{match.homeTeam} vs {match.awayTeam}</h3>
        <p>{match.utcDate}</p>
      </div>
      
      {/* Add the prediction display */}
      <PredictionDisplay matchId={match.id} />
    </div>
  );
}
```

### Option 2: Custom JavaScript Implementation

**Step 1:** Create a function to fetch predictions
```javascript
async function getPrediction(matchId) {
  try {
    const response = await fetch(`http://localhost:8000/predict?match_id=${matchId}`);
    const prediction = await response.json();
    return prediction;
  } catch (error) {
    console.error('Error fetching prediction:', error);
    return null;
  }
}
```

**Step 2:** Display the prediction
```javascript
function displayPrediction(prediction) {
  if (!prediction) return;
  
  const { probs } = prediction;
  const maxProb = Math.max(probs.home, probs.draw, probs.away);
  
  let outcome = '';
  if (maxProb === probs.home) outcome = 'Home Win';
  else if (maxProb === probs.draw) outcome = 'Draw';
  else outcome = 'Away Win';
  
  console.log(`Predicted outcome: ${outcome} (${(maxProb * 100).toFixed(1)}%)`);
}
```

**Step 3:** Use it in your app
```javascript
// Example: Get prediction when user clicks on a match
document.getElementById('match-12345').addEventListener('click', async () => {
  const prediction = await getPrediction(12345);
  displayPrediction(prediction);
});
```

## 🔄 How To: Advanced Setup (Full ML Pipeline)

If you want the complete ML experience with database storage and advanced features:

### Step 1: Set Up Database

**Install PostgreSQL:**
```bash
# On macOS with Homebrew
brew install postgresql
brew services start postgresql

# On Ubuntu
sudo apt-get install postgresql postgresql-contrib
```

**Create the database:**
```bash
createdb footy
```

### Step 2: Configure Environment

**Update your .env file:**
```env
FD_API_KEY=your_football_data_api_key_here
DB_URI=postgresql+psycopg://username:password@localhost:5432/footy
REDIS_URL=redis://localhost:6379
```

### Step 3: Run the Full Pipeline

**Set up the database schema:**
```bash
make db-migrate
```

**Ingest football data:**
```bash
make ingest-teams
make ingest-matches
make ingest-standings
```

**Build ML features:**
```bash
make build-features
```

**Train the model:**
```bash
# Quick training with sample data
make train-sample

# Full training with real data (requires API key)
make train-real
```

**Start the enhanced server:**
```bash
make serve-existing
```

## 🧪 How To: Test Your Integration

### Test the Basic Setup

**Check if the server is running:**
```bash
curl http://localhost:8000/health
```

**Test existing endpoints (should still work):**
```bash
curl http://localhost:8000/fixtures
curl http://localhost:8000/standings
```

**Test new prediction endpoints:**
```bash
curl http://localhost:8000/predict?match_id=12345
```

### Test Frontend Integration

**Start your frontend:**
```bash
cd frontend
npm run dev
```

**Navigate to a match page and verify:**
- Predictions load correctly
- No console errors
- UI displays prediction probabilities

### Run Automated Tests

**Run the integration test suite:**
```bash
make test-integration
```

**Run individual test files:**
```bash
python -m pytest tests/test_api.py
python -m pytest tests/test_features.py
```

## 🚨 How To: Troubleshoot Common Issues

### Issue 1: "Model Not Found" Error

**Problem:** The API can't find a trained model

**Solution:**
```bash
# Train a sample model
python -m backend.ml.training.train fit --algo xgb --use-sample
```

### Issue 2: "API Key Error"

**Problem:** Football Data API requests are failing

**Solution:**
```bash
# Check your API key is set correctly
cat .env | grep FD_API_KEY

# Test the API key manually
curl -H "X-Auth-Token: YOUR_API_KEY" http://api.football-data.org/v4/competitions/PL
```

### Issue 3: "Database Connection Error"

**Problem:** Can't connect to PostgreSQL

**Solutions:**
```bash
# Option A: Use simplified mode (no database required)
# Just use the basic integration - no database setup needed

# Option B: Fix database connection
# Check PostgreSQL is running
brew services list | grep postgresql

# Check connection string in .env
cat .env | grep DB_URI
```

### Issue 4: "CORS Issues" (Frontend)

**Problem:** Frontend can't call the API

**Solution:**
The API already has CORS enabled, but if you're still having issues:

```javascript
// Check your frontend proxy settings in vite.config.ts
// Make sure it points to the correct API URL
```

### Issue 5: "Slow Predictions"

**Problem:** Predictions are taking too long

**Solutions:**
```bash
# Enable caching (add to .env)
REDIS_URL=redis://localhost:6379

# Use batch predictions for multiple matches
curl -X POST "http://localhost:8000/batch/predict" \
  -d '{"match_ids": [1,2,3,4,5]}'
```

## 📈 How To: Optimize Performance

### Enable Caching

**Set up Redis:**
```bash
# Install Redis
brew install redis  # macOS
sudo apt-get install redis-server  # Ubuntu

# Start Redis
brew services start redis  # macOS
sudo systemctl start redis  # Ubuntu
```

**Add to your .env:**
```env
REDIS_URL=redis://localhost:6379
```

### Use Batch Predictions

**Instead of multiple individual calls:**
```bash
# ❌ Slow - multiple requests
curl "http://localhost:8000/predict?match_id=1"
curl "http://localhost:8000/predict?match_id=2"
curl "http://localhost:8000/predict?match_id=3"

# ✅ Fast - single batch request
curl -X POST "http://localhost:8000/batch/predict" \
  -d '{"match_ids": [1,2,3]}'
```

### Monitor Performance

**Check API health:**
```bash
curl http://localhost:8000/health
```

**Look for performance metrics in the response:**
```json
{
  "status": "healthy",
  "model_loaded": true,
  "cache_enabled": true,
  "response_time_ms": 45
}
```

## 🔧 How To: Configure Advanced Options

### Model Training Options

**Train with different algorithms:**
```bash
# XGBoost (default, best performance)
python -m backend.ml.training.train fit --algo xgb --use-sample

# Random Forest
python -m backend.ml.training.train fit --algo rf --use-sample

# Logistic Regression
python -m backend.ml.training.train fit --algo lr --use-sample
```

**Train with specific seasons:**
```bash
# Train on 2020-2023 data, validate on 2024
python -m backend.ml.training.train fit --algo xgb --seasons 2020,2021,2022,2023 --valid 2024
```

### Feature Engineering Options

**Adjust rolling windows:**
```env
# In your .env file
ROLLING_WINDOW=5  # Number of recent matches to consider
RANK_DELTA_WINDOW=5  # How many matches for ranking changes
```

**Configure competitions:**
```env
COMPETITION_CODE=PL  # Premier League
# Other options: BL1 (Bundesliga), SA (Serie A), PD (La Liga)
```

## 📞 How To: Get Help

### Check the Logs

**View application logs:**
```bash
# If using uvicorn with logging
uvicorn backend.main:app --reload --log-level debug

# Check for error messages in the terminal
```

### Run Diagnostics

**Use the integration script for diagnostics:**
```bash
python scripts/integrate_ml.py --check-only
```

**Test individual components:**
```bash
# Test API connectivity
curl http://localhost:8000/health

# Test model loading
curl http://localhost:8000/predict?match_id=12345

# Test database (if using full pipeline)
python -c "from backend.database.db import engine; print('DB OK')"
```

### Useful Commands Reference

```bash
# Quick start
make integrate

# Full pipeline setup
make pipeline

# Development
make serve-existing
make test

# Clean up
make clean

# Check status
make status
```

## 🎉 Congratulations!

You've successfully integrated ML predictions into your football API! 

**What you now have:**
- ✅ **Enhanced API**: All existing endpoints plus ML predictions
- ✅ **Smart Predictions**: Match outcome probabilities with explanations
- ✅ **Frontend Ready**: Components and examples for your UI
- ✅ **Production Ready**: Error handling, caching, and monitoring

**Next steps:**
1. **Start simple**: Use the basic integration first
2. **Add to frontend**: Display predictions on your match pages
3. **Monitor performance**: Watch prediction accuracy over time
4. **Upgrade when needed**: Move to full ML pipeline for advanced features

**Remember:** The ML model improves with more data. Consider retraining periodically with new match results for better predictions!

---

*Need help? Check the troubleshooting section above or run `python scripts/integrate_ml.py --help` for more options.*
