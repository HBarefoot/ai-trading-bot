#!/usr/bin/env python3
"""
Advanced trading strategies using comprehensive technical indicators
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import pandas as pd
import numpy as np
from data.database import get_db
from data.models import MarketData
from strategies.technical_indicators import TechnicalIndicators

class AdvancedMomentumStrategy:
    """Advanced momentum strategy with multiple indicators"""
    
    def __init__(self):
        self.name = "Advanced Momentum"
        self.indicators = TechnicalIndicators()
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """Generate sophisticated momentum signals"""
        signals = pd.Series(index=data.index, dtype=float)
        signals[:] = 0.0
        
        # Calculate indicators
        rsi = self.indicators.rsi(data['close_price'], window=14)
        macd_line, macd_signal, macd_histogram = self.indicators.macd(data['close_price'])
        bb_upper, bb_middle, bb_lower = self.indicators.bollinger_bands(data['close_price'])
        
        # Moving averages for trend
        ma_fast = data['close_price'].rolling(window=10).mean()
        ma_slow = data['close_price'].rolling(window=30).mean()
        
        close = data['close_price']
        
        # Generate signals based on multiple conditions
        for i in range(30, len(data)):
            buy_conditions = 0
            sell_conditions = 0
            
            # Condition 1: RSI oversold/overbought
            if rsi.iloc[i] < 30:  # Oversold
                buy_conditions += 1
            elif rsi.iloc[i] > 70:  # Overbought
                sell_conditions += 1
            
            # Condition 2: MACD crossover
            if (macd_line.iloc[i] > macd_signal.iloc[i] and 
                macd_line.iloc[i-1] <= macd_signal.iloc[i-1]):
                buy_conditions += 1
            elif (macd_line.iloc[i] < macd_signal.iloc[i] and 
                  macd_line.iloc[i-1] >= macd_signal.iloc[i-1]):
                sell_conditions += 1
            
            # Condition 3: MA trend
            if ma_fast.iloc[i] > ma_slow.iloc[i]:
                buy_conditions += 1
            else:
                sell_conditions += 1
            
            # Condition 4: Bollinger Bands
            if close.iloc[i] < bb_lower.iloc[i]:  # Near lower band
                buy_conditions += 1
            elif close.iloc[i] > bb_upper.iloc[i]:  # Near upper band
                sell_conditions += 1
            
            # Generate signal if enough conditions met
            if buy_conditions >= 3:
                signals.iloc[i] = 1.0
            elif sell_conditions >= 3:
                signals.iloc[i] = -1.0
        
        return signals
    
    def backtest(self, data: pd.DataFrame, initial_capital: float = 10000):
        """Advanced backtesting with risk management"""
        signals = self.generate_signals(data)
        
        cash = initial_capital
        position = 0
        portfolio_values = []
        trades = []
        max_position_size = 0.20  # Max 20% per trade
        
        for i, (timestamp, row) in enumerate(data.iterrows()):
            current_price = row['close_price']
            signal = signals.iloc[i]
            
            # Current portfolio value
            portfolio_value = cash + (position * current_price)
            portfolio_values.append(portfolio_value)
            
            # Execute trades with position sizing
            if signal == 1.0 and position == 0:  # Buy
                max_investment = portfolio_value * max_position_size
                shares_to_buy = max_investment / current_price
                if cash >= max_investment:
                    position = shares_to_buy
                    cash = cash - (shares_to_buy * current_price)
                    trades.append({
                        'type': 'BUY', 
                        'price': current_price, 
                        'shares': shares_to_buy, 
                        'timestamp': timestamp,
                        'portfolio_value': portfolio_value
                    })
                
            elif signal == -1.0 and position > 0:  # Sell
                cash = cash + (position * current_price)
                trades.append({
                    'type': 'SELL', 
                    'price': current_price, 
                    'shares': position, 
                    'timestamp': timestamp,
                    'portfolio_value': portfolio_value
                })
                position = 0
        
        # Final value
        final_price = data['close_price'].iloc[-1]
        final_value = cash + (position * final_price)
        
        # Calculate advanced metrics
        portfolio_values = np.array(portfolio_values)
        returns = np.diff(portfolio_values) / portfolio_values[:-1]
        
        # Risk metrics
        volatility = np.std(returns) * np.sqrt(365 * 24)  # Assuming hourly data
        sharpe_ratio = np.mean(returns) / np.std(returns) if np.std(returns) > 0 else 0
        max_drawdown = self._calculate_max_drawdown(portfolio_values)
        
        total_return = (final_value - initial_capital) / initial_capital
        
        return {
            'final_value': final_value,
            'total_return': total_return,
            'trades': trades,
            'portfolio_values': portfolio_values,
            'volatility': volatility,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'win_rate': self._calculate_win_rate(trades)
        }
    
    def _calculate_max_drawdown(self, portfolio_values):
        """Calculate maximum drawdown"""
        running_max = np.maximum.accumulate(portfolio_values)
        drawdown = (portfolio_values - running_max) / running_max
        return np.min(drawdown)
    
    def _calculate_win_rate(self, trades):
        """Calculate win rate from trades"""
        if len(trades) < 2:
            return 0
        
        profits = []
        for i in range(1, len(trades), 2):  # Buy-sell pairs
            if i < len(trades):
                buy_price = trades[i-1]['price']
                sell_price = trades[i]['price']
                profit = (sell_price - buy_price) / buy_price
                profits.append(profit)
        
        if not profits:
            return 0
        
        wins = sum(1 for p in profits if p > 0)
        return wins / len(profits)

def test_advanced_strategies():
    """Test advanced strategies with comprehensive analysis"""
    print("🚀 Testing Advanced Trading Strategies")
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
        
        # Test advanced momentum strategy
        advanced_strategy = AdvancedMomentumStrategy()
        result = advanced_strategy.backtest(df)
        
        print(f"\n🎯 Advanced Momentum Strategy Results:")
        print(f"  Final Value: ${result['final_value']:.2f}")
        print(f"  Total Return: {result['total_return']:.2%}")
        print(f"  Number of Trades: {len(result['trades'])}")
        print(f"  Win Rate: {result['win_rate']:.2%}")
        print(f"  Sharpe Ratio: {result['sharpe_ratio']:.3f}")
        print(f"  Max Drawdown: {result['max_drawdown']:.2%}")
        print(f"  Volatility: {result['volatility']:.2%}")
        
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
            print(f"  🎉 Advanced strategy OUTPERFORMED by {(result['total_return'] - buy_hold_return)*100:.2f}%")
        else:
            print(f"  📉 Advanced strategy UNDERPERFORMED by {(buy_hold_return - result['total_return'])*100:.2f}%")
        
        # Current market analysis with technical indicators
        print(f"\n🤖 Current Market Analysis:")
        indicators = TechnicalIndicators()
        
        # Calculate current indicators
        rsi = indicators.rsi(df['close_price'], window=14)
        macd_line, macd_signal, macd_histogram = indicators.macd(df['close_price'])
        bb_upper, bb_middle, bb_lower = indicators.bollinger_bands(df['close_price'])
        
        latest_price = df['close_price'].iloc[-1]
        latest_rsi = rsi.iloc[-1]
        latest_macd = macd_line.iloc[-1]
        latest_macd_signal = macd_signal.iloc[-1]
        
        print(f"  Current Price: ${latest_price:.2f}")
        print(f"  RSI(14): {latest_rsi:.2f} {'🔴 Overbought' if latest_rsi > 70 else '🟢 Oversold' if latest_rsi < 30 else '🟡 Neutral'}")
        print(f"  MACD: {latest_macd:.2f} vs Signal: {latest_macd_signal:.2f} {'🟢 Bullish' if latest_macd > latest_macd_signal else '🔴 Bearish'}")
        print(f"  Bollinger Position: {'🔴 Upper' if latest_price > bb_upper.iloc[-1] else '🟢 Lower' if latest_price < bb_lower.iloc[-1] else '🟡 Middle'}")
        
        # Generate current signal
        signals = advanced_strategy.generate_signals(df)
        latest_signal = signals.iloc[-1]
        
        print(f"\n🎯 Advanced Trading Signal:")
        if latest_signal > 0:
            print(f"  Signal: 🟢 STRONG BUY ({latest_signal:.2f})")
        elif latest_signal < 0:
            print(f"  Signal: 🔴 STRONG SELL ({latest_signal:.2f})")
        else:
            print(f"  Signal: 🟡 HOLD ({latest_signal:.2f})")
        
        print("\n✅ Advanced strategy testing completed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_advanced_strategies()