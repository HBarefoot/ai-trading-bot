# TradingView-Style Charts - Quick Reference

## Access the New Charts
🌐 **Dashboard:** http://localhost:8501
📊 **Tab:** Click "Charts" in the navigation

## Available Indicators

### Moving Averages
| Indicator | Period | Color | Type |
|-----------|--------|-------|------|
| SMA       | 20, 50, 200 | Blue, Green, Orange | Solid line |
| EMA       | 12, 26 | Cyan, Light Green | Dashed line |

### Bands & Volume
| Indicator | Settings | Display |
|-----------|----------|---------|
| Bollinger Bands | 20-period, 2σ | Blue shaded area |
| VWAP | Cumulative | Orange dotted line |

### Oscillators
| Indicator | Period | Zones |
|-----------|--------|-------|
| RSI | 14 | Overbought >70, Oversold <30 |
| MACD | 12, 26, 9 | Histogram with signal line |
| Stochastic | 14 | Overbought >80, Oversold <20 |

### Advanced
| Indicator | Description |
|-----------|-------------|
| Volume Profile | 20-bin horizontal volume distribution |

## Technical Summary Cards

### Trend Analysis
- 🟢 **Strong Uptrend:** Price > SMA20 > SMA50
- 🔵 **Uptrend:** Price > SMA20
- ⚪ **Sideways:** Price near SMAs
- 🟠 **Downtrend:** Price < SMA20
- 🔴 **Strong Downtrend:** Price < SMA20 < SMA50

### RSI Status
- 🔴 **Overbought:** RSI > 70 (potential reversal down)
- 🟢 **Oversold:** RSI < 30 (potential reversal up)
- 🔵 **Neutral:** 30 ≤ RSI ≤ 70 (no extreme)

### Price Distance
Shows percentage deviation from SMA20:
- 🔴 **Above:** >5% above SMA20 (extended)
- 🟢 **Below:** >5% below SMA20 (oversold)
- 🔵 **Neutral:** Within ±5% of SMA20

## How to Use

### 1. Select Symbol
Choose from: BTC/USDT, ETH/USDT, SOL/USDT

### 2. Toggle Indicators
Click checkboxes in control panel:
- Start with: SMA ✓, RSI ✓, MACD ✓ (recommended defaults)
- Add more as needed

### 3. Interpret Signals

#### Bullish Setup
- ✅ Price above SMA20 and SMA50
- ✅ RSI between 40-60 (room to move up)
- ✅ MACD histogram turning green
- ✅ Volume increasing

#### Bearish Setup
- ❌ Price below SMA20 and SMA50
- ❌ RSI between 40-60 (room to move down)
- ❌ MACD histogram turning red
- ❌ Volume increasing

#### Sideways/Choppy
- ⚠️ Price oscillating around SMA20
- ⚠️ RSI bouncing between 30-70
- ⚠️ MACD histogram near zero
- ⚠️ Low volume

### 4. Use Auto-Refresh
Enable "Auto-refresh (30s)" checkbox for continuous monitoring

## Keyboard Shortcuts (Plotly)
- **Zoom:** Click and drag on chart
- **Pan:** Hold Shift + drag
- **Reset:** Double-click chart
- **Box Select:** Click "Box Select" button
- **Save Image:** Click camera icon

## Common Trading Patterns

### Bullish Patterns
1. **Golden Cross:** SMA50 crosses above SMA200
2. **RSI Reversal:** RSI bounces from <30
3. **MACD Crossover:** MACD line crosses above signal
4. **Bollinger Squeeze:** Price at lower band, starting to rise

### Bearish Patterns
1. **Death Cross:** SMA50 crosses below SMA200
2. **RSI Reversal:** RSI drops from >70
3. **MACD Crossover:** MACD line crosses below signal
4. **Bollinger Squeeze:** Price at upper band, starting to fall

## Indicator Combinations

### Trend Following
- **Primary:** SMA 20, 50, 200
- **Confirmation:** MACD
- **Filter:** Volume above average

### Mean Reversion
- **Primary:** Bollinger Bands
- **Confirmation:** RSI (>70 or <30)
- **Filter:** Stochastic extreme zones

### Momentum Trading
- **Primary:** EMA 12, 26
- **Confirmation:** RSI 40-60
- **Filter:** MACD histogram growing

## Tips

### For Day Trading
- Focus on: EMA 12/26, RSI, MACD
- Use: 5-minute candles
- Watch: Volume Profile for support/resistance

### For Swing Trading
- Focus on: SMA 20/50/200, Bollinger Bands
- Use: 1-hour or 4-hour candles
- Watch: Trend alignment across timeframes

### For Position Trading
- Focus on: SMA 50/200, long-term trends
- Use: Daily candles
- Watch: Golden/Death crosses

## Warning Signs

### Avoid Trading When:
- ❌ All indicators conflicting
- ❌ Volume extremely low
- ❌ Price choppy (ADX < 20)
- ❌ RSI between 45-55 (indecision)
- ❌ MACD histogram flat

### High Probability When:
- ✅ Multiple indicators aligned
- ✅ Volume confirming move
- ✅ Clear trend (ADX > 25)
- ✅ RSI in strong range (55-70 or 30-45)
- ✅ MACD histogram expanding

## Troubleshooting

### Charts not loading?
```bash
# Check API
curl http://localhost:9000/api/status

# Check data
curl http://localhost:9000/api/candles/BTCUSDT?limit=10
```

### Indicators showing NaN?
Wait for more data collection (15-20 minutes)

### Slow performance?
Disable Volume Profile and use fewer candles

## Quick Test

### Verify Integration Working:
1. Go to http://localhost:8501
2. Click "Charts" tab
3. Should see:
   - ✅ Control panel with 8 checkboxes
   - ✅ 4 technical summary cards
   - ✅ Main candlestick chart
   - ✅ 4 price info cards at bottom

4. Toggle SMA checkbox:
   - ✅ Blue/Green/Orange lines appear on chart

5. Toggle RSI checkbox:
   - ✅ RSI chart appears below main chart

## Color Legend

### Chart Colors
- 🟢 **Green (#26a69a):** Bullish candle/indicator
- 🔴 **Red (#ef5350):** Bearish candle/indicator
- 🔵 **Blue (#2196F3):** SMA lines, RSI line
- 🟠 **Orange (#FF9800):** Signal lines, warnings
- 🟡 **Yellow:** Current price markers

### Status Colors
- **Strong Bullish:** Bright green
- **Bullish:** Blue-green
- **Neutral:** Gray/White
- **Bearish:** Orange
- **Strong Bearish:** Red

## Current BTC Market (Example)
```
Symbol: BTC/USDT
Price: $105,854.73
RSI: 49.1 (Neutral)
Trend: HOLD (Choppy market)
Volume: Low
Signal: Wait for setup
```

## Files Reference
- **Chart Engine:** `src/frontend/advanced_charts.py`
- **Dashboard:** `src/frontend/dashboard_pro.py`
- **Documentation:** `docs/TRADINGVIEW_CHART_INTEGRATION.md`

---
**Last Updated:** November 12, 2025
**Status:** ✅ Production Ready
