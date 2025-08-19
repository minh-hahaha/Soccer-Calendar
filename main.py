from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api.main import router

app = FastAPI(
    title="Football API",
    description="A simple REST API for football data using the football-data.org API",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the router
app.include_router(router, prefix="/v1")

@app.get("/")
def root():
    return {
        "message": "Football API",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "fixtures": "/v1/fixtures",
            "standings": "/v1/standings", 
            "teams": "/v1/teams",
            "head2head": "/v1/head2head?matchId=123"
        }
    }

@app.get("/health")
def health():
    return {"status": "healthy"}
