"""
Test Script to Diagnose Signal Execution Issues
"""
import asyncio
import sys
import os
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from trading.live_engine_5m import get_trading_engine_5m
from trading.signal_monitor import get_signal_monitor
from data.live_feed import get_data_feed_manager

async def diagnose_system():
    """Run diagnostics on the trading system"""
    
    print("=" * 80)
    print("TRADING SYSTEM DIAGNOSTICS")
    print("=" * 80)
    print(f"Time: {datetime.now()}\n")
    
    # Get trading engine
    engine = get_trading_engine_5m()
    print(f"1. Trading Engine Status:")
    print(f"   - Running: {engine.running}")
    print(f"   - Paper Trading: {engine.paper_trading}")
    print(f"   - Symbols: {engine.symbols}")
    print(f"   - Update Interval: {engine.update_interval}s")
    
    # Check portfolio
    print(f"\n2. Portfolio Status:")
    portfolio = engine.portfolio
    print(f"   - Initial Balance: ${portfolio.initial_balance:,.2f}")
    print(f"   - Cash Balance: ${portfolio.cash_balance:,.2f}")
    print(f"   - Portfolio Value: ${portfolio.get_portfolio_value():,.2f}")
    print(f"   - Open Positions: {len(portfolio.positions)}")
    print(f"   - Total Trades: {len(portfolio.trades)}")
    
    # Show position details
    if portfolio.positions:
        print(f"\n   Open Positions:")
        for symbol, pos in portfolio.positions.items():
            print(f"      - {symbol}: {pos.amount:.6f} @ ${pos.entry_price:.2f}")
    
    # Show recent trades
    if portfolio.trades:
        print(f"\n   Recent Trades (last 5):")
        for trade in portfolio.trades[-5:]:
            print(f"      - {trade.timestamp.strftime('%H:%M:%S')} {trade.side} {trade.amount:.6f} {trade.symbol} @ ${trade.price:.2f}")
    
    # Check signal monitor
    print(f"\n3. Signal Monitor:")
    signal_monitor = get_signal_monitor()
    current_signals = signal_monitor.get_current_signals()
    
    if current_signals:
        print(f"   Current Signals:")
        for symbol, state in current_signals.items():
            print(f"      - {symbol}: {state.signal_type.value} @ ${state.price:.2f} (RSI: {state.rsi:.1f if state.rsi else 'N/A'})")
    else:
        print(f"   No signals detected yet")
    
    # Show recent alerts
    recent_alerts = signal_monitor.get_recent_alerts(limit=10)
    if recent_alerts:
        print(f"\n   Recent Alerts (last 10):")
        for alert in recent_alerts:
            print(f"      - {alert.timestamp.strftime('%H:%M:%S')} [{alert.priority}] {alert.message}")
    
    # Check performance
    print(f"\n4. Performance Summary:")
    perf = signal_monitor.get_performance_summary()
    print(f"   - Total Trades: {perf['total_trades']}")
    print(f"   - Winning Trades: {perf['winning_trades']}")
    print(f"   - Losing Trades: {perf['losing_trades']}")
    print(f"   - Win Rate: {perf['win_rate']:.1f}%")
    print(f"   - Current Streak: {perf['current_streak']}")
    
    # Check data feed
    print(f"\n5. Data Feed Status:")
    print(f"   ℹ️  Note: Data feed is managed by the API backend")
    print(f"   ℹ️  This diagnostic script connects to the API, not directly to data feed")
    
    try:
        # Try to get prices from the API instead
        import requests
        response = requests.get("http://localhost:9000/api/live-data", timeout=5)
        if response.status_code == 200:
            api_data = response.json()
            # API returns: {"timestamp": "...", "prices": {"BTCUSDT": {...}, ...}}
            if 'prices' in api_data:
                prices = api_data['prices']
                print(f"   Live prices from API (Updated: {api_data.get('timestamp', 'N/A')}):")
                for symbol, data in prices.items():
                    if isinstance(data, dict) and 'price' in data:
                        price = data['price']
                        change = data.get('change_24h', 0)
                        change_str = f"+{change:.2f}%" if change > 0 else f"{change:.2f}%"
                        print(f"      - {symbol}: ${price:.2f} ({change_str} 24h)")
            else:
                print(f"   ⚠️  Unexpected API response format")
        else:
            print(f"   ⚠️  API returned status code: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"   ⚠️  API not responding. Make sure the API is running: ./start_api.sh")
        print(f"       Error: {e}")
    except Exception as e:
        print(f"   ⚠️  Error parsing API response: {e}")
    
    # Check candle aggregator
    print(f"\n6. Candle Aggregator:")
    if engine.candle_aggregator:
        print(f"   Status: Active")
        for symbol in engine.symbols:
            df = engine.candle_aggregator.get_candles_as_dataframe(symbol, limit=10)
            print(f"   - {symbol}: {len(df)} candles available")
            if len(df) > 0:
                latest = df.iloc[-1]
                print(f"      Latest: ${latest['close']:.2f} @ {latest.name}")
    else:
        print(f"   Status: Not initialized")
        print(f"   ℹ️  Candle aggregator starts when trading engine starts")
    
    
    # Check last signals
    print(f"\n7. Last Signal States:")
    if hasattr(engine, 'last_signals') and engine.last_signals:
        for symbol, signal in engine.last_signals.items():
            signal_type = "BUY" if signal > 0 else "SELL" if signal < 0 else "HOLD"
            print(f"   - {symbol}: {signal_type} ({signal})")
    else:
        print(f"   No previous signals tracked")
    
    print("\n" + "=" * 80)
    print("DIAGNOSIS COMPLETE")
    print("=" * 80)
    
    # Provide recommendations
    print("\n📋 RECOMMENDATIONS:")
    
    if not engine.running:
        print("   ⚠️  Trading engine is not running.")
        print("   💡 The trading engine is started automatically by the API backend")
        print("   💡 Check if the API is running and if trading was started via API")
        print("   💡 To check: curl http://localhost:9000/api/status")
    else:
        print("   ✅ Trading engine is running!")
    
    if len(portfolio.positions) == 0 and portfolio.cash_balance > portfolio.initial_balance * 0.1:
        print("   ℹ️  No open positions. Waiting for buy signals...")
    
    if portfolio.cash_balance < portfolio.initial_balance * 0.1:
        print("   ⚠️  Low cash balance. May not be able to open new positions.")
    
    print("\n💡 IMPORTANT NOTES:")
    print("   • Paper Trading: Simulated orders, real Binance.US market data")
    print("   • Data Source: Live WebSocket from Binance.US (via API backend)")
    print("   • The API backend (port 9000) manages the WebSocket connection")
    print("   • This diagnostic script connects to the API, not directly to Binance")
    print("   • The trading engine runs inside the API backend process")
    print("\n💡 TO START TRADING:")
    print("   1. Make sure API is running: ./start_api.sh")
    print("   2. Start trading via API: curl -X POST http://localhost:9000/api/trading/start")
    print("   3. Or use the dashboard to start/stop trading")

if __name__ == "__main__":
    asyncio.run(diagnose_system())
