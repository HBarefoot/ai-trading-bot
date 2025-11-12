#!/usr/bin/env python3
"""
Collect historical OHLCV data from Binance.US for backtesting
Target: 90+ days of hourly data
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import ccxt
from datetime import datetime, timedelta
import pandas as pd
from data.database import get_db
from data.models import MarketData
from sqlalchemy.exc import IntegrityError
import time

def collect_binance_data(symbol='BTC/USDT', days=90, timeframe='1h'):
    """
    Collect historical data from Binance.US
    
    Args:
        symbol: Trading pair (e.g., 'BTC/USDT')
        days: Number of days to collect
        timeframe: Candlestick timeframe ('1h', '4h', '1d')
    """
    print(f"\n{'='*80}")
    print(f"COLLECTING HISTORICAL DATA FROM BINANCE.US")
    print(f"{'='*80}")
    print(f"Symbol: {symbol}")
    print(f"Timeframe: {timeframe}")
    print(f"Days: {days}")
    print(f"{'='*80}\n")
    
    # Initialize Binance.US exchange
    exchange = ccxt.binance({
        'enableRateLimit': True,
        'options': {
            'defaultType': 'spot',
        },
        'urls': {
            'api': {
                'public': 'https://api.binance.us/api/v3',
                'private': 'https://api.binance.us/api/v3',
            }
        }
    })
    
    # Calculate time range
    end_time = datetime.now()
    start_time = end_time - timedelta(days=days)
    
    print(f"Fetching data from {start_time} to {end_time}...")
    
    # Convert to timestamps
    since = int(start_time.timestamp() * 1000)
    
    all_data = []
    batch_count = 0
    
    try:
        while True:
            batch_count += 1
            print(f"\nFetching batch {batch_count}... (from {datetime.fromtimestamp(since/1000)})")
            
            # Fetch OHLCV data
            ohlcv = exchange.fetch_ohlcv(symbol, timeframe, since=since, limit=1000)
            
            if not ohlcv:
                print("No more data available.")
                break
            
            print(f"  Received {len(ohlcv)} candles")
            all_data.extend(ohlcv)
            
            # Update since to last timestamp + 1
            last_timestamp = ohlcv[-1][0]
            since = last_timestamp + 1
            
            # Check if we've reached the end
            if last_timestamp >= int(end_time.timestamp() * 1000):
                print("Reached current time.")
                break
            
            # Rate limiting
            time.sleep(exchange.rateLimit / 1000)
        
        print(f"\n{'='*80}")
        print(f"FETCHED {len(all_data)} TOTAL CANDLES")
        print(f"{'='*80}\n")
        
        # Convert to DataFrame
        df = pd.DataFrame(all_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        
        print("Data range:")
        print(f"  Start: {df['timestamp'].min()}")
        print(f"  End:   {df['timestamp'].max()}")
        print(f"  Total: {len(df)} records\n")
        
        # Save to database
        db = next(get_db())
        saved_count = 0
        duplicate_count = 0
        
        print("Saving to database...")
        for _, row in df.iterrows():
            market_data = MarketData(
                symbol=symbol,
                timestamp=row['timestamp'],
                open_price=float(row['open']),
                high_price=float(row['high']),
                low_price=float(row['low']),
                close_price=float(row['close']),
                volume=float(row['volume'])
            )
            
            try:
                db.add(market_data)
                db.commit()
                saved_count += 1
                
                if saved_count % 100 == 0:
                    print(f"  Saved {saved_count} records...")
                    
            except IntegrityError:
                db.rollback()
                duplicate_count += 1
        
        print(f"\n{'='*80}")
        print(f"DATABASE SAVE COMPLETE")
        print(f"{'='*80}")
        print(f"Saved: {saved_count} new records")
        print(f"Skipped: {duplicate_count} duplicates")
        print(f"Total in DB: {saved_count + duplicate_count} records")
        print(f"{'='*80}\n")
        
        return df
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return None


def get_database_stats():
    """Get current database statistics"""
    db = next(get_db())
    
    total_count = db.query(MarketData).count()
    btc_count = db.query(MarketData).filter(MarketData.symbol == 'BTC/USDT').count()
    
    if btc_count > 0:
        btc_data = db.query(MarketData).filter(MarketData.symbol == 'BTC/USDT').order_by(MarketData.timestamp).all()
        start_date = btc_data[0].timestamp
        end_date = btc_data[-1].timestamp
        days = (end_date - start_date).days
    else:
        start_date = None
        end_date = None
        days = 0
    
    print(f"\n{'='*80}")
    print(f"CURRENT DATABASE STATS")
    print(f"{'='*80}")
    print(f"Total records: {total_count}")
    print(f"BTC/USDT records: {btc_count}")
    if btc_count > 0:
        print(f"Date range: {start_date} to {end_date}")
        print(f"Days covered: {days}")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    # Show current stats
    print("Current database state:")
    get_database_stats()
    
    # Collect 90 days of hourly data
    print("\nStarting data collection...")
    df = collect_binance_data(symbol='BTC/USDT', days=90, timeframe='1h')
    
    # Show updated stats
    if df is not None:
        print("\nUpdated database state:")
        get_database_stats()
        
        print("\n✅ Data collection complete!")
        print(f"You now have {len(df)} records for robust backtesting.")
