# Strategy Optimization Agent Prompt

**Objective:** Transform the AI trading bot from a functional prototype into a high-performance trading system with 65%+ win rate and consistent profitability.

---

## 🎯 YOUR MISSION

You are a quantitative trading strategy developer tasked with optimizing an AI-powered cryptocurrency trading bot. The bot is currently functional but needs significant performance improvements.

**Primary Goal:** Achieve 65%+ win rate with risk/reward ratio of 1:2 or better

**Current Performance:**
- ❌ Backtest shows impossible returns (bug to fix)
- ⚠️ Win rate unknown (needs clean testing)
- ⚠️ Risk/reward not optimized
- ❌ AI sentiment available but not used

---

## 📋 CONTEXT

### Project Structure:
```
ai-trading-bot/
├── src/
│   ├── strategies/          # Trading strategies (focus here)
│   │   ├── pivot_zone_strategy.py          # New S/R zone strategy
│   │   ├── optimized_strategy_week1_refined.py  # Current (MA-based)
│   │   ├── ai_enhanced_strategy.py         # AI+Sentiment (not active)
│   │   └── technical_indicators.py         # Indicator library
│   ├── trading/
│   │   ├── live_engine.py                  # Main trading loop
│   │   └── paper_trading_monitor.py        # Performance tracking
│   └── data/
│       └── models.py                        # Database schema
├── clean_backtest.py        # Backtesting script (has bugs)
└── docs/                    # All documentation here
```

### Available Data:
- **PostgreSQL database** with 3,460 BTC/USDT candles (89 days: Aug-Nov 2025)
- **Binance API** configured for live data
- **Price range:** $24,443 - $125,999
- **Symbols:** BTC, ETH, SOL, ADA, DOT

### Current Strategies:

1. **Week1RefinedStrategy** (Active)
   - MA8/MA21 crossover
   - RSI filter (<65)
   - Trend confirmation (MA50>MA200)
   - Volume filter (>1.2x avg)
   - Stop loss: 15%
   - No take profit

2. **PivotZoneStrategy** (Implemented, not tested)
   - Support/resistance zones (12 levels)
   - Fibonacci-based multipliers
   - Volume + trend confirmation
   - Stop loss: 8%
   - Take profit: 15%

3. **AIEnhancedStrategy** (Available, not active)
   - Combines technical (40%) + LSTM (30%) + sentiment (30%)
   - Uses Ollama AI for sentiment analysis
   - News + Reddit data sources

---

## 🔧 SPECIFIC TASKS

### Task 1: Fix Backtesting System ⚠️ CRITICAL

**Problem:** `clean_backtest.py` produces impossible results:
```
Final Value: $383,866,985,174,341,446,970...
Total Return: 3.8×10³⁷ %
```

**Your Job:**
1. Review `clean_backtest.py` line-by-line
2. Identify the position sizing / compound calculation bug
3. Fix the logic to produce realistic results
4. Add sanity checks (if return > 1000%, flag error)
5. Ensure cash and position tracking are accurate

**Expected Output:**
```python
# Realistic backtest results
Initial Capital: $10,000
Final Value: $11,500 (example)
Total Return: +15.0%
Win Rate: 65%
```

**Files to Modify:**
- `clean_backtest.py` (lines 35-107)

---

### Task 2: Run Clean Strategy Comparison

**Your Job:**
1. Clean the database (remove 7 fake trades)
2. Backtest all 3 strategies on the same historical data
3. Calculate standardized metrics for each:
   - Win rate
   - Total return
   - Average win / average loss
   - Risk/reward ratio
   - Max drawdown
   - Sharpe ratio
   - Total trades
4. Create comparison table

**Expected Output:**
```
STRATEGY COMPARISON (89 days BTC data)
═══════════════════════════════════════════════════════════
Strategy              Win Rate    Return    R:R    Max DD
─────────────────────────────────────────────────────────
Week1Refined          XX.X%       +X.X%    1:X    -X.X%
PivotZone             XX.X%       +X.X%    1:X    -X.X%
AIEnhanced            XX.X%       +X.X%    1:X    -X.X%
─────────────────────────────────────────────────────────
WINNER: [Strategy Name] ✅
```

**Files to Create:**
- `scripts/run_strategy_comparison.py`

---

### Task 3: Integrate TradingView Pivot Logic

**Context:** User provided a TradingView Pine Script indicator ("True Algo Alerts") that uses daily pivot zones for trading.

**Your Job:**
1. Review the TradingView code (provided in analysis)
2. Verify `PivotZoneStrategy` matches the TradingView logic
3. Test if it produces same signals
4. If different, adjust Python code to match
5. Optimize zone multipliers if needed

**Key Features to Preserve:**
- Daily pivot = current open
- Zone levels: R0-R6, S0-S6
- Fibonacci multipliers: 0.1, 0.23, 0.618, 0.786, 1.27, 1.5
- Entry: Touch zone + close opposite direction
- Volume confirmation: >1.2x average

**Files to Review/Modify:**
- `src/strategies/pivot_zone_strategy.py`

---

### Task 4: Optimize Risk/Reward Parameters

**Current Problem:** No defined risk/reward ratio

**Your Job:**
1. Add explicit risk/reward tracking to backtester
2. Test different stop loss / take profit combinations:
   ```
   Stop Loss Options: 3%, 5%, 8%, 10%, 15%
   Take Profit Options: 10%, 15%, 20%, 25%, 30%
   ```
3. Find optimal combination for each strategy
4. Calculate risk/reward ratio for each combo
5. Recommend best settings

**Target:** Risk/Reward ratio of 1:2 or better

**Example Analysis:**
```
RISK/REWARD OPTIMIZATION - PivotZoneStrategy
═══════════════════════════════════════════════════════════
SL%    TP%    Win Rate    Avg Win    Avg Loss    R:R    Return
───────────────────────────────────────────────────────────
5%     15%    68%         +14.2%     -4.8%      1:2.96  +18.5%  ✅ BEST
5%     10%    72%         +9.5%      -4.7%      1:2.02  +15.2%
8%     15%    64%         +14.5%     -7.6%      1:1.91  +12.8%
───────────────────────────────────────────────────────────
RECOMMENDATION: Stop Loss: 5% | Take Profit: 15%
```

**Files to Create:**
- `scripts/optimize_risk_reward.py`

---

### Task 5: Enable AI Sentiment (Optional)

**Your Job:**
1. Modify `src/trading/live_engine.py` to use `AIEnhancedStrategy`
2. Backtest AI strategy with sentiment enabled
3. Compare performance vs technical-only strategies
4. If better, keep enabled; if worse, disable

**Code Change:**
```python
# File: src/trading/live_engine.py (line 158)
# From:
from strategies.optimized_strategy_week1_refined import Week1RefinedStrategy
self.strategy = Week1RefinedStrategy()

# To:
from strategies.ai_enhanced_strategy import AIEnhancedStrategy
self.strategy = AIEnhancedStrategy()
```

**Test Questions:**
- Does sentiment improve win rate?
- Does sentiment reduce false signals?
- What's the performance difference?

---

### Task 6: Implement Winner Strategy

**Your Job:**
1. Based on Task 2 results, identify the best strategy
2. Implement optimized version with Task 4 risk/reward settings
3. Create `src/strategies/optimized_final_strategy.py`
4. Add comprehensive docstrings and comments
5. Update `live_engine.py` to use this strategy

**Requirements for Final Strategy:**
- ✅ Win rate: ≥65%
- ✅ Risk/Reward: ≥1:2
- ✅ Max drawdown: ≤8%
- ✅ Clear entry/exit logic
- ✅ Position sizing rules
- ✅ Stop loss and take profit defined

---

## 📊 DELIVERABLES

### Required Outputs:

1. **Fixed Backtesting System**
   - `clean_backtest.py` producing realistic results
   - Sanity checks implemented

2. **Strategy Comparison Report**
   - Markdown table with all metrics
   - Clear winner identified
   - Reasoning for choice

3. **Risk/Reward Analysis**
   - Optimal stop loss / take profit for each strategy
   - Risk/reward ratios calculated
   - Recommendation with justification

4. **Optimized Strategy Implementation**
   - Final production-ready strategy code
   - Comprehensive documentation
   - Ready for 60-day paper trading validation

5. **Updated Documentation**
   - `docs/OPTIMIZATION_RESULTS.md` (your findings)
   - `docs/FINAL_STRATEGY_GUIDE.md` (how to use)
   - `docs/BACKTEST_METHODOLOGY.md` (how you tested)

---

## 🚫 CONSTRAINTS & RULES

### DO:
- ✅ Make surgical, minimal changes to code
- ✅ Preserve existing working functionality
- ✅ Add comments explaining your changes
- ✅ Test thoroughly before recommending
- ✅ Use scientific method (hypothesis → test → conclude)
- ✅ Focus on reproducible results

### DON'T:
- ❌ Over-optimize on limited data (89 days only)
- ❌ Chase 100% win rate (impossible)
- ❌ Remove working code without testing
- ❌ Add unnecessary dependencies
- ❌ Make changes without documentation
- ❌ Trust single backtest results (need multiple tests)

---

## 📈 SUCCESS CRITERIA

### Minimum Acceptable:
- Win Rate: ≥60%
- Monthly Return: ≥10%
- Risk/Reward: ≥1:2
- Max Drawdown: ≤10%

### Excellent Performance:
- Win Rate: ≥70%
- Monthly Return: ≥20%
- Risk/Reward: ≥1:3
- Max Drawdown: ≤5%

---

## 🔍 EVALUATION METRICS

Your work will be evaluated on:

1. **Correctness** (40 points)
   - Does the backtest produce realistic results?
   - Are calculations mathematically sound?
   - Do strategies execute without errors?

2. **Performance** (30 points)
   - Did you achieve ≥65% win rate?
   - Is risk/reward ratio ≥1:2?
   - Is max drawdown <8%?

3. **Documentation** (20 points)
   - Clear explanation of methodology
   - Reproducible results
   - Well-commented code

4. **Practicality** (10 points)
   - Can strategy be deployed to paper trading?
   - Are parameters realistic?
   - Is implementation clean?

---

## 🎓 REFERENCE MATERIALS

### Key Files to Study:
```bash
# Strategy implementations
src/strategies/pivot_zone_strategy.py
src/strategies/optimized_strategy_week1_refined.py
src/strategies/ai_enhanced_strategy.py

# Backtesting
clean_backtest.py

# Trading engine
src/trading/live_engine.py

# Documentation
docs/STRATEGY_OPTIMIZATION_PLAN.md
docs/DATA_FLOW_AND_SENTIMENT_ANALYSIS.md
```

### Database Schema:
```python
# Table: market_data
- id
- symbol (BTCUSDT)
- timestamp
- open_price
- high_price
- low_price
- close_price
- volume
- created_at
```

### TradingView Indicator:
```pinescript
# See docs/COMPLETE_PROJECT_ANALYSIS_NOV_2025.md
# Section: "TRADINGVIEW INDICATOR ANALYSIS"
# Full Pine Script code provided for reference
```

---

## 🚀 GETTING STARTED

### Step 1: Understand Current State
```bash
# Review existing strategies
cat src/strategies/pivot_zone_strategy.py
cat src/strategies/optimized_strategy_week1_refined.py

# Check database
python3 -c "
import sys; sys.path.insert(0, 'src')
from data.database import get_db
from data.models import MarketData
db = next(get_db())
count = db.query(MarketData).filter(MarketData.symbol=='BTCUSDT').count()
print(f'Total candles: {count}')
"
```

### Step 2: Fix Backtest
```bash
# Run current (broken) backtest
python3 clean_backtest.py

# Identify the bug
# Fix the code
# Test again
```

### Step 3: Run Comparison
```bash
# Test all strategies
python3 scripts/run_strategy_comparison.py

# Analyze results
cat results/strategy_comparison.txt
```

### Step 4: Optimize Winner
```bash
# Run risk/reward optimization
python3 scripts/optimize_risk_reward.py

# Implement best settings
# Test final strategy
```

---

## ⚠️ IMPORTANT NOTES

### Data Limitations:
- Only 89 days of BTC data available
- Limited to 1 hour candles
- May not represent all market conditions
- Need to avoid overfitting on this small dataset

### Risk Warnings:
- This is paper trading (no real money yet)
- Past performance ≠ future results
- Crypto markets are highly volatile
- Always test before deploying live

### Validation Required:
- After optimization, requires 60-day paper trading validation
- Must prove consistency before live deployment
- Start with $100-500 when going live

---

## 📞 QUESTIONS TO ANSWER

As you work, answer these questions in your documentation:

1. **Which strategy performed best and why?**
   - Technical analysis? Pivot zones? AI-enhanced?

2. **What's the optimal risk/reward ratio?**
   - Stop loss %? Take profit %?

3. **Does sentiment analysis help?**
   - Compare AI vs non-AI strategies

4. **What's the trade frequency?**
   - How many trades per week?
   - Is it overtrading or undertrading?

5. **What market conditions does the strategy excel in?**
   - Trending? Ranging? Volatile? Calm?

6. **What are the failure modes?**
   - When does the strategy lose money?
   - How can we avoid those situations?

7. **Is 89 days enough data?**
   - Do results seem stable?
   - Should we collect more historical data?

---

## 🎯 FINAL GOAL

Deliver a production-ready, optimized trading strategy that:

✅ Achieves 65%+ win rate on historical backtest  
✅ Has risk/reward ratio of 1:2 or better  
✅ Maintains max drawdown under 8%  
✅ Is fully documented and explainable  
✅ Ready for 60-day paper trading validation  
✅ Can be deployed with confidence

---

**Timeline:** 1-2 weeks of focused work  
**Priority:** Quality over speed - get it right  
**Approach:** Scientific method - test everything  

**Good luck! 🚀**

---

**Agent Prompt Created:** November 10, 2025  
**Project:** AI Trading Bot Optimization  
**Expected Outcome:** High-performance trading system ready for validation
