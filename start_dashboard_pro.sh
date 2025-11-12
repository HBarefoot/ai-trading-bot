#!/bin/bash

echo "🚀 Starting Professional AI Trading Dashboard..."
echo "================================"
echo ""

# Activate virtual environment - try .venv first (parent dir), then local venv
if [ -d "../.venv" ]; then
    source ../.venv/bin/activate
elif [ -d "/Users/henrybarefoot/ai-learning/.venv" ]; then
    source /Users/henrybarefoot/ai-learning/.venv/bin/activate
elif [ -d ".venv" ]; then
    source .venv/bin/activate
elif [ -d "venv" ]; then
    source venv/bin/activate
fi

# Kill any existing streamlit processes
pkill -f "streamlit run.*dashboard" 2>/dev/null

# Start professional dashboard
echo "📊 Launching dashboard on http://localhost:8501"
echo ""
python3 -m streamlit run src/frontend/dashboard_pro.py \
    --server.port 8501 \
    --server.address localhost \
    --theme.base dark \
    --theme.primaryColor "#667eea" \
    --theme.backgroundColor "#0f0c29" \
    --theme.secondaryBackgroundColor "#1a1a2e" \
    --theme.textColor "#ffffff" \
    --browser.gatherUsageStats false

echo ""
echo "✅ Professional Dashboard started!"
echo "   Open: http://localhost:8501"
