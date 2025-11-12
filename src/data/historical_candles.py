#!/usr/bin/env python3
"""
Pre-load historical 5-minute candles from Binance.US for immediate dashboard display
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import requests
from datetime import datetime, timedelta
import logging
from typing import List, Dict
from data.database import get_db
from data.models import MarketData
from sqlalchemy.exc import IntegrityError

logger = logging.getLogger(__name__)

def fetch_recent_5m_candles(symbol: str = 'BTCUSDT', hours: int = 8) -> List[Dict]:
    """
    Fetch recent 5-minute candles from Binance.US
    
    Args:
        symbol: Trading pair (e.g., 'BTCUSDT')
        hours: Number of hours to fetch (8 hours = 96 candles)
    
    Returns:
        List of candle dictionaries
    """
    base_url = "https://api.binance.us/api/v3/klines"
    
    end_time = datetime.now()
    start_time = end_time - timedelta(hours=hours)
    
    start_ts = int(start_time.timestamp() * 1000)
    end_ts = int(end_time.timestamp() * 1000)
    
    params = {
        'symbol': symbol,
        'interval': '5m',  # 5-minute candles
        'startTime': start_ts,
        'endTime': end_ts,
        'limit': 1000
    }
    
    try:
        response = requests.get(base_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        candles = []
        for candle in data:
            candles.append({
                'timestamp': datetime.fromtimestamp(candle[0] / 1000),
                'open': float(candle[1]),
                'high': float(candle[2]),
                'low': float(candle[3]),
                'close': float(candle[4]),
                'volume': float(candle[5])
            })
        
        logger.info(f"Fetched {len(candles)} 5m candles for {symbol} (last {hours} hours)")
        return candles
        
    except Exception as e:
        logger.error(f"Error fetching 5m candles from Binance.US: {e}")
        return []


def preload_historical_candles_to_db(symbols: List[str] = None, hours: int = 8):
    """
    Pre-load historical 5-minute candles into database for immediate dashboard availability
    
    Args:
        symbols: List of symbols to fetch (e.g., ['BTCUSDT', 'ETHUSDT', 'SOLUSDT'])
        hours: Number of hours to fetch
    """
    if symbols is None:
        symbols = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT']
    
    # Symbol mapping: Binance format -> DB format
    symbol_map = {
        'BTCUSDT': 'BTC/USDT',
        'ETHUSDT': 'ETH/USDT',
        'SOLUSDT': 'SOL/USDT',
        'ADAUSDT': 'ADA/USDT',
        'DOTUSDT': 'DOT/USDT'
    }
    
    db = next(get_db())
    
    for binance_symbol in symbols:
        db_symbol = symbol_map.get(binance_symbol, binance_symbol)
        
        logger.info(f"Pre-loading {hours}h of 5m candles for {db_symbol}...")
        
        candles = fetch_recent_5m_candles(binance_symbol, hours)
        
        if not candles:
            logger.warning(f"No candles fetched for {binance_symbol}")
            continue
        
        saved = 0
        skipped = 0
        
        for candle in candles:
            market_data = MarketData(
                symbol=db_symbol,
                timestamp=candle['timestamp'],
                open_price=candle['open'],
                high_price=candle['high'],
                low_price=candle['low'],
                close_price=candle['close'],
                volume=candle['volume']
            )
            
            try:
                db.add(market_data)
                db.commit()
                saved += 1
            except IntegrityError:
                db.rollback()
                skipped += 1
        
        logger.info(f"  {db_symbol}: Saved {saved} new candles, skipped {skipped} duplicates")
    
    db.close()
    logger.info("Historical candle pre-load complete")


def get_db_candle_count(symbol: str = 'BTC/USDT') -> int:
    """Check how many candles are in the database for a symbol"""
    try:
        db = next(get_db())
        
        # Get candles from last 8 hours
        cutoff = datetime.now() - timedelta(hours=8)
        count = db.query(MarketData).filter(
            MarketData.symbol == symbol,
            MarketData.timestamp >= cutoff
        ).count()
        
        db.close()
        return count
    except Exception as e:
        logger.error(f"Error checking DB candle count: {e}")
        return 0


if __name__ == "__main__":
    # Test the historical candle fetcher
    logging.basicConfig(level=logging.INFO)
    
    print("\n=== Pre-loading Historical 5-Minute Candles ===\n")
    
    # Check current state
    for symbol in ['BTC/USDT', 'ETH/USDT', 'SOL/USDT']:
        count = get_db_candle_count(symbol)
        print(f"{symbol}: {count} candles in DB (last 8h)")
    
    print("\nFetching from Binance.US...")
    preload_historical_candles_to_db(symbols=['BTCUSDT', 'ETHUSDT', 'SOLUSDT'], hours=8)
    
    print("\n=== After Pre-load ===\n")
    for symbol in ['BTC/USDT', 'ETH/USDT', 'SOL/USDT']:
        count = get_db_candle_count(symbol)
        print(f"{symbol}: {count} candles in DB (last 8h)")
    
    print("\n✅ Done! Dashboard charts should now display immediately.\n")
