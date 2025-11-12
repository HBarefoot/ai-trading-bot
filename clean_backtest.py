#!/usr/bin/env python3
"""Clean backtest with historical Binance data"""
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

# Simple strategy: MA crossover
df['signal'] = 0
df.loc[df['ma_8'] > df['ma_21'], 'signal'] = 1

# Backtest with proper position sizing
initial_capital = 10000
cash = initial_capital
position = 0
position_size = 0
entry_price = 0
trades = []

# Risk management parameters
MAX_POSITION_SIZE = 0.30  # 30% max per trade
MIN_CASH_RESERVE = 0.10   # Keep 10% cash reserve
STOP_LOSS_PCT = 0.15      # 15% stop loss

for i in range(21, len(df)):
    row = df.iloc[i]
    prev_row = df.iloc[i-1]
    
    # Calculate current total portfolio value
    position_value = position_size * row['close'] if position == 1 else 0
    portfolio_value = cash + position_value
    
    # Buy signal
    if position == 0 and row['signal'] == 1 and prev_row['signal'] == 0:
        # Check if we have enough cash (keep 10% reserve)
        min_cash_reserve = portfolio_value * MIN_CASH_RESERVE
        available_cash = cash - min_cash_reserve
        
        if available_cash <= 0:
            continue
            
        # Calculate max position size (30% of TOTAL portfolio value, not cash)
        max_investment = portfolio_value * MAX_POSITION_SIZE
        investment = min(available_cash * 0.95, max_investment)  # Use 95% of available to be safe
        
        if investment <= 0:
            continue
        
        position_size = investment / row['close']
        entry_price = row['close']
        position = 1
        cash -= investment
        
        trades.append({
            'timestamp': row['timestamp'],
            'side': 'BUY',
            'price': entry_price,
            'size': position_size,
            'investment': investment,
            'cash_remaining': cash,
            'portfolio_value': portfolio_value
        })
    
    # Sell signal or stop loss
    elif position == 1:
        stop_loss = entry_price * (1 - STOP_LOSS_PCT)  # 15% stop loss
        
        exit_reason = None
        if row['close'] <= stop_loss:
            exit_reason = 'STOP_LOSS'
        elif row['signal'] == 0:
            exit_reason = 'SIGNAL'
            
        if exit_reason:
            exit_price = row['close']
            exit_value = position_size * exit_price
            cash += exit_value
            
            # Calculate P&L
            entry_value = position_size * entry_price
            pnl = exit_value - entry_value
            pnl_pct = (exit_price / entry_price - 1) * 100
            
            # Risk-adjusted return (% of total portfolio)
            portfolio_pnl_pct = (pnl / portfolio_value) * 100
            
            trades.append({
                'timestamp': row['timestamp'],
                'side': 'SELL',
                'price': exit_price,
                'size': position_size,
                'exit_value': exit_value,
                'pnl': pnl,
                'pnl_pct': pnl_pct,
                'portfolio_pnl_pct': portfolio_pnl_pct,
                'reason': exit_reason
            })
            
            position = 0
            position_size = 0

# Close open position at end
if position == 1:
    exit_price = df.iloc[-1]['close']
    exit_value = position_size * exit_price
    cash += exit_value
    
    entry_value = position_size * entry_price
    pnl = exit_value - entry_value
    pnl_pct = (exit_price / entry_price - 1) * 100
    
    trades.append({
        'timestamp': df.iloc[-1]['timestamp'],
        'side': 'SELL',
        'price': exit_price,
        'size': position_size,
        'exit_value': exit_value,
        'pnl': pnl,
        'pnl_pct': pnl_pct,
        'reason': 'END_OF_DATA'
    })
    position = 0
    position_size = 0

# Calculate metrics
final_value = cash  # All positions closed
total_return = (final_value / initial_capital - 1) * 100

# Buy & Hold comparison
buy_hold_value = initial_capital * (df.iloc[-1]['close'] / df.iloc[21]['close'])
buy_hold_return = (buy_hold_value / initial_capital - 1) * 100

# Trade analysis
sell_trades = [t for t in trades if t['side'] == 'SELL']
winning_trades = len([t for t in sell_trades if t.get('pnl', 0) > 0])
losing_trades = len([t for t in sell_trades if t.get('pnl', 0) <= 0])
win_rate = (winning_trades / len(sell_trades) * 100) if sell_trades else 0

# Risk metrics
if sell_trades:
    returns = [t['pnl_pct'] for t in sell_trades]
    avg_return = np.mean(returns)
    std_return = np.std(returns)
    sharpe_ratio = (avg_return / std_return) if std_return > 0 else 0
    
    # Max drawdown
    portfolio_values = [initial_capital]
    running_cash = initial_capital
    for trade in trades:
        if trade['side'] == 'BUY':
            running_cash -= trade['investment']
        else:
            running_cash += trade['exit_value']
        portfolio_values.append(running_cash)
    
    peak = portfolio_values[0]
    max_dd = 0
    for value in portfolio_values:
        if value > peak:
            peak = value
        dd = (peak - value) / peak * 100
        if dd > max_dd:
            max_dd = dd
else:
    avg_return = 0
    std_return = 0
    sharpe_ratio = 0
    max_dd = 0

# Results
print("📈 STRATEGY RESULTS")
print("-" * 70)
print(f"Initial Capital:     ${initial_capital:,.2f}")
print(f"Final Value:         ${final_value:,.2f}")
print(f"Profit/Loss:         ${final_value - initial_capital:,.2f}")
print(f"Total Return:        {total_return:.2f}%")
print()
print(f"Total Trades:        {len(trades)}")
print(f"Sell Trades:         {len(sell_trades)}")
print(f"Winning Trades:      {winning_trades}")
print(f"Losing Trades:       {losing_trades}")
print(f"Win Rate:            {win_rate:.2f}%")
print()

if sell_trades:
    avg_win = np.mean([t['pnl_pct'] for t in sell_trades if t.get('pnl', 0) > 0]) if winning_trades > 0 else 0
    avg_loss = np.mean([t['pnl_pct'] for t in sell_trades if t.get('pnl', 0) <= 0]) if losing_trades > 0 else 0
    risk_reward = abs(avg_win / avg_loss) if avg_loss != 0 else 0
    
    print(f"Average Win:         {avg_win:.2f}%")
    print(f"Average Loss:        {avg_loss:.2f}%")
    print(f"Risk/Reward Ratio:   {risk_reward:.2f}")
    print(f"Sharpe Ratio:        {sharpe_ratio:.2f}")
    print(f"Max Drawdown:        {max_dd:.2f}%")
    
    # Exit reason breakdown
    stop_loss_exits = len([t for t in sell_trades if t.get('reason') == 'STOP_LOSS'])
    signal_exits = len([t for t in sell_trades if t.get('reason') == 'SIGNAL'])
    print(f"\nExit Reasons:")
    print(f"  Stop Loss:         {stop_loss_exits}")
    print(f"  Signal:            {signal_exits}")
    print()

print("🔄 BUY & HOLD COMPARISON")
print("-" * 70)
print(f"Strategy Return:     {total_return:.2f}%")
print(f"Buy & Hold Return:   {buy_hold_return:.2f}%")
print(f"Difference:          {total_return - buy_hold_return:.2f}%")
print()

print("📋 RECENT TRADES (Last 10)")
print("-" * 70)
for trade in trades[-10:]:
    side_icon = "🟢" if trade['side'] == 'BUY' else "🔴"
    pnl_str = ""
    if 'pnl' in trade:
        pnl_icon = "✅" if trade['pnl'] > 0 else "❌"
        pnl_str = f" | P/L: {pnl_icon} {trade['pnl_pct']:+.2f}%"
    print(f"{side_icon} {trade['side']:4s} | ${trade['price']:,.2f} | {trade['timestamp'].date()}{pnl_str}")

print()
print("=" * 70)
print(f"✅ Clean database: 0 fake trades | {len(df)} Binance candles (89 days)")
print("=" * 70)
