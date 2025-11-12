#!/usr/bin/env python3
"""
Week 2 Strategy - Exit Strategy Improvements
Adds dynamic exits and profit-taking to Week 1 Refined strategy
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import pandas as pd
import numpy as np
from data.database import get_db
from data.models import MarketData
from strategies.technical_indicators import TechnicalIndicators

class Week2Strategy:
    """
    Enhanced strategy with Week 2 improvements:
    
    Week 1 REFINED (Entry filters):
    1. Wider stop loss (15% base)
    2. Higher timeframe trend filter (MA50/MA200)
    3. Trade cooldown (7 periods)
    4. Volume confirmation (1.1x average)
    5. MACD confirmation
    6. ADX trend strength (>20)
    
    Week 2 NEW (Exit improvements):
    7. Dynamic ATR-based stop loss (instead of fixed %)
    8. Take-profit targets (1.5:1 and 2:1 risk/reward)
    9. Trailing stop loss (activates at 10% profit)
    10. Partial profit taking (50% at first target)
    """
    
    def __init__(self):
        self.name = "Week 2 Exit Strategy"
        self.indicators = TechnicalIndicators()
        self.fast_ma = 8
        self.slow_ma = 21
        self.rsi_oversold = 35
        self.rsi_overbought = 65
        self.last_trade_index = -100
        self.cooldown_periods = 7
        self.volume_multiplier = 1.1
        self.adx_threshold = 20
        
        # Week 2: Exit strategy parameters
        self.atr_multiplier_stop = 2.0  # Stop loss = entry - (2 * ATR)
        self.atr_multiplier_tp1 = 3.0   # First target = entry + (3 * ATR) = 1.5:1 R/R
        self.atr_multiplier_tp2 = 4.0   # Second target = entry + (4 * ATR) = 2:1 R/R
        self.trailing_activation = 0.10  # Activate trailing stop at 10% profit
        self.trailing_percentage = 0.05  # Trail 5% below peak
        self.partial_exit_percentage = 0.5  # Take 50% off at TP1
    
    def calculate_atr(self, data: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate Average True Range"""
        high = data['high_price']
        low = data['low_price']
        close = data['close_price']
        
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        atr = tr.rolling(period).mean()
        return atr
    
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
    
    def volume_confirmation(self, data: pd.DataFrame, window: int = 20) -> pd.Series:
        """Check if current volume is above average"""
        avg_volume = data['volume'].rolling(window).mean()
        return data['volume'] > (avg_volume * self.volume_multiplier)
    
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """Generate trading signals with dynamic exit strategy"""
        data = data.copy()
        
        # Calculate all indicators
        data['ma_fast'] = data['close_price'].rolling(self.fast_ma).mean()
        data['ma_slow'] = data['close_price'].rolling(self.slow_ma).mean()
        data['ma50'] = data['close_price'].rolling(50).mean()
        data['ma200'] = data['close_price'].rolling(200).mean()
        data['rsi'] = self.indicators.rsi(data['close_price'])
        
        # Calculate MACD
        macd, signal, histogram = self.indicators.macd(data['close_price'])
        data['macd'] = macd
        data['macd_signal'] = signal
        data['macd_histogram'] = histogram
        
        # Calculate ADX (trend strength)
        data['adx'] = self.calculate_adx(data)
        
        # Calculate ATR (for dynamic stops)
        data['atr'] = self.calculate_atr(data)
        
        # Volume confirmation
        data['volume_confirmed'] = self.volume_confirmation(data)
        
        # Initialize signals
        data['signal'] = 0
        data['position'] = 0
        data['position_size'] = 1.0  # Full position or partial (0.5 after TP1)
        data['entry_price'] = 0.0
        data['stop_loss'] = 0.0
        data['take_profit_1'] = 0.0
        data['take_profit_2'] = 0.0
        data['trailing_stop'] = 0.0
        data['highest_price'] = 0.0
        data['exit_reason'] = ''
        
        position = 0
        position_size = 1.0
        entry_price = 0
        highest_price = 0
        tp1_hit = False
        
        for i in range(len(data)):
            if i < 200:  # Need enough data for MA200
                continue
            
            current_price = data.iloc[i]['close_price']
            current_atr = data.iloc[i]['atr']
            
            # Skip if ATR is NaN
            if pd.isna(current_atr) or current_atr == 0:
                continue
            
            # Filter 1: Higher timeframe trend (MA50 > MA200)
            trend_up = data.iloc[i]['ma50'] > data.iloc[i]['ma200']
            
            # Filter 2: Trade cooldown
            cooldown_passed = (i - self.last_trade_index) >= self.cooldown_periods
            
            # Filter 3: Volume confirmation
            volume_ok = data.iloc[i]['volume_confirmed']
            
            # Filter 4: MACD confirmation
            macd_bullish = data.iloc[i]['macd'] > data.iloc[i]['macd_signal']
            
            # Filter 5: ADX trend strength
            strong_trend = data.iloc[i]['adx'] > self.adx_threshold
            
            if position == 0:
                # BUY: All conditions must be met
                ma_cross_up = (data.iloc[i]['ma_fast'] > data.iloc[i]['ma_slow'] and 
                              data.iloc[i-1]['ma_fast'] <= data.iloc[i-1]['ma_slow'])
                rsi_ok = data.iloc[i]['rsi'] < self.rsi_overbought
                
                if (ma_cross_up and rsi_ok and trend_up and cooldown_passed and 
                    volume_ok and macd_bullish and strong_trend):
                    
                    data.loc[data.index[i], 'signal'] = 1
                    position = 1
                    position_size = 1.0
                    entry_price = current_price
                    highest_price = current_price
                    tp1_hit = False
                    
                    # Week 2: Dynamic ATR-based stops and targets
                    stop_loss = entry_price - (self.atr_multiplier_stop * current_atr)
                    tp1 = entry_price + (self.atr_multiplier_tp1 * current_atr)
                    tp2 = entry_price + (self.atr_multiplier_tp2 * current_atr)
                    
                    data.loc[data.index[i], 'entry_price'] = entry_price
                    data.loc[data.index[i], 'stop_loss'] = stop_loss
                    data.loc[data.index[i], 'take_profit_1'] = tp1
                    data.loc[data.index[i], 'take_profit_2'] = tp2
                    data.loc[data.index[i], 'trailing_stop'] = 0
                    data.loc[data.index[i], 'highest_price'] = highest_price
                    data.loc[data.index[i], 'position_size'] = position_size
                    
                    self.last_trade_index = i
                    
            elif position == 1:
                # Update highest price for trailing stop
                if current_price > highest_price:
                    highest_price = current_price
                
                # Get previous values
                prev_entry = data.iloc[i-1]['entry_price']
                prev_stop = data.iloc[i-1]['stop_loss']
                prev_tp1 = data.iloc[i-1]['take_profit_1']
                prev_tp2 = data.iloc[i-1]['take_profit_2']
                prev_trailing = data.iloc[i-1]['trailing_stop']
                
                # Calculate profit percentage
                profit_pct = (current_price - prev_entry) / prev_entry
                
                # Week 2: Check take profit targets
                exit_signal = False
                exit_reason = ''
                
                # TP2 hit - close remaining position
                if current_price >= prev_tp2:
                    exit_signal = True
                    exit_reason = 'TP2'
                    position_size = 0
                
                # TP1 hit - partial exit (50% if haven't done so already)
                elif current_price >= prev_tp1 and not tp1_hit:
                    tp1_hit = True
                    position_size = self.partial_exit_percentage
                    # Move stop to breakeven after TP1
                    prev_stop = prev_entry
                    exit_reason = 'TP1_PARTIAL'
                
                # Week 2: Trailing stop logic
                trailing_stop = prev_trailing
                if profit_pct >= self.trailing_activation:
                    # Activate trailing stop
                    trailing_stop = highest_price * (1 - self.trailing_percentage)
                    # Don't let trailing stop go below regular stop
                    trailing_stop = max(trailing_stop, prev_stop)
                    
                    # Check if trailing stop hit
                    if current_price <= trailing_stop:
                        exit_signal = True
                        exit_reason = 'TRAILING_STOP'
                        position_size = 0
                
                # Regular stop loss hit
                if current_price <= prev_stop:
                    exit_signal = True
                    exit_reason = 'STOP_LOSS'
                    position_size = 0
                
                # Original exit conditions (MA crossover or RSI)
                ma_cross_down = (data.iloc[i]['ma_fast'] < data.iloc[i]['ma_slow'] and 
                               data.iloc[i-1]['ma_fast'] >= data.iloc[i-1]['ma_slow'])
                rsi_overbought = data.iloc[i]['rsi'] > self.rsi_overbought
                
                if ma_cross_down and not exit_signal:
                    exit_signal = True
                    exit_reason = 'MA_CROSS'
                    position_size = 0
                elif rsi_overbought and not exit_signal:
                    exit_signal = True
                    exit_reason = 'RSI_OVERBOUGHT'
                    position_size = 0
                
                if exit_signal:
                    data.loc[data.index[i], 'signal'] = -1
                    data.loc[data.index[i], 'exit_reason'] = exit_reason
                    position = 0
                    position_size = 1.0
                    entry_price = 0
                    highest_price = 0
                    tp1_hit = False
                else:
                    # Carry forward position and stops
                    data.loc[data.index[i], 'entry_price'] = prev_entry
                    data.loc[data.index[i], 'stop_loss'] = prev_stop
                    data.loc[data.index[i], 'take_profit_1'] = prev_tp1
                    data.loc[data.index[i], 'take_profit_2'] = prev_tp2
                    data.loc[data.index[i], 'trailing_stop'] = trailing_stop
                    data.loc[data.index[i], 'highest_price'] = highest_price
                    data.loc[data.index[i], 'position_size'] = position_size
            
            data.loc[data.index[i], 'position'] = position
        
        return data
    
    def backtest(self, data: pd.DataFrame, initial_capital: float = 10000) -> dict:
        """Backtest the strategy with partial exits"""
        signals = self.generate_signals(data)
        
        capital = initial_capital
        position = 0
        position_size = 0
        entry_price = 0
        trades = []
        equity_curve = [initial_capital]
        
        for i in range(len(signals)):
            current_price = signals.iloc[i]['close_price']
            signal = signals.iloc[i]['signal']
            
            if signal == 1 and position == 0:
                # BUY - open full position
                position = capital / current_price
                position_size = 1.0
                entry_price = current_price
                capital = 0
                trades.append({
                    'type': 'BUY',
                    'price': current_price,
                    'size': 1.0,
                    'timestamp': signals.iloc[i]['timestamp']
                })
                
            elif signal == -1 and position > 0:
                # SELL - could be partial or full exit
                exit_reason = signals.iloc[i]['exit_reason']
                
                if exit_reason == 'TP1_PARTIAL':
                    # Partial exit - take 50% profit
                    exit_size = position * 0.5
                    capital += exit_size * current_price
                    position -= exit_size
                    position_size = 0.5
                    
                    trades.append({
                        'type': 'SELL_PARTIAL',
                        'price': current_price,
                        'size': 0.5,
                        'profit': (exit_size * current_price) - (exit_size * entry_price),
                        'return': (current_price - entry_price) / entry_price * 100,
                        'reason': exit_reason,
                        'timestamp': signals.iloc[i]['timestamp']
                    })
                else:
                    # Full exit - close entire position
                    exit_size = position
                    capital += exit_size * current_price
                    
                    trades.append({
                        'type': 'SELL',
                        'price': current_price,
                        'size': position_size,
                        'profit': (exit_size * current_price) - (exit_size * entry_price),
                        'return': (current_price - entry_price) / entry_price * 100,
                        'reason': exit_reason,
                        'timestamp': signals.iloc[i]['timestamp']
                    })
                    
                    position = 0
                    position_size = 0
                    entry_price = 0
            
            # Track equity
            if position > 0:
                equity_curve.append(capital + (position * current_price))
            else:
                equity_curve.append(capital)
        
        # Close any open position
        if position > 0:
            capital += position * signals.iloc[-1]['close_price']
        
        # Calculate metrics
        final_value = capital if capital > 0 else equity_curve[-1]
        total_return = ((final_value - initial_capital) / initial_capital) * 100
        
        # Win rate (count full exits only)
        sell_trades = [t for t in trades if t['type'] in ['SELL', 'SELL_PARTIAL']]
        winning_trades = len([t for t in sell_trades if t.get('return', 0) > 0])
        win_rate = (winning_trades / len(sell_trades) * 100) if sell_trades else 0
        
        # Max drawdown
        equity_series = pd.Series(equity_curve)
        running_max = equity_series.expanding().max()
        drawdown = (equity_series - running_max) / running_max * 100
        max_drawdown = drawdown.min()
        
        # Volatility
        returns = equity_series.pct_change().dropna()
        volatility = returns.std() * 100
        
        # Sharpe ratio
        sharpe = (returns.mean() / returns.std()) if returns.std() > 0 else 0
        
        # Average profit per trade
        profitable_trades = [t for t in sell_trades if t.get('return', 0) > 0]
        avg_profit = np.mean([t['return'] for t in profitable_trades]) if profitable_trades else 0
        
        # Count exits by reason
        exit_reasons = {}
        for t in sell_trades:
            reason = t.get('reason', 'UNKNOWN')
            exit_reasons[reason] = exit_reasons.get(reason, 0) + 1
        
        return {
            'initial_capital': initial_capital,
            'final_value': final_value,
            'total_return': total_return,
            'win_rate': win_rate,
            'max_drawdown': max_drawdown,
            'volatility': volatility,
            'sharpe_ratio': sharpe,
            'avg_profit_per_win': avg_profit,
            'trades': trades,
            'equity_curve': equity_curve,
            'exit_reasons': exit_reasons
        }


def compare_strategies():
    """Compare all strategies including Week 2"""
    from strategies.phase2_final_test import OptimizedPhase2Strategy
    from strategies.optimized_strategy_quick_wins import QuickWinsStrategy
    from strategies.optimized_strategy_week1_refined import Week1RefinedStrategy
    from sqlalchemy.orm import Session
    
    # Get data
    db = next(get_db())
    data = pd.read_sql(
        db.query(MarketData).filter(MarketData.symbol == 'BTC/USDT').statement,
        db.bind
    )
    data = data.sort_values('timestamp').reset_index(drop=True)
    
    print(f"\n{'='*80}")
    print(f"STRATEGY COMPARISON - Week 2 Exit Strategy vs Others")
    print(f"{'='*80}")
    print(f"Dataset: {len(data)} data points from {data['timestamp'].min()} to {data['timestamp'].max()}")
    print(f"{'='*80}\n")
    
    # Test all strategies
    strategies = [
        ("Original (Phase 2)", OptimizedPhase2Strategy()),
        ("Quick Wins", QuickWinsStrategy()),
        ("Week 1 Refined", Week1RefinedStrategy()),
        ("Week 2 Exit Strategy", Week2Strategy())
    ]
    
    results = {}
    for name, strategy in strategies:
        print(f"\nTesting {name}...")
        try:
            result = strategy.backtest(data)
            results[name] = result
        except Exception as e:
            print(f"  ❌ Error: {e}")
            continue
    
    # Print comparison table
    print(f"\n{'='*80}")
    print(f"RESULTS COMPARISON")
    print(f"{'='*80}\n")
    
    print(f"{'Metric':<25} {'Original':<15} {'Quick Wins':<15} {'Week 1 REF':<15} {'Week 2':<15}")
    print(f"{'-'*95}")
    
    metrics = [
        ('Final Value', 'final_value', '${:,.2f}'),
        ('Total Return', 'total_return', '{:.2f}%'),
        ('Win Rate', 'win_rate', '{:.2f}%'),
        ('Max Drawdown', 'max_drawdown', '{:.2f}%'),
        ('Volatility', 'volatility', '{:.2f}%'),
        ('Sharpe Ratio', 'sharpe_ratio', '{:.3f}')
    ]
    
    for metric_name, metric_key, format_str in metrics:
        values = []
        for name in ['Original (Phase 2)', 'Quick Wins', 'Week 1 Refined', 'Week 2 Exit Strategy']:
            if name in results:
                values.append(format_str.format(results[name][metric_key]))
            else:
                values.append('N/A')
        
        print(f"{metric_name:<25} {values[0]:<15} {values[1]:<15} {values[2]:<15} {values[3]:<15}")
    
    # Show avg profit for Week 2 separately
    if 'Week 2 Exit Strategy' in results:
        print(f"{'Avg Profit/Win':<25} {'-':<15} {'-':<15} {'-':<15} {results['Week 2 Exit Strategy']['avg_profit_per_win']:.2f}%")
    
    # Count trades
    print(f"\n{'Trade Counts':<25}", end='')
    for name in ['Original (Phase 2)', 'Quick Wins', 'Week 1 Refined', 'Week 2 Exit Strategy']:
        if name in results:
            sell_trades = [t for t in results[name]['trades'] if t['type'] in ['SELL', 'SELL_PARTIAL']]
            print(f"{len(sell_trades):<15}", end='')
        else:
            print(f"{'N/A':<15}", end='')
    print()
    
    # Show Week 2 exit reasons
    if 'Week 2 Exit Strategy' in results:
        print(f"\n{'='*80}")
        print(f"WEEK 2 EXIT ANALYSIS")
        print(f"{'='*80}")
        print("\nExit Reasons:")
        for reason, count in results['Week 2 Exit Strategy']['exit_reasons'].items():
            print(f"  {reason}: {count}")
    
    print(f"\n{'='*80}")
    print(f"IMPROVEMENTS vs Original")
    print(f"{'='*80}\n")
    
    if 'Original (Phase 2)' in results and 'Week 2 Exit Strategy' in results:
        orig = results['Original (Phase 2)']
        week2 = results['Week 2 Exit Strategy']
        
        print(f"Week 2 Exit Strategy:")
        print(f"  Win Rate:      {orig['win_rate']:.2f}% → {week2['win_rate']:.2f}% "
              f"({((week2['win_rate'] - orig['win_rate']) / orig['win_rate'] * 100):+.1f}%)")
        print(f"  Return:        {orig['total_return']:.2f}% → {week2['total_return']:.2f}% "
              f"({week2['total_return'] - orig['total_return']:+.2f}pp)")
        print(f"  Avg Profit:    ${week2['avg_profit_per_win']:.2f}% per winning trade")
        print(f"  Max Drawdown:  {orig['max_drawdown']:.2f}% → {week2['max_drawdown']:.2f}% "
              f"({((week2['max_drawdown'] - orig['max_drawdown']) / abs(orig['max_drawdown']) * 100):+.1f}%)")
        print(f"  Volatility:    {orig['volatility']:.2f}% → {week2['volatility']:.2f}% "
              f"({((week2['volatility'] - orig['volatility']) / orig['volatility'] * 100):+.1f}%)")


if __name__ == "__main__":
    compare_strategies()
