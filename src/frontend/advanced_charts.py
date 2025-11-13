"""
Advanced TradingView-Style Charting Engine
Professional technical analysis charts with multiple indicators
"""
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
from typing import Optional, List, Dict, Any


class TechnicalIndicators:
    """Calculate various technical indicators"""
    
    @staticmethod
    def calculate_sma(data: pd.Series, period: int) -> pd.Series:
        """Calculate Simple Moving Average"""
        return data.rolling(window=period).mean()
    
    @staticmethod
    def calculate_ema(data: pd.Series, period: int) -> pd.Series:
        """Calculate Exponential Moving Average"""
        return data.ewm(span=period, adjust=False).mean()
    
    @staticmethod
    def calculate_rsi(data: pd.Series, period: int = 14) -> pd.Series:
        """Calculate Relative Strength Index"""
        delta = data.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    @staticmethod
    def calculate_macd(data: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> tuple:
        """Calculate MACD, Signal, and Histogram"""
        ema_fast = data.ewm(span=fast, adjust=False).mean()
        ema_slow = data.ewm(span=slow, adjust=False).mean()
        
        macd = ema_fast - ema_slow
        signal_line = macd.ewm(span=signal, adjust=False).mean()
        histogram = macd - signal_line
        
        return macd, signal_line, histogram
    
    @staticmethod
    def calculate_bollinger_bands(data: pd.Series, period: int = 20, std_dev: int = 2) -> tuple:
        """Calculate Bollinger Bands"""
        sma = data.rolling(window=period).mean()
        std = data.rolling(window=period).std()
        
        upper_band = sma + (std * std_dev)
        lower_band = sma - (std * std_dev)
        
        return upper_band, sma, lower_band
    
    @staticmethod
    def calculate_stochastic(high: pd.Series, low: pd.Series, close: pd.Series, 
                            period: int = 14, smooth_k: int = 3, smooth_d: int = 3) -> tuple:
        """Calculate Stochastic Oscillator"""
        lowest_low = low.rolling(window=period).min()
        highest_high = high.rolling(window=period).max()
        
        k = 100 * ((close - lowest_low) / (highest_high - lowest_low))
        k = k.rolling(window=smooth_k).mean()
        d = k.rolling(window=smooth_d).mean()
        
        return k, d
    
    @staticmethod
    def calculate_vwap(df: pd.DataFrame) -> pd.Series:
        """Calculate Volume Weighted Average Price"""
        typical_price = (df['high'] + df['low'] + df['close']) / 3
        vwap = (typical_price * df['volume']).cumsum() / df['volume'].cumsum()
        return vwap


class AdvancedChart:
    """Create professional TradingView-style charts"""
    
    def __init__(self):
        self.indicators = TechnicalIndicators()
        self.colors = {
            'bullish': '#26a69a',
            'bearish': '#ef5350',
            'neutral': '#ffa726',
            'sma': ['#2196F3', '#4CAF50', '#FF9800', '#E91E63', '#9C27B0'],
            'ema': ['#00BCD4', '#8BC34A', '#FFC107', '#F06292', '#BA68C8'],
            'bb': 'rgba(33, 150, 243, 0.3)',
            'vwap': '#FF5722'
        }
    
    def create_main_chart(self, df: pd.DataFrame, 
                         show_sma: bool = False,
                         show_ema: bool = False,
                         show_bb: bool = False,
                         show_vwap: bool = False,
                         sma_periods: List[int] = [20, 50, 200],
                         ema_periods: List[int] = [12, 26],
                         trades: List[Dict] = None,
                         title: str = "Price Chart") -> go.Figure:
        """Create main candlestick chart with overlays"""
        
        # Create figure with secondary y-axis for volume
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.03,
            row_heights=[0.7, 0.3],
            subplot_titles=(title, 'Volume')
        )
        
        # Candlestick chart
        fig.add_trace(
            go.Candlestick(
                x=df['timestamp'],
                open=df['open'],
                high=df['high'],
                low=df['low'],
                close=df['close'],
                increasing_line_color=self.colors['bullish'],
                decreasing_line_color=self.colors['bearish'],
                name='Price'
            ),
            row=1, col=1
        )
        
        # Volume bars
        colors = [self.colors['bullish'] if close >= open else self.colors['bearish'] 
                 for close, open in zip(df['close'], df['open'])]
        
        fig.add_trace(
            go.Bar(
                x=df['timestamp'],
                y=df['volume'],
                marker_color=colors,
                name='Volume',
                opacity=0.5
            ),
            row=2, col=1
        )
        
        # Add SMAs
        if show_sma:
            for i, period in enumerate(sma_periods):
                if len(df) >= period:
                    sma = self.indicators.calculate_sma(df['close'], period)
                    fig.add_trace(
                        go.Scatter(
                            x=df['timestamp'],
                            y=sma,
                            mode='lines',
                            name=f'SMA {period}',
                            line=dict(color=self.colors['sma'][i % len(self.colors['sma'])], width=2)
                        ),
                        row=1, col=1
                    )
        
        # Add EMAs
        if show_ema:
            for i, period in enumerate(ema_periods):
                if len(df) >= period:
                    ema = self.indicators.calculate_ema(df['close'], period)
                    fig.add_trace(
                        go.Scatter(
                            x=df['timestamp'],
                            y=ema,
                            mode='lines',
                            name=f'EMA {period}',
                            line=dict(color=self.colors['ema'][i % len(self.colors['ema'])], width=2, dash='dash')
                        ),
                        row=1, col=1
                    )
        
        # Add Bollinger Bands
        if show_bb and len(df) >= 20:
            upper, middle, lower = self.indicators.calculate_bollinger_bands(df['close'])
            
            fig.add_trace(
                go.Scatter(
                    x=df['timestamp'],
                    y=upper,
                    mode='lines',
                    name='BB Upper',
                    line=dict(color=self.colors['bb'], width=1),
                    showlegend=False
                ),
                row=1, col=1
            )
            
            fig.add_trace(
                go.Scatter(
                    x=df['timestamp'],
                    y=lower,
                    mode='lines',
                    name='BB Lower',
                    line=dict(color=self.colors['bb'], width=1),
                    fill='tonexty',
                    fillcolor=self.colors['bb'],
                    showlegend=True
                ),
                row=1, col=1
            )
        
        # Add VWAP
        if show_vwap:
            vwap = self.indicators.calculate_vwap(df)
            fig.add_trace(
                go.Scatter(
                    x=df['timestamp'],
                    y=vwap,
                    mode='lines',
                    name='VWAP',
                    line=dict(color=self.colors['vwap'], width=2, dash='dot')
                ),
                row=1, col=1
            )
        
        # Add trade markers
        if trades:
            # Entry points
            entry_times = [t['entry_time'] for t in trades if 'entry_time' in t]
            entry_prices = [t['entry_price'] for t in trades if 'entry_price' in t]
            
            if entry_times:
                fig.add_trace(
                    go.Scatter(
                        x=entry_times,
                        y=entry_prices,
                        mode='markers',
                        name='Entry',
                        marker=dict(
                            symbol='triangle-up',
                            size=12,
                            color=self.colors['bullish'],
                            line=dict(color='white', width=1)
                        )
                    ),
                    row=1, col=1
                )
            
            # Exit points
            for trade in trades:
                if trade.get('exit_price'):
                    exit_color = self.colors['bullish'] if trade.get('profit', 0) > 0 else self.colors['bearish']
                    fig.add_trace(
                        go.Scatter(
                            x=[trade['exit_time']],
                            y=[trade['exit_price']],
                            mode='markers',
                            name='Exit',
                            marker=dict(
                                symbol='triangle-down',
                                size=12,
                                color=exit_color,
                                line=dict(color='white', width=1)
                            ),
                            showlegend=False
                        ),
                        row=1, col=1
                    )
        
        # Update layout
        fig.update_layout(
            template='plotly_dark',
            height=600,
            margin=dict(l=0, r=0, t=40, b=0),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white'),
            hovermode='x unified',
            xaxis_rangeslider_visible=False,
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
                bgcolor='rgba(0,0,0,0.5)'
            )
        )
        
        fig.update_xaxes(gridcolor='rgba(255,255,255,0.1)', showgrid=True)
        fig.update_yaxes(gridcolor='rgba(255,255,255,0.1)', showgrid=True)
        
        return fig
    
    def create_rsi_chart(self, df: pd.DataFrame, period: int = 14) -> Optional[go.Figure]:
        """Create RSI indicator chart"""
        if len(df) < period + 1:
            return None
        
        rsi = self.indicators.calculate_rsi(df['close'], period)
        
        fig = go.Figure()
        
        # RSI line
        fig.add_trace(
            go.Scatter(
                x=df['timestamp'],
                y=rsi,
                mode='lines',
                name=f'RSI ({period})',
                line=dict(color='#2196F3', width=2)
            )
        )
        
        # Overbought/Oversold zones
        fig.add_hline(y=70, line_dash="dash", line_color="red", opacity=0.5, annotation_text="Overbought")
        fig.add_hline(y=30, line_dash="dash", line_color="green", opacity=0.5, annotation_text="Oversold")
        fig.add_hline(y=50, line_dash="dot", line_color="gray", opacity=0.3)
        
        # Shade overbought/oversold regions
        fig.add_hrect(y0=70, y1=100, fillcolor="red", opacity=0.1, line_width=0)
        fig.add_hrect(y0=0, y1=30, fillcolor="green", opacity=0.1, line_width=0)
        
        fig.update_layout(
            template='plotly_dark',
            height=250,
            margin=dict(l=0, r=0, t=40, b=0),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white'),
            yaxis=dict(range=[0, 100], gridcolor='rgba(255,255,255,0.1)'),
            xaxis=dict(gridcolor='rgba(255,255,255,0.1)'),
            showlegend=False
        )
        
        return fig
    
    def create_macd_chart(self, df: pd.DataFrame) -> Optional[go.Figure]:
        """Create MACD indicator chart"""
        if len(df) < 26:
            return None
        
        macd, signal, histogram = self.indicators.calculate_macd(df['close'])
        
        fig = go.Figure()
        
        # Histogram
        colors = [self.colors['bullish'] if val >= 0 else self.colors['bearish'] for val in histogram]
        fig.add_trace(
            go.Bar(
                x=df['timestamp'],
                y=histogram,
                marker_color=colors,
                name='Histogram',
                opacity=0.6
            )
        )
        
        # MACD line
        fig.add_trace(
            go.Scatter(
                x=df['timestamp'],
                y=macd,
                mode='lines',
                name='MACD',
                line=dict(color='#2196F3', width=2)
            )
        )
        
        # Signal line
        fig.add_trace(
            go.Scatter(
                x=df['timestamp'],
                y=signal,
                mode='lines',
                name='Signal',
                line=dict(color='#FF9800', width=2)
            )
        )
        
        fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.3)
        
        fig.update_layout(
            template='plotly_dark',
            height=250,
            margin=dict(l=0, r=0, t=40, b=0),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white'),
            yaxis=dict(gridcolor='rgba(255,255,255,0.1)'),
            xaxis=dict(gridcolor='rgba(255,255,255,0.1)'),
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
                bgcolor='rgba(0,0,0,0.5)'
            )
        )
        
        return fig
    
    def create_stochastic_chart(self, df: pd.DataFrame, period: int = 14) -> Optional[go.Figure]:
        """Create Stochastic Oscillator chart"""
        if len(df) < period + 3:
            return None
        
        k, d = self.indicators.calculate_stochastic(df['high'], df['low'], df['close'], period)
        
        fig = go.Figure()
        
        # %K line
        fig.add_trace(
            go.Scatter(
                x=df['timestamp'],
                y=k,
                mode='lines',
                name='%K',
                line=dict(color='#2196F3', width=2)
            )
        )
        
        # %D line
        fig.add_trace(
            go.Scatter(
                x=df['timestamp'],
                y=d,
                mode='lines',
                name='%D',
                line=dict(color='#FF9800', width=2)
            )
        )
        
        # Overbought/Oversold zones
        fig.add_hline(y=80, line_dash="dash", line_color="red", opacity=0.5)
        fig.add_hline(y=20, line_dash="dash", line_color="green", opacity=0.5)
        
        fig.add_hrect(y0=80, y1=100, fillcolor="red", opacity=0.1, line_width=0)
        fig.add_hrect(y0=0, y1=20, fillcolor="green", opacity=0.1, line_width=0)
        
        fig.update_layout(
            template='plotly_dark',
            height=250,
            margin=dict(l=0, r=0, t=40, b=0),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white'),
            yaxis=dict(range=[0, 100], gridcolor='rgba(255,255,255,0.1)'),
            xaxis=dict(gridcolor='rgba(255,255,255,0.1)'),
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
                bgcolor='rgba(0,0,0,0.5)'
            )
        )
        
        return fig
    
    def create_volume_profile(self, df: pd.DataFrame, num_bins: int = 20) -> Optional[go.Figure]:
        """Create Volume Profile chart"""
        if len(df) < 10:
            return None
        
        # Calculate price bins
        price_range = df['high'].max() - df['low'].min()
        bin_size = price_range / num_bins
        
        # Create bins
        bins = {}
        for _, row in df.iterrows():
            bin_idx = int((row['close'] - df['low'].min()) / bin_size)
            bin_idx = min(bin_idx, num_bins - 1)  # Cap at max bin
            bins[bin_idx] = bins.get(bin_idx, 0) + row['volume']
        
        # Prepare data
        prices = [df['low'].min() + (i + 0.5) * bin_size for i in range(num_bins)]
        volumes = [bins.get(i, 0) for i in range(num_bins)]
        
        fig = go.Figure()
        
        fig.add_trace(
            go.Bar(
                x=volumes,
                y=prices,
                orientation='h',
                marker=dict(
                    color=volumes,
                    colorscale='Viridis',
                    showscale=False
                ),
                name='Volume Profile'
            )
        )
        
        # Add current price line
        current_price = df['close'].iloc[-1]
        fig.add_hline(y=current_price, line_dash="dash", line_color="yellow", 
                     annotation_text=f"Current: ${current_price:,.2f}")
        
        fig.update_layout(
            template='plotly_dark',
            height=250,
            margin=dict(l=0, r=0, t=40, b=0),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white'),
            xaxis=dict(title='Volume', gridcolor='rgba(255,255,255,0.1)'),
            yaxis=dict(title='Price', gridcolor='rgba(255,255,255,0.1)'),
            showlegend=False
        )
        
        return fig


def fetch_chart_data(symbol: str, limit: int = 200) -> pd.DataFrame:
    """Fetch chart data from API"""
    try:
        # Get API URL from Streamlit secrets, session state, or default to localhost
        import streamlit as st
        api_url = None
        try:
            api_url = st.secrets["api_url"]
        except:
            api_url = st.session_state.get('api_url', 'http://localhost:9000')
        
        response = requests.get(f'{api_url}/api/candles/{symbol}?limit={limit}', timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get('candles'):
                df = pd.DataFrame(data['candles'])
                # Ensure timestamp is datetime with flexible ISO8601 parsing
                if 'timestamp' in df.columns:
                    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                return df
    except Exception as e:
        print(f"Error fetching chart data: {e}")
    
    return pd.DataFrame()


def fetch_trades(symbol: str = None) -> List[Dict]:
    """Fetch trades from API"""
    try:
        # Get API URL from Streamlit secrets, session state, or default to localhost
        import streamlit as st
        api_url = None
        try:
            api_url = st.secrets["api_url"]
        except:
            api_url = st.session_state.get('api_url', 'http://localhost:9000')
        
        response = requests.get(f'{api_url}/api/trades?limit=50', timeout=3)
        if response.status_code == 200:
            all_trades = response.json()
            if symbol:
                return [t for t in all_trades if t.get('symbol') == symbol]
            return all_trades
    except Exception as e:
        print(f"Error fetching trades: {e}")
    
    return []
