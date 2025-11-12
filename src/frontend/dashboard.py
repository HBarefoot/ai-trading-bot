"""
Streamlit dashboard for AI Trading Bot - Phase 4 Enhanced
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import requests
import numpy as np
from datetime import datetime, timedelta
import time
import sys
import os
from typing import Optional, Dict, Any
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Trading strategy imports
try:
    from data.database import get_db
    from data.models import MarketData
    from strategies.technical_indicators import TechnicalIndicators
    from strategies.phase2_final_test import OptimizedPhase2Strategy
except ImportError as e:
    st.error(f"Import error: {e}. Some features may not work.")

# Page config
st.set_page_config(
    page_title="AI Trading Bot Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Add enhanced custom CSS
st.markdown("""
<style>
    /* Metric cards */
    .metric-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.2rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    /* Profit/Loss colors */
    .profit {
        color: #10b981;
        font-weight: bold;
    }
    .loss {
        color: #ef4444;
        font-weight: bold;
    }
    
    /* Header styling */
    .main-header {
        text-align: center;
        color: #1f77b4;
        margin-bottom: 2rem;
        font-size: 2.5rem;
        font-weight: bold;
    }
    
    /* Status badges */
    .status-active {
        background: #10b981;
        color: white;
        padding: 4px 12px;
        border-radius: 12px;
        font-weight: 600;
    }
    
    .status-inactive {
        background: #f59e0b;
        color: white;
        padding: 4px 12px;
        border-radius: 12px;
        font-weight: 600;
    }
    
    /* Button enhancements */
    .stButton>button {
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    
    /* Table styling */
    .dataframe {
        font-size: 0.9rem;
    }
    
    /* Sidebar enhancements */
    .css-1d391kg {
        padding-top: 2rem;
    }
    
    /* Metric value styling */
    [data-testid="stMetricValue"] {
        font-size: 1.8rem;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)


class APIClient:
    """Enhanced API client with error handling, caching, and retry logic"""
    
    def __init__(self, base_url: str = "http://localhost:9000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({'Content-Type': 'application/json'})
        
        # Initialize cache in session state
        if 'api_cache' not in st.session_state:
            st.session_state.api_cache = {}
        if 'api_cache_times' not in st.session_state:
            st.session_state.api_cache_times = {}
    
    def _get_cache_key(self, endpoint: str, params: Optional[Dict] = None) -> str:
        """Generate cache key from endpoint and params"""
        if params:
            param_str = "&".join([f"{k}={v}" for k, v in sorted(params.items())])
            return f"{endpoint}?{param_str}"
        return endpoint
    
    def _is_cache_valid(self, cache_key: str, ttl: int = 5) -> bool:
        """Check if cached data is still valid"""
        if cache_key not in st.session_state.api_cache_times:
            return False
        
        cache_time = st.session_state.api_cache_times[cache_key]
        return (time.time() - cache_time) < ttl
    
    def get(self, endpoint: str, params: Optional[Dict] = None, 
            use_cache: bool = False, cache_ttl: int = 5, timeout: int = 5) -> Optional[Dict]:
        """
        GET request with error handling and optional caching
        
        Args:
            endpoint: API endpoint (e.g., '/api/status')
            params: Query parameters
            use_cache: Whether to use/store cache
            cache_ttl: Cache time-to-live in seconds
            timeout: Request timeout in seconds
            
        Returns:
            dict or None: Response data or None on error
        """
        cache_key = self._get_cache_key(endpoint, params)
        
        # Check cache first
        if use_cache and self._is_cache_valid(cache_key, cache_ttl):
            logger.info(f"Cache hit for {cache_key}")
            return st.session_state.api_cache.get(cache_key)
        
        # Make API request
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = self.session.get(url, params=params, timeout=timeout)
            response.raise_for_status()
            
            data = response.json()
            
            # Store in cache if requested
            if use_cache:
                st.session_state.api_cache[cache_key] = data
                st.session_state.api_cache_times[cache_key] = time.time()
                logger.info(f"Cached {cache_key}")
            
            return data
            
        except requests.exceptions.Timeout:
            logger.error(f"Request timeout for {endpoint}")
            st.error(f"⏱️ Request timeout: {endpoint}")
            return self._get_cached_fallback(cache_key)
            
        except requests.exceptions.ConnectionError:
            logger.error(f"Connection error for {endpoint}")
            return self._get_cached_fallback(cache_key)
            
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error for {endpoint}: {e}")
            if e.response.status_code == 404:
                st.warning(f"⚠️ Endpoint not found: {endpoint}")
            else:
                st.error(f"❌ API Error {e.response.status_code}: {endpoint}")
            return None
            
        except Exception as e:
            logger.error(f"Unexpected error for {endpoint}: {e}")
            st.error(f"❌ Error: {str(e)}")
            return None
    
    def _get_cached_fallback(self, cache_key: str) -> Optional[Dict]:
        """Return cached data as fallback if available"""
        if cache_key in st.session_state.api_cache:
            st.info("📦 Using cached data (API unavailable)")
            return st.session_state.api_cache[cache_key]
        return None
    
    def post(self, endpoint: str, data: Optional[Dict] = None, timeout: int = 5) -> Optional[Dict]:
        """
        POST request with error handling
        
        Args:
            endpoint: API endpoint
            data: JSON data to send
            timeout: Request timeout in seconds
            
        Returns:
            dict or None: Response data or None on error
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = self.session.post(url, json=data, timeout=timeout)
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.Timeout:
            logger.error(f"POST timeout for {endpoint}")
            st.error(f"⏱️ Request timeout: {endpoint}")
            return None
            
        except requests.exceptions.ConnectionError:
            logger.error(f"POST connection error for {endpoint}")
            st.error("⚠️ Cannot connect to API. Please ensure backend is running.")
            return None
            
        except requests.exceptions.HTTPError as e:
            logger.error(f"POST HTTP error for {endpoint}: {e}")
            # Try to get error message from response
            error_msg = "Unknown error"
            try:
                error_detail = e.response.json().get('detail', str(e))
                error_msg = error_detail
            except:
                error_msg = str(e)
            
            st.error(f"❌ API Error: {error_msg}")
            return None
            
        except Exception as e:
            logger.error(f"POST unexpected error for {endpoint}: {e}")
            st.error(f"❌ Error: {str(e)}")
            return None
    
    def is_api_available(self) -> bool:
        """Check if API is reachable"""
        try:
            response = self.session.get(f"{self.base_url}/api/health", timeout=2)
            return response.status_code == 200
        except:
            return False


class TradingDashboard:
    """Main dashboard class with enhanced API integration"""
    
    def __init__(self):
        self.api = APIClient()
        self.api_url = "http://localhost:9000"
        
        # Initialize session state
        if 'last_refresh' not in st.session_state:
            st.session_state.last_refresh = time.time()
        if 'auto_refresh_enabled' not in st.session_state:
            st.session_state.auto_refresh_enabled = False
        if 'last_signals' not in st.session_state:
            st.session_state.last_signals = {}
        if 'last_portfolio_value' not in st.session_state:
            st.session_state.last_portfolio_value = 0
        if 'alerts_enabled' not in st.session_state:
            st.session_state.alerts_enabled = True
    
    def check_and_alert(self):
        """Check conditions and send alerts"""
        if not st.session_state.alerts_enabled:
            logger.debug("Alerts disabled, skipping checks")
            return
        
        logger.info("Checking for alert conditions...")
        try:
            # Check signal changes
            signals = self.fetch_signals()
            if signals:
                logger.info(f"Checking {len(signals)} signals for changes")
                for symbol, signal_data in signals.items():
                    if symbol in st.session_state.last_signals:
                        old_signal = st.session_state.last_signals[symbol].get('signal_type', 'HOLD')
                        new_signal = signal_data.get('signal_type', 'HOLD')
                        
                        if old_signal != new_signal and new_signal != 'HOLD':
                            # Signal changed!
                            emoji = "🟢" if new_signal == 'BUY' else "🔴"
                            st.toast(f"{emoji} Signal Alert: {symbol} → {new_signal}!", icon="🚨")
                            logger.info(f"🚨 ALERT TRIGGERED: {symbol} {old_signal} → {new_signal}")
                    
                    st.session_state.last_signals[symbol] = signal_data
            
            # Check for large P&L changes
            portfolio = self.fetch_portfolio()
            if portfolio:
                current_value = portfolio.get('total_value', 0)
                last_value = st.session_state.last_portfolio_value
                
                if last_value > 0:
                    change_pct = ((current_value - last_value) / last_value) * 100
                    
                    if abs(change_pct) > 5:  # More than 5% change
                        if change_pct > 0:
                            st.toast(f"📈 Big gain! Portfolio up {change_pct:.2f}%", icon="🎉")
                            logger.info(f"🚨 ALERT TRIGGERED: Portfolio up {change_pct:.2f}%")
                        else:
                            st.toast(f"📉 Alert: Portfolio down {change_pct:.2f}%", icon="⚠️")
                            logger.info(f"🚨 ALERT TRIGGERED: Portfolio down {change_pct:.2f}%")
                
                st.session_state.last_portfolio_value = current_value
                
        except Exception as e:
            logger.error(f"Alert check error: {e}")
    
    # Data fetching helper methods
    def fetch_system_status(self) -> Optional[Dict]:
        """Fetch system status from API"""
        return self.api.get('/api/status', use_cache=True, cache_ttl=5)
    
    def fetch_live_prices(self) -> Optional[Dict]:
        """Fetch all live cryptocurrency prices"""
        return self.api.get('/api/live-data', use_cache=True, cache_ttl=5)
    
    def fetch_portfolio(self) -> Optional[Dict]:
        """Fetch current portfolio status"""
        return self.api.get('/api/portfolio', use_cache=True, cache_ttl=5)
    
    def fetch_portfolio_value_history(self) -> Optional[Dict]:
        """Fetch portfolio value over time"""
        return self.api.get('/api/portfolio/value', use_cache=True, cache_ttl=10)
    
    def fetch_trades(self, limit: int = 50) -> Optional[list]:
        """Fetch recent trade history"""
        data = self.api.get('/api/trades', params={'limit': limit}, use_cache=True, cache_ttl=10)
        return data if data else []
    
    def fetch_performance(self) -> Optional[Dict]:
        """Fetch performance metrics"""
        return self.api.get('/api/performance', use_cache=True, cache_ttl=10)
    
    def fetch_signals(self, symbol: Optional[str] = None) -> Optional[Dict]:
        """Fetch trading signals"""
        if symbol:
            # Fetch signal for specific symbol
            endpoint = f'/api/signals/{symbol}'
            return self.api.get(endpoint, use_cache=True, cache_ttl=5)
        else:
            # Fetch signals for multiple symbols
            symbols = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'ADAUSDT']
            signals = {}
            for sym in symbols:
                signal = self.api.get(f'/api/signals/{sym}', use_cache=True, cache_ttl=5)
                if signal:
                    signals[sym] = signal
            return signals if signals else None
    
    def fetch_market_data(self, symbol: str, limit: int = 500) -> Optional[list]:
        """Fetch historical market data"""
        data = self.api.get(f'/api/market-data/{symbol}', params={'limit': limit}, use_cache=True, cache_ttl=30)
        return data if data else []
    
    def fetch_strategies(self) -> Optional[Dict]:
        """Fetch available strategies"""
        return self.api.get('/api/strategies', use_cache=True, cache_ttl=30)
    
    # Legacy method for backwards compatibility
    def get_data(self, endpoint: str):
        """Fetch data from API (legacy method)"""
        return self.api.get(f'/api/{endpoint}')
    
    def check_api_connection(self) -> bool:
        """Check if API is available and show status"""
        if not self.api.is_api_available():
            st.error("""
                ⚠️ **API Backend Not Available**
                
                The dashboard cannot connect to the API backend at `http://localhost:9000`.
                
                **To start the API:**
                ```bash
                ./start_api.sh
                ```
                
                Or manually:
                ```bash
                cd /Users/henrybarefoot/ai-learning/ai-trading-bot
                python -m uvicorn src.api.api_backend:app --reload --port 9000
                ```
            """)
            return False
        return True
    
    def plot_price_chart(self, symbol: str = "BTCUSDT"):
        """Enhanced price chart with technical indicators"""
        st.subheader(f"📈 {symbol} Price Chart")
        
        # Chart controls
        col1, col2, col3 = st.columns(3)
        with col1:
            chart_type = st.selectbox("Chart Type", ["Candlestick", "Line"], key="chart_type")
        with col2:
            show_ma = st.checkbox("Show Moving Averages", value=True, key="show_ma")
        with col3:
            show_signals = st.checkbox("Show Signals", value=True, key="show_signals")
        
        # Fetch market data
        market_data = self.fetch_market_data(symbol, limit=500)
        
        if not market_data or len(market_data) == 0:
            st.warning(f"📭 No market data available for {symbol}")
            st.info("Market data will populate as the system collects price information.")
            return
        
        df = pd.DataFrame(market_data)
        df['timestamp'] = pd.to_datetime(df['timestamp'], format='ISO8601')
        df = df.sort_values('timestamp')
        
        # Get current price and stats
        current_price = df['close'].iloc[-1]
        price_change = df['close'].iloc[-1] - df['close'].iloc[0]
        price_change_pct = (price_change / df['close'].iloc[0]) * 100
        
        # Display current stats
        stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)
        with stat_col1:
            st.metric("Current Price", f"${current_price:,.2f}")
        with stat_col2:
            st.metric("Change", f"${price_change:,.2f}", f"{price_change_pct:+.2f}%")
        with stat_col3:
            st.metric("High", f"${df['high'].max():,.2f}")
        with stat_col4:
            st.metric("Low", f"${df['low'].min():,.2f}")
        
        # Create chart based on type
        if chart_type == "Candlestick":
            # Create candlestick chart with subplots
            fig = make_subplots(
                rows=2, cols=1,
                row_heights=[0.7, 0.3],
                subplot_titles=[f'{symbol} Price', 'Volume'],
                shared_xaxes=True,
                vertical_spacing=0.05
            )
            
            # Candlestick
            fig.add_trace(
                go.Candlestick(
                    x=df['timestamp'],
                    open=df['open'],
                    high=df['high'],
                    low=df['low'],
                    close=df['close'],
                    name='Price',
                    increasing_line_color='#26a69a',
                    decreasing_line_color='#ef5350'
                ),
                row=1, col=1
            )
        else:
            # Line chart
            fig = make_subplots(
                rows=2, cols=1,
                row_heights=[0.7, 0.3],
                subplot_titles=[f'{symbol} Price', 'Volume'],
                shared_xaxes=True,
                vertical_spacing=0.05
            )
            
            fig.add_trace(
                go.Scatter(
                    x=df['timestamp'],
                    y=df['close'],
                    name='Price',
                    line=dict(color='#1f77b4', width=2),
                    fill='tozeroy',
                    fillcolor='rgba(31, 119, 180, 0.1)'
                ),
                row=1, col=1
            )
        
        # Add moving averages if enabled
        if show_ma:
            df['ma_8'] = df['close'].rolling(8).mean()
            df['ma_21'] = df['close'].rolling(21).mean()
            df['ma_50'] = df['close'].rolling(50).mean()
            
            fig.add_trace(
                go.Scatter(
                    x=df['timestamp'],
                    y=df['ma_8'],
                    name='MA(8)',
                    line=dict(color='orange', width=1.5)
                ),
                row=1, col=1
            )
            
            fig.add_trace(
                go.Scatter(
                    x=df['timestamp'],
                    y=df['ma_21'],
                    name='MA(21)',
                    line=dict(color='purple', width=1.5)
                ),
                row=1, col=1
            )
            
            fig.add_trace(
                go.Scatter(
                    x=df['timestamp'],
                    y=df['ma_50'],
                    name='MA(50)',
                    line=dict(color='red', width=1.5, dash='dash')
                ),
                row=1, col=1
            )
        
        # Add trading signals if enabled
        if show_signals:
            signals = self.fetch_signals(symbol)
            if signals:
                # Add buy/sell markers (simplified - in real scenario, match with timestamps)
                # This is a placeholder - you'd need signal history with timestamps
                pass
        
        # Volume chart
        colors = ['#ef5350' if close < open else '#26a69a' 
                 for close, open in zip(df['close'], df['open'])]
        
        fig.add_trace(
            go.Bar(
                x=df['timestamp'],
                y=df['volume'],
                name='Volume',
                marker_color=colors,
                showlegend=False
            ),
            row=2, col=1
        )
        
        # Update layout
        fig.update_layout(
            title=f"{symbol} Technical Analysis",
            xaxis_rangeslider_visible=False,
            height=700,
            hovermode='x unified',
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        fig.update_xaxes(title_text="Date", row=2, col=1)
        fig.update_yaxes(title_text="Price ($)", row=1, col=1)
        fig.update_yaxes(title_text="Volume", row=2, col=1)
        
        st.plotly_chart(fig, width="stretch")
        
        # Technical indicators panel
        with st.expander("📊 Technical Indicators"):
            if len(df) > 0:
                ind_col1, ind_col2, ind_col3 = st.columns(3)
                
                with ind_col1:
                    st.markdown("**Moving Averages**")
                    if 'ma_8' in df:
                        st.write(f"MA(8): ${df['ma_8'].iloc[-1]:.2f}")
                    if 'ma_21' in df:
                        st.write(f"MA(21): ${df['ma_21'].iloc[-1]:.2f}")
                    if 'ma_50' in df:
                        st.write(f"MA(50): ${df['ma_50'].iloc[-1]:.2f}")
                
                with ind_col2:
                    st.markdown("**Price Stats**")
                    st.write(f"24h Range: ${df['low'].tail(24).min():.2f} - ${df['high'].tail(24).max():.2f}")
                    st.write(f"24h Volume: {df['volume'].tail(24).sum():,.0f}")
                
                with ind_col3:
                    st.markdown("**Trend**")
                    if 'ma_8' in df and 'ma_21' in df:
                        if df['ma_8'].iloc[-1] > df['ma_21'].iloc[-1]:
                            st.success("🟢 Bullish (MA8 > MA21)")
                        else:
                            st.error("🔴 Bearish (MA8 < MA21)")
    
    def show_portfolio_overview(self):
        """Display portfolio overview"""
        portfolio_data = self.get_data("portfolio")
        portfolio_value = self.get_data("portfolio/value")
        
        if portfolio_data is None:
            st.warning("Portfolio data not available")
            return
        
        st.subheader("📊 Portfolio Overview")
        
        col1, col2, col3, col4 = st.columns(4)
        
        # Extract data from API response
        total_value = portfolio_data.get('total_value', 0)
        positions = portfolio_data.get('positions', [])
        
        with col1:
            st.metric("Total Value", f"${total_value:,.2f}")
        
        with col2:
            num_positions = len(positions)
            st.metric("Active Positions", num_positions)
        
        with col3:
            # Calculate total P&L from positions
            total_pnl = sum(pos.get('pnl', 0) for pos in positions)
            st.metric("Total P&L", f"${total_pnl:,.2f}", 
                     delta=f"{total_pnl/total_value*100:.2f}%" if total_value > 0 else "0%")
        
        with col4:
            # Get REAL win rate from performance API
            performance_data = self.get_data("performance")
            if performance_data:
                win_rate = performance_data.get('win_rate', 0)
                total_trades = performance_data.get('total_trades', 0)
                if total_trades > 0:
                    st.metric("Win Rate", f"{win_rate:.1f}%")
                else:
                    st.metric("Win Rate", "N/A", help="No trades yet")
            else:
                st.metric("Win Rate", "N/A", help="Performance data unavailable")
        
        # Portfolio allocation chart
        if positions:
            df_portfolio = pd.DataFrame(positions)
            
            # Use the 'value' field from API response
            df_portfolio['position_value'] = df_portfolio['value']
            
            if not df_portfolio.empty:
                fig = px.pie(
                    df_portfolio,
                    values='position_value',
                    names='symbol',
                    title="Portfolio Allocation"
                )
                st.plotly_chart(fig, width='stretch')
    
    def show_trading_history(self):
        """Display recent trades with live data"""
        st.subheader("📝 Trade History")
        
        # Filters
        col1, col2, col3 = st.columns(3)
        with col1:
            limit = st.selectbox("Show last", [10, 20, 50, 100], index=1)
        with col2:
            symbol_filter = st.selectbox("Symbol", ["All", "BTCUSDT", "ETHUSDT", "SOLUSDT", "ADAUSDT"])
        with col3:
            if st.button("🔄 Refresh Trades"):
                st.rerun()
        
        # Fetch trades from API
        trades = self.fetch_trades(limit=limit)
        
        if not trades or len(trades) == 0:
            st.info("📭 No trading history available yet. Start trading to see trades here!")
            
            # Show example of what will appear
            st.markdown("**Trades will show:**")
            st.markdown("- Timestamp and symbol")
            st.markdown("- Buy/Sell type with quantity")
            st.markdown("- Entry and exit prices")
            st.markdown("- Profit/Loss in $ and %")
            st.markdown("- Strategy used")
            return
        
        # Create DataFrame
        df_trades = pd.DataFrame(trades)
        
        # Filter by symbol if selected
        if symbol_filter != "All":
            df_trades = df_trades[df_trades['symbol'] == symbol_filter]
        
        if len(df_trades) == 0:
            st.info(f"No trades found for {symbol_filter}")
            return
        
        # Format timestamp
        df_trades['timestamp'] = pd.to_datetime(df_trades['timestamp'], format='ISO8601')
        
        # Calculate totals
        total_pnl = df_trades['profit_loss'].sum() if 'profit_loss' in df_trades else 0
        buy_count = len(df_trades[df_trades['side'] == 'buy'])
        sell_count = len(df_trades[df_trades['side'] == 'sell'])
        
        # Summary metrics
        metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
        with metric_col1:
            st.metric("Total Trades", len(df_trades))
        with metric_col2:
            st.metric("Total P&L", f"${total_pnl:,.2f}", 
                     delta_color="normal" if total_pnl >= 0 else "inverse")
        with metric_col3:
            st.metric("Buy Orders", buy_count)
        with metric_col4:
            st.metric("Sell Orders", sell_count)
        
        st.divider()
        
        # Format for display
        display_df = df_trades.copy()
        
        # Format columns
        display_df['Time'] = display_df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
        display_df['Symbol'] = display_df['symbol']
        
        # Side with emoji
        if 'side' in display_df:
            display_df['Type'] = display_df['side'].apply(
                lambda x: f"🟢 BUY" if str(x).lower() == 'buy' else f"🔴 SELL"
            )
        
        # Format numbers
        if 'quantity' in display_df:
            display_df['Quantity'] = display_df['quantity'].apply(lambda x: f"{x:.6f}")
        if 'price' in display_df:
            display_df['Price'] = display_df['price'].apply(lambda x: f"${x:,.2f}")
        if 'profit_loss' in display_df:
            display_df['P&L'] = display_df['profit_loss'].apply(
                lambda x: f"${x:,.2f}" if pd.notna(x) and x != 0 else "-"
            )
        if 'strategy' in display_df:
            display_df['Strategy'] = display_df['strategy']
        
        # Select columns to display (only include columns that exist)
        columns_to_show = ['Time', 'Symbol']
        if 'Type' in display_df:
            columns_to_show.append('Type')
        if 'Quantity' in display_df:
            columns_to_show.append('Quantity')
        if 'Price' in display_df:
            columns_to_show.append('Price')
        if 'P&L' in display_df:
            columns_to_show.append('P&L')
        if 'Strategy' in display_df:
            columns_to_show.append('Strategy')
        
        # Display table
        st.dataframe(
            display_df[columns_to_show],
            width="stretch",
            hide_index=True
        )
        
        # Export option
        if st.button("📥 Export to CSV"):
            csv = df_trades.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"trades_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
    
    def show_performance_metrics(self):
        """Display enhanced performance metrics with live data"""
        st.subheader("🎯 Performance Metrics")
        
        # Fetch data
        performance = self.fetch_performance()
        strategies_data = self.fetch_strategies()
        portfolio = self.fetch_portfolio()
        
        # Active Strategy Info
        if strategies_data:
            active_strategy = strategies_data.get('active_strategy', {})
            if isinstance(active_strategy, dict):
                strategy_name = active_strategy.get('name', 'Unknown')
            else:
                strategy_name = str(active_strategy)
            
            st.info(f"🎯 Active Strategy: **{strategy_name}**")
        
        # Performance Metrics
        if performance:
            st.markdown("### 📊 Overall Performance")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_return = performance.get('total_return', 0)
                st.metric(
                    "Total Return",
                    f"{total_return:.2f}%",
                    help="Total percentage return"
                )
            
            with col2:
                sharpe_ratio = performance.get('sharpe_ratio', 0)
                st.metric(
                    "Sharpe Ratio",
                    f"{sharpe_ratio:.2f}" if sharpe_ratio else "N/A",
                    help="Risk-adjusted return metric"
                )
            
            with col3:
                max_drawdown = performance.get('max_drawdown', 0)
                st.metric(
                    "Max Drawdown",
                    f"{max_drawdown:.2f}%",
                    help="Maximum peak-to-trough decline"
                )
            
            with col4:
                win_rate = performance.get('win_rate', 0)
                st.metric(
                    "Win Rate",
                    f"{win_rate*100:.1f}%" if win_rate else "N/A",
                    help="Percentage of profitable trades"
                )
            
            st.divider()
            
            # Additional metrics
            col1, col2, col3 = st.columns(3)
            
            with col1:
                total_trades = performance.get('total_trades', 0)
                st.metric("Total Trades", total_trades)
                
                winning_trades = performance.get('winning_trades', 0)
                st.metric("Winning Trades", winning_trades)
            
            with col2:
                avg_win = performance.get('average_win', 0)
                st.metric("Avg Win", f"${avg_win:.2f}")
                
                avg_loss = performance.get('average_loss', 0)
                st.metric("Avg Loss", f"${avg_loss:.2f}")
            
            with col3:
                profit_factor = performance.get('profit_factor', 0)
                st.metric("Profit Factor", f"{profit_factor:.2f}" if profit_factor else "N/A")
                
                best_trade = performance.get('best_trade', 0)
                st.metric("Best Trade", f"${best_trade:.2f}")
        
        st.divider()
        
        # Portfolio Value Chart
        st.markdown("### 📈 Portfolio Value Over Time")
        portfolio_history = self.fetch_portfolio_value_history()
        
        # Check if portfolio_history is a dict (current value) or list (historical data)
        if portfolio_history and isinstance(portfolio_history, dict):
            # Single value response - show current portfolio value
            current_value = portfolio_history.get('total_value_usdt', 0)
            initial_balance = portfolio_history.get('initial_balance', 10000)
            total_return = portfolio_history.get('total_return', 0)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Current Value", f"${current_value:,.2f}")
            with col2:
                st.metric("Initial Balance", f"${initial_balance:,.2f}")
            with col3:
                st.metric("Total Return", f"{total_return:.2f}%")
            
            st.info("📊 Portfolio value chart will show history as you trade over time")
            
        elif portfolio_history and isinstance(portfolio_history, list) and len(portfolio_history) > 0:
            # Historical data available
            df_portfolio = pd.DataFrame(portfolio_history)
            df_portfolio['timestamp'] = pd.to_datetime(df_portfolio['timestamp'], format='ISO8601')
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df_portfolio['timestamp'],
                y=df_portfolio['value'],
                mode='lines',
                name='Portfolio Value',
                line=dict(color='#1f77b4', width=2),
                fill='tozeroy',
                fillcolor='rgba(31, 119, 180, 0.2)'
            ))
            
            fig.update_layout(
                title='Portfolio Value History',
                xaxis_title='Date',
                yaxis_title='Value ($)',
                hovermode='x unified',
                height=400
            )
            
            st.plotly_chart(fig, width="stretch")
        else:
            st.info("📊 Portfolio history will appear here as you trade")
        
        st.divider()
        
        # Strategy Details
        if strategies_data:
            st.markdown("### 📋 Available Strategies")
            
            strategies = strategies_data.get('available_strategies', [])
            
            for strategy in strategies:
                with st.expander(f"📊 {strategy['name']}"):
                    st.write(f"**Description:** {strategy.get('description', 'N/A')}")
                    
                    if 'parameters' in strategy:
                        st.write("**Parameters:**")
                        params = strategy['parameters']
                        
                        # Display parameters in a nice format
                        param_col1, param_col2 = st.columns(2)
                        items = list(params.items())
                        mid = len(items) // 2
                        
                        with param_col1:
                            for key, value in items[:mid]:
                                st.markdown(f"- **{key}**: {value}")
                        
                        with param_col2:
                            for key, value in items[mid:]:
                                st.markdown(f"- **{key}**: {value}")
    
    def show_market_overview(self):
        """Display market overview"""
        st.subheader("🌍 Market Overview")
        
        symbols = ['BTCUSDT', 'ETHUSDT', 'ADAUSDT']
        cols = st.columns(len(symbols))
        
        for i, symbol in enumerate(symbols):
            latest_data = self.get_data(f"market-data/{symbol}/latest")
            
            with cols[i]:
                if latest_data:
                    # API returns 'price' not 'close_price'
                    price = latest_data.get('price') or latest_data.get('close_price', 0)
                    # Use actual 24h change from API if available
                    change_24h = latest_data.get('change_24h', 0)
                    
                    st.metric(
                        label=symbol.replace('USDT', '/USDT'),
                        value=f"${price:,.2f}",
                        delta=f"{change_24h:.2f}%"
                    )
                else:
                    st.metric(symbol, "N/A")
    
    def show_ml_predictions(self):
        """Display AI insights and predictions"""
        st.header("🤖 AI Insights")
        
        # Sentiment Analysis Section
        st.subheader("📊 Market Sentiment Analysis")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            symbol = st.selectbox(
                "Select Symbol",
                ["BTC", "ETH", "SOL", "ADA", "DOT"],
                key="sentiment_symbol"
            )
        
        with col2:
            if st.button("🔄 Refresh Sentiment", key="refresh_sentiment"):
                st.session_state.sentiment_cache = {}
                st.rerun()
        
        # Get sentiment
        with st.spinner(f"Analyzing sentiment for {symbol}..."):
            sentiment_data = self.get_data(f"ai/sentiment/{symbol}")
        
        if sentiment_data and "sentiment" in sentiment_data:
            # Display sentiment gauge
            sentiment_value = sentiment_data.get("sentiment", 0)
            confidence = sentiment_data.get("confidence", 0)
            
            # Color based on sentiment
            if sentiment_value > 0.3:
                color = "🟢"
                label = "BULLISH"
                bg_color = "#d4edda"
            elif sentiment_value < -0.3:
                color = "🔴"
                label = "BEARISH"
                bg_color = "#f8d7da"
            else:
                color = "🟡"
                label = "NEUTRAL"
                bg_color = "#fff3cd"
            
            # Metrics
            col1, col2, col3 = st.columns(3)
            col1.metric("Sentiment", f"{color} {label}")
            col2.metric("Score", f"{sentiment_value:+.2f}")
            col3.metric("Confidence", f"{confidence:.0%}")
            
            # Reason
            st.info(f"**Analysis:** {sentiment_data.get('reason', 'N/A')}")
            
            # Sources
            if sentiment_data.get("sources"):
                with st.expander("📰 View Sources"):
                    for i, source in enumerate(sentiment_data["sources"][:5], 1):
                        st.text(f"{i}. {source}")
        else:
            st.warning("Unable to fetch sentiment data. Please try again.")
        
        st.divider()
        
        # Daily Commentary Section
        st.subheader("📝 Daily Market Commentary")
        
        if st.button("Generate Daily Summary", key="gen_summary"):
            with st.spinner("Generating AI commentary..."):
                commentary = self.get_data("ai/commentary/daily")
                if commentary and "commentary" in commentary:
                    st.success(commentary["commentary"])
                else:
                    st.warning("Unable to generate commentary.")
        
        st.divider()
        
        # Risk Assessment Section
        st.subheader("⚠️ Risk Assessment")
        
        if st.button("Generate Risk Assessment", key="gen_risk"):
            with st.spinner("Analyzing portfolio risk..."):
                risk = self.get_data("ai/risk-assessment")
                if risk and "risk_assessment" in risk:
                    st.warning(risk["risk_assessment"])
                else:
                    st.warning("Unable to generate risk assessment.")
        
        st.divider()
        
        # Recent Trade Explanations
        st.subheader("💡 Recent Trade Explanations")
        
        trades = self.get_data("trades?limit=5")
        if trades:
            for i, trade in enumerate(trades[:5]):
                trade_symbol = trade.get('symbol', 'N/A')
                trade_side = trade.get('side', 'N/A')
                trade_price = trade.get('price', 0)
                
                with st.expander(f"{trade_symbol} - {trade_side.upper()} @ ${trade_price:.2f}"):
                    if st.button(f"Explain this trade", key=f"explain_{i}"):
                        with st.spinner("Generating explanation..."):
                            explanation_data = {
                                "symbol": trade_symbol,
                                "action": trade_side.upper(),
                                "price": trade_price,
                                "technical_signal": 0.0,  # Would come from trade data
                                "sentiment_signal": 0.0,
                                "lstm_signal": 0.0
                            }
                            try:
                                response = requests.post(
                                    f"{self.api_url}/ai/explain-trade",
                                    json=explanation_data,
                                    timeout=30
                                )
                                if response.status_code == 200:
                                    result = response.json()
                                    st.write(result.get("explanation", "Unable to generate explanation."))
                                else:
                                    st.error("Error generating explanation")
                            except Exception as e:
                                st.error(f"Error: {e}")
        else:
            st.info("No recent trades available.")
    
    def show_live_signals(self, symbol: str = "BTCUSDT"):
        """Display live trading signals - ACTUAL signals from trading engine"""
        st.subheader(f"🚨 Live Trading Signals - {symbol}")
        
        # Add warning banner
        st.info("⚡ Showing ACTUAL signals from the live trading engine (Week1Refined5m strategy)")
        
        try:
            # Get ACTUAL signals from the trading engine via API
            signal_data = self.api.get(f"/api/signals/{symbol}")
            
            if not signal_data:
                st.warning(f"No live signal data available for {symbol}")
                st.info("The trading engine may still be accumulating 5-minute candles (needs 60+ candles = ~5 hours)")
                
                # Try to get from all signals endpoint
                all_signals = self.api.get("/api/signals")
                if all_signals and 'signals' in all_signals:
                    st.write("**Available symbols with signals:**")
                    for sig in all_signals['signals']:
                        st.write(f"• {sig['symbol']}: {sig['signal_type']}")
                return
            
            # Extract current values from ACTUAL trading engine
            current_price = signal_data.get('current_price', 0)
            current_rsi = signal_data.get('rsi')
            ma_fast = signal_data.get('ma_fast')
            ma_slow = signal_data.get('ma_slow')
            trend = signal_data.get('trend', 'UNKNOWN')
            latest_signal = signal_data.get('signal', 0)
            signal_type = signal_data.get('signal_type', 'HOLD')
            last_change = signal_data.get('last_change')
            note = signal_data.get('note', '')
            
            # Display current market state from ACTUAL trading engine
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(f"Current {symbol.replace('USDT', '')} Price", f"${current_price:,.2f}")
            
            with col2:
                trend_emoji = "🟢 BULLISH" if trend == "BULLISH" else "🔴 BEARISH" if trend == "BEARISH" else "⚪ NEUTRAL"
                st.metric("Trend (HTF)", trend_emoji)
            
            with col3:
                if current_rsi is not None:
                    rsi_status = "🔥 Overbought" if current_rsi > 70 else "❄️ Oversold" if current_rsi < 30 else "⚖️ Neutral"
                    st.metric("RSI Status", f"{rsi_status} ({current_rsi:.1f})")
                else:
                    st.metric("RSI Status", "N/A")
            
            with col4:
                if ma_fast and ma_slow:
                    ma_gap = ma_fast - ma_slow
                    gap_pct = (ma_gap / ma_slow) * 100
                    st.metric("MA Gap", f"{gap_pct:.2f}%")
                else:
                    st.metric("MA Gap", "N/A")
            
            # Signal analysis - ACTUAL from trading engine
            st.subheader("🎯 Current Trading Signal (ACTUAL - What Bot Sees)")
            
            # Show note if available
            if note:
                st.caption(f"ℹ️ {note}")
            
            signal_col1, signal_col2 = st.columns(2)
            
            with signal_col1:
                if signal_type == "BUY":
                    signal_strength = "STRONG" if latest_signal >= 1.0 else "MODERATE"
                    st.success(f"🟢 {signal_strength} BUY SIGNAL ({latest_signal:.2f})")
                    
                    # Entry details
                    st.write("**Entry Strategy:**")
                    st.write(f"• Enter around current price: ${current_price:,.2f}")
                    st.write(f"• Stop loss: ${current_price * 0.85:,.2f} (-15%)")
                    st.write(f"• Take profit: ${current_price * 1.30:,.2f} (+30%)")
                    st.write(f"• Position size: 30% of portfolio max")
                    
                    # Show why it might not execute
                    st.warning("⚠️ Bot only executes when signal CHANGES from HOLD→BUY")
                    
                elif signal_type == "SELL":
                    st.error(f"🔴 SELL SIGNAL ({latest_signal:.2f})")
                    
                    # Exit details
                    st.write("**Exit Strategy:**")
                    st.write(f"• Exit around current price: ${current_price:,.2f}")
                    st.write("• Close any open long positions")
                    
                else:  # HOLD
                    st.info(f"🟡 HOLD SIGNAL ({latest_signal:.2f})")
                    st.write("**No action recommended**")
                    st.write("• Waiting for better entry/exit conditions")
                    rsi_display = f"{current_rsi:.1f}" if current_rsi is not None else "N/A"
                    st.write(f"• RSI: {rsi_display} (needs < 30 for BUY)")
                    st.write(f"• Trend: {trend}")
                    
            with signal_col2:
                # Technical details from ACTUAL trading engine
                st.write("**📊 Technical Analysis:**")
                st.write(f"• MA Fast: ${ma_fast:,.2f}" if ma_fast else "• MA Fast: N/A")
                st.write(f"• MA Slow: ${ma_slow:,.2f}" if ma_slow else "• MA Slow: N/A")
                st.write(f"• RSI(14): {current_rsi:.2f}" if current_rsi else "• RSI(14): N/A")
                
                st.write("**🎯 Week1Refined5m Strategy:**")
                st.write("• **BUY**: RSI < 30 + Price mean reversion + Bullish trend")
                st.write("• **SELL**: Position held + favorable exit conditions")
                st.write("• **HOLD**: Waiting for optimal entry conditions")
                
                # Show when signal last changed
                if last_change:
                    from datetime import datetime
                    try:
                        change_time = datetime.fromisoformat(last_change)
                        st.write(f"\n**Last Signal Change:**")
                        st.write(f"• {change_time.strftime('%Y-%m-%d %H:%M:%S')}")
                    except:
                        pass
            
            # Recent signals history from API
            st.subheader("📜 Recent Signal Changes")
            
            # Get recent alerts from signal monitor
            all_signals_data = self.api.get("/api/signals")
            if all_signals_data and 'recent_alerts' in all_signals_data:
                recent_alerts = all_signals_data['recent_alerts'][-20:]  # Last 20 alerts
                
                if recent_alerts:
                    alerts_display = []
                    for alert in recent_alerts:
                        alerts_display.append({
                            'Time': alert['timestamp'][11:19],  # HH:MM:SS
                            'Symbol': alert['symbol'],
                            'Type': alert['type'],
                            'Message': alert['message'],
                            'Priority': alert['priority']
                        })
                    
                    alerts_df = pd.DataFrame(alerts_display)
                    st.dataframe(alerts_df, use_container_width=True)
                else:
                    st.info("No recent signal changes detected. Bot is monitoring...")
            else:
                st.warning("Could not fetch signal history from API")
            
            # Auto-refresh option
            st.subheader("🔄 Auto-Refresh")
            auto_refresh = st.checkbox("Enable auto-refresh (30 seconds)")
            if auto_refresh:
                time.sleep(30)
                st.rerun()
                
        except Exception as e:
            st.error(f"Error generating signals for {symbol}: {str(e)}")
            st.write("**Possible Issues:**")
            st.write(f"• No historical data available for {symbol}")
            st.write("• Currently only BTCUSDT is fully supported")
            st.write("• Database connection issues")
            st.write("**Fallback: Manual Signal Check**")
            st.code("python src/strategies/entry_point_analyzer.py")
        
        finally:
            if 'db' in locals():
                db.close()
    
    def execute_manual_buy(self, symbol: str, amount: float) -> bool:
        """Execute a manual buy order"""
        try:
            response = self.api.post('/api/orders/buy', {
                'symbol': symbol,
                'amount': amount,
                'order_type': 'market'
            })
            
            if response and response.get('success'):
                order_id = response.get('order_id', 'N/A')
                st.sidebar.success(f"✅ Buy order placed!\nOrder ID: {order_id}")
                logger.info(f"Buy order executed: {symbol} ${amount}")
                return True
            else:
                error = response.get('error', 'Unknown error') if response else 'No response'
                st.sidebar.error(f"❌ Order failed: {error}")
                logger.error(f"Buy order failed: {error}")
                return False
                
        except Exception as e:
            st.sidebar.error(f"❌ Error: {str(e)}")
            logger.error(f"Buy order exception: {e}")
            return False
    
    def execute_manual_sell(self, symbol: str, amount: float) -> bool:
        """Execute a manual sell order"""
        try:
            response = self.api.post('/api/orders/sell', {
                'symbol': symbol,
                'amount': amount,
                'order_type': 'market'
            })
            
            if response and response.get('success'):
                order_id = response.get('order_id', 'N/A')
                st.sidebar.success(f"✅ Sell order placed!\nOrder ID: {order_id}")
                logger.info(f"Sell order executed: {symbol} ${amount}")
                return True
            else:
                error = response.get('error', 'Unknown error') if response else 'No response'
                st.sidebar.error(f"❌ Order failed: {error}")
                logger.error(f"Sell order failed: {error}")
                return False
                
        except Exception as e:
            st.sidebar.error(f"❌ Error: {str(e)}")
            logger.error(f"Sell order exception: {e}")
            return False
    
    def sidebar_controls(self):
        """Enhanced sidebar with trading controls"""
        st.sidebar.title("🎯 Trading Controls")
        
        st.sidebar.markdown("---")
        
        # Quick Trade Section
        st.sidebar.subheader("⚡ Quick Trade")
        
        # Symbol selection
        trade_symbol = st.sidebar.selectbox(
            "Symbol",
            ["BTCUSDT", "ETHUSDT", "SOLUSDT", "ADAUSDT", "DOTUSD"],
            key="trade_symbol"
        )
        
        # Get current price
        live_prices = self.fetch_live_prices()
        current_price = 0
        if live_prices and trade_symbol in live_prices:
            current_price = live_prices[trade_symbol].get('price', 0)
            st.sidebar.caption(f"Current Price: ${current_price:,.2f}")
        
        # Amount input
        amount = st.sidebar.number_input(
            "Amount (USD)",
            min_value=10.0,
            max_value=10000.0,
            value=100.0,
            step=10.0,
            help="Amount in USD to trade"
        )
        
        # Buy/Sell buttons
        col1, col2 = st.sidebar.columns(2)
        
        with col1:
            if st.button("🟢 BUY", width="stretch", type="primary"):
                # Confirmation
                if 'confirm_buy' not in st.session_state:
                    st.session_state.confirm_buy = True
                    st.sidebar.warning(f"⚠️ Confirm BUY {trade_symbol} for ${amount:.2f}?")
                    st.sidebar.info("Click BUY again to confirm")
                else:
                    # Execute trade
                    if self.execute_manual_buy(trade_symbol, amount):
                        st.session_state.last_refresh = 0  # Force refresh
                    st.session_state.confirm_buy = False
        
        with col2:
            if st.button("🔴 SELL", width="stretch"):
                # Confirmation
                if 'confirm_sell' not in st.session_state:
                    st.session_state.confirm_sell = True
                    st.sidebar.warning(f"⚠️ Confirm SELL {trade_symbol} for ${amount:.2f}?")
                    st.sidebar.info("Click SELL again to confirm")
                else:
                    # Execute trade
                    if self.execute_manual_sell(trade_symbol, amount):
                        st.session_state.last_refresh = 0  # Force refresh
                    st.session_state.confirm_sell = False
        
        st.sidebar.caption("⚠️ Paper Trading Mode - No real money")
        
        st.sidebar.markdown("---")
        
        # Engine Controls
        st.sidebar.subheader("🎛️ Engine Control")
        
        # Show prominent engine status
        status = self.fetch_system_status()
        if status:
            engine_status = status.get('trading_engine', 'unknown')
            if engine_status in ['running', 'active']:
                st.sidebar.success("### 🟢 ENGINE: RUNNING")
            elif engine_status == 'stopped':
                st.sidebar.error("### 🔴 ENGINE: STOPPED")
            else:
                st.sidebar.warning("### 🟡 ENGINE: UNKNOWN")
        else:
            st.sidebar.error("### ⚠️ Cannot connect to API")
        
        col1, col2 = st.sidebar.columns(2)
        
        with col1:
            if st.button("▶️ Start", width="stretch", help="Start trading engine", type="primary"):
                response = self.api.post('/api/trading/start')
                if response:
                    st.sidebar.success("✅ Trading started!")
                    logger.info("Trading engine started")
                    time.sleep(1)
                    st.rerun()
                else:
                    # Check if already running
                    status = self.fetch_system_status()
                    if status and status.get('trading_engine') in ['running', 'active']:
                        st.sidebar.info("ℹ️ Engine is already running")
                    # Error message already shown by APIClient
        
        with col2:
            if st.button("⏹️ Stop", width="stretch", help="Stop trading engine"):
                response = self.api.post('/api/trading/stop')
                if response:
                    st.sidebar.warning("⏸️ Trading stopped!")
                    logger.info("Trading engine stopped")
                    time.sleep(1)
                    st.rerun()
                else:
                    # Check if already stopped
                    status = self.fetch_system_status()
                    if status and status.get('trading_engine') == 'stopped':
                        st.sidebar.info("ℹ️ Engine is already stopped")
                    # Error message already shown by APIClient
                    time.sleep(1)
                    st.rerun()
        
        # Strategy selector
        strategies = self.fetch_strategies()
        if strategies and 'available_strategies' in strategies:
            st.sidebar.subheader("📊 Active Strategy")
            active_strategy = strategies.get('active_strategy', {})
            
            # Handle both dict and string responses
            if isinstance(active_strategy, dict):
                strategy_name = active_strategy.get('name', 'Unknown')
            else:
                strategy_name = str(active_strategy) if active_strategy else 'None'
            
            st.sidebar.info(f"**{strategy_name}**")
            
            # Strategy switcher (optional, for future)
            # strategy_list = [s['name'] for s in strategies['available_strategies']]
            # new_strategy = st.sidebar.selectbox("Switch Strategy", strategy_list)
        
        st.sidebar.markdown("---")
        
        # Chart Settings
        st.sidebar.subheader("� Chart Settings")
        selected_symbol = st.sidebar.selectbox(
            "Chart Symbol",
            ["BTCUSDT", "ETHUSDT", "SOLUSDT", "ADAUSDT", "DOTUSD"],
            key="chart_symbol"
        )
        
        # Refresh button
        st.sidebar.markdown("---")
        if st.sidebar.button("🔄 Refresh Data", width="stretch"):
            st.session_state.last_refresh = 0
            st.rerun()
        
        return selected_symbol
    
    def render_overview_tab(self):
        """Enhanced Overview tab with real-time data"""
        # Check API availability first
        if not self.check_api_connection():
            return
        
        # Auto-refresh control
        col1, col2 = st.columns([3, 1])
        with col1:
            st.subheader("📊 Real-Time Dashboard")
        with col2:
            auto_refresh = st.checkbox("⟳ Auto-refresh (10s)", value=st.session_state.auto_refresh_enabled)
            st.session_state.auto_refresh_enabled = auto_refresh
        
        # Auto-refresh logic
        if auto_refresh:
            time.sleep(0.1)  # Small delay to prevent rapid refreshes
            if time.time() - st.session_state.last_refresh >= 10:
                st.session_state.last_refresh = time.time()
                st.rerun()
        
        # Show last update time
        seconds_ago = int(time.time() - st.session_state.last_refresh)
        st.caption(f"Last updated: {seconds_ago}s ago")
        
        # Fetch all data
        status = self.fetch_system_status()
        portfolio = self.fetch_portfolio()
        live_prices = self.fetch_live_prices()
        signals = self.fetch_signals()
        
        # System status header
        if status:
            status_col1, status_col2 = st.columns([3, 1])
            with status_col1:
                st.markdown(f"### 🤖 AI Trading Bot")
            with status_col2:
                engine_status = status.get('trading_engine', 'unknown')
                if engine_status in ['running', 'active']:
                    st.success("🟢 System: ACTIVE")
                else:
                    st.warning("🟡 System: INACTIVE")
        
        # Metric cards
        if portfolio:
            metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
            
            with metric_col1:
                total_value = portfolio.get('total_value', 0)
                st.metric(
                    "Portfolio Value",
                    f"${total_value:,.2f}",
                    help="Total portfolio value including cash and positions"
                )
            
            with metric_col2:
                # Calculate 24h P&L (mock for now, will be real in next step)
                daily_pnl = 0
                daily_pnl_pct = 0
                positions = portfolio.get('positions', [])
                for pos in positions:
                    daily_pnl += pos.get('unrealized_pnl', 0)
                if total_value > 0:
                    daily_pnl_pct = (daily_pnl / total_value) * 100
                
                st.metric(
                    "24h P&L",
                    f"${daily_pnl:,.2f}",
                    f"{daily_pnl_pct:+.2f}%",
                    delta_color="normal"
                )
            
            with metric_col3:
                num_positions = len(positions)
                st.metric(
                    "Active Positions",
                    num_positions,
                    help="Number of open positions"
                )
            
            with metric_col4:
                # Win rate from performance (if available)
                performance = self.fetch_performance()
                win_rate = 0
                if performance and 'win_rate' in performance:
                    win_rate = performance['win_rate'] * 100
                st.metric(
                    "Win Rate",
                    f"{win_rate:.1f}%",
                    help="Percentage of winning trades"
                )
        
        st.divider()
        
        # Live market prices panel
        st.subheader("💹 Live Market Prices")
        if live_prices:
            price_cols = st.columns(5)
            symbols = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'ADAUSDT', 'DOTUSDT']
            
            # Extract prices dict from response
            prices_dict = live_prices.get('prices', {})
            
            for i, symbol in enumerate(symbols):
                with price_cols[i]:
                    price_data = prices_dict.get(symbol, {})
                    price = price_data.get('price', 0)
                    change_24h = price_data.get('change_24h', 0)
                    
                    # Format symbol for display (remove USDT)
                    display_symbol = symbol.replace('USDT', '')
                    
                    st.metric(
                        display_symbol,
                        f"${price:,.2f}" if price > 100 else f"${price:.4f}",
                        f"{change_24h:+.2f}%",
                        delta_color="normal"
                    )
        else:
            st.info("Live prices not available. Ensure API is running.")
        
        st.divider()
        
        # Two column layout for positions and signals
        col_positions, col_signals = st.columns([2, 1])
        
        with col_positions:
            st.subheader("📊 Active Positions")
            if portfolio and positions:
                position_data = []
                for pos in positions:
                    position_data.append({
                        'Symbol': pos.get('symbol', 'N/A'),
                        'Quantity': f"{pos.get('quantity', 0):.4f}",
                        'Avg Price': f"${pos.get('entry_price', 0):,.2f}",
                        'Current Value': f"${pos.get('value', 0):,.2f}",
                        'P&L': f"${pos.get('unrealized_pnl', 0):,.2f}",
                        'P&L %': f"{pos.get('unrealized_pnl_pct', 0):+.2f}%"
                    })
                
                if position_data:
                    df_positions = pd.DataFrame(position_data)
                    st.dataframe(df_positions, width="stretch", hide_index=True)
                else:
                    st.info("No active positions")
            else:
                st.info("No active positions. Start trading to see positions here.")
        
        with col_signals:
            st.subheader("🚨 Recent Signals")
            if signals:
                # Display signals for tracked symbols
                signal_symbols = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT']
                for sym in signal_symbols:
                    if sym in signals:
                        sig_data = signals[sym]
                        signal_type = sig_data.get('signal_type', 'HOLD')
                        strength = sig_data.get('signal', 0)
                        
                        # Signal emoji
                        if signal_type == 'BUY':
                            emoji = "🟢"
                            color = "green"
                        elif signal_type == 'SELL':
                            emoji = "🔴"
                            color = "red"
                        else:
                            emoji = "🟡"
                            color = "gray"
                        
                        display_sym = sym.replace('USDT', '')
                        st.markdown(f"{emoji} **{display_sym}**: {signal_type} ({strength:.2f})")
            else:
                st.info("No signals available")
        
        # Call original market overview and portfolio methods for additional info
        st.divider()
        self.show_market_overview()
        self.show_portfolio_overview()
    
    def run(self):
        """Run the enhanced dashboard with Phase 4 features"""
        # Main title with enhanced styling and engine status
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown("<h1 class='main-header'>🤖 AI Trading Bot Dashboard</h1>", 
                       unsafe_allow_html=True)
        with col2:
            # Engine status badge in header
            status = self.fetch_system_status()
            if status:
                engine_status = status.get('trading_engine', 'unknown')
                if engine_status in ['running', 'active']:
                    st.success("🟢 **ENGINE ON**")
                elif engine_status == 'stopped':
                    st.error("🔴 **ENGINE OFF**")
                else:
                    st.warning("🟡 **ENGINE ?**")
            else:
                st.error("⚠️ **API OFFLINE**")
        
        # Paper trading mode indicator - PROMINENT WARNING
        if status:
            paper_trading = status.get('paper_trading', True)
            mode = status.get('mode', 'UNKNOWN')
            
            if paper_trading:
                st.warning(
                    "🟡 **PAPER TRADING MODE** - NO REAL MONEY AT RISK\n\n"
                    "This bot is running in simulation mode. All trades and performance metrics are simulated. "
                    "No real money is being traded.",
                    icon="⚠️"
                )
            else:
                st.error(
                    "💰 **LIVE TRADING MODE** - REAL MONEY AT RISK!\n\n"
                    "This bot is trading with real money. All trades will execute on your live exchange account.",
                    icon="🚨"
                )
        
        # Check for alerts (signal changes, large P&L movements)
        self.check_and_alert()
        
        # Sidebar with enhanced trading controls
        selected_symbol = self.sidebar_controls()
        
        # API status in sidebar with alert toggle
        st.sidebar.markdown("---")
        st.sidebar.subheader("⚙️ Settings")
        
        if self.api.is_api_available():
            st.sidebar.success("✅ API Status: running")
        else:
            st.sidebar.error("❌ API Status: offline")
            st.sidebar.caption("Run: ./start_api.sh")
        
        # Trading mode indicator in sidebar
        if status:
            mode = status.get('mode', 'UNKNOWN')
            paper_trading = status.get('paper_trading', True)
            
            if paper_trading:
                st.sidebar.info(f"📄 Mode: {mode}")
            else:
                st.sidebar.error(f"💰 Mode: {mode}")
        
        # Alert settings
        st.session_state.alerts_enabled = st.sidebar.checkbox(
            "🔔 Enable Alerts",
            value=st.session_state.alerts_enabled,
            help="Get notifications for signal changes and large P&L movements"
        )
        
        # Test alert button
        if st.sidebar.button("🧪 Test Alert", help="Send a test notification"):
            if st.session_state.alerts_enabled:
                st.toast("🎉 Alert system is working! You'll see notifications for signal changes and P&L movements.", icon="✅")
            else:
                st.warning("⚠️ Please enable alerts first!")
        
        # Main content tabs
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
            ["📊 Overview", "📈 Charts", "📝 Trades", "🎯 Performance", "🚨 Live Signals", "🤖 AI Insights"]
        )
        
        with tab1:
            self.render_overview_tab()
        
        with tab2:
            if self.check_api_connection():
                self.plot_price_chart(selected_symbol)
        
        with tab3:
            if self.check_api_connection():
                self.show_trading_history()
        
        with tab4:
            if self.check_api_connection():
                self.show_performance_metrics()
        
        with tab5:
            if self.check_api_connection():
                self.show_live_signals(selected_symbol)
        
        with tab6:
            if self.check_api_connection():
                self.show_ml_predictions()
        
        # Footer with system info
        st.sidebar.markdown("---")
        st.sidebar.caption(f"🕒 Last refresh: {int(time.time() - st.session_state.last_refresh)}s ago")
        st.sidebar.caption("📍 Phase 4: Enhanced Dashboard")
        st.sidebar.caption("🔒 Paper Trading Mode")


def main():
    """Main function"""
    dashboard = TradingDashboard()
    dashboard.run()


if __name__ == "__main__":
    main()