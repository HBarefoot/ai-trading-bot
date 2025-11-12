"""
Database connection and session management
"""
import os
from sqlalchemy import create_engine, MetaData, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from .models import Base
import logging

logger = logging.getLogger(__name__)

# Database URL from environment variable
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://trader:trading123@localhost:5432/trading_bot')

# Create engine with larger pool for concurrent operations
engine = create_engine(
    DATABASE_URL,
    echo=False,  # Set to False in production
    pool_size=20,  # Increased pool size for high-frequency trading
    max_overflow=40,  # Allow more overflow connections
    pool_pre_ping=True,
    pool_recycle=300,  # Recycle connections every 5 minutes
    pool_timeout=90,  # Increased timeout for busy periods
    connect_args={"connect_timeout": 10}
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Metadata
metadata = MetaData(schema='trading')


def create_tables():
    """Create all tables in the database"""
    try:
        # Create schema if it doesn't exist
        with engine.connect() as conn:
            conn.execute(text("CREATE SCHEMA IF NOT EXISTS trading"))
            conn.commit()
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating tables: {e}")
        raise


def get_db() -> Session:
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db_sync() -> Session:
    """Get database session synchronously"""
    return SessionLocal()


def test_connection():
    """Test database connection"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            logger.info("Database connection successful")
            return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False