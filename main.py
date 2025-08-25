import logging
import sys
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

import login as login
# # Import the new AI agents

# Add project root to path
sys.path.append(str(Path(__file__).parent))

# Core imports
from backend.core.config import get_settings
from backend.core.database import init_database, db_manager
from backend.core.logger import setup_logging
from backend.core.monitoring import health_monitor
from backend.core.exceptions import DatabaseError, PipelineError

# Your existing API routers (updated imports)
from backend.api.v1.router import router as v1_router
from backend.api.v2.router import router as v2_router

# New services
from backend.services.football_service import FootballService
from backend.services.ml_service import MLService
from backend.pipeline.orchestrator import PipelineOrchestrator

# Initialize settings and logging
settings = get_settings()
logger = setup_logging()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    
    # Startup
    logger.info("🚀 Starting Football AI Analytics API")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    
    try:
        # Initialize database
        logger.info("📊 Initializing database...")
        init_database()
        
        # Initialize services
        logger.info("🔧 Initializing services...")
        app.state.football_service = FootballService()
        app.state.ml_service = MLService()
        app.state.pipeline_orchestrator = PipelineOrchestrator(settings)
        
        # Run initial health check
        logger.info("🏥 Running initial health check...")
        health_status = await health_monitor.comprehensive_health_check()
        logger.warning(f"Health check details: {health_status['checks']}")
        if health_status['healthy']:
            logger.info("✅ Initial health check passed")
        else:
            logger.warning("⚠️  Initial health check found issues")
        
        logger.info("🎯 Application startup complete")
        
    except Exception as e:
        logger.error(f"❌ Application startup failed: {str(e)}")
        raise
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down Football AI Analytics API")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description="Advanced Premier League analytics with AI agents for match analysis and fantasy football",
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handlers
@app.exception_handler(DatabaseError)
async def database_exception_handler(request, exc: DatabaseError):
    logger.error(f"Database error: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"error": "Database operation failed", "detail": str(exc)}
    )

@app.exception_handler(PipelineError)
async def pipeline_exception_handler(request, exc: PipelineError):
    logger.error(f"Pipeline error: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"error": "Pipeline operation failed", "detail": str(exc)}
    )


# app.include_router(original_api.router, prefix="/v1", tags=["Football Data"])
# app.include_router(router.router, prefix="/fantasy", tags=["Fantasy Football Agent"])
app.include_router(login.router, prefix="/login", tags=["getTeam"])

# from backend.pipeline.etl import ingest_all_football_data, ingest_players
# from backend.pipeline.fpl_history import ingest_fpl_history


# #ingest_all_football_data(os.getenv("FD_API_KEY"), os.getenv("DATABASE_URL"), "2025")


# Include your existing routers with updated prefixes
app.include_router(
    v1_router, 
    prefix="/v1", 
    tags=["Football Data API v1"]
)

app.include_router(
    v2_router, 
    prefix="/v2/fantasy", 
    tags=["AI Fantasy Football API v2"]
)

# Root endpoints
@app.get("/")
async def read_root():
    """API root endpoint"""
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "description": "Advanced Premier League analytics with AI agents",
        "endpoints": {
            "health": "/health",
            "system_info": "/system",
            "football_api": "/api/v1/",
            "fantasy_ai": "/api/v2/fantasy/",
            "pipeline": "/pipeline/",
        },
        "documentation": {
            "interactive_docs": "/docs",
            "redoc": "/redoc"
        }
    }


@app.get("/health")
async def health_check():
    """Comprehensive health check endpoint"""
    from datetime import datetime
    
    try:
        health_status = await health_monitor.comprehensive_health_check()
        
        status_code = 200 if health_status['healthy'] else 503
        
        return JSONResponse(
            status_code=status_code,
            content={
                "status": "healthy" if health_status['healthy'] else "unhealthy",
                "timestamp": health_status['timestamp'],
                "version": settings.APP_VERSION,
                "environment": settings.ENVIRONMENT,
                "checks": health_status['checks'],
                "duration_seconds": health_status['duration_seconds']
            }
        )
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )


@app.get("/health/quick")
async def quick_health_check():
    """Quick health check for load balancers"""
    from datetime import datetime
    
    try:
        db_healthy = db_manager.health_check()
        
        if db_healthy:
            return {"status": "healthy", "timestamp": datetime.now().isoformat()}
        else:
            return JSONResponse(
                status_code=503,
                content={"status": "unhealthy", "reason": "database_down"}
            )
    except Exception:
        return JSONResponse(
            status_code=503,
            content={"status": "error", "reason": "internal_error"}
        )


@app.get("/system")
async def system_info():
    """Get system information"""
    try:
        import psutil
        from datetime import datetime
        
        system_data = {
            "app_version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT,
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "cpu_count": psutil.cpu_count(),
            "memory_total_gb": round(psutil.virtual_memory().total / (1024**3), 2),
            "database_pool": db_manager.get_connection_info(),
            "timestamp": datetime.now().isoformat()
        }
        
        return system_data
        
    except Exception as e:
        logger.error(f"System info request failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve system information")


# Pipeline management endpoints
@app.post("/pipeline/run")
async def run_pipeline(
    background_tasks: BackgroundTasks,
    season: str = "2025",
    retrain_models: bool = True,
    validate_data: bool = True
):
    """Trigger the complete data pipeline"""
    
    async def run_pipeline_task():
        try:
            from scripts.run_pipeline import MainPipeline
            
            pipeline = MainPipeline()
            success = await pipeline.run_full_pipeline(
                season=season,
                retrain_models=retrain_models,
                validate_data=validate_data
            )
            
            logger.info(f"Pipeline completed with status: {'success' if success else 'failed'}")
            
        except Exception as e:
            logger.error(f"Pipeline task failed: {str(e)}")
    
    background_tasks.add_task(run_pipeline_task)
    
    return {
        "message": "Pipeline started in background",
        "parameters": {
            "season": season,
            "retrain_models": retrain_models,
            "validate_data": validate_data
        },
        "status": "started",
        "estimated_duration_minutes": "10-15"
    }


@app.post("/pipeline/ingest")
async def ingest_data(background_tasks: BackgroundTasks, season: str = "2025"):
    """Trigger data ingestion only"""
    
    async def ingest_task():
        try:
            orchestrator = app.state.pipeline_orchestrator
            await orchestrator.run_ingestion_pipeline(season)
            logger.info("Data ingestion completed successfully")
        except Exception as e:
            logger.error(f"Data ingestion failed: {str(e)}")
    
    background_tasks.add_task(ingest_task)
    
    return {
        "message": "Data ingestion started",
        "season": season,
        "status": "started"
    }


# CLI runner for development
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.is_development,
        log_level=settings.LOG_LEVEL.lower(),
    )
