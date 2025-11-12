# Signal Execution Troubleshooting Guide

## Recent Fixes Applied

### 1. **Fixed Timezone Import Error**
- **Issue**: `timezone` was not imported from datetime module
- **Fix**: Added `timezone` to imports in `src/data/live_feed.py`
- **Impact**: WebSocket messages now process without errors

### 2. **Fixed JSON Serialization Error**  
- **Issue**: Numpy int64/float64 types couldn't be serialized to JSON
- **Fix**: Added `convert_value()` helper in `signal_monitor.py` to convert numpy types
- **Impact**: Signal states now save properly without errors

### 3. **Fixed Network Timeout Issues**
- **Issue**: Binance API calls timing out after 10 seconds
- **Fix**: 
  - Increased timeout to 30 seconds
  - Added retry logic (3 attempts with 2s delay)
- **Location**: `src/trading/exchange_integration.py`
- **Impact**: More reliable API connections

### 4. **Enhanced Buy Signal Logging**
- **Issue**: Unclear why buy signals weren't executing
- **Fix**: Added comprehensive debug logging to show:
  - When buy signals are detected
  - Why positions can't be opened (existing position, insufficient cash, etc.)
  - Position size calculations
  - Order execution results
- **Location**: `src/trading/live_engine_5m.py`
- **Impact**: Clear visibility into signal execution flow

### 5. **New API Endpoint for Real-Time Signals**
- **Added**: `/api/signals` endpoint 
- **Returns**: 
  - Current signal states for all symbols
  - Recent alerts (last 20)
  - Performance summary
- **Location**: `src/api/api_backend.py`
- **Impact**: Dashboard can now display accurate real-time signal information

## Why Buy Signals May Not Execute

### Common Reasons:

1. **Position Already Exists**
   - Only one position per symbol allowed
   - Must sell existing position before buying again
   - Log message: `"Cannot open position for {symbol}: position already exists"`

2. **Insufficient Cash**
   - System keeps 10% cash minimum
   - Need at least 10% of initial balance available
   - Log message: `"insufficient cash ($X / $Y min required)"`

3. **Position Size Too Small**
   - Calculated position size must be > 0
   - Based on 30% max position size rule
   - Log message: `"Position size too small for {symbol}: $X"`

4. **Not Enough Candle Data**
   - Strategy requires 60+ 5-minute candles
   - Takes ~5 hours to accumulate from scratch
   - Log message: `"Not enough 5m candles for {symbol}: X/60"`

5. **Signal Already Processed**
   - System tracks previous signal state
   - Only executes on signal *changes*
   - If signal was already BUY, won't execute again

## How to Diagnose Issues

### 1. Run the Diagnostic Script
```bash
python test_signal_execution.py
```

This will show you:
- Trading engine status
- Portfolio balances and positions
- Current signals for all symbols
- Recent alerts
- Data feed status
- Candle availability

### 2. Check the Console Logs

Look for these key messages:

**Signal Detection:**
```
🟢 BUY SIGNAL detected for BTCUSDT @ $42000.00 (RSI: 35.2, Trend: BULLISH)
```

**Execution Attempts:**
```
💰 Executing BUY for BTCUSDT: 0.023810 @ $42000.00 ($1000.00)
✅ BUY EXECUTED: 0.023810 BTCUSDT at $42000.00
```

**Execution Blocks:**
```
⚠️  Cannot open position for BTCUSDT: position already exists
⚠️  Cannot open position for ETHUSDT: insufficient cash ($50.00 / $1000.00 min required)
```

### 3. Check API Endpoints

**System Status:**
```bash
curl http://localhost:9000/api/status
```

**Current Signals:**
```bash
curl http://localhost:9000/api/signals
```

**Portfolio Status:**
```bash
curl http://localhost:9000/api/portfolio
```

**Recent Trades:**
```bash
curl http://localhost:9000/api/trades?limit=10
```

### 4. Verify Dashboard Display

The dashboard should now accurately show:

**Overview Tab:**
- Portfolio value and P&L
- Cash balance
- Open positions with current prices
- Win rate and performance metrics

**Signals Tab:**
- Current signal for each symbol (BUY/SELL/HOLD)
- RSI values
- Moving averages
- Trend direction
- Signal change timestamps

**Trades Tab:**
- Complete trade history
- Entry/exit prices
- P&L for each trade
- Trade reasons (SIGNAL, STOP_LOSS, TAKE_PROFIT)

**Performance Tab:**
- Total return %
- Win rate
- Sharpe ratio
- Max drawdown
- Trade frequency

## Expected Behavior

### Normal Operation:

1. **Data Collection** (First 5 hours)
   - WebSocket connects to Binance.US
   - 5-minute candles accumulate
   - Need 60 candles minimum (300 minutes = 5 hours)

2. **Signal Generation** (Once sufficient data)
   - Strategy analyzes candles every 30 seconds
   - Compares current signal to previous
   - Only acts on signal *changes*

3. **Order Execution** (When signal changes)
   - BUY signal detected → checks position constraints
   - Calculates position size (30% max of portfolio)
   - Places market order on Binance
   - Records trade and updates portfolio

4. **Position Management**
   - Monitors stop loss (15% below entry)
   - Monitors take profit (30% above entry)
   - Closes positions automatically on triggers

### Typical Timeline:

- **0-5 hours**: Accumulating candle data, no trades
- **5+ hours**: Ready to trade, watching for signals
- **Expected trades**: 8-12 per day (5-minute strategy)
- **Hold time**: Minutes to hours per position

## Trading Rules Currently Active

1. **Max Position Size**: 30% of portfolio per symbol
2. **Max Positions**: 1 per symbol (no pyramiding)
3. **Cash Reserve**: Keep 10% minimum in cash
4. **Stop Loss**: 15% below entry price
5. **Take Profit**: 30% above entry price
6. **Signal Type**: Week 1 Refined 5m Strategy
7. **Timeframe**: 5-minute candles
8. **Update Frequency**: Every 30 seconds

## Next Steps

1. **Monitor for 5+ hours** to accumulate sufficient candle data
2. **Watch console logs** for signal detection messages
3. **Run diagnostic script** to verify system status
4. **Check dashboard** to confirm accurate data display
5. **Review logs/signals/alerts.json** for complete alert history

## If Issues Persist

Check these files for errors:
- `logs/trading.log` - Trading engine errors
- `logs/signals/alerts.json` - Signal alerts
- `logs/signals/signals.json` - Current signal states

Common problems:
- API connection issues → Check `.env` credentials
- No candle data → Wait for accumulation (5 hours)
- Paper trading mode → Verify mode in startup logs
