# Quick Reference Card - AI Trading Bot
**Date:** November 10, 2025

---

## 🎯 YOUR QUESTIONS - QUICK ANSWERS

| # | Question | Answer |
|---|----------|--------|
| 1 | How do we get market data? | **3 sources:** Binance WebSocket (live), PostgreSQL (historical 89 days), RSS+Reddit (sentiment) |
| 2 | How is sentiment applied to orders? | **Currently NOT applied** - exists but not enabled. Change line 158 in `live_engine.py` |
| 3 | Will live data kick in automatically? | **No** - Must change line 75 in `api_backend.py` from `use_mock=True` to `False` |
| 4 | Where does sentiment come from? | **Free sources:** News RSS (4 sites) + Reddit (4 subreddits) + Ollama AI (local, $0/month) |
| 5 | What is Alpaca? | **Stock trading platform** (NOT crypto) - Not needed, safe to ignore |
| 6 | What's our current strategy? | **MA crossover** - Too simple, 37% win rate, needs upgrade to pivot zones |
| 7 | Should we use TradingView indicator? | **YES!** Pivot zones are better than MA crossovers - recommended approach |

---

## 📊 PROJECT STATUS

### ✅ Working
- Infrastructure (API, dashboard, monitoring)
- Database (3,454 candles, 89 days BTC)
- Binance API keys configured
- Sentiment collection (News + Reddit + Ollama)

### ❌ Needs Work
- Strategy (current = 37% win rate)
- Sentiment not integrated in trading
- Using mock data (not real Binance)
- No advanced risk management

---

## 🎯 OPTIMIZATION GOAL

**From:** 37% win rate (losing money)  
**To:** 60-70% win rate (profitable)  
**How:** Implement pivot zones + AI sentiment + better risk management  
**Timeline:** 3-4 weeks implementation + 8 weeks validation = 3 months total

---

## 📁 DOCUMENTS CREATED

1. **PROJECT_ANALYSIS_SUMMARY.md** ← **START HERE**
   - Quick answers to all questions
   - Current status
   - Action plan

2. **COMPREHENSIVE_PROJECT_ANALYSIS.md**
   - Deep technical analysis
   - Data flow diagrams
   - TradingView indicator breakdown
   - Full optimization roadmap

3. **STRATEGY_OPTIMIZATION_IMPLEMENTATION_PROMPT.md**
   - Detailed code to implement
   - For AI agent to use
   - Step-by-step guide

---

## 🚀 QUICK START ACTIONS

### Option 1: Enable Live Data (Optional)
```bash
# Edit src/api/api_backend.py (line 75)
# Change: await start_live_feed(use_mock=False)
./stop_all.sh && ./start_api.sh
```

### Option 2: Enable AI Sentiment (Optional)
```bash
# Edit src/trading/live_engine.py (line 158)
# Change to: self.strategy = AIEnhancedStrategy()
./stop_all.sh && ./start_api.sh
```

### Option 3: Implement New Strategy (Recommended)
```bash
# Give STRATEGY_OPTIMIZATION_IMPLEMENTATION_PROMPT.md to AI agent
# Or implement manually following the guide
```

---

## 📈 EXPECTED RESULTS

| Metric | Current | Target |
|--------|---------|--------|
| Win Rate | 37% | 60-70% |
| Trades/Day | 5.5 | 1-2 |
| Monthly Return | -5% to +5% | +15% to +30% |
| Max Drawdown | High | <8% |
| Sharpe Ratio | Low | >1.2 |

---

## ⚠️ KEY WARNINGS

1. **Don't rush** - Paper trade 2+ months before real money
2. **Start small** - Max $500 when going live
3. **Include fees** - 0.1% Binance fees in backtest
4. **Verify data** - Check historical data quality
5. **No guarantees** - 60-70% win rate is target, not promise

---

## 📞 NEXT STEPS

1. ✅ Read PROJECT_ANALYSIS_SUMMARY.md (this is done)
2. ⏳ Read COMPREHENSIVE_PROJECT_ANALYSIS.md (for details)
3. ⏳ Decide: implement new strategy or optimize current?
4. ⏳ Optional: Enable live Binance data
5. ⏳ Optional: Enable AI sentiment
6. ⏳ Implement pivot zone strategy (2-4 weeks)
7. ⏳ Paper trade (2 months)
8. ⏳ Go live (when validated)

---

## 🎓 KEY CONCEPTS

**Pivot Zones:**
- Support/resistance levels based on daily open + range
- Price touches zone and closes above/below = signal
- More reliable than indicator crossovers
- From TradingView "True Algo Alerts"

**AI Sentiment:**
- Collects news + Reddit posts
- Ollama AI analyzes (local, free)
- Filters trades against strong opposing sentiment
- Adjusts position sizes based on confidence

**Risk Management:**
- Dynamic stops (ATR-based, adjusts to volatility)
- Take-profits (2:1 risk/reward)
- Trailing stops (lock in profits)
- Position sizing (based on win streaks)

---

## 💾 DATABASE STATUS

```
Candles:     3,454
Period:      Aug 12 - Nov 10, 2025 (89 days)
Symbol:      BTCUSDT
Fake trades: 0 (cleaned ✅)
Quality:     Needs verification ⚠️
```

---

## 🔧 FILES TO EDIT

### To enable live data:
- `src/api/api_backend.py` (line 75)

### To enable sentiment:
- `src/trading/live_engine.py` (line 158)

### To implement new strategy:
- Create: `src/strategies/pivot_zone_strategy.py`
- Create: `src/strategies/ai_pivot_strategy.py`
- Create: `test_pivot_strategy.py`

---

## 📊 DATA SOURCES

### Market Data:
- **Live:** Binance WebSocket (wss://stream.binance.com:9443/ws/)
- **Historical:** CCXT + Binance API
- **Storage:** PostgreSQL

### Sentiment Data (FREE):
- **News:** Cointelegraph, Decrypt, CoinDesk, CryptoNews
- **Social:** Reddit r/cryptocurrency, r/bitcoin, r/ethereum
- **AI:** Ollama llama3.2:3b (local)
- **Cost:** $0/month

---

## 🎯 SUCCESS METRICS

### Before Paper Trading:
- ✅ Win rate ≥ 60%
- ✅ Sharpe ratio ≥ 1.0
- ✅ Max drawdown ≤ 10%
- ✅ Profitable backtest

### Before Live Trading:
- ✅ 60+ days profitable paper trading
- ✅ Win rate maintained ≥ 60%
- ✅ No critical bugs
- ✅ Comfortable with logic

---

## 🔗 USEFUL LINKS

- **Binance API:** https://binance-docs.github.io/apidocs/spot/en/
- **Binance Testnet:** https://testnet.binance.vision/
- **Alpaca** (not needed): https://alpaca.markets/
- **Pivot Points:** https://www.investopedia.com/terms/p/pivotpoint.asp

---

**Status:** Analysis complete ✅  
**Ready:** Implementation phase ✅  
**Timeline:** 3 months to production ✅

---

**For detailed information, see PROJECT_ANALYSIS_SUMMARY.md**
