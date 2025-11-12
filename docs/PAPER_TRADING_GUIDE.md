# Paper Trading Quick Start Guide
**60-Day Validation Period**

---

## 🚀 Starting Paper Trading

```bash
cd /Users/henrybarefoot/ai-learning/ai-trading-bot
./start_paper_trading.sh
```

**What happens:**
- ✅ Week 1 Refined strategy loaded (75% backtest win rate)
- ✅ Paper trading mode enabled (NO REAL MONEY)
- ✅ Live Binance.US data streaming
- ✅ Performance monitoring active

---

## 📊 Daily Monitoring (Takes 5 Minutes)

### 1. Check API Status
```bash
curl http://localhost:9000/api/status | python3 -m json.tool
```

**Look for:**
- `"status": "healthy"`
- `"trading_engine": true`
- `"data_feed": "active"`

### 2. View Daily Summary
```bash
cat logs/paper_trading/summary.txt
```

**Key metrics:**
- **Win Rate:** Should stay above 60%
- **Total Return:** Should be positive
- **Max Drawdown:** Should stay below 10%

### 3. Check Recent Logs
```bash
tail -50 logs/api.log
```

**Look for:**
- No errors or warnings
- Trade signals being generated
- Data feed updates every minute

### 4. View Trade History
```bash
cat logs/paper_trading/trades.json
```

**Review:**
- Entry/exit prices
- Win/loss breakdown
- Exit reasons

---

## 📈 Weekly Review Checklist

**Every Sunday:**

1. **Calculate Week's Performance**
```bash
cd /Users/henrybarefoot/ai-learning/ai-trading-bot/src
/Users/henrybarefoot/ai-learning/.venv/bin/python trading/paper_trading_monitor.py
```

2. **Export to CSV for Analysis**
- Open `logs/paper_trading/trades.csv` in Excel/Google Sheets
- Calculate weekly win rate
- Plot equity curve
- Review max drawdown

3. **Check Progress**
- Days running / 60
- Current win rate vs 60% target
- Total return vs breakeven

4. **Document Issues**
- Any errors or failures?
- Unexpected behavior?
- Data feed problems?

5. **Adjust if Needed**
- If win rate < 50% after 2 weeks → investigate
- If errors frequent → check logs
- If data issues → verify Binance API

---

## 🎯 Success Criteria (After 60 Days)

✅ **READY FOR LIVE TRADING:**
- Win rate ≥ 60%
- Positive total return
- Max drawdown < 10%
- No major system errors
- Consistent performance

⚠️ **NEEDS MORE WORK:**
- Win rate < 60%
- Negative total return
- Max drawdown > 10%
- Frequent errors
- Inconsistent results

---

## 🔧 Common Commands

### Check if Running
```bash
curl http://localhost:9000/api/status
```

### Stop Everything
```bash
cd /Users/henrybarefoot/ai-learning/ai-trading-bot
./stop_all.sh
```

### Restart
```bash
./stop_all.sh
sleep 3
./start_paper_trading.sh
```

### View Live Logs
```bash
tail -f logs/api.log
```

### Check Trades
```bash
python3 -c "import json; print(json.dumps(json.load(open('logs/paper_trading/trades.json')), indent=2))"
```

---

## 📋 Daily Checklist (Print This)

**Every Morning:**
- [ ] Check API is running: `curl http://localhost:9000/api/status`
- [ ] View summary: `cat logs/paper_trading/summary.txt`
- [ ] Check win rate (should be 60%+)
- [ ] Verify no errors in logs
- [ ] Note any new trades

**Red Flags:**
- ❌ Win rate drops below 50% for 3+ days
- ❌ Multiple consecutive losing trades (5+)
- ❌ API errors or crashes
- ❌ Data feed disconnections
- ❌ Max drawdown > 15%

**What to Do:**
1. Document the issue in a text file
2. Check logs for errors
3. Consider parameter adjustments
4. May need to revisit strategy

---

## 📞 Emergency Procedures

### API Won't Start
```bash
# Check what's using port 9000
lsof -ti:9000

# Kill it
lsof -ti:9000 | xargs kill -9

# Restart
./start_paper_trading.sh
```

### Data Feed Issues
```bash
# Check .env file has API keys
cat .env | grep BINANCE

# Verify keys are valid
# Test connection manually
```

### Performance Issues
```bash
# Check system resources
top -l 1 | grep -E "^CPU|^Phys"

# Check disk space
df -h

# Restart if needed
./stop_all.sh && sleep 3 && ./start_paper_trading.sh
```

---

## 🎓 Understanding the Metrics

**Win Rate:**
- Number of profitable trades / total trades
- Target: 60%+
- Week 1 Refined backtest: 75%

**Total Return:**
- Cumulative profit/loss percentage
- Target: Positive
- Week 1 Refined backtest: +1.47% over 90 days

**Max Drawdown:**
- Largest peak-to-trough decline
- Target: < 10%
- Week 1 Refined backtest: -0.88%

**Sharpe Ratio:**
- Return per unit of risk
- Target: > 1.0
- Higher is better

---

## 📁 File Locations

**Logs:**
- Main API log: `logs/api.log`
- Paper trading summary: `logs/paper_trading/summary.txt`
- Trade history: `logs/paper_trading/trades.json`
- Daily metrics: `logs/paper_trading/daily_metrics.json`

**Strategy:**
- Week 1 Refined: `src/strategies/optimized_strategy_week1_refined.py`
- Live engine: `src/trading/live_engine.py`
- Monitor: `src/trading/paper_trading_monitor.py`

**Documentation:**
- Deployment summary: `docs/DEPLOYMENT_SUMMARY.md`
- Week 1 details: `docs/WEEK1_REFINED.md`
- Quick reference: `docs/QUICK_REFERENCE_CARD.md`

---

## 🚀 After 60 Days

**If Successful (60%+ win rate):**
1. Review `logs/paper_trading/summary.txt`
2. Export all data to CSV
3. Calculate final metrics
4. Update documentation
5. Prepare for live trading:
   - Start with $100-500
   - Risk only 2% per trade
   - Monitor even more closely
   - Scale up slowly (20% per month)

**If Not Successful (<60% win rate):**
1. Run Pivot Zone optimizer:
```bash
cd src/strategies
/Users/henrybarefoot/ai-learning/.venv/bin/python optimize_pivot_zone.py
```
2. Analyze failure modes
3. Consider alternative strategies
4. Return to paper trading with improvements

---

## 💡 Tips for Success

1. **Be Patient:** 60 days seems long, but it's necessary for validation
2. **Check Daily:** 5 minutes each morning
3. **Document Everything:** Keep notes on unusual behavior
4. **Don't Interfere:** Let the strategy run without manual intervention
5. **Trust the Process:** Week 1 Refined has proven 75% win rate
6. **Review Weekly:** Sunday review helps catch issues early
7. **Prepare for Live:** Use this time to build confidence

---

## 📞 Support

**Having Issues?**
1. Check this guide first
2. Review `logs/api.log` for errors
3. Consult `docs/DEPLOYMENT_SUMMARY.md`
4. Check GitHub issues (if applicable)

**Good Resources:**
- Week 1 Refined documentation: `docs/WEEK1_REFINED.md`
- Strategy comparison: `docs/DEPLOYMENT_SUMMARY.md`
- Quick answers: `docs/QUICK_REFERENCE_CARD.md`

---

**Current Status:** 🟢 Paper Trading Active  
**Start Date:** [Fill in when you start]  
**Target End Date:** [60 days from start]  
**Win Rate Target:** 60%+  
**Current Win Rate:** [Check daily]

**Good luck! 🚀**
