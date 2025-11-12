#!/usr/bin/env python3
"""
Test and compare trading strategies with historical data
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from data.database import get_db
from data.models import MarketData
from strategies.trading_strategies import MomentumStrategy, MeanReversionStrategy, BuyHoldStrategy, run_strategy_comparison

def test_trading_strategies():
    """Test and compare different trading strategies"""
    print("🎯 Advanced Trading Strategy Testing")
    print("=" * 50)
    
    # Get database session
    db = next(get_db())
    
    try:
        # Fetch comprehensive BTC data for backtesting
        market_data = db.query(MarketData).filter(
            MarketData.symbol == "BTCUSDT"
        ).order_by(MarketData.timestamp.asc()).all()
        
        if len(market_data) < 100:
            print("❌ Insufficient data for backtesting")
            return
        
        # Convert to DataFrame
        data = []
        for record in market_data:
            data.append({
                'timestamp': record.timestamp,
                'open_price': float(record.open_price),
                'high_price': float(record.high_price),
                'low_price': float(record.low_price),
                'close_price': float(record.close_price),
                'volume': float(record.volume)
            })
        
        df = pd.DataFrame(data)
        df.set_index('timestamp', inplace=True)
        
        print(f"📊 Backtesting with {len(df)} BTC/USDT data points")
        print(f"📅 Period: {df.index[0]} to {df.index[-1]}")
        print(f"💰 Price range: ${df['close_price'].min():.2f} - ${df['close_price'].max():.2f}")
        
        # Initial capital for backtesting
        initial_capital = 10000
        
        # Test individual strategies
        print("\n🚀 Testing Individual Strategies")
        print("-" * 40)
        
        # 1. Momentum Strategy
        print("\n📈 Momentum Strategy Analysis:")
        momentum_strategy = MomentumStrategy()
        momentum_result = momentum_strategy.backtest(df, initial_capital)
        
        mom_metrics = momentum_result['metrics']
        print(f"  Total Return: {mom_metrics['total_return']:.2%}")
        print(f"  Annualized Return: {mom_metrics['annualized_return']:.2%}")
        print(f"  Volatility: {mom_metrics['volatility']:.2%}")
        print(f"  Sharpe Ratio: {mom_metrics['sharpe_ratio']:.3f}")
        print(f"  Max Drawdown: {mom_metrics['max_drawdown']:.2%}")
        print(f"  Total Trades: {mom_metrics['total_trades']}")
        print(f"  Win Rate: {mom_metrics['win_rate']:.2%}")
        print(f"  Final Value: ${mom_metrics['final_portfolio_value']:.2f}")
        
        # 2. Mean Reversion Strategy  
        print("\n📊 Mean Reversion Strategy Analysis:")
        mean_rev_strategy = MeanReversionStrategy()
        mean_rev_result = mean_rev_strategy.backtest(df, initial_capital)
        
        mr_metrics = mean_rev_result['metrics']
        print(f"  Total Return: {mr_metrics['total_return']:.2%}")
        print(f"  Annualized Return: {mr_metrics['annualized_return']:.2%}")
        print(f"  Volatility: {mr_metrics['volatility']:.2%}")
        print(f"  Sharpe Ratio: {mr_metrics['sharpe_ratio']:.3f}")
        print(f"  Max Drawdown: {mr_metrics['max_drawdown']:.2%}")
        print(f"  Total Trades: {mr_metrics['total_trades']}")
        print(f"  Win Rate: {mr_metrics['win_rate']:.2%}")
        print(f"  Final Value: ${mr_metrics['final_portfolio_value']:.2f}")
        
        # 3. Buy & Hold Benchmark
        print("\n💎 Buy & Hold Benchmark:")
        buy_hold_strategy = BuyHoldStrategy()
        buy_hold_result = buy_hold_strategy.backtest(df, initial_capital)
        
        bh_metrics = buy_hold_result['metrics']
        print(f"  Total Return: {bh_metrics['total_return']:.2%}")
        print(f"  Annualized Return: {bh_metrics['annualized_return']:.2%}")
        print(f"  Volatility: {bh_metrics['volatility']:.2%}")
        print(f"  Sharpe Ratio: {bh_metrics['sharpe_ratio']:.3f}")
        print(f"  Max Drawdown: {bh_metrics['max_drawdown']:.2%}")
        print(f"  Final Value: ${bh_metrics['final_portfolio_value']:.2f}")
        
        # Strategy Comparison
        print("\n🏆 Strategy Performance Comparison")
        print("=" * 50)
        
        strategies_data = {
            'Momentum': mom_metrics,
            'Mean Reversion': mr_metrics,
            'Buy & Hold': bh_metrics
        }
        
        comparison_df = pd.DataFrame(strategies_data).T
        comparison_df = comparison_df[['total_return', 'sharpe_ratio', 'max_drawdown', 'total_trades']]
        
        print(comparison_df.round(4).to_string())
        
        # Find best strategy
        best_return = max(strategies_data.keys(), key=lambda x: strategies_data[x]['total_return'])
        best_sharpe = max(strategies_data.keys(), key=lambda x: strategies_data[x]['sharpe_ratio'])
        best_drawdown = min(strategies_data.keys(), key=lambda x: strategies_data[x]['max_drawdown'])
        
        print(f"\n🥇 Best Total Return: {best_return} ({strategies_data[best_return]['total_return']:.2%})")
        print(f"🥇 Best Sharpe Ratio: {best_sharpe} ({strategies_data[best_sharpe]['sharpe_ratio']:.3f})")
        print(f"🥇 Best Max Drawdown: {best_drawdown} ({strategies_data[best_drawdown]['max_drawdown']:.2%})")
        
        # Signal Analysis
        print("\n📡 Recent Trading Signals Analysis")
        print("-" * 40)
        
        # Generate signals for recent data
        momentum_signals = momentum_strategy.generate_signals(df)
        mean_rev_signals = mean_rev_strategy.generate_signals(df)
        
        recent_signals = pd.DataFrame({
            'Price': df['close_price'].tail(10),
            'Momentum': momentum_signals.tail(10).round(3),
            'Mean Reversion': mean_rev_signals.tail(10).round(3)
        })
        
        print("Last 10 periods:")
        print(recent_signals.to_string())
        
        # Current recommendations
        latest_momentum = momentum_signals.iloc[-1]
        latest_mean_rev = mean_rev_signals.iloc[-1]
        
        print(f"\n🤖 Current Signal Recommendations:")
        print(f"Momentum Strategy: {latest_momentum:.3f} ", end="")
        if latest_momentum > 0.3:
            print("🟢 BUY")
        elif latest_momentum < -0.3:
            print("🔴 SELL") 
        else:
            print("🟡 HOLD")
            
        print(f"Mean Reversion: {latest_mean_rev:.3f} ", end="")
        if latest_mean_rev > 0.3:
            print("🟢 BUY")
        elif latest_mean_rev < -0.3:
            print("🔴 SELL")
        else:
            print("🟡 HOLD")
        
        # Portfolio allocation recommendation
        combined_signal = (latest_momentum + latest_mean_rev) / 2
        print(f"\nCombined Signal: {combined_signal:.3f}")
        
        if combined_signal > 0.2:
            allocation = min(75, int(combined_signal * 100))
            print(f"💡 Recommended Allocation: {allocation}% BTC, {100-allocation}% Cash")
        elif combined_signal < -0.2:
            print("💡 Recommended Allocation: 0% BTC, 100% Cash (defensive)")
        else:
            print("💡 Recommended Allocation: 30% BTC, 70% Cash (neutral)")
        
        print("\n✅ Strategy testing completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during strategy testing: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_trading_strategies()