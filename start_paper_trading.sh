#!/bin/bash
# Start Paper Trading Bot with Week 1 Refined Strategy
# NO REAL MONEY - Paper trading mode enabled

echo "================================================================================"
echo "🚀 AI TRADING BOT - PAPER TRADING MODE"
echo "================================================================================"
echo ""
echo "📄 Mode: PAPER TRADING (NO REAL MONEY)"
echo "📊 Strategy: Week 1 Refined (75% win rate backtest)"
echo "🎯 Goal: Validate 60%+ win rate over 60 days"
echo "📡 Data: Live Binance.US WebSocket"
echo ""
echo "================================================================================"
echo ""

# Navigate to project root
cd "$(dirname "$0")"

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ Error: .env file not found!"
    echo "   Create .env file with your Binance API credentials"
    exit 1
fi

# Check if logs directory exists
mkdir -p logs/paper_trading

# Kill any existing processes
echo "🧹 Cleaning up existing processes..."
pkill -9 -f "api_backend" 2>/dev/null
lsof -ti:9000 | xargs kill -9 2>/dev/null
sleep 2

# Clear old logs
echo "📝 Setting up logs..."
echo "" > logs/api.log
echo "" > logs/paper_trading.log

echo ""
echo "================================================================================"
echo "⚠️  IMPORTANT: PAPER TRADING MODE ACTIVE"
echo "================================================================================"
echo "   - NO real orders will be placed"
echo "   - NO real money at risk"
echo "   - All trades are simulated"
echo "   - Live data from Binance.US"
echo "   - Performance metrics logged to logs/paper_trading/"
echo ""
echo "================================================================================"
echo ""

# Start the API backend with paper trading enabled
echo "🚀 Starting API backend..."
cd /Users/henrybarefoot/ai-learning/ai-trading-bot/src

# Set paper trading environment variable
export PAPER_TRADING=true

# Start the API
/Users/henrybarefoot/ai-learning/.venv/bin/python api/api_backend.py > ../logs/api.log 2>&1 &
API_PID=$!

echo "   API PID: $API_PID"
echo "   Logs: logs/api.log"

# Wait for API to start
echo ""
echo "⏳ Waiting for API to start..."
sleep 5

# Check if API is running
if curl -s http://localhost:9000/api/status > /dev/null 2>&1; then
    echo "✅ API started successfully!"
    echo ""
    
    # Start the trading engine
    echo "🚀 Starting trading engine..."
    sleep 2
    START_RESULT=$(curl -s -X POST http://localhost:9000/api/trading/start)
    echo "✅ Trading engine started"
    echo ""
    
    echo "================================================================================"
    echo "📊 MONITORING DASHBOARD"
    echo "================================================================================"
    echo "   API Status:     http://localhost:9000/api/status"
    echo "   Trading Status: http://localhost:9000/api/trading/status"
    echo "   Logs:           tail -f logs/api.log"
    echo "   Performance:    tail -f logs/paper_trading/summary.txt"
    echo ""
    echo "================================================================================"
    echo "📋 NEXT STEPS"
    echo "================================================================================"
    echo "   1. Monitor daily performance in logs/paper_trading/"
    echo "   2. Check win rate stays above 60%"
    echo "   3. Review logs/paper_trading/summary.txt each day"
    echo "   4. After 60 days, review DEPLOYMENT_SUMMARY.md"
    echo "   5. If successful, proceed to live trading with small capital"
    echo ""
    echo "   To stop:  ./stop_all.sh"
    echo "   To check: curl http://localhost:9000/api/status"
    echo ""
    echo "================================================================================"
    echo "✅ Paper trading bot is now running!"
    echo "================================================================================"
    echo ""
else
    echo "❌ Failed to start API!"
    echo "   Check logs/api.log for errors"
    echo "   Kill process: kill $API_PID"
    exit 1
fi

# Keep terminal open to show logs
echo "📡 Streaming logs (Ctrl+C to stop viewing, bot continues running)..."
echo ""
sleep 2
tail -f logs/api.log
