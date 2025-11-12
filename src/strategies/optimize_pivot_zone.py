"""
Pivot Zone Strategy Optimizer
Test different parameter combinations to improve performance
"""
import pandas as pd
import numpy as np
from datetime import datetime
from itertools import product
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from strategies.pivot_zone_strategy import PivotZoneStrategy


class PivotZoneOptimizer:
    """
    Optimize Pivot Zone Strategy parameters
    Goal: Achieve 60%+ win rate on historical data
    """
    
    def __init__(self):
        self.symbol = 'BTC/USDT'
        self.lookback_days = 90
        self.initial_capital = 10000
        
        # Parameter ranges to test
        self.param_grid = {
            'min_volume_multiplier': [1.0, 1.2, 1.5, 2.0],
            'stop_loss_pct': [0.03, 0.05, 0.08, 0.10],
            'take_profit_pct': [0.10, 0.15, 0.20, 0.25],
            'max_position_pct': [0.20, 0.30, 0.40],
            'use_trend_filter': [True, False],
            'ma_trend_period': [20, 50, 100]
        }
    
    def optimize(self, max_tests: int = 50):
        """
        Run optimization to find best parameter combination
        
        Args:
            max_tests: Maximum number of parameter combinations to test
        
        Returns:
            List of results sorted by score
        """
        print("=" * 100)
        print("PIVOT ZONE STRATEGY OPTIMIZER")
        print("=" * 100)
        print()
        print(f"🎯 Goal: Achieve 60%+ win rate")
        print(f"📊 Symbol: {self.symbol}")
        print(f"📅 Period: {self.lookback_days} days")
        print(f"🔬 Max Tests: {max_tests}")
        print()
        print("-" * 100)
        print()
        
        # Generate parameter combinations
        param_names = list(self.param_grid.keys())
        param_values = list(self.param_grid.values())
        
        combinations = list(product(*param_values))
        
        # Limit tests
        if len(combinations) > max_tests:
            import random
            combinations = random.sample(combinations, max_tests)
            print(f"⚠️  Sampling {max_tests} from {len(list(product(*param_values)))} total combinations")
            print()
        
        results = []
        
        for i, params in enumerate(combinations, 1):
            # Create parameter dict
            param_dict = dict(zip(param_names, params))
            
            print(f"Test {i}/{len(combinations)}: Testing parameters...")
            print(f"  Volume: {param_dict['min_volume_multiplier']}x")
            print(f"  Stop Loss: {param_dict['stop_loss_pct']*100:.0f}%")
            print(f"  Take Profit: {param_dict['take_profit_pct']*100:.0f}%")
            print(f"  Position: {param_dict['max_position_pct']*100:.0f}%")
            print(f"  Trend Filter: {param_dict['use_trend_filter']}")
            print(f"  MA Period: {param_dict['ma_trend_period']}")
            
            try:
                # Create strategy with these parameters
                strategy = PivotZoneStrategy()
                strategy.min_volume_multiplier = param_dict['min_volume_multiplier']
                strategy.stop_loss_pct = param_dict['stop_loss_pct']
                strategy.take_profit_pct = param_dict['take_profit_pct']
                strategy.max_position_pct = param_dict['max_position_pct']
                strategy.use_trend_filter = param_dict['use_trend_filter']
                strategy.ma_trend_period = param_dict['ma_trend_period']
                
                # Run backtest
                result = strategy.backtest(
                    symbol=self.symbol,
                    lookback_days=self.lookback_days,
                    initial_capital=self.initial_capital
                )
                
                if 'error' not in result and result['total_trades'] > 0:
                    # Calculate score (weighted)
                    score = self._calculate_score(result)
                    
                    result['parameters'] = param_dict
                    result['score'] = score
                    results.append(result)
                    
                    print(f"  ✅ Win Rate: {result['win_rate']:.1f}% | Return: {result['total_return']:.2f}% | Score: {score:.1f}")
                else:
                    print(f"  ❌ Failed: {result.get('error', 'No trades')}")
                
            except Exception as e:
                print(f"  ❌ Error: {str(e)}")
            
            print()
        
        # Sort by score
        results.sort(key=lambda x: x['score'], reverse=True)
        
        # Display top results
        print("=" * 100)
        print("TOP 10 RESULTS")
        print("=" * 100)
        print()
        
        for i, result in enumerate(results[:10], 1):
            print(f"#{i} - Score: {result['score']:.1f}/100")
            print(f"   Win Rate: {result['win_rate']:.2f}% | Return: {result['total_return']:.2f}% | Trades: {result['total_trades']}")
            print(f"   Max DD: {result['max_drawdown']:.2f}% | Avg Win: {result['avg_win']:.2f}% | Avg Loss: {result['avg_loss']:.2f}%")
            print(f"   Parameters:")
            for key, value in result['parameters'].items():
                print(f"      {key}: {value}")
            print()
        
        # Best result analysis
        if results:
            best = results[0]
            print("=" * 100)
            print("🏆 BEST CONFIGURATION")
            print("=" * 100)
            print()
            print(f"Score: {best['score']:.1f}/100")
            print(f"Win Rate: {best['win_rate']:.2f}% (Target: 60%+)")
            print(f"Total Return: {best['total_return']:.2f}%")
            print(f"Max Drawdown: {best['max_drawdown']:.2f}%")
            print(f"Total Trades: {best['total_trades']}")
            print()
            
            if best['win_rate'] >= 60:
                print("✅ TARGET ACHIEVED! This configuration meets the 60% win rate goal.")
            else:
                print(f"⚠️  Still {60 - best['win_rate']:.1f}% below target. Continue optimization.")
            
            print()
            print("Optimized Parameters:")
            print("-" * 100)
            for key, value in best['parameters'].items():
                print(f"  strategy.{key} = {value}")
            print()
            print("=" * 100)
        
        return results
    
    def _calculate_score(self, result: Dict) -> float:
        """
        Calculate weighted score for a backtest result
        
        Weights:
        - Win rate: 40%
        - Return: 30%
        - Drawdown: 20%
        - Trade count: 10%
        """
        score = 0.0
        
        # Win rate (40 points max)
        win_rate_score = min(result['win_rate'] / 100 * 40, 40)
        score += win_rate_score
        
        # Return (30 points max) - normalize to 0-30
        # Positive returns get full points, negative get 0
        if result['total_return'] > 0:
            return_score = min(result['total_return'] / 10 * 30, 30)  # 10% return = full points
        else:
            return_score = 0
        score += return_score
        
        # Drawdown (20 points max) - lower is better
        # 0% DD = 20 points, 10% DD = 0 points
        dd_score = max(0, 20 - abs(result['max_drawdown']) * 2)
        score += dd_score
        
        # Trade count (10 points max)
        # Want at least 5 trades for statistical significance
        if result['total_trades'] >= 10:
            trade_score = 10
        elif result['total_trades'] >= 5:
            trade_score = 7
        elif result['total_trades'] >= 3:
            trade_score = 5
        else:
            trade_score = 2
        score += trade_score
        
        return score
    
    def test_specific_config(self, params: Dict):
        """Test a specific parameter configuration"""
        strategy = PivotZoneStrategy()
        
        for key, value in params.items():
            setattr(strategy, key, value)
        
        result = strategy.backtest(
            symbol=self.symbol,
            lookback_days=self.lookback_days,
            initial_capital=self.initial_capital
        )
        
        if 'error' not in result:
            score = self._calculate_score(result)
            result['parameters'] = params
            result['score'] = score
        
        return result


def main():
    """Run Pivot Zone optimization"""
    optimizer = PivotZoneOptimizer()
    
    print("Starting optimization...")
    print("This may take a few minutes...")
    print()
    
    results = optimizer.optimize(max_tests=30)  # Test 30 combinations
    
    if results:
        print(f"\n✅ Optimization complete! Tested {len(results)} configurations.")
        print(f"Best win rate achieved: {results[0]['win_rate']:.2f}%")
        print(f"Best configuration score: {results[0]['score']:.1f}/100")
        
        # Save results
        import json
        output_file = 'logs/pivot_zone_optimization_results.json'
        os.makedirs('logs', exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump(results[:10], f, indent=2, default=str)
        
        print(f"\n💾 Top 10 results saved to {output_file}")
    else:
        print("\n❌ No valid results. Check error messages above.")


if __name__ == '__main__':
    main()
