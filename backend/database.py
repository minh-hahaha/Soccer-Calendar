from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, JSON, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/fantasy_football")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class BootstrapData(Base):
    """Model to store FPL bootstrap data"""
    __tablename__ = "bootstrap_data"
    
    id = Column(Integer, primary_key=True, index=True)
    gameweek = Column(Integer, nullable=False, index=True)
    data = Column(JSON, nullable=False)  # Store the complete bootstrap data
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_current = Column(Boolean, default=True)  # Only one record should be current
    
    def is_fresh(self, max_age_hours: int = 6) -> bool:
        """Check if data is fresh (less than max_age_hours old)"""
        if not self.updated_at:
            return False
        return datetime.utcnow() - self.updated_at < timedelta(hours=max_age_hours)


class FixturesData(Base):
    """Model to store FPL fixtures data"""
    __tablename__ = "fixtures_data"
    
    id = Column(Integer, primary_key=True, index=True)
    gameweek = Column(Integer, nullable=False, index=True)
    data = Column(JSON, nullable=False)  # Store the complete fixtures data
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_current = Column(Boolean, default=True)  # Only one record should be current
    
    def is_fresh(self, max_age_hours: int = 6) -> bool:
        """Check if data is fresh (less than max_age_hours old)"""
        if not self.updated_at:
            return False
        return datetime.utcnow() - self.updated_at < timedelta(hours=max_age_hours)


class AnalysisCache(Base):
    """Model to cache analysis results"""
    __tablename__ = "analysis_cache"
    
    id = Column(Integer, primary_key=True, index=True)
    analysis_type = Column(String, nullable=False, index=True)
    gameweek = Column(Integer, nullable=False, index=True)
    parameters = Column(JSON, nullable=False)  # Store analysis parameters
    result = Column(JSON, nullable=False)  # Store analysis result
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)  # When cache expires
    
    def is_expired(self) -> bool:
        """Check if cache entry has expired"""
        return datetime.utcnow() > self.expires_at


class FootballFixtures(Base):
    """Model to store football fixtures data"""
    __tablename__ = "football_fixtures"
    
    id = Column(Integer, primary_key=True, index=True)
    season = Column(String, nullable=False, index=True)
    matchday = Column(Integer, nullable=True, index=True)
    status = Column(String, nullable=True, index=True)
    team_filter = Column(String, nullable=True, index=True)
    data = Column(JSON, nullable=False)  # Store the fixtures data
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_current = Column(Boolean, default=True)  # Only one record should be current per filter
    
    def is_fresh(self, max_age_hours: int = 2) -> bool:
        """Check if data is fresh (less than max_age_hours old)"""
        if not self.updated_at:
            return False
        return datetime.utcnow() - self.updated_at < timedelta(hours=max_age_hours)


class FootballTeams(Base):
    """Model to store football teams data"""
    __tablename__ = "football_teams"
    
    id = Column(Integer, primary_key=True, index=True)
    season = Column(String, nullable=False, index=True)
    data = Column(JSON, nullable=False)  # Store the teams data
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_current = Column(Boolean, default=True)  # Only one record should be current per season
    
    def is_fresh(self, max_age_hours: int = 24) -> bool:
        """Check if data is fresh (less than max_age_hours old)"""
        if not self.updated_at:
            return False
        return datetime.utcnow() - self.updated_at < timedelta(hours=max_age_hours)


class FootballStandings(Base):
    """Model to store football standings data"""
    __tablename__ = "football_standings"
    
    id = Column(Integer, primary_key=True, index=True)
    season = Column(String, nullable=False, index=True)
    matchday = Column(Integer, nullable=True, index=True)
    data = Column(JSON, nullable=False)  # Store the standings data
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_current = Column(Boolean, default=True)  # Only one record should be current per season/matchday
    
    def is_fresh(self, max_age_hours: int = 4) -> bool:
        """Check if data is fresh (less than max_age_hours old)"""
        if not self.updated_at:
            return False
        return datetime.utcnow() - self.updated_at < timedelta(hours=max_age_hours)


class FootballHead2Head(Base):
    """Model to store football head-to-head data"""
    __tablename__ = "football_head2head"
    
    id = Column(Integer, primary_key=True, index=True)
    match_id = Column(Integer, nullable=False, index=True)
    data = Column(JSON, nullable=False)  # Store the head-to-head data
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)  # When cache expires
    
    def is_fresh(self, max_age_hours: int = 24) -> bool:
        """Check if data is fresh (less than max_age_hours old)"""
        if not self.updated_at:
            return False
        return datetime.utcnow() - self.updated_at < timedelta(hours=max_age_hours)
    
    def is_expired(self) -> bool:
        """Check if cache entry has expired"""
        return datetime.utcnow() > self.expires_at


# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Database utility functions
class DatabaseManager:
    def __init__(self):
        self.engine = engine
        self.SessionLocal = SessionLocal
    
    def create_tables(self):
        """Create all database tables"""
        Base.metadata.create_all(bind=self.engine)
    
    def get_current_bootstrap_data(self, db) -> Optional[BootstrapData]:
        """Get current bootstrap data from database"""
        return db.query(BootstrapData).filter(BootstrapData.is_current == True).first()
    
    def get_current_fixtures_data(self, db) -> Optional[FixturesData]:
        """Get current fixtures data from database"""
        return db.query(FixturesData).filter(FixturesData.is_current == True).first()
    
    def save_bootstrap_data(self, db, gameweek: int, data: Dict[str, Any]):
        """Save bootstrap data to database"""
        # Mark existing current data as not current
        db.query(BootstrapData).filter(BootstrapData.is_current == True).update({"is_current": False})
        
        # Create new record
        bootstrap_data = BootstrapData(
            gameweek=gameweek,
            data=data,
            is_current=True
        )
        db.add(bootstrap_data)
        db.commit()
        return bootstrap_data
    
    def save_fixtures_data(self, db, gameweek: int, data: Dict[str, Any]):
        """Save fixtures data to database"""
        # Mark existing current data as not current
        db.query(FixturesData).filter(FixturesData.is_current == True).update({"is_current": False})
        
        # Create new record
        fixtures_data = FixturesData(
            gameweek=gameweek,
            data=data,
            is_current=True
        )
        db.add(fixtures_data)
        db.commit()
        return fixtures_data
    
    def get_cached_analysis(self, db, analysis_type: str, gameweek: int, parameters: Dict[str, Any]) -> Optional[AnalysisCache]:
        """Get cached analysis result"""
        # Simple parameter matching - in production you might want more sophisticated matching
        cache_entry = db.query(AnalysisCache).filter(
            AnalysisCache.analysis_type == analysis_type,
            AnalysisCache.gameweek == gameweek,
            AnalysisCache.parameters == parameters,
            AnalysisCache.expires_at > datetime.utcnow()
        ).first()
        
        return cache_entry if cache_entry and not cache_entry.is_expired() else None
    
    def save_analysis_cache(self, db, analysis_type: str, gameweek: int, parameters: Dict[str, Any], result: Dict[str, Any], cache_duration_hours: int = 2):
        """Save analysis result to cache"""
        expires_at = datetime.utcnow() + timedelta(hours=cache_duration_hours)
        
        cache_entry = AnalysisCache(
            analysis_type=analysis_type,
            gameweek=gameweek,
            parameters=parameters,
            result=result,
            expires_at=expires_at
        )
        
        db.add(cache_entry)
        db.commit()
        return cache_entry
    
    def cleanup_expired_cache(self, db):
        """Remove expired cache entries"""
        db.query(AnalysisCache).filter(AnalysisCache.expires_at < datetime.utcnow()).delete()
        db.commit()
    
    # Football data methods
    def get_football_fixtures(self, db, season: str, matchday: Optional[int] = None, 
                             status: Optional[str] = None, team_filter: Optional[str] = None) -> Optional[FootballFixtures]:
        """Get football fixtures from database"""
        query = db.query(FootballFixtures).filter(
            FootballFixtures.season == season,
            FootballFixtures.is_current == True
        )
        
        if matchday is not None:
            query = query.filter(FootballFixtures.matchday == matchday)
        if status is not None:
            query = query.filter(FootballFixtures.status == status)
        if team_filter is not None:
            query = query.filter(FootballFixtures.team_filter == team_filter)
        
        return query.first()
    
    def save_football_fixtures(self, db, season: str, data: Dict[str, Any], 
                              matchday: Optional[int] = None, status: Optional[str] = None, 
                              team_filter: Optional[str] = None):
        """Save football fixtures to database"""
        # Mark existing current data as not current for this filter combination
        query = db.query(FootballFixtures).filter(
            FootballFixtures.season == season,
            FootballFixtures.is_current == True
        )
        
        if matchday is not None:
            query = query.filter(FootballFixtures.matchday == matchday)
        if status is not None:
            query = query.filter(FootballFixtures.status == status)
        if team_filter is not None:
            query = query.filter(FootballFixtures.team_filter == team_filter)
        
        query.update({"is_current": False})
        
        # Create new record
        fixtures_data = FootballFixtures(
            season=season,
            matchday=matchday,
            status=status,
            team_filter=team_filter,
            data=data,
            is_current=True
        )
        db.add(fixtures_data)
        db.commit()
        return fixtures_data
    
    def get_football_teams(self, db, season: str) -> Optional[FootballTeams]:
        """Get football teams from database"""
        return db.query(FootballTeams).filter(
            FootballTeams.season == season,
            FootballTeams.is_current == True
        ).first()
    
    def save_football_teams(self, db, season: str, data: Dict[str, Any]):
        """Save football teams to database"""
        # Mark existing current data as not current
        db.query(FootballTeams).filter(
            FootballTeams.season == season,
            FootballTeams.is_current == True
        ).update({"is_current": False})
        
        # Create new record
        teams_data = FootballTeams(
            season=season,
            data=data,
            is_current=True
        )
        db.add(teams_data)
        db.commit()
        return teams_data
    
    def get_football_standings(self, db, season: str, matchday: Optional[int] = None) -> Optional[FootballStandings]:
        """Get football standings from database"""
        query = db.query(FootballStandings).filter(
            FootballStandings.season == season,
            FootballStandings.is_current == True
        )
        
        if matchday is not None:
            query = query.filter(FootballStandings.matchday == matchday)
        
        return query.first()
    
    def save_football_standings(self, db, season: str, data: Dict[str, Any], matchday: Optional[int] = None):
        """Save football standings to database"""
        # Mark existing current data as not current
        query = db.query(FootballStandings).filter(
            FootballStandings.season == season,
            FootballStandings.is_current == True
        )
        
        if matchday is not None:
            query = query.filter(FootballStandings.matchday == matchday)
        
        query.update({"is_current": False})
        
        # Create new record
        standings_data = FootballStandings(
            season=season,
            matchday=matchday,
            data=data,
            is_current=True
        )
        db.add(standings_data)
        db.commit()
        return standings_data
    
    def get_football_head2head(self, db, match_id: int) -> Optional[FootballHead2Head]:
        """Get football head-to-head data from database"""
        return db.query(FootballHead2Head).filter(
            FootballHead2Head.match_id == match_id,
            FootballHead2Head.expires_at > datetime.utcnow()
        ).first()
    
    def save_football_head2head(self, db, match_id: int, data: Dict[str, Any], cache_duration_hours: int = 24):
        """Save football head-to-head data to database"""
        expires_at = datetime.utcnow() + timedelta(hours=cache_duration_hours)
        
        head2head_data = FootballHead2Head(
            match_id=match_id,
            data=data,
            expires_at=expires_at
        )
        
        db.add(head2head_data)
        db.commit()
        return head2head_data
    
    def cleanup_expired_football_cache(self, db):
        """Remove expired football cache entries"""
        db.query(FootballHead2Head).filter(FootballHead2Head.expires_at < datetime.utcnow()).delete()
        db.commit()


# Global database manager instance
db_manager = DatabaseManager()
