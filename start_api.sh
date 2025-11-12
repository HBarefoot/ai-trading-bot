#!/bin/bash

# AI Trading Bot - Startup Script
# This script starts all components of the trading bot

echo "🚀 Starting AI Trading Bot..."
echo "================================"

# Navigate to project directory
cd /Users/henrybarefoot/ai-learning/ai-trading-bot

# Activate virtual environment
source /Users/henrybarefoot/ai-learning/.venv/bin/activate

# Check if API server is already running
if lsof -Pi :9000 -sTCP:LISTEN -t >/dev/null ; then
    echo "⚠️  API Server already running on port 9000"
    echo "   Stop it with: lsof -ti:9000 | xargs kill -9"
    exit 1
fi

echo ""
echo "📡 Starting API Backend Server..."
echo "   URL: http://localhost:9000"
echo "   Docs: http://localhost:9000/docs"
echo ""

# Start the API backend server in background
python -m uvicorn src.api.api_backend:app --reload --host 0.0.0.0 --port 9000 &
API_PID=$!

echo "⏳ Waiting for API to be ready..."
sleep 5

# Check if API is responding
for i in {1..10}; do
    if curl -s http://localhost:9000/api/status > /dev/null 2>&1; then
        echo "✅ API is ready!"
        break
    fi
    echo "   Waiting... ($i/10)"
    sleep 2
done

# Start the trading engine
echo ""
echo "🤖 Starting trading engine..."
START_RESPONSE=$(curl -s -X POST http://localhost:9000/api/trading/start 2>/dev/null)
if echo "$START_RESPONSE" | grep -q "started"; then
    echo "✅ Trading engine started successfully!"
else
    echo "⚠️  Response: $START_RESPONSE"
fi

# Verify engine is running
sleep 2
STATUS=$(curl -s http://localhost:9000/api/status 2>/dev/null)
if echo "$STATUS" | grep -q '"trading_engine":"active"'; then
    echo "✅ Trading engine is ACTIVE and processing signals"
else
    echo "⚠️  Trading engine may not be active. Check status:"
    echo "   curl http://localhost:9000/api/status | python3 -m json.tool"
fi

echo ""
echo "✅ AI Trading Bot is running!"
echo "   API: http://localhost:9000"
echo "   Status: curl http://localhost:9000/api/status"
echo ""
echo "Press Ctrl+C to stop..."

# Wait for API process
wait $API_PID

echo ""
echo "✅ API Server stopped"