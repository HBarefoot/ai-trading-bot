#!/bin/bash
################################################################################
# RESTART SYSTEM WITH ALL FIXES APPLIED
# Stops all services and restarts with proper sequence
################################################################################

echo "================================================================================"
echo "🔧 RESTARTING AI TRADING BOT WITH ALL FIXES"
echo "================================================================================"
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Step 1: Stop everything
echo -e "${BLUE}Step 1: Stopping all services...${NC}"
./stop_all.sh
sleep 2
echo -e "${GREEN}✓ All services stopped${NC}"
echo ""

# Step 2: Start API backend
echo -e "${BLUE}Step 2: Starting API backend...${NC}"
./start_api.sh
echo "Waiting for API to initialize (15 seconds)..."
sleep 15

# Check if API is responding
if curl -s http://localhost:9000/api/status > /dev/null 2>&1; then
    echo -e "${GREEN}✓ API started successfully${NC}"
else
    echo -e "${YELLOW}⚠️  API might still be starting up${NC}"
fi
echo ""

# Step 3: Start trading engine
echo -e "${BLUE}Step 3: Starting trading engine...${NC}"
response=$(curl -s -X POST http://localhost:9000/api/trading/start)
if echo "$response" | grep -q "started"; then
    echo -e "${GREEN}✓ Trading engine started${NC}"
else
    echo -e "${YELLOW}⚠️  Check API logs if engine didn't start${NC}"
fi
echo ""

# Step 4: Verify status
echo -e "${BLUE}Step 4: Verifying system status...${NC}"
status=$(curl -s http://localhost:9000/api/status)
echo "$status" | python3 -m json.tool 2>/dev/null || echo "$status"
echo ""

# Step 5: Start dashboard
echo -e "${BLUE}Step 5: Starting professional dashboard...${NC}"
./start_dashboard_pro.sh &
DASH_PID=$!
sleep 3
echo -e "${GREEN}✓ Dashboard started${NC}"
echo ""

echo "================================================================================"
echo -e "${GREEN}🚀 SYSTEM RESTART COMPLETE!${NC}"
echo "================================================================================"
echo ""
echo "📊 Access Points:"
echo "   • API:       http://localhost:9000/docs"
echo "   • Dashboard: http://localhost:8501"
echo ""
echo "🔍 Quick Status Check:"
echo "   curl http://localhost:9000/api/status"
echo ""
echo "📝 Monitor Logs:"
echo "   • API:       tail -f logs/api/api.log"
echo "   • Engine:    tail -f logs/trading/live_engine.log"
echo "   • Signals:   tail -f logs/signals/alerts.json"
echo ""
echo "⏱️  Charts will appear in dashboard after 10-15 minutes of data collection"
echo ""
echo "================================================================================"
