#!/bin/bash

# AI Trading Bot - Stop All Services
# This script stops all running components

echo "🛑 Stopping AI Trading Bot Services..."
echo "================================"

# Stop API Server (port 9000)
if lsof -Pi :9000 -sTCP:LISTEN -t >/dev/null ; then
    echo "🔴 Stopping API Server (port 9000)..."
    lsof -ti:9000 | xargs kill -9
    echo "   ✅ API Server stopped"
else
    echo "   ℹ️  API Server not running"
fi

# Stop Dashboard (port 8501)
if lsof -Pi :8501 -sTCP:LISTEN -t >/dev/null ; then
    echo "🔴 Stopping Dashboard (port 8501)..."
    lsof -ti:8501 | xargs kill -9
    echo "   ✅ Dashboard stopped"
else
    echo "   ℹ️  Dashboard not running"
fi

echo ""
echo "✅ All services stopped"