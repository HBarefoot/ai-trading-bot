#!/bin/bash
# Quick Start Script - Restart Everything Clean

echo "════════════════════════════════════════════════════════════════"
echo "     🚀 AI TRADING BOT - QUICK START"
echo "════════════════════════════════════════════════════════════════"
echo ""

cd /Users/henrybarefoot/ai-learning/ai-trading-bot

# Stop everything
echo "1️⃣  Stopping all running services..."
./stop_all.sh > /dev/null 2>&1
sleep 2
echo "   ✅ All services stopped"
echo ""

# Start API and engine
echo "2️⃣  Starting API backend and trading engine..."
./start_api.sh &
API_PID=$!
sleep 25

echo ""
echo "3️⃣  Verifying system status..."
sleep 2

STATUS=$(curl -s http://localhost:9000/api/status 2>/dev/null)
if echo "$STATUS" | grep -q '"trading_engine":"active"'; then
    echo "   ✅ Trading engine is ACTIVE"
else
    echo "   ⚠️  Trading engine may need manual start:"
    echo "      curl -X POST http://localhost:9000/api/trading/start"
fi

if echo "$STATUS" | grep -q '"data_feed":"active"'; then
    echo "   ✅ Data feed is ACTIVE"
else
    echo "   ⚠️  Data feed not active"
fi

if echo "$STATUS" | grep -q '"exchange":"connected"'; then
    echo "   ✅ Exchange connected"
else
    echo "   ⚠️  Exchange not connected"
fi

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "     ✅ SYSTEM STARTED SUCCESSFULLY!"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "📊 Dashboard:"
echo "   Run in NEW terminal: ./start_dashboard_pro.sh"
echo "   URL: http://localhost:8501"
echo ""
echo "🔍 Quick Checks:"
echo "   Status:  curl http://localhost:9000/api/status | python3 -m json.tool"
echo "   Signals: curl http://localhost:9000/api/signals | python3 -m json.tool"
echo "   Trades:  curl 'http://localhost:9000/api/trades?limit=5' | python3 -m json.tool"
echo ""
echo "📈 Timeline:"
echo "   Now:      Data collection started"
echo "   +15 min:  Charts appear in dashboard"
echo "   +5 hours: Strategy activates (needs 60 candles)"
echo "   +6-24 hrs: First trade expected"
echo ""
echo "📚 Documentation:"
echo "   Quick Ref:  cat FIXES_SUMMARY.txt"
echo "   Full Guide: cat STARTUP_GUIDE.md"
echo ""
echo "Press Ctrl+C to stop the API..."
echo "════════════════════════════════════════════════════════════════"

wait $API_PID
