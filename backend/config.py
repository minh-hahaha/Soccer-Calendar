import os
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # API Configuration
    fd_api_key: str = os.getenv("FD_API_KEY", "")
    db_uri: str = os.getenv("DB_URI", "postgresql+psycopg://postgres:postgres@localhost:5432/footy")
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    model_dir: str = os.getenv("MODEL_DIR", "../artifacts")
    competition_code: str = os.getenv("COMPETITION_CODE", "PL")
    seasons: str = os.getenv("SEASONS", "2020,2021,2022,2023,2024")
    
    # Feature Engineering
    rolling_window: int = 5
    rank_delta_window: int = 5
    
    # Model Configuration
    random_seed: int = 42
    test_size: float = 0.2
    
    # API Configuration
    base_url: str = "https://api.football-data.org/v4"
    rate_limit_delay: float = 1.0  # seconds between requests
    
    @property
    def season_list(self) -> List[int]:
        return [int(s.strip()) for s in self.seasons.split(",")]
    
    class Config:
        env_file = ".env"


settings = Settings()
