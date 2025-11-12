"""
Test configuration and fixtures
"""
import pytest
import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../src'))

from data.database import get_db
from data.models import Base
from backend.main import app

# Test database URL
TEST_DATABASE_URL = "postgresql://trader:trading123@localhost:5432/trading_bot_test"

# Create test engine
test_engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session")
def db_engine():
    """Database engine fixture"""
    # Create test database tables
    Base.metadata.create_all(bind=test_engine)
    yield test_engine
    # Cleanup
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def db_session(db_engine):
    """Database session fixture"""
    connection = db_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def client(db_session):
    """FastAPI test client"""
    def override_get_db():
        try:
            yield db_session
        finally:
            db_session.close()
    
    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture
def sample_market_data():
    """Sample market data for testing"""
    return {
        'symbol': 'BTCUSDT',
        'timestamp': '2025-11-06T10:00:00Z',
        'open_price': 50000.0,
        'high_price': 51000.0,
        'low_price': 49500.0,
        'close_price': 50500.0,
        'volume': 1000.0
    }


@pytest.fixture
def sample_trade_request():
    """Sample trade request for testing"""
    return {
        'symbol': 'BTCUSDT',
        'side': 'buy',
        'quantity': 0.001,
        'price': 50000.0,
        'strategy': 'test_strategy'
    }


@pytest.fixture
def auth_headers():
    """Mock authentication headers"""
    return {'Authorization': 'Bearer test_token'}