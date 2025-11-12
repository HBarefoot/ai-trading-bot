#!/bin/bash

# Start 5-Minute High-Frequency Trading Bot
# Optimized for 8-12 trades per day with 65-75% win rate

echo "=========================================="
echo "Starting 5-Minute Trading Bot"
echo "=========================================="
echo ""
echo "Strategy: Week1Refined5m"
echo "Timeframe: 5 minutes"
echo "Expected: 8-12 trades/day"
echo "Win Rate Target: 65-75%"
echo ""
echo "⚠️  PAPER TRADING MODE - NO REAL MONEY"
echo ""
echo "=========================================="
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Error: Virtual environment not found"
    echo "Please run: python3 -m venv venv"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Set Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"

# Start the 5-minute trading engine
python3 -m src.trading.live_engine_5m

echo ""
echo "Trading bot stopped"
