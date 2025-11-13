"""
FastAPI backend for AI Trading Bot
"""
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import List, Optional
import logging
import os
from datetime import datetime, timedelta

# Configure logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import local modules
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

try:
    from data.database import get_db, test_connection
    from data.models import MarketData, Trade, Portfolio, Strategy
    from .schemas import (
        MarketDataResponse, TradeRequest, TradeResponse, 
        PortfolioResponse, StrategyResponse
    )
    from .services import TradingService, PortfolioService
    logger.info("All modules imported successfully")
except Exception as e:
    logger.error(f"Import error: {e}")
    # Create dummy functions if imports fail
    def get_db():
        raise HTTPException(status_code=503, detail="Database not available")
    def test_connection():
        return False
    class TradingService:
        pass
    class PortfolioService:
        pass

# Initialize FastAPI app
app = FastAPI(
    title="AI Trading Bot API",
    description="RESTful API for cryptocurrency trading bot with ML predictions",
    version="1.0.2",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Services
trading_service = TradingService()
portfolio_service = PortfolioService()


@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    logger.info("Starting AI Trading Bot API...")
    
    # Test database connection (non-blocking for Railway deployment)
    try:
        if test_connection():
            logger.info("Database connected successfully")
            # Auto-create tables if they don't exist
            try:
                from data.database import create_tables
                create_tables()
                logger.info("Database schema initialized")
            except Exception as e:
                logger.warning(f"Could not initialize database schema: {e}")
        else:
            logger.warning("Database connection unavailable - some features will be limited")
    except Exception as e:
        logger.warning(f"Database connection error: {e} - continuing without database")
    
    logger.info("API started successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down AI Trading Bot API...")


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "AI Trading Bot API",
        "version": "1.0.2",
        "status": "running",
        "docs": "/docs",
        "health": "/health"
    }


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    db_status = "unknown"
    try:
        db_status = "connected" if test_connection() else "disconnected"
    except:
        db_status = "unavailable"
    
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "version": "1.0.2",
        "database": db_status,
        "environment": os.getenv("ENVIRONMENT", "production")
    }


@app.get("/api/status")
async def get_status(db: Session = Depends(get_db)):
    """Get trading bot status"""
    try:
        # Check database connection
        db_connected = test_connection()
        
        # Get some basic stats
        total_trades = db.query(Trade).count() if db_connected else 0
        active_positions = db.query(Portfolio).filter(Portfolio.quantity > 0).count() if db_connected else 0
        
        return {
            "trading_engine": "stopped",  # Default - would be "active" if trading engine running
            "database": "connected" if db_connected else "disconnected",
            "total_trades": total_trades,
            "active_positions": active_positions,
            "uptime": "online",
            "last_update": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        return {
            "trading_engine": "stopped",
            "database": "error",
            "error": str(e)
        }


@app.get("/api/signals")
async def get_signals():
    """Get current trading signals"""
    # This would integrate with your ML model / trading signals
    # For now, return empty or demo data
    return {
        "signals": [],
        "last_update": datetime.utcnow().isoformat(),
        "message": "No active signals - ML model not yet integrated"
    }


# Market data endpoints
@app.get("/api/market-data/{symbol}", response_model=List[MarketDataResponse])
async def get_market_data(
    symbol: str,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get market data for a symbol"""
    try:
        data = db.query(MarketData).filter(
            MarketData.symbol == symbol.replace('/', '')
        ).order_by(MarketData.timestamp.desc()).limit(limit).all()
        
        return [MarketDataResponse.from_orm(d) for d in data]
    except Exception as e:
        logger.error(f"Error fetching market data: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/market-data/{symbol}/latest", response_model=MarketDataResponse)
async def get_latest_price(symbol: str, db: Session = Depends(get_db)):
    """Get latest price for a symbol"""
    try:
        data = db.query(MarketData).filter(
            MarketData.symbol == symbol.replace('/', '')
        ).order_by(MarketData.timestamp.desc()).first()
        
        if not data:
            raise HTTPException(status_code=404, detail="Symbol not found")
        
        return MarketDataResponse.from_orm(data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching latest price: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/candles/{symbol}")
async def get_candles(symbol: str, limit: int = 200):
    """Get candlestick data for charts (live from Binance)"""
    try:
        import ccxt
        
        # Initialize Binance exchange
        exchange = ccxt.binance({
            'enableRateLimit': True,
            'options': {'defaultType': 'spot'}
        })
        
        # Fetch OHLCV data
        ohlcv = exchange.fetch_ohlcv(symbol, '1h', limit=limit)
        
        # Format for frontend
        candles = []
        for candle in ohlcv:
            candles.append({
                'timestamp': candle[0],
                'open': candle[1],
                'high': candle[2],
                'low': candle[3],
                'close': candle[4],
                'volume': candle[5]
            })
        
        return {
            'symbol': symbol,
            'candles': candles,
            'count': len(candles)
        }
    except Exception as e:
        logger.error(f"Error fetching candles: {e}")
        # Return empty data instead of error to prevent frontend crashes
        return {
            'symbol': symbol,
            'candles': [],
            'count': 0,
            'error': str(e)
        }


# Trading endpoints
@app.post("/api/trades", response_model=TradeResponse)
async def execute_trade(
    trade_request: TradeRequest,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Execute a trade"""
    try:
        # Validate trade request
        if trade_request.quantity <= 0:
            raise HTTPException(status_code=400, detail="Invalid quantity")
        
        if trade_request.side not in ['buy', 'sell']:
            raise HTTPException(status_code=400, detail="Invalid side")
        
        # Execute trade through service
        trade = await trading_service.execute_trade(trade_request, db)
        return TradeResponse.from_orm(trade)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing trade: {e}")
        raise HTTPException(status_code=500, detail="Failed to execute trade")


@app.get("/api/trades", response_model=List[TradeResponse])
async def get_trades(
    symbol: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get trade history"""
    try:
        query = db.query(Trade)
        
        if symbol:
            query = query.filter(Trade.symbol == symbol.replace('/', ''))
        
        trades = query.order_by(Trade.timestamp.desc()).limit(limit).all()
        return [TradeResponse.from_orm(trade) for trade in trades]
        
    except Exception as e:
        logger.error(f"Error fetching trades: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Portfolio endpoints
@app.get("/api/portfolio", response_model=List[PortfolioResponse])
async def get_portfolio(
    db: Session = Depends(get_db)
):
    """Get current portfolio"""
    try:
        portfolio = await portfolio_service.get_portfolio(db)
        return [PortfolioResponse.from_orm(p) for p in portfolio]
        
    except Exception as e:
        logger.error(f"Error fetching portfolio: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/portfolio/value")
async def get_portfolio_value(
    db: Session = Depends(get_db)
):
    """Get total portfolio value in USDT"""
    try:
        value = await portfolio_service.calculate_portfolio_value(db)
        return {"total_value_usdt": value, "timestamp": datetime.utcnow()}
        
    except Exception as e:
        logger.error(f"Error calculating portfolio value: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Strategy endpoints
@app.get("/api/strategies", response_model=List[StrategyResponse])
async def get_strategies(db: Session = Depends(get_db)):
    """Get all trading strategies"""
    try:
        strategies = db.query(Strategy).all()
        return [StrategyResponse.from_orm(s) for s in strategies]
        
    except Exception as e:
        logger.error(f"Error fetching strategies: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/strategies/{strategy_name}/performance")
async def get_strategy_performance(strategy_name: str, db: Session = Depends(get_db)):
    """Get strategy performance metrics"""
    try:
        strategy = db.query(Strategy).filter(Strategy.name == strategy_name).first()
        if not strategy:
            raise HTTPException(status_code=404, detail="Strategy not found")
        
        # Calculate additional metrics
        trades = db.query(Trade).filter(Trade.strategy == strategy_name).all()
        
        performance = {
            "name": strategy.name,
            "total_trades": strategy.total_trades,
            "winning_trades": strategy.winning_trades,
            "win_rate": strategy.winning_trades / strategy.total_trades if strategy.total_trades > 0 else 0,
            "total_profit_loss": float(strategy.total_profit_loss or 0),
            "sharpe_ratio": float(strategy.sharpe_ratio or 0),
            "max_drawdown": float(strategy.max_drawdown or 0),
            "average_trade_size": sum(float(t.quantity) for t in trades) / len(trades) if trades else 0,
            "updated_at": strategy.updated_at
        }
        
        return performance
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching strategy performance: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# ML Prediction endpoints
@app.get("/api/predictions/{symbol}")
async def get_price_prediction(symbol: str):
    """Get ML price prediction for a symbol"""
    try:
        # TODO: Integrate with ML service
        # For now, return mock data
        return {
            "symbol": symbol,
            "predicted_price": 50000.0,  # Mock prediction
            "confidence": 0.85,
            "prediction_horizon": "24h",
            "timestamp": datetime.utcnow(),
            "model": "LSTM_v1"
        }
        
    except Exception as e:
        logger.error(f"Error getting prediction: {e}")
        raise HTTPException(status_code=500, detail="Prediction service unavailable")


# Statistics endpoints
@app.get("/api/stats/summary")
async def get_summary_stats(db: Session = Depends(get_db)):
    """Get summary statistics"""
    try:
        # Count total records
        total_market_data = db.query(MarketData).count()
        total_trades = db.query(Trade).count()
        total_strategies = db.query(Strategy).count()
        
        # Get latest data timestamp
        latest_data = db.query(MarketData).order_by(MarketData.timestamp.desc()).first()
        
        return {
            "total_market_data_points": total_market_data,
            "total_trades": total_trades,
            "total_strategies": total_strategies,
            "latest_data_timestamp": latest_data.timestamp if latest_data else None,
            "api_version": "1.0.0",
            "timestamp": datetime.utcnow()
        }
        
    except Exception as e:
        logger.error(f"Error fetching summary stats: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)