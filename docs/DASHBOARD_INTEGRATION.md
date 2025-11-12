# Dashboard Integration - Paper Trading Status

## Overview

The dashboard now displays paper trading status prominently to ensure users always know whether the bot is trading with real money or in simulation mode.

## What Was Updated

### 1. API Backend (`src/api/api_backend.py`)

Added paper trading status to `/api/status` endpoint:

```json
{
  "status": "running",
  "timestamp": "2025-11-10T15:13:46",
  "trading_engine": "active",
  "paper_trading": true,           ← NEW
  "mode": "PAPER TRADING",          ← NEW
  "exchange": "connected",
  "data_feed": "active"
}
```

**Location:** Lines 169-173

**Changes:**
- Reads `trading_engine.paper_trading` flag
- Returns `paper_trading` boolean field
- Returns `mode` string field ("PAPER TRADING" or "LIVE TRADING")

### 2. Dashboard UI (`src/frontend/dashboard.py`)

Added two prominent indicators:

#### A. Main Content Area Warning Banner

**Location:** Lines 1683-1697

**Paper Trading Mode:**
```
🟡 PAPER TRADING MODE - NO REAL MONEY AT RISK

This bot is running in simulation mode. All trades and performance 
metrics are simulated. No real money is being traded.
```

**Live Trading Mode:**
```
💰 LIVE TRADING MODE - REAL MONEY AT RISK!

This bot is trading with real money. All trades will execute on 
your live exchange account.
```

#### B. Sidebar Mode Indicator

**Location:** Lines 1710-1718

Shows mode in settings section:
- Paper Trading: `📄 Mode: PAPER TRADING` (blue info)
- Live Trading: `💰 Mode: LIVE TRADING` (red error)

## How It Works

1. **Dashboard fetches status from API**
   ```python
   status = self.fetch_system_status()
   # Returns: {"paper_trading": true, "mode": "PAPER TRADING", ...}
   ```

2. **Dashboard checks paper_trading flag**
   ```python
   paper_trading = status.get('paper_trading', True)
   mode = status.get('mode', 'UNKNOWN')
   ```

3. **Dashboard displays appropriate warning**
   - Yellow warning banner for paper trading
   - Red error banner for live trading
   - Sidebar indicator always visible

## Visual Indicators

### Paper Trading Mode
- ✅ Yellow warning banner at top of dashboard
- ✅ Blue info badge in sidebar
- ✅ "NO REAL MONEY AT RISK" text
- ✅ 📄 Paper icon

### Live Trading Mode
- ✅ Red error banner at top of dashboard
- ✅ Red error badge in sidebar
- ✅ "REAL MONEY AT RISK!" text
- ✅ 💰 Money icon with 🚨 alert

## Verification

### Check API Status
```bash
curl http://localhost:9000/api/status | python -m json.tool
```

**Expected Response (Paper Trading):**
```json
{
  "status": "running",
  "paper_trading": true,
  "mode": "PAPER TRADING",
  ...
}
```

### View Dashboard
```bash
# Terminal 1: Start API
cd /Users/henrybarefoot/ai-learning/ai-trading-bot
./start_paper_trading.sh

# Terminal 2: Launch Dashboard
cd /Users/henrybarefoot/ai-learning/ai-trading-bot
source .venv/bin/activate
streamlit run src/frontend/dashboard.py --server.port 8501
```

**Access:** http://localhost:8501

**What You'll See:**
1. Yellow warning banner at top: "🟡 PAPER TRADING MODE"
2. Sidebar shows: "📄 Mode: PAPER TRADING"
3. All metrics and trades are from simulation
4. No confusion with real trading

## Safety Features

### Defaults to Paper Trading
- API defaults `paper_trading = True` if engine not running
- Dashboard assumes paper trading if status unavailable
- **Safety First:** Better to assume paper trading than risk real money confusion

### Clear Visual Separation
- **Paper Trading:** Yellow/blue indicators, warning style
- **Live Trading:** Red indicators, error/alert style
- Impossible to mistake one for the other

### Multiple Indicators
- Main content area (always visible)
- Sidebar (always visible when scrolling)
- Mode text explicitly states "PAPER" or "LIVE"

## Paper Trading Metrics

The dashboard will display:

### From API Endpoints
- `/api/status` - Paper trading mode, engine status
- `/api/portfolio` - Simulated portfolio value
- `/api/trades` - Simulated trade history
- `/api/performance` - Simulated performance metrics
- `/api/signals` - Live signals (same for paper and live)

### From Monitoring System
Located in `logs/paper_trading/`:
- `summary.txt` - Daily performance summary
- `trades.json` - Complete trade log
- `daily_metrics.json` - Daily metrics history
- `trades.csv` - Exportable trade data
- `daily_metrics.csv` - Exportable metrics data

## 60-Day Validation

During the 60-day paper trading period:

### Daily Monitoring (5 minutes)
1. Open dashboard: http://localhost:8501
2. Verify yellow "PAPER TRADING MODE" banner shows
3. Check today's trades and PnL
4. Verify win rate is above 60%
5. Check for any errors or warnings

### Weekly Review (30 minutes)
1. View full trade history in dashboard
2. Check `logs/paper_trading/summary.txt`
3. Export CSV: `logs/paper_trading/trades.csv`
4. Calculate weekly win rate
5. Review drawdown and risk metrics

### What Dashboard Shows
- **Portfolio Value:** Starting $10,000 + simulated gains/losses
- **Daily Return:** Today's PnL percentage
- **Win Rate:** Percentage of winning trades
- **Trade Count:** Total trades executed
- **Max Drawdown:** Worst peak-to-trough decline
- **Recent Trades:** Last 10-20 trades with entry/exit/PnL

## Troubleshooting

### Dashboard shows "API OFFLINE"
```bash
# Check if API is running
curl http://localhost:9000/api/status

# If not, start API
cd /Users/henrybarefoot/ai-learning/ai-trading-bot
./start_paper_trading.sh
```

### No paper trading banner shows
1. Check API returns paper_trading flag:
   ```bash
   curl http://localhost:9000/api/status | grep paper_trading
   ```
2. Restart dashboard:
   ```bash
   # Kill streamlit
   pkill -f streamlit
   
   # Restart
   streamlit run src/frontend/dashboard.py --server.port 8501
   ```

### Shows "LIVE TRADING" but should be paper trading
```bash
# Check engine status
curl http://localhost:9000/api/status

# Restart in paper trading mode
cd /Users/henrybarefoot/ai-learning/ai-trading-bot
./start_paper_trading.sh
```

### Metrics not updating
1. Check engine is running: Dashboard shows "🟢 ENGINE ON"
2. Check data feed is active: `/api/status` shows `"data_feed": "active"`
3. View logs: `tail -f logs/paper_trading/summary.txt`

## Next Steps

### After Completing These Updates

1. ✅ API returns paper_trading status
2. ✅ Dashboard displays paper trading banner
3. ✅ Sidebar shows mode indicator
4. ⏳ Test dashboard with bot running
5. ⏳ Start 60-day validation

### To Start Paper Trading

```bash
# Terminal 1: Start Bot
cd /Users/henrybarefoot/ai-learning/ai-trading-bot
./start_paper_trading.sh

# Terminal 2: Launch Dashboard
cd /Users/henrybarefoot/ai-learning/ai-trading-bot
source .venv/bin/activate
streamlit run src/frontend/dashboard.py --server.port 8501
```

### Monitor URLs
- **API Status:** http://localhost:9000/api/status
- **Dashboard:** http://localhost:8501
- **API Docs:** http://localhost:9000/docs

## Files Modified

1. `src/api/api_backend.py` - Lines 169-173 (added paper_trading fields)
2. `src/frontend/dashboard.py` - Lines 1683-1697 (main banner)
3. `src/frontend/dashboard.py` - Lines 1710-1718 (sidebar indicator)

## Summary

✅ **Dashboard will reflect paper trading status**

The dashboard now shows:
1. Prominent yellow warning banner: "PAPER TRADING MODE - NO REAL MONEY AT RISK"
2. Sidebar mode indicator: "📄 Mode: PAPER TRADING"
3. All trades and metrics clearly marked as simulated
4. Impossible to confuse with live trading

All paper trading data will be visible on the dashboard during the 60-day validation period. The monitoring system logs everything to `logs/paper_trading/` and the dashboard displays it in real-time.

**Safety:** The system defaults to paper trading mode and displays multiple warnings. Users cannot accidentally think they're in live trading when in paper trading mode.
