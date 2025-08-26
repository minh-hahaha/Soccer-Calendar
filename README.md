# Football AI Analytics API

Production-ready FastAPI backend for Premier League analytics and AI-powered Fantasy Football. Includes a data pipeline, model training endpoints, health checks, and ops tooling.

## Quick Start

```bash
# 1) Install dev deps and setup env
make install-dev
make env-setup
make create-dirs

# 2) Create DB schema
make setup-db

# 3) Start server (dev)
make serve
# Prod-style
# make serve-prod
```

- API docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Quick health: http://localhost:8000/health/quick

## Project Layout (Backend)

- `main.py`: FastAPI app, lifespan, routers, pipeline triggers
- `backend/`:
  - `api/v1/`: Football data REST API
  - `api/v2/`: Fantasy AI REST API
  - `core/`: config, database, logging, monitoring, exceptions
  - `services/`: `football_service`, `ml_service`
  - `pipeline/`: orchestrator and ETL utilities
- `data/`: your data directory
  - `logs/app.log`: application logs
  - `models/`: trained models

Notes:
- `data/logs/` is ignored by git.
- Keep secrets in `.env` (also ignored). Use `.env.example` as template.

## Environment Variables (.env)

Minimal set commonly used by the app (adjust to your `backend.core.config`):

```
# API
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=INFO
ENVIRONMENT=development
APP_NAME=Football AI Analytics API
APP_VERSION=2.0.0

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/football
# or SQLite for local experiments
# DATABASE_URL=sqlite:///./football.db

# External APIs
FD_API_KEY=your_football_data_api_key
FPL_API_BASE_URL=https://fantasy.premierleague.com/api
```

## Makefile Commands

```bash
# Install
make install           # production deps
make install-dev       # dev deps (pytest, black, flake8, etc.)

# Server
make serve             # dev server (reload)
make serve-prod        # uvicorn with workers

# Database
make setup-db          # create/upgrade schema
make check-db          # check DB health
make reset-db          # DANGER: drop/reset

# Pipeline
make pipeline          # run full pipeline
make pipeline-ingest   # ingest only
make pipeline-train    # train models only
make load-historical-data  # load CSVs from data/ into DB

# Health & Monitoring
make health-check      # comprehensive health check
make monitor           # watch mode monitor
make quick-health      # quick LB probe
make status            # summarize status


# Docker
make docker-build
make docker-run
make docker-stop
make docker-logs

# Utilities
make logs              # tail data/logs/app.log
make clean             # clean caches/logs
make backup-models     # tar.gz models
make quickstart        # one-shot dev setup
```

## Endpoints

- Root: `GET /`
- Health:
  - `GET /health` (comprehensive)
  - `GET /health/quick` (fast probe)
- System:
  - `GET /system` (version, env, resources)
- API v1 (football data): `GET /v1/...`
- API v2 (fantasy AI): `GET /v2/fantasy/...`
- Docs: `/docs`, `/redoc`

Examples:
```bash
# Quick health
curl -s http://localhost:8000/health/quick

# System info
curl -s http://localhost:8000/system | jq '.'

# Football v1
curl -s http://localhost:8000/v1/teams | jq '.'

# Fantasy AI v2 (examples; adjust to implemented routes)
curl -s "http://localhost:8000/v2/fantasy/player-predictions?player_ids=1,2,3" | jq '.'
```

## Data Pipeline (CLI)

The project ships a CLI for pipeline control via `scripts/run_pipeline.py` (as wired in the Makefile):

- Full pipeline: `make pipeline`
- Ingestion only: `make pipeline-ingest`
- Train models: `make pipeline-train`
- Load CSVs in `data/`: `make load-historical-data`

Put historical CSVs in `data/` (e.g., `2020-21_players.csv`, `2021-22_players.csv`, ...). The loader auto-detects the season by filename.

## Logging

- File: `data/logs/app.log`
- Configure level via `LOG_LEVEL`.

## Testing (optional)

If/when a `tests/` folder exists:
```bash
pytest -v
pytest --cov
```

## Docker

```bash
make docker-build
make docker-run
# open http://localhost:8000/docs
make docker-logs
make docker-stop
```

## Security & Secrets

- Never commit secrets. `.env` and `.env.*` are ignored.
- Use `.env.example` as a reference.

## Troubleshooting

- Logs not ignored? Remove tracked files once:
  ```bash
  git rm --cached -r data/logs
  git commit -m "Stop tracking logs"
  ```
- DB connection issues: verify `DATABASE_URL` and that the DB is reachable.
- Missing API keys: set `FD_API_KEY` in `.env`.

---

Built for development-first workflows, structured for production hardening.
