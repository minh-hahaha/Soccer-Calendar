
"""Database Models"""

from .base import Base
from .football import Match, Team, Standing  # ← Football tables
from .fantasy import PlayerHistoricalData, ModelTrainingLog  # ← Fantasy tables