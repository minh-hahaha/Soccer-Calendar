import sys
import os
import glob
import pandas as pd

sys.path.append('.')

from backend.pipeline.etl import get_session
from backend.core.config import get_settings
from backend.models.database.fantasy import PlayerHistoricalData

settings = get_settings()
session = get_session(settings.DATABASE_URL)

# Clear existing historical data before loading new data
print("Clearing existing historical data...")
session.query(PlayerHistoricalData).delete()
session.commit()
print("✅ Existing data cleared")


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
