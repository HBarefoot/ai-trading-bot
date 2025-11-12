#!/bin/bash
# Reset signal history to test if bot will execute on current signals
# WARNING: Use only for testing! This forces the bot to treat current signals as "new"

echo "========================================="
echo "⚠️  Signal History Reset Tool"
echo "========================================="
echo ""
echo "This will:"
echo "  1. Backup current signal history"
echo "  2. Clear signal memory"
echo "  3. Restart trading engine"
echo "  4. Bot will treat current signals as NEW"
echo ""
echo "⚠️  WARNING: If current signal is BUY, bot will execute immediately!"
echo ""
read -p "Are you sure you want to continue? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Cancelled."
    exit 0
fi

echo ""
echo "1. Checking current signals..."
echo "Current signal states:"
cat logs/signals/signals.json | python3 -c "import json, sys; d=json.load(sys.stdin); [print(f'  {k}: {v[\"signal_type\"]} (signal={v[\"signal\"]})') for k,v in d.items()]"
echo ""

read -p "Continue with reset? (yes/no): " confirm2
if [ "$confirm2" != "yes" ]; then
    echo "Cancelled."
    exit 0
fi

echo ""
echo "2. Backing up current state..."
timestamp=$(date +%Y%m%d_%H%M%S)
cp logs/signals/signals.json logs/signals/signals_backup_${timestamp}.json
cp logs/signals/alerts.json logs/signals/alerts_backup_${timestamp}.json 2>/dev/null
echo "   Backup saved to: logs/signals/*_backup_${timestamp}.json"

echo ""
echo "3. Clearing signal history..."
echo '{}' > logs/signals/signals.json
echo "[]" > logs/signals/alerts.json

echo ""
echo "4. Restarting trading engine..."
curl -s -X POST http://localhost:9000/api/trading/stop > /dev/null
echo "   Engine stopped"
sleep 3
curl -s -X POST http://localhost:9000/api/trading/start > /dev/null
echo "   Engine started"

echo ""
echo "========================================="
echo "✅ Reset complete!"
echo "========================================="
echo ""
echo "The bot will now:"
echo "  - Build new signal history from scratch"
echo "  - Treat the next signal it sees as 'new'"
echo "  - Execute if that signal is BUY"
echo ""
echo "Monitor the API console for messages like:"
echo "  🟢 BUY SIGNAL detected for BTCUSDT @ \$XXX"
echo "  💰 Executing BUY for BTCUSDT..."
echo ""
echo "To restore backup if needed:"
echo "  cp logs/signals/signals_backup_${timestamp}.json logs/signals/signals.json"
echo ""
