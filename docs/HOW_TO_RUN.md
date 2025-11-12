# 🚀 How to Run the AI Trading Bot

## Quick Start (3 Easy Steps)

### 1️⃣ Start the API Backend

```bash
cd /Users/henrybarefoot/ai-learning/ai-trading-bot
./start_api.sh
```

This will start:
- **API Server** at `http://localhost:9000`
- **Interactive API Docs** at `http://localhost:9000/docs`

### 2️⃣ Start the Dashboard (Optional)

In a **new terminal**:

```bash
cd /Users/henrybarefoot/ai-learning/ai-trading-bot
./start_dashboard.sh
```

This will start:
- **Streamlit Dashboard** at `http://localhost:8501`

### 3️⃣ Stop All Services

```bash
cd /Users/henrybarefoot/ai-learning/ai-trading-bot
./stop_all.sh
```

---

## 📋 Manual Commands

### Option 1: Start API Backend (Required)

```bash
cd /Users/henrybarefoot/ai-learning
source .venv/bin/activate
cd ai-trading-bot
python -m uvicorn src.api.api_backend:app --reload --host 0.0.0.0 --port 9000
```

### Option 2: Start Dashboard

```bash
cd /Users/henrybarefoot/ai-learning
source .venv/bin/activate
cd ai-trading-bot
streamlit run src/frontend/dashboard.py --server.port 8501
```

### Option 3: Run Demo/Test Scripts

```bash
cd /Users/henrybarefoot/ai-learning
source .venv/bin/activate
cd ai-trading-bot

# Test the live API system
python demo_live_system.py

# Run Phase 2 backtesting
python src/strategies/phase2_final_test.py

# Run reality check analysis
python src/analysis/reality_check.py
```

---

## 🎯 What Each Component Does

### 1. **API Backend** (Port 9000)
The core trading engine that provides:
- ✅ Real-time market data feeds
- ✅ Trading signal generation
- ✅ Portfolio management
- ✅ Order execution interface
- ✅ Live trading engine control

**Key Endpoints:**
- `GET /api/status` - System status
- `GET /api/live-data` - Live cryptocurrency prices
- `GET /api/portfolio` - Current portfolio
- `GET /api/signals/{symbol}` - Trading signals
- `POST /api/trading/start` - Start live trading

**View all endpoints:** http://localhost:9000/docs

### 2. **Streamlit Dashboard** (Port 8501) - ✅ PHASE 4 ENHANCED
Professional trading interface with:
- ✅ **Overview Tab**: Real-time dashboard with auto-refresh, 4 metric cards, live prices, positions, signals
- ✅ **Charts Tab**: Interactive candlestick/line charts with technical indicators (MA8, MA21, MA50)
- ✅ **Trades Tab**: Complete trade history with filters, export to CSV, P&L tracking
- ✅ **Performance Tab**: 8+ performance metrics, portfolio value chart, strategy details
- ✅ **Live Signals Tab**: Real-time trading signals with technical analysis
- ✅ **AI Insights Tab**: ML predictions placeholder (Phase 5)

**New Phase 4 Features:**
- 🎮 **Manual Trading Controls**: Buy/sell buttons in sidebar with confirmation
- 🎛️ **Engine Controls**: Start/stop trading from dashboard
- 🔔 **Alert System**: Notifications for signal changes and large P&L movements
- 📊 **Enhanced Visualizations**: Professional charts and tables
- � **Export Data**: Download trades as CSV
- 🔄 **Auto-Refresh**: 10-second updates with toggle control
- 🎨 **Custom Styling**: Professional UI with gradient cards and hover effects

---

## 🧪 Testing the System

### Quick API Test

```bash
# Check if API is running
curl http://localhost:9000/api/status

# Get live Bitcoin price
curl http://localhost:9000/api/live-data/BTCUSDT

# Get trading signal for Ethereum
curl http://localhost:9000/api/signals/ETHUSDT

# View portfolio
curl http://localhost:9000/api/portfolio
```

### Run Complete Demo

```bash
cd /Users/henrybarefoot/ai-learning/ai-trading-bot
source /Users/henrybarefoot/ai-learning/.venv/bin/activate
python demo_live_system.py
```

This will test all API endpoints and show live data!

---

## 🔧 Troubleshooting

### "Port already in use" Error

```bash
# Kill process on port 9000 (API)
lsof -ti:9000 | xargs kill -9

# Kill process on port 8501 (Dashboard)
lsof -ti:8501 | xargs kill -9

# Or use the stop script
./stop_all.sh
```

### "Module not found" Error

Make sure you're in the virtual environment:

```bash
cd /Users/henrybarefoot/ai-learning
source .venv/bin/activate
```

### Check if services are running

```bash
# Check API (should return JSON with status)
curl http://localhost:9000/api/status

# Check Dashboard (should show HTML)
curl http://localhost:8501
```

---

## 📊 Project Structure

```
ai-trading-bot/
├── src/
│   ├── api/
│   │   └── api_backend.py          # FastAPI server
│   ├── data/
│   │   ├── database.py             # Database management
│   │   └── live_feed.py            # Real-time data feeds
│   ├── trading/
│   │   ├── live_engine.py          # Live trading engine
│   │   └── exchange_integration.py # Exchange APIs
│   ├── strategies/
│   │   └── phase2_final_test.py    # Backtesting
│   └── frontend/
│       └── dashboard.py            # Streamlit UI
├── start_api.sh                     # Start API server
├── start_dashboard.sh               # Start dashboard
├── stop_all.sh                      # Stop all services
└── demo_live_system.py              # System demo
```

---

## 🎮 Usage Examples

### 1. View Live Trading Signals

**API:**
```bash
curl http://localhost:9000/api/signals/BTCUSDT
```

**Dashboard:**
Go to http://localhost:8501 → "Live Signals" tab

### 2. Check Portfolio Value

**API:**
```bash
curl http://localhost:9000/api/portfolio
```

**Dashboard:**
View "Portfolio" section in the dashboard

### 3. Start Live Trading

**API:**
```bash
curl -X POST http://localhost:9000/api/trading/start
```

**Note:** Currently in DEMO MODE - no real trades will be executed!

---

## ⚠️ Important Notes

1. **Demo Mode**: The system runs in demo/testnet mode by default
2. **No Real Trading**: No actual money will be traded
3. **Paper Trading**: Portfolio starts with $10,000 virtual balance
4. **Real Exchange APIs**: To enable real trading, add your API keys to `.env` file

---

## 🚀 Next Steps

1. ✅ Run the API backend
2. ✅ Open http://localhost:9000/docs to explore the API
3. ✅ Run `python demo_live_system.py` to see it in action
4. 🔜 Connect the dashboard to the live API (Phase 4)
5. 🔜 Deploy to production (Phase 5)

---

## 📞 Support

If you encounter issues:

1. Check logs in the terminal where services are running
2. Verify ports 9000 and 8501 are available
3. Ensure virtual environment is activated
4. Run `./stop_all.sh` and restart services

**Status Check:**
```bash
# Check what's running
lsof -i :9000  # API server
lsof -i :8501  # Dashboard
```

---

**🎉 You're ready to go! Start with `./start_api.sh` and explore the trading bot!**