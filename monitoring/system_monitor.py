"""
System Monitoring for Phase 5 - Extended Paper Trading
Tracks system health, performance, and trading metrics
"""
import time
import psutil
import requests
from datetime import datetime, timedelta
from typing import Dict, List
import json
import os
from pathlib import Path

class SystemMonitor:
    """Monitor system health and performance metrics"""
    
    def __init__(self, log_dir: str = "logs/trading"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.api_url = "http://localhost:9000"
        self.start_time = datetime.now()
        
    def get_system_metrics(self) -> Dict:
        """Collect system-level metrics"""
        return {
            "timestamp": datetime.now().isoformat(),
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "memory_used_gb": psutil.virtual_memory().used / (1024**3),
            "disk_usage_percent": psutil.disk_usage('/').percent,
        }
    
    def get_api_metrics(self) -> Dict:
        """Collect API metrics"""
        try:
            # Health check
            start = time.time()
            response = requests.get(f"{self.api_url}/api/health", timeout=5)
            latency = (time.time() - start) * 1000  # ms
            
            health_data = response.json() if response.status_code == 200 else {}
            
            # System status
            status_response = requests.get(f"{self.api_url}/api/status", timeout=5)
            status_data = status_response.json() if status_response.status_code == 200 else {}
            
            return {
                "api_healthy": response.status_code == 200,
                "api_latency_ms": round(latency, 2),
                "trading_engine_active": status_data.get("trading_engine", {}).get("active", False),
                "engine_uptime_seconds": status_data.get("trading_engine", {}).get("uptime_seconds", 0),
            }
        except Exception as e:
            return {
                "api_healthy": False,
                "error": str(e)
            }
    
    def get_trading_metrics(self) -> Dict:
        """Collect trading performance metrics"""
        try:
            # Portfolio
            portfolio = requests.get(f"{self.api_url}/api/portfolio", timeout=5).json()
            
            # Trades
            trades = requests.get(f"{self.api_url}/api/trades?limit=100", timeout=5).json()
            
            # Performance
            performance = requests.get(f"{self.api_url}/api/performance", timeout=5).json()
            
            # Calculate metrics
            total_trades = len(trades)
            winning_trades = sum(1 for t in trades if t.get('profit_loss', 0) > 0)
            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
            
            total_pnl = sum(t.get('profit_loss', 0) for t in trades)
            
            return {
                "portfolio_value": portfolio.get("total_value", 0),
                "cash_balance": portfolio.get("cash", 0),
                "num_positions": len(portfolio.get("positions", [])),
                "total_trades": total_trades,
                "win_rate_pct": round(win_rate, 2),
                "total_pnl": round(total_pnl, 2),
                "sharpe_ratio": performance.get("sharpe_ratio"),
                "max_drawdown_pct": performance.get("max_drawdown_pct"),
            }
        except Exception as e:
            return {
                "error": str(e)
            }
    
    def collect_snapshot(self) -> Dict:
        """Collect complete system snapshot"""
        snapshot = {
            "timestamp": datetime.now().isoformat(),
            "uptime_hours": (datetime.now() - self.start_time).total_seconds() / 3600,
            "system": self.get_system_metrics(),
            "api": self.get_api_metrics(),
            "trading": self.get_trading_metrics(),
        }
        return snapshot
    
    def log_snapshot(self, snapshot: Dict):
        """Log snapshot to file"""
        date_str = datetime.now().strftime("%Y%m%d")
        log_file = self.log_dir / f"monitoring_{date_str}.jsonl"
        
        with open(log_file, 'a') as f:
            f.write(json.dumps(snapshot) + '\n')
    
    def generate_report(self, hours: int = 24) -> str:
        """Generate performance report for last N hours"""
        cutoff = datetime.now() - timedelta(hours=hours)
        date_str = cutoff.strftime("%Y%m%d")
        log_file = self.log_dir / f"monitoring_{date_str}.jsonl"
        
        if not log_file.exists():
            return f"No data found for last {hours} hours"
        
        snapshots = []
        with open(log_file, 'r') as f:
            for line in f:
                snapshot = json.loads(line)
                snapshot_time = datetime.fromisoformat(snapshot['timestamp'])
                if snapshot_time >= cutoff:
                    snapshots.append(snapshot)
        
        if not snapshots:
            return f"No data found for last {hours} hours"
        
        # Calculate statistics
        cpu_values = [s['system']['cpu_percent'] for s in snapshots if 'system' in s]
        memory_values = [s['system']['memory_percent'] for s in snapshots if 'system' in s]
        latency_values = [s['api']['api_latency_ms'] for s in snapshots if 'api' in s and 'api_latency_ms' in s['api']]
        
        report = f"""
=== System Performance Report ({hours}h) ===
Period: {cutoff.strftime('%Y-%m-%d %H:%M')} to {datetime.now().strftime('%Y-%m-%d %H:%M')}
Snapshots Collected: {len(snapshots)}

SYSTEM METRICS:
  CPU Usage:     Avg: {sum(cpu_values)/len(cpu_values):.1f}%, Max: {max(cpu_values):.1f}%
  Memory Usage:  Avg: {sum(memory_values)/len(memory_values):.1f}%, Max: {max(memory_values):.1f}%
  
API METRICS:
  Latency:       Avg: {sum(latency_values)/len(latency_values):.1f}ms, Max: {max(latency_values):.1f}ms
  Uptime:        {sum(1 for s in snapshots if s.get('api', {}).get('api_healthy')) / len(snapshots) * 100:.1f}%

TRADING METRICS:
"""
        
        # Get latest trading metrics
        if snapshots[-1].get('trading'):
            trading = snapshots[-1]['trading']
            report += f"""  Portfolio Value: ${trading.get('portfolio_value', 0):,.2f}
  Total Trades:    {trading.get('total_trades', 0)}
  Win Rate:        {trading.get('win_rate_pct', 0):.1f}%
  Total P&L:       ${trading.get('total_pnl', 0):,.2f}
  Sharpe Ratio:    {trading.get('sharpe_ratio', 'N/A')}
  Max Drawdown:    {trading.get('max_drawdown_pct', 'N/A')}%
"""
        
        return report
    
    def run_continuous_monitoring(self, interval_seconds: int = 300):
        """Run continuous monitoring loop"""
        print(f"🔍 Starting continuous monitoring (interval: {interval_seconds}s)")
        print(f"📁 Logs: {self.log_dir}")
        print(f"⏰ Started: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        iteration = 0
        try:
            while True:
                iteration += 1
                snapshot = self.collect_snapshot()
                self.log_snapshot(snapshot)
                
                # Print summary
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Snapshot #{iteration}")
                print(f"  CPU: {snapshot['system']['cpu_percent']:.1f}% | "
                      f"MEM: {snapshot['system']['memory_percent']:.1f}% | "
                      f"API: {snapshot['api'].get('api_latency_ms', 'N/A')}ms | "
                      f"Portfolio: ${snapshot['trading'].get('portfolio_value', 0):,.2f}")
                
                # Every hour, generate report
                if iteration % 12 == 0:  # 12 * 5min = 1 hour
                    print("\n" + self.generate_report(hours=24))
                
                time.sleep(interval_seconds)
                
        except KeyboardInterrupt:
            print("\n\n🛑 Monitoring stopped")
            print("\nGenerating final report...")
            print(self.generate_report(hours=24))


if __name__ == "__main__":
    monitor = SystemMonitor()
    
    # Run continuous monitoring (every 5 minutes)
    monitor.run_continuous_monitoring(interval_seconds=300)
