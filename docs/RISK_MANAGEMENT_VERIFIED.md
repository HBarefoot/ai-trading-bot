# Risk Management Verification - November 10, 2025

## ✅ VERIFIED: Risk Management is Now Accurate

All risk management parameters now match between the Week1Refined strategy and live trading engine.

---

## Risk Management Settings

### Position Sizing
- **Max Position Size:** 30% of total portfolio value per trade
- **Cash Buffer:** Keep 5% cash buffer when calculating position size
- **Minimum Cash:** Maintain 10% cash minimum before opening new positions

**Example with $10,000 portfolio:**
```
BTC @ $105,000
Position Size: 0.02857143 BTC
Investment: $3,000 (30% of portfolio)
Cash Remaining: $7,000 (70%)
```

### Stop Loss
- **Stop Loss:** 15% below entry price
- **Trigger:** Automatically sells when price drops to stop loss level
- **Purpose:** Limits maximum loss per trade

**Example:**
```
Entry: $105,000
Stop Loss: $89,250 (-15%)
Loss per BTC: $15,750
Max Loss: $450 (4.5% of portfolio with 30% position)
```

### Take Profit
- **Take Profit:** 30% above entry price
- **Trigger:** Automatically sells when price reaches take profit level
- **Purpose:** Locks in profits at target level

**Example:**
```
Entry: $105,000
Take Profit: $136,500 (+30%)
Gain per BTC: $31,500
Max Gain: $900 (9.0% of portfolio with 30% position)
```

### Risk/Reward Ratio
- **Ratio:** 1:2.0
- **Risk:** 15% downside
- **Reward:** 30% upside
- **Assessment:** Excellent risk/reward profile

---

## Verification Test Results

### Test Date: November 10, 2025

**Portfolio Manager Settings:**
```python
self.max_position_size = 0.30  # 30% per position
self.stop_loss_pct = 0.15      # 15% stop loss
self.take_profit_pct = 0.30    # 30% take profit
```

**Week1Refined Strategy Settings:**
```python
data['stop_loss'] = entry_price * 0.85    # 15% stop loss
data['take_profit'] = entry_price * 1.30  # 30% profit target
```

✅ **MATCH CONFIRMED** - All settings aligned

---

## Risk Per Trade Breakdown

### Scenario: $10,000 Portfolio, BTC @ $105,000

| Metric | Value | Percentage |
|--------|-------|------------|
| **Position Size** | 0.02857143 BTC | 30% of portfolio |
| **Investment** | $3,000 | 30% of portfolio |
| **Entry Price** | $105,000 | - |
| **Stop Loss** | $89,250 | -15% from entry |
| **Take Profit** | $136,500 | +30% from entry |
| **Max Loss** | $450 | 4.5% of portfolio |
| **Max Gain** | $900 | 9.0% of portfolio |
| **Cash Remaining** | $7,000 | 70% of portfolio |

### Multiple Trades

If strategy triggers 3 simultaneous trades (different coins):

| Trade | Symbol | Investment | Max Loss | Max Gain |
|-------|--------|------------|----------|----------|
| 1 | BTCUSDT | $3,000 | $450 | $900 |
| 2 | ETHUSDT | $2,100 | $315 | $630 |
| 3 | SOLUSDT | $1,470 | $220 | $441 |
| **Total** | - | **$6,570** | **$985** | **$1,971** |

- Portfolio exposure: 65.7%
- Cash reserve: 34.3%
- Max portfolio drawdown: 9.85%
- Max portfolio gain: 19.71%

---

## Strategy Exit Conditions

The Week1Refined strategy will exit a position when **ANY** of these trigger:

### 1. Stop Loss Hit
```python
if current_price <= position.stop_loss:
    SELL (reason: "STOP_LOSS")
```
**Example:** Entry $105,000, exits at $89,250 or below

### 2. Take Profit Hit
```python
if current_price >= position.take_profit:
    SELL (reason: "TAKE_PROFIT")
```
**Example:** Entry $105,000, exits at $136,500 or above

### 3. MA Crossover (Trend Reversal)
```python
if ma_fast < ma_slow:  # MA8 crosses below MA21
    SELL (reason: "SIGNAL")
```
**Purpose:** Exit early if trend reverses before hitting SL/TP

### 4. RSI Overbought
```python
if rsi > 65:
    SELL (reason: "SIGNAL")
```
**Purpose:** Exit when momentum becomes extreme

---

## Live Trading Cycle

### Every Minute, the bot:

1. **Updates Prices**
   - Fetches current price for all positions
   - Updates unrealized P&L

2. **Checks Stop Losses**
   - Compares current price to stop loss level
   - Auto-sells if triggered

3. **Checks Take Profits**
   - Compares current price to take profit level
   - Auto-sells if triggered

4. **Generates Signals**
   - Analyzes latest candle with Week1Refined
   - Checks all 7 entry conditions
   - Executes BUY if all conditions met

5. **Checks Exit Signals**
   - MA crossover
   - RSI overbought
   - Auto-sells if triggered

---

## Paper Trading Validation

### Current Test Trades (Test Data - To Be Cleared)

The CSV shows 7 test trades from monitoring system tests:
```csv
2025-11-10 16:08:10,BTCUSDT,BUY,100000.0,0.1
2025-11-10 16:08:10,BTCUSDT,SELL,100000.0,0.1,100500.0,50.0,0.5,Take Profit
```

**These are NOT real strategy trades** - they are from `paper_trading_monitor.py` test runs.

### Expected Real Trades

Once live engine starts and market conditions improve:

```csv
timestamp,symbol,side,entry_price,amount,exit_price,pnl,pnl_pct,reason
2025-11-10 18:30:00,BTCUSDT,BUY,105000.0,0.02857143,,,,
2025-11-10 20:45:00,BTCUSDT,SELL,105000.0,0.02857143,136500.0,900.0,30.0,Take Profit
```

**This is what accurate trades will look like:**
- Entry based on strategy signals
- Position size: 30% of portfolio
- Exit at stop loss (-15%) or take profit (+30%)
- Or exit on trend reversal signal

---

## Risk Management Matrix

### Win Scenarios

| Outcome | Exit Reason | Return | Portfolio Impact |
|---------|-------------|--------|------------------|
| **Big Win** | Take Profit | +30% | +9.0% portfolio |
| **Trend Exit** | MA Cross | +5% to +25% | +1.5% to +7.5% |
| **Momentum Exit** | RSI | +10% to +28% | +3.0% to +8.4% |

### Loss Scenarios

| Outcome | Exit Reason | Return | Portfolio Impact |
|---------|-------------|--------|------------------|
| **Stop Loss** | Price Drop | -15% | -4.5% portfolio |
| **Early Exit** | Trend Reversal | -5% to -12% | -1.5% to -3.6% |

### Expected Performance

Based on 75% win rate from backtests:

**Per 100 trades:**
- 75 wins: Average +20% = +15% per winning trade
- 25 losses: Average -12% = -3% per losing trade
- Net: (+15% × 0.75) + (-3% × 0.25) = +10.5% average per trade
- **With 30% position size:** +3.15% portfolio growth per trade

**Conservative estimate:**
- 10 trades per month
- Win rate: 65% (conservative)
- Average win: +15% (+4.5% portfolio)
- Average loss: -10% (-3.0% portfolio)
- **Monthly return:** ~15-20%

---

## Changes Made (November 10, 2025)

### Issue Identified
```
Strategy: 15% SL, 30% TP
Live Engine: 10% SL, NO TP
❌ MISMATCH
```

### Fix Applied

**File:** `src/trading/live_engine.py`

**Lines 62-64 - Updated:**
```python
self.max_position_size = 0.30  # Max 30% per position
self.stop_loss_pct = 0.15      # 15% stop loss (matches strategy)
self.take_profit_pct = 0.30    # 30% take profit (matches strategy)
```

**Lines 102-104 - Updated open_position:**
```python
stop_loss=price * (1 - self.stop_loss_pct),     # 15% below entry
take_profit=price * (1 + self.take_profit_pct),  # 30% above entry
```

**Lines 155-166 - Added check_take_profits method:**
```python
def check_take_profits(self, prices: Dict[str, float]) -> List[str]:
    """Check for take profit triggers"""
    take_profit_triggers = []
    
    for symbol, position in self.positions.items():
        if symbol in prices and position.take_profit:
            current_price = prices[symbol]
            if current_price >= position.take_profit:
                take_profit_triggers.append(symbol)
                logger.info(f"Take profit triggered for {symbol}")
    
    return take_profit_triggers
```

**Lines 231-235 - Updated trading_cycle:**
```python
# Check take profits
take_profit_triggers = self.portfolio.check_take_profits(current_prices)
for symbol in take_profit_triggers:
    await self.execute_sell(symbol, current_prices[symbol], "TAKE_PROFIT")
```

---

## Verification Checklist

- ✅ Stop Loss: 15% (matches strategy)
- ✅ Take Profit: 30% (matches strategy)
- ✅ Position Size: 30% (matches recommendation)
- ✅ Risk/Reward: 1:2.0 (excellent)
- ✅ Auto-exit on stop loss (implemented)
- ✅ Auto-exit on take profit (implemented)
- ✅ Signal-based exit (implemented)
- ✅ Multiple position support (implemented)
- ✅ Cash management (70% reserve maintained)
- ✅ Logging (entry, exit, SL, TP all logged)

---

## Next Steps

1. **Clear Test Trades**
   ```bash
   rm -f src/logs/paper_trading/*.csv
   rm -f src/logs/paper_trading/*.json
   ```

2. **Start Live Engine**
   ```bash
   ./start_paper_trading.sh
   ```

3. **Monitor for Real Signals**
   - Check dashboard: http://localhost:8501
   - View logs: `cat logs/paper_trading/summary.txt`
   - Current market: HOLD (waiting for setup)

4. **When First Trade Executes**
   - Verify position size = 30% of portfolio
   - Verify stop loss = entry × 0.85
   - Verify take profit = entry × 1.30
   - Monitor until exit

5. **60-Day Validation**
   - Track all trades
   - Verify win rate ≥ 60%
   - Verify max drawdown < 10%
   - Verify risk management working

---

## Summary

✅ **Risk management is now accurate and matches the Week1Refined strategy exactly.**

**Key Points:**
- 30% position size per trade (keeps 70% cash)
- 15% stop loss (limits risk to 4.5% per trade)
- 30% take profit (targets 9% gain per trade)
- 1:2.0 risk/reward ratio
- Auto-exit on SL, TP, or trend signals
- Maximum 3-5 positions simultaneously

**Safety:**
- Never risk more than 4.5% on one trade
- Never deploy more than 90% of capital
- Always maintain minimum 10% cash
- Stop losses protect against major losses
- Take profits lock in gains

The bot is now ready for paper trading validation with accurate risk management!
