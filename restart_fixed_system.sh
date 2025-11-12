#!/bin/bash
# Complete system restart with AI-enhanced strategy

echo "🔄 Restarting AI Trading Bot with fixes..."
echo "=========================================="
echo ""

# Stop all running processes
echo "1️⃣  Stopping all processes..."
./stop_all.sh
sleep 3

echo ""
echo "2️⃣  Starting API backend (with AI enabled)..."
./start_api.sh &
sleep 10

echo ""
echo "3️⃣  Starting trading engine..."
curl -X POST http://localhost:9000/api/trading/start 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✅ Trading engine started!"
else
    echo "⚠️  Couldn't auto-start engine. Use dashboard button or run:"
    echo "   curl -X POST http://localhost:9000/api/trading/start"
fi

echo ""
echo "4️⃣  Opening professional dashboard..."
sleep 2
open http://localhost:8501 2>/dev/null || echo "   Navigate to: http://localhost:8501"
./start_dashboard_pro.sh &

echo ""
echo "=========================================="
echo "✅ System restarted!"
echo ""
echo "📊 Dashboard: http://localhost:8501"
echo "🔌 API: http://localhost:9000"
echo ""
echo "💡 The system is now running with:"
echo "   • AI-Enhanced Strategy (Technical 40% + LSTM 30% + Sentiment 30%)"
echo "   • Paper Trading Mode"
echo "   • 5-minute timeframe"
echo "   • Real-time Binance.US data"
echo ""
