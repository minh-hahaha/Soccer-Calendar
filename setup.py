#!/usr/bin/env python3
"""
Setup script for AI Fantasy Football Agent
This script helps you set up the database, load historical data, and train initial models.
"""

import os
import pandas as pd
import argparse
from sqlalchemy import create_engine, text
import glob
from pathlib import Path
import logging
from typing import List, Dict
import requests
from datetime import datetime
import json

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FantasyAISetup:
    def __init__(self, db_connection_string: str):
        self.db_connection = db_connection_string
        self.engine = create_engine(db_connection_string)
        
    def create_database_schema(self):
        """Create the required database tables"""
        logger.info("Creating database schema...")
        
        schema_sql = """
        -- Drop existing table if exists
        DROP TABLE IF EXISTS player_historical_data CASCADE;
        
        -- Create historical player data table
        CREATE TABLE player_historical_data (
            id SERIAL PRIMARY KEY,
            first_name VARCHAR(100) NOT NULL,
            second_name VARCHAR(100) NOT NULL,
            goals_scored INTEGER DEFAULT 0,
            assists INTEGER DEFAULT 0,
            total_points INTEGER DEFAULT 0,
            minutes INTEGER DEFAULT 0,
            goals_conceded INTEGER DEFAULT 0,
            creativity DECIMAL(10,2) DEFAULT 0,
            influence DECIMAL(10,2) DEFAULT 0,
            threat DECIMAL(10,2) DEFAULT 0,
            bonus INTEGER DEFAULT 0,
            bps INTEGER DEFAULT 0,
            ict_index DECIMAL(10,2) DEFAULT 0,
            clean_sheets INTEGER DEFAULT 0,
            red_cards INTEGER DEFAULT 0,
            yellow_cards INTEGER DEFAULT 0,
            selected_by_percent DECIMAL(5,2) DEFAULT 0,
            now_cost INTEGER DEFAULT 0,
            element_type VARCHAR(10) NOT NULL,
            season_year VARCHAR(10) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            -- Constraints
            CONSTRAINT unique_player_season UNIQUE(first_name, second_name, season_year, total_points),
            CONSTRAINT valid_element_type CHECK(element_type IN ('GKP', 'DEF', 'MID', 'FWD')),
            CONSTRAINT valid_season_format CHECK(season_year ~ '^[0-9]{4}-[0-9]{2}$')
        );
        
        -- Create indexes for better query performance
        CREATE INDEX idx_player_name_season ON player_historical_data(first_name, second_name, season_year);
        CREATE INDEX idx_season_year ON player_historical_data(season_year);
        CREATE INDEX idx_element_type ON player_historical_data(element_type);
        CREATE INDEX idx_total_points ON player_historical_data(total_points);
        CREATE INDEX idx_minutes ON player_historical_data(minutes);
        
        -- Create a view for easy analysis
        CREATE OR REPLACE VIEW player_summary AS
        SELECT 
            first_name,
            second_name,
            element_type,
            COUNT(*) as seasons_played,
            AVG(total_points) as avg_points_per_season,
            AVG(minutes) as avg_minutes_per_season,
            SUM(goals_scored) as total_goals,
            SUM(assists) as total_assists,
            MAX(total_points) as best_season_points,
            MIN(total_points) as worst_season_points
        FROM player_historical_data
        WHERE minutes > 100  -- Only players with significant playing time
        GROUP BY first_name, second_name, element_type
        ORDER BY avg_points_per_season DESC;
        
        -- Create table for storing model metadata
        CREATE TABLE IF NOT EXISTS model_training_log (
            id SERIAL PRIMARY KEY,
            model_name VARCHAR(100),
            training_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            data_size INTEGER,
            performance_metrics JSONB,
            model_path VARCHAR(255),
            notes TEXT
        );
        """
        
        with self.engine.connect() as conn:
            for statement in schema_sql.split(';'):
                if statement.strip():
                    conn.execute(text(statement))
            conn.commit()
        
        logger.info("Database schema created successfully!")
    
    def load_csv_files(self, data_directory: str):
        """Load historical CSV files into the database"""
        logger.info(f"Loading CSV files from {data_directory}...")
        
        # Define expected season mappings
        season_mappings = {
            # '2016-17': '2016-17',
            # '2017-18': '2017-18', 
            # '2018-19': '2018-19',
            # '2019-20': '2019-20',
            '2020-21': '2020-21',
            '2021-22': '2021-22',
            '2022-23': '2022-23',
            '2023-24': '2023-24',
            '2024-25': '2024-25'
        }
        
        total_records = 0
        
        # Look for CSV files in the directory
        csv_files = glob.glob(os.path.join(data_directory, "*.csv"))
        
        if not csv_files:
            logger.error(f"No CSV files found in {data_directory}")
            return
        
        for csv_file in csv_files:
            try:
                # Extract season from filename
                filename = os.path.basename(csv_file)
                season = None
                
                # Try to extract season from filename
                for season_key in season_mappings.keys():
                    if season_key.replace('-', '_') in filename or season_key in filename:
                        season = season_mappings[season_key]
                        break
                
                if not season:
                    logger.warning(f"Could not determine season for file {filename}. Skipping.")
                    continue
                
                logger.info(f"Processing {filename} for season {season}...")
                
                # Load and clean data
                df = pd.read_csv(csv_file)
                
                # Standardize column names
                df.columns = df.columns.str.lower().str.replace(' ', '_')
                
                # Add season information
                df['season_year'] = season
                
                # Clean and validate data
                df = self._clean_player_data(df, season)
                
                if len(df) == 0:
                    logger.warning(f"No valid data found in {filename}")
                    continue
                
                # Insert into database
                df.to_sql('player_historical_data', self.engine, if_exists='append', index=False, method='multi')
                
                records_added = len(df)
                total_records += records_added
                logger.info(f"Added {records_added} records for season {season}")
                
            except Exception as e:
                logger.error(f"Error processing {csv_file}: {str(e)}")
                continue
        
        logger.info(f"Successfully loaded {total_records} total records!")
        
        # Verify data
        self._verify_data_integrity()
    
    def _clean_player_data(self, df: pd.DataFrame, season: str) -> pd.DataFrame:
        """Clean and standardize player data"""
        
        # Required columns
        required_columns = ['first_name', 'second_name', 'element_type']
        
        # Check for required columns
        for col in required_columns:
            if col not in df.columns:
                logger.error(f"Required column '{col}' not found in data for season {season}")
                return pd.DataFrame()
        
        # Fill NaN values
        numeric_columns = [
            'goals_scored', 'assists', 'total_points', 'minutes', 'goals_conceded',
            'creativity', 'influence', 'threat', 'bonus', 'bps', 'ict_index',
            'clean_sheets', 'red_cards', 'yellow_cards', 'selected_by_percent', 'now_cost'
        ]
        
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        # Standardize position names
        position_mapping = {
            'GK': 'GKP', 'Goalkeeper': 'GKP', 'GKP': 'GKP',
            'DEF': 'DEF', 'Defender': 'DEF', 'Defence': 'DEF',
            'MID': 'MID', 'Midfielder': 'MID', 'Midfield': 'MID',
            'FWD': 'FWD', 'Forward': 'FWD', 'Attack': 'FWD'
        }
        
        df['element_type'] = df['element_type'].map(position_mapping).fillna('MID')
        
        # Clean player names
        df['first_name'] = df['first_name'].astype(str).str.strip()
        df['second_name'] = df['second_name'].astype(str).str.strip()
        
        # Remove players with no meaningful data
        df = df[
            (df['first_name'] != '') & 
            (df['second_name'] != '') & 
            (df['first_name'] != 'nan') & 
            (df['second_name'] != 'nan')
        ]
        
        # Ensure data types
        df['season_year'] = season
        
        logger.info(f"Cleaned data: {len(df)} players for season {season}")
        return df
    
    def _verify_data_integrity(self):
        """Verify the integrity of loaded data"""
        logger.info("Verifying data integrity...")
        
        with self.engine.connect() as conn:
            # Check total records
            result = conn.execute(text("SELECT COUNT(*) FROM player_historical_data")).fetchone()
            total_records = result[0]
            logger.info(f"Total records in database: {total_records}")
            
            # Check records by season
            result = conn.execute(text("""
                SELECT season_year, COUNT(*) as player_count, 
                       AVG(total_points) as avg_points,
                       COUNT(DISTINCT element_type) as positions
                FROM player_historical_data 
                GROUP BY season_year 
                ORDER BY season_year
            """)).fetchall()
            
            logger.info("Records by season:")
            for row in result:
                logger.info(f"  {row[0]}: {row[1]} players, avg {row[2]:.1f} points, {row[3]} positions")
            
            # Check for potential duplicates
            result = conn.execute(text("""
                SELECT first_name, second_name, season_year, COUNT(*) 
                FROM player_historical_data 
                GROUP BY first_name, second_name, season_year 
                HAVING COUNT(*) > 1
            """)).fetchall()
            
            if result:
                logger.warning(f"Found {len(result)} potential duplicate players")
            else:
                logger.info("No duplicate players found")
            
            # Check data quality
            result = conn.execute(text("""
                SELECT 
                    COUNT(CASE WHEN minutes = 0 THEN 1 END) as zero_minutes,
                    COUNT(CASE WHEN total_points = 0 THEN 1 END) as zero_points,
                    COUNT(CASE WHEN now_cost = 0 THEN 1 END) as zero_cost
                FROM player_historical_data
            """)).fetchone()
            
            logger.info(f"Data quality check:")
            logger.info(f"  Players with 0 minutes: {result[0]}")
            logger.info(f"  Players with 0 points: {result[1]}")
            logger.info(f"  Players with 0 cost: {result[2]}")
    
    def fetch_current_season_data(self):
        """Fetch and store current season data for reference"""
        logger.info("Fetching current season data from FPL API...")
        
        try:
            response = requests.get("https://fantasy.premierleague.com/api/bootstrap-static/")
            if response.status_code == 200:
                data = response.json()
                
                # Save current season data
                current_season_file = f"current_season_data_{datetime.now().strftime('%Y-%m-%d')}.json"
                with open(current_season_file, 'w') as f:
                    import json
                    json.dump(data, f, indent=2)
                
                logger.info(f"Current season data saved to {current_season_file}")
                
                # Extract player data for comparison
                players = data['elements']
                logger.info(f"Current season has {len(players)} players")
                
                return data
            else:
                logger.error(f"Failed to fetch current season data: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching current season data: {str(e)}")
            return None
    
    def train_initial_models(self):
        """Train initial AI models"""
        logger.info("Training initial AI models...")
        
        try:
            from backend.api.v2.fantasy_agent import FantasyFootballAgent
            
            agent = FantasyFootballAgent(self.db_connection)
            
            # Initialize and train
            if agent.initialize_data():
                agent.train_prediction_models()
                
                # Log training results
                performance = agent.get_model_performance_report()
                
                with self.engine.connect() as conn:
                    conn.execute(text("""
                        INSERT INTO model_training_log 
                        (model_name, data_size, performance_metrics, notes)
                        VALUES (:model_name, :data_size, :performance, :notes)
                    """), {
                        'model_name': 'initial_training',
                        'data_size': performance['training_data_size'],
                        'performance': json.dumps(performance['model_performance']),
                        'notes': 'Initial model training completed'
                    })
                    conn.commit()
                
                logger.info("Model training completed successfully!")
                logger.info(f"Model performance: {performance}")
                
                return True
            else:
                logger.error("Failed to initialize agent data")
                return False
                
        except ImportError:
            logger.error("Could not import AIFantasyFootballAgent. Make sure it's available.")
            return False
        except Exception as e:
            logger.error(f"Error during model training: {str(e)}")
            return False
    
    def create_sample_data(self, num_seasons: int = 3, players_per_season: int = 500):
        """Create sample data for testing (if you don't have historical CSV files)"""
        logger.info(f"Creating sample data for {num_seasons} seasons with {players_per_season} players each...")
        
        import random
        import numpy as np
        
        positions = ['GKP', 'DEF', 'MID', 'FWD']
        position_weights = [0.05, 0.35, 0.35, 0.25]  # Realistic distribution
        
        # Sample player names
        first_names = ['Aaron', 'Alex', 'Ben', 'Charlie', 'David', 'Eddie', 'Frank', 'George', 'Harry', 'Ivan',
                      'Jack', 'Kyle', 'Luke', 'Mason', 'Nathan', 'Oscar', 'Paul', 'Quinn', 'Ryan', 'Sam',
                      'Tom', 'Usman', 'Victor', 'Will', 'Xavier', 'Yannick', 'Zack']
        
        last_names = ['Adams', 'Brown', 'Clark', 'Davis', 'Evans', 'Ford', 'Green', 'Hall', 'Jones', 'King',
                     'Lewis', 'Moore', 'Nash', 'Owen', 'Price', 'Quinn', 'Reed', 'Smith', 'Taylor', 'White']
        
        seasons = [f"{2016+i}-{str(17+i).zfill(2)}" for i in range(num_seasons)]
        
        sample_data = []
        
        for season in seasons:
            logger.info(f"Generating data for season {season}...")
            
            for i in range(players_per_season):
                position = np.random.choice(positions, p=position_weights)
                
                # Position-specific stats
                if position == 'GKP':
                    base_points = random.randint(50, 180)
                    goals = 0
                    assists = random.randint(0, 2)
                    clean_sheets = random.randint(3, 20)
                    saves = random.randint(50, 150)
                    price = random.randint(40, 60)
                elif position == 'DEF':
                    base_points = random.randint(30, 200)
                    goals = random.randint(0, 8)
                    assists = random.randint(0, 12)
                    clean_sheets = random.randint(2, 18)
                    saves = 0
                    price = random.randint(40, 80)
                elif position == 'MID':
                    base_points = random.randint(20, 280)
                    goals = random.randint(0, 25)
                    assists = random.randint(0, 20)
                    clean_sheets = random.randint(0, 15)
                    saves = 0
                    price = random.randint(45, 130)
                else:  # FWD
                    base_points = random.randint(20, 300)
                    goals = random.randint(0, 30)
                    assists = random.randint(0, 15)
                    clean_sheets = 0
                    saves = 0
                    price = random.randint(50, 140)
                
                # Generate correlated stats
                minutes = max(0, int(np.random.normal(1800, 800)))
                minutes = min(minutes, 3420)  # Max minutes in a season
                
                # Adjust points based on minutes
                if minutes < 500:
                    base_points = int(base_points * 0.3)
                elif minutes < 1000:
                    base_points = int(base_points * 0.6)
                
                player_data = {
                    'first_name': random.choice(first_names),
                    'second_name': random.choice(last_names),
                    'goals_scored': goals,
                    'assists': assists,
                    'total_points': base_points,
                    'minutes': minutes,
                    'goals_conceded': random.randint(0, 80) if position in ['GKP', 'DEF'] else 0,
                    'creativity': round(random.uniform(0, 100), 1),
                    'influence': round(random.uniform(0, 100), 1),
                    'threat': round(random.uniform(0, 100), 1),
                    'bonus': random.randint(0, 30),
                    'bps': random.randint(0, 800),
                    'ict_index': round(random.uniform(0, 50), 1),
                    'clean_sheets': clean_sheets,
                    'red_cards': random.randint(0, 3),
                    'yellow_cards': random.randint(0, 15),
                    'selected_by_percent': round(random.uniform(0.1, 50), 1),
                    'now_cost': price,
                    'element_type': position,
                    'season_year': season
                }
                
                sample_data.append(player_data)
        
        # Insert sample data
        df = pd.DataFrame(sample_data)
        df.to_sql('player_historical_data', self.engine, if_exists='append', index=False, method='multi')
        
        logger.info(f"Created {len(sample_data)} sample records!")
        return len(sample_data)


def main():
    parser = argparse.ArgumentParser(description="Setup AI Fantasy Football Agent")
    parser.add_argument("--db-url", required=True, 
                       help="Database connection string (e.g., postgresql://user:pass@localhost/fantasy_db)")
    parser.add_argument("--data-dir", 
                       help="Directory containing historical CSV files")
    parser.add_argument("--create-schema", action="store_true",
                       help="Create database schema")
    parser.add_argument("--load-data", action="store_true",
                       help="Load historical CSV data")
    parser.add_argument("--create-sample", action="store_true",
                       help="Create sample data for testing")
    parser.add_argument("--train-models", action="store_true",
                       help="Train initial AI models")
    parser.add_argument("--fetch-current", action="store_true",
                       help="Fetch current season data from FPL API")
    parser.add_argument("--full-setup", action="store_true",
                       help="Run complete setup process")
    
    args = parser.parse_args()
    
    # Initialize setup
    setup = FantasyAISetup(args.db_url)
    
    try:
        if args.full_setup:
            logger.info("Running full setup process...")
            
            # 1. Create schema
            setup.create_database_schema()
            
            # 2. Load data (sample if no data directory provided)
            if args.data_dir:
                setup.load_csv_files(args.data_dir)
            else:
                logger.info("No data directory provided, creating sample data...")
                setup.create_sample_data()
            
            # 3. Fetch current season data
            setup.fetch_current_season_data()
            
            # 4. Train models
            setup.train_initial_models()
            
            logger.info("✅ Full setup completed successfully!")
            
        else:
            # Run individual tasks
            if args.create_schema:
                setup.create_database_schema()
            
            if args.load_data and args.data_dir:
                setup.load_csv_files(args.data_dir)
            elif args.load_data:
                logger.error("--data-dir required when using --load-data")
            
            if args.create_sample:
                setup.create_sample_data()
            
            if args.fetch_current:
                setup.fetch_current_season_data()
            
            if args.train_models:
                setup.train_initial_models()
    
    except Exception as e:
        logger.error(f"Setup failed: {str(e)}")
        return 1
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())