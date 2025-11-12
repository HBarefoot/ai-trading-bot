#!/usr/bin/env python3
"""
Test Week 2 v2 Optimized Strategy
Shows if TP targets and trailing stops are now working
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from strategies.optimized_strategy_week2_v2 import OptimizedStrategyWeek2V2
from strategies.optimized_strategy_week2 import Week2Strategy
from data.database import get_db

def test_week2_v2():
    """Test Week 2 v2 Optimized"""
    db = next(get_db())
    
    print("\n" + "="*80)
    print("WEEK 2 v2 OPTIMIZATION TEST")
    print("="*80)
    print("\nChanges in v2:")
    print("  ✅ RSI Overbought: 65 → 70 (allow more profit)")
    print("  ✅ TP1: 3.0 ATR → 2.5 ATR (easier to hit)")
    print("  ✅ TP2: 4.0 ATR → 3.5 ATR (more achievable)")
    print("  ✅ Trailing Activation: 10% → 5% (activate sooner)")
    print("\n" + "="*80)
    
    # Test Week 2 v2 Optimized
    print("\n📊 Testing Week 2 v2 Optimized on 90 days of data...")
    week2_v2 = OptimizedStrategyWeek2V2()
    result_v2 = week2_v2.backtest(db, days=90)
    
    # Print results
    print("\n" + "="*80)
    print("WEEK 2 V2 RESULTS (90 days)")
    print("="*80)
    
    print(f"\n{'Metric':<25} {'Value':<20}")
    print("-"*50)
    print(f"{'Win Rate':<25} {result_v2.get('win_rate', 0):<20.2%}")
    print(f"{'Total Return':<25} {result_v2.get('total_return', 0):<20.2%}")
    print(f"{'Max Drawdown':<25} {result_v2.get('max_drawdown', 0):<20.2%}")
    print(f"{'Volatility':<25} {result_v2.get('volatility', 0):<20.2%}")
    print(f"{'Total Trades':<25} {result_v2.get('total_trades', 0):<20}")
    print(f"{'Avg Profit/Win':<25} {result_v2.get('avg_profit_per_win', 0):<20.2%}")
    
    # Exit reasons
    print("\n" + "="*80)
    print("EXIT REASONS")
    print("="*80)
    
    print("\nWeek 2 v2 Exits:")
    for reason, count in result_v2.get('exit_reasons', {}).items():
        print(f"  {reason}: {count}")
    
    # Detailed trade analysis for Week 2 v2
    print("\n" + "="*80)
    print("WEEK 2 V2 - DETAILED TRADES")
    print("="*80)
    
    if 'trades' in result_v2:
        for i, trade in enumerate(result_v2['trades'], 1):
            if trade['type'] in ['SELL', 'SELL_PARTIAL']:
                partial_tag = " 🎯 PARTIAL EXIT (50%)" if trade['type'] == 'SELL_PARTIAL' else ""
                print(f"\nTrade {i}{partial_tag}:")
                print(f"  Entry:  {trade['entry_time']} @ ${trade['entry_price']:.2f}")
                print(f"  Exit:   {trade['exit_time']} @ ${trade['exit_price']:.2f}")
                print(f"  Return: {trade['profit_pct']:.2f}%")
                print(f"  Reason: {trade['exit_reason']}")
                duration = (trade['exit_time'] - trade['entry_time']).total_seconds() / 3600
                print(f"  Duration: {duration:.1f} hours")
    
    # Key insights
    print("\n" + "="*80)
    print("KEY INSIGHTS")
    print("="*80)
    
    v2_exits = result_v2.get('exit_reasons', {})
    tp1_count = v2_exits.get('TP1_HIT', 0)
    tp2_count = v2_exits.get('TP2_HIT', 0)
    trailing_count = v2_exits.get('TRAILING_STOP', 0)
    rsi_count = v2_exits.get('RSI_OVERBOUGHT', 0)
    
    print(f"\n✨ TP1 Hits: {tp1_count} (target: 40-50% of trades)")
    print(f"✨ TP2 Hits: {tp2_count} (bonus for trending moves)")
    print(f"✨ Trailing Stops: {trailing_count} (protects big wins)")
    print(f"⚠️  RSI Exits: {rsi_count} (still exiting early?)")
    
    if tp1_count > 0:
        print("\n🎉 SUCCESS! TP1 targets are now being hit!")
        print(f"   Partial exits working: {tp1_count} trades took 50% profit at TP1")
    elif rsi_count > 0:
        print("\n⚠️  Still exiting on RSI before TP1")
        print("   May need to relax RSI further (70 → 75) or lower TP1 more")
    
    print(f"\n📈 Total Return: {result_v2.get('total_return', 0):+.2%}")
    print(f"🎯 Win Rate: {result_v2.get('win_rate', 0):.2%}")


if __name__ == "__main__":
    test_week2_v2()
