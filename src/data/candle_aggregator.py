"""
Real-Time Candle Aggregator
Builds multi-timeframe candles from live price data
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from collections import defaultdict
import pandas as pd

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from data.live_feed import PriceUpdate, get_data_feed_manager
from data.database import get_db
from data.models import MarketData

logger = logging.getLogger(__name__)

@dataclass
class Candle:
    """OHLCV candle data"""
    symbol: str
    timestamp: datetime
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    volume: float
    timeframe: str  # '1m', '5m', '15m', '1h', etc.

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'symbol': self.symbol,
            'timestamp': self.timestamp,
            'open_price': self.open_price,
            'high_price': self.high_price,
            'low_price': self.low_price,
            'close_price': self.close_price,
            'volume': self.volume,
            'timeframe': self.timeframe
        }

class CandleAggregator:
    """
    Aggregates real-time price updates into candles

    Features:
    - Builds 5-minute candles from tick data
    - Maintains historical candle buffer
    - Saves completed candles to database
    - Provides current candle state
    """

    def __init__(self, symbols: List[str], timeframe_minutes: int = 5,
                 buffer_size: int = 500):
        """
        Args:
            symbols: List of symbols to track
            timeframe_minutes: Candle timeframe in minutes (default: 5)
            buffer_size: Number of completed candles to keep in memory
        """
        self.symbols = symbols
        self.timeframe_minutes = timeframe_minutes
        self.timeframe_str = f"{timeframe_minutes}m"
        self.buffer_size = buffer_size

        # Current candles being built (one per symbol)
        self.current_candles: Dict[str, Candle] = {}

        # Completed candles buffer
        self.candle_history: Dict[str, List[Candle]] = defaultdict(list)

        # Track first price of current period
        self.period_start_times: Dict[str, datetime] = {}

        logger.info(f"Candle Aggregator initialized: {timeframe_minutes}m candles for {len(symbols)} symbols")

    def get_current_period_start(self, timestamp: datetime) -> datetime:
        """Get the start time of the current period"""
        # Round down to nearest period
        minutes = (timestamp.minute // self.timeframe_minutes) * self.timeframe_minutes
        return timestamp.replace(minute=minutes, second=0, microsecond=0)

    def process_price_update(self, update: PriceUpdate):
        """
        Process incoming price update and build/update candles

        Args:
            update: PriceUpdate from live data feed
        """
        symbol = update.symbol
        price = update.price
        timestamp = update.timestamp
        volume = update.volume or 0

        # Get current period start
        period_start = self.get_current_period_start(timestamp)

        # Check if we need to close the current candle and start a new one
        if symbol in self.current_candles:
            current_candle = self.current_candles[symbol]

            # If we've moved to a new period, close the current candle
            if period_start > current_candle.timestamp:
                self._complete_candle(symbol, current_candle)
                self.current_candles[symbol] = None

        # Start a new candle if needed
        if symbol not in self.current_candles or self.current_candles[symbol] is None:
            self.current_candles[symbol] = Candle(
                symbol=symbol,
                timestamp=period_start,
                open_price=price,
                high_price=price,
                low_price=price,
                close_price=price,
                volume=volume,
                timeframe=self.timeframe_str
            )
            logger.debug(f"Started new {self.timeframe_str} candle for {symbol} at {period_start}")

        # Update current candle
        else:
            candle = self.current_candles[symbol]
            candle.high_price = max(candle.high_price, price)
            candle.low_price = min(candle.low_price, price)
            candle.close_price = price
            candle.volume += volume

    def _complete_candle(self, symbol: str, candle: Candle):
        """Complete and store a candle"""
        # Add to history
        self.candle_history[symbol].append(candle)

        # Limit buffer size
        if len(self.candle_history[symbol]) > self.buffer_size:
            self.candle_history[symbol] = self.candle_history[symbol][-self.buffer_size:]

        # Save to database
        self._save_to_database(candle)

        logger.info(f"Completed {self.timeframe_str} candle: {symbol} @ {candle.timestamp} "
                   f"O:{candle.open_price:.2f} H:{candle.high_price:.2f} "
                   f"L:{candle.low_price:.2f} C:{candle.close_price:.2f}")

    def _save_to_database(self, candle: Candle):
        """Save candle to database"""
        try:
            from data.database import get_db_sync
            from sqlalchemy.exc import IntegrityError
            db = get_db_sync()
            
            try:
                market_record = MarketData(
                    symbol=candle.symbol,
                    timestamp=candle.timestamp,
                    open_price=candle.open_price,
                    high_price=candle.high_price,
                    low_price=candle.low_price,
                    close_price=candle.close_price,
                    volume=candle.volume
                )

                db.add(market_record)
                db.commit()

                logger.debug(f"Saved {self.timeframe_str} candle to database: {candle.symbol}")

            except IntegrityError:
                # Duplicate candle, skip silently
                db.rollback()
            except Exception as e:
                logger.error(f"Error saving candle to database: {e}")
                db.rollback()
            finally:
                db.close()
        except Exception as e:
            logger.error(f"Database connection error: {e}")

    def get_candle_history(self, symbol: str, limit: Optional[int] = None) -> List[Candle]:
        """
        Get historical candles for a symbol

        Args:
            symbol: Trading symbol
            limit: Number of recent candles to return (None = all)

        Returns:
            List of candles, most recent last
        """
        candles = self.candle_history.get(symbol, [])

        if limit:
            return candles[-limit:]

        return candles

    def get_candles_as_dataframe(self, symbol: str, limit: Optional[int] = None) -> pd.DataFrame:
        """
        Get candle history as pandas DataFrame

        Args:
            symbol: Trading symbol
            limit: Number of recent candles to return

        Returns:
            DataFrame with OHLCV data
        """
        candles = self.get_candle_history(symbol, limit)

        if not candles:
            return pd.DataFrame()

        df = pd.DataFrame([
            {
                'timestamp': c.timestamp,
                'open_price': c.open_price,
                'high_price': c.high_price,
                'low_price': c.low_price,
                'close_price': c.close_price,
                'volume': c.volume
            }
            for c in candles
        ])

        df.set_index('timestamp', inplace=True)
        return df

    def get_current_candle(self, symbol: str) -> Optional[Candle]:
        """Get the current (incomplete) candle for a symbol"""
        return self.current_candles.get(symbol)

    def get_all_symbols(self) -> List[str]:
        """Get all tracked symbols"""
        return self.symbols

    async def load_historical_from_db(self, symbol: str, lookback_minutes: int = 2400):
        """
        Load historical candles from database (for initial buffer)

        Args:
            symbol: Trading symbol
            lookback_minutes: How far back to load (default: 2400 min = 40 hours)
        """
        try:
            from data.database import get_db_sync
            db = get_db_sync()
            
            try:
                # Calculate lookback time
                lookback_time = datetime.now() - timedelta(minutes=lookback_minutes)

                # Query database for historical data
                records = db.query(MarketData).filter(
                    MarketData.symbol == symbol,
                    MarketData.timestamp >= lookback_time
                ).order_by(MarketData.timestamp.asc()).all()
            except Exception as e:
                logger.error(f"Error loading historical candles: {e}")
                records = []
            finally:
                db.close()
        except Exception as e:
            logger.error(f"Database connection error: {e}")
            records = []
        
        try:

            if not records:
                logger.warning(f"No historical data found for {symbol}")
                return

            # Group into candles
            for record in records:
                # Create a fake PriceUpdate to reuse aggregation logic
                update = PriceUpdate(
                    symbol=record.symbol,
                    price=float(record.close_price),
                    timestamp=record.timestamp,
                    volume=float(record.volume)
                )

                # Process each record
                self.process_price_update(update)

            logger.info(f"Loaded {len(records)} historical records for {symbol}, "
                       f"created {len(self.candle_history[symbol])} candles")

        except Exception as e:
            logger.error(f"Error loading historical data for {symbol}: {e}")


# Global aggregator
_candle_aggregator: Optional[CandleAggregator] = None

def get_candle_aggregator(symbols: List[str] = None,
                          timeframe_minutes: int = 5) -> CandleAggregator:
    """Get the global candle aggregator"""
    global _candle_aggregator

    if _candle_aggregator is None:
        default_symbols = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'ADAUSDT', 'DOTUSDT']
        _candle_aggregator = CandleAggregator(
            symbols or default_symbols,
            timeframe_minutes=timeframe_minutes
        )

    return _candle_aggregator


async def start_candle_aggregator(symbols: List[str] = None,
                                  timeframe_minutes: int = 5) -> CandleAggregator:
    """
    Start the candle aggregator and connect to live data feed

    Args:
        symbols: List of symbols to track
        timeframe_minutes: Candle timeframe in minutes

    Returns:
        CandleAggregator instance
    """
    # Get or create aggregator
    aggregator = get_candle_aggregator(symbols, timeframe_minutes)

    # Load historical data for each symbol
    for symbol in aggregator.symbols:
        await aggregator.load_historical_from_db(symbol)

    # Subscribe to live data feed
    data_feed = get_data_feed_manager()
    data_feed.subscribe_to_prices(aggregator.process_price_update)

    logger.info(f"Candle aggregator started: {timeframe_minutes}m candles")

    return aggregator


if __name__ == "__main__":
    # Demo usage
    import asyncio

    async def demo():
        print("Candle Aggregator Demo")
        print("=" * 70)

        # Create aggregator for 5-minute candles
        aggregator = CandleAggregator(['BTCUSDT', 'ETHUSDT'], timeframe_minutes=5)

        # Simulate price updates
        now = datetime.now()
        prices = [32000, 32100, 32050, 32200, 32150]

        for i, price in enumerate(prices):
            timestamp = now + timedelta(minutes=i)
            update = PriceUpdate(
                symbol='BTCUSDT',
                price=price,
                timestamp=timestamp,
                volume=100.0
            )

            aggregator.process_price_update(update)
            print(f"\nProcessed: ${price} at {timestamp.strftime('%H:%M')}")

            current = aggregator.get_current_candle('BTCUSDT')
            if current:
                print(f"Current candle: O:{current.open_price} H:{current.high_price} "
                      f"L:{current.low_price} C:{current.close_price}")

        # Show history
        history = aggregator.get_candle_history('BTCUSDT')
        print(f"\nCompleted candles: {len(history)}")

    asyncio.run(demo())
