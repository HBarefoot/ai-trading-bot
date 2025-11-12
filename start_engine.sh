#!/bin/bash

# Start Trading Engine Helper Script
echo "🚀 Starting trading engine..."

# Wait for API to be ready
sleep 3

# Start the engine
curl -X POST http://localhost:9000/api/trading/start 2>/dev/null

echo ""
echo "✅ Trading engine started!"
echo "   Dashboard: http://localhost:8501"
