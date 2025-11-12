# 🚀 Complete System Startup Guide

## Quick Start (3 Steps)

### Step 1: Stop Everything and Apply Fixes
```bash
cd /Users/henrybarefoot/ai-learning/ai-trading-bot

# Stop all running processes
./stop_all.sh

# Apply critical fixes (already done, but safe to run again)
python3 fix_critical_errors.py
```

### Step 2: Start the Trading System
```bash
# Start API backend and trading engine
./start_api.sh
```

**Expected Output:**
```
🚀 Starting AI Trading Bot...
📡 Starting API Backend Server...
   Waiting... (1/10)
✅ API is ready!
🤖 Starting trading engine...
✅ Trading engine started successfully!
✅ Trading engine is ACTIVE and processing signals
✅ AI Trading Bot is running!
```

### Step 3: Start the Professional Dashboard
```bash
# In a NEW terminal window
cd /Users/henrybarefoot/ai-learning/ai-trading-bot
source /Users/henrybarefoot/ai-learning/.venv/bin/activate
./start_dashboard_pro.sh
```

**Dashboard URL:** http://localhost:8501

---

## ✅ Verification Checklist

### 1. Check API Status
```bash
curl http://localhost:9000/api/status | python3 -m json.tool
```

**Expected output:**
```json
{
  "status": "running",
  "trading_engine": "active",     ← MUST BE "active"
  "paper_trading": true,
  "mode": "PAPER TRADING",
  "exchange": "connected",
  "data_feed": "active"
}
```

### 2. Check Dashboard
- Open http://localhost:8501
- **System Status** should show: **🟢 ACTIVE**
- **Trading Mode** should show: **PAPER TRADING**
- **Exchange** should show: **Binance.US ✅**
- **Data Feed** should show: **Live WebSocket ✅**

### 3. Check Data Collection
```bash
# Should show candles being collected
curl "http://localhost:9000/api/candles/BTCUSDT?limit=5" | python3 -m json.tool
```

### 4. Check Current Signals
```bash
curl http://localhost:9000/api/signals | python3 -m json.tool
```

---

## 📊 Dashboard Features

### Overview Tab
- **System Status**: Real-time engine status (Active/Inactive)
- **Portfolio Metrics**: Value, P&L, position count
- **Performance**: Win rate, total trades, Sharpe ratio
- **Recent Activity**: Last 5 trades

### Charts Tab ⭐️
**Professional TradingView-Style Charts:**
- ✅ Candlestick charts (5-minute timeframe)
- ✅ Symbol selector (BTC, ETH, SOL)
- ✅ Trade markers (entry/exit points)
- ✅ Stop loss & take profit lines
- ✅ Interactive hover data
- ✅ Dark theme

**Note:** Charts need 10-15 minutes of data collection to appear.

**Why Charts May Be Empty:**
1. System just started - wait 10-15 minutes
2. Data feed not connected - check API status
3. Database empty - system will auto-populate from Binance

### Signals Tab
- Current signal for each symbol (BUY/SELL/HOLD)
- AI sentiment score
- Technical indicators (RSI, MA, trend)
- Signal strength and confidence

### Trades Tab
- Complete trade history
- Entry/exit prices
- Stop loss & take profit levels
- P&L per trade
- Trade duration

### Portfolio Tab
- Open positions details
- Unrealized P&L
- Position sizes
- Entry prices

---

## ⏱️ Timeline Expectations

### First 15 Minutes
- ✅ System startup complete
- ✅ WebSocket connected to Binance.US
- ✅ Real-time price data flowing
- ✅ Candles being aggregated every 5 minutes
- ⏳ Charts still building (need more data)

### After 1 Hour
- ✅ ~12 candles collected (1 hour of 5-min data)
- ✅ Charts start appearing in dashboard
- ⏳ Still accumulating data for strategy (needs 60+ candles)

### After 5 Hours (60 candles)
- ✅ Full dataset available
- ✅ Strategy starts generating signals
- ✅ AI sentiment analysis active
- ✅ Ready to trade (waiting for signal change)

### After 6-24 Hours
- ✅ **First trade expected** (when strong BUY signal appears)
- ✅ Full system operational
- ✅ All dashboard features working

---

## 🤖 AI Features Active

### ✨ AI-Enhanced Strategy is ENABLED
The system is using AIEnhancedStrategy with:
- **40% Technical Indicators** (MA, RSI, Volume)
- **30% LSTM Predictions** (placeholder for now)
- **30% Sentiment Analysis** (News + Reddit + AI)

### Sentiment Sources
1. **News RSS Feeds** - CryptoPanic, CoinDesk, etc.
2. **Reddit** - r/cryptocurrency, r/bitcoin, etc.
3. **Ollama AI** - Local sentiment analysis (free)

### Sentiment Caching
- Cached for 1 hour per symbol
- Automatically refreshes
- Prevents rate limiting
- Reduces API costs (all free sources)

---

## 🎯 Why Trades Aren't Executing

### Common Reasons:

#### 1. **Engine Not Started** ✓ FIXED
- Solution: Improved `start_api.sh` now auto-starts engine
- Verification: Check `/api/status` shows `"trading_engine": "active"`

#### 2. **Insufficient Data** ⏳ EXPECTED
- Needs: 60+ candles (5 hours of data)
- Current: System just started
- Solution: Wait for data accumulation

#### 3. **No Signal Change** 🎯 CORRECT BEHAVIOR
- Bot only trades when signal CHANGES from HOLD → BUY
- Dashboard may show "BUY" signal but no trade if it's been BUY for a while
- This prevents re-entering the same position

#### 4. **Strict Entry Conditions** 🔒 BY DESIGN
- Requires ALL confirmations:
  - RSI < 30 (oversold)
  - MA crossover
  - HTF trend confirmation (MA20 > MA50 on higher timeframe)
  - Volume > 1.05x average
  - No cooldown (15 min since last trade)

#### 5. **Paper Trading Cash** 💵 CHECK BALANCE
- Needs sufficient cash (>30% position size)
- Check: Dashboard → Portfolio → Cash Balance
- Initial: $10,000 paper money

---

## 🐛 Troubleshooting

### Dashboard Shows "INACTIVE"
```bash
# Start the trading engine manually
curl -X POST http://localhost:9000/api/trading/start

# Verify
curl http://localhost:9000/api/status | grep trading_engine
# Should show: "trading_engine": "active"
```

### Charts Not Appearing
```bash
# Check if candles are being collected
curl "http://localhost:9000/api/candles/BTCUSDT?limit=1" | python3 -m json.tool

# If empty, wait 10-15 minutes
# System is collecting live data from Binance WebSocket
```

### No Signals Showing
```bash
# Check signal endpoint
curl http://localhost:9000/api/signals | python3 -m json.tool

# If empty, engine may not have 60+ candles yet
# Check candle count:
curl "http://localhost:9000/api/candles/BTCUSDT?limit=100" | python3 -c "import sys, json; print(len(json.load(sys.stdin)))"
```

### API Errors
```bash
# Check API logs
tail -f logs/trading_bot.log

# Common errors and solutions:
# - "Read timed out" → Normal, Binance API timeout, retries automatically
# - "timezone not defined" → Fixed in latest version
# - "close_price not found" → Fixed in latest version
# - "int64 not JSON serializable" → Fixed in latest version
```

### Dashboard Won't Start
```bash
# Check if Streamlit is installed
python3 -c "import streamlit" 2>/dev/null && echo "✅ Installed" || echo "❌ Missing"

# If missing:
source /Users/henrybarefoot/ai-learning/.venv/bin/activate
pip install streamlit plotly

# Then try again:
./start_dashboard_pro.sh
```

---

## 📱 Dashboard Access

### Local Access
- **URL**: http://localhost:8501
- **Browser**: Chrome, Firefox, Safari (any modern browser)
- **Auto-refresh**: Enable in dashboard settings (every 30 seconds)

### Remote Access (Optional)
If you want to access from another device on your network:

1. Find your local IP:
```bash
ipconfig getifaddr en0  # macOS WiFi
# or
ipconfig getifaddr en1  # macOS Ethernet
```

2. Access from other device:
```
http://YOUR_LOCAL_IP:8501
```

---

## 🔄 Daily Operations

### Morning Check (Before Market Hours)
```bash
# 1. Verify system is running
curl http://localhost:9000/api/status

# 2. Check overnight signals
curl http://localhost:9000/api/signals | python3 -m json.tool

# 3. Review any trades
curl "http://localhost:9000/api/trades?limit=10" | python3 -m json.tool
```

### During Trading Day
- Monitor dashboard: http://localhost:8501
- Watch for signal changes in "Signals" tab
- Check trade executions in "Trades" tab
- Monitor P&L in "Portfolio" tab

### End of Day
```bash
# Review performance
curl http://localhost:9000/api/portfolio | python3 -m json.tool

# Check logs for errors
tail -100 logs/trading_bot.log | grep ERROR
```

### System Restart (If Needed)
```bash
# Clean restart
./stop_all.sh
sleep 5
./start_api.sh

# Wait 30 seconds, then start dashboard in new terminal
./start_dashboard_pro.sh
```

---

## 📈 Expected Performance

### Paper Trading Goals
- **Win Rate Target**: 65-70%
- **Risk/Reward**: 1:2 minimum
- **Max Drawdown**: <8%
- **Sharpe Ratio**: >1.2

### Current Strategy Stats (from Backtest)
- **Strategy**: Week1Refined5m + AI Enhancement
- **Backtest Win Rate**: 75% (before AI)
- **Expected Live Win Rate**: 60-65% (with AI)
- **Trade Frequency**: 8-12 trades per day (5-min timeframe)

### Validation Period
- **Minimum**: 60 days of paper trading
- **Required trades**: 50+ completed trades
- **Success criteria**: Meet performance goals above

---

## 🎓 Understanding the System

### Signal Generation Process
1. **Data Collection**: Binance WebSocket → 5-min candles
2. **Aggregation**: Real-time candle builder
3. **Technical Analysis**: Week1Refined5m strategy
4. **AI Enhancement**: Sentiment + LSTM fusion
5. **Signal Output**: BUY (1.0), SELL (-1.0), HOLD (0.0)
6. **Execution**: Only when signal CHANGES

### Trade Execution Flow
1. Signal changes from HOLD → BUY
2. Check entry conditions (all must pass)
3. Calculate position size (30% of portfolio max)
4. Place paper trade order
5. Set stop loss (-15%) and take profit (+30%)
6. Monitor position
7. Exit on signal change or stop/profit trigger

### Risk Management
- **Position Size**: Max 30% per trade
- **Stop Loss**: 15% below entry
- **Take Profit**: 30% above entry
- **Cash Reserve**: Min 10% kept in cash
- **Cooldown**: 15 minutes between trades
- **Max Risk Per Trade**: 4.5% of portfolio (30% × 15%)

---

## 📞 Quick Reference

### Important URLs
- API Backend: http://localhost:9000
- API Docs: http://localhost:9000/docs
- Dashboard: http://localhost:8501
- GitHub MCP: (if configured)

### Important Files
- Logs: `logs/trading_bot.log`
- Signals: `logs/signals/signals.json`
- Config: `config/trading_config.yaml`
- Environment: `.env`

### Key Commands
```bash
# Status check
curl http://localhost:9000/api/status | python3 -m json.tool

# Start engine
curl -X POST http://localhost:9000/api/trading/start

# Stop engine
curl -X POST http://localhost:9000/api/trading/stop

# Get signals
curl http://localhost:9000/api/signals | python3 -m json.tool

# Get trades
curl "http://localhost:9000/api/trades?limit=5" | python3 -m json.tool

# Get portfolio
curl http://localhost:9000/api/portfolio | python3 -m json.tool
```

---

## ✅ Success Criteria

You'll know the system is working correctly when:

1. ✅ Dashboard shows "🟢 ACTIVE" status
2. ✅ Charts display after 15 minutes
3. ✅ Signals show for all 3 symbols (BTC, ETH, SOL)
4. ✅ No ERROR logs (except occasional timeouts)
5. ✅ Candles accumulating (check API endpoint)
6. ✅ First trade executes within 24 hours (after 5+ hours of data)

---

**Ready to Trade!** 🚀

Once you complete the 3 startup steps and verify all checkmarks above, your system is fully operational and ready for paper trading validation.

**Next Steps:**
1. ✅ Complete startup steps
2. ⏱️ Wait 5 hours for data accumulation
3. 👀 Monitor first trade execution
4. 📊 Track performance for 60 days
5. 🎯 Achieve target metrics
6. 💰 Consider live trading (after validation)

---

*Last Updated: 2025-01-12*
*All Critical Fixes Applied ✅*
