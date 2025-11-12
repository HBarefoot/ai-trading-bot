#!/usr/bin/env python3
"""Detailed test of Week 2 strategy to see exit reasons and partial exits"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import pandas as pd
from data.database import get_db
from data.models import MarketData
from strategies.optimized_strategy_week2 import Week2Strategy

# Get data
db = next(get_db())
data = pd.read_sql(
    db.query(MarketData).filter(MarketData.symbol == 'BTC/USDT').statement,
    db.bind
)
data = data.sort_values('timestamp').reset_index(drop=True)

print(f"Dataset: {len(data)} records")
print(f"Date range: {data['timestamp'].min()} to {data['timestamp'].max()}")

# Test Week 2 strategy
strategy = Week2Strategy()
result = strategy.backtest(data)

print(f"\n{'='*80}")
print(f"WEEK 2 EXIT STRATEGY - DETAILED RESULTS")
print(f"{'='*80}")
print(f"Win Rate: {result['win_rate']:.2f}%")
print(f"Return: {result['total_return']:.2f}%")
print(f"Max Drawdown: {result['max_drawdown']:.2f}%")
print(f"Volatility: {result['volatility']:.2f}%")
print(f"Avg Profit per Win: {result['avg_profit_per_win']:.2f}%")

# Show all trades
print(f"\n{'='*80}")
print(f"TRADE DETAILS")
print(f"{'='*80}\n")

for i, trade in enumerate(result['trades'], 1):
    print(f"Trade {i}:")
    print(f"  Type: {trade['type']}")
    print(f"  Price: ${trade['price']:,.2f}")
    if 'return' in trade:
        print(f"  Return: {trade['return']:.2f}%")
    if 'reason' in trade:
        print(f"  Exit Reason: {trade['reason']}")
    if 'size' in trade:
        print(f"  Position Size: {trade['size']*100:.0f}%")
    print(f"  Time: {trade['timestamp']}")
    print()

# Exit reason breakdown
print(f"{'='*80}")
print(f"EXIT REASON BREAKDOWN")
print(f"{'='*80}\n")
for reason, count in result['exit_reasons'].items():
    print(f"{reason}: {count}")

print(f"\n{'='*80}")
print("STRATEGY PARAMETERS:")
print(f"{'='*80}")
print(f"ATR Multiplier (Stop): {strategy.atr_multiplier_stop}x")
print(f"ATR Multiplier (TP1): {strategy.atr_multiplier_tp1}x (1.5:1 R/R)")
print(f"ATR Multiplier (TP2): {strategy.atr_multiplier_tp2}x (2:1 R/R)")
print(f"Trailing Activation: {strategy.trailing_activation*100}% profit")
print(f"Trailing Stop: {strategy.trailing_percentage*100}% below peak")
print(f"Partial Exit: {strategy.partial_exit_percentage*100}% at TP1")
