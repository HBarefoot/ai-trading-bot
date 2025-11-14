"""
Real-Time Signal Monitor and Alert System
Tracks signal changes and provides notifications
"""
import logging
from datetime import datetime
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import json
from pathlib import Path

logger = logging.getLogger(__name__)

# Import alert manager
try:
    from trading.alert_manager import get_alert_manager
    ALERT_MANAGER_AVAILABLE = True
except ImportError:
    ALERT_MANAGER_AVAILABLE = False
    logger.warning("Alert manager not available")

class SignalType(Enum):
    """Signal types"""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"

class AlertType(Enum):
    """Alert types"""
    SIGNAL_CHANGE = "SIGNAL_CHANGE"
    TRADE_EXECUTED = "TRADE_EXECUTED"
    STOP_LOSS_HIT = "STOP_LOSS_HIT"
    TAKE_PROFIT_HIT = "TAKE_PROFIT_HIT"
    WIN_RATE_WARNING = "WIN_RATE_WARNING"
    HIGH_WIN_STREAK = "HIGH_WIN_STREAK"

@dataclass
class SignalAlert:
    """Signal alert data"""
    alert_type: AlertType
    symbol: str
    timestamp: datetime
    message: str
    data: Dict
    priority: str = "INFO"  # INFO, WARNING, CRITICAL

@dataclass
class SignalState:
    """Current signal state for a symbol"""
    symbol: str
    current_signal: float
    signal_type: SignalType
    last_change: datetime
    price: float
    rsi: Optional[float] = None
    ma_fast: Optional[float] = None
    ma_slow: Optional[float] = None
    trend: Optional[str] = None

class SignalMonitor:
    """
    Real-time signal monitoring and alert system

    Features:
    - Track signal changes for all symbols
    - Generate alerts on signal transitions
    - Monitor position performance
    - Track win rate and send warnings
    - Log all events with timestamps
    """

    def __init__(self, log_dir: str = "logs/signals"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # State tracking
        self.signal_states: Dict[str, SignalState] = {}
        self.alerts: List[SignalAlert] = []
        self.callbacks: List[Callable[[SignalAlert], None]] = []

        # Performance tracking
        self.trade_count = 0
        self.winning_trades = 0
        self.losing_trades = 0
        self.current_streak = 0
        self.win_rate_threshold = 60.0  # Alert if below this

        # Files
        self.alerts_file = self.log_dir / "alerts.json"
        self.signals_file = self.log_dir / "signals.json"

        # Load existing data
        self._load_alerts()
        self._load_signal_states()

        logger.info(f"Signal Monitor initialized. Logs: {self.log_dir}")

    def subscribe(self, callback: Callable[[SignalAlert], None]):
        """Subscribe to alerts"""
        self.callbacks.append(callback)
        logger.info(f"Alert callback registered: {callback.__name__}")

    def unsubscribe(self, callback: Callable):
        """Unsubscribe from alerts"""
        if callback in self.callbacks:
            self.callbacks.remove(callback)

    def update_signal(self, symbol: str, signal: float, price: float,
                     rsi: Optional[float] = None,
                     ma_fast: Optional[float] = None,
                     ma_slow: Optional[float] = None,
                     trend: Optional[str] = None) -> Optional[SignalAlert]:
        """
        Update signal for a symbol and check for changes

        Args:
            symbol: Trading symbol
            signal: Signal value (1=BUY, 0=HOLD, -1=SELL)
            price: Current price
            rsi: RSI value
            ma_fast: Fast MA value
            ma_slow: Slow MA value
            trend: Trend direction

        Returns:
            SignalAlert if signal changed, None otherwise
        """
        # Determine signal type
        if signal > 0:
            signal_type = SignalType.BUY
        elif signal < 0:
            signal_type = SignalType.SELL
        else:
            signal_type = SignalType.HOLD

        # Check if this is a signal change
        prev_state = self.signal_states.get(symbol)
        signal_changed = False

        if prev_state is None:
            # First time seeing this symbol
            signal_changed = signal_type != SignalType.HOLD
            logger.info(f"Initial signal for {symbol}: {signal_type.value}")
        elif prev_state.signal_type != signal_type:
            # Signal changed
            signal_changed = True
            logger.info(f"Signal change for {symbol}: {prev_state.signal_type.value} → {signal_type.value}")

        # Update state
        new_state = SignalState(
            symbol=symbol,
            current_signal=signal,
            signal_type=signal_type,
            last_change=datetime.now() if signal_changed else prev_state.last_change if prev_state else datetime.now(),
            price=price,
            rsi=rsi,
            ma_fast=ma_fast,
            ma_slow=ma_slow,
            trend=trend
        )
        self.signal_states[symbol] = new_state

        # Generate alert if signal changed
        alert = None
        if signal_changed:
            alert = self._create_signal_change_alert(symbol, prev_state, new_state)
            self._notify(alert)

        # Save state
        self._save_signal_state(new_state)

        return alert

    def log_trade_execution(self, symbol: str, side: str, price: float,
                           amount: float, reason: str = "SIGNAL") -> SignalAlert:
        """
        Log trade execution

        Args:
            symbol: Trading symbol
            side: 'BUY' or 'SELL'
            price: Execution price
            amount: Trade amount
            reason: Trade reason (SIGNAL, STOP_LOSS, TAKE_PROFIT)
        """
        self.trade_count += 1

        message = f"Trade #{self.trade_count}: {side} {amount:.6f} {symbol} @ ${price:.2f}"

        alert = SignalAlert(
            alert_type=AlertType.TRADE_EXECUTED,
            symbol=symbol,
            timestamp=datetime.now(),
            message=message,
            data={
                'side': side,
                'price': price,
                'amount': amount,
                'reason': reason,
                'trade_number': self.trade_count
            },
            priority="INFO"
        )

        self._notify(alert)
        return alert

    def log_stop_loss(self, symbol: str, entry_price: float,
                     exit_price: float, loss_pct: float) -> SignalAlert:
        """Log stop loss hit"""
        self.losing_trades += 1
        self.current_streak = min(0, self.current_streak - 1)

        message = f"🛑 STOP LOSS: {symbol} ${entry_price:.2f} → ${exit_price:.2f} ({loss_pct:.2f}%)"

        alert = SignalAlert(
            alert_type=AlertType.STOP_LOSS_HIT,
            symbol=symbol,
            timestamp=datetime.now(),
            message=message,
            data={
                'entry_price': entry_price,
                'exit_price': exit_price,
                'loss_pct': loss_pct,
                'losing_streak': abs(self.current_streak)
            },
            priority="WARNING"
        )

        self._notify(alert)
        self._check_win_rate()
        return alert

    def log_take_profit(self, symbol: str, entry_price: float,
                       exit_price: float, profit_pct: float) -> SignalAlert:
        """Log take profit hit"""
        self.winning_trades += 1
        self.current_streak = max(0, self.current_streak + 1)

        message = f"🎯 TAKE PROFIT: {symbol} ${entry_price:.2f} → ${exit_price:.2f} (+{profit_pct:.2f}%)"

        alert = SignalAlert(
            alert_type=AlertType.TAKE_PROFIT_HIT,
            symbol=symbol,
            timestamp=datetime.now(),
            message=message,
            data={
                'entry_price': entry_price,
                'exit_price': exit_price,
                'profit_pct': profit_pct,
                'winning_streak': self.current_streak
            },
            priority="INFO"
        )

        self._notify(alert)

        # Check for high win streak
        if self.current_streak >= 5:
            streak_alert = SignalAlert(
                alert_type=AlertType.HIGH_WIN_STREAK,
                symbol="ALL",
                timestamp=datetime.now(),
                message=f"🔥 {self.current_streak} winning trades in a row!",
                data={'streak': self.current_streak},
                priority="INFO"
            )
            self._notify(streak_alert)

        return alert

    def get_current_signals(self) -> Dict[str, SignalState]:
        """Get current signal states for all symbols"""
        return self.signal_states.copy()

    def get_recent_alerts(self, limit: int = 20) -> List[SignalAlert]:
        """Get recent alerts"""
        return self.alerts[-limit:]

    def get_performance_summary(self) -> Dict:
        """Get performance summary"""
        total_trades = self.winning_trades + self.losing_trades
        win_rate = (self.winning_trades / total_trades * 100) if total_trades > 0 else 0

        return {
            'total_trades': total_trades,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'win_rate': win_rate,
            'current_streak': self.current_streak,
            'target_win_rate': self.win_rate_threshold,
            'status': 'ABOVE_TARGET' if win_rate >= self.win_rate_threshold else 'BELOW_TARGET'
        }

    def _create_signal_change_alert(self, symbol: str,
                                   prev_state: Optional[SignalState],
                                   new_state: SignalState) -> SignalAlert:
        """Create alert for signal change"""
        prev_type = prev_state.signal_type.value if prev_state else "NONE"
        new_type = new_state.signal_type.value

        # Determine priority
        if new_type == "BUY":
            emoji = "🟢"
            priority = "INFO"
        elif new_type == "SELL":
            emoji = "🔴"
            priority = "INFO"
        else:
            emoji = "⚪"
            priority = "INFO"

        message = f"{emoji} Signal: {symbol} {prev_type} → {new_type} @ ${new_state.price:.2f}"

        if new_state.rsi:
            message += f" | RSI: {new_state.rsi:.1f}"
        if new_state.trend:
            message += f" | Trend: {new_state.trend}"

        alert = SignalAlert(
            alert_type=AlertType.SIGNAL_CHANGE,
            symbol=symbol,
            timestamp=new_state.last_change,
            message=message,
            data={
                'prev_signal': prev_type,
                'new_signal': new_type,
                'price': new_state.price,
                'rsi': new_state.rsi,
                'ma_fast': new_state.ma_fast,
                'ma_slow': new_state.ma_slow,
                'trend': new_state.trend
            },
            priority=priority
        )

        return alert

    def _check_win_rate(self):
        """Check win rate and send alert if below threshold"""
        total = self.winning_trades + self.losing_trades
        if total >= 10:  # Only check after 10 trades
            win_rate = (self.winning_trades / total * 100)

            if win_rate < self.win_rate_threshold:
                alert = SignalAlert(
                    alert_type=AlertType.WIN_RATE_WARNING,
                    symbol="ALL",
                    timestamp=datetime.now(),
                    message=f"⚠️  Win Rate: {win_rate:.1f}% (Target: {self.win_rate_threshold}%)",
                    data={
                        'win_rate': win_rate,
                        'threshold': self.win_rate_threshold,
                        'total_trades': total,
                        'winning_trades': self.winning_trades
                    },
                    priority="WARNING"
                )
                self._notify(alert)

    def _notify(self, alert: SignalAlert):
        """Notify all subscribers and log alert"""
        self.alerts.append(alert)

        # Console output
        timestamp = alert.timestamp.strftime("%H:%M:%S")
        print(f"[{timestamp}] {alert.message}")

        # Call callbacks
        for callback in self.callbacks:
            try:
                callback(alert)
            except Exception as e:
                logger.error(f"Error in alert callback: {e}")

        # Save to file
        self._save_alert(alert)

    def _save_alert(self, alert: SignalAlert):
        """Save alert to file and database"""
        try:
            # Save to JSON file (legacy)
            alerts = self._load_alerts()
            alerts.append({
                'type': alert.alert_type.value,
                'symbol': alert.symbol,
                'timestamp': alert.timestamp.isoformat(),
                'message': alert.message,
                'data': alert.data,
                'priority': alert.priority
            })

            with open(self.alerts_file, 'w') as f:
                json.dump(alerts, f, indent=2)
            
            # Save to database via alert manager
            if ALERT_MANAGER_AVAILABLE:
                alert_manager = get_alert_manager()
                alert_manager.add_alert(
                    alert_type=alert.alert_type.value,
                    symbol=alert.symbol,
                    message=alert.message,
                    priority=alert.priority,
                    data=alert.data
                )

        except Exception as e:
            logger.error(f"Error saving alert: {e}")

    def _save_signal_state(self, state: SignalState):
        """Save signal state to file and database"""
        try:
            # Save to database
            self._save_signal_to_db(state)

            # Save to JSON file (legacy)
            states = {}
            if self.signals_file.exists():
                try:
                    with open(self.signals_file, 'r') as f:
                        states = json.load(f)
                except json.JSONDecodeError:
                    logger.warning(f"Corrupted signals file, resetting: {self.signals_file}")
                    states = {}

            # Convert numpy types to native Python types for JSON serialization
            def convert_value(val):
                import numpy as np
                import pandas as pd
                if val is None:
                    return None
                if isinstance(val, pd.Timestamp):
                    return val.isoformat()
                if isinstance(val, datetime):
                    return val.isoformat()
                if hasattr(val, 'item'):  # numpy types have .item() method
                    return val.item()
                if isinstance(val, (np.integer, np.int64, np.int32, np.int16, np.int8)):
                    return int(val)
                if isinstance(val, (np.floating, np.float64, np.float32, np.float16)):
                    return float(val)
                if isinstance(val, (int, float)):
                    return val
                try:
                    return float(val)
                except (ValueError, TypeError):
                    return str(val)

            states[state.symbol] = {
                'signal': convert_value(state.current_signal),
                'signal_type': state.signal_type.value,
                'last_change': state.last_change.isoformat(),
                'price': convert_value(state.price),
                'rsi': convert_value(state.rsi),
                'ma_fast': convert_value(state.ma_fast),
                'ma_slow': convert_value(state.ma_slow),
                'trend': state.trend
            }

            with open(self.signals_file, 'w') as f:
                json.dump(states, f, indent=2)

        except Exception as e:
            logger.error(f"Error saving signal state: {e}")

    def _load_alerts(self) -> List[Dict]:
        """Load alerts from file"""
        try:
            if self.alerts_file.exists():
                with open(self.alerts_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Error loading alerts: {e}")

        return []

    def _load_signal_states(self):
        """Load signal states from file on startup"""
        try:
            if self.signals_file.exists():
                with open(self.signals_file, 'r') as f:
                    states_dict = json.load(f)
                
                # Convert JSON back to SignalState objects
                for symbol, state_data in states_dict.items():
                    signal_type = SignalType(state_data['signal_type'])
                    
                    # Parse datetime
                    from datetime import datetime
                    last_change = datetime.fromisoformat(state_data['last_change'])
                    
                    # Create SignalState
                    state = SignalState(
                        symbol=symbol,
                        current_signal=state_data['signal'],
                        signal_type=signal_type,
                        last_change=last_change,
                        price=state_data['price'],
                        rsi=state_data.get('rsi'),
                        ma_fast=state_data.get('ma_fast'),
                        ma_slow=state_data.get('ma_slow'),
                        trend=state_data.get('trend', 'NEUTRAL')
                    )
                    
                    self.signal_states[symbol] = state
                
                logger.info(f"Loaded {len(self.signal_states)} signal states from file")
                
        except Exception as e:
            logger.error(f"Error loading signal states: {e}")

    def _save_signal_to_db(self, state: SignalState):
        """Save signal to database"""
        try:
            import os
            db_url = os.getenv('DATABASE_URL')
            if not db_url:
                return  # No database configured

            from sqlalchemy import create_engine
            from sqlalchemy.orm import sessionmaker
            from data.models import Signal
            from datetime import datetime

            engine = create_engine(db_url)
            Session = sessionmaker(bind=engine)
            session = Session()

            try:
                # Convert numpy types to native Python types
                def convert_value(val):
                    if val is None:
                        return None
                    if hasattr(val, 'item'):  # numpy types
                        return val.item()
                    try:
                        return float(val)
                    except (ValueError, TypeError):
                        return None

                # Create signal record
                signal = Signal(
                    symbol=state.symbol,
                    signal_type=state.signal_type.value,
                    signal_value=convert_value(state.current_signal),
                    price=convert_value(state.price),
                    rsi=convert_value(state.rsi),
                    ma_fast=convert_value(state.ma_fast),
                    ma_slow=convert_value(state.ma_slow),
                    trend=state.trend,
                    timestamp=state.last_change if isinstance(state.last_change, datetime) else datetime.now()
                )

                session.add(signal)
                session.commit()

            finally:
                session.close()

        except Exception as e:
            logger.error(f"Error saving signal to database: {e}")


# Global signal monitor
_signal_monitor: Optional[SignalMonitor] = None

def get_signal_monitor(log_dir: str = "logs/signals") -> SignalMonitor:
    """Get the global signal monitor"""
    global _signal_monitor

    if _signal_monitor is None:
        _signal_monitor = SignalMonitor(log_dir)

    return _signal_monitor


if __name__ == "__main__":
    # Demo usage
    print("Signal Monitor Demo")
    print("=" * 70)

    monitor = SignalMonitor()

    # Subscribe to alerts
    def print_alert(alert: SignalAlert):
        print(f"  ALERT: {alert.message}")

    monitor.subscribe(print_alert)

    # Simulate signal updates
    print("\nSimulating signal updates...")
    monitor.update_signal("BTCUSDT", 0, 32000.0, rsi=45.0, trend="BULLISH")
    monitor.update_signal("BTCUSDT", 1, 32500.0, rsi=55.0, trend="BULLISH")  # Signal change!
    monitor.log_trade_execution("BTCUSDT", "BUY", 32500.0, 0.1)

    print("\nPerformance Summary:")
    summary = monitor.get_performance_summary()
    for key, value in summary.items():
        print(f"  {key}: {value}")
