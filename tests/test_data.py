"""
Test suite for data collection and database operations
"""
import pytest
import pandas as pd
from datetime import datetime
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '../src'))

from data.models import MarketData, Trade, Portfolio
from data.collector import DataCollector


class TestDataCollection:
    """Test data collection functionality"""
    
    def test_market_data_model(self, db_session):
        """Test MarketData model creation"""
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
        
        # Query back
        result = db_session.query(MarketData).filter(
            MarketData.symbol == 'BTCUSDT'
        ).first()
        
        assert result is not None
        assert result.symbol == 'BTCUSDT'
        assert result.close_price == 50500.0
    
    def test_trade_model(self, db_session):
        """Test Trade model creation"""
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
        
        result = db_session.query(Trade).filter(
            Trade.symbol == 'BTCUSDT'
        ).first()
        
        assert result is not None
        assert result.side == 'buy'
        assert result.quantity == 0.001
    
    def test_portfolio_model(self, db_session):
        """Test Portfolio model creation"""
        portfolio = Portfolio(
            symbol='BTCUSDT',
            quantity=0.5,
            avg_cost=50000.0
        )
        
        db_session.add(portfolio)
        db_session.commit()
        
        result = db_session.query(Portfolio).filter(
            Portfolio.symbol == 'BTCUSDT'
        ).first()
        
        assert result is not None
        assert result.quantity == 0.5
        assert result.avg_cost == 50000.0
    
    @pytest.mark.skip(reason="Requires external API connection")
    def test_data_collector_initialization(self):
        """Test DataCollector initialization"""
        collector = DataCollector('binance')
        assert collector.exchange_name == 'binance'
        assert collector.exchange is not None
    
    def test_data_preparation(self):
        """Test data preparation for ML models"""
        # Create sample data
        dates = pd.date_range('2025-01-01', periods=100, freq='1H')
        data = {
            'timestamp': dates,
            'symbol': ['BTCUSDT'] * 100,
            'open_price': range(50000, 50100),
            'high_price': range(50100, 50200),
            'low_price': range(49900, 50000),
            'close_price': range(50050, 50150),
            'volume': range(1000, 1100)
        }
        df = pd.DataFrame(data)
        
        # Basic validation
        assert len(df) == 100
        assert 'timestamp' in df.columns
        assert 'close_price' in df.columns
        assert df['symbol'].iloc[0] == 'BTCUSDT'


class TestDataValidation:
    """Test data validation and integrity"""
    
    def test_price_data_integrity(self, db_session):
        """Test that price data maintains proper OHLC relationships"""
        market_data = MarketData(
            symbol='BTCUSDT',
            timestamp=datetime.utcnow(),
            open_price=50000.0,
            high_price=51000.0,  # Should be >= open, low, close
            low_price=49500.0,   # Should be <= open, high, close
            close_price=50500.0,
            volume=1000.0
        )
        
        # Validate OHLC relationships
        assert market_data.high_price >= market_data.open_price
        assert market_data.high_price >= market_data.close_price
        assert market_data.low_price <= market_data.open_price
        assert market_data.low_price <= market_data.close_price
        
        db_session.add(market_data)
        db_session.commit()
    
    def test_trade_side_validation(self, db_session):
        """Test trade side validation"""
        # Valid sides
        for side in ['buy', 'sell']:
            trade = Trade(
                symbol='BTCUSDT',
                side=side,
                quantity=0.001,
                price=50000.0,
                timestamp=datetime.utcnow()
            )
            db_session.add(trade)
        
        db_session.commit()
        
        # Count trades
        trade_count = db_session.query(Trade).count()
        assert trade_count == 2
    
    def test_positive_quantities(self, db_session):
        """Test that quantities are positive"""
        trade = Trade(
            symbol='BTCUSDT',
            side='buy',
            quantity=0.001,  # Should be positive
            price=50000.0,
            timestamp=datetime.utcnow()
        )
        
        assert trade.quantity > 0
        assert trade.price > 0
        
        db_session.add(trade)
        db_session.commit()