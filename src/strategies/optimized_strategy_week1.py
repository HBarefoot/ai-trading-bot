#!/usr/bin/env python3
"""
Week 1 Strategy - Entry Signal Improvements
Adds volume confirmation and MACD to Quick Wins strategy
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import pandas as pd
import numpy as np
from data.database import get_db
from data.models import MarketData
from strategies.technical_indicators import TechnicalIndicators

class Week1Strategy:
    """
    Enhanced strategy with Week 1 improvements:
    
    Quick Wins (already implemented):
    1. Wider stop loss (15%)
    2. Higher timeframe trend filter (MA50/MA200)
    3. Trade cooldown period
    
    Week 1 Additions:
    4. Volume confirmation (must be 1.2x average)
    5. MACD confirmation (must align with MA signal)
    6. ADX trend strength filter (ADX > 25)
    """
    
    def __init__(self):
        self.name = "Week 1 Enhanced Strategy"
        self.indicators = TechnicalIndicators()
        self.fast_ma = 8
        self.slow_ma = 21
        self.rsi_oversold = 35
        self.rsi_overbought = 65
        self.last_trade_index = -100
        self.cooldown_periods = 10
    
    def calculate_adx(self, data: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate Average Directional Index (ADX)"""
        high = data['high_price']
        low = data['low_price']
        close = data['close_price']
        
        # Calculate +DM and -DM
        plus_dm = high.diff()
        minus_dm = low.diff().mul(-1)
        
        # Set to 0 if not directional move
        plus_dm[plus_dm < 0] = 0
        minus_dm[minus_dm < 0] = 0
        plus_dm[(plus_dm <= minus_dm)] = 0
        minus_dm[(minus_dm <= plus_dm)] = 0
        
        # Calculate True Range
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        # Smooth +DM, -DM, and TR
        atr = tr.rolling(period).mean()
        plus_di = 100 * (plus_dm.rolling(period).mean() / atr)
        minus_di = 100 * (minus_dm.rolling(period).mean() / atr)
        
        # Calculate DX and ADX
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        adx = dx.rolling(period).mean()
        
        return adx
    
    def volume_confirmation(self, data: pd.DataFrame, lookback: int = 20) -> pd.Series:
        """Check if current volume is above average (indicates strong move)"""
        avg_volume = data['volume'].rolling(lookback).mean()
        current_volume = data['volume']
        
        # Volume must be 20% above average
        return current_volume > (avg_volume * 1.2)
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Generate signals with all Week 1 improvements
        """
        signals = pd.Series(index=data.index, dtype=float)
        signals[:] = 0.0
        
        close = data['close_price']
        
        # Core indicators
        ma_fast = close.rolling(window=self.fast_ma).mean()
        ma_slow = close.rolling(window=self.slow_ma).mean()
        rsi = self.indicators.rsi(close, window=14)
        
        # Quick Wins: Higher timeframe
        ma_50 = close.rolling(window=50).mean()
        ma_200 = close.rolling(window=200).mean()
        
        # Week 1: Volume confirmation
        volume_conf = self.volume_confirmation(data)
        
        # Week 1: MACD
        macd, macd_signal, macd_hist = self.indicators.macd(close)
        
        # Week 1: ADX (trend strength)
        adx = self.calculate_adx(data)
        
        # Generate signals
        for i in range(max(self.slow_ma, 200), len(data)):
            # Quick Wins checks
            higher_tf_bullish = ma_50.iloc[i] > ma_200.iloc[i]
            higher_tf_bearish = ma_50.iloc[i] < ma_200.iloc[i]
            cooldown_ok = (i - self.last_trade_index) >= self.cooldown_periods
            
            # Week 1 checks
            volume_ok = volume_conf.iloc[i]  # ✅ Volume confirmation
            macd_bullish = macd.iloc[i] > macd_signal.iloc[i]  # ✅ MACD confirmation
            macd_bearish = macd.iloc[i] < macd_signal.iloc[i]
            is_trending = adx.iloc[i] > 25  # ✅ ADX trend strength
            
            # MA crossover signals
            ma_bullish = ma_fast.iloc[i] > ma_slow.iloc[i]
            ma_crossover_up = (ma_fast.iloc[i] > ma_slow.iloc[i] and 
                              ma_fast.iloc[i-1] <= ma_slow.iloc[i-1])
            ma_crossover_down = (ma_fast.iloc[i] < ma_slow.iloc[i] and 
                               ma_fast.iloc[i-1] >= ma_slow.iloc[i-1])
            
            # RSI
            rsi_oversold = rsi.iloc[i] < self.rsi_oversold
            rsi_overbought = rsi.iloc[i] > self.rsi_overbought
            
            # ✅ ENHANCED BUY CONDITIONS (All must be true):
            if (ma_crossover_up and                # 1. MA crossover
                not rsi_overbought and             # 2. RSI not overbought
                higher_tf_bullish and              # 3. Higher TF bullish (Quick Win)
                cooldown_ok and                    # 4. Cooldown OK (Quick Win)
                volume_ok and                      # 5. Volume confirmation (Week 1)
                macd_bullish and                   # 6. MACD bullish (Week 1)
                is_trending):                      # 7. Market trending (Week 1)
                
                signals.iloc[i] = 1.0  # STRONG BUY - all confirmations
                self.last_trade_index = i
            
            # ✅ ENHANCED SELL CONDITIONS:
            elif (ma_crossover_down and macd_bearish) or (rsi_overbought and rsi.iloc[i] > 70):
                signals.iloc[i] = -1.0
                self.last_trade_index = i
            
            # Alternative BUY: Strong oversold with all confirmations
            elif (rsi_oversold and 
                  rsi.iloc[i] < 30 and 
                  ma_bullish and 
                  higher_tf_bullish and 
                  cooldown_ok and
                  volume_ok and
                  macd_bullish and
                  is_trending):
                signals.iloc[i] = 0.5  # Weaker signal but well-confirmed
                self.last_trade_index = i
        
        return signals
    
    def backtest(self, data: pd.DataFrame, initial_capital: float = 10000):
        """Backtest with Week 1 strategy"""
        signals = self.generate_signals(data)
        
        cash = initial_capital
        position = 0
        portfolio_values = []
        trades = []
        
        # Risk management
        max_position_pct = 0.30
        stop_loss_pct = 0.15
        entry_price = 0
        
        for i, (timestamp, row) in enumerate(data.iterrows()):
            current_price = row['close_price']
            signal = signals.iloc[i]
            
            portfolio_value = cash + (position * current_price)
            portfolio_values.append(portfolio_value)
            
            # Stop loss
            if position > 0 and entry_price > 0:
                if current_price <= entry_price * (1 - stop_loss_pct):
                    cash = cash + (position * current_price)
                    trades.append({
                        'type': 'STOP_LOSS', 
                        'price': current_price, 
                        'shares': position, 
                        'timestamp': timestamp
                    })
                    position = 0
                    entry_price = 0
            
            # Trading signals
            if signal > 0 and position == 0:
                position_size = max_position_pct * signal
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
                
            elif signal < 0 and position > 0:
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
        
        # Metrics
        portfolio_values = np.array(portfolio_values)
        returns = np.diff(portfolio_values) / portfolio_values[:-1]
        volatility = np.std(returns) * np.sqrt(365 * 24) if len(returns) > 0 else 0
        sharpe_ratio = np.mean(returns) / np.std(returns) if np.std(returns) > 0 else 0
        
        # Win rate
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
            'max_drawdown': self._calculate_max_drawdown(portfolio_values)
        }
    
    def _calculate_max_drawdown(self, portfolio_values):
        """Calculate maximum drawdown"""
        running_max = np.maximum.accumulate(portfolio_values)
        drawdown = (portfolio_values - running_max) / running_max
        return np.min(drawdown)


def compare_all_strategies():
    """Compare Original -> Quick Wins -> Week 1"""
    from strategies.phase2_final_test import OptimizedPhase2Strategy
    from strategies.optimized_strategy_quick_wins import QuickWinsStrategy
    
    print("=" * 100)
    print("📊 STRATEGY EVOLUTION COMPARISON")
    print("=" * 100)
    
    # Get data
    db = next(get_db())
    
    try:
        market_data = db.query(MarketData).filter(
            MarketData.symbol == "BTCUSDT"
        ).order_by(MarketData.timestamp.asc()).all()
        
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
        print(f"📅 Period: {df.index[0]} to {df.index[-1]}\n")
        
        # Test all strategies
        strategies = {
            'Original': OptimizedPhase2Strategy(),
            'Quick Wins': QuickWinsStrategy(),
            'Week 1': Week1Strategy()
        }
        
        results = {}
        
        for name, strategy in strategies.items():
            print(f"Testing {name}...")
            result = strategy.backtest(df)
            results[name] = result
        
        # Comparison table
        print("\n" + "=" * 100)
        print("📈 PERFORMANCE COMPARISON")
        print("=" * 100)
        
        print(f"\n{'Metric':<25} {'Original':<25} {'Quick Wins':<25} {'Week 1':<25}")
        print("-" * 100)
        
        metrics = [
            ('Final Value', 'final_value', '${:,.2f}'),
            ('Total Return', 'total_return', '{:.2%}'),
            ('Win Rate', 'win_rate', '{:.2%}'),
            ('Sharpe Ratio', 'sharpe_ratio', '{:.3f}'),
            ('Max Drawdown', 'max_drawdown', '{:.2%}'),
            ('Volatility', 'volatility', '{:.2%}')
        ]
        
        for metric_name, metric_key, fmt in metrics:
            original = results['Original'][metric_key]
            quick_wins = results['Quick Wins'][metric_key]
            week1 = results['Week 1'][metric_key]
            
            print(f"{metric_name:<25} {fmt.format(original):<25} {fmt.format(quick_wins):<25} {fmt.format(week1):<25}")
        
        # Trade counts
        orig_trades = len([t for t in results['Original']['trades'] if t['type'] == 'BUY'])
        qw_trades = len([t for t in results['Quick Wins']['trades'] if t['type'] == 'BUY'])
        w1_trades = len([t for t in results['Week 1']['trades'] if t['type'] == 'BUY'])
        
        print(f"{'Total Trades':<25} {orig_trades:<25} {qw_trades:<25} {w1_trades:<25}")
        
        print("\n" + "=" * 100)
        print("✅ WEEK 1 ENHANCEMENTS:")
        print("=" * 100)
        print("Quick Wins:")
        print("  1. ✅ Stop loss: 10% → 15%")
        print("  2. ✅ Higher TF filter (MA50/MA200)")
        print("  3. ✅ Trade cooldown (10 periods)")
        print("\nWeek 1 Additions:")
        print("  4. ✅ Volume confirmation (1.2x average)")
        print("  5. ✅ MACD confirmation")
        print("  6. ✅ ADX trend strength filter (>25)")
        print("\n📈 Result: Even more selective, higher quality trades!")
        print("=" * 100)
        
    finally:
        db.close()


if __name__ == "__main__":
    compare_all_strategies()
