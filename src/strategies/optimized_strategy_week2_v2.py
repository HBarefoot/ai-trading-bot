"""
Week 2 v2: Optimized Exit Strategy
Improvements over Week 2:
- Relaxed RSI overbought (65 → 70) to allow more profit
- Lower TP1 target (3.0 ATR → 2.5 ATR) for easier hits
- Lower trailing activation (10% → 5%) for more activation
- Keep all other Week 2 features (ATR stops, partial exits, TP2, trailing)

Expected: TP1 hit rate 40-50%, avg profit +1.5%, return 2.5-3%
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from typing import List, Dict, Optional, Tuple
import pandas as pd
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from data.database import get_db
from data.models import MarketData
from strategies.technical_indicators import TechnicalIndicators

class OptimizedStrategyWeek2V2:
    """Week 2 v2 - Optimized Exit Strategy with relaxed parameters"""
    
    def __init__(self):
        self.name = "Week 2 v2 Optimized"
        
        # Entry filters (same as Week 1 Refined - proven)
        self.rsi_overbought = 70  # ✅ OPTIMIZED: Was 65 - allow more profit BEFORE EXIT
        self.adx_threshold = 20
        self.volume_multiplier = 1.1
        self.signal_cooldown = 7  # hours
        self.cooldown_periods = 7  # For compatibility
        self.last_trade_index = -100  # For compatibility
        
        # Week 2 v2 Exit Parameters - OPTIMIZED
        self.atr_multiplier_stop = 2.0  # Stop loss distance
        self.atr_multiplier_tp1 = 2.5  # ✅ OPTIMIZED: Was 3.0 - easier to hit (1.25:1 R/R)
        self.atr_multiplier_tp2 = 3.5  # ✅ OPTIMIZED: Was 4.0 - more achievable (1.75:1 R/R)
        self.trailing_activation = 0.05  # ✅ OPTIMIZED: Was 0.10 - activate at 5% profit
        self.trailing_percentage = 0.05  # Trail 5% below peak
        self.partial_exit_percentage = 0.5  # Exit 50% at TP1
        
        self.indicators = TechnicalIndicators()
        self.last_signal_time = None
        
    def calculate_atr(self, data: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate Average True Range"""
        high = data['high_price']
        low = data['low_price']
        close = data['close_price']
        
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        
        return atr
    
    def calculate_adx(self, data: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate Average Directional Index"""
        high = data['high_price']
        low = data['low_price']
        close = data['close_price']
        
        # Plus/Minus Directional Movement
        plus_dm = high.diff()
        minus_dm = -low.diff()
        
        plus_dm[plus_dm < 0] = 0
        minus_dm[minus_dm < 0] = 0
        
        # True Range
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        # Smoothed indicators
        atr = tr.rolling(window=period).mean()
        plus_di = 100 * (plus_dm.rolling(window=period).mean() / atr)
        minus_di = 100 * (minus_dm.rolling(window=period).mean() / atr)
        
        # ADX
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        adx = dx.rolling(window=period).mean()
        
        return adx

    def generate_signals(self, data: pd.DataFrame) -> List[Dict]:
        """
        Generate trading signals with Week 2 v2 optimized exit strategy
        Returns list of signals with dynamic ATR-based stops and targets
        """
        signals = []
        
        if len(data) < 50:
            return signals
        
        # Calculate all indicators
        data = data.copy()
        data['rsi'] = self.indicators.rsi(data['close_price'])
        macd_line, signal_line, histogram = self.indicators.macd(
            data['close_price']
        )
        data['macd'] = macd_line
        data['macd_signal'] = signal_line
        data['macd_histogram'] = histogram
        
        # MAs for entry (Week 1 Refined style)
        data['ma_fast'] = self.indicators.simple_moving_average(data['close_price'], window=20)
        data['ma_slow'] = self.indicators.simple_moving_average(data['close_price'], window=50)
        data['ma50'] = self.indicators.simple_moving_average(data['close_price'], window=50)
        data['ma200'] = self.indicators.simple_moving_average(data['close_price'], window=200)
        
        data['adx'] = self.calculate_adx(data)
        data['atr'] = self.calculate_atr(data)
        
        # Volume analysis
        data['volume_sma'] = data['volume'].rolling(window=20).mean()
        
        # Track position and exit levels
        in_position = False
        entry_price = 0
        entry_time = None
        stop_loss = 0
        tp1 = 0
        tp2 = 0
        position_size = 1.0  # Full position (1.0 = 100%, 0.5 = 50%)
        highest_price = 0
        trailing_stop = 0
        tp1_hit = False
        
        for i in range(200, len(data)):  # Need 200 periods for MA200
            current_time = data.iloc[i]['timestamp']
            current_price = data.iloc[i]['close_price']
            current_high = data.iloc[i]['high_price']
            current_low = data.iloc[i]['low_price']
            current_atr = data.iloc[i]['atr']
            
            # ENTRY LOGIC - Week 1 Refined style (MA crossover, not RSI oversold)
            if not in_position:
                # Check cooldown
                cooldown_passed = (i - self.last_trade_index) >= self.cooldown_periods
                if not cooldown_passed:
                    continue
                
                # Entry filters (Week 1 Refined - proven to work)
                ma_cross_up = (data.iloc[i]['ma_fast'] > data.iloc[i]['ma_slow'] and
                              data.iloc[i-1]['ma_fast'] <= data.iloc[i-1]['ma_slow'])
                rsi_ok = data.iloc[i]['rsi'] < self.rsi_overbought
                trend_up = data.iloc[i]['ma50'] > data.iloc[i]['ma200']
                macd_bullish = data.iloc[i]['macd'] > data.iloc[i]['macd_signal']
                strong_trend = data.iloc[i]['adx'] > self.adx_threshold
                volume_ok = data.iloc[i]['volume'] > (data.iloc[i]['volume_sma'] * self.volume_multiplier)
                positive_macd = data.iloc[i]['macd_histogram'] > 0
                
                if (ma_cross_up and rsi_ok and trend_up and macd_bullish and 
                    strong_trend and volume_ok and positive_macd):
                    
                    # Calculate dynamic stop and targets using ATR
                    entry_price = current_price
                    entry_time = current_time
                    
                    # Week 2 v2: Optimized exit levels
                    stop_loss = entry_price - (self.atr_multiplier_stop * current_atr)
                    tp1 = entry_price + (self.atr_multiplier_tp1 * current_atr)  # 2.5 ATR (easier)
                    tp2 = entry_price + (self.atr_multiplier_tp2 * current_atr)  # 3.5 ATR (more achievable)
                    
                    signals.append({
                        'timestamp': current_time,
                        'signal': 'BUY',
                        'price': entry_price,
                        'rsi': data.iloc[i]['rsi'],
                        'macd': data.iloc[i]['macd'],
                        'adx': data.iloc[i]['adx'],
                        'atr': current_atr,
                        'stop_loss': stop_loss,
                        'tp1': tp1,
                        'tp2': tp2,
                        'reason': 'Week2v2: MA crossover + Trend + MACD + Volume + ADX'
                    })
                    
                    in_position = True
                    position_size = 1.0
                    highest_price = entry_price
                    trailing_stop = 0
                    tp1_hit = False
                    self.last_trade_index = i
            
            # EXIT LOGIC - Week 2 v2 with optimized cascade
            else:
                # Update highest price for trailing stop
                if current_high > highest_price:
                    highest_price = current_high
                
                current_profit_pct = (current_price - entry_price) / entry_price
                exit_signal = None
                exit_reason = None
                
                # Exit Priority (highest to lowest):
                
                # 1. TP2 - Full exit at second target
                if current_high >= tp2:
                    exit_signal = 'SELL'
                    exit_reason = 'TP2_HIT'
                    exit_price = tp2
                
                # 2. TP1 - Partial exit (50%), move stop to breakeven
                elif current_high >= tp1 and not tp1_hit:
                    exit_signal = 'SELL_PARTIAL'
                    exit_reason = 'TP1_HIT'
                    exit_price = tp1
                    tp1_hit = True
                    position_size = 0.5  # Keep 50%
                    stop_loss = entry_price  # Move stop to breakeven
                
                # 3. Trailing stop (only if activated by 5% profit)
                elif current_profit_pct >= self.trailing_activation:
                    # Activate/update trailing stop
                    new_trailing = highest_price * (1 - self.trailing_percentage)
                    if new_trailing > trailing_stop:
                        trailing_stop = new_trailing
                    
                    # Check if trailing stop hit
                    if current_low <= trailing_stop:
                        exit_signal = 'SELL'
                        exit_reason = 'TRAILING_STOP'
                        exit_price = trailing_stop
                
                # 4. Regular stop loss
                elif current_low <= stop_loss:
                    exit_signal = 'SELL'
                    exit_reason = 'STOP_LOSS'
                    exit_price = stop_loss
                
                # 5. MA crossover (bearish)
                elif (data.iloc[i]['ma_fast'] < data.iloc[i]['ma_slow'] and
                      data.iloc[i-1]['ma_fast'] >= data.iloc[i-1]['ma_slow']):
                    exit_signal = 'SELL'
                    exit_reason = 'MA_BEARISH_CROSS'
                    exit_price = current_price
                
                # 6. RSI overbought (OPTIMIZED: 70 instead of 65)
                elif data.iloc[i]['rsi'] > self.rsi_overbought:
                    exit_signal = 'SELL'
                    exit_reason = 'RSI_OVERBOUGHT'
                    exit_price = current_price
                
                # Execute exit
                if exit_signal:
                    profit_pct = (exit_price - entry_price) / entry_price * 100
                    
                    signals.append({
                        'timestamp': current_time,
                        'signal': exit_signal,
                        'price': exit_price,
                        'rsi': data.iloc[i]['rsi'],
                        'profit_pct': profit_pct,
                        'exit_reason': exit_reason,
                        'position_size': position_size,
                        'entry_price': entry_price,
                        'duration_hours': (current_time - entry_time).total_seconds() / 3600
                    })
                    
                    # Full exit or partial?
                    if exit_signal == 'SELL_PARTIAL':
                        # Continue holding 50%
                        pass
                    else:
                        # Full exit
                        in_position = False
                        entry_price = 0
                        entry_time = None
        
        return signals
    
    def backtest(self, db: Session, days: int = 90, initial_capital: float = 10000.0) -> Dict:
        """
        Backtest Week 2 v2 strategy with partial exit support
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Fetch data
        data = db.query(MarketData).filter(
            MarketData.timestamp >= start_date,
            MarketData.timestamp <= end_date,
            MarketData.symbol == 'BTC/USDT'  # Historical data has slash
        ).order_by(MarketData.timestamp).all()
        
        if not data:
            return {'error': 'No data available'}
        
        df = pd.DataFrame([{
            'timestamp': d.timestamp,
            'open_price': float(d.open_price),
            'high_price': float(d.high_price),
            'low_price': float(d.low_price),
            'close_price': float(d.close_price),
            'volume': float(d.volume)
        } for d in data])
        
        # Generate signals
        signals = self.generate_signals(df)
        
        # Calculate performance with partial exit support
        capital = initial_capital
        position = 0
        entry_price = 0
        trades = []
        equity_curve = [initial_capital]
        exit_reasons = {}
        total_profit = 0
        winning_profits = []
        
        for signal in signals:
            if signal['signal'] == 'BUY':
                position = capital / signal['price']
                entry_price = signal['price']
                trades.append({
                    'entry_time': signal['timestamp'],
                    'entry_price': entry_price,
                    'type': 'BUY'
                })
            
            elif signal['signal'] == 'SELL_PARTIAL':
                # Partial exit (50%)
                exit_size = position * 0.5
                exit_value = exit_size * signal['price']
                profit = exit_value - (exit_size * entry_price)
                capital += profit
                position -= exit_size
                total_profit += profit
                
                if profit > 0:
                    profit_pct = (signal['price'] - entry_price) / entry_price
                    winning_profits.append(profit_pct)
                
                trades.append({
                    'entry_time': trades[-1]['entry_time'],
                    'entry_price': entry_price,
                    'exit_time': signal['timestamp'],
                    'exit_price': signal['price'],
                    'profit': profit,
                    'profit_pct': signal['profit_pct'],
                    'exit_reason': signal['exit_reason'],
                    'position_size': 0.5,
                    'type': 'SELL_PARTIAL'
                })
                
                exit_reasons[signal['exit_reason']] = exit_reasons.get(signal['exit_reason'], 0) + 1
            
            elif signal['signal'] == 'SELL':
                # Full exit (or remaining 50% after partial)
                exit_value = position * signal['price']
                profit = exit_value - (position * entry_price)
                capital += profit
                total_profit += profit
                
                if profit > 0:
                    profit_pct = (signal['price'] - entry_price) / entry_price
                    winning_profits.append(profit_pct)
                
                trades.append({
                    'entry_time': trades[-1]['entry_time'],
                    'entry_price': entry_price,
                    'exit_time': signal['timestamp'],
                    'exit_price': signal['price'],
                    'profit': profit,
                    'profit_pct': signal['profit_pct'],
                    'exit_reason': signal['exit_reason'],
                    'position_size': signal.get('position_size', 1.0),
                    'type': 'SELL'
                })
                
                position = 0
                equity_curve.append(capital)
                exit_reasons[signal['exit_reason']] = exit_reasons.get(signal['exit_reason'], 0) + 1
        
        # Calculate metrics
        completed_trades = [t for t in trades if t['type'] in ['SELL', 'SELL_PARTIAL']]
        winning_trades = [t for t in completed_trades if t['profit'] > 0]
        losing_trades = [t for t in completed_trades if t['profit'] <= 0]
        
        win_rate = len(winning_trades) / len(completed_trades) if completed_trades else 0
        total_return = (capital - initial_capital) / initial_capital
        
        # Calculate drawdown
        equity_series = pd.Series(equity_curve)
        rolling_max = equity_series.expanding().max()
        drawdowns = (equity_series - rolling_max) / rolling_max
        max_drawdown = drawdowns.min()
        
        # Calculate volatility
        returns = equity_series.pct_change().dropna()
        volatility = returns.std()
        
        # Average profit per winning trade
        avg_profit_per_win = sum(winning_profits) / len(winning_profits) if winning_profits else 0
        
        return {
            'win_rate': win_rate,
            'total_return': total_return,
            'max_drawdown': max_drawdown,
            'volatility': volatility,
            'total_trades': len(completed_trades),
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'exit_reasons': exit_reasons,
            'avg_profit_per_win': avg_profit_per_win,
            'trades': completed_trades,
            'signals': signals
        }


def compare_all_strategies():
    """Compare Week 2 versions"""
    from strategies.optimized_strategy_quick_wins import QuickWinsStrategy
    from strategies.optimized_strategy_week1_refined import Week1RefinedStrategy
    from strategies.optimized_strategy_week2 import Week2Strategy
    
    db = next(get_db())
    
    print("\n" + "="*80)
    print("WEEK 2 v2 OPTIMIZATION RESULTS")
    print("="*80)
    
    strategies = [
        ("Quick Wins", QuickWinsStrategy()),
        ("Week 1 Refined", Week1RefinedStrategy()),
        ("Week 2 Original", Week2Strategy()),
        ("Week 2 v2 OPTIMIZED", OptimizedStrategyWeek2V2()),
    ]
    
    results = []
    for name, strategy in strategies:
        print(f"\n📊 Testing {name}...")
        result = strategy.backtest(db, days=90)
        results.append((name, result))
    
    # Print comparison table
    print("\n" + "="*80)
    print("RESULTS SUMMARY (90 days)")
    print("="*80)
    print(f"{'Strategy':<25} {'Win Rate':<12} {'Return':<12} {'Max DD':<12} {'Trades':<10}")
    print("-"*80)
    
    for name, result in results:
        if 'error' not in result:
            print(f"{name:<25} {result['win_rate']:<12.2%} {result['total_return']:<12.2%} "
                  f"{result['max_drawdown']:<12.2%} {result['total_trades']:<10}")
    
    # Week 2 versions detailed comparison
    print("\n" + "="*80)
    print("WEEK 2 DETAILED COMPARISON")
    print("="*80)
    
    week2_results = [(n, r) for n, r in results if 'Week 2' in n]
    
    for name, result in week2_results:
        if 'error' not in result:
            print(f"\n{name}:")
            print(f"  Win Rate: {result['win_rate']:.2%}")
            print(f"  Total Return: {result['total_return']:.2%}")
            print(f"  Max Drawdown: {result['max_drawdown']:.2%}")
            print(f"  Avg Profit/Win: {result.get('avg_profit_per_win', 0):.2%}")
            print(f"  Total Trades: {result['total_trades']}")
            print(f"  Exit Reasons: {result.get('exit_reasons', {})}")
    
    # Show Week 2 v2 trades in detail
    print("\n" + "="*80)
    print("WEEK 2 V2 - TRADE DETAILS")
    print("="*80)
    
    week2v2_result = [r for n, r in results if n == "Week 2 v2 Optimized"][0]
    if 'trades' in week2v2_result:
        for i, trade in enumerate(week2v2_result['trades'], 1):
            if trade['type'] in ['SELL', 'SELL_PARTIAL']:
                partial_tag = " (PARTIAL 50%)" if trade['type'] == 'SELL_PARTIAL' else ""
                print(f"\nTrade {i}{partial_tag}:")
                print(f"  Entry:  {trade['entry_time']} @ ${trade['entry_price']:.2f}")
                print(f"  Exit:   {trade['exit_time']} @ ${trade['exit_price']:.2f}")
                print(f"  Return: {trade['profit_pct']:.2f}%")
                print(f"  Reason: {trade['exit_reason']}")
                if 'duration_hours' in trade:
                    duration = (trade['exit_time'] - trade['entry_time']).total_seconds() / 3600
                    print(f"  Duration: {duration:.1f} hours")


if __name__ == "__main__":
    compare_all_strategies()
