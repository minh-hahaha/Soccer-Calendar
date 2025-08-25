"""
Main Pipeline Runner Script
"""
#!/usr/bin/env python3

import asyncio
import logging
import sys
import time
from pathlib import Path
from datetime import datetime

import click

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from backend.core.config import get_settings
from backend.core.logger import setup_logging
from backend.pipeline.orchestrator import PipelineOrchestrator
from backend.core.monitoring import health_monitor
from backend.core.exceptions import PipelineError

# Setup
settings = get_settings()
logger = setup_logging()


class MainPipeline:
    """Main pipeline coordinator"""
    
    def __init__(self):
        self.settings = settings
        self.orchestrator = PipelineOrchestrator(settings)
    
    async def run_full_pipeline(self, 
                               season: str = "2025",
                               retrain_models: bool = True,
                               validate_data: bool = True) -> bool:
        """Run the complete pipeline"""
        pipeline_start = time.time()
        
        try:
            logger.info("🚀 Starting Full Pipeline Execution")
            logger.info(f"Season: {season}, Retrain Models: {retrain_models}")
            
            # Step 1: Data ingestion
            logger.info("📊 Starting Data Ingestion Phase")
            await self.orchestrator.run_ingestion_pipeline(season)
            
            # Step 2: Data validation (optional)
            if validate_data:
                logger.info("✅ Starting Data Validation Phase")
                await self.orchestrator.validate_ingested_data()
            
            # Step 3: ML Pipeline
            if retrain_models:
                logger.info("🤖 Starting ML Training Phase")
                await self.orchestrator.run_ml_pipeline()
            
            pipeline_duration = time.time() - pipeline_start
            logger.info(f"✅ Pipeline completed successfully in {pipeline_duration:.2f}s")
            
            return True
            
        except Exception as e:
            pipeline_duration = time.time() - pipeline_start
            logger.error(f"❌ Pipeline failed after {pipeline_duration:.2f}s: {str(e)}")
            return False


@click.group()
def cli():
    """Football AI Pipeline CLI"""
    pass


@cli.command()
@click.option('--season', default='2025', help='Season year (e.g., 2025)')
@click.option('--no-training', is_flag=True, help='Skip model training')
@click.option('--no-validation', is_flag=True, help='Skip data validation')
def run_pipeline(season: str, no_training: bool, no_validation: bool):
    """Run the complete pipeline"""
    
    pipeline = MainPipeline()
    
    success = asyncio.run(pipeline.run_full_pipeline(
        season=season,
        retrain_models=not no_training,
        validate_data=not no_validation
    ))
    
    sys.exit(0 if success else 1)


@cli.command()
@click.option('--season', default='2025', help='Season year')
def ingest_only(season: str):
    """Run only data ingestion"""
    
    pipeline = MainPipeline()
    
    async def run():
        await pipeline.orchestrator.run_ingestion_pipeline(season)
    
    asyncio.run(run())


@cli.command()
@click.option('--retrain', is_flag=True, help='Force model retraining')
def train_models(retrain: bool):
    """Run only model training"""
    
    pipeline = MainPipeline()
    
    async def run():
        await pipeline.orchestrator.run_ml_pipeline(force_retrain=retrain)
    
    asyncio.run(run())


@cli.command()
def health_check():
    """Run comprehensive health check"""
    
    async def run():
        try:
            health_status = await health_monitor.comprehensive_health_check()
            
            if health_status['healthy']:
                logger.info("✅ All health checks passed")
                print("System Status: HEALTHY")
                return True
            else:
                logger.error("❌ Health check failed")
                print("System Status: UNHEALTHY")
                for check_name, result in health_status['checks'].items():
                    if not result.get('healthy', False):
                        print(f"  - {check_name}: {result.get('error', 'Failed')}")
                return False
        except Exception as e:
            logger.error(f"❌ Health check failed: {str(e)}")
            return False
    
    success = asyncio.run(run())
    sys.exit(0 if success else 1)


@cli.command()
@click.option('--watch', is_flag=True, help='Watch mode - continuous monitoring')
@click.option('--interval', default=300, help='Check interval in seconds')
def monitor(watch: bool, interval: int):
    """Monitor system health"""
    
    async def run_monitoring():
        if not watch:
            # Single health check
            status = await health_monitor.comprehensive_health_check()
            print(f"System status: {'HEALTHY' if status['healthy'] else 'UNHEALTHY'}")
            return
        
        # Continuous monitoring
        print(f"Starting continuous monitoring (interval: {interval}s)")
        print("Press Ctrl+C to stop")
        
        while True:
            try:
                status = await health_monitor.comprehensive_health_check()
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                status_text = "HEALTHY" if status['healthy'] else "UNHEALTHY"
                print(f"[{timestamp}] System Status: {status_text}")
                
                if not status['healthy']:
                    print("Issues detected:")
                    for check_name, result in status['checks'].items():
                        if not result.get('healthy', False):
                            print(f"  - {check_name}: {result.get('error', 'Failed')}")
                
                await asyncio.sleep(interval)
                
            except KeyboardInterrupt:
                print("\nMonitoring stopped by user")
                break
            except Exception as e:
                print(f"Monitoring error: {str(e)}")
                await asyncio.sleep(interval)
    
    asyncio.run(run_monitoring())


if __name__ == "__main__":
    cli()
