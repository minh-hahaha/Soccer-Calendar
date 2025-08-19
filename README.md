# Football Prediction API

A comprehensive football match prediction service with machine learning capabilities.

## 🏗️ Project Structure

```
football-prediction/
├── backend/                 # All backend code
│   ├── api/                # API endpoints
│   │   ├── main.py         # Existing football API
│   │   ├── ml_api.py       # ML prediction endpoints
│   │   └── routes/         # Organized routes
│   ├── ml/                 # Machine Learning service
│   │   ├── models/         # ML model definitions
│   │   ├── features/       # Feature engineering
│   │   ├── training/       # Model training
│   │   └── evaluation/     # Model evaluation
│   ├── database/           # Database layer
│   │   ├── models.py       # SQLAlchemy models
│   │   ├── schemas.py      # Pydantic schemas
│   │   ├── db.py          # Database connection
│   │   └── migrations/     # Alembic migrations
│   ├── services/           # Business logic
│   │   ├── client.py       # Football data API client
│   │   ├── commands.py     # CLI commands
│   │   └── mappers.py      # Data mappers
│   ├── utils/              # Utilities
│   │   └── redis_cache.py  # Redis caching
│   ├── config.py           # Configuration
│   ├── cli.py             # CLI entry point
│   └── main.py            # Combined API entry point
├── frontend/               # React application
├── shared/                 # Shared types/config
├── tests/                  # Test suite
├── docs/                   # Documentation
├── scripts/                # Utility scripts
└── artifacts/              # ML model artifacts
```

## 🚀 Quick Start

### 1. Setup Environment

```bash
# Copy environment template
cp env.example .env

# Edit .env with your API key
FD_API_KEY=your_football_data_api_key_here
```

### 2. Install Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install frontend dependencies (optional)
cd frontend && npm install
```

### 3. Start the API

```bash
# Start the combined API server
make serve

# Or use uvicorn directly
uvicorn backend.main:app --reload
```

### 4. Access the API

- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Fixtures**: http://localhost:8000/v1/fixtures
- **Predictions**: http://localhost:8000/v1/predict?match_id=12345

## 📊 API Endpoints

### Existing Football API (v1)
- `GET /v1/fixtures` - Get match fixtures
- `GET /v1/teams` - Get teams
- `GET /v1/standings` - Get league standings
- `GET /v1/head2head?matchId=123` - Get head-to-head stats

### ML Prediction API (v1)
- `GET /v1/predict?match_id=123` - Predict single match
- `POST /v1/batch/predict` - Predict multiple matches
- `GET /v1/features?match_id=123` - Get match features
- `GET /v1/health` - Enhanced health check

## 🤖 Machine Learning Features

### Feature Engineering
- **Form Features**: Rolling window PPG, goal difference
- **Standings Features**: Current position, rank changes
- **Head-to-Head**: Historical match statistics
- **Context Features**: Home advantage, rest days

### Models
- **XGBoost**: Gradient boosting for classification
- **Logistic Regression**: Linear model baseline
- **Random Forest**: Ensemble method

### Training Pipeline
```bash
# Train with sample data
make train-sample

# Train with real data
make train-real

# Build features
make build-features

# Evaluate models
python -m backend eval report --seasons 2020-2024
```

## 🛠️ Development

### Available Commands

```bash
# Setup
make setup                    # Setup database and directories
make install                  # Install dependencies

# Data Pipeline
make ingest-teams            # Ingest teams data
make ingest-matches          # Ingest matches data
make ingest-standings        # Ingest standings data
make build-features          # Build ML features

# ML Pipeline
make train-sample            # Train with sample data
make train-real              # Train with real data

# API
make serve                   # Start combined API
make serve-existing          # Start existing API only

# Development
make test                    # Run tests
make format                  # Format code
make lint                    # Lint code
make type-check              # Type checking

# Database
make db-migrate              # Run migrations
make db-rollback             # Rollback migration
make db-reset                # Reset database

# Full Pipeline
make pipeline                # Run full pipeline (sample data)
make pipeline-real           # Run full pipeline (real data)
```

### Environment Variables

```env
# API Configuration
FD_API_KEY=your_football_data_api_key_here
DB_URI=postgresql+psycopg://user:pass@localhost:5432/footy
REDIS_URL=redis://localhost:6379

# Model Configuration
MODEL_DIR=./artifacts
COMPETITION_CODE=PL
SEASONS=2020,2021,2022,2023,2024

# Feature Engineering
ROLLING_WINDOW=5
RANK_DELTA_WINDOW=5
```

## 🧪 Testing

```bash
# Run all tests
make test

# Run specific test files
pytest tests/test_features.py -v
pytest tests/test_api.py -v

# Run with coverage
pytest --cov=backend tests/
```

## 📈 Model Evaluation

### Metrics
- **Accuracy**: Overall prediction accuracy
- **Log Loss**: Logarithmic loss for probability calibration
- **Brier Score**: Mean squared error of probabilities
- **Expected Calibration Error (ECE)**: Probability calibration quality

### Baselines
- **Home Advantage**: Simple home team bias
- **Table Only**: Using only standings information

## 🎨 Frontend Integration

The frontend is a React application that can consume the API:

```bash
cd frontend
npm install
npm run dev
```

### Components
- `PredictionDisplay`: Shows ML predictions for matches
- `Fixtures`: Displays match fixtures with predictions
- `Standings`: League table view

## 🚀 Deployment

### Docker
```bash
# Build image
make docker-build

# Run container
make docker-run
```

### Production
```bash
# Start production server
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## 📚 Documentation

- [Integration Guide](docs/INTEGRATION_GUIDE.md) - How to integrate with existing systems
- [API Documentation](http://localhost:8000/docs) - Interactive API docs
- [Model Documentation](docs/MODEL_GUIDE.md) - ML model details

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

- **Issues**: Create an issue on GitHub
- **Documentation**: Check the docs folder
- **API Docs**: Visit http://localhost:8000/docs when running

---

**Note**: This is a production-ready football prediction service with comprehensive ML capabilities, proper testing, and clean architecture.
