# Strategy Optimization Implementation Prompt
## For AI Agent to Implement Pivot Zone Strategy with AI Enhancement

**Date:** November 10, 2025  
**Goal:** Achieve 60%+ win rate with profitable, consistent trading strategy  
**Current Win Rate:** 37% (needs improvement)  
**Timeline:** 2-3 weeks implementation

---

## 🎯 OBJECTIVE

Implement a new trading strategy that combines:
1. **Pivot Point Zones** (support/resistance based entries)
2. **Volume Confirmation** (validate moves with liquidity)
3. **Trend Filters** (trade with momentum, not against it)
4. **AI Sentiment** (avoid trades against market mood)
5. **Advanced Risk Management** (dynamic stops, take-profits, trailing stops)

**Target Performance:**
- Win rate: 60-70%
- Monthly return: 15-30%
- Max drawdown: <8%
- Sharpe ratio: >1.2
- Trades/month: 20-40 (quality over quantity)

---

## 📋 BACKGROUND

### Current Situation

**What Works:**
- Database: 3,454 Binance candles (89 days of BTC data) ✅
- Binance API: Keys configured, ready to use ✅
- Sentiment: News + Reddit + Ollama AI working ✅
- Infrastructure: Dashboard, API, monitoring all operational ✅

**What Doesn't Work:**
- Strategy: Simple MA crossover (37% win rate) ❌
- Over-trading: 486 trades in 89 days (5.5/day) ❌
- No sentiment integration in live trading ❌
- No advanced risk management ❌
- Using mock data instead of real Binance data ❌

### TradingView Indicator Analysis

I've analyzed the "True Algo Alerts" TradingView indicator provided. Key insights:

**Concept:** Pivot point zones (support/resistance)
- Daily pivot = open price
- Range calculated from previous day's high/low
- 6 resistance zones (R0, R1, R2, R3, R5, R6)
- 6 support zones (S0, S1, S2, S3, S5, S6)

**Signals:**
- **BUY:** Price touches zone and closes ABOVE it
- **SELL:** Price touches zone and closes BELOW it

**Why this works:**
- Support/resistance levels are self-fulfilling prophecies
- Zone bounces are more reliable than indicator crossovers
- Multiple entry points across different levels
- Clear risk/reward at each zone

**Adaptations needed for crypto:**
- Remove session filters (crypto is 24/7)
- Add volume confirmation
- Add trend filters
- Make zones dynamic (ATR-based multipliers)
- Overlay AI sentiment

---

## 🏗️ IMPLEMENTATION PLAN

### PHASE 1: Build PivotZoneStrategy (Core)

Create file: `src/strategies/pivot_zone_strategy.py`

**Requirements:**

1. **Calculate Daily Pivot Zones**
```python
class PivotZoneStrategy:
    """
    Support/Resistance zone-based trading strategy
    Inspired by TradingView's pivot point strategies
    """
    
    def __init__(self):
        self.name = "Pivot Zone Strategy"
        self.indicators = TechnicalIndicators()
        
        # Zone multipliers (can optimize these)
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
    
    def calculate_pivot_zones(self, data: pd.DataFrame) -> Dict:
        """
        Calculate daily pivot zones based on opening range
        
        Returns dict with keys: pp, r0-r6, s0-s6
        Each value is a pandas Series indexed by timestamp
        """
        # Daily aggregation
        daily = data.resample('1D', on='timestamp')
        
        # Pivot point = daily open
        pp = daily['open'].first()
        
        # Range = max of:
        # - Previous day high - low
        # - Previous day high - close(2 days ago)
        # - Previous day low - close(2 days ago)
        # - High - current open
        # - Low - current open
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
            zones[key] = zones[key].reindex(data.index, method='ffill')
        
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
        
        # Use MA50 vs MA200 for trend
        ma50 = data['close'].iloc[i-50:i].mean()
        ma200 = data['close'].iloc[i-200:i].mean() if i >= 200 else ma50
        
        if ma50 > ma200 * 1.02:  # 2% buffer to avoid choppy signals
            return 'BULLISH'
        elif ma50 < ma200 * 0.98:
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
        zones = self.calculate_pivot_zones(data)
        
        signals = pd.DataFrame(index=data.index)
        signals['signal'] = 0.0
        signals['zone_name'] = ''
        signals['signal_strength'] = 0.0
        
        # Zone pairs to check (name, bottom, top)
        zone_pairs = [
            ('R5/R6', zones['r5'], zones['r6']),
            ('R2/R3', zones['r2'], zones['r3']),
            ('R0/R1', zones['r0'], zones['r1']),
            ('S0/S1', zones['s1'], zones['s0']),  # Note: s1 < s0
            ('S2/S3', zones['s3'], zones['s2']),
            ('S5/S6', zones['s6'], zones['s5']),
        ]
        
        for i in range(max(self.ma_trend_period, 200), len(data)):
            candle = data.iloc[i]
            
            # Get trend
            trend = self.check_trend_direction(data, i)
            
            # Check volume
            volume_ok = self.check_volume_confirmation(data, i)
            
            # Check each zone
            for zone_name, zone_bottom, zone_top in zone_pairs:
                bottom_val = zone_bottom.iloc[i]
                top_val = zone_top.iloc[i]
                
                # BUY signal: Touched zone and closed ABOVE
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
                elif self.check_zone_touch_and_close(candle, bottom_val, top_val, 'BELOW'):
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
```

2. **Add Backtesting Method**
```python
    def backtest(self, data: pd.DataFrame, initial_capital: float = 10000):
        """
        Backtest the pivot zone strategy
        
        Returns dict with performance metrics
        """
        signals_df = self.generate_signals(data)
        
        cash = initial_capital
        position = 0
        entry_price = 0
        portfolio_values = []
        trades = []
        
        # Risk management
        stop_loss_pct = 0.10  # 10% stop loss (will make dynamic later)
        max_position_pct = 0.30  # 30% max position
        
        for i in range(len(data)):
            timestamp = data.index[i]
            current_price = data['close'].iloc[i]
            signal = signals_df['signal'].iloc[i]
            signal_strength = signals_df['signal_strength'].iloc[i]
            
            # Portfolio value
            portfolio_value = cash + (position * current_price)
            portfolio_values.append(portfolio_value)
            
            # Stop loss check
            if position > 0 and entry_price > 0:
                if current_price <= entry_price * (1 - stop_loss_pct):
                    # Stop loss triggered
                    proceeds = position * current_price
                    pnl = proceeds - (position * entry_price)
                    cash += proceeds
                    
                    trades.append({
                        'type': 'STOP_LOSS',
                        'entry_price': entry_price,
                        'exit_price': current_price,
                        'shares': position,
                        'pnl': pnl,
                        'pnl_pct': (current_price / entry_price - 1) * 100,
                        'timestamp': timestamp
                    })
                    
                    position = 0
                    entry_price = 0
            
            # Buy signal
            if signal > 0 and position == 0:
                # Position size based on signal strength
                position_size = max_position_pct * signal_strength
                investment = portfolio_value * position_size
                
                if cash >= investment:
                    position = investment / current_price
                    cash -= investment
                    entry_price = current_price
                    
                    trades.append({
                        'type': 'BUY',
                        'entry_price': current_price,
                        'shares': position,
                        'investment': investment,
                        'signal_strength': signal_strength,
                        'zone': signals_df['zone_name'].iloc[i],
                        'timestamp': timestamp
                    })
            
            # Sell signal
            elif signal < 0 and position > 0:
                proceeds = position * current_price
                pnl = proceeds - (position * entry_price)
                cash += proceeds
                
                trades.append({
                    'type': 'SELL',
                    'entry_price': entry_price,
                    'exit_price': current_price,
                    'shares': position,
                    'pnl': pnl,
                    'pnl_pct': (current_price / entry_price - 1) * 100,
                    'zone': signals_df['zone_name'].iloc[i],
                    'timestamp': timestamp
                })
                
                position = 0
                entry_price = 0
        
        # Close any open position
        if position > 0:
            final_price = data['close'].iloc[-1]
            proceeds = position * final_price
            pnl = proceeds - (position * entry_price)
            cash += proceeds
            
            trades.append({
                'type': 'SELL',
                'entry_price': entry_price,
                'exit_price': final_price,
                'shares': position,
                'pnl': pnl,
                'pnl_pct': (final_price / entry_price - 1) * 100,
                'timestamp': data.index[-1]
            })
        
        # Calculate metrics
        final_value = cash
        total_return = (final_value / initial_capital - 1) * 100
        
        # Win rate
        completed_trades = [t for t in trades if 'pnl' in t]
        winning_trades = [t for t in completed_trades if t['pnl'] > 0]
        win_rate = len(winning_trades) / len(completed_trades) if completed_trades else 0
        
        # Average win/loss
        avg_win = np.mean([t['pnl_pct'] for t in winning_trades]) if winning_trades else 0
        losing_trades = [t for t in completed_trades if t['pnl'] <= 0]
        avg_loss = np.mean([t['pnl_pct'] for t in losing_trades]) if losing_trades else 0
        
        # Sharpe ratio
        portfolio_values = np.array(portfolio_values)
        returns = np.diff(portfolio_values) / portfolio_values[:-1]
        sharpe = (np.mean(returns) / np.std(returns)) * np.sqrt(365 * 24) if len(returns) > 0 and np.std(returns) > 0 else 0
        
        # Max drawdown
        running_max = np.maximum.accumulate(portfolio_values)
        drawdowns = (portfolio_values - running_max) / running_max
        max_drawdown = np.min(drawdowns) if len(drawdowns) > 0 else 0
        
        return {
            'final_value': final_value,
            'total_return': total_return,
            'win_rate': win_rate,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'num_trades': len(trades),
            'num_completed': len(completed_trades),
            'sharpe_ratio': sharpe,
            'max_drawdown': max_drawdown,
            'trades': trades,
            'portfolio_values': portfolio_values
        }
```

### PHASE 2: Add AI Sentiment Layer

Create file: `src/strategies/ai_pivot_strategy.py`

**Requirements:**

1. **Extend PivotZoneStrategy with sentiment filtering**
```python
from strategies.pivot_zone_strategy import PivotZoneStrategy
from ai.data_collectors import news_collector, reddit_collector
from ai.sentiment_analyzer import sentiment_analyzer
from datetime import datetime

class AIPivotStrategy(PivotZoneStrategy):
    """
    Pivot Zone Strategy enhanced with AI sentiment analysis
    """
    
    def __init__(self):
        super().__init__()
        self.name = "AI-Enhanced Pivot Strategy"
        self.sentiment_weight = 0.3  # 30% weight on sentiment
        self.sentiment_cache = {}
        self.sentiment_ttl = 3600  # 1 hour cache
        self.sentiment_threshold = 0.5  # Filter signals if sentiment opposes
    
    def get_sentiment(self, symbol: str) -> float:
        """
        Get sentiment score for symbol (-1.0 to +1.0)
        Uses cached value if available and fresh
        """
        # Check cache
        if symbol in self.sentiment_cache:
            score, timestamp = self.sentiment_cache[symbol]
            age = (datetime.now() - timestamp).total_seconds()
            if age < self.sentiment_ttl:
                return score
        
        # Collect fresh sentiment data
        try:
            news = news_collector.collect_headlines(symbol, hours=24, max_results=10)
            reddit = reddit_collector.collect_posts(symbol, hours=24, max_results=10)
            
            # Analyze with Ollama
            sentiment_result = sentiment_analyzer.get_market_sentiment(
                symbol=symbol,
                news_headlines=news,
                reddit_posts=reddit
            )
            
            # Adjust by confidence
            score = sentiment_result.sentiment * sentiment_result.confidence
            
            # Cache
            self.sentiment_cache[symbol] = (score, datetime.now())
            
            return score
        
        except Exception as e:
            logger.error(f"Error getting sentiment for {symbol}: {e}")
            return 0.0  # Neutral if error
    
    def filter_signal_by_sentiment(self, signal: float, sentiment: float, signal_strength: float) -> tuple:
        """
        Filter and adjust signal based on sentiment
        
        Returns: (filtered_signal, adjusted_strength)
        """
        # Don't buy if sentiment very negative
        if signal > 0 and sentiment < -self.sentiment_threshold:
            logger.info(f"Filtered BUY signal - negative sentiment: {sentiment:.2f}")
            return 0.0, 0.0
        
        # Don't sell if sentiment very positive
        if signal < 0 and sentiment > self.sentiment_threshold:
            logger.info(f"Filtered SELL signal - positive sentiment: {sentiment:.2f}")
            return 0.0, 0.0
        
        # Adjust signal strength based on sentiment alignment
        if signal > 0:  # Buy signal
            # Increase strength if sentiment positive
            adjustment = max(0, sentiment) * self.sentiment_weight
            adjusted_strength = min(signal_strength + adjustment, 1.0)
        else:  # Sell signal
            # Increase strength if sentiment negative
            adjustment = max(0, -sentiment) * self.sentiment_weight
            adjusted_strength = min(signal_strength + adjustment, 1.0)
        
        return signal, adjusted_strength
    
    def generate_signals(self, data: pd.DataFrame, symbol: str = 'BTC') -> pd.DataFrame:
        """
        Generate signals with AI sentiment filtering
        """
        # Get base pivot zone signals
        signals_df = super().generate_signals(data)
        
        # Get sentiment
        sentiment = self.get_sentiment(symbol)
        logger.info(f"Current sentiment for {symbol}: {sentiment:.2f}")
        
        # Filter and adjust each signal
        for i in range(len(signals_df)):
            if signals_df['signal'].iloc[i] != 0:
                original_signal = signals_df['signal'].iloc[i]
                original_strength = signals_df['signal_strength'].iloc[i]
                
                filtered_signal, adjusted_strength = self.filter_signal_by_sentiment(
                    original_signal,
                    sentiment,
                    original_strength
                )
                
                signals_df.loc[signals_df.index[i], 'signal'] = filtered_signal
                signals_df.loc[signals_df.index[i], 'signal_strength'] = adjusted_strength
                signals_df.loc[signals_df.index[i], 'sentiment'] = sentiment
        
        return signals_df
```

### PHASE 3: Advanced Risk Management

Add to `pivot_zone_strategy.py`:

```python
    def calculate_dynamic_stop_loss(self, data: pd.DataFrame, entry_price: float, i: int) -> float:
        """
        Calculate ATR-based dynamic stop loss
        """
        atr = self.indicators.atr(data, period=14).iloc[i]
        stop_distance = 2 * atr  # 2x ATR
        return entry_price - stop_distance
    
    def calculate_take_profit(self, entry_price: float, stop_loss: float) -> float:
        """
        Calculate take profit at 2:1 risk/reward ratio
        """
        risk = entry_price - stop_loss
        reward = risk * 2
        return entry_price + reward
    
    def calculate_trailing_stop(self, entry_price: float, current_price: float, 
                                highest_price: float, trail_pct: float = 0.05) -> float:
        """
        Calculate trailing stop loss (locks in profits)
        """
        if current_price > entry_price:
            # In profit - trail from highest price
            trailing_stop = highest_price * (1 - trail_pct)
            return max(trailing_stop, entry_price)  # Never below breakeven
        return None
```

### PHASE 4: Testing & Validation

Create file: `test_pivot_strategy.py`

```python
#!/usr/bin/env python3
"""Test the new Pivot Zone Strategy"""
import sys
sys.path.insert(0, 'src')

from strategies.pivot_zone_strategy import PivotZoneStrategy
from strategies.ai_pivot_strategy import AIPivotStrategy
from data.database import get_db
from data.models import MarketData
import pandas as pd

def test_pivot_strategy():
    """Test pivot zone strategy on historical data"""
    
    print("🧪 TESTING PIVOT ZONE STRATEGY")
    print("=" * 70)
    
    # Load data
    db = next(get_db())
    data = db.query(MarketData).filter(
        MarketData.symbol == 'BTCUSDT'
    ).order_by(MarketData.timestamp.asc()).all()
    db.close()
    
    # Convert to DataFrame
    df = pd.DataFrame([{
        'timestamp': d.timestamp,
        'open': float(d.open_price),
        'high': float(d.high_price),
        'low': float(d.low_price),
        'close': float(d.close_price),
        'volume': float(d.volume)
    } for d in data])
    df.set_index('timestamp', inplace=True)
    
    print(f"📊 Dataset: {len(df)} candles")
    print(f"📅 Period: {df.index[0].date()} to {df.index[-1].date()}")
    print()
    
    # Test base pivot strategy
    print("🔷 Testing Base Pivot Zone Strategy...")
    pivot_strategy = PivotZoneStrategy()
    pivot_results = pivot_strategy.backtest(df)
    
    print(f"  Final Value:    ${pivot_results['final_value']:,.2f}")
    print(f"  Total Return:   {pivot_results['total_return']:.2f}%")
    print(f"  Win Rate:       {pivot_results['win_rate']:.2%}")
    print(f"  Trades:         {pivot_results['num_completed']}")
    print(f"  Avg Win:        {pivot_results['avg_win']:.2f}%")
    print(f"  Avg Loss:       {pivot_results['avg_loss']:.2f}%")
    print(f"  Sharpe Ratio:   {pivot_results['sharpe_ratio']:.3f}")
    print(f"  Max Drawdown:   {pivot_results['max_drawdown']:.2%}")
    print()
    
    # Test AI-enhanced pivot strategy
    print("🤖 Testing AI-Enhanced Pivot Zone Strategy...")
    ai_strategy = AIPivotStrategy()
    ai_results = ai_strategy.backtest(df)
    
    print(f"  Final Value:    ${ai_results['final_value']:,.2f}")
    print(f"  Total Return:   {ai_results['total_return']:.2f}%")
    print(f"  Win Rate:       {ai_results['win_rate']:.2%}")
    print(f"  Trades:         {ai_results['num_completed']}")
    print(f"  Avg Win:        {ai_results['avg_win']:.2f}%")
    print(f"  Avg Loss:       {ai_results['avg_loss']:.2f}%")
    print(f"  Sharpe Ratio:   {ai_results['sharpe_ratio']:.3f}")
    print(f"  Max Drawdown:   {ai_results['max_drawdown']:.2%}")
    print()
    
    # Comparison
    print("📊 STRATEGY COMPARISON")
    print("-" * 70)
    print(f"{'Metric':<20} {'Base Pivot':<15} {'AI-Enhanced':<15} {'Improvement':<15}")
    print("-" * 70)
    
    metrics = [
        ('Return', f"{pivot_results['total_return']:.2f}%", f"{ai_results['total_return']:.2f}%", 
         f"{ai_results['total_return'] - pivot_results['total_return']:+.2f}%"),
        ('Win Rate', f"{pivot_results['win_rate']:.2%}", f"{ai_results['win_rate']:.2%}",
         f"{(ai_results['win_rate'] - pivot_results['win_rate']) * 100:+.1f}%"),
        ('Trades', str(pivot_results['num_completed']), str(ai_results['num_completed']),
         str(ai_results['num_completed'] - pivot_results['num_completed'])),
        ('Sharpe', f"{pivot_results['sharpe_ratio']:.3f}", f"{ai_results['sharpe_ratio']:.3f}",
         f"{ai_results['sharpe_ratio'] - pivot_results['sharpe_ratio']:+.3f}"),
    ]
    
    for metric_name, base_val, ai_val, improvement in metrics:
        print(f"{metric_name:<20} {base_val:<15} {ai_val:<15} {improvement:<15}")
    
    print()
    
    # Success criteria
    print("✅ SUCCESS CRITERIA CHECK")
    print("-" * 70)
    criteria = [
        ("Win Rate ≥ 60%", ai_results['win_rate'] >= 0.60),
        ("Sharpe ≥ 1.0", ai_results['sharpe_ratio'] >= 1.0),
        ("Max DD ≤ 10%", ai_results['max_drawdown'] >= -0.10),
        ("Profitable", ai_results['total_return'] > 0),
    ]
    
    for criterion, passed in criteria:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {criterion:<30} {status}")
    
    print()
    print("=" * 70)
    
    if all(p for _, p in criteria):
        print("🎉 ALL CRITERIA MET - STRATEGY READY FOR PAPER TRADING!")
    else:
        print("⚠️  SOME CRITERIA NOT MET - NEEDS OPTIMIZATION")
    
    return pivot_results, ai_results

if __name__ == "__main__":
    test_pivot_strategy()
```

---

## 🎯 IMPLEMENTATION CHECKLIST

### Week 1: Core Strategy
- [ ] Create `src/strategies/pivot_zone_strategy.py`
- [ ] Implement `calculate_pivot_zones()`
- [ ] Implement `check_zone_touch_and_close()`
- [ ] Implement `check_volume_confirmation()`
- [ ] Implement `check_trend_direction()`
- [ ] Implement `generate_signals()`
- [ ] Implement `backtest()`
- [ ] Test on historical data
- [ ] Verify win rate ≥ 50%

### Week 2: AI Enhancement
- [ ] Create `src/strategies/ai_pivot_strategy.py`
- [ ] Implement `get_sentiment()`
- [ ] Implement `filter_signal_by_sentiment()`
- [ ] Override `generate_signals()` with sentiment
- [ ] Test sentiment collection
- [ ] Backtest AI strategy
- [ ] Compare vs base pivot strategy
- [ ] Verify win rate ≥ 60%

### Week 3: Risk Management
- [ ] Implement `calculate_dynamic_stop_loss()` (ATR-based)
- [ ] Implement `calculate_take_profit()` (2:1 R/R)
- [ ] Implement `calculate_trailing_stop()`
- [ ] Add partial profit taking
- [ ] Add daily loss limits
- [ ] Update backtest with new risk management
- [ ] Verify max drawdown ≤ 8%

### Week 4: Integration & Testing
- [ ] Create `test_pivot_strategy.py`
- [ ] Run full backtest comparison
- [ ] Verify all success criteria
- [ ] Update `live_engine.py` to use new strategy
- [ ] Enable live Binance data feed
- [ ] Test in paper trading mode
- [ ] Monitor for 1 week

---

## 📊 EXPECTED RESULTS

### Minimum Acceptable:
- Win rate: ≥ 60%
- Monthly return: ≥ 15%
- Max drawdown: ≤ 8%
- Sharpe ratio: ≥ 1.0
- Trades/month: 20-40

### Ideal Target:
- Win rate: ≥ 70%
- Monthly return: ≥ 25%
- Max drawdown: ≤ 5%
- Sharpe ratio: ≥ 1.5
- Consistent profitability

---

## 🔧 FILES TO CREATE/MODIFY

### New Files:
1. `src/strategies/pivot_zone_strategy.py` (main implementation)
2. `src/strategies/ai_pivot_strategy.py` (AI enhancement)
3. `test_pivot_strategy.py` (testing script)

### Modify Files:
1. `src/trading/live_engine.py` (line 158-159 - switch to new strategy)
2. `src/api/api_backend.py` (line 75 - enable real Binance data)

---

## ⚠️ IMPORTANT NOTES

1. **Start Simple:** Implement base pivot strategy first, validate it works, then add AI
2. **Test Thoroughly:** Each phase should have win rate ≥ 50% before moving to next
3. **Use Clean Data:** Verify data quality before backtesting
4. **Paper Trade:** Don't use real money until 2+ months of profitable paper trading
5. **Monitor Closely:** Check every trade for logic errors
6. **Transaction Fees:** Include 0.1% Binance fees in backtest
7. **Realistic Expectations:** 60-70% win rate is excellent, don't aim for 100%

---

## 🚀 NEXT ACTIONS

1. **Implement** `PivotZoneStrategy` class
2. **Backtest** on clean historical data
3. **Validate** win rate ≥ 50%
4. **Add** AI sentiment layer
5. **Test** AI-enhanced version
6. **Validate** win rate ≥ 60%
7. **Deploy** to paper trading
8. **Monitor** for 60+ days

---

**Goal:** Achieve 60%+ win rate with profitable, consistent trading strategy  
**Timeline:** 3-4 weeks implementation + 8 weeks validation = Ready in 3 months  
**Risk:** Controlled (paper trading only until proven)

---
