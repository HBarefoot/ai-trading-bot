#!/usr/bin/env python3
"""
Test technical indicators with sample market data
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import pandas as pd
from data.database import get_db
from data.models import MarketData
from strategies.technical_indicators import TechnicalIndicators, SignalGenerator

def test_technical_indicators():
    """Test technical indicators with BTC data"""
    print("🧪 Testing Technical Indicators with Sample Data")
    
    # Get database session
    db = next(get_db())
    
    try:
        # Fetch BTC market data
        market_data = db.query(MarketData).filter(
            MarketData.symbol == "BTCUSDT"
        ).order_by(MarketData.timestamp.asc()).limit(200).all()
        
        if not market_data:
            print("❌ No market data found")
            return
        
        # Convert to DataFrame
        data = []
        for record in market_data:
            data.append({
                'timestamp': record.timestamp,
                'open_price': float(record.open_price),
                'high_price': float(record.high_price),
                'low_price': float(record.low_price),
                'close_price': float(record.close_price),
                'volume': float(record.volume)
            })
        
        df = pd.DataFrame(data)
        df.set_index('timestamp', inplace=True)
        
        print(f"📊 Processing {len(df)} BTC/USDT data points")
        
        # Calculate all technical indicators
        df_with_indicators = TechnicalIndicators.calculate_all_indicators(df)
        
        # Display sample results
        print("\n🔍 Sample Technical Indicators (Latest 5 records):")
        print("=" * 80)
        
        # Select key indicators to display
        key_indicators = [
            'close_price', 'sma_20', 'ema_20', 'rsi', 'macd', 'macd_signal',
            'bb_upper', 'bb_lower', 'stoch_k', 'atr'
        ]
        
        sample_data = df_with_indicators[key_indicators].tail(5)
        for col in sample_data.columns:
            if col != 'close_price':
                sample_data[col] = sample_data[col].round(4)
            else:
                sample_data[col] = sample_data[col].round(2)
        
        print(sample_data.to_string())
        
        # Generate some trading signals
        print("\n📈 Trading Signals Analysis:")
        print("=" * 50)
        
        latest = df_with_indicators.iloc[-1]
        
        # RSI Analysis
        rsi_level = latest['rsi']
        if rsi_level < 30:
            rsi_signal = "🟢 OVERSOLD - Consider buying"
        elif rsi_level > 70:
            rsi_signal = "🔴 OVERBOUGHT - Consider selling"
        else:
            rsi_signal = "🟡 NEUTRAL"
        
        print(f"RSI ({rsi_level:.2f}): {rsi_signal}")
        
        # MACD Analysis
        macd_value = latest['macd']
        macd_signal = latest['macd_signal']
        if macd_value > macd_signal:
            macd_trend = "🟢 BULLISH - MACD above signal"
        else:
            macd_trend = "🔴 BEARISH - MACD below signal"
        
        print(f"MACD: {macd_trend}")
        
        # Bollinger Bands Analysis
        close_price = latest['close_price']
        bb_upper = latest['bb_upper']
        bb_lower = latest['bb_lower']
        bb_position = latest['bb_position']
        
        if bb_position > 0.8:
            bb_signal = "🔴 Near upper band - Potential resistance"
        elif bb_position < 0.2:
            bb_signal = "🟢 Near lower band - Potential support"
        else:
            bb_signal = "🟡 Middle of bands"
        
        print(f"Bollinger Bands ({bb_position:.2f}): {bb_signal}")
        
        # Moving Average Analysis
        sma_20 = latest['sma_20']
        sma_50 = latest['sma_50']
        
        if close_price > sma_20 > sma_50:
            ma_trend = "🟢 UPTREND - Price above both MAs"
        elif close_price < sma_20 < sma_50:
            ma_trend = "🔴 DOWNTREND - Price below both MAs"
        else:
            ma_trend = "🟡 MIXED SIGNALS"
        
        print(f"Moving Averages: {ma_trend}")
        
        # Generate combined signals
        print("\n🤖 Automated Signal Generation:")
        print("=" * 40)
        
        rsi_signals = SignalGenerator.rsi_signals(df_with_indicators['rsi'])
        ma_signals = SignalGenerator.ma_crossover_signals(
            df_with_indicators['sma_20'], df_with_indicators['sma_50']
        )
        bb_signals = SignalGenerator.bollinger_band_signals(
            df_with_indicators['close_price'],
            df_with_indicators['bb_upper'],
            df_with_indicators['bb_lower']
        )
        macd_signals = SignalGenerator.macd_signals(
            df_with_indicators['macd'], df_with_indicators['macd_signal']
        )
        
        # Recent signals
        recent_signals = pd.DataFrame({
            'RSI': rsi_signals.tail(5),
            'MA_Cross': ma_signals.tail(5),
            'Bollinger': bb_signals.tail(5),
            'MACD': macd_signals.tail(5)
        })
        
        print("Recent signals (1=Buy, -1=Sell, 0=Hold):")
        print(recent_signals.to_string())
        
        # Signal summary
        latest_signals = {
            'RSI': rsi_signals.iloc[-1],
            'MA_Cross': ma_signals.iloc[-1], 
            'Bollinger': bb_signals.iloc[-1],
            'MACD': macd_signals.iloc[-1]
        }
        
        signal_strength = sum(latest_signals.values())
        
        print(f"\n🎯 Overall Signal Strength: {signal_strength}")
        if signal_strength >= 2:
            print("🟢 STRONG BUY signal")
        elif signal_strength >= 1:
            print("🟢 Moderate BUY signal")
        elif signal_strength <= -2:
            print("🔴 STRONG SELL signal")
        elif signal_strength <= -1:
            print("🔴 Moderate SELL signal")
        else:
            print("🟡 NEUTRAL - Hold position")
        
        print("\n✅ Technical analysis completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during technical analysis: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_technical_indicators()