#!/bin/bash
# Stop Phase 5 monitoring

echo "🛑 Stopping Phase 5 monitoring..."

# Check if PID file exists
if [ -f logs/monitoring/monitor.pid ]; then
    PID=$(cat logs/monitoring/monitor.pid)
    if ps -p $PID > /dev/null; then
        kill $PID
        echo "✅ Stopped monitoring process (PID: $PID)"
        rm logs/monitoring/monitor.pid
    else
        echo "⚠️  Process not running"
        rm logs/monitoring/monitor.pid
    fi
else
    echo "⚠️  No PID file found. Monitoring may not be running."
fi

# Generate final report
echo ""
echo "📊 Generating final report..."
/Users/henrybarefoot/ai-learning/.venv/bin/python monitoring/performance_tracker.py

echo ""
echo "✅ Done!"
