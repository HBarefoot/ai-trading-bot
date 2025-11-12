"""
Live Data Feed Module
Provides real-time cryptocurrency price feeds
"""
import asyncio
import websockets
import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Callable, Optional
import threading
from dataclasses import dataclass

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from data.database import get_db
from data.models import MarketData
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

@dataclass
class PriceUpdate:
    symbol: str
    price: float
    timestamp: datetime
    volume: Optional[float] = None
    change_24h: Optional[float] = None

class LiveDataFeed:
    """Base class for live data feeds"""
    
    def __init__(self, symbols: List[str]):
        self.symbols = symbols
        self.subscribers: List[Callable] = []
        self.running = False
        self.latest_prices: Dict[str, PriceUpdate] = {}
    
    def subscribe(self, callback: Callable[[PriceUpdate], None]):
        """Subscribe to price updates"""
        self.subscribers.append(callback)
    
    def unsubscribe(self, callback: Callable):
        """Unsubscribe from price updates"""
        if callback in self.subscribers:
            self.subscribers.remove(callback)
    
    def notify_subscribers(self, update: PriceUpdate):
        """Notify all subscribers of price update"""
        self.latest_prices[update.symbol] = update
        
        for callback in self.subscribers:
            try:
                callback(update)
            except Exception as e:
                logger.error(f"Error in subscriber callback: {e}")
    
    async def start(self):
        """Start the data feed"""
        self.running = True
        logger.info(f"Starting live data feed for {self.symbols}")
    
    async def stop(self):
        """Stop the data feed"""
        self.running = False
        logger.info("Live data feed stopped")
    
    def get_latest_price(self, symbol: str) -> Optional[PriceUpdate]:
        """Get latest price for a symbol"""
        return self.latest_prices.get(symbol)

class BinanceWebSocketFeed(LiveDataFeed):
    """Binance.US WebSocket data feed"""
    
    def __init__(self, symbols: List[str], use_us: bool = True):
        super().__init__(symbols)
        # Use Binance.US WebSocket endpoint for US users
        if use_us:
            self.ws_url = "wss://stream.binance.us:9443/ws/"
            logger.info("Using Binance.US WebSocket endpoint")
        else:
            self.ws_url = "wss://stream.binance.com:9443/ws/"
            logger.info("Using global Binance WebSocket endpoint")
        self.websocket = None
    
    async def start(self):
        """Start Binance WebSocket feed"""
        await super().start()
        
        # Convert symbols to lowercase for Binance API
        streams = [f"{symbol.lower()}@ticker" for symbol in self.symbols]
        stream_url = self.ws_url + "/".join(streams)
        
        try:
            while self.running:
                try:
                    async with websockets.connect(stream_url) as websocket:
                        self.websocket = websocket
                        logger.info(f"Connected to Binance.US WebSocket: {streams}")
                        
                        async for message in websocket:
                            if not self.running:
                                break
                                
                            await self.handle_message(message)
                            
                except websockets.exceptions.ConnectionClosed:
                    if self.running:
                        logger.warning("WebSocket connection closed, reconnecting in 5 seconds...")
                        await asyncio.sleep(5)
                except Exception as e:
                    logger.error(f"WebSocket error: {e}")
                    if self.running:
                        await asyncio.sleep(5)
                        
        except Exception as e:
            logger.error(f"Error starting WebSocket feed: {e}")
    
    async def handle_message(self, message: str):
        """Handle incoming WebSocket message"""
        try:
            data = json.loads(message)
            
            if 'e' in data and data['e'] == '24hrTicker':
                symbol = data['s']  # Symbol
                price = float(data['c'])  # Current price
                volume = float(data['v'])  # Volume
                change_24h = float(data['P'])  # 24h price change percent
                
                update = PriceUpdate(
                    symbol=symbol,
                    price=price,
                    timestamp=datetime.now(timezone.utc),
                    volume=volume,
                    change_24h=change_24h
                )
                
                self.notify_subscribers(update)
                
        except Exception as e:
            logger.error(f"Error handling WebSocket message: {e}")

class MockDataFeed(LiveDataFeed):
    """Mock data feed for testing"""
    
    def __init__(self, symbols: List[str]):
        super().__init__(symbols)
        self.base_prices = {
            'BTCUSDT': 32030.58,
            'ETHUSDT': 2529.55,
            'SOLUSDT': 108.04,
            'ADAUSDT': 0.55,
            'DOTUSDT': 5.23
        }
    
    async def start(self):
        """Start mock data feed"""
        await super().start()
        
        while self.running:
            for symbol in self.symbols:
                # Simulate price movement with random walk
                import random
                
                base_price = self.base_prices.get(symbol, 100.0)
                # Small random changes (-1% to +1%)
                price_change = random.uniform(-0.01, 0.01)
                new_price = base_price * (1 + price_change)
                
                # Update base price for next iteration
                self.base_prices[symbol] = new_price
                
                update = PriceUpdate(
                    symbol=symbol,
                    price=new_price,
                    timestamp=datetime.now(timezone.utc),
                    volume=random.uniform(1000, 10000),
                    change_24h=random.uniform(-5, 5)
                )
                
                self.notify_subscribers(update)
            
            await asyncio.sleep(5)  # Update every 5 seconds

class DataFeedManager:
    """Manages live data feeds"""
    
    def __init__(self, symbols: List[str], use_mock: bool = True):
        self.symbols = symbols
        self.use_mock = use_mock
        
        if use_mock:
            self.feed = MockDataFeed(symbols)
        else:
            # Use Binance.US WebSocket for US users
            self.feed = BinanceWebSocketFeed(symbols, use_us=True)
        
        self.running = False
        self.feed_task = None
        
        # Set up database storage
        self.store_to_db = True
        self.db_update_interval = 60  # Store to DB every 60 seconds
        self.last_db_update = {}
    
    def subscribe_to_prices(self, callback: Callable[[PriceUpdate], None]):
        """Subscribe to price updates"""
        self.feed.subscribe(callback)
    
    def get_latest_prices(self) -> Dict[str, PriceUpdate]:
        """Get all latest prices"""
        return self.feed.latest_prices.copy()
    
    def get_latest_price(self, symbol: str) -> Optional[PriceUpdate]:
        """Get latest price for a symbol"""
        return self.feed.get_latest_price(symbol)
    
    async def start(self):
        """Start the data feed manager"""
        if self.running:
            logger.warning("Data feed manager is already running")
            return
        
        self.running = True
        
        # Subscribe to our own feed for database storage
        if self.store_to_db:
            self.feed.subscribe(self._store_price_update)
        
        # Start the feed
        self.feed_task = asyncio.create_task(self.feed.start())
        
        logger.info("Data feed manager started")
    
    async def stop(self):
        """Stop the data feed manager"""
        self.running = False
        
        if self.feed:
            await self.feed.stop()
        
        if self.feed_task:
            self.feed_task.cancel()
            try:
                await self.feed_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Data feed manager stopped")
    
    def _store_price_update(self, update: PriceUpdate):
        """Store price update to database"""
        try:
            # Only store to DB every minute per symbol to avoid spam
            now = datetime.now()
            last_update = self.last_db_update.get(update.symbol)
            
            if last_update is None or (now - last_update).seconds >= self.db_update_interval:
                self._save_to_database(update)
                self.last_db_update[update.symbol] = now
                
        except Exception as e:
            logger.error(f"Error storing price update to database: {e}")
    
    def _save_to_database(self, update: PriceUpdate):
        """Save price update to database"""
        try:
            db = next(get_db())
            
            # Create a new market data record
            market_record = MarketData(
                symbol=update.symbol,
                timestamp=update.timestamp,
                open_price=update.price,  # For live data, use current price for all OHLC
                high_price=update.price,
                low_price=update.price,
                close_price=update.price,
                volume=update.volume or 0
            )
            
            db.add(market_record)
            db.commit()
            db.close()
            
            logger.debug(f"Stored price update: {update.symbol} @ ${update.price:.2f}")
            
        except Exception as e:
            logger.error(f"Error saving to database: {e}")

# Global data feed manager
data_feed_manager = None

def get_data_feed_manager(symbols: List[str] = None, use_mock: bool = True) -> DataFeedManager:
    """Get the global data feed manager"""
    global data_feed_manager
    
    if data_feed_manager is None:
        default_symbols = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'ADAUSDT', 'DOTUSDT']
        data_feed_manager = DataFeedManager(symbols or default_symbols, use_mock)
    
    return data_feed_manager

# Convenience functions
async def start_live_feed(symbols: List[str] = None, use_mock: bool = True):
    """Start the live data feed"""
    manager = get_data_feed_manager(symbols, use_mock)
    await manager.start()
    return manager

async def stop_live_feed():
    """Stop the live data feed"""
    global data_feed_manager
    if data_feed_manager:
        await data_feed_manager.stop()
        data_feed_manager = None