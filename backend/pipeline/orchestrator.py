"""
Pipeline Orchestrator - Coordinates the entire data pipeline
"""
import asyncio
import logging
from typing import Optional
from ..core.config import Settings
from ..core.exceptions import PipelineError
from ..services.football_service import FootballService
from ..services.ml_service import MLService

logger = logging.getLogger(__name__)


class PipelineOrchestrator:
    """Main pipeline orchestrator"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.football_service = FootballService()
        self.ml_service = MLService()
    
    async def run_ingestion_pipeline(self, season: str = "2025") -> bool:
        """Run data ingestion pipeline"""
        try:
            logger.info(f"Starting data ingestion for season {season}")
            
            # Import your existing ingestion function
            from backend.pipeline.etl import ingest_all_football_data
            
            # Run ingestion
            ingest_all_football_data(
                api_key=self.settings.FD_API_KEY,
                database_url=self.settings.DATABASE_URL,
                season=season
            )
            
            logger.info("Data ingestion completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Data ingestion failed: {str(e)}")
            raise PipelineError(f"Data ingestion failed: {str(e)}")
    
    async def run_ml_pipeline(self, force_retrain: bool = False) -> bool:
        """Run ML training pipeline"""
        try:
            logger.info("Starting ML pipeline")
            
            success = await self.ml_service.train_all_models(force_retrain=force_retrain)
            
            if success:
                logger.info("ML pipeline completed successfully")
                return True
            else:
                raise PipelineError("ML training failed")
                
        except Exception as e:
            logger.error(f"ML pipeline failed: {str(e)}")
            raise PipelineError(f"ML pipeline failed: {str(e)}")
    
    async def validate_ingested_data(self) -> bool:
        """Validate ingested data quality"""
        try:
            logger.info("Validating ingested data")
            
            # Add your data validation logic here
            # For now, just return True
            
            logger.info("Data validation completed")
            return True
            
        except Exception as e:
            logger.error(f"Data validation failed: {str(e)}")
            return False