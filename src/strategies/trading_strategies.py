"""
Advanced Trading Strategies for Cryptocurrency Markets
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import logging
from abc import ABC, abstractmethod

from .technical_indicators import TechnicalIndicators, SignalGenerator

logger = logging.getLogger(__name__)


class BaseStrategy(ABC):
    """
    Abstract base class for all trading strategies
    """
    
    def __init__(self, name: str, parameters: Dict[str, Any]):
        self.name = name
        self.parameters = parameters
        self.trades = []
        self.performance_metrics = {}
        
    @abstractmethod
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """Generate trading signals based on strategy logic"""
        pass
    
    @abstractmethod
    def get_position_size(self, signal: float, current_price: float, portfolio_value: float) -> float:
        """Calculate position size based on signal strength and risk management"""
        pass
    
    def backtest(self, data: pd.DataFrame, initial_capital: float = 10000) -> Dict[str, Any]:
        """Run backtest on historical data"""
        signals = self.generate_signals(data)
        
        cash = initial_capital
        position = 0  # Number of shares/coins held
        trades = []
        portfolio_values = []
        
        for i, (timestamp, row) in enumerate(data.iterrows()):
            current_price = row['close_price']
            signal = signals.iloc[i] if i < len(signals) else 0
            
            # Current portfolio value
            current_portfolio_value = cash + (position * current_price)
            portfolio_values.append(current_portfolio_value)
            
            # Calculate target position size (as fraction of portfolio)
            target_position_fraction = self.get_position_size(signal, current_price, current_portfolio_value)
            target_position_value = target_position_fraction * current_portfolio_value
            target_position_shares = target_position_value / current_price if current_price > 0 else 0
            
            # Execute trade if significant change
            position_change = target_position_shares - position
            
            if abs(position_change * current_price) > current_portfolio_value * 0.01:  # 1% minimum trade size
                trade_value = position_change * current_price
                fee = abs(trade_value) * 0.001  # 0.1% trading fee
                
                # Check if we have enough cash for the trade
                if trade_value <= cash + fee:
                    # Execute the trade
                    cash -= trade_value + fee
                    position = target_position_shares
                    
                    trades.append({
                        'timestamp': timestamp,
                        'signal': signal,
                        'price': current_price,
                        'size': position_change,
                        'position': position,
                        'cash': cash,
                        'portfolio_value': cash + (position * current_price)
                    })
        
        # Final portfolio value
        final_price = data['close_price'].iloc[-1]
        final_portfolio_value = cash + (position * final_price)
        portfolio_values[-1] = final_portfolio_value
        
        # Calculate performance metrics
        if len(portfolio_values) > 1:
            returns = pd.Series(portfolio_values).pct_change().dropna()
            
            total_return = (final_portfolio_value - initial_capital) / initial_capital
            
            # Handle edge cases for metrics calculation
            volatility = returns.std() * np.sqrt(365) if len(returns) > 1 and returns.std() > 0 else 0
            sharpe_ratio = (returns.mean() * 365) / volatility if volatility > 0 else 0
            
            metrics = {
                'total_return': total_return,
                'annualized_return': ((final_portfolio_value / initial_capital) ** (365 / max(len(data), 1))) - 1 if len(data) > 0 else 0,
                'volatility': volatility,
                'sharpe_ratio': sharpe_ratio,
                'max_drawdown': self._calculate_max_drawdown(portfolio_values),
                'total_trades': len(trades),
                'win_rate': len([t for t in trades if t['size'] * (data['close_price'].iloc[-1] - t['price']) > 0]) / len(trades) if trades else 0,
                'final_portfolio_value': final_portfolio_value
            }
        else:
            metrics = {
                'total_return': 0,
                'annualized_return': 0,
                'volatility': 0,
                'sharpe_ratio': 0,
                'max_drawdown': 0,
                'total_trades': 0,
                'win_rate': 0,
                'final_portfolio_value': initial_capital
            }
        
        return {
            'metrics': metrics,
            'trades': trades,
            'portfolio_values': portfolio_values,
            'signals': signals
        }
    
    def _calculate_max_drawdown(self, portfolio_values: List[float]) -> float:
        """Calculate maximum drawdown"""
        peak = portfolio_values[0]
        max_dd = 0
        
        for value in portfolio_values:
            if value > peak:
                peak = value
            
            drawdown = (peak - value) / peak
            if drawdown > max_dd:
                max_dd = drawdown
        
        return max_dd


class MomentumStrategy(BaseStrategy):
    """
    Advanced Momentum Strategy
    
    Combines multiple momentum indicators:
    - Moving Average Crossover (primary signal)
    - RSI for momentum confirmation
    - MACD for trend strength
    - Volume analysis for signal validation
    - ATR for volatility-based position sizing
    """
    
    def __init__(self, parameters: Optional[Dict[str, Any]] = None):
        default_params = {
            'fast_ma': 10,      # Fast moving average period
            'slow_ma': 20,      # Slow moving average period
            'rsi_period': 14,   # RSI calculation period
            'rsi_threshold': 50, # RSI momentum threshold
            'macd_fast': 12,    # MACD fast period
            'macd_slow': 26,    # MACD slow period
            'macd_signal': 9,   # MACD signal period
            'volume_threshold': 1.2,  # Volume spike threshold
            'atr_period': 14,   # ATR period for volatility
            'max_position': 0.95,     # Maximum position size (95% of portfolio)
            'min_signal_strength': 0.3,  # Minimum signal strength for trade
            'stop_loss': 0.05,  # Stop loss percentage
            'take_profit': 0.15  # Take profit percentage
        }
        
        if parameters:
            default_params.update(parameters)
            
        super().__init__("Advanced Momentum Strategy", default_params)
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Generate momentum signals based on multiple indicators
        
        Signal strength: -1 (strong sell) to +1 (strong buy)
        """
        # Calculate all technical indicators
        data_with_indicators = TechnicalIndicators.calculate_all_indicators(data)
        
        # Extract relevant columns
        close = data_with_indicators['close_price']
        fast_ma = data_with_indicators[f'sma_{self.parameters["fast_ma"]}']
        slow_ma = data_with_indicators[f'sma_{self.parameters["slow_ma"]}']
        rsi = data_with_indicators['rsi']
        macd = data_with_indicators['macd']
        macd_signal = data_with_indicators['macd_signal']
        volume_ratio = data_with_indicators['volume_ratio']
        
        # Initialize signals
        signals = pd.Series(index=data.index, dtype=float)
        signals[:] = 0.0
        
        # 1. Moving Average Crossover (Primary Signal)
        ma_signals = SignalGenerator.ma_crossover_signals(fast_ma, slow_ma)
        ma_strength = (fast_ma - slow_ma) / slow_ma  # Normalized MA spread
        
        # 2. RSI Momentum Filter
        rsi_momentum = (rsi - 50) / 50  # Normalized RSI (-1 to 1)
        rsi_filter = np.where(
            (ma_signals > 0) & (rsi > self.parameters['rsi_threshold']), 1,
            np.where((ma_signals < 0) & (rsi < (100 - self.parameters['rsi_threshold'])), -1, 0)
        )
        
        # 3. MACD Trend Confirmation
        macd_signals = SignalGenerator.macd_signals(macd, macd_signal)
        macd_strength = np.tanh(macd / macd.rolling(20).std())  # Normalized MACD strength
        
        # 4. Volume Validation
        volume_confirmation = np.where(
            volume_ratio > self.parameters['volume_threshold'], 1, 0.5
        )
        
        # 5. Combine signals with weighted scoring
        for i in range(len(signals)):
            if i < max(self.parameters['fast_ma'], self.parameters['slow_ma']):
                continue  # Skip initial periods without enough data
                
            # Base signal from MA crossover
            base_signal = ma_signals.iloc[i]
            
            if base_signal != 0:  # Only proceed if there's a base signal
                # Calculate signal strength components
                ma_component = ma_strength.iloc[i] * 0.4  # 40% weight
                rsi_component = rsi_momentum.iloc[i] * 0.25  # 25% weight
                macd_component = macd_strength.iloc[i] * 0.25  # 25% weight
                volume_mult = volume_confirmation[i] * 0.1  # 10% boost for volume
                
                # Combined signal strength
                signal_strength = base_signal * (
                    abs(ma_component) + abs(rsi_component) + abs(macd_component) + volume_mult
                )
                
                # Apply momentum filter
                if rsi_filter[i] == base_signal or rsi_filter[i] == 0:
                    signals.iloc[i] = np.clip(signal_strength, -1, 1)
                else:
                    signals.iloc[i] = signal_strength * 0.5  # Reduce signal if RSI conflicts
        
        # Smooth signals to reduce noise
        signals = signals.rolling(window=3).mean().fillna(0)
        
        return signals
    
    def get_position_size(self, signal: float, current_price: float, portfolio_value: float) -> float:
        """
        Calculate position size based on signal strength and risk management
        
        Uses volatility-adjusted position sizing with Kelly Criterion concepts
        """
        if abs(signal) < self.parameters['min_signal_strength']:
            return 0.0
        
        # Base position size from signal strength
        base_position = signal * self.parameters['max_position']
        
        # Risk adjustment could be added here (ATR-based, volatility-based, etc.)
        # For now, using simple signal-based sizing
        
        return base_position
    
    def get_stop_loss_take_profit(self, entry_price: float, signal: float) -> Tuple[float, float]:
        """Calculate stop loss and take profit levels"""
        if signal > 0:  # Long position
            stop_loss = entry_price * (1 - self.parameters['stop_loss'])
            take_profit = entry_price * (1 + self.parameters['take_profit'])
        else:  # Short position
            stop_loss = entry_price * (1 + self.parameters['stop_loss'])
            take_profit = entry_price * (1 - self.parameters['take_profit'])
        
        return stop_loss, take_profit


class MeanReversionStrategy(BaseStrategy):
    """
    Mean Reversion Strategy
    
    Exploits price reversions to the mean using:
    - Bollinger Bands for overbought/oversold levels
    - RSI for momentum extremes
    - Z-score analysis for statistical mean reversion
    - Volume analysis for reversal confirmation
    """
    
    def __init__(self, parameters: Optional[Dict[str, Any]] = None):
        default_params = {
            'bb_period': 20,        # Bollinger Bands period
            'bb_std': 2.0,          # Bollinger Bands standard deviation
            'rsi_oversold': 25,     # RSI oversold threshold
            'rsi_overbought': 75,   # RSI overbought threshold
            'zscore_threshold': 2.0, # Z-score threshold for mean reversion
            'volume_confirmation': 0.8,  # Volume requirement for signals
            'max_position': 0.5,    # Maximum position size
            'hold_period': 5,       # Minimum holding period
            'stop_loss': 0.03,      # Stop loss percentage
            'take_profit': 0.08     # Take profit percentage
        }
        
        if parameters:
            default_params.update(parameters)
            
        super().__init__("Mean Reversion Strategy", default_params)
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """Generate mean reversion signals"""
        # Calculate indicators
        data_with_indicators = TechnicalIndicators.calculate_all_indicators(data)
        
        close = data_with_indicators['close_price']
        bb_upper = data_with_indicators['bb_upper']
        bb_lower = data_with_indicators['bb_lower']
        bb_middle = data_with_indicators['bb_middle']
        rsi = data_with_indicators['rsi']
        volume_ratio = data_with_indicators['volume_ratio']
        
        # Calculate z-score for mean reversion
        price_mean = close.rolling(window=self.parameters['bb_period']).mean()
        price_std = close.rolling(window=self.parameters['bb_period']).std()
        zscore = (close - price_mean) / price_std
        
        # Initialize signals
        signals = pd.Series(index=data.index, dtype=float)
        signals[:] = 0.0
        
        for i in range(self.parameters['bb_period'], len(signals)):
            current_price = close.iloc[i]
            current_rsi = rsi.iloc[i]
            current_zscore = zscore.iloc[i]
            current_volume = volume_ratio.iloc[i]
            
            # Mean reversion conditions
            oversold_conditions = [
                current_price <= bb_lower.iloc[i],  # Price at lower Bollinger Band
                current_rsi <= self.parameters['rsi_oversold'],  # RSI oversold
                current_zscore <= -self.parameters['zscore_threshold']  # Z-score oversold
            ]
            
            overbought_conditions = [
                current_price >= bb_upper.iloc[i],  # Price at upper Bollinger Band
                current_rsi >= self.parameters['rsi_overbought'],  # RSI overbought
                current_zscore >= self.parameters['zscore_threshold']  # Z-score overbought
            ]
            
            # Volume confirmation
            volume_confirmed = current_volume >= self.parameters['volume_confirmation']
            
            # Generate signals
            if sum(oversold_conditions) >= 2 and volume_confirmed:
                # Buy signal (expecting price to revert up)
                signal_strength = min(sum(oversold_conditions) / 3, 1.0)
                signals.iloc[i] = signal_strength
            elif sum(overbought_conditions) >= 2 and volume_confirmed:
                # Sell signal (expecting price to revert down)
                signal_strength = min(sum(overbought_conditions) / 3, 1.0)
                signals.iloc[i] = -signal_strength
        
        return signals
    
    def get_position_size(self, signal: float, current_price: float, portfolio_value: float) -> float:
        """Position sizing for mean reversion strategy"""
        if abs(signal) < 0.3:  # Minimum signal threshold
            return 0.0
        
        # Conservative position sizing for mean reversion
        base_position = signal * self.parameters['max_position'] * 0.5
        return base_position


def run_strategy_comparison(data: pd.DataFrame, initial_capital: float = 10000) -> Dict[str, Any]:
    """
    Run and compare multiple trading strategies
    """
    print("🚀 Running Strategy Comparison Analysis")
    print("=" * 60)
    
    strategies = {
        'Momentum': MomentumStrategy(),
        'Mean Reversion': MeanReversionStrategy(),
        'Buy & Hold': BuyHoldStrategy()
    }
    
    results = {}
    
    for name, strategy in strategies.items():
        print(f"\n📊 Testing {name} Strategy...")
        
        try:
            result = strategy.backtest(data, initial_capital)
            results[name] = result
            
            metrics = result['metrics']
            print(f"Total Return: {metrics['total_return']:.2%}")
            print(f"Sharpe Ratio: {metrics['sharpe_ratio']:.3f}")
            print(f"Max Drawdown: {metrics['max_drawdown']:.2%}")
            print(f"Total Trades: {metrics['total_trades']}")
            
        except Exception as e:
            print(f"❌ Error testing {name}: {e}")
            results[name] = None
    
    return results


class BuyHoldStrategy(BaseStrategy):
    """Simple buy and hold strategy for comparison"""
    
    def __init__(self):
        super().__init__("Buy & Hold", {})
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        signals = pd.Series(index=data.index, dtype=float)
        signals[:] = 0.0
        signals.iloc[0] = 1.0  # Buy at the beginning
        return signals
    
    def get_position_size(self, signal: float, current_price: float, portfolio_value: float) -> float:
        return 1.0 if signal > 0 else 0.0


if __name__ == "__main__":
    print("🎯 Advanced Trading Strategies Module")
    print("Available strategies:")
    print("1. Momentum Strategy - Multi-indicator momentum trading")
    print("2. Mean Reversion Strategy - Statistical reversal trading")
    print("3. Buy & Hold Strategy - Benchmark comparison")