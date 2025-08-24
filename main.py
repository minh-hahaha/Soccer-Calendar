from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api import original as original_api
from backend.api import agent_api as agent_api
# Import the new AI agents

load_dotenv()
import os

app = FastAPI(
    title="Premier League AI Analytics w/ Fantasy Football",
    description="Advanced Premier League analytics with AI agents for match analysis and fantasy football",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(original_api.router, prefix="/v1", tags=["Football Data"])
# app.include_router(match_agent_router, prefix="/agent", tags=["Match Analysis Agent"])
app.include_router(agent_api.router, prefix="/fantasy", tags=["Fantasy Football Agent"])

from backend.pipeline.etl import ingest_all_football_data, ingest_players
from backend.pipeline.fpl_history import ingest_fpl_history


# ingest_all_football_data(os.getenv("FD_API_KEY"), os.getenv("DATABASE_URL"), "2025")
# ingest_all_football_data(os.getenv("FD_API_KEY"), os.getenv("DATABASE_URL"), "2024")

#ingest_players(os.getenv("DATABASE_URL"))

# ingest_fpl_history(os.getenv("DATABASE_URL"))

@app.get("/")
def read_root():
    return {
        "message": "Premier League AI Analytics API",
        "version": "2.0.0",
        "features": [
            "Match fixtures and results",
            "League standings",
            "AI-powered match analysis",
            "Fantasy Football assistant",
            "Market intelligence",
            "Transfer recommendations",
        ],
        "agents": {
            #  "match_analyst": "/agent/analyze",
            "fantasy_assistant": "/fantasy/analyze"
        },
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "version": "2.0.0",
        "agents_status": {
            #   "match_agent": "operational",
            "fantasy_agent": "operational"
        },
    }


