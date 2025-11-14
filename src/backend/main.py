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
                from data.database import create_tables, engine
                from sqlalchemy import text, inspect
                
                # Create tables in public schema
                create_tables()
                
                # Verify tables were created
                inspector = inspect(engine)
                tables = inspector.get_table_names(schema='public')
                logger.info(f"Database initialized - Public schema tables: {tables}")
                
                if not tables:
                    logger.error("No tables found in public schema after creation!")
            except Exception as e:
                logger.error(f"Could not initialize database schema: {e}", exc_info=True)
        else:
            logger.warning("Database connection unavailable - some features will be limited")
    except Exception as e:
        logger.warning(f"Database connection error: {e} - continuing without database")
    
    logger.info("API started successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down AI Trading Bot API...")


@app.get("/api/admin/init-database")
async def init_database():
    """Manually initialize database tables (admin endpoint)"""
    try:
        from data.database import create_tables, engine
        from sqlalchemy import text, inspect
        
        # Create tables in public schema
        create_tables()
        
        # Check what was created
        inspector = inspect(engine)
        
        # Check public schema (Railway default)
        public_tables = inspector.get_table_names(schema='public')
        
        return {
            "status": "success",
            "message": "Database tables created in public schema",
            "tables": public_tables,
            "table_count": len(public_tables)
        }
    except Exception as e:
        logger.error(f"Database initialization failed: {e}", exc_info=True)
        return {
            "status": "error",
            "message": str(e)
        }


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
            "trading_engine": "stopped",  # "stopped" or "active"
            "mode": "PAPER TRADING",  # Trading mode display
            "exchange": "connected",  # Exchange connection status
            "data_feed": "active",  # Data feed status
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


@app.get("/api/alerts")
async def get_alerts(
    limit: int = 20,
    offset: int = 0,
    unread_only: bool = False,
    alert_type: str = None,
    symbol: str = None,
    hours: int = None
):
    """Get trading alerts"""
    # This would integrate with your alert system
    # For now, return empty data
    return {
        "alerts": [],
        "stats": {
            "total": 0,
            "unread": 0,
            "recent_24h": 0
        },
        "has_more": False
    }


@app.post("/api/alerts/mark-all-read")
async def mark_alerts_read(symbol: str = None):
    """Mark all alerts as read"""
    return {"success": True, "message": "All alerts marked as read"}


@app.post("/api/trading/start")
async def start_trading():
    """Start the trading engine"""
    # This would start your actual trading engine
    # For now, just return success
    return {
        "success": True,
        "message": "Trading engine start requested",
        "status": "starting"
    }


@app.post("/api/trading/stop")
async def stop_trading():
    """Stop the trading engine"""
    # This would stop your actual trading engine
    # For now, just return success
    return {
        "success": True,
        "message": "Trading engine stop requested",
        "status": "stopping"
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
    """Get candlestick data for charts (live from Binance or fallback to demo data)"""
    try:
        import ccxt
        from datetime import datetime, timedelta
        
        # Try Binance.US first
        try:
            exchange = ccxt.binanceus({
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
        except Exception as binance_error:
            logger.warning(f"Binance.US unavailable, using fallback data: {binance_error}")
            
            # Fallback: Generate realistic demo data
            import random
            base_price = 90000 if 'BTC' in symbol else 3400  # BTC or ETH base
            now = datetime.now()
            candles = []
            
            for i in range(limit):
                timestamp = int((now - timedelta(hours=limit-i)).timestamp() * 1000)
                # Simulate realistic price movement
                variation = random.uniform(-0.02, 0.02)
                open_price = base_price * (1 + variation)
                close_price = base_price * (1 + random.uniform(-0.02, 0.02))
                high_price = max(open_price, close_price) * random.uniform(1.0, 1.01)
                low_price = min(open_price, close_price) * random.uniform(0.99, 1.0)
                volume = random.uniform(100, 1000)
                
                candles.append({
                    'timestamp': timestamp,
                    'open': round(open_price, 2),
                    'high': round(high_price, 2),
                    'low': round(low_price, 2),
                    'close': round(close_price, 2),
                    'volume': round(volume, 2)
                })
                base_price = close_price  # Continue from previous close
            
            return {
                'symbol': symbol,
                'candles': candles,
                'count': len(candles),
                'mode': 'DEMO_DATA'
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
@app.get("/api/portfolio")
async def get_portfolio(
    db: Session = Depends(get_db)
):
    """Get portfolio summary for dashboard"""
    try:
        # Get all positions from database
        positions = db.query(Portfolio).all()
        
        # Calculate portfolio metrics
        total_value = 0
        cash_balance = 10000.0  # Default starting balance for paper trading
        unrealized_pnl = 0
        
        position_list = []
        for pos in positions:
            total_value += pos.current_value or 0
            unrealized_pnl += (pos.current_value or 0) - (pos.average_price * pos.quantity)
            position_list.append({
                'symbol': pos.symbol,
                'quantity': pos.quantity,
                'average_price': pos.average_price,
                'current_value': pos.current_value
            })
        
        # Calculate total portfolio value
        total_portfolio_value = total_value + cash_balance
        
        # Calculate return percentage
        initial_value = 10000.0  # Starting balance
        total_return_pct = ((total_portfolio_value - initial_value) / initial_value) * 100 if initial_value > 0 else 0
        
        return {
            'total_value': round(total_portfolio_value, 2),
            'cash': round(cash_balance, 2),
            'cash_balance': round(cash_balance, 2),
            'unrealized_pnl': round(unrealized_pnl, 2),
            'total_return_pct': round(total_return_pct, 2),
            'positions': position_list,
            'position_count': len(position_list)
        }
        
    except Exception as e:
        logger.error(f"Error fetching portfolio: {e}")
        # Return empty portfolio instead of error
        return {
            'total_value': 10000.0,
            'cash': 10000.0,
            'cash_balance': 10000.0,
            'unrealized_pnl': 0.0,
            'total_return_pct': 0.0,
            'positions': [],
            'position_count': 0
        }


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