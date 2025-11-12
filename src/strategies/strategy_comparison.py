"""
Strategy Comparison Framework
Run multiple strategies side-by-side on same data and compare results
"""
import pandas as pd
import numpy as np
from typing import Dict, List
from datetime import datetime
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from strategies.optimized_strategy_week1_refined import Week1RefinedStrategy
from strategies.pivot_zone_strategy import PivotZoneStrategy


class StrategyComparison:
    """
    Compare multiple trading strategies on the same dataset
    Provides detailed performance metrics and trade analysis
    """
    
    def __init__(self):
        self.strategies = {
            'Week1Refined': Week1RefinedStrategy(),
            'PivotZone': PivotZoneStrategy()
        }
    
    def run_comparison(self, symbol: str = 'BTC/USDT', lookback_days: int = 90, initial_capital: float = 10000):
        """
        Run all strategies and compare results
        
        Args:
            symbol: Trading pair symbol
            lookback_days: Number of days to backtest
            initial_capital: Starting capital for each strategy
        
        Returns:
            Dict with comparison results
        """
        print("=" * 100)
        print("STRATEGY COMPARISON FRAMEWORK")
        print("=" * 100)
        print()
        print(f"📊 Symbol: {symbol}")
        print(f"📅 Period: {lookback_days} days")
        print(f"💰 Initial Capital: ${initial_capital:,.2f}")
        print()
        print("-" * 100)
        print()
        
        # Get historical data once for all strategies
        from data.database import get_db
        from data.models import MarketData
        
        db = next(get_db())
        end_date = datetime.now()
        start_date = end_date - pd.Timedelta(days=lookback_days)
        
        records = db.query(MarketData).filter(
            MarketData.symbol == symbol,
            MarketData.timestamp >= start_date,
            MarketData.timestamp <= end_date
        ).order_by(MarketData.timestamp).all()
        
        if not records:
            print(f"❌ No data found for {symbol}")
            return {}
        
        # Convert to DataFrame
        data = pd.DataFrame([{
            'timestamp': r.timestamp,
            'open': float(r.open_price),
            'high': float(r.high_price),
            'low': float(r.low_price),
            'close': float(r.close_price),
            'volume': float(r.volume)
        } for r in records])
        
        data['timestamp'] = pd.to_datetime(data['timestamp'])
        
        # Add _price suffix for strategies that expect it (Week1Refined)
        data['open_price'] = data['open']
        data['high_price'] = data['high']
        data['low_price'] = data['low']
        data['close_price'] = data['close']
        
        print(f"📊 Loaded {len(data)} candles from {data['timestamp'].min()} to {data['timestamp'].max()}")
        print()
        
        results = {}
        
        for name, strategy in self.strategies.items():
            print(f"🧪 Testing: {name}")
            print("-" * 100)
            
            try:
                # Check which backtest interface the strategy uses
                import inspect
                sig = inspect.signature(strategy.backtest)
                params = sig.parameters
                
                if 'symbol' in params:
                    # New interface: strategy handles data loading
                    result = strategy.backtest(symbol=symbol, lookback_days=lookback_days, initial_capital=initial_capital)
                else:
                    # Old interface: pass DataFrame directly
                    result = strategy.backtest(data=data, initial_capital=initial_capital)
                
                # Normalize result format
                if 'total_trades' not in result:
                    # Week1Refined format - calculate missing metrics
                    sell_trades = [t for t in result.get('trades', []) if t.get('type') == 'SELL']
                    winning_trades = [t for t in sell_trades if t.get('return', 0) > 0]
                    losing_trades = [t for t in sell_trades if t.get('return', 0) <= 0]
                    
                    result['total_trades'] = len(sell_trades)
                    result['winning_trades'] = len(winning_trades)
                    result['losing_trades'] = len(losing_trades)
                    result['avg_win'] = np.mean([t.get('return', 0) for t in winning_trades]) if winning_trades else 0
                    result['avg_loss'] = np.mean([t.get('return', 0) for t in losing_trades]) if losing_trades else 0
                
                results[name] = result
                
                # Display results
                if 'error' in result:
                    print(f"❌ Error: {result['error']}")
                else:
                    print(f"  Total Trades: {result['total_trades']}")
                    print(f"  Win Rate: {result['win_rate']:.2f}%")
                    print(f"  Total Return: {result['total_return']:.2f}%")
                    print(f"  Max Drawdown: {result['max_drawdown']:.2f}%")
                    print(f"  Final Value: ${result['final_value']:,.2f}")
                    
                    if result['total_trades'] > 0:
                        print(f"  Avg Win: {result['avg_win']:.2f}%")
                        print(f"  Avg Loss: {result['avg_loss']:.2f}%")
                        
                        # Risk-reward ratio
                        if result['avg_loss'] != 0:
                            rr_ratio = abs(result['avg_win'] / result['avg_loss'])
                            print(f"  Risk/Reward Ratio: {rr_ratio:.2f}")
                        
                        # Expectancy
                        win_rate_decimal = result['win_rate'] / 100
                        expectancy = (win_rate_decimal * result['avg_win']) + ((1 - win_rate_decimal) * result['avg_loss'])
                        print(f"  Expectancy: {expectancy:.2f}% per trade")
                
                print()
                
            except Exception as e:
                print(f"❌ Error running {name}: {str(e)}")
                print()
                results[name] = {'error': str(e)}
        
        # Comparison table
        print("=" * 100)
        print("COMPARISON TABLE")
        print("=" * 100)
        print()
        
        # Build comparison data
        comparison_data = []
        for name, result in results.items():
            if 'error' not in result:
                comparison_data.append({
                    'Strategy': name,
                    'Trades': result['total_trades'],
                    'Win Rate': f"{result['win_rate']:.2f}%",
                    'Return': f"{result['total_return']:.2f}%",
                    'Max DD': f"{result['max_drawdown']:.2f}%",
                    'Final Value': f"${result['final_value']:,.2f}",
                    'Avg Win': f"{result['avg_win']:.2f}%" if result['total_trades'] > 0 else 'N/A',
                    'Avg Loss': f"{result['avg_loss']:.2f}%" if result['total_trades'] > 0 else 'N/A'
                })
        
        if comparison_data:
            df = pd.DataFrame(comparison_data)
            print(df.to_string(index=False))
            print()
        
        # Winner analysis
        print("=" * 100)
        print("WINNER ANALYSIS")
        print("=" * 100)
        print()
        
        valid_results = {k: v for k, v in results.items() if 'error' not in v and v['total_trades'] > 0}
        
        if valid_results:
            # Best win rate
            best_wr = max(valid_results.items(), key=lambda x: x[1]['win_rate'])
            print(f"🏆 Best Win Rate: {best_wr[0]} ({best_wr[1]['win_rate']:.2f}%)")
            
            # Best return
            best_return = max(valid_results.items(), key=lambda x: x[1]['total_return'])
            print(f"💰 Best Return: {best_return[0]} ({best_return[1]['total_return']:.2f}%)")
            
            # Lowest drawdown (closest to 0)
            best_dd = max(valid_results.items(), key=lambda x: x[1]['max_drawdown'])
            print(f"🛡️  Lowest Drawdown: {best_dd[0]} ({best_dd[1]['max_drawdown']:.2f}%)")
            
            # Most trades
            most_trades = max(valid_results.items(), key=lambda x: x[1]['total_trades'])
            print(f"📊 Most Active: {most_trades[0]} ({most_trades[1]['total_trades']} trades)")
            
            print()
            
            # Overall recommendation
            print("=" * 100)
            print("RECOMMENDATION")
            print("=" * 100)
            print()
            
            # Score each strategy (weighted)
            scores = {}
            for name, result in valid_results.items():
                score = 0
                
                # Win rate (40% weight)
                score += (result['win_rate'] / 100) * 40
                
                # Return (30% weight) - normalize to 0-30 scale
                max_return = max(r['total_return'] for r in valid_results.values())
                if max_return > 0:
                    score += (result['total_return'] / max_return) * 30
                
                # Drawdown (20% weight) - lower is better
                max_dd = max(abs(r['max_drawdown']) for r in valid_results.values())
                if max_dd > 0:
                    score += (1 - abs(result['max_drawdown']) / max_dd) * 20
                
                # Trade count (10% weight) - more is better up to a point
                if result['total_trades'] >= 3:
                    score += 10
                elif result['total_trades'] >= 1:
                    score += 5
                
                scores[name] = score
            
            # Winner
            winner = max(scores.items(), key=lambda x: x[1])
            print(f"🥇 Overall Winner: {winner[0]}")
            print(f"   Score: {winner[1]:.2f}/100")
            print()
            
            winner_result = valid_results[winner[0]]
            print(f"   Why it won:")
            print(f"   - Win Rate: {winner_result['win_rate']:.2f}% (target: 60%+)")
            print(f"   - Return: {winner_result['total_return']:.2f}% in {lookback_days} days")
            print(f"   - Max Drawdown: {winner_result['max_drawdown']:.2f}% (target: <10%)")
            print(f"   - Total Trades: {winner_result['total_trades']}")
            
            # Recommendation
            print()
            print("   Recommendation:")
            if winner_result['win_rate'] >= 60 and winner_result['total_trades'] >= 3:
                print(f"   ✅ {winner[0]} is READY FOR PAPER TRADING")
                print(f"   - Meets 60% win rate target")
                print(f"   - Has sufficient trade sample")
                print(f"   - Deploy to live_engine.py and monitor for 60 days")
            elif winner_result['win_rate'] >= 60:
                print(f"   ⚠️  {winner[0]} looks promising but needs more data")
                print(f"   - Win rate meets target but only {winner_result['total_trades']} trades")
                print(f"   - Consider testing on longer period or different market conditions")
            else:
                print(f"   ⚠️  {winner[0]} needs more optimization")
                print(f"   - Win rate {winner_result['win_rate']:.2f}% below 60% target")
                print(f"   - Continue parameter tuning or try different approach")
            
            print()
            print("   Deployment Plan:")
            print("   1. Update live_engine.py to use winner strategy")
            print("   2. Enable paper trading mode (no real money)")
            print("   3. Monitor for 60 days minimum")
            print("   4. Track: win rate, drawdown, Sharpe ratio")
            print("   5. If consistent 60%+ win rate → go live with small capital")
            
        else:
            print("❌ No valid results to compare")
        
        print()
        print("=" * 100)
        
        return results
    
    def detailed_trade_analysis(self, results: Dict):
        """
        Show detailed trade-by-trade comparison
        
        Args:
            results: Results dict from run_comparison()
        """
        print()
        print("=" * 100)
        print("DETAILED TRADE ANALYSIS")
        print("=" * 100)
        print()
        
        for name, result in results.items():
            if 'error' in result or result['total_trades'] == 0:
                continue
            
            print(f"📊 {name} - Trade Breakdown")
            print("-" * 100)
            
            trades = result['trades']
            
            # Show first 5 and last 5 trades
            show_trades = trades[:5] + trades[-5:] if len(trades) > 10 else trades
            
            for i, trade in enumerate(show_trades):
                # Handle different trade formats
                if 'entry_time' in trade:
                    # PivotZone format
                    entry_str = trade['entry_time'].strftime('%b %d, %I:%M %p')
                    exit_str = trade['exit_time'].strftime('%b %d, %I:%M %p')
                    
                    pnl_symbol = "✅" if trade['pnl'] > 0 else "❌"
                    
                    print(f"  Trade {i+1}:")
                    print(f"    {pnl_symbol} {entry_str} @ ${trade['entry_price']:.2f} → {exit_str} @ ${trade['exit_price']:.2f}")
                    print(f"    PnL: {trade['pnl_pct']:.2f}% | Exit: {trade['exit_reason']}", end='')
                    
                    if 'zone' in trade:
                        print(f" | Zone: {trade['zone']}")
                    else:
                        print()
                else:
                    # Week1Refined format
                    if trade['type'] == 'BUY':
                        print(f"  Trade {i+1}: BUY @ ${trade['price']:.2f}")
                    elif trade['type'] == 'SELL':
                        pnl_symbol = "✅" if trade.get('return', 0) > 0 else "❌"
                        print(f"  Trade {i+1}: {pnl_symbol} SELL @ ${trade['price']:.2f} | Return: {trade.get('return', 0):.2f}% | Reason: {trade.get('reason', 'N/A')}")
                
                print()
            
            if len(trades) > 10:
                print(f"  ... ({len(trades) - 10} more trades)")
                print()
        
        print("=" * 100)


def main():
    """Run strategy comparison"""
    comparison = StrategyComparison()
    
    # Run comparison on 90 days
    results = comparison.run_comparison(
        symbol='BTC/USDT',
        lookback_days=90,
        initial_capital=10000
    )
    
    # Show detailed trade analysis
    comparison.detailed_trade_analysis(results)


if __name__ == '__main__':
    main()
