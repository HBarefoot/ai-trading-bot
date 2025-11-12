#!/usr/bin/env python3
"""
Validation script to test all fixes are working
"""
import requests
import time
import json
from datetime import datetime

def test_api_connection():
    """Test API is running and responding"""
    print("🔍 Testing API connection...")
    try:
        response = requests.get('http://localhost:9000/api/status', timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ API responding")
            print(f"   ℹ️  Engine status: {data.get('trading_engine', 'unknown')}")
            print(f"   ℹ️  Mode: {data.get('mode', 'unknown')}")
            return True
        else:
            print(f"   ❌ API returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ API not responding: {e}")
        return False

def test_portfolio():
    """Test portfolio endpoint"""
    print("\n💼 Testing portfolio endpoint...")
    try:
        response = requests.get('http://localhost:9000/api/portfolio', timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Portfolio responding")
            print(f"   ℹ️  Total value: ${data.get('total_value', 0):,.2f}")
            print(f"   ℹ️  Cash: ${data.get('cash_balance', 0):,.2f}")
            return True
        else:
            print(f"   ❌ Portfolio returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Portfolio error: {e}")
        return False

def test_signals():
    """Test signals endpoint"""
    print("\n📊 Testing signals endpoint...")
    try:
        response = requests.get('http://localhost:9000/api/signals', timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Signals responding")
            if data:
                print(f"   ℹ️  Active signals: {len(data)}")
                for signal in data[:3]:  # Show first 3
                    print(f"      {signal.get('symbol')}: {signal.get('signal_type')} @ ${signal.get('price', 0):,.2f}")
            else:
                print(f"   ℹ️  No signals yet (engine building data)")
            return True
        else:
            print(f"   ❌ Signals returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Signals error: {e}")
        return False

def test_candles():
    """Test candles endpoint"""
    print("\n📈 Testing candles endpoint...")
    try:
        response = requests.get('http://localhost:9000/api/candles/BTCUSDT?limit=5', timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Candles responding")
            print(f"   ℹ️  Candles available: {len(data)}")
            if len(data) > 0:
                latest = data[-1]
                print(f"      Latest: ${latest.get('close', 0):,.2f} @ {latest.get('timestamp', 'unknown')}")
            else:
                print(f"   ℹ️  No candles yet (accumulating data, wait 10-15 min)")
            return True
        else:
            print(f"   ❌ Candles returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Candles error: {e}")
        return False

def test_ai_status():
    """Test AI status endpoint"""
    print("\n🤖 Testing AI status...")
    try:
        response = requests.get('http://localhost:9000/api/ai/status', timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ AI module responding")
            print(f"   ℹ️  Sentiment analyzer: {'ready' if data.get('sentiment_analyzer') else 'not ready'}")
            if 'sentiment_cache' in data:
                cache = data['sentiment_cache']
                print(f"   ℹ️  Cached sentiments: {len(cache)}")
            return True
        else:
            print(f"   ❌ AI returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"   ⚠️  AI endpoint not available (may need dependencies)")
        return False

def main():
    print("=" * 70)
    print("🔍 SYSTEM VALIDATION - TESTING ALL FIXES")
    print("=" * 70)
    print()
    
    results = []
    
    # Test each component
    results.append(("API Connection", test_api_connection()))
    results.append(("Portfolio", test_portfolio()))
    results.append(("Signals", test_signals()))
    results.append(("Candles", test_candles()))
    results.append(("AI Status", test_ai_status()))
    
    # Summary
    print()
    print("=" * 70)
    print("📊 VALIDATION SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {name:.<30} {status}")
    
    print()
    print(f"Total: {passed}/{total} tests passed")
    
    if passed == total:
        print()
        print("🎉 ALL TESTS PASSED!")
        print()
        print("Next steps:")
        print("1. Open dashboard: http://localhost:8501")
        print("2. Click 'Start' button if engine is not active")
        print("3. Wait 10-15 minutes for candles to accumulate")
        print("4. Monitor 'Signals' tab for buy opportunities")
    else:
        print()
        print("⚠️  Some tests failed. Check that:")
        print("   • API is running: ./start_api.sh")
        print("   • No errors in API console")
        print("   • Database is accessible")
    
    print()
    print("=" * 70)

if __name__ == "__main__":
    main()
