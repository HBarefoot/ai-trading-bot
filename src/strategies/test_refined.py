#!/usr/bin/env python3
"""Quick test of refined strategy"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import pandas as pd
from data.database import get_db
from data.models import MarketData
from strategies.optimized_strategy_week1_refined import Week1RefinedStrategy

# Get data
db = next(get_db())
data = pd.read_sql(
    db.query(MarketData).filter(MarketData.symbol == 'BTC/USDT').statement,
    db.bind
)
data = data.sort_values('timestamp').reset_index(drop=True)

print(f"Dataset: {len(data)} records")
print(f"Date range: {data['timestamp'].min()} to {data['timestamp'].max()}")

# Test refined strategy
strategy = Week1RefinedStrategy()
result = strategy.backtest(data)

print(f"\nWeek 1 REFINED Results:")
print(f"Win Rate: {result['win_rate']:.2f}%")
print(f"Return: {result['total_return']:.2f}%")
print(f"Max Drawdown: {result['max_drawdown']:.2f}%")
print(f"Volatility: {result['volatility']:.2f}%")

# Count trades
sell_trades = [t for t in result['trades'] if t['type'] == 'SELL']
print(f"Total Trades: {len(sell_trades)}")
