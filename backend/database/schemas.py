from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime


class TeamSchema(BaseModel):
    id: int
    name: str
    tla: Optional[str] = None
    area_name: Optional[str] = None


class MatchSchema(BaseModel):
    id: int
    season: int
    utc_date: datetime
    matchday: int
    status: str
    stage: Optional[str] = None
    home_team_id: int
    away_team_id: int
    home_score: Optional[int] = None
    away_score: Optional[int] = None
    venue: Optional[str] = None
    city: Optional[str] = None


class StandingsSnapshotSchema(BaseModel):
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
    snapshot_at: datetime


class PredictionRequest(BaseModel):
    match_id: int


class BatchPredictionRequest(BaseModel):
    match_ids: List[int]


class TopFeature(BaseModel):
    name: str
    contribution: float


class PredictionResponse(BaseModel):
    match_id: int
    competition: str
    kickoff: datetime
    home_team_id: int
    away_team_id: int
    probs: Dict[str, float]  # {"home": 0.47, "draw": 0.26, "away": 0.27}
    top_features: List[TopFeature]
    model_version: str
    calibrated: bool
    data_quality: Optional[Dict[str, Any]] = None


class BatchPredictionResponse(BaseModel):
    predictions: List[PredictionResponse]


class FeaturesResponse(BaseModel):
    match_id: int
    features: Dict[str, Any]
    built_at: datetime


class HealthResponse(BaseModel):
    status: str
    model_version: Optional[str] = None
    database_connected: bool


# Additional schemas for missing models
class HeadToHeadCacheSchema(BaseModel):
    home_team_id: int
    away_team_id: int
    season: int
    computed_at: datetime
    payload: Optional[Dict[str, Any]] = None


class LineupSchema(BaseModel):
    id: int
    match_id: int
    team_id: int
    person_id: int
    name: str
    position: str
    shirt_number: Optional[int] = None
    is_starter: bool = False
    minutes: int = 0
    yellow_cards: int = 0
    red_cards: int = 0


class TeamStatisticsSchema(BaseModel):
    id: int
    match_id: int
    team_id: int
    corner_kicks: int = 0
    free_kicks: int = 0
    goal_kicks: int = 0
    offsides: int = 0
    fouls: int = 0
    ball_possession: int = 0  # Percentage
    saves: int = 0
    throw_ins: int = 0
    shots: int = 0
    shots_on_goal: int = 0
    shots_off_goal: int = 0
    yellow_cards: int = 0
    yellow_red_cards: int = 0
    red_cards: int = 0


class FeaturesMatchSchema(BaseModel):
    match_id: int
    feature_json: Dict[str, Any]
    built_at: datetime


class PredictionSchema(BaseModel):
    match_id: int
    p_home: float
    p_draw: float
    p_away: float
    model_version: str
    calibrated: bool = False
    created_at: datetime
