#!/usr/bin/env python3
"""
Quick comparison: Week 2 v2 with different RSI thresholds
Tests RSI 70, 75, 80, and NO RSI exit
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from strategies.optimized_strategy_week2_v2 import OptimizedStrategyWeek2V2
from data.database import get_db

def test_rsi_thresholds():
    """Test different RSI overbought thresholds"""
    db = next(get_db())
    
    print("\n" + "="*80)
    print("WEEK 2 v2 - RSI THRESHOLD OPTIMIZATION")
    print("="*80)
    print("\nTesting: How much should we relax RSI to activate TP targets?\n")
    
    results = []
    
    for rsi_threshold in [70, 75, 80, 999]:  # 999 = effectively no RSI exit
        print(f"\n📊 Testing with RSI overbought = {rsi_threshold if rsi_threshold < 999 else 'DISABLED'}...")
        
        strategy = OptimizedStrategyWeek2V2()
        strategy.rsi_overbought = rsi_threshold
        
        result = strategy.backtest(db, days=90)
        
        label = f"RSI {rsi_threshold}" if rsi_threshold < 999 else "NO RSI Exit"
        results.append((label, result))
        
        print(f"   Trades: {result.get('total_trades', 0)}")
        print(f"   Win Rate: {result.get('win_rate', 0):.2%}")
        print(f"   Return: {result.get('total_return', 0):+.2%}")
        if 'exit_reasons' in result:
            print(f"   Exits: {result['exit_reasons']}")
    
    # Comparison table
    print("\n" + "="*80)
    print("COMPARISON TABLE")
    print("="*80)
    print(f"{'RSI Threshold':<20} {'Trades':<10} {'Win Rate':<12} {'Return':<12} {'TP1 Hits':<10}")
    print("-"*80)
    
    for label, result in results:
        if 'error' not in result:
            tp1_hits = result.get('exit_reasons', {}).get('TP1_HIT', 0)
            print(f"{label:<20} {result['total_trades']:<10} {result['win_rate']:<12.2%} "
                  f"{result['total_return']:<12.2%} {tp1_hits:<10}")
    
    # Detailed exit analysis
    print("\n" + "="*80)
    print("EXIT REASON BREAKDOWN")
    print("="*80)
    
    for label, result in results:
        if 'error' not in result and result.get('total_trades', 0) > 0:
            print(f"\n{label}:")
            for reason, count in result.get('exit_reasons', {}).items():
                print(f"  {reason}: {count}")
    
    # Recommendation
    print("\n" + "="*80)
    print("RECOMMENDATION")
    print("="*80)
    
    best_result = max(results, key=lambda x: x[1].get('total_return', 0) if 'error' not in x[1] else -999)
    best_label = best_result[0]
    best_return = best_result[1].get('total_return', 0)
    tp1_count = best_result[1].get('exit_reasons', {}).get('TP1_HIT', 0)
    
    print(f"\n🏆 Best performer: {best_label}")
    print(f"   Return: {best_return:+.2%}")
    print(f"   TP1 Hits: {tp1_count}")
    
    if tp1_count > 0:
        print("\n✅ SUCCESS! Partial exits are working!")
        print(f"   Recommended setting: {best_label}")
    else:
        print("\n⚠️  TP1 targets still not hitting")
        print("   Need to either:")
        print("   1. Lower TP1 target (2.5 ATR → 2.0 ATR)")
        print("   2. Remove RSI exit entirely")
        print("   3. Accept that current market doesn't have big enough moves")


if __name__ == "__main__":
    test_rsi_thresholds()
