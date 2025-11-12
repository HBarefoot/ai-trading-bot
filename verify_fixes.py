#!/usr/bin/env python3
"""
Verify All Critical Fixes Are Working
Quick diagnostic to confirm all issues are resolved
"""
import sys
import os
import requests
import time
from datetime import datetime

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(project_root, 'src'))

print("=" * 80)
print("🔍 VERIFYING CRITICAL FIXES")
print("=" * 80)
print()

# Colors
GREEN = '\033[0;32m'
RED = '\033[0;31m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
NC = '\033[0m'  # No Color

def check_api():
    """Check if API is responding"""
    print(f"{BLUE}1. Checking API Connection...{NC}")
    try:
        response = requests.get('http://localhost:9000/api/status', timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"   {GREEN}✓ API is responding{NC}")
            print(f"   Trading Engine: {data.get('trading_engine', 'unknown')}")
            print(f"   Mode: {data.get('mode', 'unknown')}")
            print(f"   Exchange: {data.get('exchange', 'unknown')}")
            print(f"   Data Feed: {data.get('data_feed', 'unknown')}")
            return True, data
        else:
            print(f"   {RED}✗ API returned status {response.status_code}{NC}")
            return False, None
    except requests.exceptions.ConnectionError:
        print(f"   {RED}✗ Cannot connect to API (not running?){NC}")
        print(f"   {YELLOW}→ Run: ./start_api.sh{NC}")
        return False, None
    except Exception as e:
        print(f"   {RED}✗ Error: {e}{NC}")
        return False, None

def check_portfolio():
    """Check portfolio status"""
    print(f"\n{BLUE}2. Checking Portfolio...{NC}")
    try:
        response = requests.get('http://localhost:9000/api/portfolio', timeout=5)
        if response.status_code == 200:
            data = response.json()
            cash = data.get('cash_balance', 0)
            positions = len(data.get('positions', []))
            total_value = data.get('portfolio_value', 0)
            
            print(f"   {GREEN}✓ Portfolio accessible{NC}")
            print(f"   Cash Balance: ${cash:,.2f}")
            print(f"   Open Positions: {positions}")
            print(f"   Total Portfolio Value: ${total_value:,.2f}")
            
            if cash == 0:
                print(f"   {YELLOW}⚠️  WARNING: Cash balance is $0 (expected $10,000){NC}")
                print(f"   {YELLOW}→ Portfolio may need reinitialization{NC}")
                return True, True  # API works, but has warning
            else:
                return True, False
        else:
            print(f"   {RED}✗ Portfolio endpoint error{NC}")
            return False, False
    except Exception as e:
        print(f"   {RED}✗ Error: {e}{NC}")
        return False, False

def check_signals():
    """Check signal generation"""
    print(f"\n{BLUE}3. Checking Signal Generation...{NC}")
    try:
        response = requests.get('http://localhost:9000/api/signals', timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data:
                print(f"   {GREEN}✓ Signals are being generated{NC}")
                print(f"   Active Symbols: {len(data)}")
                for symbol_data in data[:3]:  # Show first 3
                    symbol = symbol_data.get('symbol', 'N/A')
                    signal = symbol_data.get('signal', 0)
                    print(f"   - {symbol}: {signal:.2f}")
                return True
            else:
                print(f"   {YELLOW}⚠️  No signals yet (engine might be starting){NC}")
                return True
        else:
            print(f"   {RED}✗ Signals endpoint error{NC}")
            return False
    except Exception as e:
        print(f"   {RED}✗ Error: {e}{NC}")
        return False

def check_candles():
    """Check if candles are being stored"""
    print(f"\n{BLUE}4. Checking Candle Data...{NC}")
    try:
        response = requests.get('http://localhost:9000/api/candles/BTCUSDT?limit=10', timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                print(f"   {GREEN}✓ Candle data available{NC}")
                print(f"   BTC Candles: {len(data)}")
                if len(data) >= 10:
                    print(f"   {GREEN}✓ Enough data for charts{NC}")
                else:
                    print(f"   {YELLOW}⚠️  Only {len(data)} candles (need ~10 for charts){NC}")
                    print(f"   {YELLOW}→ Wait 10-15 more minutes{NC}")
                return True
            else:
                print(f"   {YELLOW}⚠️  No candles yet (data collection starting){NC}")
                print(f"   {YELLOW}→ Wait 10-15 minutes for first candles{NC}")
                return True
        else:
            print(f"   {RED}✗ Candles endpoint error{NC}")
            return False
    except Exception as e:
        print(f"   {RED}✗ Error: {e}{NC}")
        return False

def check_database():
    """Check database connection"""
    print(f"\n{BLUE}5. Checking Database Connection...{NC}")
    try:
        from data.database import test_connection
        if test_connection():
            print(f"   {GREEN}✓ Database connected{NC}")
            return True
        else:
            print(f"   {RED}✗ Database connection failed{NC}")
            print(f"   {YELLOW}→ Check PostgreSQL is running{NC}")
            return False
    except Exception as e:
        print(f"   {RED}✗ Error: {e}{NC}")
        return False

def main():
    """Run all checks"""
    results = []
    warnings = []
    
    # Run checks
    api_ok, status_data = check_api()
    results.append(('API Connection', api_ok))
    
    portfolio_ok, portfolio_warning = check_portfolio()
    results.append(('Portfolio', portfolio_ok))
    if portfolio_warning:
        warnings.append('Cash balance is $0')
    
    signals_ok = check_signals()
    results.append(('Signal Generation', signals_ok))
    
    candles_ok = check_candles()
    results.append(('Candle Data', candles_ok))
    
    db_ok = check_database()
    results.append(('Database', db_ok))
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 VERIFICATION SUMMARY")
    print("=" * 80)
    
    all_passed = all(result[1] for result in results)
    
    for name, passed in results:
        status = f"{GREEN}✓ PASS{NC}" if passed else f"{RED}✗ FAIL{NC}"
        print(f"   {name:.<40} {status}")
    
    print()
    
    if all_passed and not warnings:
        print(f"{GREEN}🎉 ALL SYSTEMS OPERATIONAL!{NC}")
        print()
        print("Next Steps:")
        print("  1. Open dashboard: http://localhost:8501")
        print("  2. Verify System Status shows: 🟢 ACTIVE")
        print("  3. Wait for charts to populate (10-15 min)")
        print("  4. Monitor for first trade (3-7 days expected)")
    elif all_passed and warnings:
        print(f"{YELLOW}⚠️  SYSTEMS OPERATIONAL WITH WARNINGS{NC}")
        print()
        print("Warnings:")
        for warning in warnings:
            print(f"  • {warning}")
        print()
        print("Action Required:")
        print("  1. Check portfolio initialization")
        print("  2. Verify logs for errors")
    else:
        print(f"{RED}❌ SOME SYSTEMS FAILED{NC}")
        print()
        print("Action Required:")
        if not api_ok:
            print("  1. Start API: ./start_api.sh")
        if not db_ok:
            print("  2. Start database: docker-compose up -d")
        print("  3. Check logs for errors")
    
    print()
    print("=" * 80)
    
    return all_passed

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nVerification interrupted.")
        sys.exit(1)
