"""
Sample data generator for testing when exchange APIs are unavailable
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from data.database import get_db_sync, test_connection, create_tables
from data.models import MarketData
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def generate_sample_market_data(symbol: str, days: int = 30) -> pd.DataFrame:
    """Generate realistic sample market data"""
    
    # Starting price based on symbol
    price_ranges = {
        'BTCUSDT': 45000,
        'ETHUSDT': 2800,
        'ADAUSDT': 0.85,
        'DOTUSDT': 6.5,
        'SOLUSDT': 180
    }
    
    base_price = price_ranges.get(symbol.replace('/', ''), 50000)
    
    # Generate timestamps (hourly data)
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(days=days)
    timestamps = pd.date_range(start_time, end_time, freq='1H')
    
    # Generate price data with realistic patterns
    num_points = len(timestamps)
    
    # Generate random walk with trend
    returns = np.random.normal(0, 0.02, num_points)  # 2% volatility
    trend = np.linspace(0, 0.1, num_points)  # Slight upward trend
    
    # Apply returns to generate prices
    prices = [base_price]
    for i in range(1, num_points):
        new_price = prices[-1] * (1 + returns[i] + trend[i]/num_points)
        prices.append(max(new_price, base_price * 0.5))  # Prevent extreme drops
    
    # Generate OHLCV data
    data = []
    for i, timestamp in enumerate(timestamps):
        if i == 0:
            continue
            
        # Close price from our generated series
        close = prices[i]
        open_price = prices[i-1]
        
        # Generate high and low around open/close
        high_low_range = abs(close - open_price) * 2 + close * 0.01
        high = max(open_price, close) + np.random.uniform(0, high_low_range)
        low = min(open_price, close) - np.random.uniform(0, high_low_range)
        
        # Ensure high >= max(open, close) and low <= min(open, close)
        high = max(high, open_price, close)
        low = min(low, open_price, close)
        
        # Generate volume (higher during price movements)
        volatility = abs(close - open_price) / open_price
        base_volume = np.random.uniform(100, 1000)
        volume = base_volume * (1 + volatility * 10)
        
        data.append({
            'timestamp': timestamp,
            'symbol': symbol.replace('/', ''),
            'open_price': round(open_price, 8),
            'high_price': round(high, 8),
            'low_price': round(low, 8),
            'close_price': round(close, 8),
            'volume': round(volume, 8)
        })
    
    df = pd.DataFrame(data)
    logger.info(f"Generated {len(df)} sample data points for {symbol}")
    return df


def save_sample_data(df: pd.DataFrame) -> bool:
    """Save sample data to database"""
    try:
        db = get_db_sync()
        
        # Prepare data for database
        records = []
        for _, row in df.iterrows():
            record = MarketData(
                symbol=row['symbol'],
                timestamp=row['timestamp'],
                open_price=float(row['open_price']),
                high_price=float(row['high_price']),
                low_price=float(row['low_price']),
                close_price=float(row['close_price']),
                volume=float(row['volume'])
            )
            records.append(record)
        
        # Save records
        try:
            db.bulk_save_objects(records)
            db.commit()
            logger.info(f"Saved {len(records)} sample records to database")
            return True
        except Exception as e:
            db.rollback()
            logger.error(f"Error saving sample data: {e}")
            return False
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error saving sample data: {e}")
        return False


def main():
    """Generate and save sample data for all symbols"""
    print("🎲 Generating Sample Market Data for Testing")
    
    # Test database connection
    if not test_connection():
        print("❌ Database connection failed")
        return
    
    # Create tables if they don't exist
    create_tables()
    
    # Generate sample data for multiple symbols
    symbols = ['BTC/USDT', 'ETH/USDT', 'ADA/USDT', 'DOT/USDT', 'SOL/USDT']
    
    for symbol in symbols:
        print(f"📊 Generating sample data for {symbol}...")
        
        # Generate 30 days of hourly data
        df = generate_sample_market_data(symbol, days=30)
        
        # Save to database
        success = save_sample_data(df)
        if success:
            print(f"✅ Sample data saved for {symbol}")
        else:
            print(f"❌ Failed to save sample data for {symbol}")
    
    print("🎉 Sample data generation completed!")
    print("📈 You can now test the trading bot with this data")


if __name__ == "__main__":
    main()