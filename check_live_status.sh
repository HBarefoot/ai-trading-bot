#!/bin/bash
# Quick status check for live trading bot

echo "========================================="
echo "AI Trading Bot - Live Status Check"
echo "========================================="
echo ""

echo "1. API Status:"
curl -s http://localhost:9000/api/status | python3 -c "import json, sys; d=json.load(sys.stdin); print(f\"   Engine: {d['trading_engine']}\"); print(f\"   Mode: {d['mode']}\"); print(f\"   Data Feed: {d['data_feed']}\")"
echo ""

echo "2. Current Portfolio:"
curl -s http://localhost:9000/api/portfolio | python3 -c "import json, sys; d=json.load(sys.stdin); print(f\"   Total Value: \${d['total_value']:.2f}\"); print(f\"   Cash: \${d['cash']:.2f}\"); print(f\"   Positions: {len(d['positions'])}\")"
echo ""

echo "3. Real-Time Signals (from Signal Monitor):"
curl -s http://localhost:9000/api/signals | python3 -c "import json, sys; d=json.load(sys.stdin); signals=d.get('signals', []); [print(f\"   {s['symbol']}: {s['signal_type']} @ \${s['price']:.2f} | RSI: {s['rsi']:.1f if s['rsi'] else 'N/A'} | Trend: {s['trend']}\") for s in signals] if signals else print('   No signals yet')"
echo ""

echo "4. Recent Alerts:"
curl -s http://localhost:9000/api/signals | python3 -c "import json, sys; d=json.load(sys.stdin); alerts=d.get('recent_alerts', [])[-5:]; [print(f\"   [{a['timestamp'][11:19]}] {a['message']}\") for a in alerts] if alerts else print('   No alerts yet')"
echo ""

echo "5. Recent Trades:"
curl -s http://localhost:9000/api/trades?limit=5 | python3 -c "import json, sys; trades=json.load(sys.stdin); [print(f\"   {t['timestamp'][11:19]} {t['side']} {t['quantity']:.6f} {t['symbol']} @ \${t['price']:.2f}\") for t in trades] if trades else print('   No trades yet')"
echo ""

echo "========================================="
echo "For detailed diagnostics run:"
echo "  source venv/bin/activate && python test_signal_execution.py"
echo "========================================="
