#!/usr/bin/env python3
"""
Quick Wins Strategy - Immediate Improvements to Phase 2
Implements 3 quick changes for immediate performance boost
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import pandas as pd
import numpy as np
from data.database import get_db
from data.models import MarketData
from strategies.technical_indicators import TechnicalIndicators

class QuickWinsStrategy:
    """
    Enhanced strategy with Quick Win improvements:
    1. Wider stop loss (10% → 15%) for crypto volatility
    2. Higher timeframe trend filter (MA50/MA200)
    3. Trade cooldown period (quality over quantity)
    """
    
    def __init__(self):
        self.name = "Quick Wins Strategy"
        self.indicators = TechnicalIndicators()
        self.fast_ma = 8
        self.slow_ma = 21
        self.rsi_oversold = 35
        self.rsi_overbought = 65
        self.last_trade_index = -100  # Track last trade for cooldown
        self.cooldown_periods = 10  # Minimum bars between trades
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Generate optimized signals with Quick Win improvements
        """
        signals = pd.Series(index=data.index, dtype=float)
        signals[:] = 0.0
        
        close = data['close_price']
        
        # Core indicators
        ma_fast = close.rolling(window=self.fast_ma).mean()
        ma_slow = close.rolling(window=self.slow_ma).mean()
        rsi = self.indicators.rsi(close, window=14)
        
        # ✅ QUICK WIN #2: Higher timeframe trend filter
        ma_50 = close.rolling(window=50).mean()
        ma_200 = close.rolling(window=200).mean()
        
        # Generate signals
        for i in range(max(self.slow_ma, 200), len(data)):
            # Higher timeframe trend
            higher_tf_bullish = ma_50.iloc[i] > ma_200.iloc[i]
            higher_tf_bearish = ma_50.iloc[i] < ma_200.iloc[i]
            
            # Primary: MA crossover
            ma_bullish = ma_fast.iloc[i] > ma_slow.iloc[i]
            ma_crossover_up = (ma_fast.iloc[i] > ma_slow.iloc[i] and 
                              ma_fast.iloc[i-1] <= ma_slow.iloc[i-1])
            ma_crossover_down = (ma_fast.iloc[i] < ma_slow.iloc[i] and 
                               ma_fast.iloc[i-1] >= ma_slow.iloc[i-1])
            
            # Secondary: RSI confirmation
            rsi_oversold = rsi.iloc[i] < self.rsi_oversold
            rsi_overbought = rsi.iloc[i] > self.rsi_overbought
            
            # ✅ QUICK WIN #3: Trade cooldown period
            cooldown_ok = (i - self.last_trade_index) >= self.cooldown_periods
            
            # BUY: MA crossover up + RSI not overbought + HIGHER TF BULLISH + COOLDOWN
            if (ma_crossover_up and 
                not rsi_overbought and 
                higher_tf_bullish and  # ✅ Only buy in uptrend!
                cooldown_ok):
                signals.iloc[i] = 1.0
                self.last_trade_index = i
            
            # SELL: MA crossover down OR RSI very overbought
            elif ma_crossover_down or (rsi_overbought and rsi.iloc[i] > 70):
                signals.iloc[i] = -1.0
                self.last_trade_index = i
            
            # Alternative BUY: Strong oversold + bullish trend + HIGHER TF BULLISH
            elif (rsi_oversold and 
                  ma_bullish and 
                  rsi.iloc[i] < 30 and 
                  higher_tf_bullish and  # ✅ Trend confirmation
                  cooldown_ok):
                signals.iloc[i] = 0.5  # Weaker signal
                self.last_trade_index = i
        
        return signals
    
    def backtest(self, data: pd.DataFrame, initial_capital: float = 10000):
        """
        Optimized backtesting with Quick Win improvements
        """
        signals = self.generate_signals(data)
        
        cash = initial_capital
        position = 0
        portfolio_values = []
        trades = []
        
        # Risk management
        max_position_pct = 0.30  # Max 30% per trade
        stop_loss_pct = 0.15     # ✅ QUICK WIN #1: 15% stop loss (was 10%)
        entry_price = 0
        
        for i, (timestamp, row) in enumerate(data.iterrows()):
            current_price = row['close_price']
            signal = signals.iloc[i]
            
            # Current portfolio value
            portfolio_value = cash + (position * current_price)
            portfolio_values.append(portfolio_value)
            
            # Stop loss check
            if position > 0 and entry_price > 0:
                if current_price <= entry_price * (1 - stop_loss_pct):
                    # Stop loss triggered
                    cash = cash + (position * current_price)
                    trades.append({
                        'type': 'STOP_LOSS', 
                        'price': current_price, 
                        'shares': position, 
                        'timestamp': timestamp
                    })
                    position = 0
                    entry_price = 0
            
            # Signal-based trading
            if signal > 0 and position == 0:  # Buy signal
                position_size = max_position_pct * signal  # Scale by signal strength
                max_investment = portfolio_value * position_size
                shares_to_buy = max_investment / current_price
                
                if cash >= max_investment:
                    position = shares_to_buy
                    cash = cash - (shares_to_buy * current_price)
                    entry_price = current_price
                    trades.append({
                        'type': 'BUY', 
                        'price': current_price, 
                        'shares': shares_to_buy, 
                        'timestamp': timestamp,
                        'signal_strength': signal
                    })
                
            elif signal < 0 and position > 0:  # Sell signal
                cash = cash + (position * current_price)
                trades.append({
                    'type': 'SELL', 
                    'price': current_price, 
                    'shares': position, 
                    'timestamp': timestamp
                })
                position = 0
                entry_price = 0
        
        # Final calculations
        final_price = data['close_price'].iloc[-1]
        final_value = cash + (position * final_price)
        total_return = (final_value - initial_capital) / initial_capital
        
        # Performance metrics
        portfolio_values = np.array(portfolio_values)
        returns = np.diff(portfolio_values) / portfolio_values[:-1]
        volatility = np.std(returns) * np.sqrt(365 * 24) if len(returns) > 0 else 0
        sharpe_ratio = np.mean(returns) / np.std(returns) if np.std(returns) > 0 else 0
        
        # Win rate calculation
        profitable_trades = 0
        total_completed_trades = 0
        
        for i in range(len(trades) - 1):
            if trades[i]['type'] == 'BUY' and trades[i+1]['type'] in ['SELL', 'STOP_LOSS']:
                total_completed_trades += 1
                if trades[i+1]['price'] > trades[i]['price']:
                    profitable_trades += 1
        
        win_rate = profitable_trades / total_completed_trades if total_completed_trades > 0 else 0
        
        return {
            'final_value': final_value,
            'total_return': total_return,
            'trades': trades,
            'portfolio_values': portfolio_values,
            'volatility': volatility,
            'sharpe_ratio': sharpe_ratio,
            'win_rate': win_rate,
            'max_drawdown': self._calculate_max_drawdown(portfolio_values),
            'total_trades': len([t for t in trades if t['type'] == 'BUY'])
        }
    
    def _calculate_max_drawdown(self, portfolio_values):
        """Calculate maximum drawdown"""
        running_max = np.maximum.accumulate(portfolio_values)
        drawdown = (portfolio_values - running_max) / running_max
        return np.min(drawdown)


def compare_strategies():
    """Compare Original vs Quick Wins strategy"""
    from strategies.phase2_final_test import OptimizedPhase2Strategy
    
    print("=" * 80)
    print("🚀 QUICK WINS STRATEGY COMPARISON")
    print("=" * 80)
    
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
        
        print(f"\n📊 Dataset: {len(df)} data points")
        print(f"📅 Period: {df.index[0]} to {df.index[-1]}")
        print()
        
        # Test both strategies
        strategies = {
            'Original Phase 2': OptimizedPhase2Strategy(),
            'Quick Wins': QuickWinsStrategy()
        }
        
        results = {}
        
        for name, strategy in strategies.items():
            print(f"Testing {name}...")
            result = strategy.backtest(df)
            results[name] = result
        
        # Print comparison
        print("\n" + "=" * 80)
        print("📊 PERFORMANCE COMPARISON")
        print("=" * 80)
        
        print(f"\n{'Metric':<25} {'Original':<20} {'Quick Wins':<20} {'Improvement':<15}")
        print("-" * 80)
        
        metrics = [
            ('Final Value', 'final_value', '${:,.2f}'),
            ('Total Return', 'total_return', '{:.2%}'),
            ('Win Rate', 'win_rate', '{:.2%}'),
            ('Sharpe Ratio', 'sharpe_ratio', '{:.3f}'),
            ('Max Drawdown', 'max_drawdown', '{:.2%}'),
            ('Volatility', 'volatility', '{:.2%}')
        ]
        
        # Count trades manually
        original_trades = len([t for t in results['Original Phase 2']['trades'] if t['type'] == 'BUY'])
        quick_wins_trades = len([t for t in results['Quick Wins']['trades'] if t['type'] == 'BUY'])
        
        for metric_name, metric_key, fmt in metrics:
            original = results['Original Phase 2'][metric_key]
            quick_wins = results['Quick Wins'][metric_key]
            
            if metric_key in ['max_drawdown']:  # Lower is better
                improvement = (original - quick_wins) / abs(original) if original != 0 else 0
                improvement_str = f"{improvement:+.1%}" if improvement != 0 else "-"
            else:  # Higher is better
                improvement = (quick_wins - original) / abs(original) if original != 0 else 0
                improvement_str = f"{improvement:+.1%}" if improvement != 0 else "-"
            
            print(f"{metric_name:<25} {fmt.format(original):<20} {fmt.format(quick_wins):<20} {improvement_str:<15}")
        
        # Print trade count separately
        trade_improvement = (quick_wins_trades - original_trades) / original_trades if original_trades > 0 else 0
        print(f"{'Total Trades':<25} {original_trades:<20} {quick_wins_trades:<20} {trade_improvement:+.1%}")
        
        print("\n" + "=" * 80)
        print("✅ QUICK WINS IMPLEMENTED:")
        print("=" * 80)
        print("1. ✅ Stop loss widened from 10% to 15%")
        print("2. ✅ Added MA50/MA200 higher timeframe trend filter")
        print("3. ✅ Implemented 10-period cooldown between trades")
        print("\n📈 Expected improvements:")
        print("   • Fewer false signals (trend filter)")
        print("   • Less stopped out early (wider stops)")
        print("   • Higher quality trades (cooldown)")
        print("=" * 80)
        
    finally:
        db.close()


if __name__ == "__main__":
    compare_strategies()
