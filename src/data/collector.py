"""
Market data collector using CCXT library
Fetches historical and real-time data from cryptocurrency exchanges
"""
import ccxt
import pandas as pd
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import time
import sys
import os

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from data.database import get_db_sync, test_connection, create_tables
from data.models import MarketData

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/data_collector.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class DataCollector:
    """Cryptocurrency data collector"""
    
    def __init__(self, exchange_name: str = 'binance'):
        """Initialize data collector
        
        Args:
            exchange_name: Name of the exchange to collect data from
        """
        self.exchange_name = exchange_name
        self.exchange = self._initialize_exchange()
        self.db = get_db_sync()
        
    def _initialize_exchange(self):
        """Initialize exchange connection"""
        try:
            exchange_class = getattr(ccxt, self.exchange_name)
            exchange = exchange_class({
                'apiKey': os.getenv(f'{self.exchange_name.upper()}_API_KEY'),
                'secret': os.getenv(f'{self.exchange_name.upper()}_SECRET_KEY'),
                'sandbox': False,  # Use production API for public data
                'enableRateLimit': True,
                'options': {
                    'defaultType': 'spot'  # Use spot trading
                }
            })
            logger.info(f"Initialized {self.exchange_name} exchange")
            return exchange
        except Exception as e:
            logger.error(f"Failed to initialize exchange {self.exchange_name}: {e}")
            # Fallback to public-only mode
            exchange_class = getattr(ccxt, self.exchange_name)
            return exchange_class({'enableRateLimit': True})
    
    def get_historical_data(self, symbol: str, timeframe: str = '1h', 
                          days: int = 365) -> pd.DataFrame:
        """Fetch historical OHLCV data
        
        Args:
            symbol: Trading pair symbol (e.g., 'BTC/USDT')
            timeframe: Timeframe for candles ('1m', '5m', '1h', '1d')
            days: Number of days of historical data
            
        Returns:
            DataFrame with OHLCV data
        """
        try:
            # Calculate since timestamp
            since = self.exchange.milliseconds() - (days * 24 * 60 * 60 * 1000)
            
            logger.info(f"Fetching {days} days of {timeframe} data for {symbol}")
            
            # Fetch data in chunks to avoid rate limits
            all_ohlcv = []
            current_since = since
            
            while current_since < self.exchange.milliseconds():
                try:
                    ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, current_since, limit=1000)
                    if not ohlcv:
                        break
                    
                    all_ohlcv.extend(ohlcv)
                    current_since = ohlcv[-1][0] + 1  # Move to next timestamp
                    
                    # Rate limiting
                    time.sleep(self.exchange.rateLimit / 1000)
                    
                except Exception as e:
                    logger.warning(f"Error fetching batch: {e}")
                    break
            
            # Convert to DataFrame
            df = pd.DataFrame(all_ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df['symbol'] = symbol.replace('/', '')  # Remove slash for database
            
            logger.info(f"Fetched {len(df)} candles for {symbol}")
            return df
            
        except Exception as e:
            logger.error(f"Error fetching historical data for {symbol}: {e}")
            return pd.DataFrame()
    
    def save_to_database(self, df: pd.DataFrame) -> bool:
        """Save DataFrame to database
        
        Args:
            df: DataFrame with market data
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if df.empty:
                logger.warning("No data to save")
                return False
            
            # Prepare data for database
            records = []
            for _, row in df.iterrows():
                record = MarketData(
                    symbol=row['symbol'],
                    timestamp=row['timestamp'],
                    open_price=float(row['open']),
                    high_price=float(row['high']),
                    low_price=float(row['low']),
                    close_price=float(row['close']),
                    volume=float(row['volume'])
                )
                records.append(record)
            
            # Bulk insert with conflict handling
            try:
                self.db.bulk_save_objects(records)
                self.db.commit()
                logger.info(f"Saved {len(records)} records to database")
                return True
            except Exception as e:
                self.db.rollback()
                # Try individual inserts for duplicate handling
                success_count = 0
                for record in records:
                    try:
                        # Check if record exists
                        existing = self.db.query(MarketData).filter(
                            MarketData.symbol == record.symbol,
                            MarketData.timestamp == record.timestamp
                        ).first()
                        
                        if not existing:
                            self.db.add(record)
                            self.db.commit()
                            success_count += 1
                    except Exception:
                        self.db.rollback()
                        continue
                
                logger.info(f"Saved {success_count} new records (skipped duplicates)")
                return success_count > 0
                
        except Exception as e:
            logger.error(f"Error saving to database: {e}")
            self.db.rollback()
            return False
    
    def collect_symbol_data(self, symbol: str, days: int = 365):
        """Collect and save data for a single symbol"""
        logger.info(f"Starting data collection for {symbol}")
        
        # Fetch historical data
        df = self.get_historical_data(symbol, '1h', days)
        
        if not df.empty:
            # Save to database
            success = self.save_to_database(df)
            if success:
                logger.info(f"Successfully collected data for {symbol}")
            else:
                logger.error(f"Failed to save data for {symbol}")
        else:
            logger.warning(f"No data collected for {symbol}")
    
    def collect_all_data(self, symbols: List[str], days: int = 365):
        """Collect data for multiple symbols"""
        logger.info(f"Starting data collection for {len(symbols)} symbols")
        
        for symbol in symbols:
            try:
                self.collect_symbol_data(symbol, days)
                # Small delay between symbols
                time.sleep(2)
            except Exception as e:
                logger.error(f"Error collecting data for {symbol}: {e}")
                continue
        
        logger.info("Data collection completed")


def main():
    """Main function to run data collection"""
    print("🚀 Starting AI Trading Bot Data Collector")
    
    # Test database connection
    if not test_connection():
        print("❌ Database connection failed")
        return
    
    # Create tables if they don't exist
    create_tables()
    
    # Initialize collector
    collector = DataCollector('binance')
    
    # Define symbols to collect
    symbols = ['BTC/USDT', 'ETH/USDT', 'ADA/USDT', 'DOT/USDT', 'SOL/USDT']
    
    print(f"📊 Collecting data for symbols: {symbols}")
    print("⏳ This may take several minutes...")
    
    # Collect 5 years of data
    collector.collect_all_data(symbols, days=1825)  # 5 years
    
    print("✅ Data collection completed!")
    print("📈 You can now run the trading bot")


if __name__ == "__main__":
    main()