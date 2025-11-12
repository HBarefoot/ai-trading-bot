"""
Integration test suite for complete system workflow
"""
import pytest
import time
from datetime import datetime
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '../src'))


class TestSystemIntegration:
    """Integration tests for complete workflows"""
    
    @pytest.mark.integration
    def test_data_to_api_workflow(self, client, db_session):
        """Test complete data collection to API workflow"""
        from data.models import MarketData
        
        # Step 1: Add market data (simulating data collection)
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
        
        # Step 2: Verify data via API
        response = client.get("/api/market-data/BTCUSDT/latest")
        assert response.status_code == 200
        
        data = response.json()
        assert data["close_price"] == 50500.0
    
    @pytest.mark.integration
    def test_trading_workflow(self, client, db_session, auth_headers):
        """Test complete trading workflow"""
        from data.models import MarketData, Trade, Portfolio
        
        # Step 1: Add market data
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
        
        # Step 2: Execute buy trade
        trade_request = {
            "symbol": "ETHUSDT",
            "side": "buy",
            "quantity": 1.0,
            "strategy": "integration_test"
        }
        
        response = client.post("/api/trades", json=trade_request, headers=auth_headers)
        assert response.status_code == 200
        
        trade_data = response.json()
        assert trade_data["side"] == "buy"
        
        # Step 3: Check portfolio was updated
        response = client.get("/api/portfolio", headers=auth_headers)
        assert response.status_code == 200
        
        portfolio = response.json()
        eth_position = next((p for p in portfolio if p["symbol"] == "ETHUSDT"), None)
        assert eth_position is not None
        assert eth_position["quantity"] == 1.0
        
        # Step 4: Execute sell trade
        sell_request = {
            "symbol": "ETHUSDT",
            "side": "sell",
            "quantity": 0.5,
            "strategy": "integration_test"
        }
        
        response = client.post("/api/trades", json=sell_request, headers=auth_headers)
        assert response.status_code == 200
        
        # Step 5: Verify portfolio updated
        response = client.get("/api/portfolio", headers=auth_headers)
        portfolio = response.json()
        eth_position = next((p for p in portfolio if p["symbol"] == "ETHUSDT"), None)
        assert eth_position["quantity"] == 0.5  # Reduced by sell
    
    @pytest.mark.integration
    def test_api_health_and_stats(self, client, db_session):
        """Test API health and statistics endpoints"""
        # Health check
        response = client.get("/health")
        assert response.status_code == 200
        
        health_data = response.json()
        assert health_data["status"] == "healthy"
        
        # Stats endpoint
        response = client.get("/api/stats/summary")
        assert response.status_code == 200
        
        stats = response.json()
        assert "total_market_data_points" in stats
        assert "api_version" in stats
    
    @pytest.mark.integration
    @pytest.mark.slow
    def test_performance_under_load(self, client, db_session):
        """Test API performance with multiple requests"""
        from data.models import MarketData
        
        # Add test data
        for i in range(10):
            market_data = MarketData(
                symbol='BTCUSDT',
                timestamp=datetime.utcnow(),
                open_price=50000 + i,
                high_price=51000 + i,
                low_price=49500 + i,
                close_price=50500 + i,
                volume=1000 + i
            )
            db_session.add(market_data)
        db_session.commit()
        
        # Test multiple concurrent requests
        start_time = time.time()
        responses = []
        
        for _ in range(10):
            response = client.get("/api/market-data/BTCUSDT")
            responses.append(response)
        
        end_time = time.time()
        
        # All requests should succeed
        for response in responses:
            assert response.status_code == 200
        
        # Should complete in reasonable time (< 5 seconds for 10 requests)
        total_time = end_time - start_time
        assert total_time < 5.0


class TestErrorHandling:
    """Test error handling and edge cases"""
    
    def test_invalid_symbol_handling(self, client):
        """Test handling of invalid symbols"""
        response = client.get("/api/market-data/INVALID/latest")
        assert response.status_code == 404
    
    def test_malformed_trade_request(self, client, auth_headers):
        """Test handling of malformed trade requests"""
        # Missing required fields
        invalid_request = {"symbol": "BTCUSDT"}
        
        response = client.post("/api/trades", json=invalid_request, headers=auth_headers)
        assert response.status_code == 422  # Validation error
    
    def test_unauthorized_access(self, client):
        """Test unauthorized access to protected endpoints"""
        trade_request = {
            "symbol": "BTCUSDT",
            "side": "buy",
            "quantity": 0.001
        }
        
        # Request without auth headers
        response = client.post("/api/trades", json=trade_request)
        assert response.status_code == 403  # Forbidden
    
    def test_database_connection_error_simulation(self, client):
        """Test API behavior when database is unavailable"""
        # This would require mocking database connection failure
        # For now, just test that error responses are properly formatted
        response = client.get("/api/market-data/NONEXISTENT/latest")
        
        if response.status_code != 200:
            error_data = response.json()
            assert "detail" in error_data or "error" in error_data


class TestDataConsistency:
    """Test data consistency across the system"""
    
    @pytest.mark.integration
    def test_trade_portfolio_consistency(self, client, db_session, auth_headers):
        """Test that trades and portfolio remain consistent"""
        from data.models import MarketData
        
        # Add market data
        market_data = MarketData(
            symbol='ADAUSDT',
            timestamp=datetime.utcnow(),
            open_price=1.0,
            high_price=1.1,
            low_price=0.95,
            close_price=1.05,
            volume=10000.0
        )
        db_session.add(market_data)
        db_session.commit()
        
        # Execute multiple trades
        trades = [
            {"symbol": "ADAUSDT", "side": "buy", "quantity": 100.0},
            {"symbol": "ADAUSDT", "side": "buy", "quantity": 50.0},
            {"symbol": "ADAUSDT", "side": "sell", "quantity": 30.0}
        ]
        
        executed_trades = []
        for trade in trades:
            response = client.post("/api/trades", json=trade, headers=auth_headers)
            assert response.status_code == 200
            executed_trades.append(response.json())
        
        # Check final portfolio position
        response = client.get("/api/portfolio", headers=auth_headers)
        portfolio = response.json()
        ada_position = next((p for p in portfolio if p["symbol"] == "ADAUSDT"), None)
        
        # Should have 120 total (100 + 50 - 30)
        assert ada_position is not None
        assert ada_position["quantity"] == 120.0
    
    def test_timestamp_consistency(self, client, db_session):
        """Test that timestamps are consistent across the system"""
        from data.models import MarketData
        
        before_time = datetime.utcnow()
        
        # Add market data
        market_data = MarketData(
            symbol='DOTUSDT',
            timestamp=datetime.utcnow(),
            open_price=25.0,
            high_price=26.0,
            low_price=24.5,
            close_price=25.5,
            volume=2000.0
        )
        db_session.add(market_data)
        db_session.commit()
        
        after_time = datetime.utcnow()
        
        # Retrieve via API
        response = client.get("/api/market-data/DOTUSDT/latest")
        assert response.status_code == 200
        
        data = response.json()
        api_timestamp = datetime.fromisoformat(data["timestamp"].replace('Z', '+00:00'))
        
        # Timestamp should be between before and after times
        assert before_time <= api_timestamp.replace(tzinfo=None) <= after_time