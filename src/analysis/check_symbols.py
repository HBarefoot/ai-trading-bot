#!/usr/bin/env python3
"""
Check what symbols are available in the database
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from data.database import get_db
from data.models import MarketData

def check_available_symbols():
    """Check what trading symbols are available in the database"""
    print("🔍 CHECKING AVAILABLE SYMBOLS IN DATABASE")
    print("=" * 50)
    
    db = next(get_db())
    
    try:
        # Get all unique symbols
        symbols = db.query(MarketData.symbol).distinct().all()
        symbol_list = [s[0] for s in symbols]
        
        print(f"📊 Available symbols: {len(symbol_list)}")
        for symbol in symbol_list:
            # Count records for each symbol
            count = db.query(MarketData).filter(MarketData.symbol == symbol).count()
            print(f"  • {symbol}: {count} records")
        
        # Check date ranges
        print(f"\n📅 Data ranges:")
        for symbol in symbol_list:
            first_record = db.query(MarketData).filter(
                MarketData.symbol == symbol
            ).order_by(MarketData.timestamp.asc()).first()
            
            last_record = db.query(MarketData).filter(
                MarketData.symbol == symbol
            ).order_by(MarketData.timestamp.desc()).first()
            
            if first_record and last_record:
                print(f"  • {symbol}: {first_record.timestamp} to {last_record.timestamp}")
        
        print(f"\n🎯 DASHBOARD SYMBOL SUPPORT:")
        if len(symbol_list) == 1 and symbol_list[0] == "BTCUSDT":
            print("  ✅ Currently only BTCUSDT data is available")
            print("  ⚠️ When you change symbols in dashboard, signals will show:")
            print("     'No market data available for [SYMBOL]'")
            print("     'Currently only BTCUSDT data is available'")
        else:
            print(f"  ✅ Multiple symbols available: {', '.join(symbol_list)}")
            print("  🎉 Dashboard should work with all listed symbols")
        
        print(f"\n💡 TO ADD MORE SYMBOLS:")
        print("  1. Modify data collection to fetch other cryptocurrencies")
        print("  2. Run: python src/data/collect_data.py --symbol ETHUSDT")
        print("  3. Dashboard will automatically support new symbols")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    check_available_symbols()