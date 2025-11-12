"""
Pivot Zone Strategy
Based on TradingView pivot point support/resistance zones
Implements zone-based entries with volume and trend confirmation
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from strategies.technical_indicators import TechnicalIndicators
from data.models import MarketData
from data.database import get_db


class PivotZoneStrategy:
    """
    Support/Resistance zone-based trading strategy
    Inspired by TradingView's pivot point strategies
    
    Entry Rules:
    - BUY: Price touches support zone and closes ABOVE it
    - SELL: Price touches resistance zone and closes BELOW it
    
    Filters:
    - Volume must be 1.2x average
    - Only trade with trend (optional)
    - Signal strength based on trend + volume confluence
    """
    
    def __init__(self):
        self.name = "Pivot Zone Strategy"
        self.indicators = TechnicalIndicators()
        
        # Zone multipliers (based on Fibonacci and pivot calculations)
        self.multipliers = {
            'r6': 1.5,
            'r5': 1.27,
            'r3': 0.786,
            'r2': 0.618,
            'r1': 0.23,
            'r0': 0.1,
            's0': 0.1,
            's1': 0.23,
            's2': 0.618,
            's3': 0.786,
            's5': 1.27,
            's6': 1.5
        }
        
        # Filters
        self.min_volume_multiplier = 1.2  # Volume must be 1.2x average
        self.use_trend_filter = True       # Only trade with trend
        self.ma_trend_period = 50          # For trend identification
        
        # Risk management
        # Optimized TP/SL for 3:1 Risk/Reward ratio
        self.stop_loss_pct = 0.10  # 10% stop loss (tighter)
        self.take_profit_pct = 0.30  # 30% take profit (wider - let winners run)
        self.max_position_pct = 0.30  # 30% max position size
    
    def calculate_pivot_zones(self, data: pd.DataFrame) -> Dict:
        """
        Calculate daily pivot zones based on opening range
        
        Args:
            data: DataFrame with OHLCV data
        
        Returns:
            Dict with keys: pp, r0-r6, s0-s6
            Each value is a pandas Series indexed by timestamp
        """
        # Make a copy and ensure we have datetime index
        df = data.copy()
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.set_index('timestamp')
        
        # Daily aggregation
        daily = df.resample('1D')
        
        # Pivot point = daily open
        pp = daily['open'].first()
        
        # Range calculation (max of multiple range measures)
        prev_high = daily['high'].max().shift(1)
        prev_low = daily['low'].min().shift(1)
        prev_close = daily['close'].last().shift(1)
        prev_close_2 = daily['close'].last().shift(2)
        
        range_1 = prev_high - prev_low
        range_2 = abs(prev_high - prev_close_2)
        range_3 = abs(prev_low - prev_close_2)
        range_4 = abs(prev_high - pp)
        range_5 = abs(prev_low - pp)
        range_6 = abs(prev_close - pp)
        
        range_val = pd.concat([range_1, range_2, range_3, range_4, range_5, range_6], axis=1).max(axis=1)
        
        # Calculate all zone levels
        zones = {'pp': pp}
        
        # Resistance zones
        for level in ['r0', 'r1', 'r2', 'r3', 'r5', 'r6']:
            zones[level] = pp + (range_val * self.multipliers[level])
        
        # Support zones
        for level in ['s0', 's1', 's2', 's3', 's5', 's6']:
            zones[level] = pp - (range_val * self.multipliers[level])
        
        # Forward-fill to match original data frequency
        for key in zones:
            zones[key] = zones[key].reindex(df.index, method='ffill')
        
        return zones
    
    def check_zone_touch_and_close(self, candle, zone_bottom, zone_top, direction):
        """
        Check if candle touched zone and closed in the right direction
        
        Args:
            candle: Single row from dataframe with OHLC
            zone_bottom: Lower bound of zone
            zone_top: Upper bound of zone
            direction: 'ABOVE' for buys, 'BELOW' for sells
        
        Returns:
            True if signal triggered, False otherwise
        """
        # Did candle touch the zone?
        touched = (candle['low'] <= zone_top) and (candle['high'] >= zone_bottom)
        
        # Did candle open in the zone?
        opened_in_zone = (zone_bottom <= candle['open'] <= zone_top)
        
        # Was there interaction with zone?
        interaction = touched or opened_in_zone
        
        if not interaction:
            return False
        
        # Check close direction
        if direction == 'ABOVE':
            return candle['close'] > zone_top
        elif direction == 'BELOW':
            return candle['close'] < zone_bottom
        
        return False
    
    def check_volume_confirmation(self, data: pd.DataFrame, i: int, lookback=20) -> bool:
        """
        Check if current volume confirms the move
        Volume should be above 1.2x the average
        """
        if i < lookback:
            return True  # Not enough data, skip filter
        
        avg_volume = data['volume'].iloc[i-lookback:i].mean()
        current_volume = data['volume'].iloc[i]
        
        return current_volume >= (avg_volume * self.min_volume_multiplier)
    
    def check_trend_direction(self, data: pd.DataFrame, i: int) -> str:
        """
        Determine overall trend direction
        Returns: 'BULLISH', 'BEARISH', or 'NEUTRAL'
        """
        if i < self.ma_trend_period:
            return 'NEUTRAL'
        
        # Use MA50 vs current price for trend
        ma50 = data['close'].iloc[i-50:i].mean()
        current_price = data['close'].iloc[i]
        
        # Also check longer MA if available
        if i >= 200:
            ma200 = data['close'].iloc[i-200:i].mean()
            if ma50 > ma200 * 1.02 and current_price > ma50:  # 2% buffer
                return 'BULLISH'
            elif ma50 < ma200 * 0.98 and current_price < ma50:
                return 'BEARISH'
            else:
                return 'NEUTRAL'
        else:
            # Simple trend based on MA50
            if current_price > ma50 * 1.02:
                return 'BULLISH'
            elif current_price < ma50 * 0.98:
                return 'BEARISH'
            else:
                return 'NEUTRAL'
    
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Generate buy/sell signals based on pivot zones
        
        Returns DataFrame with columns:
        - signal: 1.0 (buy), -1.0 (sell), 0.0 (hold)
        - zone_name: Which zone triggered
        - signal_strength: 0.0-1.0 confidence score
        """
        # Ensure we have a proper dataframe
        if isinstance(data, pd.DataFrame):
            df = data.copy()
        else:
            df = pd.DataFrame(data)
        
        zones = self.calculate_pivot_zones(df)
        
        signals = pd.DataFrame(index=df.index)
        signals['signal'] = 0.0
        signals['zone_name'] = ''
        signals['signal_strength'] = 0.0
        
        # Zone pairs to check (name, bottom, top)
        # Check support zones for buys, resistance zones for sells
        zone_pairs = [
            ('R5/R6', zones['r5'], zones['r6']),
            ('R2/R3', zones['r2'], zones['r3']),
            ('R0/R1', zones['r0'], zones['r1']),
            ('S0/S1', zones['s1'], zones['s0']),  # Note: s1 < s0
            ('S2/S3', zones['s3'], zones['s2']),
            ('S5/S6', zones['s6'], zones['s5']),
        ]
        
        # Start after we have enough data for all indicators
        start_idx = max(self.ma_trend_period, 200, 20)
        
        for i in range(start_idx, len(df)):
            candle = df.iloc[i]
            
            # Get trend
            trend = self.check_trend_direction(df, i)
            
            # Check volume
            volume_ok = self.check_volume_confirmation(df, i)
            
            # Check each zone
            for zone_name, zone_bottom, zone_top in zone_pairs:
                bottom_val = zone_bottom.iloc[i]
                top_val = zone_top.iloc[i]
                
                # BUY signal: Touched zone and closed ABOVE
                # This happens at support zones when price bounces
                if 'S' in zone_name:  # Support zones = potential buy
                    if self.check_zone_touch_and_close(candle, bottom_val, top_val, 'ABOVE'):
                        # Apply filters
                        if self.use_trend_filter and trend == 'BEARISH':
                            continue  # Don't buy in downtrend
                        
                        if not volume_ok:
                            continue  # Skip low volume signals
                        
                        # Calculate signal strength
                        strength = 0.6  # Base
                        if trend == 'BULLISH':
                            strength += 0.2
                        if volume_ok:
                            strength += 0.2
                        
                        signals.loc[signals.index[i], 'signal'] = 1.0
                        signals.loc[signals.index[i], 'zone_name'] = zone_name
                        signals.loc[signals.index[i], 'signal_strength'] = min(strength, 1.0)
                        break  # Only one signal per candle
                
                # SELL signal: Touched zone and closed BELOW
                # This happens at resistance zones when price rejects
                elif 'R' in zone_name:  # Resistance zones = potential sell
                    if self.check_zone_touch_and_close(candle, bottom_val, top_val, 'BELOW'):
                        # Apply filters
                        if self.use_trend_filter and trend == 'BULLISH':
                            continue  # Don't sell in uptrend
                        
                        if not volume_ok:
                            continue  # Skip low volume signals
                        
                        # Calculate signal strength
                        strength = 0.6  # Base
                        if trend == 'BEARISH':
                            strength += 0.2
                        if volume_ok:
                            strength += 0.2
                        
                        signals.loc[signals.index[i], 'signal'] = -1.0
                        signals.loc[signals.index[i], 'zone_name'] = zone_name
                        signals.loc[signals.index[i], 'signal_strength'] = min(strength, 1.0)
                        break  # Only one signal per candle
        
        return signals
    
    def backtest(self, symbol: str = 'BTC/USDT', lookback_days: int = 90, initial_capital: float = 10000):
        """
        Backtest the pivot zone strategy on historical data
        
        Args:
            symbol: Trading pair symbol
            lookback_days: Number of days to backtest
            initial_capital: Starting capital
        
        Returns:
            Dict with performance metrics and trade list
        """
        # Get historical data
        db = next(get_db())
        end_date = datetime.now()
        start_date = end_date - pd.Timedelta(days=lookback_days)
        
        records = db.query(MarketData).filter(
            MarketData.symbol == symbol,
            MarketData.timestamp >= start_date,
            MarketData.timestamp <= end_date
        ).order_by(MarketData.timestamp).all()
        
        if not records:
            return {
                'error': f'No data found for {symbol}',
                'trades': [],
                'win_rate': 0,
                'total_return': 0
            }
        
        # Convert to DataFrame
        data = pd.DataFrame([{
            'timestamp': r.timestamp,
            'open': float(r.open_price),
            'high': float(r.high_price),
            'low': float(r.low_price),
            'close': float(r.close_price),
            'volume': float(r.volume)
        } for r in records])
        
        data['timestamp'] = pd.to_datetime(data['timestamp'])
        data = data.set_index('timestamp')
        
        # Generate signals
        signals_df = self.generate_signals(data)
        
        # Backtest loop
        cash = initial_capital
        position = 0
        entry_price = 0
        entry_zone = ''
        portfolio_values = []
        trades = []
        
        for i in range(len(data)):
            timestamp = data.index[i]
            current_price = data['close'].iloc[i]
            signal = signals_df['signal'].iloc[i]
            signal_strength = signals_df['signal_strength'].iloc[i]
            zone_name = signals_df['zone_name'].iloc[i]
            
            # Portfolio value
            portfolio_value = cash + (position * current_price)
            portfolio_values.append(portfolio_value)
            
            # Stop loss and take profit checks
            if position > 0 and entry_price > 0:
                # Stop loss
                if current_price <= entry_price * (1 - self.stop_loss_pct):
                    proceeds = position * current_price
                    pnl = proceeds - (position * entry_price)
                    pnl_pct = (current_price / entry_price - 1) * 100
                    cash += proceeds
                    
                    trades.append({
                        'entry_time': entry_time,
                        'exit_time': timestamp,
                        'entry_price': entry_price,
                        'exit_price': current_price,
                        'shares': position,
                        'pnl': pnl,
                        'pnl_pct': pnl_pct,
                        'exit_reason': 'STOP_LOSS',
                        'zone': entry_zone
                    })
                    
                    position = 0
                    entry_price = 0
                    continue
                
                # Take profit
                if current_price >= entry_price * (1 + self.take_profit_pct):
                    proceeds = position * current_price
                    pnl = proceeds - (position * entry_price)
                    pnl_pct = (current_price / entry_price - 1) * 100
                    cash += proceeds
                    
                    trades.append({
                        'entry_time': entry_time,
                        'exit_time': timestamp,
                        'entry_price': entry_price,
                        'exit_price': current_price,
                        'shares': position,
                        'pnl': pnl,
                        'pnl_pct': pnl_pct,
                        'exit_reason': 'TAKE_PROFIT',
                        'zone': entry_zone
                    })
                    
                    position = 0
                    entry_price = 0
                    continue
            
            # Buy signal
            if signal > 0 and position == 0 and cash > 0:
                # Position size based on signal strength
                position_size = self.max_position_pct * signal_strength
                investment = portfolio_value * position_size
                
                if cash >= investment:
                    position = investment / current_price
                    cash -= investment
                    entry_price = current_price
                    entry_time = timestamp
                    entry_zone = zone_name
            
            # Sell signal (close position)
            elif signal < 0 and position > 0:
                proceeds = position * current_price
                pnl = proceeds - (position * entry_price)
                pnl_pct = (current_price / entry_price - 1) * 100
                cash += proceeds
                
                trades.append({
                    'entry_time': entry_time,
                    'exit_time': timestamp,
                    'entry_price': entry_price,
                    'exit_price': current_price,
                    'shares': position,
                    'pnl': pnl,
                    'pnl_pct': pnl_pct,
                    'exit_reason': 'SIGNAL',
                    'zone': entry_zone
                })
                
                position = 0
                entry_price = 0
        
        # Close final position if still open
        if position > 0:
            proceeds = position * data['close'].iloc[-1]
            pnl = proceeds - (position * entry_price)
            pnl_pct = (data['close'].iloc[-1] / entry_price - 1) * 100
            cash += proceeds
            
            trades.append({
                'entry_time': entry_time,
                'exit_time': data.index[-1],
                'entry_price': entry_price,
                'exit_price': data['close'].iloc[-1],
                'shares': position,
                'pnl': pnl,
                'pnl_pct': pnl_pct,
                'exit_reason': 'FINAL_CLOSE',
                'zone': entry_zone
            })
        
        # Calculate metrics
        final_value = cash
        total_return = ((final_value - initial_capital) / initial_capital) * 100
        
        winning_trades = [t for t in trades if t['pnl'] > 0]
        losing_trades = [t for t in trades if t['pnl'] <= 0]
        
        win_rate = (len(winning_trades) / len(trades) * 100) if trades else 0
        
        avg_win = np.mean([t['pnl_pct'] for t in winning_trades]) if winning_trades else 0
        avg_loss = np.mean([t['pnl_pct'] for t in losing_trades]) if losing_trades else 0
        
        # Max drawdown
        portfolio_series = pd.Series(portfolio_values)
        running_max = portfolio_series.cummax()
        drawdown = (portfolio_series - running_max) / running_max
        max_drawdown = drawdown.min() * 100
        
        return {
            'strategy': self.name,
            'symbol': symbol,
            'period': f'{lookback_days} days',
            'total_trades': len(trades),
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate': win_rate,
            'total_return': total_return,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'max_drawdown': max_drawdown,
            'final_value': final_value,
            'trades': trades
        }


if __name__ == '__main__':
    """Test the Pivot Zone strategy"""
    print("=" * 80)
    print("PIVOT ZONE STRATEGY - BACKTEST")
    print("=" * 80)
    print()
    
    strategy = PivotZoneStrategy()
    results = strategy.backtest(symbol='BTC/USDT', lookback_days=90)
    
    if 'error' in results:
        print(f"❌ Error: {results['error']}")
    else:
        print(f"📊 Strategy: {results['strategy']}")
        print(f"📈 Symbol: {results['symbol']}")
        print(f"📅 Period: {results['period']}")
        print(f"🎯 Total Trades: {results['total_trades']}")
        print(f"✅ Winning Trades: {results['winning_trades']}")
        print(f"❌ Losing Trades: {results['losing_trades']}")
        print(f"📊 Win Rate: {results['win_rate']:.2f}%")
        print(f"💰 Total Return: {results['total_return']:.2f}%")
        print(f"📈 Avg Win: {results['avg_win']:.2f}%")
        print(f"📉 Avg Loss: {results['avg_loss']:.2f}%")
        print(f"⚠️  Max Drawdown: {results['max_drawdown']:.2f}%")
        print(f"💵 Final Value: ${results['final_value']:.2f}")
        print()
        
        if results['trades']:
            print("Recent Trades:")
            print("-" * 80)
            for trade in results['trades'][-5:]:
                print(f"  {trade['entry_time'].strftime('%b %d, %I:%M %p')} @ ${trade['entry_price']:.2f} → "
                      f"{trade['exit_time'].strftime('%b %d, %I:%M %p')} @ ${trade['exit_price']:.2f}")
                print(f"  Zone: {trade['zone']} | PnL: {trade['pnl_pct']:.2f}% | Reason: {trade['exit_reason']}")
                print()
