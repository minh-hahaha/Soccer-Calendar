.PHONY: help install install-dev serve clean test lint format \
        pipeline setup-db health-check monitor docker-build docker-run

# Configuration
PYTHON := python3
PIP := pip3

help: ## Show this help message
	@echo "Football AI Analytics API - Development Commands"
	@echo "==============================================="
	@echo ""
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

## Installation Commands
install: ## Install production dependencies
	$(PIP) install -r requirements.txt

install-dev: ## Install development dependencies
	$(PIP) install -r requirements.txt
	$(PIP) install pytest pytest-asyncio pytest-cov httpx black isort flake8 psutil click aiohttp

## Development Commands
serve: ## Start development server
	$(PYTHON) main.py

serve-prod: ## Start production server
	uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4

## Database Commands
setup-db: ## Set up database schema
	$(PYTHON) scripts/setup_database.py create-schema
	@echo "✅ Database schema created"

check-db: ## Check database health
	$(PYTHON) scripts/setup_database.py health-check

reset-db: ## Reset database (CAUTION: destroys data)
	$(PYTHON) scripts/setup_database.py reset-database
	@echo "⚠️  Database reset completed"

## Pipeline Commands
pipeline: ## Run complete data pipeline
	$(PYTHON) scripts/run_pipeline.py run-pipeline --season 2025
	@echo "✅ Pipeline execution completed"

pipeline-ingest: ## Run data ingestion only
	$(PYTHON) scripts/run_pipeline.py ingest-only --season 2025
	@echo "✅ Data ingestion completed"

pipeline-train: ## Train ML models only
	$(PYTHON) scripts/run_pipeline.py train-models --retrain
	@echo "✅ Model training completed"

load-historical-data: ## Load historical CSV data from data folder
	@echo "Loading historical data from CSV files..."
	$(PYTHON) -c "\
import sys, os; \
sys.path.append('.'); \
from backend.pipeline.etl import get_session; \
from backend.core.config import get_settings; \
from backend.models.database.fantasy import PlayerHistoricalData; \
import pandas as pd; \
import glob; \
settings = get_settings(); \
session = get_session(settings.DATABASE_URL); \
csv_files = glob.glob('./data/*.csv'); \
total_records = 0; \
for csv_file in csv_files: \
    print(f'Processing {csv_file}...'); \
    try: \
        filename = os.path.basename(csv_file); \
        season = None; \
        if '2020-21' in filename: season = '2020-21'; \
        elif '2021-22' in filename: season = '2021-22'; \
        elif '2022-23' in filename: season = '2022-23'; \
        elif '2023-24' in filename: season = '2023-24'; \
        elif '2024-25' in filename: season = '2024-25'; \
        else: print(f'Cannot determine season for {filename}, skipping'); continue; \
        df = pd.read_csv(csv_file); \
        df['season_year'] = season; \
        df.columns = df.columns.str.lower().str.replace(' ', '_'); \
        required_cols = {'first_name': 'first_name', 'second_name': 'second_name', 'total_points': 'total_points', 'element_type': 'element_type'}; \
        missing_cols = [col for col in required_cols.keys() if col not in df.columns]; \
        if missing_cols: print(f'Missing columns {missing_cols} in {filename}, skipping'); continue; \
        numeric_cols = ['goals_scored', 'assists', 'total_points', 'minutes', 'creativity', 'influence', 'threat', 'now_cost']; \
        for col in numeric_cols: \
            if col in df.columns: df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0); \
        position_map = {1: 'GKP', 2: 'DEF', 3: 'MID', 4: 'FWD'}; \
        if df['element_type'].dtype != 'object': df['element_type'] = df['element_type'].map(position_map).fillna('MID'); \
        records = df.to_dict('records'); \
        for record in records: \
            player = PlayerHistoricalData( \
                first_name=str(record.get('first_name', '')), \
                second_name=str(record.get('second_name', '')), \
                goals_scored=int(record.get('goals_scored', 0)), \
                assists=int(record.get('assists', 0)), \
                total_points=int(record.get('total_points', 0)), \
                minutes=int(record.get('minutes', 0)), \
                creativity=float(record.get('creativity', 0)), \
                influence=float(record.get('influence', 0)), \
                threat=float(record.get('threat', 0)), \
                now_cost=int(record.get('now_cost', 0)), \
                element_type=str(record.get('element_type', 'MID')), \
                season_year=season \
            ); \
            session.add(player); \
        session.commit(); \
        total_records += len(records); \
        print(f'Loaded {len(records)} records from {filename}'); \
    except Exception as e: print(f'Error processing {csv_file}: {str(e)}'); session.rollback(); continue; \
session.close(); \
print(f'✅ Total records loaded: {total_records}');"

## Health and Monitoring Commands
health-check: ## Run comprehensive health check
	$(PYTHON) scripts/run_pipeline.py health-check
	@echo "✅ Health check completed"

monitor: ## Start monitoring (watch mode)
	$(PYTHON) scripts/run_pipeline.py monitor --watch --interval 60

quick-health: ## Quick health check
	@curl -s http://localhost:8000/health/quick | jq -r '.status // "Server not running"' 2>/dev/null || echo "Server not running"

status: ## Show application status
	@echo "Application Status:"
	@echo "=================="
	@curl -s http://localhost:8000/health/quick 2>/dev/null | jq -r '.status // "Server not running"' || echo "Server not running"

## Testing Commands
test: ## Run all tests (when test files are created)
	@echo "Setting up test environment..."
	@if [ -d "tests" ]; then \
		$(PYTHON) -m pytest tests/ -v; \
	else \
		echo "No tests directory found. Create tests/ directory first."; \
	fi

test-api: ## Test API endpoints manually
	@echo "Testing API endpoints..."
	@echo "Health Check:"
	@curl -s http://localhost:8000/health/quick 2>/dev/null || echo "Server not running"
	@echo "\nSystem Info:"
	@curl -s http://localhost:8000/system 2>/dev/null | jq '.app_version // "N/A"' || echo "Server not running"

## Code Quality Commands  
format: ## Format code with black (if available)
	@if command -v black >/dev/null 2>&1; then \
		black backend/ main.py scripts/; \
		echo "✅ Code formatted"; \
	else \
		echo "⚠️  black not installed. Run 'make install-dev' first"; \
	fi

lint: ## Lint code with flake8 (if available)
	@if command -v flake8 >/dev/null 2>&1; then \
		flake8 backend/ main.py scripts/ --max-line-length=100 --ignore=E203,W503; \
		echo "✅ Code linting completed"; \
	else \
		echo "⚠️  flake8 not installed. Run 'make install-dev' first"; \
	fi

## Docker Commands
docker-build: ## Build Docker image
	docker build -t football-ai-api:latest .
	@echo "✅ Docker image built"

docker-run: ## Run application in Docker
	docker run -d --name football-ai-container \
		-p 8000:8000 \
		--env-file .env \
		-v $(PWD)/data:/app/data \
		football-ai-api:latest
	@echo "✅ Container started: football-ai-container"

docker-stop: ## Stop Docker container
	docker stop football-ai-container || true
	docker rm football-ai-container || true
	@echo "✅ Container stopped"

docker-logs: ## View Docker logs
	docker logs -f football-ai-container

## Environment Commands
env-setup: ## Create .env file from example
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "✅ .env file created from example"; \
		echo "⚠️  Please edit .env with your configuration"; \
	else \
		echo ".env file already exists"; \
	fi

create-dirs: ## Create necessary directories
	mkdir -p data/logs data/models data/exports
	@echo "✅ Required directories created"

## Development Workflow
dev-setup: install-dev env-setup create-dirs setup-db ## Complete development setup
	@echo ""
	@echo "🎯 Development Setup Complete!"
	@echo "================================"
	@echo ""
	@echo "Next steps:"
	@echo "  1. Edit .env file with your API keys"
	@echo "  2. Run 'make load-historical-data' to load your CSV files"  
	@echo "  3. Run 'make serve' to start the development server"
	@echo "  4. Visit http://localhost:8000/docs for API documentation"

full-pipeline-setup: install setup-db load-historical-data pipeline ## Complete pipeline setup
	@echo ""
	@echo "🚀 Full Pipeline Setup Complete!"
	@echo "================================"
	@echo ""
	@echo "Your system is now ready with:"
	@echo "  ✅ Database schema created"
	@echo "  ✅ Historical data loaded"
	@echo "  ✅ Data pipeline executed"
	@echo "  ✅ ML models trained"

## API Interaction Commands
api-fixtures: ## Test fixtures endpoint
	@echo "Testing fixtures endpoint..."
	@curl -s "http://localhost:8000/api/v1/fixtures" | jq '.fixtures[0:3] // "No fixtures found"' 2>/dev/null || echo "Server not running"

api-teams: ## Test teams endpoint  
	@echo "Testing teams endpoint..."
	@curl -s "http://localhost:8000/api/v1/teams" | jq '.teams[0:3] // "No teams found"' 2>/dev/null || echo "Server not running"

api-fantasy-health: ## Test fantasy AI health
	@echo "Testing fantasy AI health..."
	@curl -s "http://localhost:8000/api/v2/fantasy/health" | jq '.' 2>/dev/null || echo "Server not running"

api-train-models: ## Trigger model training via API
	@echo "Starting model training..."
	@curl -X POST "http://localhost:8000/api/v2/fantasy/train-models?retrain=true" \
		-H "Content-Type: application/json" 2>/dev/null | jq '.' || echo "Server not running"

## Maintenance Commands
clean: ## Clean up temporary files
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type f -name "*.log" -delete 2>/dev/null || true
	rm -rf .pytest_cache/ 2>/dev/null || true
	@echo "✅ Cleanup completed"

logs: ## View application logs
	@if [ -f "./data/logs/app.log" ]; then \
		tail -f ./data/logs/app.log; \
	else \
		echo "No log file found at ./data/logs/app.log"; \
		echo "Start the application first with 'make serve'"; \
	fi

backup-models: ## Backup trained models
	@if [ -d "./data/models" ]; then \
		tar -czf "models_backup_$(shell date +%Y%m%d_%H%M%S).tar.gz" data/models/; \
		echo "✅ Models backup created"; \
	else \
		echo "No models directory found"; \
	fi

## Quick Start Commands
quickstart: ## Quick start for new developers
	@echo "🚀 Football AI API - Quick Start"
	@echo "================================"
	@echo ""
	@$(MAKE) install-dev
	@$(MAKE) env-setup
	@$(MAKE) create-dirs  
	@$(MAKE) setup-db
	@echo ""
	@echo "✅ Quick start completed!"
	@echo ""
	@echo "Next steps:"
	@echo "  1. Edit .env file with your API configuration"
	@echo "  2. Add your historical CSV files to the data/ directory"
	@echo "  3. Run 'make load-historical-data' to load the data"
	@echo "  4. Run 'make serve' to start the development server"
	@echo "  5. Visit http://localhost:8000/docs for API documentation"

# Default target
.DEFAULT_GOAL := help