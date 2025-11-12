# Data Flow Architecture - Paper Trading with Live Data

## How It Works

### You Are Correct! ✅

**Paper Trading** = Simulated orders + Real market data from Binance

```
┌─────────────────────────────────────────────────────────────┐
│                    PAPER TRADING MODE                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  📊 REAL DATA (from Binance.US)                             │
│  ├─ Live prices via WebSocket                               │
│  ├─ Real-time ticker updates                                │
│  └─ Actual market conditions                                │
│                                                              │
│  💰 SIMULATED TRADING (no real money)                       │
│  ├─ Virtual portfolio ($10,000 starting balance)            │
│  ├─ Simulated order execution                               │
│  ├─ Fake positions and P&L                                  │
│  └─ No actual exchange orders                               │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Data Flow Diagram

```
Binance.US API
    │
    │ WebSocket Stream (live prices)
    ↓
API Backend (port 9000)
    │
    ├─→ Data Feed Manager
    │   └─→ Stores latest prices in memory
    │
    ├─→ Candle Aggregator
    │   └─→ Builds 5-minute candles from live ticks
    │
    └─→ Trading Engine
        │
        ├─→ Strategy (generates signals from candles)
        │
        └─→ Portfolio Manager
            │
            ├─→ PAPER MODE: Simulates order execution
            └─→ LIVE MODE: Actually sends orders to Binance
```

## Key Components

### 1. **API Backend** (`src/api/api_backend.py`)
- Runs on port 9000
- Manages WebSocket connection to Binance.US
- Configuration: `use_mock=False` (real data)
- Serves data to dashboard and diagnostic tools

### 2. **Data Feed Manager** (`src/data/live_feed.py`)
- Connects to Binance.US WebSocket
- Receives real-time price updates
- Stores latest prices for each symbol
- Used by: Trading engine, API endpoints

### 3. **Candle Aggregator** (`src/data/candle_aggregator.py`)
- Takes live price ticks
- Builds 5-minute OHLCV candles
- Stores candles in memory
- Provides historical data to strategy

### 4. **Trading Engine** (`src/trading/live_engine_5m.py`)
- Gets candles from aggregator
- Generates trading signals
- Executes trades based on mode:
  - **Paper Trading**: `exchange.demo_mode = True` (simulated)
  - **Live Trading**: `exchange.demo_mode = False` (real orders)

## Your Current Setup

Based on your system:

```python
# From src/api/api_backend.py startup
await start_live_feed(use_mock=False)  # ✅ Real Binance.US data

# From trading engine
paper_trading = True  # ✅ Simulated orders
```

**Result**: You're getting **real market data** from Binance.US but making **simulated trades**.

## Why the Diagnostic Script Shows Warning

The diagnostic script (`test_signal_execution.py`) runs as a **separate process** from your API backend. 

**Problem**:
- Script tries to create its own `data_feed_manager`
- That instance is NOT connected to Binance WebSocket
- Only the API backend has the active WebSocket connection

**Solution**: 
- Script now checks the API endpoint instead: `GET /api/live-data`
- This gets the actual live prices from the running API backend

## Verify Your Setup

### 1. Check API Backend Console

You should see:
```
INFO:data.live_feed:Using Binance.US WebSocket endpoint
INFO:data.live_feed:Connected to Binance.US WebSocket: ['btcusdt@ticker', ...]
INFO:     Application startup complete.
```

✅ This confirms real Binance.US data is flowing

### 2. Check Trading Engine Mode

In console when bot starts:
```
📄 PAPER TRADING (5m) Engine Started
⚠️  PAPER TRADING MODE - NO REAL MONEY AT RISK
```

✅ This confirms simulated trading

### 3. Check Live Prices via API

```bash
curl http://localhost:9000/api/live-data
```

Should return real-time prices:
```json
{
  "BTCUSDT": {
    "symbol": "BTCUSDT",
    "price": 89234.50,
    "timestamp": "2025-11-11T20:45:00Z",
    "volume": 123456.78,
    "change_24h": 2.34
  },
  ...
}
```

✅ This confirms data is coming from Binance.US

## What "Paper Trading" Means

| Aspect | Paper Trading | Live Trading |
|--------|--------------|--------------|
| Market Data | ✅ Real from Binance.US | ✅ Real from Binance.US |
| Price Updates | ✅ Real-time WebSocket | ✅ Real-time WebSocket |
| Signal Generation | ✅ Real strategy logic | ✅ Real strategy logic |
| Order Execution | ❌ Simulated | ✅ Real orders sent |
| Money at Risk | ❌ None ($0) | ✅ Real money |
| Portfolio | ❌ Virtual balance | ✅ Real exchange balance |
| Positions | ❌ Tracked in memory | ✅ Actual exchange positions |
| P&L | ❌ Simulated gains/losses | ✅ Real gains/losses |

## Testing Your Setup

### 1. Verify Live Data is Flowing

```bash
# Start the API (if not running)
./start_api.sh

# Wait 30 seconds, then check
curl http://localhost:9000/api/live-data | python3 -m json.tool
```

You should see current BTC/ETH/SOL prices that match Binance.US market.

### 2. Verify Candles are Accumulating

```bash
# Run diagnostic script
python test_signal_execution.py
```

Look for section "6. Candle Aggregator" - should show increasing candle counts.

### 3. Watch for Signals

Console should show (after 5 hours):
```
🟢 BUY SIGNAL detected for BTCUSDT @ $89234.50 (RSI: 35.2, Trend: BULLISH)
💰 Executing BUY for BTCUSDT: 0.033500 @ $89234.50 ($2989.00)
✅ BUY EXECUTED: 0.033500 BTCUSDT at $89234.50
```

✅ This is a **simulated order** using **real price data**

## Summary

Your understanding is **100% correct**:

✅ **Paper Trading** = You're not risking real money
✅ **Real Data** = Prices come from live Binance.US WebSocket
✅ **Simulated Orders** = Bot "pretends" to buy/sell
✅ **Safe Testing** = Learn and tune strategy risk-free

The warning in the diagnostic script was misleading because:
- Script runs separately from API
- Doesn't have access to the live WebSocket connection
- Needs to query the API instead

**Your bot is working correctly!** It's receiving real Binance.US market data and making simulated trades based on that real data. This is exactly what paper trading should do.
