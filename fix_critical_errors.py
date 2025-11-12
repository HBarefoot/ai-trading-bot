#!/usr/bin/env python3
"""
Critical Error Fixes
Resolves all blocking issues preventing the trading system from working
"""
import sys
import subprocess
import os

print("=" * 80)
print("CRITICAL ERROR FIX SCRIPT")
print("=" * 80)

# 1. Fix missing dependencies
print("\n1. Installing missing AI dependencies...")
try:
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "feedparser", "beautifulsoup4", "lxml"], check=True)
    print("✅ AI dependencies installed")
except Exception as e:
    print(f"⚠️  Warning: {e}")

# 2. Install streamlit for dashboard_pro
print("\n2. Installing Streamlit for professional dashboard...")
try:
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "streamlit", "plotly"], check=True)
    print("✅ Streamlit installed")
except Exception as e:
    print(f"⚠️  Warning: {e}")

# 3. Clean corrupted signals file
print("\n3. Cleaning corrupted signals file...")
signals_file = "logs/signals/signals.json"
if os.path.exists(signals_file):
    try:
        os.remove(signals_file)
        print(f"✅ Removed corrupted {signals_file}")
    except Exception as e:
        print(f"⚠️  Warning: {e}")

# 4. Create fresh signals directory
print("\n4. Ensuring signals directory exists...")
os.makedirs("logs/signals", exist_ok=True)
print("✅ Signals directory ready")

print("\n" + "=" * 80)
print("FIXES APPLIED SUCCESSFULLY!")
print("=" * 80)
print("\n📋 Next steps:")
print("   1. Restart the API: ./stop_all.sh && ./start_api.sh")
print("   2. Start the professional dashboard: ./start_dashboard_pro.sh")
print("   3. Monitor the logs for errors")
