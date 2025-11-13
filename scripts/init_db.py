"""
Initialize database schema for Railway deployment
Run this script to create all necessary tables
"""
import sys
import os

# Add parent directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.data.database import create_tables, engine
from src.data.models import Base
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init_database():
    """Initialize database with schema and tables"""
    try:
        logger.info("Starting database initialization...")
        
        # Create schema
        with engine.connect() as conn:
            logger.info("Creating 'trading' schema...")
            conn.execute(text("CREATE SCHEMA IF NOT EXISTS trading"))
            conn.commit()
            logger.info("Schema created successfully")
        
        # Create all tables
        logger.info("Creating tables...")
        create_tables()
        logger.info("All tables created successfully!")
        
        # Verify tables exist
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'trading'
                ORDER BY table_name
            """))
            tables = [row[0] for row in result]
            logger.info(f"Created tables: {', '.join(tables)}")
        
        return True
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        return False


if __name__ == "__main__":
    success = init_database()
    sys.exit(0 if success else 1)
