#!/usr/bin/env python3
"""
Week 1 Strategy - REFINED - Better balance of quality and quantity
Relaxed parameters for more trade opportunities while maintaining quality
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import pandas as pd
import numpy as np
from data.database import get_db
from data.models import MarketData
from strategies.technical_indicators import TechnicalIndicators

class Week1RefinedStrategy:
    """
    Enhanced strategy with REFINED Week 1 parameters:
    
    Quick Wins (unchanged):
    1. Wider stop loss (15%)
    2. Higher timeframe trend filter (MA50/MA200)
    
    Week 1 REFINED (relaxed for more trades):
    3. Trade cooldown: 10 → 7 periods
    4. Volume confirmation: 1.2x → 1.1x average
    5. MACD confirmation (must align with MA signal)
    6. ADX trend strength: 25 → 20 (allows more trending markets)
    
    Target: 15-20 trades with 55-60% win rate
    """
    
    def __init__(self):
        self.name = "Week 1 Refined Strategy"
        self.indicators = TechnicalIndicators()
        self.fast_ma = 8
        self.slow_ma = 21
        self.rsi_oversold = 35
        self.rsi_overbought = 65
        self.last_trade_index = -100
        self.cooldown_periods = 7  # REDUCED from 10
        self.volume_multiplier = 1.1  # REDUCED from 1.2
        self.adx_threshold = 20  # REDUCED from 25
    
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
        """Check if current volume is above average (RELAXED threshold)"""
        avg_volume = data['volume'].rolling(window).mean()
        return data['volume'] > (avg_volume * self.volume_multiplier)
    
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """Generate trading signals with ALL 7 filters (REFINED parameters)"""
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
        
        # Volume confirmation (RELAXED: 1.1x instead of 1.2x)
        data['volume_confirmed'] = self.volume_confirmation(data)
        
        # Initialize signals
        data['signal'] = 0
        data['position'] = 0
        data['entry_price'] = 0.0
        data['stop_loss'] = 0.0
        data['take_profit'] = 0.0
        
        position = 0
        entry_price = 0
        
        for i in range(len(data)):
            if i < 200:  # Need enough data for MA200
                continue
            
            # Filter 1: Higher timeframe trend (MA50 > MA200)
            trend_up = data.iloc[i]['ma50'] > data.iloc[i]['ma200']
            
            # Filter 2: Trade cooldown (RELAXED: 7 periods instead of 10)
            cooldown_passed = (i - self.last_trade_index) >= self.cooldown_periods
            
            # Filter 3: Volume confirmation (RELAXED: 1.1x instead of 1.2x)
            volume_ok = data.iloc[i]['volume_confirmed']
            
            # Filter 4: MACD confirmation (MACD must align with trend)
            macd_bullish = data.iloc[i]['macd'] > data.iloc[i]['macd_signal']
            
            # Filter 5: ADX trend strength (RELAXED: >20 instead of >25)
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
                    entry_price = data.iloc[i]['close_price']
                    data.loc[data.index[i], 'entry_price'] = entry_price
                    data.loc[data.index[i], 'stop_loss'] = entry_price * 0.85  # 15% stop loss
                    data.loc[data.index[i], 'take_profit'] = entry_price * 1.30  # 30% profit target
                    self.last_trade_index = i
                    
            elif position == 1:
                # SELL conditions
                ma_cross_down = (data.iloc[i]['ma_fast'] < data.iloc[i]['ma_slow'] and 
                               data.iloc[i-1]['ma_fast'] >= data.iloc[i-1]['ma_slow'])
                rsi_overbought = data.iloc[i]['rsi'] > self.rsi_overbought
                stop_loss_hit = data.iloc[i]['close_price'] <= data.iloc[i-1]['stop_loss']
                take_profit_hit = data.iloc[i]['close_price'] >= data.iloc[i-1]['take_profit']
                
                if ma_cross_down or rsi_overbought or stop_loss_hit or take_profit_hit:
                    data.loc[data.index[i], 'signal'] = -1
                    position = 0
                    entry_price = 0
                else:
                    # Carry forward position and stops
                    data.loc[data.index[i], 'entry_price'] = data.iloc[i-1]['entry_price']
                    data.loc[data.index[i], 'stop_loss'] = data.iloc[i-1]['stop_loss']
                    data.loc[data.index[i], 'take_profit'] = data.iloc[i-1]['take_profit']
            
            data.loc[data.index[i], 'position'] = position
        
        return data
    
    def backtest(self, data: pd.DataFrame, initial_capital: float = 10000) -> dict:
        """Backtest the strategy"""
        signals = self.generate_signals(data)
        
        capital = initial_capital
        position = 0
        entry_price = 0
        trades = []
        equity_curve = [initial_capital]
        
        for i in range(len(signals)):
            current_price = signals.iloc[i]['close_price']
            signal = signals.iloc[i]['signal']
            
            if signal == 1 and position == 0:
                # BUY
                position = capital / current_price
                entry_price = current_price
                capital = 0
                trades.append({
                    'type': 'BUY',
                    'price': current_price,
                    'timestamp': signals.iloc[i]['timestamp']
                })
                
            elif signal == -1 and position > 0:
                # SELL
                capital = position * current_price
                profit = capital - initial_capital
                trades.append({
                    'type': 'SELL',
                    'price': current_price,
                    'profit': profit,
                    'return': (current_price - entry_price) / entry_price * 100,
                    'timestamp': signals.iloc[i]['timestamp']
                })
                position = 0
                entry_price = 0
            
            # Track equity
            if position > 0:
                equity_curve.append(position * current_price)
            else:
                equity_curve.append(capital)
        
        # Close any open position
        if position > 0:
            capital = position * signals.iloc[-1]['close_price']
        
        # Calculate metrics
        final_value = capital if capital > 0 else equity_curve[-1]
        total_return = ((final_value - initial_capital) / initial_capital) * 100
        
        # Win rate
        sell_trades = [t for t in trades if t['type'] == 'SELL']
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
        
        return {
            'initial_capital': initial_capital,
            'final_value': final_value,
            'total_return': total_return,
            'win_rate': win_rate,
            'max_drawdown': max_drawdown,
            'volatility': volatility,
            'sharpe_ratio': sharpe,
            'trades': trades,
            'equity_curve': equity_curve
        }


def compare_strategies():
    """Compare Original, Quick Wins, Week 1, and Week 1 Refined strategies"""
    from strategies.phase2_final_test import OptimizedPhase2Strategy
    from strategies.optimized_strategy_quick_wins import QuickWinsStrategy
    from strategies.optimized_strategy_week1 import Week1Strategy
    from sqlalchemy.orm import Session
    
    # Get data
    db = next(get_db())
    data = pd.read_sql(
        db.query(MarketData).filter(MarketData.symbol == 'BTC/USDT').statement,
        db.bind
    )
    data = data.sort_values('timestamp').reset_index(drop=True)
    
    print(f"\n{'='*80}")
    print(f"STRATEGY COMPARISON - Week 1 REFINED vs Others")
    print(f"{'='*80}")
    print(f"Dataset: {len(data)} data points from {data['timestamp'].min()} to {data['timestamp'].max()}")
    print(f"{'='*80}\n")
    
    # Test all strategies
    strategies = [
        ("Original (Phase 2)", OptimizedPhase2Strategy()),
        ("Quick Wins", QuickWinsStrategy()),
        ("Week 1 (Original)", Week1Strategy()),
        ("Week 1 REFINED", Week1RefinedStrategy())
    ]
    
    results = []
    for name, strategy in strategies:
        print(f"\nTesting {name}...")
        result = strategy.backtest(data)
        results.append((name, result))
    
    # Print comparison table
    print(f"\n{'='*80}")
    print(f"RESULTS COMPARISON")
    print(f"{'='*80}\n")
    
    print(f"{'Metric':<25} {'Original':<15} {'Quick Wins':<15} {'Week 1':<15} {'Week 1 REF':<15}")
    print(f"{'-'*85}")
    
    metrics = [
        ('Final Value', 'final_value', '${:.2f}'),
        ('Total Return', 'total_return', '{:.2f}%'),
        ('Win Rate', 'win_rate', '{:.2f}%'),
        ('Max Drawdown', 'max_drawdown', '{:.2f}%'),
        ('Volatility', 'volatility', '{:.2f}%'),
        ('Sharpe Ratio', 'sharpe_ratio', '{:.3f}')
    ]
    
    for metric_name, metric_key, format_str in metrics:
        values = [format_str.format(r[1][metric_key]) for _, r in results]
        print(f"{metric_name:<25} {values[0]:<15} {values[1]:<15} {values[2]:<15} {values[3]:<15}")
    
    # Count trades manually from trade list
    trade_counts = []
    for name, result in results:
        sell_trades = [t for t in result['trades'] if t['type'] == 'SELL']
        trade_counts.append(len(sell_trades))
    
    print(f"{'Total Trades':<25} {trade_counts[0]:<15} {trade_counts[1]:<15} {trade_counts[2]:<15} {trade_counts[3]:<15}")
    
    print(f"\n{'='*80}")
    print(f"IMPROVEMENTS vs Original")
    print(f"{'='*80}\n")
    
    orig_result = results[0][1]
    for i, (name, result) in enumerate(results[1:], 1):
        print(f"\n{name}:")
        print(f"  Win Rate:      {orig_result['win_rate']:.2f}% → {result['win_rate']:.2f}% "
              f"({((result['win_rate'] - orig_result['win_rate']) / orig_result['win_rate'] * 100):+.1f}%)")
        print(f"  Return:        {orig_result['total_return']:.2f}% → {result['total_return']:.2f}% "
              f"({((result['total_return'] - orig_result['total_return']) / abs(orig_result['total_return']) * 100):+.1f}%)")
        print(f"  Max Drawdown:  {orig_result['max_drawdown']:.2f}% → {result['max_drawdown']:.2f}% "
              f"({((result['max_drawdown'] - orig_result['max_drawdown']) / abs(orig_result['max_drawdown']) * 100):+.1f}%)")
        print(f"  Volatility:    {orig_result['volatility']:.2f}% → {result['volatility']:.2f}% "
              f"({((result['volatility'] - orig_result['volatility']) / orig_result['volatility'] * 100):+.1f}%)")
        print(f"  Trades:        {trade_counts[0]} → {trade_counts[i]} "
              f"({((trade_counts[i] - trade_counts[0]) / trade_counts[0] * 100):+.1f}%)")


if __name__ == "__main__":
    compare_strategies()
