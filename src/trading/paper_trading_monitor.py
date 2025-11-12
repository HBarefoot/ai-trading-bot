"""
Paper Trading Performance Monitor
Tracks daily performance metrics for 60-day validation period
"""
import json
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))


class PaperTradingMonitor:
    """
    Monitor paper trading performance over 60-day validation period
    
    Tracks:
    - Daily win rate
    - Daily returns
    - Max drawdown
    - Sharpe ratio
    - Trade log
    """
    
    def __init__(self, log_dir: str = "logs/paper_trading"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        self.metrics_file = self.log_dir / "daily_metrics.json"
        self.trades_file = self.log_dir / "trades.json"
        self.summary_file = self.log_dir / "summary.txt"
        
        # Load existing data or initialize
        self.daily_metrics = self._load_metrics()
        self.trades = self._load_trades()
        
        # Validation targets
        self.target_win_rate = 60.0  # Minimum acceptable win rate
        self.target_days = 60  # Validation period
        self.start_date = datetime.now()
    
    def _load_metrics(self) -> List[Dict]:
        """Load existing daily metrics"""
        if self.metrics_file.exists():
            with open(self.metrics_file, 'r') as f:
                return json.load(f)
        return []
    
    def _save_metrics(self):
        """Save daily metrics to disk"""
        with open(self.metrics_file, 'w') as f:
            json.dump(self.daily_metrics, f, indent=2, default=str)
    
    def _load_trades(self) -> List[Dict]:
        """Load existing trades"""
        if self.trades_file.exists():
            with open(self.trades_file, 'r') as f:
                return json.load(f)
        return []
    
    def _save_trades(self):
        """Save trades to disk"""
        with open(self.trades_file, 'w') as f:
            json.dump(self.trades, f, indent=2, default=str)
    
    def log_trade(self, trade_data: Dict):
        """
        Log a completed trade
        
        Args:
            trade_data: Dict with keys:
                - timestamp: datetime
                - symbol: str
                - side: 'BUY' or 'SELL'
                - entry_price: float
                - exit_price: float (for SELL)
                - amount: float
                - pnl: float (for SELL)
                - pnl_pct: float (for SELL)
                - reason: str (exit reason)
        """
        trade_data['timestamp'] = str(trade_data.get('timestamp', datetime.now()))
        self.trades.append(trade_data)
        self._save_trades()
        
        print(f"📝 Trade logged: {trade_data['side']} {trade_data['symbol']} @ ${trade_data.get('entry_price', trade_data.get('exit_price')):.2f}")
        
        if trade_data['side'] == 'SELL' and 'pnl_pct' in trade_data:
            symbol = "✅" if trade_data['pnl_pct'] > 0 else "❌"
            print(f"   {symbol} PnL: {trade_data['pnl_pct']:.2f}% (${trade_data.get('pnl', 0):.2f})")
    
    def log_daily_metrics(self, metrics: Dict):
        """
        Log daily performance metrics
        
        Args:
            metrics: Dict with keys:
                - date: datetime
                - portfolio_value: float
                - daily_return: float
                - win_rate: float
                - total_trades: int
                - winning_trades: int
                - losing_trades: int
                - max_drawdown: float
        """
        metrics['date'] = str(metrics.get('date', datetime.now().date()))
        self.daily_metrics.append(metrics)
        self._save_metrics()
        
        print(f"\n📊 Daily Metrics - {metrics['date']}")
        print(f"   Portfolio Value: ${metrics['portfolio_value']:,.2f}")
        print(f"   Daily Return: {metrics['daily_return']:.2f}%")
        print(f"   Win Rate: {metrics['win_rate']:.2f}%")
        print(f"   Trades Today: {metrics['total_trades']}")
        print(f"   Max Drawdown: {metrics['max_drawdown']:.2f}%")
    
    def calculate_current_performance(self) -> Dict:
        """Calculate current cumulative performance"""
        if not self.trades:
            return {
                'total_trades': 0,
                'win_rate': 0.0,
                'total_return': 0.0,
                'avg_win': 0.0,
                'avg_loss': 0.0,
                'max_drawdown': 0.0,
                'days_running': 0
            }
        
        # Get completed trades (SELL only)
        completed = [t for t in self.trades if t['side'] == 'SELL']
        
        if not completed:
            return {
                'total_trades': 0,
                'win_rate': 0.0,
                'total_return': 0.0,
                'avg_win': 0.0,
                'avg_loss': 0.0,
                'max_drawdown': 0.0,
                'days_running': (datetime.now() - self.start_date).days
            }
        
        # Calculate metrics
        winning = [t for t in completed if t.get('pnl_pct', 0) > 0]
        losing = [t for t in completed if t.get('pnl_pct', 0) <= 0]
        
        total_return = sum(t.get('pnl_pct', 0) for t in completed)
        win_rate = (len(winning) / len(completed) * 100) if completed else 0
        avg_win = (sum(t['pnl_pct'] for t in winning) / len(winning)) if winning else 0
        avg_loss = (sum(t['pnl_pct'] for t in losing) / len(losing)) if losing else 0
        
        # Calculate max drawdown from daily metrics
        max_dd = 0.0
        if self.daily_metrics:
            max_dd = min(m.get('max_drawdown', 0) for m in self.daily_metrics)
        
        days_running = (datetime.now() - self.start_date).days
        
        return {
            'total_trades': len(completed),
            'winning_trades': len(winning),
            'losing_trades': len(losing),
            'win_rate': win_rate,
            'total_return': total_return,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'max_drawdown': max_dd,
            'days_running': days_running,
            'days_remaining': max(0, self.target_days - days_running)
        }
    
    def generate_daily_report(self) -> str:
        """Generate daily performance report"""
        perf = self.calculate_current_performance()
        
        report = []
        report.append("=" * 80)
        report.append("PAPER TRADING DAILY REPORT")
        report.append("=" * 80)
        report.append(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Days Running: {perf['days_running']} / {self.target_days}")
        report.append(f"Days Remaining: {perf['days_remaining']}")
        report.append("")
        
        report.append("📊 Performance Metrics")
        report.append("-" * 80)
        report.append(f"Total Trades: {perf['total_trades']}")
        report.append(f"Winning Trades: {perf['winning_trades']}")
        report.append(f"Losing Trades: {perf['losing_trades']}")
        report.append(f"Win Rate: {perf['win_rate']:.2f}% (Target: {self.target_win_rate}%)")
        
        # Status indicator
        if perf['win_rate'] >= self.target_win_rate:
            status = "✅ ABOVE TARGET"
        elif perf['win_rate'] >= self.target_win_rate * 0.9:
            status = "⚠️  CLOSE TO TARGET"
        else:
            status = "❌ BELOW TARGET"
        report.append(f"Status: {status}")
        report.append("")
        
        report.append(f"Total Return: {perf['total_return']:.2f}%")
        report.append(f"Avg Win: {perf['avg_win']:.2f}%")
        report.append(f"Avg Loss: {perf['avg_loss']:.2f}%")
        report.append(f"Max Drawdown: {perf['max_drawdown']:.2f}%")
        report.append("")
        
        # Recent trades
        if self.trades:
            report.append("📝 Recent Trades (Last 5)")
            report.append("-" * 80)
            recent = self.trades[-5:]
            for trade in recent:
                side = trade['side']
                symbol = trade['symbol']
                price = trade.get('exit_price', trade.get('entry_price', 0))
                
                if side == 'SELL' and 'pnl_pct' in trade:
                    emoji = "✅" if trade['pnl_pct'] > 0 else "❌"
                    report.append(f"  {emoji} {side} {symbol} @ ${price:.2f} | PnL: {trade['pnl_pct']:.2f}%")
                else:
                    report.append(f"  📈 {side} {symbol} @ ${price:.2f}")
        
        report.append("")
        report.append("=" * 80)
        
        report_text = "\n".join(report)
        
        # Save to file
        with open(self.summary_file, 'w') as f:
            f.write(report_text)
        
        return report_text
    
    def check_validation_status(self) -> Dict:
        """Check if validation period is complete and if target is met"""
        perf = self.calculate_current_performance()
        days_complete = (perf['days_running'] / self.target_days) * 100
        
        validation_complete = perf['days_running'] >= self.target_days
        target_met = perf['win_rate'] >= self.target_win_rate
        ready_for_live = validation_complete and target_met
        
        return {
            'validation_complete': validation_complete,
            'target_met': target_met,
            'ready_for_live': ready_for_live,
            'days_progress': days_complete,
            'current_win_rate': perf['win_rate'],
            'target_win_rate': self.target_win_rate,
            'recommendation': self._get_recommendation(perf, validation_complete, target_met)
        }
    
    def _get_recommendation(self, perf: Dict, validation_complete: bool, target_met: bool) -> str:
        """Generate recommendation based on current status"""
        if validation_complete and target_met:
            return "✅ READY FOR LIVE TRADING - All targets met!"
        elif validation_complete and not target_met:
            return f"❌ NOT READY - Win rate {perf['win_rate']:.1f}% below {self.target_win_rate}% target. Continue optimization."
        elif not validation_complete and target_met:
            days_left = self.target_days - perf['days_running']
            return f"⏳ ON TRACK - Continue monitoring for {days_left} more days"
        else:
            return f"⚠️  BELOW TARGET - Current {perf['win_rate']:.1f}% vs {self.target_win_rate}% target. Monitor closely."
    
    def export_to_csv(self):
        """Export trades and metrics to CSV for analysis"""
        if self.trades:
            df_trades = pd.DataFrame(self.trades)
            df_trades.to_csv(self.log_dir / "trades.csv", index=False)
            print(f"✅ Trades exported to {self.log_dir / 'trades.csv'}")
        
        if self.daily_metrics:
            df_metrics = pd.DataFrame(self.daily_metrics)
            df_metrics.to_csv(self.log_dir / "daily_metrics.csv", index=False)
            print(f"✅ Metrics exported to {self.log_dir / 'daily_metrics.csv'}")


def main():
    """Display current paper trading status"""
    monitor = PaperTradingMonitor()
    
    print("\n" + "="*70)
    print("📊 PAPER TRADING MONITOR - Current Status")
    print("="*70 + "\n")
    
    # Show current status without creating fake trades
    if monitor.trades:
        print(f"Total Trades: {len(monitor.trades)}")
        print(f"Days Running: {monitor.days_running} / 60")
        print("\n" + monitor.generate_daily_report())
        
        # Check validation status
        status = monitor.check_validation_status()
        print("\n📋 Validation Status:")
        print(f"   Days Progress: {status['days_progress']:.1f}%")
        print(f"   Target Met: {status['target_met']}")
        print(f"   Recommendation: {status['recommendation']}")
        print("\n" + "="*70)
        print("📁 Log Files:")
        print(f"   Trades: {monitor.log_dir / 'trades.csv'}")
        print(f"   Metrics: {monitor.log_dir / 'daily_metrics.csv'}")
        print(f"   Summary: {monitor.log_dir / 'summary.txt'}")
        print("="*70 + "\n")
    else:
        print("No trades recorded yet.")
        print("\nTo start paper trading:")
        print("  1. Run: ./start_paper_trading.sh")
        print("  2. Monitor: http://localhost:8501")
        print("  3. Wait for strategy signals")
        print("\nThe bot is monitoring the market and will execute trades")
        print("automatically when conditions are met.")
        print("\n" + "="*70 + "\n")


if __name__ == '__main__':
    main()
