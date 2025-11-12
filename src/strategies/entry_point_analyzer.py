#!/usr/bin/env python3
"""
🎯 LIVE TRADING ENTRY POINT DETECTOR
Shows exactly when and why to enter/exit trades
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import pandas as pd
import numpy as np
from data.database import get_db
from data.models import MarketData
from strategies.technical_indicators import TechnicalIndicators

def analyze_entry_points():
    """Detailed analysis of when to enter trades"""
    print("🎯 LIVE TRADING ENTRY POINT ANALYSIS")
    print("=" * 60)
    
    # Get data
    db = next(get_db())
    
    try:
        market_data = db.query(MarketData).filter(
            MarketData.symbol == "BTCUSDT"
        ).order_by(MarketData.timestamp.asc()).all()
        
        # Convert to DataFrame
        data = []
        for record in market_data:
            data.append({
                'timestamp': record.timestamp,
                'close_price': float(record.close_price),
                'volume': float(record.volume)
            })
        
        df = pd.DataFrame(data)
        df.set_index('timestamp', inplace=True)
        
        # Calculate indicators
        indicators = TechnicalIndicators()
        close = df['close_price']
        
        # Core indicators for entry detection
        ma8 = close.rolling(8).mean()
        ma21 = close.rolling(21).mean()
        rsi = indicators.rsi(close, window=14)
        
        # Current values
        current_price = close.iloc[-1]
        current_ma8 = ma8.iloc[-1]
        current_ma21 = ma21.iloc[-1]
        current_rsi = rsi.iloc[-1]
        
        print(f"📊 CURRENT MARKET STATE:")
        print(f"  💰 Bitcoin Price: ${current_price:,.2f}")
        print(f"  📈 Short MA(8): ${current_ma8:,.2f}")
        print(f"  📉 Long MA(21): ${current_ma21:,.2f}")
        print(f"  📊 RSI(14): {current_rsi:.2f}")
        
        # Determine current market condition
        trend = "BULLISH" if current_ma8 > current_ma21 else "BEARISH"
        trend_emoji = "🟢" if trend == "BULLISH" else "🔴"
        
        rsi_condition = "OVERSOLD" if current_rsi < 30 else "OVERBOUGHT" if current_rsi > 70 else "NEUTRAL"
        rsi_emoji = "🟢" if rsi_condition == "OVERSOLD" else "🔴" if rsi_condition == "OVERBOUGHT" else "🟡"
        
        print(f"\n🎯 MARKET ANALYSIS:")
        print(f"  Trend: {trend_emoji} {trend}")
        print(f"  RSI Status: {rsi_emoji} {rsi_condition}")
        
        # Calculate distance to crossover
        ma_gap = current_ma8 - current_ma21
        ma_gap_pct = (ma_gap / current_ma21) * 100
        
        print(f"  MA Gap: ${ma_gap:.2f} ({ma_gap_pct:.2f}%)")
        
        # Entry signal analysis
        print(f"\n🚨 ENTRY SIGNAL ANALYSIS:")
        
        if trend == "BEARISH":
            # Look for bullish reversal
            price_above_short_ma = current_price > current_ma8
            gap_closing = ma_gap > -500  # Gap is small
            rsi_not_overbought = current_rsi < 65
            
            print(f"  📈 LOOKING FOR BUY SIGNAL:")
            print(f"    ✅ Price above MA(8): {price_above_short_ma} (${current_price:,.2f} vs ${current_ma8:,.2f})")
            print(f"    ✅ MA gap small: {gap_closing} ({ma_gap:.2f})")
            print(f"    ✅ RSI not overbought: {rsi_not_overbought} ({current_rsi:.2f})")
            
            # Calculate what price needs to be for signal
            breakeven_price = current_ma21  # Price needs to get MA8 above MA21
            price_change_needed = (breakeven_price - current_price) / current_price * 100
            
            print(f"\n🎯 BUY SIGNAL WILL TRIGGER WHEN:")
            print(f"    📈 Bitcoin rises to ~${breakeven_price:,.2f} ({price_change_needed:+.1f}%)")
            print(f"    📊 MA(8) crosses above MA(21)")
            print(f"    ⚖️ RSI stays below 65")
            
            if abs(price_change_needed) < 5:
                print(f"    🔥 CLOSE TO SIGNAL! Only {abs(price_change_needed):.1f}% away")
            elif abs(price_change_needed) < 10:
                print(f"    ⚡ MODERATE DISTANCE: {abs(price_change_needed):.1f}% away")
            else:
                print(f"    ⏰ PATIENCE NEEDED: {abs(price_change_needed):.1f}% away")
                
        else:  # BULLISH trend
            print(f"  📈 BULLISH TREND ACTIVE - LOOK FOR:")
            print(f"    🔴 Sell signals if RSI > 70")
            print(f"    🔴 Sell signals if MA(8) crosses below MA(21)")
            
        # Show recent signal history
        print(f"\n📜 RECENT SIGNAL HISTORY (Last 10 periods):")
        
        # Generate signals for last 10 periods
        for i in range(-10, 0):
            timestamp = df.index[i]
            price = close.iloc[i]
            ma8_val = ma8.iloc[i]
            ma21_val = ma21.iloc[i]
            rsi_val = rsi.iloc[i]
            
            # Check for crossover
            if i > -10:  # Need previous value
                ma8_prev = ma8.iloc[i-1]
                ma21_prev = ma21.iloc[i-1]
                
                signal = ""
                if ma8_val > ma21_val and ma8_prev <= ma21_prev and rsi_val < 65:
                    signal = "🟢 BUY"
                elif ma8_val < ma21_val and ma8_prev >= ma21_prev:
                    signal = "🔴 SELL"
                elif rsi_val < 30:
                    signal = "🟡 OVERSOLD"
                elif rsi_val > 70:
                    signal = "🟡 OVERBOUGHT"
                else:
                    signal = "⚪ HOLD"
                
                print(f"    {timestamp.strftime('%m-%d %H:%M')} | ${price:,.0f} | RSI:{rsi_val:.0f} | {signal}")
        
        # Risk management
        print(f"\n⚠️ RISK MANAGEMENT RULES:")
        print(f"  🛑 Stop Loss: 10% below entry price")
        print(f"  💰 Position Size: Maximum 30% of portfolio per trade")
        print(f"  ⏰ Hold Time: Monitor daily, exit on opposite signal")
        print(f"  🎯 Take Profit: Consider taking profits at +15% or RSI > 70")
        
        # What to watch for
        print(f"\n👀 WHAT TO WATCH FOR NEXT:")
        if trend == "BEARISH":
            print(f"  1. Bitcoin price movement toward ${current_ma21:,.2f}")
            print(f"  2. MA(8) line starting to curve upward")
            print(f"  3. RSI bouncing from oversold levels")
            print(f"  4. Volume increase on any upward movement")
        else:
            print(f"  1. Signs of trend weakening")
            print(f"  2. RSI approaching overbought (>70)")
            print(f"  3. MA(8) starting to flatten or turn down")
            print(f"  4. Volume decreasing on upward moves")
        
        print(f"\n✅ SUMMARY:")
        print(f"  🎯 Current Signal: {'🟡 HOLD - Waiting for entry' if trend == 'BEARISH' else '🟡 HOLD - Monitor for exit'}")
        print(f"  📊 Market Condition: {trend_emoji} {trend} trend, {rsi_emoji} {rsi_condition} RSI")
        print(f"  ⏰ Next Action: {'Wait for bullish crossover' if trend == 'BEARISH' else 'Monitor for bearish signals'}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    analyze_entry_points()