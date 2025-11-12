#!/usr/bin/env python3
"""
FIXED Clean Backtest with Proper Position Sizing
Critical Bug Fix: Using 30% max position size (not 100%)
"""
import sys
sys.path.insert(0, 'src')
from data.database import get_db
from data.models import MarketData
import pandas as pd
import numpy as np

print("🎯 FIXED BACKTEST - PROPER POSITION SIZING")
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
print(f"💰 Price Range: ${df['close'].min():.2f} - ${df['close'].max():.2f}")
print()

# Calculate indicators
df['ma_8'] = df['close'].rolling(window=8).mean()
df['ma_21'] = df['close'].rolling(window=21).mean()

# Simple strategy: MA crossover
df['signal'] = 0
df.loc[df['ma_8'] > df['ma_21'], 'signal'] = 1

# Backtest with PROPER position sizing
initial_capital = 10000
cash = initial_capital
position_qty = 0  # Quantity of BTC held
entry_price = 0
trades = []

# Risk management parameters
MAX_POSITION_PCT = 0.30  # Max 30% of portfolio per trade
STOP_LOSS_PCT = 0.15      # 15% stop loss

print(f"⚙️  Configuration:")
print(f"   Initial Capital: ${initial_capital:,.2f}")
print(f"   Max Position Size: {MAX_POSITION_PCT*100}%")
print(f"   Stop Loss: {STOP_LOSS_PCT*100}%")
print()

for i in range(21, len(df)):
    row = df.iloc[i]
    prev_row = df.iloc[i-1]
    
    # Calculate current portfolio value
    position_value = position_qty * row['close']
    total_value = cash + position_value
    
    # Buy signal (new position)
    if position_qty == 0 and row['signal'] == 1 and prev_row['signal'] == 0:
        # Calculate position size: 30% of CURRENT portfolio value
        position_dollar_size = total_value * MAX_POSITION_PCT
        
        # Can't invest more than available cash
        if position_dollar_size > cash:
            position_dollar_size = cash * 0.95  # Leave 5% cash buffer
        
        if position_dollar_size > 100:  # Minimum $100 trade
            position_qty = position_dollar_size / row['close']
            entry_price = row['close']
            cash -= position_dollar_size
            
            trades.append({
                'type': 'BUY',
                'timestamp': row['timestamp'],
                'price': entry_price,
                'qty': position_qty,
                'investment': position_dollar_size,
                'portfolio_value': total_value,
                'cash_after': cash
            })
    
    # Sell signal or stop loss
    elif position_qty > 0:
        stop_loss = entry_price * (1 - STOP_LOSS_PCT)
        
        should_exit = False
        exit_reason = None
        
        if row['close'] <= stop_loss:
            should_exit = True
            exit_reason = 'STOP_LOSS'
        elif row['signal'] == 0:
            should_exit = True
            exit_reason = 'SIGNAL'
        
        if should_exit:
            exit_price = row['close']
            exit_value = position_qty * exit_price
            pnl_dollars = exit_value - (position_qty * entry_price)
            pnl_pct = (exit_price / entry_price - 1) * 100
            
            cash += exit_value
            
            trades.append({
                'type': 'SELL',
                'timestamp': row['timestamp'],
                'price': exit_price,
                'qty': position_qty,
                'exit_value': exit_value,
                'pnl_dollars': pnl_dollars,
                'pnl_pct': pnl_pct,
                'reason': exit_reason,
                'portfolio_value': cash + exit_value
            })
            
            position_qty = 0
            entry_price = 0

# Close any remaining position
if position_qty > 0:
    exit_price = df.iloc[-1]['close']
    exit_value = position_qty * exit_price
    pnl_dollars = exit_value - (position_qty * entry_price)
    pnl_pct = (exit_price / entry_price - 1) * 100
    
    cash += exit_value
    
    trades.append({
        'type': 'SELL',
        'timestamp': df.iloc[-1]['timestamp'],
        'price': exit_price,
        'qty': position_qty,
        'exit_value': exit_value,
        'pnl_dollars': pnl_dollars,
        'pnl_pct': pnl_pct,
        'reason': 'END',
        'portfolio_value': cash
    })
    
    position_qty = 0

# Calculate metrics
final_value = cash
total_return_pct = (final_value / initial_capital - 1) * 100
total_profit = final_value - initial_capital

# Buy & Hold
buy_hold_qty = initial_capital / df.iloc[21]['close']
buy_hold_value = buy_hold_qty * df.iloc[-1]['close']
buy_hold_return = (buy_hold_value / initial_capital - 1) * 100

# Trade analysis
buy_trades = [t for t in trades if t['type'] == 'BUY']
sell_trades = [t for t in trades if t['type'] == 'SELL']

winning_trades = [t for t in sell_trades if t['pnl_dollars'] > 0]
losing_trades = [t for t in sell_trades if t['pnl_dollars'] <= 0]

win_rate = (len(winning_trades) / len(sell_trades) * 100) if sell_trades else 0

# Calculate average win/loss
avg_win_pct = np.mean([t['pnl_pct'] for t in winning_trades]) if winning_trades else 0
avg_loss_pct = np.mean([t['pnl_pct'] for t in losing_trades]) if losing_trades else 0
risk_reward = abs(avg_win_pct / avg_loss_pct) if avg_loss_pct != 0 else 0

# Sharpe ratio
returns = [t['pnl_pct'] for t in sell_trades]
avg_return = np.mean(returns) if returns else 0
std_return = np.std(returns) if returns else 1
sharpe = (avg_return / std_return * np.sqrt(252)) if std_return > 0 else 0  # Annualized

# Max drawdown
portfolio_values = [initial_capital]
for trade in trades:
    portfolio_values.append(trade['portfolio_value'])

peak = portfolio_values[0]
max_dd_pct = 0
for value in portfolio_values:
    if value > peak:
        peak = value
    dd = (peak - value) / peak * 100
    if dd > max_dd_pct:
        max_dd_pct = dd

# Results
print("📈 STRATEGY RESULTS")
print("-" * 70)
print(f"Initial Capital:     ${initial_capital:,.2f}")
print(f"Final Value:         ${final_value:,.2f}")
print(f"Total Profit/Loss:   ${total_profit:,.2f}")
print(f"Total Return:        {total_return_pct:+.2f}%")
print()

print(f"📊 TRADE STATISTICS")
print("-" * 70)
print(f"Total Trades:        {len(buy_trades)} entries / {len(sell_trades)} exits")
print(f"Winning Trades:      {len(winning_trades)}")
print(f"Losing Trades:       {len(losing_trades)}")
print(f"Win Rate:            {win_rate:.2f}%")
print()

if sell_trades:
    print(f"💰 PERFORMANCE METRICS")
    print("-" * 70)
    print(f"Average Win:         {avg_win_pct:+.2f}%")
    print(f"Average Loss:        {avg_loss_pct:+.2f}%")
    print(f"Risk/Reward Ratio:   {risk_reward:.2f}:1")
    print(f"Sharpe Ratio:        {sharpe:.2f}")
    print(f"Max Drawdown:        {max_dd_pct:.2f}%")
    print()
    
    # Exit reasons
    stop_losses = len([t for t in sell_trades if t.get('reason') == 'STOP_LOSS'])
    signals = len([t for t in sell_trades if t.get('reason') == 'SIGNAL'])
    print(f"📋 EXIT BREAKDOWN")
    print("-" * 70)
    print(f"Stop Loss Exits:     {stop_losses} ({stop_losses/len(sell_trades)*100:.1f}%)")
    print(f"Signal Exits:        {signals} ({signals/len(sell_trades)*100:.1f}%)")
    print()

print("🔄 BUY & HOLD COMPARISON")
print("-" * 70)
print(f"Strategy Return:     {total_return_pct:+.2f}%")
print(f"Buy & Hold Return:   {buy_hold_return:+.2f}%")
print(f"Alpha (Difference):  {total_return_pct - buy_hold_return:+.2f}%")
print()

# Show recent trades
print("📋 RECENT TRADES (Last 10)")
print("-" * 70)
recent = trades[-20:]  # Last 10 buy/sell pairs
for trade in recent:
    if trade['type'] == 'BUY':
        print(f"🟢 BUY  | ${trade['price']:,.2f} | {trade['timestamp'].strftime('%Y-%m-%d')}")
    else:
        emoji = "✅" if trade['pnl_dollars'] > 0 else "❌"
        print(f"🔴 SELL | ${trade['price']:,.2f} | {trade['timestamp'].strftime('%Y-%m-%d')} | P/L: {emoji} {trade['pnl_pct']:+.2f}%")

print()
print("=" * 70)
print(f"✅ FIXED: Using 30% position sizing (not 100%)")
print(f"✅ Realistic returns: {total_return_pct:+.2f}% over {len(df)} candles")
print("=" * 70)
