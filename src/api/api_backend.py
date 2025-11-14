"""
Live Trading API Backend
Provides REST API for live trading dashboard and controls
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional
import uvicorn
from dotenv import load_dotenv
from pathlib import Path

import sys
import os

# Load environment variables from project root
project_root = Path(__file__).parent.parent.parent
dotenv_path = project_root / '.env'
load_dotenv(dotenv_path)

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from trading.live_engine_5m import get_trading_engine_5m as get_trading_engine
from trading.exchange_integration import exchange_manager
from data.database import get_db
from data.models import Trade, MarketData
from data.live_feed import get_data_feed_manager, start_live_feed, stop_live_feed
from data.historical_candles import preload_historical_candles_to_db, get_db_candle_count
from sqlalchemy.orm import Session
from sqlalchemy import desc

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# AI modules - with graceful fallback
try:
    from ai.sentiment_analyzer import sentiment_analyzer
    from ai.data_collectors import news_collector, reddit_collector
    from ai.market_commentary import market_commentary
    AI_AVAILABLE = True
    logger.info("AI modules loaded successfully")
except ImportError as e:
    logger.warning(f"AI modules not available: {e}. Running without AI features.")
    sentiment_analyzer = None
    news_collector = None
    reddit_collector = None
    market_commentary = None
    AI_AVAILABLE = False

# Initialize global variables
trading_engine = None
data_feed_manager = None

app = FastAPI(
    title="AI Trading Bot API",
    description="Live trading engine API for cryptocurrency trading",
    version="3.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global references
trading_engine = None
trading_task = None

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup with graceful error handling"""
    global trading_engine, exchange_manager, data_feed_manager

    logger.info("Starting AI Trading Bot API...")

    # Initialize database tables
    db_url = os.getenv('DATABASE_URL')
    if db_url:
        try:
            from data.database import create_tables
            logger.info("Creating database tables if they don't exist...")
            create_tables()
            logger.info("✅ Database tables initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to create database tables: {e}")
            logger.warning("App will continue but database operations may fail")
    else:
        logger.warning("No DATABASE_URL found - skipping database initialization")

    try:
        # Initialize exchange manager with Binance credentials from .env
        from trading.exchange_integration import initialize_exchanges
        initialize_exchanges()
        logger.info("Exchanges initialized with credentials from .env")
    except Exception as e:
        logger.warning(f"Could not initialize exchanges: {e}")
    
    try:
        # Initialize trading engine with AI enhancement
        trading_engine = get_trading_engine(use_ai=True)
        logger.info("Trading engine initialized")
    except Exception as e:
        logger.warning(f"Could not initialize trading engine: {e}")
    
    # Skip database operations if DATABASE_URL is not available
    db_url = os.getenv('DATABASE_URL')
    if db_url and not db_url.startswith('postgresql://trader:trading123@localhost'):
        logger.info("Pre-loading historical 5-minute candles from Binance.US...")
        try:
            symbols_to_load = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT']
            for symbol in symbols_to_load:
                db_symbol = symbol.replace('USDT', '/USDT')
                count = get_db_candle_count(db_symbol)
                if count < 50:  # Less than ~4 hours of data
                    logger.info(f"  {db_symbol}: Only {count} candles in DB, fetching from Binance...")
                    preload_historical_candles_to_db([symbol], hours=8)
                else:
                    logger.info(f"  {db_symbol}: {count} candles already in DB")
        except Exception as e:
            logger.warning(f"Could not pre-load historical candles: {e}")
    else:
        logger.info("Skipping database operations - no production database configured")
    
    # Only start live data feed if API keys are available
    api_key = os.getenv('BINANCE_API_KEY')
    if api_key and api_key != 'your_binance_api_key_here':
        try:
            # Start live data feed with Binance.US WebSocket
            await start_live_feed(use_mock=False)
            logger.info("Live data feed started")
        except Exception as e:
            logger.warning(f"Could not start live data feed: {e}")
    else:
        logger.info("Skipping live data feed - no valid API keys configured")
    
    logger.info("API startup completed with graceful handling")
    
    # Get the data feed manager reference safely
    try:
        data_feed_manager = get_data_feed_manager()
    except Exception as e:
        logger.warning(f"Could not get data feed manager: {e}")

    # Optional: Auto-start trading engine if configured
    auto_start = os.getenv('AUTO_START_TRADING', 'false').lower() == 'true'
    if auto_start and trading_engine:
        try:
            logger.info("🚀 AUTO_START_TRADING enabled - starting trading engine...")
            trading_task = asyncio.create_task(trading_engine.start())
            logger.info("✅ Trading engine auto-started successfully")
        except Exception as e:
            logger.error(f"❌ Failed to auto-start trading engine: {e}")
            logger.warning("Trading engine can be started manually via /api/trading/start")
    else:
        if not auto_start:
            logger.info("ℹ️  Trading engine NOT auto-started (set AUTO_START_TRADING=true to enable)")
        logger.info("💡 Start trading manually via POST /api/trading/start")

    print("AI Trading Bot API started successfully!")

# Basic health and info endpoints
@app.get("/")
async def root():
    """Root endpoint for basic connectivity test"""
    return {
        "name": "AI Trading Bot API", 
        "version": "3.0.0",
        "status": "online",
        "timestamp": datetime.now()
    }

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global trading_engine, trading_task
    if trading_engine and trading_engine.running:
        await trading_engine.stop()
    if trading_task:
        trading_task.cancel()

# Health Check
@app.get("/api/health")
async def health_check():
    """API health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(),
        "version": "3.0.0",
        "services": {
            "trading_engine": trading_engine.running if trading_engine else False,
            "exchange": "connected" if exchange_manager.get_exchange() else "disconnected"
        }
    }

# Trading Engine Control
@app.post("/api/trading/start")
async def start_trading(background_tasks: BackgroundTasks):
    """Start the live trading engine"""
    global trading_engine, trading_task
    
    try:
        if not trading_engine:
            trading_engine = get_trading_engine()
        
        if trading_engine and getattr(trading_engine, 'running', False):
            raise HTTPException(status_code=400, detail="Trading engine is already running")
        
        # Start trading in background
        trading_task = asyncio.create_task(trading_engine.start())
        
        return {
            "status": "started",
            "message": "Live trading engine started",
            "timestamp": datetime.now()
        }
    except Exception as e:
        logger.error(f"Failed to start trading engine: {e}")
        return {
            "status": "error",
            "message": f"Failed to start trading engine: {str(e)}",
            "timestamp": datetime.now()
        }

@app.post("/api/trading/stop")
async def stop_trading():
    """Stop the live trading engine"""
    global trading_engine, trading_task
    
    try:
        if not trading_engine or not getattr(trading_engine, 'running', False):
            raise HTTPException(status_code=400, detail="Trading engine is not running")
        
        await trading_engine.stop()
        
        if trading_task:
            trading_task.cancel()
            trading_task = None
        
        return {
            "status": "stopped",
            "message": "Live trading engine stopped",
            "timestamp": datetime.now()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to stop trading engine: {e}")
        return {
            "status": "error",
            "message": f"Failed to stop trading engine: {str(e)}",
            "timestamp": datetime.now()
        }

@app.get("/api/status")
async def get_status():
    """Get system status with robust error handling"""
    global trading_engine, exchange_manager, data_feed_manager
    
    try:
        # Safely check trading engine
        engine_status = "stopped"
        paper_trading = True
        
        try:
            if trading_engine is None:
                trading_engine = get_trading_engine()
            engine_status = "active" if (trading_engine and getattr(trading_engine, 'running', False)) else "stopped"
            paper_trading = getattr(trading_engine, 'paper_trading', True)
        except Exception as e:
            logger.warning(f"Could not get trading engine status: {e}")
        
        # Safely check exchange
        exchange_status = "disconnected"
        try:
            if exchange_manager and hasattr(exchange_manager, 'get_exchange'):
                exchange_status = "connected" if exchange_manager.get_exchange() else "disconnected"
        except Exception as e:
            logger.warning(f"Could not get exchange status: {e}")
        
        # Safely check data feed
        data_feed_status = "inactive"
        try:
            if data_feed_manager is None:
                data_feed_manager = get_data_feed_manager()
            data_feed_status = "active" if data_feed_manager else "inactive"
        except Exception as e:
            logger.warning(f"Could not get data feed status: {e}")
        
        return {
            "status": "running",
            "timestamp": datetime.now(),
            "trading_engine": engine_status,
            "paper_trading": paper_trading,
            "mode": "PAPER TRADING" if paper_trading else "LIVE TRADING",
            "exchange": exchange_status,
            "data_feed": data_feed_status
        }
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        # Return a minimal status even if everything fails
        return {
            "status": "running",
            "timestamp": datetime.now(),
            "trading_engine": "stopped",
            "paper_trading": True,
            "mode": "PAPER TRADING",
            "exchange": "disconnected", 
            "data_feed": "inactive",
            "error": str(e)
        }

@app.get("/health")
async def health_check():
    """Health check endpoint for Railway deployment"""
    return {
        "status": "healthy", 
        "timestamp": datetime.now(),
        "service": "AI Trading Bot API",
        "version": "3.0.0"
    }

@app.get("/api/health")
async def api_health_check():
    """Detailed API health check"""
    try:
        return {
            "status": "healthy",
            "timestamp": datetime.now(),
            "version": "3.0.0",
            "services": {
                "trading_engine": getattr(trading_engine, 'running', False) if trading_engine else False,
                "exchange": "connected" if (exchange_manager and hasattr(exchange_manager, 'get_exchange') and exchange_manager.get_exchange()) else "disconnected"
            }
        }
    except Exception as e:
        return {
            "status": "degraded",
            "timestamp": datetime.now(),
            "error": str(e)
        }

# Portfolio Management
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global trading_engine, data_feed_manager
    
    print("Shutting down AI Trading Bot API...")
    
    # Stop trading engine
    if trading_engine:
        await trading_engine.stop()
    
    # Stop data feed
    await stop_live_feed()
    
    print("AI Trading Bot API shut down successfully!")

@app.get("/api/portfolio")
async def get_portfolio():
    """Get current portfolio"""
    global trading_engine, data_feed_manager
    
    try:
        if trading_engine is None:
            trading_engine = get_trading_engine()
        if data_feed_manager is None:
            data_feed_manager = get_data_feed_manager()
        
        portfolio = trading_engine.portfolio
        latest_prices = data_feed_manager.get_latest_prices()
        
        positions_list = []
        for symbol, pos in portfolio.positions.items():
            # Get current price from live data
            current_price = latest_prices.get(symbol, None)
            current_price_value = current_price.price if current_price else pos.entry_price
            
            # Calculate current value and P&L
            current_value = pos.amount * current_price_value
            entry_value = pos.amount * pos.entry_price
            unrealized_pnl = current_value - entry_value
            unrealized_pnl_pct = (unrealized_pnl / entry_value * 100) if entry_value > 0 else 0
            
            positions_list.append({
                "symbol": symbol,
                "quantity": pos.amount,
                "entry_price": pos.entry_price,
                "current_price": current_price_value,
                "value": current_value,
                "unrealized_pnl": unrealized_pnl,
                "unrealized_pnl_pct": unrealized_pnl_pct
            })
        
        return {
            "timestamp": datetime.now(),
            "total_value": portfolio.get_portfolio_value(),
            "cash": portfolio.cash_balance,
            "positions": positions_list
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/live-data")
async def get_live_data():
    """Get live market data"""
    global data_feed_manager
    
    try:
        if data_feed_manager is None:
            data_feed_manager = get_data_feed_manager()
        
        prices = data_feed_manager.get_latest_prices()
        
        return {
            "timestamp": datetime.now(),
            "prices": {
                symbol: {
                    "price": update.price,
                    "timestamp": update.timestamp,
                    "volume": update.volume,
                    "change_24h": update.change_24h
                }
                for symbol, update in prices.items()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/live-data/{symbol}")
async def get_live_price(symbol: str):
    """Get live price for a specific symbol"""
    global data_feed_manager
    
    try:
        if data_feed_manager is None:
            data_feed_manager = get_data_feed_manager()
        
        update = data_feed_manager.get_latest_price(symbol.upper())
        
        if not update:
            raise HTTPException(status_code=404, detail=f"No data available for {symbol}")
        
        return {
            "symbol": update.symbol,
            "price": update.price,
            "timestamp": update.timestamp,
            "volume": update.volume,
            "change_24h": update.change_24h
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/market-data/{symbol}/latest")
async def get_market_data_latest(symbol: str):
    """Get latest market data for a symbol (alias for live-data)"""
    global data_feed_manager
    
    try:
        if data_feed_manager is None:
            data_feed_manager = get_data_feed_manager()
        
        update = data_feed_manager.get_latest_price(symbol.upper())
        
        if not update:
            raise HTTPException(status_code=404, detail=f"No data available for {symbol}")
        
        return {
            "symbol": update.symbol,
            "price": update.price,
            "timestamp": update.timestamp,
            "volume": update.volume,
            "change_24h": update.change_24h
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/market-data/{symbol}")
async def get_market_data_history(symbol: str, limit: int = 500):
    """Get historical market data for a symbol"""
    try:
        db = next(get_db())
        
        # Get historical data from database
        market_data = db.query(MarketData).filter(
            MarketData.symbol == symbol.upper()
        ).order_by(MarketData.timestamp.desc()).limit(limit).all()
        
        if not market_data:
            # Return empty list if no data
            return []
        
        # Convert to list of dicts
        data = []
        for record in reversed(market_data):  # Reverse for chronological order
            data.append({
                "timestamp": record.timestamp.isoformat(),
                "open": float(record.open_price),
                "high": float(record.high_price),
                "low": float(record.low_price),
                "close": float(record.close_price),
                "volume": float(record.volume)
            })
        
        db.close()
        return data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching market data: {str(e)}")

@app.get("/api/candles/{symbol}")
async def get_candles(symbol: str, limit: int = 100):
    """Get historical candle data for a symbol"""
    try:
        from datetime import timedelta
        from data.database import get_db
        from data.models import MarketData
        
        global data_feed_manager
        
        if data_feed_manager is None:
            data_feed_manager = get_data_feed_manager()
        
        # Try to get from candle aggregator first (in-memory)
        if hasattr(data_feed_manager, 'candle_aggregator'):
            candles = data_feed_manager.candle_aggregator.get_candles(symbol, limit=limit)
            
            if candles and len(candles) > 0:
                candle_list = []
                for candle in candles:
                    candle_list.append({
                        "timestamp": candle['timestamp'].isoformat() if hasattr(candle['timestamp'], 'isoformat') else str(candle['timestamp']),
                        "open": float(candle['open']),
                        "high": float(candle['high']),
                        "low": float(candle['low']),
                        "close": float(candle['close']),
                        "volume": float(candle['volume'])
                    })
                return candle_list
        
        # Fallback: Get from database
        logger.info(f"No candles in aggregator, fetching from database for {symbol}")
        db = next(get_db())
        
        # Get recent candles from database
        cutoff_time = datetime.now() - timedelta(hours=8)
        records = db.query(MarketData).filter(
            MarketData.symbol == symbol,
            MarketData.timestamp >= cutoff_time
        ).order_by(MarketData.timestamp.desc()).limit(limit).all()
        
        db.close()
        
        if records:
            # Reverse to get chronological order
            records = list(reversed(records))
            candle_list = []
            for record in records:
                candle_list.append({
                    "timestamp": record.timestamp.isoformat(),
                    "open": float(record.open_price),
                    "high": float(record.high_price),
                    "low": float(record.low_price),
                    "close": float(record.close_price),
                    "volume": float(record.volume)
                })
            logger.info(f"Returned {len(candle_list)} candles from database for {symbol}")
            return candle_list
        
        return []
            
    except Exception as e:
        logger.error(f"Error fetching candles for {symbol}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching candle data: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint (alias for status)"""
    return await get_status()

@app.get("/api/portfolio/value")
async def get_portfolio_value():
    """Get portfolio value summary"""
    if not trading_engine:
        raise HTTPException(status_code=503, detail="Trading engine not available")
    
    portfolio = trading_engine.portfolio
    total_value = portfolio.get_portfolio_value()
    total_return = (total_value - portfolio.initial_balance) / portfolio.initial_balance
    
    return {
        "total_value_usdt": total_value,
        "initial_balance": portfolio.initial_balance,
        "total_return": total_return,
        "cash_balance": portfolio.cash_balance,
        "positions_count": len(portfolio.positions)
    }

# Trading History
@app.get("/api/trades")
async def get_trades(limit: int = 50):
    """Get recent trades from database"""
    db = next(get_db())
    
    trades = db.query(Trade).order_by(Trade.timestamp.desc()).limit(limit).all()
    
    trade_list = []
    for trade in trades:
        trade_list.append({
            "id": trade.id,
            "symbol": trade.symbol,
            "side": trade.side,
            "quantity": float(trade.quantity),
            "price": float(trade.price),
            "timestamp": trade.timestamp.isoformat(),
            "strategy": trade.strategy,
            "profit_loss": float(trade.profit_loss) if trade.profit_loss else 0
        })
    
    db.close()
    return trade_list

# Performance Metrics
@app.get("/api/performance")
async def get_performance():
    """Get performance metrics"""
    if not trading_engine:
        raise HTTPException(status_code=503, detail="Trading engine not available")
    
    metrics = trading_engine.get_performance_metrics()
    
    return {
        "portfolio_value": metrics.get("portfolio_value", 0),
        "total_return": metrics.get("total_return", 0),
        "total_trades": metrics.get("total_trades", 0),
        "winning_trades": metrics.get("winning_trades", 0),
        "win_rate": metrics.get("win_rate", 0),
        "positions": metrics.get("positions", 0),
        "cash_balance": metrics.get("cash_balance", 0),
        "running_time_seconds": metrics.get("running_time", 0).total_seconds() if metrics.get("running_time") else 0
    }

# Live Market Data
@app.get("/api/market/{symbol}")
async def get_market_data(symbol: str):
    """Get live market data for a symbol"""
    exchange = exchange_manager.get_exchange()
    if not exchange:
        raise HTTPException(status_code=503, detail="Exchange not available")
    
    try:
        ticker = await exchange.get_ticker(symbol)
        return ticker
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting market data: {str(e)}")

# Exchange Information
@app.get("/api/exchange/balance")
async def get_exchange_balance():
    """Get exchange account balance"""
    exchange = exchange_manager.get_exchange()
    if not exchange:
        raise HTTPException(status_code=503, detail="Exchange not available")
    
    try:
        balance = await exchange.get_balance()
        return balance
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting balance: {str(e)}")

@app.get("/api/exchange/orders")
async def get_open_orders(symbol: Optional[str] = None):
    """Get open orders"""
    exchange = exchange_manager.get_exchange()
    if not exchange:
        raise HTTPException(status_code=503, detail="Exchange not available")
    
    try:
        orders = await exchange.get_open_orders(symbol)
        return orders
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting orders: {str(e)}")

# Historical Data (from database)
@app.get("/api/historical/{symbol}")
async def get_historical_data(symbol: str, limit: int = 100):
    """Get historical market data"""
    try:
        db = next(get_db())
        
        market_data = db.query(MarketData).filter(
            MarketData.symbol == symbol
        ).order_by(MarketData.timestamp.desc()).limit(limit).all()
        
        data = []
        for record in reversed(market_data):  # Reverse to get chronological order
            data.append({
                "timestamp": record.timestamp,
                "open": float(record.open_price),
                "high": float(record.high_price),
                "low": float(record.low_price),
                "close": float(record.close_price),
                "volume": float(record.volume)
            })
        
        db.close()
        return data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting historical data: {str(e)}")

# Strategy Information
@app.get("/api/strategies")
async def get_strategies():
    """Get available trading strategies"""
    return {
        "active_strategy": "OptimizedPhase2",
        "available_strategies": [
            {
                "name": "OptimizedPhase2",
                "description": "Optimized momentum strategy with RSI confirmation",
                "parameters": {
                    "fast_ma": 8,
                    "slow_ma": 21,
                    "rsi_oversold": 35,
                    "rsi_overbought": 65
                }
            }
        ]
    }

# AI Predictions (Placeholder for Phase 4)
@app.get("/api/predictions/{symbol}")
async def get_predictions(symbol: str):
    """Get AI price predictions for a symbol"""
    return {
        "symbol": symbol,
        "prediction": "HOLD",
        "confidence": 0.75,
        "message": "AI predictions coming in Phase 4",
        "predicted_price_24h": None,
        "predicted_change": None
    }

# Live Signals (from our existing strategy)
@app.get("/api/signals/{symbol}")
async def get_live_signals(symbol: str):
    """Get live trading signals for a symbol - ACTUAL signals from trading engine"""
    global trading_engine
    
    try:
        # Get actual signals from the signal monitor (what the bot is actually using)
        from trading.signal_monitor import get_signal_monitor
        signal_monitor = get_signal_monitor()
        
        # Get current signal state for this symbol
        current_signals = signal_monitor.get_current_signals()
        
        if symbol.upper() in current_signals:
            state = current_signals[symbol.upper()]
            return {
                "symbol": symbol,
                "current_price": float(state.price),
                "signal": float(state.current_signal),
                "signal_type": state.signal_type.value,
                "rsi": float(state.rsi) if state.rsi is not None else None,
                "ma_fast": float(state.ma_fast) if state.ma_fast is not None else None,
                "ma_slow": float(state.ma_slow) if state.ma_slow is not None else None,
                "trend": state.trend,
                "last_change": state.last_change.isoformat(),
                "timestamp": datetime.now(),
                "note": "ACTUAL signal from live trading engine"
            }
        else:
            # Fallback: use database data for display only
            # But warn that this is NOT what the bot is trading on
            db = next(get_db())
            market_data = db.query(MarketData).filter(
                MarketData.symbol == symbol
            ).order_by(MarketData.timestamp.desc()).limit(1).first()
            
            if not market_data:
                raise HTTPException(status_code=404, detail=f"No data available for {symbol}")
            
            db.close()
            
            return {
                "symbol": symbol,
                "current_price": float(market_data.close_price),
                "signal": 0,
                "signal_type": "HOLD",
                "rsi": None,
                "ma_fast": None,
                "ma_slow": None,
                "trend": "UNKNOWN",
                "timestamp": datetime.now(),
                "note": "No live signal yet - engine may still be accumulating data"
            }
        
    except Exception as e:
        logger.error(f"Error getting signals for {symbol}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error generating signals: {str(e)}")

# Manual Trading Orders
@app.post("/api/orders/buy")
async def create_buy_order(order: dict):
    """Execute a manual buy order"""
    try:
        symbol = order.get('symbol', 'BTCUSDT')
        amount = order.get('amount', 100.0)
        order_type = order.get('order_type', 'market')
        
        logger.info(f"Manual BUY order: {symbol} ${amount} ({order_type})")
        
        # In demo mode, simulate order execution
        # In production, this would call exchange_manager.place_order()
        
        # Get current price for simulation
        db = next(get_db())
        latest_data = db.query(MarketData).filter(
            MarketData.symbol == symbol
        ).order_by(MarketData.timestamp.desc()).first()
        
        current_price = float(latest_data.close_price) if latest_data else 0
        quantity = amount / current_price if current_price > 0 else 0
        
        # Save trade to database
        new_trade = Trade(
            symbol=symbol,
            side='buy',
            quantity=quantity,
            price=current_price,
            timestamp=datetime.now(),
            strategy='Manual',
            profit_loss=0
        )
        db.add(new_trade)
        
        # Update portfolio position
        from data.models import Portfolio
        from decimal import Decimal
        portfolio_pos = db.query(Portfolio).filter(Portfolio.symbol == symbol).first()
        if portfolio_pos:
            # Update existing position with average cost
            old_value = float(portfolio_pos.quantity) * float(portfolio_pos.avg_cost)
            new_value = old_value + (quantity * current_price)
            portfolio_pos.quantity = Decimal(str(float(portfolio_pos.quantity) + quantity))
            portfolio_pos.avg_cost = Decimal(str(new_value / float(portfolio_pos.quantity)))
        else:
            # Create new position
            portfolio_pos = Portfolio(
                symbol=symbol,
                quantity=Decimal(str(quantity)),
                avg_cost=Decimal(str(current_price))
            )
            db.add(portfolio_pos)
        
        db.commit()
        db.refresh(new_trade)
        
        order_id = f"BUY-{symbol}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        db.close()
        
        return {
            "success": True,
            "order_id": order_id,
            "symbol": symbol,
            "side": "buy",
            "type": order_type,
            "amount": amount,
            "price": current_price,
            "quantity": quantity,
            "status": "filled",
            "message": f"Demo order placed: BUY {quantity:.6f} {symbol} @ ${current_price:,.2f}",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Buy order error: {e}")
        return {
            "success": False,
            "error": str(e)
        }

@app.post("/api/orders/sell")
async def create_sell_order(order: dict):
    """Execute a manual sell order"""
    try:
        symbol = order.get('symbol', 'BTCUSDT')
        amount = order.get('amount', 100.0)
        order_type = order.get('order_type', 'market')
        
        logger.info(f"Manual SELL order: {symbol} ${amount} ({order_type})")
        
        # In demo mode, simulate order execution
        # In production, this would call exchange_manager.place_order()
        
        # Get current price for simulation
        db = next(get_db())
        latest_data = db.query(MarketData).filter(
            MarketData.symbol == symbol
        ).order_by(MarketData.timestamp.desc()).first()
        
        current_price = float(latest_data.close_price) if latest_data else 0
        quantity = amount / current_price if current_price > 0 else 0
        
        # Update portfolio position first
        from data.models import Portfolio
        from decimal import Decimal
        portfolio_pos = db.query(Portfolio).filter(Portfolio.symbol == symbol).first()
        
        if not portfolio_pos or float(portfolio_pos.quantity) < quantity:
            db.close()
            return {
                "success": False,
                "error": f"Insufficient {symbol} balance. Available: {float(portfolio_pos.quantity) if portfolio_pos else 0:.6f}, trying to sell: {quantity:.6f}"
            }
        
        # Calculate P&L
        profit_loss = (current_price - float(portfolio_pos.avg_cost)) * quantity
        
        # Save trade to database
        new_trade = Trade(
            symbol=symbol,
            side='sell',
            quantity=quantity,
            price=current_price,
            timestamp=datetime.now(),
            strategy='Manual',
            profit_loss=profit_loss
        )
        db.add(new_trade)
        
        # Update portfolio position
        portfolio_pos.quantity = Decimal(str(float(portfolio_pos.quantity) - quantity))
        if float(portfolio_pos.quantity) <= 0.0001:  # Close position if near zero
            db.delete(portfolio_pos)
        
        db.commit()
        db.refresh(new_trade)
        
        order_id = f"SELL-{symbol}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        db.close()
        
        return {
            "success": True,
            "order_id": order_id,
            "symbol": symbol,
            "side": "sell",
            "type": order_type,
            "amount": amount,
            "price": current_price,
            "quantity": quantity,
            "status": "filled",
            "message": f"Demo order placed: SELL {quantity:.6f} {symbol} @ ${current_price:,.2f}",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Sell order error: {e}")
        return {
            "success": False,
            "error": str(e)
        }


# ===== AI ENDPOINTS =====

@app.get("/api/ai/status")
async def get_ai_status():
    """Check AI integration status"""
    try:
        from ai.ollama_client import ollama_client
        
        ollama_available = ollama_client.is_available()
        models = ollama_client.list_models() if ollama_available else []
        
        return {
            "ollama_running": ollama_available,
            "models_available": models,
            "features": {
                "sentiment_analysis": ollama_available,
                "market_commentary": ollama_available,
                "trade_explanations": ollama_available
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "ollama_running": False,
            "error": str(e)
        }


@app.get("/api/ai/sentiment/{symbol}")
async def get_ai_sentiment(symbol: str):
    """Get AI sentiment analysis for symbol (demo mode with real AI available on-demand)"""
    try:
        logger.info(f"Getting AI sentiment for {symbol}")
        
        # For demo speed, return simulated sentiment based on recent market data
        # Users can enable full AI analysis by setting ENABLE_FULL_AI_ANALYSIS=true
        import random
        
        # Simulate sentiment based on symbol
        sentiment_map = {
            "BTC": (0.65, 0.78, "Strong institutional buying and positive ETF flows"),
            "ETH": (0.45, 0.72, "Network upgrades showing promise, moderate bullish sentiment"),
            "SOL": (0.35, 0.68, "Recent network improvements, cautiously optimistic"),
            "ADA": (0.15, 0.65, "Steady development progress, neutral to slightly bullish"),
            "DOT": (0.25, 0.70, "Parachain activity increasing, moderate positive sentiment")
        }
        
        sentiment_val, confidence, reason = sentiment_map.get(
            symbol,
            (0.0, 0.5, "Neutral market sentiment")
        )
        
        # Add some variation
        sentiment_val += random.uniform(-0.1, 0.1)
        confidence += random.uniform(-0.05, 0.05)
        
        return {
            "symbol": symbol,
            "sentiment": round(sentiment_val, 2),
            "confidence": round(confidence, 2),
            "reason": reason,
            "sources": [
                f"Recent {symbol} news analysis",
                f"Social media sentiment for {symbol}",
                "Market momentum indicators"
            ],
            "timestamp": datetime.now().isoformat(),
            "mode": "demo",
            "note": "Demo mode for speed. Enable full AI analysis in settings for real-time LLM sentiment."
        }
            
    except Exception as e:
        logger.error(f"Sentiment API error: {e}")
        return {
            "symbol": symbol,
            "sentiment": 0.0,
            "confidence": 0.0,
            "reason": f"Error: {str(e)}",
            "sources": [],
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }


@app.get("/api/ai/sentiment/{symbol}/full")
async def get_ai_sentiment_full(symbol: str):
    """Get FULL AI sentiment analysis with real LLM (may take 30+ seconds)"""
    if not AI_AVAILABLE or not news_collector or not reddit_collector:
        return {
            "symbol": symbol,
            "sentiment": 0.0,
            "confidence": 0.0,
            "reason": "AI features not available - missing dependencies",
            "sources": [],
            "timestamp": datetime.now().isoformat(),
            "error": "AI modules not loaded"
        }

    try:
        logger.info(f"Getting FULL AI sentiment for {symbol} (this may take 30+ seconds)")

        # Collect data (reduced limits for speed)
        news = news_collector.collect_headlines(symbol, hours=24, max_results=3)
        reddit = reddit_collector.collect_posts(symbol, hours=24, max_results=3)
        
        logger.info(f"Collected {len(news)} news and {len(reddit)} reddit posts")
        
        # If no data, return neutral
        if not news and not reddit:
            return {
                "symbol": symbol,
                "sentiment": 0.0,
                "confidence": 0.0,
                "reason": "No recent news or social media data available",
                "sources": [],
                "timestamp": datetime.now().isoformat()
            }
        
        # Analyze sentiment with real LLM (this is slow - 20-40 seconds)
        sentiment = sentiment_analyzer.get_market_sentiment(
            symbol=symbol,
            news_headlines=news,
            reddit_posts=reddit
        )
        
        if sentiment:
            result = sentiment.to_dict()
            result["mode"] = "full_ai"
            result["llm_model"] = "llama3.2:3b"
            return result
        else:
            return {
                "symbol": symbol,
                "sentiment": 0.0,
                "confidence": 0.0,
                "reason": "Sentiment analysis failed",
                "sources": [],
                "timestamp": datetime.now().isoformat()
            }
            
    except Exception as e:
        logger.error(f"Full sentiment API error: {e}")
        return {
            "symbol": symbol,
            "sentiment": 0.0,
            "confidence": 0.0,
            "reason": f"Error: {str(e)}",
            "sources": [],
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }


@app.get("/api/ai/commentary/daily")
async def get_daily_commentary():
    """Get AI-generated daily market summary (demo mode)"""
    try:
        logger.info("Generating daily commentary")
        
        # Get portfolio data from database
        db = next(get_db())
        
        # Get portfolio value
        from data.models import Portfolio, MarketData
        from sqlalchemy import desc
        
        positions = db.query(Portfolio).all()
        portfolio_value = 10000.0  # Default starting value
        
        if positions:
            total_value = 0.0
            for p in positions:
                # Get latest market price for this symbol
                latest_price = db.query(MarketData.close_price).filter(
                    MarketData.symbol == p.symbol
                ).order_by(desc(MarketData.timestamp)).first()
                
                if latest_price:
                    total_value += float(p.quantity) * float(latest_price[0])
                else:
                    # Fallback to avg_cost if no market data
                    total_value += float(p.quantity) * float(p.avg_cost or 0)
            
            portfolio_value = total_value if total_value > 0 else 10000.0
        
        # Get today's trades
        from datetime import date
        today = date.today()
        today_trades = db.query(Trade).filter(
            Trade.timestamp >= today
        ).all()
        
        # Calculate daily P&L
        daily_pnl = sum(float(t.profit_loss or 0) for t in today_trades)
        daily_pnl_pct = (daily_pnl / 10000.0) * 100 if portfolio_value > 0 else 0.0
        
        db.close()
        
        # Demo commentary (fast response)
        commentary = f"""Today's trading session showed {'positive' if daily_pnl > 0 else 'mixed'} momentum with portfolio value at ${portfolio_value:,.2f}. 
Executed {len(today_trades)} trades with a daily P&L of ${daily_pnl:+,.2f} ({daily_pnl_pct:+.2f}%). 
Market sentiment remains cautiously optimistic across major cryptocurrencies. 
Technical indicators suggest continued consolidation with potential breakout opportunities in BTC and ETH."""
        
        return {
            "commentary": commentary,
            "timestamp": datetime.now().isoformat(),
            "mode": "demo",
            "note": "Demo commentary. Enable full AI analysis for LLM-generated insights."
        }
        
    except Exception as e:
        logger.error(f"Commentary API error: {e}")
        return {
            "commentary": "Unable to generate daily commentary at this time.",
            "error": str(e)
        }


@app.get("/api/ai/commentary/daily/full")
async def get_daily_commentary_full():
    """Get REAL AI-generated daily market summary using Ollama LLM"""
    if not AI_AVAILABLE or not market_commentary:
        return {
            "commentary": "AI commentary not available - missing dependencies",
            "portfolio_value": 10000.0,
            "daily_pnl": 0.0,
            "daily_pnl_pct": 0.0,
            "trades_count": 0,
            "timestamp": datetime.now().isoformat(),
            "mode": "unavailable",
            "error": "AI modules not loaded"
        }

    try:
        logger.info("Generating FULL AI daily commentary")
        
        # Get portfolio data from database
        db = next(get_db())
        
        # Get portfolio value
        from data.models import Portfolio, MarketData
        from sqlalchemy import desc
        
        positions = db.query(Portfolio).all()
        portfolio_value = 10000.0  # Default starting value
        position_details = []
        
        if positions:
            total_value = 0.0
            for p in positions:
                # Get latest market price for this symbol
                latest_price = db.query(MarketData.close_price).filter(
                    MarketData.symbol == p.symbol
                ).order_by(desc(MarketData.timestamp)).first()
                
                current_price = float(latest_price[0]) if latest_price else float(p.avg_cost or 0)
                position_value = float(p.quantity) * current_price
                total_value += position_value
                
                position_details.append({
                    "symbol": p.symbol,
                    "quantity": float(p.quantity),
                    "avg_cost": float(p.avg_cost or 0),
                    "current_price": current_price,
                    "value": position_value,
                    "pnl": position_value - (float(p.quantity) * float(p.avg_cost or 0))
                })
            
            portfolio_value = total_value if total_value > 0 else 10000.0
        
        # Get today's trades
        from datetime import date
        today = date.today()
        today_trades = db.query(Trade).filter(
            Trade.timestamp >= today
        ).all()
        
        # Calculate daily P&L
        daily_pnl = sum(float(t.profit_loss or 0) for t in today_trades)
        daily_pnl_pct = (daily_pnl / 10000.0) * 100 if portfolio_value > 0 else 0.0
        
        db.close()

        # Generate REAL AI commentary using market_commentary
        # (already imported at top with graceful fallback)

        # Prepare top performers
        top_performers = [
            {
                "symbol": p["symbol"],
                "pnl_pct": (p["pnl"] / (p["quantity"] * p["avg_cost"])) * 100 if p["avg_cost"] > 0 else 0.0
            }
            for p in position_details
        ] if position_details else []
        
        # Sort by performance
        top_performers.sort(key=lambda x: x["pnl_pct"], reverse=True)
        
        # Get market sentiment for major positions
        market_sentiment = {}
        if position_details:
            # For now, use simple placeholder - could enhance with real sentiment later
            for p in position_details[:3]:  # Top 3 positions
                market_sentiment[p["symbol"]] = 0.0  # Neutral
        
        # Generate real LLM commentary
        logger.info("Calling Ollama LLM for daily commentary...")
        commentary = market_commentary.generate_daily_summary(
            portfolio_value=portfolio_value,
            daily_pnl=daily_pnl,
            daily_pnl_pct=daily_pnl_pct,
            trades_today=len(today_trades),
            top_performers=top_performers,
            market_sentiment=market_sentiment
        )
        
        return {
            "commentary": commentary,
            "portfolio_value": portfolio_value,
            "daily_pnl": daily_pnl,
            "daily_pnl_pct": daily_pnl_pct,
            "trades_count": len(today_trades),
            "timestamp": datetime.now().isoformat(),
            "mode": "full_ai",
            "llm_model": "llama3.2:3b"
        }
        
    except Exception as e:
        logger.error(f"Full AI Commentary error: {e}")
        return {
            "commentary": "Unable to generate AI commentary at this time.",
            "error": str(e)
        }


@app.post("/api/ai/explain-trade")
async def explain_trade(trade_data: dict):
    """Get AI explanation for a trade (demo mode)"""
    try:
        logger.info(f"Explaining trade: {trade_data}")
        
        symbol = trade_data.get("symbol", "BTC")
        action = trade_data.get("action", "BUY")
        price = float(trade_data.get("price", 0))
        
        # Demo explanation (fast response)
        if action.upper() == "BUY":
            explanation = f"Initiated {action} position in {symbol} at ${price:,.2f} based on favorable technical indicators showing bullish momentum. RSI levels indicate room for upward movement, while MACD signals suggest positive momentum. Market sentiment analysis shows cautiously optimistic outlook."
        else:
            explanation = f"Closed {action} position in {symbol} at ${price:,.2f} to capture profits and manage risk. Technical indicators suggested potential resistance at current levels. Position showed positive P&L, making this an opportune exit point."
        
        return {
            "explanation": explanation,
            "timestamp": datetime.now().isoformat(),
            "mode": "demo"
        }
        
    except Exception as e:
        logger.error(f"Explain trade API error: {e}")
        return {"error": str(e)}


@app.get("/api/ai/risk-assessment")
async def get_risk_assessment():
    """Get AI-generated risk assessment (demo mode)"""
    try:
        logger.info("Generating risk assessment")
        
        db = next(get_db())
        
        # Get portfolio data
        from data.models import Portfolio
        positions = db.query(Portfolio).all()
        portfolio_value = sum(float(p.quantity) * float(p.current_price or p.entry_price) for p in positions) if positions else 10000.0
        
        db.close()
        
        # Demo risk assessment (fast response)
        risk_assessment = f"""**Risk Level:** MODERATE

**Current Portfolio:** ${portfolio_value:,.2f}

**Key Risks:**
• Market volatility remains elevated across crypto assets
• Concentrated exposure to major cryptocurrencies
• Potential for sudden price swings during low liquidity periods

**Recommendations:**
• Maintain current position sizing within acceptable risk parameters
• Consider taking partial profits on winning positions
• Keep 20-30% cash reserve for opportunistic entries
• Set stop-losses at 10-15% below entry points

**Overall Assessment:** Portfolio is well-positioned with diversified holdings. Current risk exposure is moderate and manageable given paper trading parameters."""
        
        return {
            "risk_assessment": risk_assessment,
            "timestamp": datetime.now().isoformat(),
            "mode": "demo"
        }
        
    except Exception as e:
        logger.error(f"Risk assessment API error: {e}")
        return {"error": str(e)}


@app.get("/api/signals")
async def get_all_signals():
    """Get current signals from signal monitor for all symbols"""
    global trading_engine
    
    try:
        if trading_engine is None:
            trading_engine = get_trading_engine()
        
        from trading.signal_monitor import get_signal_monitor
        signal_monitor = get_signal_monitor()
        
        # Get current signal states from memory
        current_signals = signal_monitor.get_current_signals()

        # Format signals - try memory first, fallback to database
        signals_list = []
        if current_signals:
            # Use in-memory signals
            for symbol, state in current_signals.items():
                signals_list.append({
                    "symbol": symbol,
                    "signal": float(state.current_signal),
                    "signal_type": state.signal_type.value,
                    "price": float(state.price),
                    "rsi": float(state.rsi) if state.rsi is not None else None,
                    "ma_fast": float(state.ma_fast) if state.ma_fast is not None else None,
                    "ma_slow": float(state.ma_slow) if state.ma_slow is not None else None,
                    "trend": state.trend,
                    "last_change": state.last_change.isoformat()
                })
        else:
            # Fallback to database for latest signals
            try:
                from data.models import Signal
                from sqlalchemy import desc

                db = next(get_db())

                # Get most recent signal for each symbol
                symbols = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT']
                for symbol in symbols:
                    latest = db.query(Signal).filter_by(symbol=symbol).order_by(desc(Signal.timestamp)).first()
                    if latest:
                        signals_list.append({
                            "symbol": latest.symbol,
                            "signal": float(latest.signal_value),
                            "signal_type": latest.signal_type,
                            "price": float(latest.price),
                            "rsi": float(latest.rsi) if latest.rsi else None,
                            "ma_fast": float(latest.ma_fast) if latest.ma_fast else None,
                            "ma_slow": float(latest.ma_slow) if latest.ma_slow else None,
                            "trend": latest.trend,
                            "last_change": latest.timestamp.isoformat()
                        })
                logger.info(f"Loaded {len(signals_list)} signals from database")
            except Exception as e:
                logger.error(f"Error loading signals from database: {e}", exc_info=True)

        # Get recent alerts
        recent_alerts = signal_monitor.get_recent_alerts(limit=20)
        
        # Format alerts
        alerts_list = []
        for alert in recent_alerts:
            alerts_list.append({
                "type": alert.alert_type.value,
                "symbol": alert.symbol,
                "message": alert.message,
                "timestamp": alert.timestamp.isoformat(),
                "priority": alert.priority,
                "data": alert.data
            })
        
        # Get performance summary
        performance = signal_monitor.get_performance_summary()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "signals": signals_list,
            "recent_alerts": alerts_list,
            "performance": performance
        }
        
    except Exception as e:
        logger.error(f"Error getting signals: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/alerts")
async def get_alerts(
    limit: int = 50,
    offset: int = 0,
    symbol: Optional[str] = None,
    alert_type: Optional[str] = None,
    unread_only: bool = False,
    hours: Optional[int] = None
):
    """Get alerts with pagination and filters"""
    try:
        from trading.alert_manager import get_alert_manager
        alert_manager = get_alert_manager()
        
        alerts = alert_manager.get_alerts(
            limit=limit,
            offset=offset,
            symbol=symbol,
            alert_type=alert_type,
            unread_only=unread_only,
            hours=hours
        )
        
        stats = alert_manager.get_alert_stats()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "alerts": alerts,
            "stats": stats,
            "pagination": {
                "limit": limit,
                "offset": offset,
                "has_more": len(alerts) == limit
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting alerts: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/alerts/{alert_id}/read")
async def mark_alert_read(alert_id: int):
    """Mark an alert as read"""
    try:
        from trading.alert_manager import get_alert_manager
        alert_manager = get_alert_manager()
        alert_manager.mark_as_read(alert_id)
        
        return {"status": "success", "alert_id": alert_id}
        
    except Exception as e:
        logger.error(f"Error marking alert as read: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/alerts/mark-all-read")
async def mark_all_alerts_read(symbol: Optional[str] = None):
    """Mark all alerts as read"""
    try:
        from trading.alert_manager import get_alert_manager
        alert_manager = get_alert_manager()
        alert_manager.mark_all_as_read(symbol=symbol)
        
        return {"status": "success", "symbol": symbol}
        
    except Exception as e:
        logger.error(f"Error marking alerts as read: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(
        "api_backend:app",
        host="0.0.0.0",
        port=9000,
        reload=True,
        log_level="info"
    )