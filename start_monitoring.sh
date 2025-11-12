#!/bin/bash
# Phase 5 - Start Extended Monitoring
# Runs continuous system monitoring in the background

echo "🚀 Starting Phase 5 Extended Monitoring..."
echo ""

# Navigate to project directory
cd "$(dirname "$0")"

# Check if API is running
if ! curl -s http://localhost:9000/api/health > /dev/null; then
    echo "❌ API is not running. Please start the API first:"
    echo "   ./start_api.sh"
    exit 1
fi

echo "✅ API is running"

# Check if Dashboard is running
if ! curl -s http://localhost:8501 > /dev/null; then
    echo "⚠️  Dashboard is not running. Start it with:"
    echo "   ./start_dashboard.sh"
fi

# Create logs directory
mkdir -p logs/monitoring

# Start system monitor in background
echo ""
echo "📊 Starting system monitor (5-minute intervals)..."
nohup /Users/henrybarefoot/ai-learning/.venv/bin/python monitoring/system_monitor.py > logs/monitoring/monitor.log 2>&1 &
MONITOR_PID=$!
echo "   PID: $MONITOR_PID"
echo "   Log: logs/monitoring/monitor.log"

# Save PID for later
echo $MONITOR_PID > logs/monitoring/monitor.pid

echo ""
echo "✅ Monitoring started successfully!"
echo ""
echo "To view real-time logs:"
echo "   tail -f logs/monitoring/monitor.log"
echo ""
echo "To collect daily snapshot:"
echo "   /Users/henrybarefoot/ai-learning/.venv/bin/python monitoring/performance_tracker.py"
echo ""
echo "To stop monitoring:"
echo "   ./stop_monitoring.sh"
echo ""
