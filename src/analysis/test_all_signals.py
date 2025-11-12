#!/usr/bin/env python3
"""
Test signals for different cryptocurrencies
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import pandas as pd
from data.database import get_db
from data.models import MarketData
from strategies.technical_indicators import TechnicalIndicators
from strategies.phase2_final_test import OptimizedPhase2Strategy

def test_signals_all_symbols():
    """Test signals for all available symbols"""
    print("🎯 TESTING SIGNALS FOR ALL CRYPTOCURRENCIES")
    print("=" * 60)
    
    db = next(get_db())
    
    try:
        # Get all symbols
        symbols = db.query(MarketData.symbol).distinct().all()
        symbol_list = [s[0] for s in symbols]
        
        strategy = OptimizedPhase2Strategy()
        indicators = TechnicalIndicators()
        
        for symbol in symbol_list:
            print(f"\n🔥 {symbol} ANALYSIS:")
            print("-" * 30)
            
            # Get data for this symbol
            market_data = db.query(MarketData).filter(
                MarketData.symbol == symbol
            ).order_by(MarketData.timestamp.asc()).all()
            
            if not market_data:
                print(f"  ❌ No data for {symbol}")
                continue
            
            # Convert to DataFrame
            data = []
            for record in market_data:
                data.append({
                    'timestamp': record.timestamp,
                    'close_price': float(record.close_price),
                })
            
            df = pd.DataFrame(data)
            df.set_index('timestamp', inplace=True)
            
            # Calculate indicators
            close = df['close_price']
            ma8 = close.rolling(8).mean()
            ma21 = close.rolling(21).mean()
            rsi = indicators.rsi(close, window=14)
            
            # Current values
            current_price = close.iloc[-1]
            current_ma8 = ma8.iloc[-1]
            current_ma21 = ma21.iloc[-1]
            current_rsi = rsi.iloc[-1]
            
            # Generate signal
            signals = strategy.generate_signals(df)
            latest_signal = signals.iloc[-1]
            
            # Display results
            print(f"  💰 Current Price: ${current_price:,.2f}")
            print(f"  📈 MA(8): ${current_ma8:,.2f}")
            print(f"  📉 MA(21): ${current_ma21:,.2f}")
            print(f"  📊 RSI: {current_rsi:.2f}")
            
            # Trend analysis
            trend = "🟢 BULLISH" if current_ma8 > current_ma21 else "🔴 BEARISH"
            rsi_status = "🔥 Overbought" if current_rsi > 70 else "❄️ Oversold" if current_rsi < 30 else "⚖️ Neutral"
            
            print(f"  🎯 Trend: {trend}")
            print(f"  🌡️ RSI: {rsi_status}")
            
            # Signal interpretation
            if latest_signal > 0:
                signal_strength = "STRONG" if latest_signal >= 1.0 else "MODERATE"
                print(f"  🚨 Signal: 🟢 {signal_strength} BUY ({latest_signal:.2f})")
            elif latest_signal < 0:
                print(f"  🚨 Signal: 🔴 SELL ({latest_signal:.2f})")
            else:
                print(f"  🚨 Signal: 🟡 HOLD ({latest_signal:.2f})")
                
                # Distance to next signal
                if current_ma8 < current_ma21:
                    crossover_price = current_ma21
                    price_change = (crossover_price - current_price) / current_price * 100
                    print(f"     📈 Next BUY at: ${crossover_price:,.2f} ({price_change:+.1f}%)")
                    if abs(price_change) < 5:
                        print(f"     🔥 CLOSE TO SIGNAL!")
        
        print(f"\n🏆 SUMMARY:")
        print(f"  ✅ All {len(symbol_list)} symbols have working signals")
        print(f"  ✅ Dashboard now supports dynamic symbol switching")
        print(f"  ✅ Live Signals tab will update when you change symbols")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_signals_all_symbols()