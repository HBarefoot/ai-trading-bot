#!/usr/bin/env python3
"""
Initialize database tables on Railway
Run this locally to create tables in Railway's PostgreSQL database
"""
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Set DATABASE_URL for Railway PostgreSQL
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:password@localhost:5432/trading')
os.environ['DATABASE_URL'] = DATABASE_URL

print(f"Connecting to database: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'localhost'}")

from src.data.database import engine, create_tables
from sqlalchemy import text

def init_railway_db():
    """Initialize database schema and tables on Railway"""
    try:
        # Test connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"✓ Connected to PostgreSQL: {version.split(',')[0]}")
            
            # Create schema
            print("\nCreating 'trading' schema...")
            conn.execute(text("CREATE SCHEMA IF NOT EXISTS trading"))
            conn.commit()
            print("✓ Schema 'trading' ready")
        
        # Create tables
        print("\nCreating tables...")
        create_tables()
        print("✓ All tables created successfully")
        
        # Verify tables
        print("\nVerifying tables...")
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'trading'
                ORDER BY table_name
            """))
            tables = [row[0] for row in result.fetchall()]
            
            if tables:
                print(f"✓ Found {len(tables)} tables:")
                for table in tables:
                    print(f"  - trading.{table}")
                return True
            else:
                print("✗ No tables found!")
                return False
                
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Railway Database Initialization")
    print("=" * 60)
    
    if not os.getenv('DATABASE_URL'):
        print("\n⚠️  Warning: DATABASE_URL environment variable not set!")
        print("Set it to your Railway PostgreSQL connection string:")
        print("export DATABASE_URL='postgresql://...'")
        sys.exit(1)
    
    success = init_railway_db()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ Database initialization completed successfully!")
    else:
        print("❌ Database initialization failed!")
    print("=" * 60)
    
    sys.exit(0 if success else 1)
