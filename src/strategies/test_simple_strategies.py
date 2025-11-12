#!/usr/bin/env python3
"""
Simplified trading strategies for immediate testing
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import pandas as pd
import numpy as np
from data.database import get_db
from data.models import MarketData
from strategies.technical_indicators import TechnicalIndicators

class SimpleMomentumStrategy:
    """Simplified momentum strategy for testing"""
    
    def __init__(self):
        self.name = "Simple Momentum"
        self.fast_period = 5
        self.slow_period = 20
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """Generate momentum signals using moving average crossover"""
        close = data['close_price']
        
        # Calculate moving averages
        ma_fast = close.rolling(window=self.fast_period).mean()
        ma_slow = close.rolling(window=self.slow_period).mean()
        
        # Generate signals
        signals = pd.Series(index=data.index, dtype=float)
        signals[:] = 0.0
        
        # Simple crossover strategy
        for i in range(self.slow_period, len(data)):
            if ma_fast.iloc[i] > ma_slow.iloc[i] and ma_fast.iloc[i-1] <= ma_slow.iloc[i-1]:
                signals.iloc[i] = 1.0  # Buy signal
            elif ma_fast.iloc[i] < ma_slow.iloc[i] and ma_fast.iloc[i-1] >= ma_slow.iloc[i-1]:
                signals.iloc[i] = -1.0  # Sell signal
        
        return signals
    
    def backtest(self, data: pd.DataFrame, initial_capital: float = 10000):
        """Simple backtesting"""
        signals = self.generate_signals(data)
        
        cash = initial_capital
        position = 0
        portfolio_values = []
        trades = []
        
        for i, (timestamp, row) in enumerate(data.iterrows()):
            current_price = row['close_price']
            signal = signals.iloc[i]
            
            # Current portfolio value
            portfolio_value = cash + (position * current_price)
            portfolio_values.append(portfolio_value)
            
            # Execute trades
            if signal == 1.0 and position == 0:  # Buy
                shares_to_buy = cash * 0.95 / current_price  # Use 95% of cash
                position = shares_to_buy
                cash = cash - (shares_to_buy * current_price)
                trades.append({'type': 'BUY', 'price': current_price, 'shares': shares_to_buy, 'timestamp': timestamp})
                
            elif signal == -1.0 and position > 0:  # Sell
                cash = cash + (position * current_price)
                trades.append({'type': 'SELL', 'price': current_price, 'shares': position, 'timestamp': timestamp})
                position = 0
        
        # Final value
        final_price = data['close_price'].iloc[-1]
        final_value = cash + (position * final_price)
        
        # Calculate metrics
        total_return = (final_value - initial_capital) / initial_capital
        
        return {
            'final_value': final_value,
            'total_return': total_return,
            'trades': trades,
            'portfolio_values': portfolio_values
        }

def test_simple_strategies():
    """Test simplified strategies"""
    print("🎯 Testing Simplified Trading Strategies")
    print("=" * 50)
    
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
                'open_price': float(record.open_price),
                'high_price': float(record.high_price),
                'low_price': float(record.low_price),
                'close_price': float(record.close_price),
                'volume': float(record.volume)
            })
        
        df = pd.DataFrame(data)
        df.set_index('timestamp', inplace=True)
        
        print(f"📊 Testing with {len(df)} data points")
        print(f"💰 Price range: ${df['close_price'].min():.2f} - ${df['close_price'].max():.2f}")
        
        # Test momentum strategy
        momentum_strategy = SimpleMomentumStrategy()
        result = momentum_strategy.backtest(df)
        
        print(f"\n📈 Simple Momentum Strategy Results:")
        print(f"  Final Value: ${result['final_value']:.2f}")
        print(f"  Total Return: {result['total_return']:.2%}")
        print(f"  Number of Trades: {len(result['trades'])}")
        
        # Show recent trades
        if result['trades']:
            print(f"\n🔄 Recent Trades:")
            for trade in result['trades'][-5:]:
                print(f"  {trade['type']} {trade['shares']:.4f} at ${trade['price']:.2f} on {trade['timestamp']}")
        
        # Buy & Hold comparison
        buy_hold_return = (df['close_price'].iloc[-1] - df['close_price'].iloc[0]) / df['close_price'].iloc[0]
        buy_hold_final = 10000 * (1 + buy_hold_return)
        
        print(f"\n💎 Buy & Hold Comparison:")
        print(f"  Final Value: ${buy_hold_final:.2f}")
        print(f"  Total Return: {buy_hold_return:.2%}")
        
        # Performance comparison
        print(f"\n🏆 Performance Summary:")
        if result['total_return'] > buy_hold_return:
            print(f"  🎉 Momentum strategy OUTPERFORMED by {(result['total_return'] - buy_hold_return)*100:.2f}%")
        else:
            print(f"  📉 Momentum strategy UNDERPERFORMED by {(buy_hold_return - result['total_return'])*100:.2f}%")
        
        # Generate current signals
        signals = momentum_strategy.generate_signals(df)
        latest_signal = signals.iloc[-1]
        latest_price = df['close_price'].iloc[-1]
        
        print(f"\n🤖 Current Trading Signal:")
        print(f"  Current Price: ${latest_price:.2f}")
        if latest_signal > 0:
            print(f"  Signal: 🟢 BUY ({latest_signal:.2f})")
        elif latest_signal < 0:
            print(f"  Signal: 🔴 SELL ({latest_signal:.2f})")
        else:
            print(f"  Signal: 🟡 HOLD ({latest_signal:.2f})")
        
        # Technical analysis summary
        print(f"\n📊 Technical Analysis Summary:")
        close = df['close_price']
        ma5 = close.rolling(5).mean().iloc[-1]
        ma20 = close.rolling(20).mean().iloc[-1]
        
        print(f"  MA(5): ${ma5:.2f}")
        print(f"  MA(20): ${ma20:.2f}")
        print(f"  Trend: {'🟢 BULLISH' if ma5 > ma20 else '🔴 BEARISH'}")
        
        print("\n✅ Strategy testing completed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_simple_strategies()