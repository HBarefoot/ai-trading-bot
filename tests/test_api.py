"""
Test suite for FastAPI backend endpoints
"""
import pytest
import json
from datetime import datetime
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '../src'))

from data.models import MarketData, Trade


class TestAPIEndpoints:
    """Test FastAPI endpoints"""
    
    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data
    
    def test_market_data_endpoint_empty(self, client):
        """Test market data endpoint with no data"""
        response = client.get("/api/market-data/BTCUSDT")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0  # No data initially
    
    def test_market_data_endpoint_with_data(self, client, db_session):
        """Test market data endpoint with data"""
        # Add test data
        market_data = MarketData(
            symbol='BTCUSDT',
            timestamp=datetime.utcnow(),
            open_price=50000.0,
            high_price=51000.0,
            low_price=49500.0,
            close_price=50500.0,
            volume=1000.0
        )
        db_session.add(market_data)
        db_session.commit()
        
        response = client.get("/api/market-data/BTCUSDT")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 1
        assert data[0]["symbol"] == "BTCUSDT"
        assert data[0]["close_price"] == 50500.0
    
    def test_latest_price_endpoint(self, client, db_session):
        """Test latest price endpoint"""
        # Add test data
        market_data = MarketData(
            symbol='ETHUSDT',
            timestamp=datetime.utcnow(),
            open_price=3000.0,
            high_price=3100.0,
            low_price=2950.0,
            close_price=3050.0,
            volume=500.0
        )
        db_session.add(market_data)
        db_session.commit()
        
        response = client.get("/api/market-data/ETHUSDT/latest")
        assert response.status_code == 200
        
        data = response.json()
        assert data["symbol"] == "ETHUSDT"
        assert data["close_price"] == 3050.0
    
    def test_latest_price_not_found(self, client):
        """Test latest price for non-existent symbol"""
        response = client.get("/api/market-data/NONEXISTENT/latest")
        assert response.status_code == 404
        
        data = response.json()
        assert "detail" in data
    
    def test_execute_trade_endpoint(self, client, db_session, auth_headers):
        """Test trade execution endpoint"""
        # Add market data first
        market_data = MarketData(
            symbol='BTCUSDT',
            timestamp=datetime.utcnow(),
            open_price=50000.0,
            high_price=51000.0,
            low_price=49500.0,
            close_price=50500.0,
            volume=1000.0
        )
        db_session.add(market_data)
        db_session.commit()
        
        trade_request = {
            "symbol": "BTCUSDT",
            "side": "buy",
            "quantity": 0.001,
            "strategy": "test_strategy"
        }
        
        response = client.post(
            "/api/trades",
            json=trade_request,
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["symbol"] == "BTCUSDT"
        assert data["side"] == "buy"
        assert data["quantity"] == 0.001
    
    def test_invalid_trade_request(self, client, auth_headers):
        """Test invalid trade request"""
        trade_request = {
            "symbol": "BTCUSDT",
            "side": "invalid_side",  # Invalid side
            "quantity": 0.001
        }
        
        response = client.post(
            "/api/trades",
            json=trade_request,
            headers=auth_headers
        )
        assert response.status_code == 400
    
    def test_negative_quantity_trade(self, client, auth_headers):
        """Test trade with negative quantity"""
        trade_request = {
            "symbol": "BTCUSDT",
            "side": "buy",
            "quantity": -0.001  # Negative quantity
        }
        
        response = client.post(
            "/api/trades",
            json=trade_request,
            headers=auth_headers
        )
        assert response.status_code == 400
    
    def test_get_trades_endpoint(self, client, db_session, auth_headers):
        """Test get trades endpoint"""
        # Add test trade
        trade = Trade(
            symbol='BTCUSDT',
            side='buy',
            quantity=0.001,
            price=50000.0,
            timestamp=datetime.utcnow(),
            strategy='test_strategy'
        )
        db_session.add(trade)
        db_session.commit()
        
        response = client.get("/api/trades", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 1
        assert data[0]["symbol"] == "BTCUSDT"
        assert data[0]["side"] == "buy"
    
    def test_portfolio_endpoint(self, client, auth_headers):
        """Test portfolio endpoint"""
        response = client.get("/api/portfolio", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
    
    def test_portfolio_value_endpoint(self, client, auth_headers):
        """Test portfolio value endpoint"""
        response = client.get("/api/portfolio/value", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "total_value_usdt" in data
        assert "timestamp" in data
    
    def test_strategies_endpoint(self, client):
        """Test strategies endpoint"""
        response = client.get("/api/strategies")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
    
    def test_predictions_endpoint(self, client):
        """Test ML predictions endpoint"""
        response = client.get("/api/predictions/BTCUSDT")
        assert response.status_code == 200
        
        data = response.json()
        assert "symbol" in data
        assert "predicted_price" in data
        assert "confidence" in data
    
    def test_summary_stats_endpoint(self, client):
        """Test summary statistics endpoint"""
        response = client.get("/api/stats/summary")
        assert response.status_code == 200
        
        data = response.json()
        assert "total_market_data_points" in data
        assert "total_trades" in data
        assert "api_version" in data