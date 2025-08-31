"""
Main Pipeline Runner Script
"""
#!/usr/bin/env python3

import asyncio
import os
import sys
import time
from pathlib import Path
from datetime import datetime
import glob
import pandas as pd

import click

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from backend.core.config import get_settings
from backend.core.logger import setup_logging
from backend.pipeline.orchestrator import PipelineOrchestrator
from backend.core.monitoring import health_monitor
from backend.core.exceptions import PipelineError

from backend.pipeline.etl import get_session
from backend.models.database.fantasy import PlayerHistoricalData


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

            # loading csv players. CAN MOVE TO etl.py
            session = get_session(settings.DATABASE_URL)
            csv_files = glob.glob('./data/*.csv')
            total_records = 0

            for csv_file in csv_files:
                print(f'Processing {csv_file}...')
                try:
                    filename = os.path.basename(csv_file)
                    season = None
                    if '2020-21' in filename:
                        season = '2020-21'
                    elif '2021-22' in filename:
                        season = '2021-22'
                    elif '2022-23' in filename:
                        season = '2022-23'
                    elif '2023-24' in filename:
                        season = '2023-24'
                    elif '2024-25' in filename:
                        season = '2024-25'
                    else:
                        print(f'Cannot determine season for {filename}, skipping')
                        continue

                    df = pd.read_csv(csv_file)
                    df['season_year'] = season
                    df.columns = df.columns.str.lower().str.replace(' ', '_')

                    required_cols = ['first_name', 'second_name', 'total_points', 'element_type']
                    missing_cols = [col for col in required_cols if col not in df.columns]
                    if missing_cols:
                        print(f'Missing columns {missing_cols} in {filename}, skipping')
                        continue

                    numeric_cols = ['goals_scored', 'assists', 'total_points', 'minutes',
                                    'creativity', 'influence', 'threat', 'now_cost']
                    for col in numeric_cols:
                        if col in df.columns:
                            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

                    position_map = {1: 'GKP', 2: 'DEF', 3: 'MID', 4: 'FWD'}
                    if df['element_type'].dtype != 'object':
                        df['element_type'] = df['element_type'].map(position_map).fillna('MID')

                    records = df.to_dict('records')
                    for record in records:
                        player = PlayerHistoricalData(
                            first_name=str(record.get('first_name', '')),
                            second_name=str(record.get('second_name', '')),
                            goals_scored=int(record.get('goals_scored', 0)),
                            assists=int(record.get('assists', 0)),
                            total_points=int(record.get('total_points', 0)),
                            minutes=int(record.get('minutes', 0)),
                            creativity=float(record.get('creativity', 0)),
                            influence=float(record.get('influence', 0)),
                            threat=float(record.get('threat', 0)),
                            now_cost=int(record.get('now_cost', 0)),
                            element_type=str(record.get('element_type', 'MID')),
                            season_year=season
                        )
                        session.add(player)

                    session.commit()
                    total_records += len(records)
                    print(f'Loaded {len(records)} records from {filename}')

                except Exception as e:
                    print(f'Error processing {csv_file}: {str(e)}')
                    session.rollback()
                    continue

            session.close()
            print(f'✅ Total records loaded: {total_records}')

            
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
