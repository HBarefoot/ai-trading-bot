"""
Pydantic schemas for API request/response models
"""
from pydantic import BaseModel, Field
from datetime import datetime
from decimal import Decimal
from typing import Optional


class MarketDataResponse(BaseModel):
    """Market data response model"""
    id: int
    symbol: str
    timestamp: datetime
    open_price: float = Field(..., description="Opening price")
    high_price: float = Field(..., description="Highest price")
    low_price: float = Field(..., description="Lowest price")
    close_price: float = Field(..., description="Closing price")
    volume: float = Field(..., description="Trading volume")
    
    class Config:
        from_attributes = True
        json_encoders = {
            Decimal: float,
            datetime: lambda v: v.isoformat()
        }


class TradeRequest(BaseModel):
    """Trade execution request"""
    symbol: str = Field(..., description="Trading pair symbol (e.g., BTCUSDT)")
    side: str = Field(..., description="Trade side: buy or sell")
    quantity: float = Field(..., gt=0, description="Quantity to trade")
    price: Optional[float] = Field(None, description="Limit price (optional for market orders)")
    strategy: Optional[str] = Field(None, description="Strategy name")


class TradeResponse(BaseModel):
    """Trade execution response"""
    id: int
    symbol: str
    side: str
    quantity: float
    price: float
    timestamp: datetime
    strategy: Optional[str]
    profit_loss: Optional[float]
    
    class Config:
        from_attributes = True
        json_encoders = {
            Decimal: float,
            datetime: lambda v: v.isoformat()
        }


class PortfolioResponse(BaseModel):
    """Portfolio position response"""
    id: int
    symbol: str
    quantity: float
    avg_cost: Optional[float]
    current_value: Optional[float] = None
    unrealized_pnl: Optional[float] = None
    updated_at: datetime
    
    class Config:
        from_attributes = True
        json_encoders = {
            Decimal: float,
            datetime: lambda v: v.isoformat()
        }


class StrategyResponse(BaseModel):
    """Strategy performance response"""
    id: int
    name: str
    description: Optional[str]
    total_trades: int
    winning_trades: int
    win_rate: Optional[float] = None
    total_profit_loss: float
    sharpe_ratio: Optional[float]
    max_drawdown: Optional[float]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
        json_encoders = {
            Decimal: float,
            datetime: lambda v: v.isoformat()
        }


class PredictionResponse(BaseModel):
    """ML prediction response"""
    symbol: str
    predicted_price: float
    confidence: float = Field(..., ge=0, le=1)
    prediction_horizon: str
    timestamp: datetime
    model: str
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ErrorResponse(BaseModel):
    """Error response model"""
    error: str
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }