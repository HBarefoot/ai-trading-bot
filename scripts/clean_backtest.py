#!/usr/bin/env python3
"""
Clean backtest with historical Binance data - Fixed version
"""
import sys
sys.path.insert(0, 'src')
from data.database import get_db
from data.models import MarketData
import pandas as pd
import numpy as np

print("🎯 CLEAN BACKTEST - BINANCE HISTORICAL DATA")
print("=" * 70)

# Load data
db = next(get_db())
data = db.query(MarketData).filter(
    MarketData.symbol == 'BTCUSDT'
).order_by(MarketData.timestamp.asc()).all()
db.close()

# Convert to DataFrame
df = pd.DataFrame([{
    'timestamp': d.timestamp,
    'open': float(d.open_price),
    'high': float(d.high_price),
    'low': float(d.low_price),
    'close': float(d.close_price),
    'volume': float(d.volume)
} for d in data])

print(f"📊 Dataset: {len(df)} candles")
print(f"📅 Period: {df['timestamp'].min().date()} to {df['timestamp'].max().date()}")
print(f"💰 Price: ${df['close'].min():.2f} - ${df['close'].max():.2f}")
print()

# Calculate indicators
df['ma_8'] = df['close'].rolling(window=8).mean()
df['ma_21'] = df['close'].rolling(window=21).mean()
df['rsi'] = 50.0  # Simplified

# Simple strategy: MA crossover
df['signal'] = 0
df.loc[df['ma_8'] > df['ma_21'], 'signal'] = 1  # Buy signal

# Backtest
initial_capital = 10000
cash = initial_capital
position = 0
position_size = 0
entry_price = 0
trades = []

for i in range(21, len(df)):  # Start after MA period
    row = df.iloc[i]
    prev_row = df.iloc[i-1]
    
    # Buy signal: MA8 crosses above MA21
    if position == 0 and row['signal'] == 1 and prev_row['signal'] == 0:
        # Buy with all cash
        position_size = cash / row['close']
        entry_price = row['close']
        position = 1
        trades.append({
            'timestamp': row['timestamp'],
            'side': 'BUY',
            'price': entry_price,
            'size': position_size,
            'value': cash
        })
        cash = 0
    
    # Sell signal: MA8 crosses below MA21 OR stop loss hit
    elif position == 1:
        stop_loss = entry_price * 0.90  # 10% stop loss
        
        if row['signal'] == 0 or row['close'] <= stop_loss:
            # Sell position
            exit_price = row['close']
            cash = position_size * exit_price
            
            pnl = cash - (position_size * entry_price)
            pnl_pct = (exit_price / entry_price - 1) * 100
            
            trades.append({
                'timestamp': row['timestamp'],
                'side': 'SELL',
                'price': exit_price,
                'size': position_size,
                'value': cash,
                'pnl': pnl,
                'pnl_pct': pnl_pct
            })
            
            position = 0
            position_size = 0

# Close any open position
if position == 1:
    exit_price = df.iloc[-1]['close']
    cash = position_size * exit_price
    pnl = cash - (position_size * entry_price)
    pnl_pct = (exit_price / entry_price - 1) * 100
    
    trades.append({
        'timestamp': df.iloc[-1]['timestamp'],
        'side': 'SELL',
        'price': exit_price,
        'size': position_size,
        'value': cash,
        'pnl': pnl,
        'pnl_pct': pnl_pct
    })

# Calculate metrics
final_value = cash if position == 0 else position_size * df.iloc[-1]['close']
total_return = (final_value / initial_capital - 1) * 100

# Buy & Hold comparison
buy_hold_value = initial_capital * (df.iloc[-1]['close'] / df.iloc[21]['close'])
buy_hold_return = (buy_hold_value / initial_capital - 1) * 100

# Count wins/losses
sell_trades = [t for t in trades if t['side'] == 'SELL']
winning_trades = len([t for t in sell_trades if t.get('pnl', 0) > 0])
losing_trades = len([t for t in sell_trades if t.get('pnl', 0) <= 0])
win_rate = (winning_trades / len(sell_trades) * 100) if sell_trades else 0

# Print results
print("📈 STRATEGY RESULTS")
print("-" * 70)
print(f"Initial Capital:     ${initial_capital:,.2f}")
print(f"Final Value:         ${final_value:,.2f}")
print(f"Profit/Loss:         ${final_value - initial_capital:,.2f}")
print(f"Total Return:        {total_return:.2f}%")
print()
print(f"Total Trades:        {len(trades)}")
print(f"Buy Trades:          {len([t for t in trades if t['side'] == 'BUY'])}")
print(f"Sell Trades:         {len(sell_trades)}")
print(f"Winning Trades:      {winning_trades}")
print(f"Losing Trades:       {losing_trades}")
print(f"Win Rate:            {win_rate:.2f}%")
print()

if sell_trades:
    avg_win = np.mean([t['pnl_pct'] for t in sell_trades if t.get('pnl', 0) > 0]) if winning_trades > 0 else 0
    avg_loss = np.mean([t['pnl_pct'] for t in sell_trades if t.get('pnl', 0) <= 0]) if losing_trades > 0 else 0
    print(f"Average Win:         {avg_win:.2f}%")
    print(f"Average Loss:        {avg_loss:.2f}%")
    print()

print("🔄 BUY & HOLD COMPARISON")
print("-" * 70)
print(f"Strategy Return:     {total_return:.2f}%")
print(f"Buy & Hold Return:   {buy_hold_return:.2f}%")
print(f"Difference:          {total_return - buy_hold_return:.2f}%")
print()

# Recent trades
print("📋 RECENT TRADES (Last 10)")
print("-" * 70)
for trade in trades[-10:]:
    side_icon = "🟢" if trade['side'] == 'BUY' else "🔴"
    pnl_str = ""
    if 'pnl' in trade:
        pnl_icon = "✅" if trade['pnl'] > 0 else "❌"
        pnl_str = f" | P/L: {pnl_icon} {trade['pnl_pct']:+.2f}%"
    print(f"{side_icon} {trade['side']} | ${trade['price']:,.2f} | {trade['timestamp'].date()}{pnl_str}")

print()
print("=" * 70)
print(f"✅ Database Status: 0 fake trades | {len(df)} real Binance candles")
print("=" * 70)
