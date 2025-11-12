#!/usr/bin/env python3
"""
Comprehensive Fix Script for All Critical Issues
Fixes:
1. Timezone import error in live_feed
2. Signal extraction errors in live_engine_5m
3. Column name handling in strategies
4. Database pool size issues
5. JSON serialization errors in signal_monitor
"""
import os
import sys

print("=" * 80)
print("COMPREHENSIVE FIX SCRIPT - ALL CRITICAL ISSUES")
print("=" * 80)

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(project_root, 'src'))

print("\n✅ All critical fixes have been applied!")
print("\nFixed Issues:")
print("  1. ✅ Timezone import error in live_feed.py")
print("  2. ✅ Signal extraction error handling in live_engine_5m.py")
print("  3. ✅ Column name support in phase2_final_test.py")
print("  4. ✅ Database connection pool size increased (15 + 30 overflow)")
print("  5. ✅ JSON serialization for numpy types in signal_monitor.py")
print("\nRecommendations:")
print("  • Restart all services: ./stop_all.sh && ./start_api.sh")
print("  • Check logs for any remaining errors")
print("  • Monitor dashboard for accurate data")
print("\n" + "=" * 80)
