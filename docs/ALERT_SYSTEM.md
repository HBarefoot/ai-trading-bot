# Alert System & Enhanced Signals - Implementation Guide

## Overview
Comprehensive alert system with real-time notifications and paginated signal/alert history.

## Features Implemented

### 1. **Alert Manager** (`src/trading/alert_manager.py`)
Persistent alert storage using SQLite database.

**Features:**
- Database-backed alert storage
- Pagination support
- Multiple filter options (symbol, type, time range, read/unread)
- Alert statistics and metrics
- Automatic cleanup of old alerts

**Methods:**
- `add_alert()` - Store new alert
- `get_alerts()` - Retrieve alerts with filters
- `get_unread_count()` - Count unread alerts
- `mark_as_read()` - Mark single alert as read
- `mark_all_as_read()` - Mark all/filtered alerts as read
- `get_alert_stats()` - Get alert statistics

### 2. **API Endpoints** (src/api/api_backend.py)

#### GET `/api/alerts`
Retrieve alerts with pagination and filtering.

**Parameters:**
- `limit` (int): Number of alerts per page (default: 50)
- `offset` (int): Pagination offset (default: 0)
- `symbol` (str): Filter by symbol (optional)
- `alert_type` (str): Filter by alert type (optional)
- `unread_only` (bool): Show only unread alerts (default: false)
- `hours` (int): Filter by time range in hours (optional)

**Example:**
```bash
curl "http://localhost:9000/api/alerts?limit=20&offset=0&symbol=BTCUSDT&unread_only=true"
```

**Response:**
```json
{
  "timestamp": "2025-11-12T...",
  "alerts": [...],
  "stats": {
    "total": 150,
    "unread": 12,
    "read": 138,
    "by_priority": {"INFO": 100, "WARNING": 40, "CRITICAL": 10},
    "by_type": {...},
    "recent_24h": 25
  },
  "pagination": {
    "limit": 20,
    "offset": 0,
    "has_more": true
  }
}
```

#### POST `/api/alerts/{alert_id}/read`
Mark a specific alert as read.

#### POST `/api/alerts/mark-all-read`
Mark all alerts (or filtered by symbol) as read.

**Parameters:**
- `symbol` (str): Optional - mark only alerts for specific symbol

### 3. **Signal Monitor Integration**
The `SignalMonitor` class now automatically saves alerts to both JSON files (legacy) and the alert database.

**Alert Types:**
- `SIGNAL_CHANGE` - Signal transitions (BUY/SELL/HOLD)
- `TRADE_EXECUTED` - Trade executions
- `STOP_LOSS_HIT` - Stop loss triggered
- `TAKE_PROFIT_HIT` - Take profit triggered
- `WIN_RATE_WARNING` - Win rate below threshold
- `HIGH_WIN_STREAK` - Winning streak achieved

### 4. **Dashboard Enhancements**

#### Enhanced Signals Tab
Now features two sub-tabs:

**📊 Current Signals:**
- Shows current signal state for each symbol
- Real-time data from signal monitor
- Color-coded signals (🟢 BUY, 🔴 SELL, ⚪ HOLD)

**🔔 Alert History:**
- Paginated alert history (20 per page)
- Advanced filtering:
  - Alert Type filter
  - Symbol filter
  - Time Range filter (24h, 7d, 30d, All Time)
  - Unread Only toggle
- Alert statistics cards (Total, Unread, Last 24h)
- "Mark All Read" button
- Visual indicators:
  - 🔴 Unread alerts
  - Color-coded priority (blue=INFO, orange=WARNING, red=CRITICAL)
  - Left border color by priority
- Pagination controls (Previous/Next)

#### Real-Time Toast Notifications
- Automatic check for new alerts
- Pop-up toast notifications for new unread alerts
- Icon-based alerts (📊 signals, 💹 trades, 🛑 stop loss, etc.)
- Non-intrusive notifications
- Session tracking to avoid duplicate notifications

## Usage Examples

### API Usage

**Get recent unread alerts:**
```python
import requests

response = requests.get('http://localhost:9000/api/alerts', params={
    'limit': 20,
    'unread_only': True,
    'hours': 24
})

alerts = response.json()['alerts']
```

**Mark alert as read:**
```python
requests.post(f'http://localhost:9000/api/alerts/{alert_id}/read')
```

**Get alert statistics:**
```python
response = requests.get('http://localhost:9000/api/alerts', params={'limit': 1})
stats = response.json()['stats']
print(f"Total alerts: {stats['total']}")
print(f"Unread: {stats['unread']}")
```

### Dashboard Usage

1. **View Current Signals:**
   - Navigate to "Signals" tab
   - Click "📊 Current Signals" sub-tab
   - See real-time signal states

2. **View Alert History:**
   - Navigate to "Signals" tab
   - Click "🔔 Alert History" sub-tab
   - Use filters to narrow down alerts
   - Click Previous/Next for pagination

3. **Manage Alerts:**
   - Click "Mark All Read" to clear unread status
   - Alerts auto-expire after 30 days

4. **Real-Time Notifications:**
   - New alerts appear as toast notifications
   - Automatic checks every dashboard refresh
   - No duplicate notifications in same session

## Database Schema

### alerts table
```sql
CREATE TABLE alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    alert_type TEXT NOT NULL,
    symbol TEXT NOT NULL,
    message TEXT NOT NULL,
    priority TEXT NOT NULL,
    data TEXT,  -- JSON
    read INTEGER DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
)
```

**Indexes:**
- `idx_timestamp` - Fast time-based queries
- `idx_symbol` - Fast symbol filtering
- `idx_read` - Fast unread filtering

## Alert Types & Priorities

### Alert Types
1. **SIGNAL_CHANGE** (INFO)
   - Signal transitions: HOLD → BUY, BUY → SELL, etc.
   - Includes price, RSI, trend data

2. **TRADE_EXECUTED** (INFO)
   - Trade execution notifications
   - Includes side, price, amount, reason

3. **STOP_LOSS_HIT** (WARNING)
   - Stop loss triggered
   - Includes entry/exit prices, loss %

4. **TAKE_PROFIT_HIT** (INFO)
   - Take profit hit
   - Includes entry/exit prices, profit %

5. **WIN_RATE_WARNING** (WARNING)
   - Win rate below threshold (60%)
   - Triggered after 10+ trades

6. **HIGH_WIN_STREAK** (INFO)
   - Winning streak achievement
   - Motivational alerts

### Priority Levels
- **INFO** (Blue): Regular notifications
- **WARNING** (Orange): Attention required
- **CRITICAL** (Red): Urgent issues

## Configuration

### Alert Manager Settings
Located in `alert_manager.py`:
```python
db_path = "data/alerts.db"  # Database location
```

### Signal Monitor Settings
Located in `signal_monitor.py`:
```python
win_rate_threshold = 60.0  # Alert if below this %
```

### Auto-Cleanup
Delete alerts older than 30 days:
```python
from trading.alert_manager import get_alert_manager
alert_manager = get_alert_manager()
alert_manager.delete_old_alerts(days=30)
```

## Testing

### Test Alert Creation
```python
from trading.alert_manager import get_alert_manager

alert_manager = get_alert_manager()
alert_manager.add_alert(
    alert_type="SIGNAL_CHANGE",
    symbol="BTCUSDT",
    message="🟢 Signal: BTCUSDT HOLD → BUY @ $105,000",
    priority="INFO",
    data={'price': 105000, 'rsi': 45.2}
)
```

### Test API Endpoints
```bash
# Get alerts
curl http://localhost:9000/api/alerts?limit=10

# Mark as read
curl -X POST http://localhost:9000/api/alerts/1/read

# Mark all as read
curl -X POST http://localhost:9000/api/alerts/mark-all-read
```

### Test Dashboard
1. Start dashboard: `streamlit run src/frontend/dashboard_pro.py`
2. Navigate to Signals → Alert History
3. Generate test alert (via API or signal monitor)
4. Verify toast notification appears
5. Check alert in history tab

## Performance

### Database Performance
- Indexed queries for fast filtering
- Pagination prevents large result sets
- Automatic cleanup of old data

### Dashboard Performance
- Lazy loading of alerts (20 per page)
- Session-based notification tracking
- Efficient API calls with timeouts

## Maintenance

### Regular Cleanup
Add to cron or scheduler:
```python
# Run daily
from trading.alert_manager import get_alert_manager
get_alert_manager().delete_old_alerts(days=30)
```

### Monitoring
Check alert statistics:
```python
stats = get_alert_manager().get_alert_stats()
print(f"Total alerts: {stats['total']}")
print(f"Unread: {stats['unread']}")
print(f"Last 24h: {stats['recent_24h']}")
```

## Troubleshooting

### Issue: Alerts not appearing
**Solution:** Check signal monitor is running and alert manager is imported

### Issue: Duplicate notifications
**Solution:** Session state tracks shown alerts - refresh browser to reset

### Issue: Database locked
**Solution:** Check for concurrent access, restart trading engine

### Issue: Old alerts accumulating
**Solution:** Run cleanup: `delete_old_alerts(days=30)`

## Future Enhancements

### Planned Features
- [ ] Email/SMS alert delivery
- [ ] Webhook integration
- [ ] Alert priority customization
- [ ] Alert sound notifications
- [ ] Export alerts to CSV
- [ ] Alert templates
- [ ] Alert scheduling (quiet hours)
- [ ] Mobile push notifications

---

## Summary

✅ **Implemented:**
- Persistent alert storage (SQLite)
- Paginated alert history
- Advanced filtering
- Real-time toast notifications
- Alert statistics
- Mark as read functionality
- Auto-cleanup

✅ **Benefits:**
- Never miss a signal
- Review complete alert history
- Filter by time, symbol, type
- Monitor system performance
- Clean, organized interface

✅ **Ready for Use:**
- Dashboard running: http://localhost:8501
- API running: http://localhost:9000
- Database: `data/alerts.db`

**Last Updated:** November 12, 2025
