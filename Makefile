.PHONY: help setup install test train serve clean

help: ## Show this help message
	@echo "Football Match Prediction Service"
	@echo "================================"
	@echo ""
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies
	pip install -r requirements.txt

setup: ## Setup the application (database, directories)
	python -m backend setup

test: ## Run tests
	pytest tests/ -v

train-sample: ## Train model with sample data
	python -m backend train fit --algo xgb --use-sample

train-real: ## Train model with real data (requires API key)
	python -m backend train fit --algo xgb --seasons 2020,2021,2022,2023 --valid 2024

ingest-teams: ## Ingest teams data
	python -m backend ingest teams

ingest-matches: ## Ingest matches data for current season
	python -m backend ingest matches --season 2024

ingest-standings: ## Ingest standings data for current season
	python -m backend ingest standings --season 2024

build-features: ## Build features for current season
	python -m backend features build --season 2024

serve: ## Start the combined API server
	uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

clean: ## Clean up generated files
	rm -rf cache/
	rm -rf artifacts/
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete

docker-build: ## Build Docker image
	docker build -t football-prediction .

docker-run: ## Run Docker container
	docker run -p 8000:8000 football-prediction

# Development commands
format: ## Format code with black
	black backend/ tests/

lint: ## Lint code with flake8
	flake8 backend/ tests/

type-check: ## Type check with mypy
	mypy backend/

# Database commands
db-migrate: ## Run database migrations
	cd backend/database && alembic upgrade head

db-rollback: ## Rollback last migration
	cd backend/database && alembic downgrade -1

db-reset: ## Reset database (drop and recreate)
	cd backend/database && alembic downgrade base
	cd backend/database && alembic upgrade head

# Full pipeline
pipeline: setup ingest-teams ingest-matches ingest-standings build-features train-sample serve ## Run full pipeline with sample data

pipeline-real: setup ingest-teams ingest-matches ingest-standings build-features train-real serve ## Run full pipeline with real data

# Integration commands
integrate: ## Integrate ML service with existing API
	python scripts/integrate_ml.py

serve-existing: ## Start existing API server (legacy)
	uvicorn backend.api.main:app --reload --host 0.0.0.0 --port 8000

test-integration: ## Test the integrated API
	python scripts/integrate_ml.py

# Learning from mistakes commands
learn-analyze: ## Analyze recent prediction errors
	cd backend && source venv/bin/activate && python -m ml.training.learn analyze --days-back 7

learn-retrain: ## Retrain model with new data and learn from mistakes
	cd backend && source venv/bin/activate && python -m ml.training.learn retrain --algorithm xgb --days-back 30

learn-compare: ## Compare old vs new model performance
	cd backend && source venv/bin/activate && python -m ml.training.learn compare --days-back 7 --algorithm xgb

learn-monitor: ## Monitor prediction performance continuously
	cd backend && source venv/bin/activate && python -m ml.training.learn monitor --interval-hours 24 --auto-retrain

# Quick analysis commands
analyze-matchday: ## Analyze predictions for specific matchday
	cd backend && source venv/bin/activate && python -m ml.training.learn analyze --matchday 1 --output-file analysis_matchday1.json

analyze-season: ## Analyze predictions for current season
	cd backend && source venv/bin/activate && python -m ml.training.learn analyze --season 2024 --output-file analysis_season2024.json
