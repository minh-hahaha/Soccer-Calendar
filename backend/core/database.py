"""Database connection"""

import logging
from contextlib import contextmanager
from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
from .config import get_settings
from .exceptions import DatabaseError

logger = logging.getLogger(__name__)
settings = get_settings()

# Create engine
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    echo=settings.DB_ECHO,
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class DatabaseManager:
    """Database manager with health monitoring"""
    
    def __init__(self):
        self.engine = engine
    
    def health_check(self) -> bool:
        """Check database connectivity"""
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
                return True
        except SQLAlchemyError as e:
            logger.error(f"Database health check failed: {str(e)}")
            return False
    
    def get_connection_info(self) -> dict:
        """Get database connection pool information"""
        pool = self.engine.pool
        return {
            "pool_size": pool.size(),
            "checked_in": pool.checkedin(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
        }


db_manager = DatabaseManager()


# Dependency for FastAPI
def get_db() -> Generator[Session, None, None]:
    """Database dependency for FastAPI"""
    db = SessionLocal()
    try:
        yield db
    except SQLAlchemyError as e:
        logger.error(f"Database error: {str(e)}")
        db.rollback()
        raise DatabaseError(f"Database operation failed: {str(e)}")
    finally:
        db.close()


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """Context manager for database session"""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Database session error: {str(e)}")
        raise
    finally:
        session.close()


def init_database():
    """Initialize database tables"""
    try:
        from backend.models.database.base import Base
        from backend.models.database import football, fantasy  # Import both modules
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
        return True
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        raise DatabaseError(f"Database initialization failed: {str(e)}")
    
def reset_database():
    """Reset database by dropping all tables and recreating them"""
    try:
        from backend.models.database.base import Base
        from backend.models.database import football, fantasy  # Import both modules
        from sqlalchemy import text
        
        logger.info("Starting database reset...")
        
        # Get all table names and drop them with CASCADE
        with engine.connect() as conn:
            # Get all tables in the public schema
            result = conn.execute(text("""
                SELECT tablename FROM pg_tables 
                WHERE schemaname = 'public'
            """))
            tables = [row[0] for row in result]
            
            # Drop each table with CASCADE
            for table in tables:
                conn.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE"))
            
            conn.commit()
        
        logger.info("All tables dropped successfully with CASCADE")
        
        # Recreate all tables
        Base.metadata.create_all(bind=engine)
        logger.info("All tables recreated successfully")
        
        return True
        
    except Exception as e:
        logger.error(f"Database reset failed: {str(e)}")
        raise DatabaseError(f"Database reset failed: {str(e)}")