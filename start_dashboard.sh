#!/bin/bash

# AI Trading Bot - Dashboard Startup Script
# This script starts the Streamlit dashboard

echo "🎨 Starting AI Trading Bot Dashboard..."
echo "================================"

# Navigate to project directory
cd /Users/henrybarefoot/ai-learning

# Activate virtual environment
source .venv/bin/activate

# Check if dashboard is already running
if lsof -Pi :8501 -sTCP:LISTEN -t >/dev/null ; then
    echo "⚠️  Dashboard already running on port 8501"
    echo "   Stop it with: lsof -ti:8501 | xargs kill -9"
    exit 1
fi

echo ""
echo "🎨 Starting Streamlit Dashboard..."
echo "   URL: http://localhost:8501"
echo ""

# Start the Streamlit dashboard
cd ai-trading-bot
streamlit run src/frontend/dashboard.py --server.port 8501

echo ""
echo "✅ Dashboard stopped"