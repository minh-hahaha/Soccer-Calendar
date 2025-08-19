from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database.db import Base


class Team(Base):
    __tablename__ = "teams"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    tla = Column(String(10))
    area_name = Column(String(255))
    
    # Relationships
    home_matches = relationship("Match", foreign_keys="Match.home_team_id", back_populates="home_team")
    away_matches = relationship("Match", foreign_keys="Match.away_team_id", back_populates="away_team")
    standings = relationship("StandingsSnapshot", back_populates="team")


class Match(Base):
    __tablename__ = "matches"
    
    id = Column(Integer, primary_key=True)
    season = Column(Integer, nullable=False)
    utc_date = Column(DateTime(timezone=True), nullable=False)
    matchday = Column(Integer, nullable=False)
    status = Column(String(50), nullable=False)
    stage = Column(String(50))
    home_team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    away_team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    home_score = Column(Integer)
    away_score = Column(Integer)
    venue = Column(String(255))
    city = Column(String(255))
    
    # Relationships
    home_team = relationship("Team", foreign_keys=[home_team_id], back_populates="home_matches")
    away_team = relationship("Team", foreign_keys=[away_team_id], back_populates="away_matches")
    lineups = relationship("Lineup", back_populates="match")
    team_statistics = relationship("TeamStatistics", back_populates="match")
    features = relationship("FeaturesMatch", back_populates="match", uselist=False)
    prediction = relationship("Prediction", back_populates="match", uselist=False)


class StandingsSnapshot(Base):
    __tablename__ = "standings_snapshots"
    
    id = Column(Integer, primary_key=True)
    season = Column(Integer, nullable=False)
    matchday = Column(Integer, nullable=False)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    position = Column(Integer, nullable=False)
    played_games = Column(Integer, nullable=False)
    points = Column(Integer, nullable=False)
    goals_for = Column(Integer, nullable=False)
    goals_against = Column(Integer, nullable=False)
    goal_diff = Column(Integer, nullable=False)
    snapshot_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    team = relationship("Team", back_populates="standings")


class HeadToHeadCache(Base):
    __tablename__ = "head_to_head_cache"
    
    home_team_id = Column(Integer, ForeignKey("teams.id"), primary_key=True)
    away_team_id = Column(Integer, ForeignKey("teams.id"), primary_key=True)
    season = Column(Integer, primary_key=True)
    computed_at = Column(DateTime(timezone=True), server_default=func.now())
    payload = Column(JSON)


class Lineup(Base):
    __tablename__ = "lineups"
    
    id = Column(Integer, primary_key=True)
    match_id = Column(Integer, ForeignKey("matches.id"), nullable=False)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    person_id = Column(Integer, nullable=False)
    name = Column(String(255), nullable=False)
    position = Column(String(100), nullable=False)
    shirt_number = Column(Integer)
    is_starter = Column(Boolean, default=False)  # True for lineup, False for bench
    minutes = Column(Integer, default=0)
    yellow_cards = Column(Integer, default=0)
    red_cards = Column(Integer, default=0)
    
    # Relationships
    match = relationship("Match", back_populates="lineups")


class TeamStatistics(Base): # can retrain model with this info later
    __tablename__ = "team_statistics"
    
    id = Column(Integer, primary_key=True)
    match_id = Column(Integer, ForeignKey("matches.id"), nullable=False)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    corner_kicks = Column(Integer, default=0)
    free_kicks = Column(Integer, default=0)
    goal_kicks = Column(Integer, default=0)
    offsides = Column(Integer, default=0)
    fouls = Column(Integer, default=0)
    ball_possession = Column(Integer, default=0)  # Percentage
    saves = Column(Integer, default=0)
    throw_ins = Column(Integer, default=0)
    shots = Column(Integer, default=0)
    shots_on_goal = Column(Integer, default=0)
    shots_off_goal = Column(Integer, default=0)
    yellow_cards = Column(Integer, default=0)
    yellow_red_cards = Column(Integer, default=0)
    red_cards = Column(Integer, default=0)
    
    # Relationships
    match = relationship("Match", back_populates="team_statistics")
    team = relationship("Team")


class FeaturesMatch(Base):
    __tablename__ = "features_match"
    
    match_id = Column(Integer, ForeignKey("matches.id"), primary_key=True)
    feature_json = Column(JSON, nullable=False)
    built_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    match = relationship("Match", back_populates="features")


class Prediction(Base):
    __tablename__ = "predictions"
    
    match_id = Column(Integer, ForeignKey("matches.id"), primary_key=True)
    p_home = Column(Float, nullable=False)
    p_draw = Column(Float, nullable=False)
    p_away = Column(Float, nullable=False)
    model_version = Column(String(100), nullable=False)
    calibrated = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    match = relationship("Match", back_populates="prediction")
