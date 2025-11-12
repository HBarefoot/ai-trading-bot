"""
Phase 5 Trading Performance Tracker
Tracks extended paper trading session metrics
"""
import json
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List
import pandas as pd


class TradingPerformanceTracker:
    """Track trading performance over extended period"""
    
    def __init__(self, log_dir: str = "logs/trading"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.api_url = "http://localhost:9000"
        
    def collect_daily_snapshot(self) -> Dict:
        """Collect comprehensive daily trading snapshot"""
        try:
            # Get all data
            portfolio = requests.get(f"{self.api_url}/api/portfolio", timeout=10).json()
            trades = requests.get(f"{self.api_url}/api/trades?limit=1000", timeout=10).json()
            performance = requests.get(f"{self.api_url}/api/performance", timeout=10).json()
            strategies = requests.get(f"{self.api_url}/api/strategies", timeout=10).json()
            
            # Calculate detailed metrics
            daily_trades = [t for t in trades 
                           if datetime.fromisoformat(t['timestamp'].replace('+00:00', '')) 
                           >= datetime.now() - timedelta(days=1)]
            
            winning_trades = [t for t in trades if t.get('profit_loss', 0) > 0]
            losing_trades = [t for t in trades if t.get('profit_loss', 0) < 0]
            
            snapshot = {
                "date": datetime.now().strftime("%Y-%m-%d"),
                "timestamp": datetime.now().isoformat(),
                
                # Portfolio
                "portfolio_value": portfolio.get("total_value", 0),
                "cash_balance": portfolio.get("cash", 0),
                "positions_count": len(portfolio.get("positions", [])),
                "positions": portfolio.get("positions", []),
                
                # Trading Activity
                "total_trades": len(trades),
                "daily_trades": len(daily_trades),
                "winning_trades": len(winning_trades),
                "losing_trades": len(losing_trades),
                "win_rate_pct": (len(winning_trades) / len(trades) * 100) if trades else 0,
                
                # P&L
                "total_pnl": sum(t.get('profit_loss', 0) for t in trades),
                "daily_pnl": sum(t.get('profit_loss', 0) for t in daily_trades),
                "avg_win": sum(t['profit_loss'] for t in winning_trades) / len(winning_trades) if winning_trades else 0,
                "avg_loss": sum(t['profit_loss'] for t in losing_trades) / len(losing_trades) if losing_trades else 0,
                
                # Risk Metrics
                "sharpe_ratio": performance.get("sharpe_ratio"),
                "sortino_ratio": performance.get("sortino_ratio"),
                "max_drawdown_pct": performance.get("max_drawdown_pct"),
                "volatility": performance.get("volatility"),
                
                # Strategy
                "active_strategy": strategies.get("active_strategy", "unknown"),
                
                # Trade Breakdown by Symbol
                "trades_by_symbol": self._count_by_symbol(trades),
                "pnl_by_symbol": self._pnl_by_symbol(trades),
            }
            
            return snapshot
            
        except Exception as e:
            return {
                "date": datetime.now().strftime("%Y-%m-%d"),
                "error": str(e)
            }
    
    def _count_by_symbol(self, trades: List[Dict]) -> Dict:
        """Count trades by symbol"""
        counts = {}
        for trade in trades:
            symbol = trade.get('symbol', 'UNKNOWN')
            counts[symbol] = counts.get(symbol, 0) + 1
        return counts
    
    def _pnl_by_symbol(self, trades: List[Dict]) -> Dict:
        """Calculate P&L by symbol"""
        pnl = {}
        for trade in trades:
            symbol = trade.get('symbol', 'UNKNOWN')
            profit_loss = trade.get('profit_loss', 0)
            pnl[symbol] = pnl.get(symbol, 0) + profit_loss
        return pnl
    
    def save_daily_snapshot(self, snapshot: Dict):
        """Save daily snapshot to file"""
        filename = self.log_dir / f"daily_{snapshot['date']}.json"
        with open(filename, 'w') as f:
            json.dump(snapshot, f, indent=2)
        print(f"✅ Saved daily snapshot: {filename}")
    
    def generate_7day_report(self) -> str:
        """Generate comprehensive 7-day report"""
        # Load last 7 days of data
        snapshots = []
        for i in range(7):
            date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            filename = self.log_dir / f"daily_{date}.json"
            if filename.exists():
                with open(filename, 'r') as f:
                    snapshots.append(json.load(f))
        
        if not snapshots:
            return "❌ No data available for 7-day report"
        
        snapshots.sort(key=lambda x: x['date'])
        
        # Calculate statistics
        start_value = snapshots[0]['portfolio_value']
        end_value = snapshots[-1]['portfolio_value']
        total_return = ((end_value - start_value) / start_value * 100) if start_value > 0 else 0
        
        total_trades = snapshots[-1]['total_trades'] - snapshots[0]['total_trades']
        avg_daily_trades = total_trades / len(snapshots)
        
        report = f"""
╔══════════════════════════════════════════════════════════╗
║       7-DAY PAPER TRADING PERFORMANCE REPORT            ║
║              Phase 5 - Week 1 Results                    ║
╚══════════════════════════════════════════════════════════╝

📅 PERIOD: {snapshots[0]['date']} to {snapshots[-1]['date']}
📊 SNAPSHOTS COLLECTED: {len(snapshots)} days

💰 PORTFOLIO PERFORMANCE:
  Starting Value:    ${start_value:,.2f}
  Ending Value:      ${end_value:,.2f}
  Total Return:      {total_return:+.2f}%
  Total P&L:         ${end_value - start_value:+,.2f}

📈 TRADING ACTIVITY:
  Total Trades:      {total_trades}
  Avg Daily Trades:  {avg_daily_trades:.1f}
  Win Rate:          {snapshots[-1]['win_rate_pct']:.1f}%
  Winning Trades:    {snapshots[-1]['winning_trades']}
  Losing Trades:     {snapshots[-1]['losing_trades']}

💵 P&L ANALYSIS:
  Total P&L:         ${snapshots[-1]['total_pnl']:+,.2f}
  Avg Win:           ${snapshots[-1]['avg_win']:+,.2f}
  Avg Loss:          ${snapshots[-1]['avg_loss']:+,.2f}
  Profit Factor:     {abs(snapshots[-1]['avg_win'] / snapshots[-1]['avg_loss']) if snapshots[-1]['avg_loss'] != 0 else 'N/A'}

📊 RISK METRICS:
  Sharpe Ratio:      {snapshots[-1]['sharpe_ratio'] or 'N/A'}
  Sortino Ratio:     {snapshots[-1]['sortino_ratio'] or 'N/A'}
  Max Drawdown:      {snapshots[-1]['max_drawdown_pct'] or 'N/A'}%
  Volatility:        {snapshots[-1]['volatility'] or 'N/A'}

🎯 ACTIVE POSITIONS: {snapshots[-1]['positions_count']}
"""
        
        if snapshots[-1]['positions']:
            report += "\nCurrent Positions:\n"
            for pos in snapshots[-1]['positions']:
                qty = pos.get('quantity', 0)
                avg_cost = pos.get('avg_cost') or pos.get('average_price', 0)
                report += f"  • {pos['symbol']}: {qty:.6f} @ ${avg_cost:.2f}\n"
        
        report += f"\n🤖 STRATEGY: {snapshots[-1]['active_strategy']}\n"
        
        # Trade distribution
        if snapshots[-1]['trades_by_symbol']:
            report += "\n📊 TRADES BY SYMBOL:\n"
            for symbol, count in sorted(snapshots[-1]['trades_by_symbol'].items(), 
                                       key=lambda x: x[1], reverse=True):
                pnl = snapshots[-1]['pnl_by_symbol'].get(symbol, 0)
                report += f"  • {symbol}: {count} trades, P&L: ${pnl:+,.2f}\n"
        
        report += "\n" + "="*60 + "\n"
        
        return report


def main():
    """Main execution"""
    tracker = TradingPerformanceTracker()
    
    print("📊 Collecting daily snapshot...")
    snapshot = tracker.collect_daily_snapshot()
    
    if 'error' not in snapshot:
        tracker.save_daily_snapshot(snapshot)
        print(f"\n✅ Daily snapshot saved successfully!")
        print(f"   Portfolio Value: ${snapshot['portfolio_value']:,.2f}")
        print(f"   Daily Trades: {snapshot['daily_trades']}")
        print(f"   Win Rate: {snapshot['win_rate_pct']:.1f}%")
    else:
        print(f"❌ Error collecting snapshot: {snapshot['error']}")
    
    # Try to generate 7-day report
    print("\n" + "="*60)
    print(tracker.generate_7day_report())


if __name__ == "__main__":
    main()
