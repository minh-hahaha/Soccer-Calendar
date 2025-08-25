"""Football Data Models"""
from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean
from .base import Base


class Match(Base):
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True)
    date = Column(DateTime, nullable=False)
    home_team = Column(String, nullable=False)
    away_team = Column(String, nullable=False)
    home_score = Column(Integer)
    away_score = Column(Integer)
    matchday = Column(Integer)
    status = Column(String)
    home_team_crest = Column(String)
    away_team_crest = Column(String)
    season = Column(Integer)


class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    short_name = Column(String, nullable=False)
    tla = Column(String)
    crest = Column(String)
    season = Column(String)


class Standing(Base):
    __tablename__ = "standings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    season = Column(String, nullable=False)
    matchday = Column(Integer)
    position = Column(Integer, nullable=False)
    team = Column(String, nullable=False)
    crest = Column(String)
    played_games = Column(Integer)
    won = Column(Integer)
    draw = Column(Integer)
    lost = Column(Integer)
    points = Column(Integer)
    goal_difference = Column(Integer)
    form = Column(String)