"""Lightweight data models used by the tests.

The full project defines SQLAlchemy models inside ``backend.database``.
Importing those requires a number of third‑party dependencies which may
not be available in the execution environment.  The unit tests only need
simple attribute containers for type hints and mocks, so we provide
minimal ``dataclass`` implementations here.  This keeps the public API
compatible with the expected ``app.models`` module without pulling in the
heavy database stack.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Team:
    """Simplified representation of a football team."""

    id: int
    name: str
    tla: Optional[str] = None
    area_name: Optional[str] = None


@dataclass
class Match:
    """Minimal match record used for type annotations and mocks."""

    id: int
    season: int
    utc_date: datetime
    matchday: int
    status: str
    stage: Optional[str] = None
    home_team_id: int = 0
    away_team_id: int = 0
    home_score: Optional[int] = None
    away_score: Optional[int] = None
    venue: Optional[str] = None
    city: Optional[str] = None


@dataclass
class StandingsSnapshot:
    """Snapshot of league standings for a particular team and matchday."""

    id: int
    season: int
    matchday: int
    team_id: int
    position: int
    played_games: int
    points: int
    goals_for: int
    goals_against: int
    goal_diff: int

