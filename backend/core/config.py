import os
from functools import lru_cache
from typing import Optional, List
from pydantic_settings import BaseSettings
from pydantic import Field
from pydantic.networks import PostgresDsn


class Settings(BaseSettings):
    """Application settings with validation"""

    
    # Application
    APP_NAME: str = "Football AI Analytics"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = Field(default=False, env="DEBUG")
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")
    
    # API Configuration
    API_HOST: str = Field(default="0.0.0.0", env="API_HOST")
    API_PORT: int = Field(default=8000, env="API_PORT")
    
    # External APIs
    FD_API_KEY: str = Field(..., env="FD_API_KEY")
    FD_API_BASE_URL: str = Field(default="https://api.football-data.org/v4", env="FD_API_BASE_URL")
    FPL_API_BASE_URL: str = Field(default="https://fantasy.premierleague.com/api", env="FPL_API_BASE_URL")
    
    # Database
    DATABASE_URL: str = Field(..., env="DATABASE_URL")
    DB_ECHO: bool = Field(default=False, env="DB_ECHO")
    
    # ML Configuration
    MODEL_PATH: str = Field(default="./data/models", env="MODEL_PATH")
    HISTORICAL_DATA_PATH: str = Field(default="./data", env="HISTORICAL_DATA_PATH")
    
    # Logging
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_FILE: str = Field(default="./data/logs/app.log", env="LOG_FILE")
    
    # Security
    SECRET_KEY: str = Field(default="dev-secret-key-change-in-production", env="SECRET_KEY")
    CORS_ORIGINS: List[str] = Field(default=["*"], env="CORS_ORIGINS")

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() == "production"
    
    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT.lower() in ["development", "dev"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "allow"  


@lru_cache()
def get_settings() -> Settings:
    return Settings()
