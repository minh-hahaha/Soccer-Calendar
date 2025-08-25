"""Fantasy Football Data Models"""
from sqlalchemy import Column, Integer, String, Float, Text, DECIMAL
from .base import Base, TimestampMixin


class PlayerHistoricalData(Base, TimestampMixin):
    __tablename__ = "player_historical_data"

    id = Column(Integer, primary_key=True, autoincrement=True)
    first_name = Column(String(100), nullable=False)
    second_name = Column(String(100), nullable=False)
    goals_scored = Column(Integer, default=0)
    assists = Column(Integer, default=0)
    total_points = Column(Integer, default=0)
    minutes = Column(Integer, default=0)
    goals_conceded = Column(Integer, default=0)
    creativity = Column(DECIMAL(10,2), default=0)
    influence = Column(DECIMAL(10,2), default=0)
    threat = Column(DECIMAL(10,2), default=0)
    bonus = Column(Integer, default=0)
    bps = Column(Integer, default=0)
    ict_index = Column(DECIMAL(10,2), default=0)
    clean_sheets = Column(Integer, default=0)
    red_cards = Column(Integer, default=0)
    yellow_cards = Column(Integer, default=0)
    selected_by_percent = Column(DECIMAL(5,2), default=0)
    now_cost = Column(Integer, default=0)
    element_type = Column(String(10), nullable=False)
    season_year = Column(String(10), nullable=False)


class ModelTrainingLog(Base, TimestampMixin):
    __tablename__ = "model_training_log"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    model_name = Column(String(100))
    data_size = Column(Integer)
    performance_metrics = Column(Text)  # JSON string
    model_path = Column(String(255))
    notes = Column(Text)
