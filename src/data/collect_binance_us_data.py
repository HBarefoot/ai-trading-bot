#!/usr/bin/env python3
"""
Collect historical OHLCV data from Binance.US using direct API calls
Target: 90+ days of hourly data
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import requests
from datetime import datetime, timedelta
import pandas as pd
from data.database import get_db
from data.models import MarketData
from sqlalchemy.exc import IntegrityError
import time

def collect_binance_us_data(symbol='BTCUSDT', days=90, interval='1h'):
    """
    Collect historical data from Binance.US using direct API
    
    Args:
        symbol: Trading pair without slash (e.g., 'BTCUSDT')
        days: Number of days to collect
        interval: Candlestick interval ('1h', '4h', '1d')
    """
    print(f"\n{'='*80}")
    print(f"COLLECTING HISTORICAL DATA FROM BINANCE.US (Direct API)")
    print(f"{'='*80}")
    print(f"Symbol: {symbol}")
    print(f"Interval: {interval}")
    print(f"Days: {days}")
    print(f"{'='*80}\n")
    
    base_url = "https://api.binance.us/api/v3/klines"
    
    # Calculate time range
    end_time = datetime.now()
    start_time = end_time - timedelta(days=days)
    
    # Convert to milliseconds
    start_ts = int(start_time.timestamp() * 1000)
    end_ts = int(end_time.timestamp() * 1000)
    
    print(f"Fetching data from {start_time} to {end_time}...")
    
    all_data = []
    current_start = start_ts
    batch_count = 0
    
    try:
        while current_start < end_ts:
            batch_count += 1
            print(f"\nBatch {batch_count}... (from {datetime.fromtimestamp(current_start/1000)})")
            
            # Binance API parameters
            params = {
                'symbol': symbol,
                'interval': interval,
                'startTime': current_start,
                'endTime': end_ts,
                'limit': 1000  # Max limit per request
            }
            
            # Make request
            response = requests.get(base_url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            if not data:
                print("  No more data available.")
                break
            
            print(f"  Received {len(data)} candles")
            all_data.extend(data)
            
            # Update start time for next batch (last timestamp + 1ms)
            current_start = data[-1][0] + 1
            
            # If we got less than 1000, we've reached the end
            if len(data) < 1000:
                print("  Reached end of available data.")
                break
            
            # Rate limiting (weight = 1, limit = 1200/min)
            time.sleep(0.1)  # 10 requests per second = 600/min
        
        print(f"\n{'='*80}")
        print(f"FETCHED {len(all_data)} TOTAL CANDLES")
        print(f"{'='*80}\n")
        
        # Convert to DataFrame
        # Binance kline format: [open_time, open, high, low, close, volume, close_time, ...]
        df = pd.DataFrame(all_data, columns=[
            'open_time', 'open', 'high', 'low', 'close', 'volume', 
            'close_time', 'quote_volume', 'trades', 'taker_buy_base', 
            'taker_buy_quote', 'ignore'
        ])
        
        # Convert types
        df['timestamp'] = pd.to_datetime(df['open_time'], unit='ms')
        df['open'] = df['open'].astype(float)
        df['high'] = df['high'].astype(float)
        df['low'] = df['low'].astype(float)
        df['close'] = df['close'].astype(float)
        df['volume'] = df['volume'].astype(float)
        
        print("Data range:")
        print(f"  Start: {df['timestamp'].min()}")
        print(f"  End:   {df['timestamp'].max()}")
        print(f"  Total: {len(df)} records")
        print(f"  First close price: ${df['close'].iloc[0]:,.2f}")
        print(f"  Last close price: ${df['close'].iloc[-1]:,.2f}\n")
        
        # Save to database
        db = next(get_db())
        saved_count = 0
        duplicate_count = 0
        
        # Use standard symbol format for database
        db_symbol = 'BTC/USDT'
        
        print(f"Saving to database as {db_symbol}...")
        for _, row in df.iterrows():
            market_data = MarketData(
                symbol=db_symbol,
                timestamp=row['timestamp'],
                open_price=row['open'],
                high_price=row['high'],
                low_price=row['low'],
                close_price=row['close'],
                volume=row['volume']
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
        print(f"Total saved: {saved_count + duplicate_count} records")
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
        btc_data = db.query(MarketData).filter(
            MarketData.symbol == 'BTC/USDT'
        ).order_by(MarketData.timestamp).all()
        start_date = btc_data[0].timestamp
        end_date = btc_data[-1].timestamp
        days = (end_date - start_date).days
        
        # Get price range
        first_price = btc_data[0].close_price
        last_price = btc_data[-1].close_price
    else:
        start_date = None
        end_date = None
        days = 0
        first_price = 0
        last_price = 0
    
    print(f"\n{'='*80}")
    print(f"CURRENT DATABASE STATS")
    print(f"{'='*80}")
    print(f"Total records (all symbols): {total_count}")
    print(f"BTC/USDT records: {btc_count}")
    if btc_count > 0:
        print(f"Date range: {start_date} to {end_date}")
        print(f"Days covered: {days}")
        print(f"Price range: ${first_price:,.2f} to ${last_price:,.2f}")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    # Show current stats
    print("Current database state:")
    get_database_stats()
    
    # Collect 90 days of hourly data
    print("\nStarting data collection...")
    df = collect_binance_us_data(symbol='BTCUSDT', days=90, interval='1h')
    
    # Show updated stats
    if df is not None:
        print("\nUpdated database state:")
        get_database_stats()
        
        print("\n✅ Data collection complete!")
        print(f"You now have enough historical data for robust backtesting.")
