#!/usr/bin/env python3
"""
Main entry point for the Football Prediction Backend
Combines existing API with ML prediction service
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import existing API routes
from api.main import router as existing_api

# Import ML API routes
from api.ml_api import router as ml_api

# Create main app
app = FastAPI(
    title="Football Prediction API",
    description="Combined football data API with ML predictions",
    version="2.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include existing API routes
app.include_router(existing_api, prefix="/v1", tags=["existing-api"])

# Include ML API routes
app.include_router(ml_api, prefix="/ml", tags=["ml-api"])

# Root endpoint
@app.get("/")
def root():
    return {
        "message": "Football Prediction API",
        "version": "2.0.0",
        "docs": "/docs",
        "endpoints": {
            "existing": "/v1/fixtures, /v1/teams, /v1/standings, /v1/head2head",
            "ml": "/ml/predict, /ml/batch/predict, /ml/features, /ml/health"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
