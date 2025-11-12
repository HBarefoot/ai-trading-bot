#!/usr/bin/env python3
"""
Debug Week 2 v2 - Figure out why no trades
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from strategies.optimized_strategy_week2_v2 import OptimizedStrategyWeek2V2
from data.database import get_db
import pandas as pd
from datetime import datetime, timedelta

def debug_week2_v2():
    """Debug Week 2 v2 to see why no trades"""
    db = next(get_db())
    
    print("\n" + "="*80)
    print("DEBUGGING WEEK 2 v2")
    print("="*80)
    
    strategy = OptimizedStrategyWeek2V2()
    
    # Get data
    end_date = datetime.now()
    start_date = end_date - timedelta(days=90)
    
    from data.models import MarketData
    data = db.query(MarketData).filter(
        MarketData.timestamp >= start_date,
        MarketData.timestamp <= end_date,
        MarketData.symbol == 'BTCUSDT'
    ).order_by(MarketData.timestamp).all()
    
    print(f"\n📊 Data loaded: {len(data)} records")
    if len(data) > 0:
        print(f"   First: {data[0].timestamp}")
        print(f"   Last: {data[-1].timestamp}")
        print(f"   Price range: ${float(data[0].close_price):.2f} → ${float(data[-1].close_price):.2f}")
    
    # Convert to DataFrame
    df = pd.DataFrame([{
        'timestamp': d.timestamp,
        'open_price': float(d.open_price),
        'high_price': float(d.high_price),
        'low_price': float(d.low_price),
        'close_price': float(d.close_price),
        'volume': float(d.volume)
    } for d in data])
    
    print(f"\n📊 DataFrame shape: {df.shape}")
    print(f"   Columns: {list(df.columns)}")
    
    # Generate signals with debug
    print("\n📊 Generating signals...")
    signals = strategy.generate_signals(df)
    
    print(f"\n📊 Signals generated: {len(signals)}")
    if len(signals) > 0:
        print("\nFirst few signals:")
        for signal in signals[:10]:
            print(f"  {signal['timestamp']} - {signal['signal']} @ ${signal['price']:.2f}")
    else:
        print("  ⚠️ NO SIGNALS GENERATED!")
        print("\nLet's check if indicators are calculating...")
        
        # Manually calculate indicators to debug
        data_copy = df.copy()
        data_copy['rsi'] = strategy.indicators.rsi(data_copy['close_price'])
        print(f"\n  RSI min: {data_copy['rsi'].min():.2f}, max: {data_copy['rsi'].max():.2f}")
        print(f"  RSI < 30 count: {(data_copy['rsi'] < 30).sum()}")
        
        macd_line, signal_line, histogram = strategy.indicators.macd(data_copy['close_price'])
        print(f"\n  MACD histogram min: {histogram.min():.4f}, max: {histogram.max():.4f}")
        print(f"  MACD > signal count: {(macd_line > signal_line).sum()}")
        
        data_copy['sma_20'] = strategy.indicators.simple_moving_average(data_copy['close_price'], window=20)
        data_copy['sma_50'] = strategy.indicators.simple_moving_average(data_copy['close_price'], window=50)
        print(f"\n  SMA20 > SMA50 count: {(data_copy['sma_20'] > data_copy['sma_50']).sum()}")
        
        data_copy['adx'] = strategy.calculate_adx(data_copy)
        print(f"\n  ADX min: {data_copy['adx'].min():.2f}, max: {data_copy['adx'].max():.2f}")
        print(f"  ADX > 20 count: {(data_copy['adx'] > 20).sum()}")
        
        # Check volume
        data_copy['volume_sma'] = data_copy['volume'].rolling(window=20).mean()
        volume_surge = data_copy['volume'] > (data_copy['volume_sma'] * 1.1)
        print(f"\n  Volume surge count: {volume_surge.sum()}")
        
        # Check all conditions together
        print("\n  Checking combined conditions...")
        rsi_ok = data_copy['rsi'] < 30
        sma_ok = data_copy['sma_20'] > data_copy['sma_50']
        adx_ok = data_copy['adx'] > 20
        volume_ok = data_copy['volume'] > (data_copy['volume_sma'] * 1.1)
        price_ok = data_copy['close_price'] > data_copy['sma_20']
        
        print(f"    RSI < 30: {rsi_ok.sum()}")
        print(f"    SMA20 > SMA50: {sma_ok.sum()}")
        print(f"    ADX > 20: {adx_ok.sum()}")
        print(f"    Volume surge: {volume_ok.sum()}")
        print(f"    Price > SMA20: {price_ok.sum()}")
        
        combined = rsi_ok & sma_ok & adx_ok & volume_ok & price_ok
        print(f"\n  All conditions met: {combined.sum()} times")
        
        if combined.sum() > 0:
            print("\n  Dates when all conditions met:")
            matching_dates = data_copy[combined]['timestamp']
            for date in matching_dates.head(10):
                print(f"    {date}")

if __name__ == "__main__":
    debug_week2_v2()
