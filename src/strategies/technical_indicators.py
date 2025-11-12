"""
Technical Analysis Indicators for Trading Strategies
"""
import pandas as pd
import numpy as np
from typing import Optional, Tuple, Dict, Any
import logging

logger = logging.getLogger(__name__)


class TechnicalIndicators:
    """
    Comprehensive technical analysis indicators for cryptocurrency trading
    
    Features:
    - Trend indicators (SMA, EMA, VWAP)
    - Momentum indicators (RSI, Stochastic, Williams %R) 
    - Volatility indicators (Bollinger Bands, ATR)
    - Volume indicators (OBV, Volume SMA)
    - Oscillators (MACD, CCI)
    """
    
    @staticmethod
    def simple_moving_average(data: pd.Series, window: int) -> pd.Series:
        """Calculate Simple Moving Average"""
        return data.rolling(window=window).mean()
    
    @staticmethod
    def exponential_moving_average(data: pd.Series, window: int) -> pd.Series:
        """Calculate Exponential Moving Average"""
        return data.ewm(span=window, adjust=False).mean()
    
    @staticmethod
    def rsi(data: pd.Series, window: int = 14) -> pd.Series:
        """
        Calculate Relative Strength Index (RSI)
        
        RSI = 100 - (100 / (1 + RS))
        RS = Average Gain / Average Loss
        """
        delta = data.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    @staticmethod
    def macd(data: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Calculate Moving Average Convergence Divergence (MACD)
        
        Returns:
        - MACD line: EMA(12) - EMA(26)
        - Signal line: EMA(9) of MACD line
        - Histogram: MACD - Signal
        """
        ema_fast = TechnicalIndicators.exponential_moving_average(data, fast)
        ema_slow = TechnicalIndicators.exponential_moving_average(data, slow)
        
        macd_line = ema_fast - ema_slow
        signal_line = TechnicalIndicators.exponential_moving_average(macd_line, signal)
        histogram = macd_line - signal_line
        
        return macd_line, signal_line, histogram
    
    @staticmethod
    def bollinger_bands(data: pd.Series, window: int = 20, num_std: float = 2) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Calculate Bollinger Bands
        
        Returns:
        - Upper Band: SMA + (STD * multiplier)
        - Middle Band: SMA
        - Lower Band: SMA - (STD * multiplier)
        """
        sma = TechnicalIndicators.simple_moving_average(data, window)
        std = data.rolling(window=window).std()
        
        upper_band = sma + (std * num_std)
        lower_band = sma - (std * num_std)
        
        return upper_band, sma, lower_band
    
    @staticmethod
    def stochastic_oscillator(high: pd.Series, low: pd.Series, close: pd.Series, 
                            k_window: int = 14, d_window: int = 3) -> Tuple[pd.Series, pd.Series]:
        """
        Calculate Stochastic Oscillator
        
        %K = ((Close - Lowest Low) / (Highest High - Lowest Low)) * 100
        %D = SMA of %K
        
        Returns:
        - %K line
        - %D line (signal)
        """
        lowest_low = low.rolling(window=k_window).min()
        highest_high = high.rolling(window=k_window).max()
        
        k_percent = ((close - lowest_low) / (highest_high - lowest_low)) * 100
        d_percent = k_percent.rolling(window=d_window).mean()
        
        return k_percent, d_percent
    
    @staticmethod
    def williams_r(high: pd.Series, low: pd.Series, close: pd.Series, window: int = 14) -> pd.Series:
        """
        Calculate Williams %R
        
        %R = ((Highest High - Close) / (Highest High - Lowest Low)) * -100
        """
        highest_high = high.rolling(window=window).max()
        lowest_low = low.rolling(window=window).min()
        
        williams_r = ((highest_high - close) / (highest_high - lowest_low)) * -100
        return williams_r
    
    @staticmethod
    def average_true_range(high: pd.Series, low: pd.Series, close: pd.Series, window: int = 14) -> pd.Series:
        """
        Calculate Average True Range (ATR)
        
        True Range = max(High - Low, abs(High - Previous Close), abs(Low - Previous Close))
        ATR = SMA of True Range
        """
        high_low = high - low
        high_close_prev = (high - close.shift(1)).abs()
        low_close_prev = (low - close.shift(1)).abs()
        
        true_range = pd.concat([high_low, high_close_prev, low_close_prev], axis=1).max(axis=1)
        atr = true_range.rolling(window=window).mean()
        
        return atr
    
    @staticmethod
    def on_balance_volume(close: pd.Series, volume: pd.Series) -> pd.Series:
        """
        Calculate On-Balance Volume (OBV)
        
        If Close > Previous Close: OBV = Previous OBV + Volume
        If Close < Previous Close: OBV = Previous OBV - Volume
        If Close = Previous Close: OBV = Previous OBV
        """
        price_change = close.diff()
        obv = pd.Series(index=close.index, dtype=float)
        obv.iloc[0] = volume.iloc[0]
        
        for i in range(1, len(close)):
            if price_change.iloc[i] > 0:
                obv.iloc[i] = obv.iloc[i-1] + volume.iloc[i]
            elif price_change.iloc[i] < 0:
                obv.iloc[i] = obv.iloc[i-1] - volume.iloc[i]
            else:
                obv.iloc[i] = obv.iloc[i-1]
        
        return obv
    
    @staticmethod
    def vwap(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series) -> pd.Series:
        """
        Calculate Volume Weighted Average Price (VWAP)
        
        VWAP = Σ(Price * Volume) / Σ(Volume)
        Price = (High + Low + Close) / 3
        """
        typical_price = (high + low + close) / 3
        cumulative_volume_price = (typical_price * volume).cumsum()
        cumulative_volume = volume.cumsum()
        
        vwap = cumulative_volume_price / cumulative_volume
        return vwap
    
    @staticmethod
    def commodity_channel_index(high: pd.Series, low: pd.Series, close: pd.Series, window: int = 20) -> pd.Series:
        """
        Calculate Commodity Channel Index (CCI)
        
        CCI = (Typical Price - SMA of Typical Price) / (0.015 * Mean Deviation)
        """
        typical_price = (high + low + close) / 3
        sma_tp = typical_price.rolling(window=window).mean()
        
        # Calculate mean deviation
        mean_deviation = typical_price.rolling(window=window).apply(
            lambda x: np.mean(np.abs(x - x.mean())), raw=True
        )
        
        cci = (typical_price - sma_tp) / (0.015 * mean_deviation)
        return cci
    
    @staticmethod
    def parabolic_sar(high: pd.Series, low: pd.Series, af_start: float = 0.02, 
                     af_increment: float = 0.02, af_max: float = 0.2) -> pd.Series:
        """
        Calculate Parabolic SAR (Stop and Reverse)
        
        Complex indicator that provides potential reversal points
        """
        length = len(high)
        psar = pd.Series(index=high.index, dtype=float)
        uptrend = True
        af = af_start
        ep = high.iloc[0] if uptrend else low.iloc[0]
        
        psar.iloc[0] = low.iloc[0]
        
        for i in range(1, length):
            if uptrend:
                psar.iloc[i] = psar.iloc[i-1] + af * (ep - psar.iloc[i-1])
                
                if low.iloc[i] <= psar.iloc[i]:
                    uptrend = False
                    psar.iloc[i] = ep
                    ep = low.iloc[i]
                    af = af_start
                else:
                    if high.iloc[i] > ep:
                        ep = high.iloc[i]
                        af = min(af + af_increment, af_max)
            else:
                psar.iloc[i] = psar.iloc[i-1] + af * (ep - psar.iloc[i-1])
                
                if high.iloc[i] >= psar.iloc[i]:
                    uptrend = True
                    psar.iloc[i] = ep
                    ep = high.iloc[i]
                    af = af_start
                else:
                    if low.iloc[i] < ep:
                        ep = low.iloc[i]
                        af = min(af + af_increment, af_max)
        
        return psar
    
    @classmethod
    def calculate_all_indicators(cls, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate all technical indicators for a given DataFrame
        
        Expected columns: open_price, high_price, low_price, close_price, volume
        """
        try:
            result = df.copy()
            
            # Price data
            close = df['close_price']
            high = df['high_price']
            low = df['low_price']
            volume = df['volume']
            
            # Moving Averages
            result['sma_5'] = cls.simple_moving_average(close, 5)
            result['sma_10'] = cls.simple_moving_average(close, 10)
            result['sma_20'] = cls.simple_moving_average(close, 20)
            result['sma_50'] = cls.simple_moving_average(close, 50)
            result['sma_200'] = cls.simple_moving_average(close, 200)
            
            result['ema_5'] = cls.exponential_moving_average(close, 5)
            result['ema_10'] = cls.exponential_moving_average(close, 10)
            result['ema_20'] = cls.exponential_moving_average(close, 20)
            result['ema_50'] = cls.exponential_moving_average(close, 50)
            
            # Momentum Indicators
            result['rsi'] = cls.rsi(close, 14)
            result['rsi_30'] = cls.rsi(close, 30)
            
            # MACD
            macd_line, signal_line, histogram = cls.macd(close)
            result['macd'] = macd_line
            result['macd_signal'] = signal_line
            result['macd_histogram'] = histogram
            
            # Bollinger Bands
            bb_upper, bb_middle, bb_lower = cls.bollinger_bands(close)
            result['bb_upper'] = bb_upper
            result['bb_middle'] = bb_middle
            result['bb_lower'] = bb_lower
            result['bb_width'] = (bb_upper - bb_lower) / bb_middle
            result['bb_position'] = (close - bb_lower) / (bb_upper - bb_lower)
            
            # Stochastic
            stoch_k, stoch_d = cls.stochastic_oscillator(high, low, close)
            result['stoch_k'] = stoch_k
            result['stoch_d'] = stoch_d
            
            # Other Indicators
            result['williams_r'] = cls.williams_r(high, low, close)
            result['atr'] = cls.average_true_range(high, low, close)
            result['obv'] = cls.on_balance_volume(close, volume)
            result['vwap'] = cls.vwap(high, low, close, volume)
            result['cci'] = cls.commodity_channel_index(high, low, close)
            result['psar'] = cls.parabolic_sar(high, low)
            
            # Volume indicators
            result['volume_sma'] = cls.simple_moving_average(volume, 20)
            result['volume_ratio'] = volume / result['volume_sma']
            
            # Price momentum
            result['price_change'] = close.pct_change()
            result['price_change_5d'] = close.pct_change(5)
            result['price_volatility'] = close.rolling(20).std()
            
            logger.info(f"Calculated {len(result.columns) - len(df.columns)} technical indicators")
            return result
            
        except Exception as e:
            logger.error(f"Error calculating technical indicators: {e}")
            raise


class SignalGenerator:
    """
    Generate trading signals based on technical indicators
    """
    
    @staticmethod
    def rsi_signals(rsi: pd.Series, oversold: float = 30, overbought: float = 70) -> pd.Series:
        """Generate buy/sell signals based on RSI levels"""
        signals = pd.Series(index=rsi.index, dtype=int)
        signals[:] = 0  # 0 = hold, 1 = buy, -1 = sell
        
        signals[rsi < oversold] = 1  # Buy signal
        signals[rsi > overbought] = -1  # Sell signal
        
        return signals
    
    @staticmethod
    def ma_crossover_signals(fast_ma: pd.Series, slow_ma: pd.Series) -> pd.Series:
        """Generate signals based on moving average crossover"""
        signals = pd.Series(index=fast_ma.index, dtype=int)
        signals[:] = 0
        
        # Buy when fast MA crosses above slow MA
        signals[(fast_ma > slow_ma) & (fast_ma.shift(1) <= slow_ma.shift(1))] = 1
        # Sell when fast MA crosses below slow MA
        signals[(fast_ma < slow_ma) & (fast_ma.shift(1) >= slow_ma.shift(1))] = -1
        
        return signals
    
    @staticmethod
    def bollinger_band_signals(close: pd.Series, bb_upper: pd.Series, bb_lower: pd.Series) -> pd.Series:
        """Generate signals based on Bollinger Band bounces"""
        signals = pd.Series(index=close.index, dtype=int)
        signals[:] = 0
        
        # Buy when price touches lower band
        signals[close <= bb_lower] = 1
        # Sell when price touches upper band
        signals[close >= bb_upper] = -1
        
        return signals
    
    @staticmethod
    def macd_signals(macd: pd.Series, signal: pd.Series) -> pd.Series:
        """Generate signals based on MACD crossover"""
        signals = pd.Series(index=macd.index, dtype=int)
        signals[:] = 0
        
        # Buy when MACD crosses above signal line
        signals[(macd > signal) & (macd.shift(1) <= signal.shift(1))] = 1
        # Sell when MACD crosses below signal line
        signals[(macd < signal) & (macd.shift(1) >= signal.shift(1))] = -1
        
        return signals
    
    @staticmethod
    def combine_signals(signals_dict: Dict[str, pd.Series], weights: Optional[Dict[str, float]] = None) -> pd.Series:
        """
        Combine multiple trading signals with optional weighting
        
        Args:
            signals_dict: Dictionary of signal names and their corresponding series
            weights: Optional weights for each signal (default: equal weighting)
        
        Returns:
            Combined signal series where values represent signal strength
        """
        if weights is None:
            weights = {name: 1.0 for name in signals_dict.keys()}
        
        combined = pd.Series(index=list(signals_dict.values())[0].index, dtype=float)
        combined[:] = 0.0
        
        for name, signal in signals_dict.items():
            weight = weights.get(name, 1.0)
            combined += signal * weight
        
        # Normalize to -1, 0, 1 scale
        combined = combined / len(signals_dict)
        
        return combined


if __name__ == "__main__":
    # Example usage
    print("Technical Indicators module loaded successfully!")
    print("Available indicators:")
    indicators = [
        "Simple Moving Average (SMA)", "Exponential Moving Average (EMA)",
        "Relative Strength Index (RSI)", "MACD", "Bollinger Bands",
        "Stochastic Oscillator", "Williams %R", "Average True Range (ATR)",
        "On-Balance Volume (OBV)", "VWAP", "Commodity Channel Index (CCI)",
        "Parabolic SAR"
    ]
    for i, indicator in enumerate(indicators, 1):
        print(f"{i}. {indicator}")