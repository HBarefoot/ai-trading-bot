# Quick Answers - November 10, 2025

## Your Questions Answered

### 1. How are we getting market data into this app?

**Answer:** Binance API → PostgreSQL → Trading Engine

- **Source:** Binance REST API via CCXT library
- **Current Data:** 3,572 hourly candles (89 days of BTCUSDT)
- **Status:** ✅ Working with your API keys
- **WebSocket:** Available but not needed for 1-hour timeframe

### 2. How are we applying sentiment at the moment of placing orders?

**Answer:** Currently NOT APPLIED ❌

- **Current Strategy:** Week1RefinedStrategy (technical only)
- **Sentiment System:** Fully implemented but not enabled
- **To Enable:** Change 1 line in src/trading/live_engine.py to use AIEnhancedStrategy
- **How it works:** Sentiment weighted 30% in final decision

### 3. What about Alpaca credentials?

**Answer:** NOT NEEDED - Alpaca is for stocks, you're trading crypto on Binance ✅

### 4. Will live data automatically kick in?

**Answer:** YES - Already collecting! ✅ (3,572 candles from Binance)

### 5. Where does sentiment data come from?

**Answer:** 3 FREE sources analyzed locally:
- News RSS feeds (4 crypto sites)
- Reddit (4 crypto subreddits)
- Ollama AI (local analysis)
- Cost: $0/month

### 6. TradingView indicator - does it make sense?

**Answer:** YES ✅ - Already implemented as PivotZoneStrategy

---

## Current Strategy: Week1RefinedStrategy

**Entry:** MA8 > MA21 + RSI < 65 + Volume + Trend filters
**Exit:** MA8 < MA21 OR Stop Loss (-15%) OR Take Profit (+30%)
**Risk/Reward:** 1:2
**Timeframe:** 1-hour candles

---

## Backtest Bug (CRITICAL)

**Issue:** Uses 100% cash per trade instead of 30%
**Result:** Unrealistic 10^37% return
**Real Expected:** 20-40% over 89 days
**Win Rate:** 74% (likely accurate)

**Fix:** Edit clean_backtest.py line 56-67 to use 30% position sizing

---

## Optimization Agent Prompt

```
TASK: Optimize Trading Strategy for 65%+ Win Rate

1. Fix position sizing bug (30% per trade)
2. Compare 3 strategies on 3,572 Binance candles
3. Optimize winner (grid search parameters)
4. Validate (walk-forward + Monte Carlo)
5. Deliver optimized config + performance report

GOAL: 65%+ win rate, 15%+ monthly return
DATA: 89 days BTCUSDT hourly
TIMELINE: 5 days
```

---

**Full Report:** See COMPREHENSIVE_PROJECT_REPORT_NOV10_2025.md
**Status:** 80% complete - fix bug, test strategies, validate 60 days, go live
