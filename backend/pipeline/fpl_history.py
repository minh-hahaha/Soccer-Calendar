from pathlib import Path
import subprocess
from typing import Optional

import pandas as pd
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    Integer,
    String,
)

from .etl import Base, get_session


FPL_HISTORY_REPO_URL = "https://github.com/vaastav/Fantasy-Premier-League.git"

def clone_history_repo(target_dir: str = "vaastav-data", repo_url: str = FPL_HISTORY_REPO_URL) -> Path:
    """Clone the Vaastav Fantasy Premier League data repository if not already present."""
    path = Path(target_dir)
    if path.exists():
        return path
    subprocess.run(
        ["git", "clone", "--depth", "1", repo_url, str(path)],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return path

def load_player_gameweek_csvs(repo_path: str, season: str) -> pd.DataFrame:
    """Load all player gameweek CSVs for a given season into a single DataFrame."""
    base = Path(repo_path) / "data" / season / "gws"
    frames = []
    for csv_file in base.glob("*.csv"):
        if csv_file.name == "merged_gw.csv":
            continue
        frames.append(pd.read_csv(csv_file))
    if frames:
        return pd.concat(frames, ignore_index=True)
    return pd.DataFrame()


def normalize_fpl_history(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize column names and parse dates for FPL history data."""
    df = df.rename(columns=lambda c: c.strip().lower().replace(" ", "_"))
    if "kickoff_time" in df.columns:
        df["kickoff_time"] = pd.to_datetime(df["kickoff_time"], errors="coerce")
    if "round" in df.columns:
        df = df.rename(columns={"round": "gameweek"})
    if "value" in df.columns:
        df["value"] = df["value"].astype(float) / 10
    return df

class PlayerGameweek(Base):
    """SQLAlchemy model for storing player gameweek statistics."""

    __tablename__ = "player_gameweeks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    element = Column(Integer, nullable=False)
    season = Column(String, nullable=False)
    gameweek = Column(Integer, nullable=False)
    kickoff_time = Column(DateTime)
    total_points = Column(Integer)
    opponent_team = Column(Integer)
    was_home = Column(Boolean)
    team_h_score = Column(Integer)
    team_a_score = Column(Integer)
    minutes = Column(Integer)
    goals_scored = Column(Integer)
    assists = Column(Integer)
    clean_sheets = Column(Integer)
    goals_conceded = Column(Integer)
    own_goals = Column(Integer)
    penalties_saved = Column(Integer)
    penalties_missed = Column(Integer)
    yellow_cards = Column(Integer)
    red_cards = Column(Integer)
    saves = Column(Integer)
    bonus = Column(Integer)
    bps = Column(Integer)
    influence = Column(Float)
    creativity = Column(Float)
    threat = Column(Float)
    ict_index = Column(Float)
    value = Column(Float)
    transfers_balance = Column(Integer)
    selected = Column(Integer)
    transfers_in = Column(Integer)
    transfers_out = Column(Integer)


def store_player_gameweeks(session, df: pd.DataFrame, season: str) -> None:
    """Persist cleaned player gameweek data to the database."""
    if df.empty:
        return
    df = df.copy()
    df["season"] = season
    
    # Convert NaN in boolean columns to False
    bool_cols = [col.name for col in PlayerGameweek.__table__.columns if isinstance(col.type, Boolean)]
    for col in bool_cols:
        if col in df.columns:
            df[col] = df[col].fillna(False).astype(bool)

    records = df.to_dict(orient="records")
    cols = {c.name for c in PlayerGameweek.__table__.columns}
    filtered = [{k: v for k, v in r.items() if k in cols} for r in records]
    session.query(PlayerGameweek).filter(PlayerGameweek.season == season).delete()
    session.bulk_insert_mappings(PlayerGameweek, filtered)
    session.commit()

def ingest_fpl_history(
    database_url: str,
    season: str = "2024-25",
    repo_path: Optional[str] = None,
) -> None:
    """Clone, load, clean, and store FPL history data for a season."""
    repo = clone_history_repo(repo_path or "vaastav-data")
    df = load_player_gameweek_csvs(repo, season)
    df = normalize_fpl_history(df)
    session = get_session(database_url)
    try:
        store_player_gameweeks(session, df, season)
        print(f"Stored {len(df)} player gameweek rows for season {season}")
    except Exception as exc:
        session.rollback()
        print(f"Error during FPL history ingestion: {exc}")
        raise
    finally:
        session.close()