# Trading Strategy Optimization Implementation Prompt

**Date:** November 7, 2025  
**Project:** AI Trading Bot - Strategy Optimization  
**Goal:** Improve win rate from 37.5% to 65%+ and achieve +25% monthly returns  
**Timeline:** 4 weeks implementation

---

## 🎯 MISSION

You are tasked with optimizing a cryptocurrency trading bot's strategy. The current strategy is **losing money** (-8.97% return, 37.5% win rate) and needs significant improvements to become profitable.

Your goal is to implement the optimization plan detailed in `docs/STRATEGY_OPTIMIZATION_PLAN.md` to achieve:
- **Win Rate:** 65%+ (from 37.5%)
- **Monthly Return:** +25% (from -8.97%)
- **Sharpe Ratio:** 1.3+ (from -0.012)
- **Max Drawdown:** <5% (from -13.36%)

---

## 📁 PROJECT STRUCTURE

```
ai-trading-bot/
├── src/
│   ├── strategies/
│   │   ├── phase2_final_test.py          ← CURRENT STRATEGY (needs optimization)
│   │   ├── ai_enhanced_strategy.py       ← AI strategy (available but not active)
│   │   ├── technical_indicators.py       ← Indicator calculations
│   │   └── trading_strategies.py         ← Base strategy classes
│   ├── trading/
│   │   └── live_engine.py                ← Trading engine (line 157: strategy selection)
│   ├── data/
│   │   ├── database.py                   ← Database access
│   │   └── models.py                     ← Data models
│   └── ai/
│       ├── sentiment_analyzer.py         ← Sentiment analysis (Ollama)
│       └── data_collectors.py            ← News/Reddit data collection
├── docs/
│   ├── STRATEGY_OPTIMIZATION_PLAN.md     ← MASTER PLAN (READ THIS FIRST!)
│   ├── DATA_FLOW_AND_SENTIMENT_ANALYSIS.md
│   └── SENTIMENT_DATA_SOURCES.md
└── tests/
```

---

## 📖 REQUIRED READING (CRITICAL!)

Before starting, read these documents in order:

1. **`docs/STRATEGY_OPTIMIZATION_PLAN.md`** ← PRIMARY REFERENCE
   - Complete 60-page optimization plan
   - Root cause analysis
   - All code changes detailed
   - Expected results

2. **Current Strategy Description** (this section below)

3. **Data Flow Documentation** (`docs/DATA_FLOW_AND_SENTIMENT_ANALYSIS.md`)

---

## 📊 CURRENT STRATEGY OVERVIEW

### Strategy: OptimizedPhase2Strategy

**File:** `src/strategies/phase2_final_test.py`

**Indicators:**
- MA8 (8-period Simple Moving Average)
- MA21 (21-period Simple Moving Average)
- RSI (14-period Relative Strength Index)

**Entry Logic:**
```python
# BUY Signal
if ma_fast crosses above ma_slow AND rsi < 65:
    signal = 1.0  # Strong buy

# Alternative BUY
if rsi < 30 AND ma_fast > ma_slow:
    signal = 0.5  # Weak buy (oversold bounce)

# SELL Signal
if ma_fast crosses below ma_slow OR rsi > 70:
    signal = -1.0  # Sell
```

**Risk Management:**
- Stop Loss: 10% fixed
- Position Size: 30% max per trade
- No take-profit targets

**Current Performance (720 candles, 10 days):**
- Return: -8.97%
- Win Rate: 37.5% (24 wins, 40 losses)
- Sharpe: -0.012
- Max Drawdown: -13.36%
- Total Trades: 64

**Problems Identified:**
1. False breakouts (40% of losses) - MA crossovers are lagging
2. Whipsaws in sideways markets (30% of losses) - No trend filter
3. Tight stops (20% of losses) - 10% too tight for crypto
4. No exit strategy (10% of losses) - No take-profit targets

---

## 🚀 IMPLEMENTATION PLAN (4 Weeks)

### WEEK 1: Fix Entry Signals

**Objective:** Reduce false signals by 50%, increase win rate to 52%

**Tasks:**

1. **Add Higher Timeframe Trend Filter**
   ```python
   # Add to generate_signals() method
   ma_50 = close.rolling(window=50).mean()
   ma_200 = close.rolling(window=200).mean()
   
   # Only buy in uptrend, only sell in downtrend
   higher_tf_bullish = ma_50.iloc[i] > ma_200.iloc[i]
   ```

2. **Add Volume Confirmation**
   ```python
   avg_volume = data['volume'].rolling(20).mean()
   volume_confirmed = data['volume'].iloc[i] > avg_volume.iloc[i] * 1.2
   ```

3. **Add MACD Confirmation**
   ```python
   macd, signal_line, _ = self.indicators.macd(close)
   macd_bullish = macd.iloc[i] > signal_line.iloc[i]
   ```

4. **Add ADX Trend Strength Filter**
   ```python
   # Only trade when ADX > 25 (trending market)
   adx = self.indicators.adx(data, period=14)
   is_trending = adx.iloc[i] > 25
   ```

**Deliverable:** New `generate_signals_v2()` method with all confirmations

**Files to Modify:**
- `src/strategies/phase2_final_test.py` or create `src/strategies/optimized_strategy_v2.py`

---

### WEEK 2: Improve Exit Strategy

**Objective:** Increase profit per trade by 30%, win rate to 57%

**Tasks:**

1. **Dynamic ATR-Based Stop Loss**
   ```python
   def calculate_dynamic_stop(self, data, entry_price, lookback=14):
       atr = self.indicators.atr(data, period=lookback)
       stop_distance = 2 * atr.iloc[-1]  # 2x ATR
       return entry_price - stop_distance
   ```

2. **Take Profit Targets (1:2 Risk/Reward)**
   ```python
   def calculate_take_profit(self, entry_price, stop_price):
       risk = entry_price - stop_price
       reward = risk * 2
       return entry_price + reward
   ```

3. **Trailing Stop Loss**
   ```python
   def update_trailing_stop(self, current_price, entry_price, 
                           highest_price, trail_pct=0.05):
       if current_price > entry_price:
           return highest_price * (1 - trail_pct)
       return None
   ```

4. **Partial Profit Taking**
   ```python
   # Take 50% profit at target, let rest run
   if current_price >= take_profit_target:
       sell_half()
       move_stop_to_breakeven()
   ```

**Deliverable:** New `ExitManager` class

**Files to Create:**
- `src/strategies/exit_manager.py`

---

### WEEK 3: Integrate AI & Sentiment

**Objective:** Improve timing, avoid bad trades, win rate to 63%

**Tasks:**

1. **Enable AIEnhancedStrategy**
   ```python
   # File: src/trading/live_engine.py (line 157)
   # Change from:
   self.strategy = OptimizedPhase2Strategy()
   
   # To:
   from strategies.ai_enhanced_strategy import AIEnhancedStrategy
   self.strategy = AIEnhancedStrategy(
       technical_weight=0.5,
       lstm_weight=0.2,
       sentiment_weight=0.3
   )
   ```

2. **Add Sentiment Filter**
   ```python
   def sentiment_filter(self, symbol, signal):
       sentiment = self.get_sentiment_signal(symbol)
       
       # Cancel buy if sentiment very negative
       if signal > 0 and sentiment < -0.6:
           return 0
       
       # Cancel sell if sentiment very positive
       if signal < 0 and sentiment > 0.6:
           return 0
       
       return signal
   ```

3. **News Event Detection**
   ```python
   def check_major_news(self, symbol):
       news = news_collector.collect_headlines(symbol, hours=1)
       major_keywords = ['etf', 'sec', 'regulation', 'hack', 'ban']
       
       for headline in news:
           if any(kw in headline.lower() for kw in major_keywords):
               return True
       return False
   ```

**Deliverable:** Fully integrated AI strategy

**Files to Modify:**
- `src/trading/live_engine.py`
- `src/strategies/ai_enhanced_strategy.py`

---

### WEEK 4: Risk Management Overhaul

**Objective:** Preserve capital, reduce drawdown, win rate to 65%

**Tasks:**

1. **Dynamic Position Sizing**
   ```python
   def calculate_position_size(self, win_streak, base_size=0.3):
       if win_streak <= -3:
           return base_size * 0.5  # Reduce after losses
       elif win_streak >= 3:
           return min(base_size * 1.5, 0.4)  # Increase after wins
       return base_size
   ```

2. **Daily Loss Limit**
   ```python
   def check_daily_loss_limit(self, daily_pnl, limit_pct=0.03):
       if daily_pnl < -limit_pct:
           return False  # Stop trading for the day
       return True
   ```

3. **Correlation Filter**
   ```python
   # Don't hold correlated assets simultaneously
   # If BTC and ETH correlation > 0.9, close one
   ```

**Deliverable:** New `RiskManager` class

**Files to Create:**
- `src/strategies/risk_manager.py`

---

## 🎯 QUICK WINS (Start with These!)

Before implementing the full 4-week plan, apply these 3 changes TODAY for immediate +20% win rate improvement:

### Quick Win #1: Widen Stop Loss (5 minutes)

**File:** `src/strategies/phase2_final_test.py` (line 77)

```python
# Change from:
stop_loss_pct = 0.10  # 10%

# To:
stop_loss_pct = 0.15  # 15% (better for crypto volatility)
```

**Expected Impact:** +5% win rate immediately

---

### Quick Win #2: Add Higher Timeframe Filter (10 minutes)

**File:** `src/strategies/phase2_final_test.py`

```python
# After line 36 (in generate_signals method), add:
ma_50 = close.rolling(window=50).mean()
ma_200 = close.rolling(window=200).mean()

# In signal loop (line 54), change to:
if ma_crossover_up and not rsi_overbought and ma_50.iloc[i] > ma_200.iloc[i]:
    signals.iloc[i] = 1.0  # Only buy in uptrend
```

**Expected Impact:** +8% win rate immediately

---

### Quick Win #3: Reduce Trade Frequency (5 minutes)

**File:** `src/strategies/phase2_final_test.py` (in generate_signals method)

```python
# Add at start of method:
last_trade_index = -100  # Track last trade

# In loop (line 54), add cooldown check:
if ma_crossover_up and not rsi_overbought and (i - last_trade_index) > 10:
    signals.iloc[i] = 1.0
    last_trade_index = i
```

**Expected Impact:** -30% trades, +10% win rate (quality over quantity)

---

## 📊 TESTING & VALIDATION

### Step 1: Backtest Each Change

After each modification:

```bash
cd /Users/henrybarefoot/ai-learning/ai-trading-bot
python3 src/strategies/phase2_final_test.py
```

Compare results:
- Total Return (should improve)
- Win Rate (target 65%+)
- Sharpe Ratio (target 1.0+)
- Max Drawdown (target <8%)

### Step 2: Collect More Historical Data

**CRITICAL:** Current data is only 10 days (720 candles). Need 90+ days for reliable testing.

```python
# Use CCXT to fetch historical data
import ccxt

exchange = ccxt.binance()
symbol = 'BTC/USDT'
timeframe = '1h'
since = exchange.parse8601('2024-08-01T00:00:00Z')

# Fetch 90 days of hourly data
ohlcv = exchange.fetch_ohlcv(symbol, timeframe, since, limit=2160)

# Store in database
# (Add code to save to PostgreSQL)
```

### Step 3: Out-of-Sample Testing

- Train on 70% of data (first 60 days)
- Test on 30% of data (last 30 days)
- Verify no overfitting

### Step 4: Paper Trading Validation

Before using real money:
- Run in paper trading mode for 2+ months
- Monitor daily performance
- Verify consistent profitability

---

## 💻 CODE IMPLEMENTATION GUIDELINES

### Coding Standards

1. **Follow existing code style**
   - Use type hints
   - Add docstrings
   - Keep methods < 50 lines

2. **Test incrementally**
   - Add one feature at a time
   - Backtest after each change
   - Don't break existing functionality

3. **Document changes**
   - Comment WHY, not WHAT
   - Update docstrings
   - Log important decisions

### Example: Proper Code Structure

```python
class OptimizedStrategyV3:
    """
    Enhanced trading strategy with multiple confirmations
    
    Improvements over V2:
    - Higher timeframe trend filter
    - Volume confirmation
    - MACD momentum
    - ADX trend strength
    
    Expected Performance:
    - Win Rate: 65%+
    - Sharpe: 1.3+
    - Max DD: <5%
    """
    
    def __init__(self):
        self.name = "Optimized V3"
        self.indicators = TechnicalIndicators()
        
        # MA parameters
        self.fast_ma = 8
        self.slow_ma = 21
        self.trend_ma_1 = 50
        self.trend_ma_2 = 200
        
        # RSI parameters
        self.rsi_oversold = 35
        self.rsi_overbought = 65
        
        # Volume parameters
        self.volume_multiplier = 1.2
        
        # Trend strength
        self.min_adx = 25
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Generate trading signals with multiple confirmations
        
        Entry Requirements:
        1. MA crossover (8 crosses 21)
        2. Higher TF trend confirmation (50 > 200)
        3. Volume above average (1.2x)
        4. MACD alignment
        5. Market is trending (ADX > 25)
        6. RSI not extreme
        
        Returns:
            Series of signals: 1.0 (strong buy), -1.0 (sell), 0.0 (hold)
        """
        # Implementation here...
```

---

## 🔧 TECHNICAL REQUIREMENTS

### Environment

```bash
# Python version
Python 3.8+

# Required packages (already installed)
pandas
numpy
ccxt
sqlalchemy
psycopg2-binary

# Database
PostgreSQL 14+

# AI Components
Ollama (for sentiment analysis)
```

### Database Access

```python
from data.database import get_db
from data.models import MarketData

# Get database session
db = next(get_db())

# Query market data
data = db.query(MarketData).filter(
    MarketData.symbol == 'BTCUSDT'
).order_by(MarketData.timestamp.desc()).limit(200).all()
```

### Indicator Library

All technical indicators available in `src/strategies/technical_indicators.py`:

```python
from strategies.technical_indicators import TechnicalIndicators

indicators = TechnicalIndicators()

# Available methods:
rsi = indicators.rsi(close, window=14)
macd, signal, histogram = indicators.macd(close)
atr = indicators.atr(data, period=14)
adx = indicators.adx(data, period=14)
bollinger = indicators.bollinger_bands(close, window=20)
```

---

## ⚠️ CRITICAL WARNINGS

### DO NOT:

1. ❌ **Over-optimize on limited data**
   - Only have 10 days currently
   - Need 90+ days minimum
   - Risk: Strategy only works on this specific data

2. ❌ **Ignore transaction costs**
   - Binance fees: 0.1% per trade
   - Slippage: ~0.05%
   - Must subtract from returns

3. ❌ **Chase 100% win rate**
   - Impossible in trading
   - 65-70% is excellent
   - Focus on profit factor

4. ❌ **Use real money before validation**
   - Stay in paper trading for 2+ months
   - Prove consistent profitability
   - Start tiny ($100-500) when going live

### DO:

1. ✅ **Test each change independently**
   - Add one feature at a time
   - Measure impact
   - Keep what works, discard what doesn't

2. ✅ **Collect more data**
   - Fetch 90+ days historical
   - Test across different market conditions
   - Bull, bear, sideways markets

3. ✅ **Document everything**
   - Track all changes
   - Record results
   - Note what worked and why

4. ✅ **Focus on risk management**
   - Protect capital first
   - Profits second
   - Survive to trade another day

---

## 📈 SUCCESS METRICS

### Minimum Acceptable Performance:

- ✅ Win Rate: >60%
- ✅ Total Return: >15% per month
- ✅ Sharpe Ratio: >1.0
- ✅ Max Drawdown: <8%
- ✅ Profit Factor: >2.0
- ✅ Consecutive Losses: <5

### Target Performance:

- 🎯 Win Rate: 65%+
- 🎯 Total Return: 25%+ per month
- 🎯 Sharpe Ratio: 1.3+
- 🎯 Max Drawdown: <5%
- 🎯 Profit Factor: 3.0+

---

## 📝 DELIVERABLES

At the end of each week, provide:

1. **Code Changes**
   - All modified files
   - New files created
   - Git commit messages

2. **Performance Report**
   - Backtest results
   - Before/after comparison
   - Charts/graphs

3. **Documentation**
   - Changes made
   - Reasoning behind decisions
   - Known issues/limitations

4. **Next Steps**
   - What's working
   - What needs adjustment
   - Plan for next week

---

## 🎯 EXPECTED TIMELINE

```
Week 1: Entry Signal Improvements
├─ Day 1-2: Implement Quick Wins
├─ Day 3-4: Add confirmations (volume, MACD, ADX)
├─ Day 5:   Backtest and document
└─ Result:  Win rate 37.5% → 52%

Week 2: Exit Strategy
├─ Day 1-2: Dynamic stops (ATR-based)
├─ Day 3-4: Take profits & trailing stops
├─ Day 5:   Backtest and document
└─ Result:  Win rate 52% → 57%

Week 3: AI Integration
├─ Day 1-2: Enable AIEnhancedStrategy
├─ Day 3-4: Sentiment filters & news detection
├─ Day 5:   Backtest and document
└─ Result:  Win rate 57% → 63%

Week 4: Risk Management
├─ Day 1-2: Dynamic position sizing
├─ Day 3-4: Loss limits & correlation filter
├─ Day 5:   Final backtest and report
└─ Result:  Win rate 63% → 65%

TOTAL: 65% win rate, +25% monthly return, 1.3 Sharpe
```

---

## 📚 ADDITIONAL RESOURCES

### Documentation to Reference:

1. `docs/STRATEGY_OPTIMIZATION_PLAN.md` - Master plan
2. `docs/DATA_FLOW_AND_SENTIMENT_ANALYSIS.md` - Data architecture
3. `docs/SENTIMENT_DATA_SOURCES.md` - How sentiment works
4. `docs/ENABLE_LIVE_DATA_GUIDE.md` - Live data setup

### Key Files to Understand:

1. `src/strategies/phase2_final_test.py` - Current strategy
2. `src/strategies/ai_enhanced_strategy.py` - AI strategy
3. `src/strategies/technical_indicators.py` - Indicators
4. `src/trading/live_engine.py` - Trading engine
5. `src/ai/sentiment_analyzer.py` - Sentiment analysis

---

## 🚀 START HERE

### Immediate Actions (First Day):

1. **Read the master plan**
   ```bash
   cat docs/STRATEGY_OPTIMIZATION_PLAN.md
   ```

2. **Understand current strategy**
   ```bash
   python3 src/strategies/phase2_final_test.py
   ```

3. **Implement Quick Win #1** (widen stops)
   - Edit `src/strategies/phase2_final_test.py` line 77
   - Change `stop_loss_pct = 0.10` to `0.15`
   - Test and measure impact

4. **Implement Quick Win #2** (trend filter)
   - Add 50/200 MA filter
   - Test and measure impact

5. **Implement Quick Win #3** (reduce frequency)
   - Add cooldown period
   - Test and measure impact

6. **Report Results**
   - Document win rate improvement
   - Share before/after metrics
   - Proceed to Week 1 full implementation

---

## ✅ CHECKLIST

Before starting:
- [ ] Read `docs/STRATEGY_OPTIMIZATION_PLAN.md` completely
- [ ] Understand current strategy performance
- [ ] Review existing code structure
- [ ] Set up development environment
- [ ] Have database access
- [ ] Can run backtests successfully

During implementation:
- [ ] Test each change independently
- [ ] Backtest after every modification
- [ ] Document all changes
- [ ] Track performance metrics
- [ ] Don't break existing functionality

After completion:
- [ ] Final backtest on full dataset
- [ ] Performance report
- [ ] Code review
- [ ] Deploy to paper trading
- [ ] Monitor for 2+ months

---

## 📞 SUPPORT & QUESTIONS

If you encounter issues:

1. **Check existing documentation** in `docs/` folder
2. **Review code comments** in strategy files
3. **Test on small dataset** first before full backtest
4. **Verify database connection** if data issues
5. **Check Ollama** is running if sentiment fails

Common issues:
- "No data found" → Run data collection first
- "Import error" → Check Python path includes `src/`
- "Ollama error" → Verify Ollama is running (`ollama list`)
- "Database error" → Check PostgreSQL is running

---

## 🎯 FINAL NOTES

**Remember:**
- Quality over quantity (fewer, better trades)
- Risk management first, profits second
- Test rigorously before deploying
- Stay in paper trading until proven
- Start small when going live

**Goal:**
Transform a losing strategy (-8.97%, 37.5% win rate) into a winning one (65%+ win rate, +25% monthly return).

**Success Criteria:**
Not just hitting target metrics, but **consistent, reproducible performance** across different market conditions.

**Timeline:**
4 weeks to optimize, 8 weeks to validate = live trading in ~3 months

---

**Good luck! Transform this bot from losing to winning! 🚀**

---

**Generated:** November 7, 2025  
**For:** AI Trading Bot Strategy Optimization  
**By:** Strategy Analysis Agent  
**Next Agent:** Implementation Agent
