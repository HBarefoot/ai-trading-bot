"""
Database models for the AI Trading Bot
"""
from sqlalchemy import Column, Integer, String, Numeric, DateTime, Index, CheckConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime
from decimal import Decimal

Base = declarative_base()


class MarketData(Base):
    """Market data model for storing OHLCV data"""
    __tablename__ = 'market_data'
    __table_args__ = (
        Index('idx_market_data_symbol_timestamp', 'symbol', 'timestamp'),
    )

    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    open_price = Column(Numeric(20, 8), nullable=False)
    high_price = Column(Numeric(20, 8), nullable=False)
    low_price = Column(Numeric(20, 8), nullable=False)
    close_price = Column(Numeric(20, 8), nullable=False)
    volume = Column(Numeric(20, 8), nullable=False)
    created_at = Column(DateTime(timezone=True), default=func.now())

    def __repr__(self):
        return f"<MarketData(symbol={self.symbol}, timestamp={self.timestamp}, close={self.close_price})>"


class Trade(Base):
    """Trade execution model"""
    __tablename__ = 'trades'
    __table_args__ = (
        CheckConstraint("side IN ('buy', 'sell')", name='check_trade_side'),
    )

    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), nullable=False)
    side = Column(String(4), nullable=False)  # 'buy' or 'sell'
    quantity = Column(Numeric(20, 8), nullable=False)
    price = Column(Numeric(20, 8), nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    strategy = Column(String(50))
    profit_loss = Column(Numeric(20, 8))
    created_at = Column(DateTime(timezone=True), default=func.now())

    def __repr__(self):
        return f"<Trade(symbol={self.symbol}, side={self.side}, quantity={self.quantity}, price={self.price})>"


class Portfolio(Base):
    """Portfolio tracking model"""
    __tablename__ = 'portfolio'

    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), nullable=False, unique=True)
    quantity = Column(Numeric(20, 8), nullable=False, default=0)
    avg_cost = Column(Numeric(20, 8))
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Portfolio(symbol={self.symbol}, quantity={self.quantity}, avg_cost={self.avg_cost})>"


class Strategy(Base):
    """Strategy performance tracking"""
    __tablename__ = 'strategies'

    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False, unique=True)
    description = Column(String(200))
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    total_profit_loss = Column(Numeric(20, 8), default=0)
    sharpe_ratio = Column(Numeric(10, 4))
    max_drawdown = Column(Numeric(10, 4))
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Strategy(name={self.name}, total_trades={self.total_trades})>"


class Signal(Base):
    """Trading signals tracking"""
    __tablename__ = 'signals'
    __table_args__ = (
        Index('idx_signals_symbol_timestamp', 'symbol', 'timestamp'),
    )

    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), nullable=False)
    signal_type = Column(String(10), nullable=False)  # 'BUY', 'SELL', 'HOLD'
    signal_value = Column(Numeric(10, 4), nullable=False)  # Numerical signal (-1 to 1)
    price = Column(Numeric(20, 8), nullable=False)
    rsi = Column(Numeric(10, 4))
    ma_fast = Column(Numeric(20, 8))
    ma_slow = Column(Numeric(20, 8))
    trend = Column(String(20))
    timestamp = Column(DateTime(timezone=True), nullable=False, default=func.now())
    created_at = Column(DateTime(timezone=True), default=func.now())

    def __repr__(self):
        return f"<Signal(symbol={self.symbol}, type={self.signal_type}, price={self.price})>"