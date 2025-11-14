"""
Professional AI Trading Bot Dashboard
Modern dark theme with enhanced visuals and clean layout
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import requests
from datetime import datetime, timedelta
import time
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# Page config with dark theme
st.set_page_config(
    page_title="AI Trading Bot Pro",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'About': "AI-Enhanced Trading Bot - Professional Dashboard"
    }
)


# Authentication function
def check_password():
    """Returns True if user is authenticated."""
    
    # Initialize authentication state
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    
    # If already authenticated, continue
    if st.session_state.authenticated:
        return True
    
    # Hide default Streamlit elements for clean login page
    st.markdown("""
    <style>
        /* Hide Streamlit elements on login page */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        .stDeployButton {display: none;}
        
        /* Full screen login background */
        .stApp {
            background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
        }
        
        /* Hide default padding */
        .block-container {
            padding-top: 0rem;
            padding-bottom: 0rem;
            padding-left: 1rem;
            padding-right: 1rem;
        }
        
        /* Login input styling */
        .stTextInput > div > div > input {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(102, 126, 234, 0.3);
            border-radius: 12px;
            color: white;
            font-size: 1rem;
            padding: 1rem;
        }
        
        .stTextInput > div > div > input:focus {
            border-color: rgba(102, 126, 234, 0.8);
            box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.2);
        }
        
        .stTextInput > label {
            color: rgba(255, 255, 255, 0.9);
            font-weight: 600;
            font-size: 0.95rem;
            margin-bottom: 0.5rem;
        }
        
        /* Button styling */
        .stButton > button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 12px;
            padding: 0.75rem 2rem;
            font-weight: 600;
            font-size: 1rem;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
        }
        
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Center everything vertically and horizontally
    col_left, col_center, col_right = st.columns([1, 2, 1])
    
    with col_center:
        st.markdown("<div style='height: 10vh;'></div>", unsafe_allow_html=True)
        
        # Logo and title
        st.markdown("""
        <div style='text-align: center; margin-bottom: 3rem;'>
            <div style='font-size: 4rem; margin-bottom: 1rem;'>🤖</div>
            <h1 style='
                color: white;
                font-size: 2.5rem;
                font-weight: 700;
                margin-bottom: 0.5rem;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
            '>AI Trading Bot Pro</h1>
            <p style='
                color: rgba(255, 255, 255, 0.7);
                font-size: 1rem;
                font-weight: 500;
            '>AI-Enhanced • Real-Time Analysis • Professional Trading</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Login card
        st.markdown("""
        <div style='
            background: linear-gradient(135deg, rgba(15, 12, 41, 0.8), rgba(48, 43, 99, 0.6));
            border-radius: 20px;
            padding: 2.5rem;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.4), 0 0 100px rgba(102, 126, 234, 0.1);
            border: 1px solid rgba(102, 126, 234, 0.3);
            backdrop-filter: blur(10px);
        '>
        """, unsafe_allow_html=True)
        
        # Password input
        password = st.text_input(
            "Password", 
            type="password", 
            key="password_input",
            placeholder="Enter your password",
            label_visibility="visible"
        )
        
        st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
        
        # Login button
        if st.button("🔓 Unlock Dashboard", use_container_width=True):
            # Check password from secrets (Streamlit Cloud) or environment variable
            try:
                correct_password = st.secrets["app_password"]
            except (KeyError, FileNotFoundError, AttributeError):
                # Fallback for local development
                correct_password = "trading2024"
            
            if password == correct_password:
                st.session_state.authenticated = True
                st.success("✅ Access granted! Loading dashboard...")
                time.sleep(0.8)
                st.rerun()
            else:
                st.error("❌ Access denied. Please check your password.")
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Footer
        st.markdown("""
        <div style='text-align: center; margin-top: 2rem; color: rgba(255, 255, 255, 0.4); font-size: 0.85rem;'>
            <p>Secure authentication required • Your trading data is protected</p>
        </div>
        """, unsafe_allow_html=True)
    
    return False


# Check authentication before showing dashboard
if not check_password():
    st.stop()

# Professional dark theme CSS
st.markdown("""
<style>
    /* Main background and text */
    .stApp {
        background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
    }
    
    /* Remove Streamlit branding - but keep sidebar toggle working */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Keep header visible so sidebar toggle button works */
    header[data-testid="stHeader"] {
        background: transparent;
    }
    
    /* Custom header */
    .header-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
    }
    
    .header-title {
        color: white;
        font-size: 2.5rem;
        font-weight: 700;
        text-align: center;
        margin: 0;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    
    .header-subtitle {
        color: rgba(255,255,255,0.9);
        font-size: 1.1rem;
        text-align: center;
        margin-top: 0.5rem;
    }
    
    /* Metric cards */
    .metric-card {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 15px;
        padding: 1.5rem;
        margin: 0.5rem 0;
        min-height: 140px;
        height: 140px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
        transition: all 0.3s ease;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 40px rgba(0, 0, 0, 0.3);
        border-color: rgba(102, 126, 234, 0.5);
    }
    
    .metric-label {
        color: rgba(255, 255, 255, 0.7);
        font-size: 0.9rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 0.5rem;
    }
    
    .metric-value {
        color: white;
        font-size: 2rem;
        font-weight: 700;
        margin-bottom: 0.3rem;
    }
    
    .metric-delta {
        font-size: 0.9rem;
        font-weight: 600;
    }
    
    .metric-delta.positive {
        color: #10b981;
    }
    
    .metric-delta.negative {
        color: #ef4444;
    }
    
    /* Indicator cards for technical analysis */
    .indicator-card {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 1rem;
        margin: 0.5rem 0;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
        transition: all 0.3s ease;
    }
    
    .indicator-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 6px 24px rgba(0, 0, 0, 0.3);
        border-color: rgba(102, 126, 234, 0.4);
    }
    
    .indicator-label {
        color: rgba(255, 255, 255, 0.6);
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 0.5rem;
    }
    
    .indicator-value {
        color: white;
        font-size: 1.1rem;
        font-weight: 600;
        line-height: 1.4;
    }
    
    /* Status badges */
    .status-badge {
        display: inline-block;
        padding: 6px 16px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.85rem;
        letter-spacing: 0.5px;
        text-transform: uppercase;
    }
    
    .status-active {
        background: linear-gradient(135deg, #10b981, #059669);
        color: white;
        box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
    }
    
    .status-inactive {
        background: linear-gradient(135deg, #f59e0b, #d97706);
        color: white;
        box-shadow: 0 4px 12px rgba(245, 158, 11, 0.3);
    }
    
    .status-error {
        background: linear-gradient(135deg, #ef4444, #dc2626);
        color: white;
        box-shadow: 0 4px 12px rgba(239, 68, 68, 0.3);
    }
    
    /* Signal indicators */
    .signal-buy {
        background: linear-gradient(135deg, #10b981, #059669);
        color: white;
        padding: 8px 16px;
        border-radius: 10px;
        font-weight: 700;
        display: inline-block;
        box-shadow: 0 4px 12px rgba(16, 185, 129, 0.4);
    }
    
    .signal-sell {
        background: linear-gradient(135deg, #ef4444, #dc2626);
        color: white;
        padding: 8px 16px;
        border-radius: 10px;
        font-weight: 700;
        display: inline-block;
        box-shadow: 0 4px 12px rgba(239, 68, 68, 0.4);
    }
    
    .signal-hold {
        background: linear-gradient(135deg, #6b7280, #4b5563);
        color: white;
        padding: 8px 16px;
        border-radius: 10px;
        font-weight: 700;
        display: inline-block;
        box-shadow: 0 4px 12px rgba(107, 114, 128, 0.4);
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: rgba(15, 12, 41, 0.9);
        backdrop-filter: blur(10px);
    }
    
    [data-testid="stSidebar"] .element-container {
        color: white;
    }
    
    /* Sidebar toggle button - simple and clean, don't interfere with Streamlit */
    [data-testid="collapsedControl"] {
        visibility: visible !important;
        opacity: 1 !important;
    }
    
    /* Tables */
    .dataframe {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 10px;
        overflow: hidden;
    }
    
    /* Buttons */
    .stButton>button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.5rem 2rem;
        font-weight: 600;
        font-size: 1rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.5);
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: rgba(255, 255, 255, 0.05);
        border-radius: 10px;
        padding: 0.5rem;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        color: rgba(255, 255, 255, 0.7);
        border-radius: 8px;
        font-weight: 600;
        padding: 0.75rem 1.5rem;
        transition: all 0.3s ease;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background: rgba(255, 255, 255, 0.1);
        color: white;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
    
    /* Text colors */
    h1, h2, h3, h4, h5, h6, p, span, div {
        color: white !important;
    }
    
    /* Info boxes */
    .stAlert {
        background: rgba(255, 255, 255, 0.05);
        border-left: 4px solid #667eea;
        border-radius: 10px;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 10px;
        color: white;
        font-weight: 600;
    }
    
    /* Chart containers */
    .js-plotly-plot {
        border-radius: 15px;
        overflow: hidden;
    }
</style>
""", unsafe_allow_html=True)


class APIClient:
    """API client for backend communication"""
    
    def __init__(self, base_url: str = None):
        # For local development, always use localhost
        # Try to get API URL from secrets (Streamlit Cloud or Railway)
        if base_url is None:
            # Force localhost for local development
            base_url = "http://localhost:9000"
            logger.info(f"Using localhost API for local development: {base_url}")
            
            # Comment out the production logic for now
            # try:
            #     # Streamlit secrets access - try both possible locations
            #     if hasattr(st, 'secrets') and 'api_url' in st.secrets:
            #         base_url = st.secrets["api_url"]
            #         logger.info(f"Loaded API URL from secrets: {base_url}")
            #     else:
            #         raise KeyError("api_url not found in secrets")
            # except Exception as e:
            #     # Try environment variable for deployed environments
            #     import os
            #     env_api_url = os.getenv('API_URL', os.getenv('API_BASE_URL'))
            #     if env_api_url:
            #         base_url = env_api_url
            #         logger.info(f"Using API URL from environment: {base_url}")
            #     else:
            #         # Fallback to localhost for local development
            #         base_url = "http://localhost:9000"
            #         logger.warning(f"Using localhost API (no secrets/env found: {e})")
        self.base_url = base_url
        logger.info(f"APIClient initialized with base_url: {self.base_url}")
    
    def get(self, endpoint: str, timeout: int = 5) -> Optional[Dict]:
        """GET request with error handling"""
        try:
            url = f"{self.base_url}{endpoint}"
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()
            return response.json()
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            # Silently fail on connection errors (expected when API is not available)
            return None
        except Exception:
            # Silently fail on other errors in demo mode
            return None
    
    def post(self, endpoint: str, data: dict = None, timeout: int = 5) -> Optional[Dict]:
        """POST request with error handling"""
        try:
            response = requests.post(f"{self.base_url}{endpoint}", json=data, timeout=timeout)
            response.raise_for_status()
            return response.json()
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            return None
        except Exception:
            return None


def render_header():
    """Render professional header"""
    st.markdown("""
        <div class="header-container">
            <h1 class="header-title">🤖 AI Trading Bot Pro</h1>
            <p class="header-subtitle">
                AI-Enhanced • Real-Time Analysis • Professional Trading
            </p>
        </div>
    """, unsafe_allow_html=True)


def render_status_card(status_data: Dict):
    """Render system status card"""
    if not status_data:
        st.info("ℹ️ **Demo Mode** - Backend API not available. Displaying chart visualization only.")
        return
    
    is_active = status_data.get('trading_engine') == 'active'
    status_class = 'status-active' if is_active else 'status-inactive'
    status_text = '🟢 ACTIVE' if is_active else '🟡 INACTIVE'
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        # Combined System Status with Exchange and Data Feed
        exchange_status = '🟢 Connected' if status_data.get('exchange') == 'connected' else '🔴 Disconnected'
        feed_status = '🟢 Live' if status_data.get('data_feed') == 'active' else '🔴 Offline'
        
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">System Status</div>
                <div class="metric-value"><span class="status-badge {status_class}">{status_text}</span></div>
                <div style="font-size: 0.8rem; margin-top: 0.5rem; color: rgba(255,255,255,0.7);">
                    Exchange: {exchange_status}<br>
                    Data Feed: {feed_status}
                </div>
            </div>
        """, unsafe_allow_html=True)

    with col2:
        mode = status_data.get('mode', 'UNKNOWN')
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Trading Mode</div>
                <div class="metric-value">{mode}</div>
            </div>
        """, unsafe_allow_html=True)

    with col3:
        # Add Win Rate and Performance Stats here
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Performance</div>
                <div class="metric-value">Win Rate: 0%</div>
                <div style="font-size: 0.8rem; margin-top: 0.5rem; color: rgba(255,255,255,0.7);">
                    Total Trades: 3<br>
                    Avg Trade: $0.00
                </div>
            </div>
        """, unsafe_allow_html=True)

    with col4:
        # Additional stats can go here
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Market Status</div>
                <div class="metric-value">🟢 Monitoring</div>
                <div style="font-size: 0.8rem; margin-top: 0.5rem; color: rgba(255,255,255,0.7);">
                    Signals: Active<br>
                    Last Update: Just now
                </div>
            </div>
        """, unsafe_allow_html=True)


def render_portfolio_metrics(portfolio_data: Dict):
    """Render portfolio metrics"""
    if not portfolio_data:
        st.info("📊 Portfolio data requires backend API connection")
        return
    
    total_value = portfolio_data.get('total_value', 0)
    cash = portfolio_data.get('cash', portfolio_data.get('cash_balance', 0))  # Support both 'cash' and 'cash_balance'
    pnl = portfolio_data.get('unrealized_pnl', 0)
    pnl_pct = portfolio_data.get('total_return_pct', 0)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Portfolio Value</div>
                <div class="metric-value">${total_value:,.2f}</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Cash Balance</div>
                <div class="metric-value">${cash:,.2f}</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col3:
        delta_class = 'positive' if pnl >= 0 else 'negative'
        delta_sign = '+' if pnl >= 0 else ''
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Unrealized P&L</div>
                <div class="metric-value">${pnl:,.2f}</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col4:
        positions = len(portfolio_data.get('positions', []))
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Open Positions</div>
                <div class="metric-value">{positions}</div>
            </div>
        """, unsafe_allow_html=True)


def render_performance_chart(trades_data: list):
    """Render cumulative P&L chart"""
    if not trades_data:
        st.markdown("""
            <div class="metric-card" style="text-align: center; padding: 3rem;">
                <div style="font-size: 3rem; margin-bottom: 1rem;">📊</div>
                <div class="metric-label">No Trades Yet</div>
                <div style="color: rgba(255,255,255,0.6); margin-top: 1rem;">
                    Performance chart will appear after your first trade executes.<br>
                    Bot is monitoring market and waiting for optimal entry signal.
                </div>
            </div>
        """, unsafe_allow_html=True)
        return
    
    df = pd.DataFrame(trades_data)
    if 'timestamp' in df.columns and 'profit_loss' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp')
        df['cumulative_pnl'] = df['profit_loss'].cumsum()
        
        fig = go.Figure()
        
        # Add cumulative P&L line
        fig.add_trace(go.Scatter(
            x=df['timestamp'],
            y=df['cumulative_pnl'],
            mode='lines+markers',
            name='Cumulative P&L',
            line=dict(color='#10b981', width=3),
            marker=dict(size=8, color='#10b981'),
            fill='tozeroy',
            fillcolor='rgba(16, 185, 129, 0.1)'
        ))
        
        # Add zero line
        fig.add_hline(y=0, line_dash="dash", line_color="rgba(255,255,255,0.3)")
        
        fig.update_layout(
            title="Cumulative Performance",
            xaxis_title="Date",
            yaxis_title="Profit/Loss ($)",
            template="plotly_dark",
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white'),
            hovermode='x unified',
            showlegend=False
        )
        
        st.plotly_chart(fig, width='stretch')


def render_signals_table(signals_data: Dict):
    """Render signals and alerts with pagination"""
    
    # Tabs for Signals and Alerts
    signal_tab, alert_tab = st.tabs(["📊 Current Signals", "🔔 Alert History"])
    
    with signal_tab:
        if not signals_data or not signals_data.get('signals'):
            st.markdown("""
                <div class="metric-card" style="text-align: center; padding: 3rem;">
                    <div style="font-size: 3rem; margin-bottom: 1rem;">🔍</div>
                    <div class="metric-label">Monitoring Market</div>
                    <div style="color: rgba(255,255,255,0.6); margin-top: 1rem;">
                        AI is analyzing market data every 30 seconds.<br>
                        Signals will appear when conditions align.
                    </div>
                </div>
            """, unsafe_allow_html=True)
        else:
            signals = signals_data['signals']
            df = pd.DataFrame(signals)
            
            # Format the display
            if not df.empty:
                # Add signal badges
                def format_signal(signal_type):
                    if signal_type == 'BUY':
                        return '🟢 BUY'
                    elif signal_type == 'SELL':
                        return '🔴 SELL'
                    else:
                        return '⚪ HOLD'
                
                df['Signal'] = df['signal_type'].apply(format_signal)
                df['Price'] = df['price'].apply(lambda x: f"${x:,.2f}")
                df['RSI'] = df['rsi'].apply(lambda x: f"{x:.1f}" if pd.notna(x) else 'N/A')
                
                # Display table
                display_df = df[['symbol', 'Signal', 'Price', 'RSI', 'trend']].rename(columns={
                    'symbol': 'Symbol',
                    'trend': 'Trend'
                })
                
                st.dataframe(display_df, width='stretch', hide_index=True)
    
    with alert_tab:
        render_alerts_history()


def render_alerts_history():
    """Render alert history with pagination and filtering"""
    
    # Filters
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        alert_type_filter = st.selectbox(
            "Alert Type",
            ["All", "SIGNAL_CHANGE", "TRADE_EXECUTED", "STOP_LOSS_HIT", "TAKE_PROFIT_HIT"],
            index=0
        )
    
    with col2:
        symbol_filter = st.selectbox(
            "Symbol",
            ["All", "BTCUSDT", "ETHUSDT", "SOLUSDT"],
            index=0
        )
    
    with col3:
        time_filter = st.selectbox(
            "Time Range",
            ["All Time", "Last 24 Hours", "Last 7 Days", "Last 30 Days"],
            index=1
        )
    
    with col4:
        show_unread = st.checkbox("Unread Only", value=False, key="alerts_unread_only")
    
    # Convert time filter to hours
    time_hours_map = {
        "Last 24 Hours": 24,
        "Last 7 Days": 168,
        "Last 30 Days": 720,
        "All Time": None
    }
    hours = time_hours_map.get(time_filter)
    
    # Pagination state
    if 'alert_page' not in st.session_state:
        st.session_state.alert_page = 0
    
    page = st.session_state.alert_page
    limit = 20
    offset = page * limit
    
    # Fetch alerts from API
    try:
        params = {
            'limit': limit,
            'offset': offset,
            'unread_only': show_unread
        }
        
        if alert_type_filter != "All":
            params['alert_type'] = alert_type_filter
        
        if symbol_filter != "All":
            params['symbol'] = symbol_filter
        
        if hours:
            params['hours'] = hours
        
        # Get API URL from session state (set in main())
        api_url = st.session_state.get('api_url', 'http://localhost:9000')
        response = requests.get(f'{api_url}/api/alerts', params=params, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            alerts = data.get('alerts', [])
            stats = data.get('stats', {})
            
            # Show stats
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Alerts", stats.get('total', 0))
            
            with col2:
                st.metric("Unread", stats.get('unread', 0))
            
            with col3:
                st.metric("Last 24h", stats.get('recent_24h', 0))
            
            with col4:
                if st.button("Mark All Read"):
                    try:
                        mark_params = {}
                        if symbol_filter != "All":
                            mark_params['symbol'] = symbol_filter
                        api_url = st.session_state.get('api_url', 'http://localhost:9000')
                        requests.post(f'{api_url}/api/alerts/mark-all-read', params=mark_params)
                        st.success("All alerts marked as read")
                        st.rerun()
                    except:
                        st.error("Failed to mark alerts as read")
            
            st.markdown("---")
            
            # Display alerts
            if not alerts:
                st.info("No alerts found with the selected filters")
            else:
                for alert in alerts:
                    priority_color = {
                        'INFO': '#2196F3',
                        'WARNING': '#FF9800',
                        'CRITICAL': '#ef5350'
                    }.get(alert.get('priority', 'INFO'), '#2196F3')
                    
                    read_indicator = "" if alert.get('read') else "🔴 "
                    
                    timestamp_str = datetime.fromisoformat(alert['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
                    
                    st.markdown(f"""
                        <div class="metric-card" style="border-left: 4px solid {priority_color}; margin-bottom: 0.5rem;">
                            <div style="display: flex; justify-content: space-between; align-items: start;">
                                <div>
                                    <div style="color: rgba(255,255,255,0.7); font-size: 0.8rem; margin-bottom: 0.3rem;">
                                        {read_indicator}{alert['symbol']} • {alert['alert_type']} • {timestamp_str}
                                    </div>
                                    <div style="color: white; font-size: 1rem;">
                                        {alert['message']}
                                    </div>
                                </div>
                                <div style="padding: 0.2rem 0.6rem; background: {priority_color}; border-radius: 4px; font-size: 0.7rem;">
                                    {alert['priority']}
                                </div>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                
                # Pagination controls
                st.markdown("---")
                col1, col2, col3 = st.columns([1, 2, 1])
                
                with col1:
                    if st.button("← Previous", disabled=(page == 0)):
                        st.session_state.alert_page -= 1
                        st.rerun()
                
                with col2:
                    st.markdown(f"<div style='text-align: center;'>Page {page + 1}</div>", unsafe_allow_html=True)
                
                with col3:
                    has_more = data.get('pagination', {}).get('has_more', False)
                    if st.button("Next →", disabled=not has_more):
                        st.session_state.alert_page += 1
                        st.rerun()
        
        else:
            st.error("Failed to fetch alerts from API")

    except requests.exceptions.Timeout:
        st.warning("⏱️ Alert loading timed out. The backend may be processing a large number of alerts. Try refreshing the page.")
    except requests.exceptions.ConnectionError:
        st.error("❌ Cannot connect to backend API. Check your connection.")
    except Exception as e:
        st.error(f"❌ Error loading alerts: {str(e)}")


def render_price_charts(api: 'APIClient'):
    """Render TradingView-style professional charts with technical indicators"""
    from advanced_charts import AdvancedChart, TechnicalIndicators, fetch_chart_data, fetch_trades
    
    # Symbol selector
    symbol_options = {
        'BTC/USDT': 'BTCUSDT',
        'ETH/USDT': 'ETHUSDT',
        'SOL/USDT': 'SOLUSDT'
    }
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        selected_display = st.selectbox(
            "Select Symbol",
            options=list(symbol_options.keys()),
            index=0
        )
    
    with col3:
        auto_refresh = st.checkbox("Auto-refresh (30s)", value=False, key="price_charts_auto_refresh")
        if auto_refresh:
            st.rerun()
    
    symbol = symbol_options[selected_display]
    
    # Fetch data
    df = fetch_chart_data(symbol, limit=200)

    # Show progress if less than minimum candles
    candle_count = len(df)
    min_candles = 20  # Reduced from 50 for faster display

    if df.empty or candle_count < min_candles:
        progress_pct = (candle_count / min_candles) * 100 if candle_count > 0 else 0
        st.markdown(f"""
            <div class="metric-card" style="text-align: center; padding: 3rem;">
                <div style="font-size: 3rem; margin-bottom: 1rem;">⏳</div>
                <div class="metric-label">Building Price History</div>
                <div style="color: rgba(255,255,255,0.6); margin-top: 1rem;">
                    System is accumulating candle data from Binance.US<br>
                    <strong>{candle_count} / {min_candles} candles collected</strong> ({progress_pct:.0f}%)<br>
                    Chart will appear in ~{(min_candles - candle_count) * 5} minutes
                </div>
            </div>
        """, unsafe_allow_html=True)
        return
    
    # Initialize chart engine
    chart_engine = AdvancedChart()
    indicators = TechnicalIndicators()
    
    # --- CONTROL PANEL ---
    st.markdown("### 📊 Technical Analysis Controls")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("**Moving Averages**")
        show_sma = st.checkbox("SMA", value=True, key="indicator_sma")
        show_ema = st.checkbox("EMA", value=False, key="indicator_ema")
        
    with col2:
        st.markdown("**Bands & Volume**")
        show_bb = st.checkbox("Bollinger Bands", value=False, key="indicator_bb")
        show_vwap = st.checkbox("VWAP", value=False, key="indicator_vwap")
        
    with col3:
        st.markdown("**Oscillators**")
        show_rsi = st.checkbox("RSI", value=True, key="indicator_rsi")
        show_macd = st.checkbox("MACD", value=True, key="indicator_macd")
        
    with col4:
        st.markdown("**Advanced**")
        show_stoch = st.checkbox("Stochastic", value=False, key="indicator_stoch")
        show_volume_profile = st.checkbox("Volume Profile", value=False, key="indicator_volume_profile")
    
    st.markdown("---")
    
    # --- TECHNICAL SUMMARY ---
    st.markdown("### 📈 Technical Summary")
    
    # Calculate key indicators for summary
    latest = df.iloc[-1]
    rsi = indicators.calculate_rsi(df['close']).iloc[-1]
    sma20 = indicators.calculate_sma(df['close'], 20).iloc[-1]
    sma50 = indicators.calculate_sma(df['close'], 50).iloc[-1] if len(df) >= 50 else None
    
    # Determine trend
    if sma50 is not None:
        if latest['close'] > sma20 > sma50:
            trend = "🟢 Strong Uptrend"
            trend_color = "#26a69a"
        elif latest['close'] > sma20:
            trend = "🔵 Uptrend"
            trend_color = "#2196F3"
        elif latest['close'] < sma20 < sma50:
            trend = "🔴 Strong Downtrend"
            trend_color = "#ef5350"
        elif latest['close'] < sma20:
            trend = "🟠 Downtrend"
            trend_color = "#FF9800"
        else:
            trend = "⚪ Sideways"
            trend_color = "#9E9E9E"
    else:
        trend = "⚪ Insufficient Data"
        trend_color = "#9E9E9E"
    
    # RSI status
    if rsi > 70:
        rsi_status = "🔴 Overbought"
        rsi_color = "#ef5350"
    elif rsi < 30:
        rsi_status = "🟢 Oversold"
        rsi_color = "#26a69a"
    else:
        rsi_status = "🔵 Neutral"
        rsi_color = "#2196F3"
    
    # Price vs SMA20
    price_dist = ((latest['close'] - sma20) / sma20 * 100)
    if price_dist > 5:
        price_status = f"🔴 +{price_dist:.1f}% above SMA20"
        price_color = "#ef5350"
    elif price_dist < -5:
        price_status = f"🟢 {price_dist:.1f}% below SMA20"
        price_color = "#26a69a"
    else:
        price_status = f"🔵 {price_dist:+.1f}% from SMA20"
        price_color = "#2196F3"
    
    # Display summary cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
            <div class="indicator-card">
                <div class="indicator-label">TREND</div>
                <div class="indicator-value" style="color: {trend_color};">
                    {trend}
                </div>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
            <div class="indicator-card">
                <div class="indicator-label">RSI (14)</div>
                <div class="indicator-value" style="color: {rsi_color};">
                    {rsi:.1f} - {rsi_status}
                </div>
            </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
            <div class="indicator-card">
                <div class="indicator-label">PRICE vs SMA20</div>
                <div class="indicator-value" style="color: {price_color};">
                    {price_status}
                </div>
            </div>
        """, unsafe_allow_html=True)
    
    with col4:
        price_change = latest['close'] - df.iloc[0]['close']
        price_change_pct = (price_change / df.iloc[0]['close'] * 100)
        change_color = '#26a69a' if price_change >= 0 else '#ef5350'
        
        st.markdown(f"""
            <div class="indicator-card">
                <div class="indicator-label">PERIOD CHANGE</div>
                <div class="indicator-value" style="color: {change_color};">
                    {'+' if price_change >= 0 else ''}{price_change_pct:.2f}%
                </div>
            </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # --- MAIN CHART ---
    trades = fetch_trades(symbol)
    
    main_chart = chart_engine.create_main_chart(
        df,
        show_sma=show_sma,
        show_ema=show_ema,
        show_bb=show_bb,
        show_vwap=show_vwap,
        trades=trades,
        title=f"{selected_display} - Professional Analysis"
    )
    
    if main_chart:
        st.plotly_chart(main_chart, width='stretch')
    
    # --- OSCILLATORS ---
    if show_rsi or show_macd or show_stoch or show_volume_profile:
        st.markdown("### 📉 Oscillators & Indicators")
        
        # Two-column layout for oscillators
        col1, col2 = st.columns(2)
        
        with col1:
            if show_rsi:
                rsi_chart = chart_engine.create_rsi_chart(df)
                if rsi_chart:
                    st.plotly_chart(rsi_chart, width='stretch')
            
            if show_stoch:
                stoch_chart = chart_engine.create_stochastic_chart(df)
                if stoch_chart:
                    st.plotly_chart(stoch_chart, width='stretch')
        
        with col2:
            if show_macd:
                macd_chart = chart_engine.create_macd_chart(df)
                if macd_chart:
                    st.plotly_chart(macd_chart, width='stretch')
            
            if show_volume_profile:
                volume_profile = chart_engine.create_volume_profile(df)
                if volume_profile:
                    st.plotly_chart(volume_profile, width='stretch')
    
    # --- PRICE INFO CARDS ---
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)
    
    price_change_24h = latest['close'] - latest['open']
    price_change_pct_24h = (price_change_24h / latest['open'] * 100) if latest['open'] > 0 else 0
    change_color_24h = '#26a69a' if price_change_24h >= 0 else '#ef5350'
    
    with col1:
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Last Price</div>
                <div class="metric-value">${latest['close']:,.2f}</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">24h Change</div>
                <div class="metric-value" style="color: {change_color_24h};">
                    {'+' if price_change_24h >= 0 else ''}{price_change_pct_24h:.2f}%
                </div>
            </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">High</div>
                <div class="metric-value">${latest['high']:,.2f}</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Low</div>
                <div class="metric-value">${latest['low']:,.2f}</div>
            </div>
        """, unsafe_allow_html=True)


def render_trades_table(trades_data: list):
    """Render recent trades"""
    if not trades_data:
        st.markdown("""
            <div class="metric-card" style="text-align: center; padding: 3rem;">
                <div style="font-size: 3rem; margin-bottom: 1rem;">📋</div>
                <div class="metric-label">No Trades Yet</div>
                <div style="color: rgba(255,255,255,0.6); margin-top: 1rem;">
                    Trade history will appear here after first execution.<br>
                    Expected: 3-7 days for first trade (high-probability setups only).
                </div>
            </div>
        """, unsafe_allow_html=True)
        return
    
    df = pd.DataFrame(trades_data)
    
    if not df.empty:
        # Format columns based on available data
        df['Entry'] = df['price'].apply(lambda x: f"${x:,.2f}")
        df['Exit'] = 'Open'  # All current trades are open positions
        df['P&L'] = df['profit_loss'].apply(lambda x: f"${x:,.2f}" if pd.notna(x) else '$0.00')
        df['P&L %'] = '0.00%'  # No profit/loss calculation for open positions
        
        # Select columns to display
        display_df = df[['symbol', 'side', 'Entry', 'Exit', 'P&L', 'P&L %', 'timestamp']].rename(columns={
            'symbol': 'Symbol',
            'side': 'Side',
            'timestamp': 'Time'
        })
        
        st.dataframe(display_df.tail(20), width='stretch', hide_index=True)


def check_new_alerts():
    """Check for new unread alerts and show notifications"""
    try:
        # Initialize session state for last alert check
        if 'last_alert_check' not in st.session_state:
            st.session_state.last_alert_check = datetime.now()
            st.session_state.shown_alert_ids = set()
        
        # Check for new alerts (last 5 minutes)
        api_url = st.session_state.get('api_url', 'http://localhost:9000')
        response = requests.get(
            f'{api_url}/api/alerts',
            params={'limit': 10, 'unread_only': True, 'hours': 1},
            timeout=3
        )
        
        if response.status_code == 200:
            data = response.json()
            alerts = data.get('alerts', [])
            
            # Show new alerts as toasts
            for alert in alerts:
                alert_id = alert['id']
                if alert_id not in st.session_state.shown_alert_ids:
                    # Determine icon based on alert type
                    icon_map = {
                        'SIGNAL_CHANGE': '📊',
                        'TRADE_EXECUTED': '💹',
                        'STOP_LOSS_HIT': '🛑',
                        'TAKE_PROFIT_HIT': '🎯',
                        'WIN_RATE_WARNING': '⚠️',
                        'HIGH_WIN_STREAK': '🔥'
                    }
                    icon = icon_map.get(alert.get('alert_type'), '🔔')
                    
                    # Show toast notification
                    st.toast(f"{icon} {alert['message']}", icon=icon)
                    
                    # Mark as shown
                    st.session_state.shown_alert_ids.add(alert_id)
            
            st.session_state.last_alert_check = datetime.now()
    
    except Exception:
        # Silently fail on connection errors (expected when API is not available)
        pass


def main():
    """Main dashboard"""
    api = APIClient()
    
    # Store API URL in session state for other functions to use
    st.session_state.api_url = api.base_url
    
    # Check for new alerts
    check_new_alerts()
    
    # Render header
    render_header()
    
    # Sidebar controls
    with st.sidebar:
        st.markdown("### 🎛️ Dashboard Controls")
        
        # Engine control buttons
        status_check = api.get('/api/status')
        is_running = bool(status_check and status_check.get('trading_engine') == 'active')
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("▶️ Start", disabled=is_running):
                result = api.post('/api/trading/start')
                if result:
                    st.success("Engine started!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Failed to start engine")
        
        with col2:
            if st.button("⏸️ Stop", disabled=not is_running):
                result = api.post('/api/trading/stop')
                if result:
                    st.success("Engine stopped!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Failed to stop engine")
        
        st.markdown("---")
        
        if st.button("🔄 Refresh Data"):
            st.rerun()
        
        auto_refresh = st.checkbox("Auto-refresh (30s)", value=False, key="portfolio_auto_refresh")
        
        if auto_refresh:
            time.sleep(30)
            st.rerun()
        
        st.markdown("---")
        st.markdown("### 📊 System Info")
        st.caption(f"API: {api.base_url}")
        st.caption(f"Updated: {datetime.now().strftime('%H:%M:%S')}")
    
    # Fetch data
    status_data = api.get('/api/status')
    portfolio_data = api.get('/api/portfolio')
    signals_data = api.get('/api/signals')
    trades_data = api.get('/api/trades?limit=50')
    
    # Status cards
    render_status_card(status_data)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Portfolio metrics
    render_portfolio_metrics(portfolio_data)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Overview", "📈 Charts", "💹 Signals", "📋 Trades", "💼 Portfolio"])
    
    with tab1:
        st.markdown("### 📈 Performance Overview")
        
        # Show monitoring status if no trades
        if not trades_data:
            st.markdown("""
                <div class="metric-card" style="margin-bottom: 2rem;">
                    <div style="display: flex; align-items: center; gap: 1rem;">
                        <div style="font-size: 2rem;">🎯</div>
                        <div>
                            <div class="metric-label">System Status</div>
                            <div style="color: white; font-size: 1.2rem; margin-top: 0.5rem;">
                                ✅ Bot is actively monitoring market (every 30s)
                            </div>
                            <div style="color: rgba(255,255,255,0.6); margin-top: 0.5rem; font-size: 0.9rem;">
                                Waiting for: Technical (40%) + LSTM (30%) + Sentiment (30%) alignment > 0.6
                            </div>
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
        
        render_performance_chart(trades_data if trades_data else [])
        
        col1, col2 = st.columns(2)
        
        with col1:
            if trades_data:
                df = pd.DataFrame(trades_data)
                winning = len(df[df['profit_loss'] > 0])
                total = len(df)
                win_rate = (winning / total * 100) if total > 0 else 0
                
                st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">Win Rate</div>
                        <div class="metric-value">{win_rate:.1f}%</div>
                        <div class="metric-delta">({winning}/{total} trades)</div>
                    </div>
                """, unsafe_allow_html=True)
        
        with col2:
            if trades_data:
                df = pd.DataFrame(trades_data)
                total_profit = df['profit_loss'].sum()
                
                delta_class = 'positive' if total_profit >= 0 else 'negative'
                st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">Total Realized P&L</div>
                        <div class="metric-value">${total_profit:,.2f}</div>
                    </div>
                """, unsafe_allow_html=True)
    
    with tab2:
        st.markdown("### 📈 Live Price Charts")
        render_price_charts(api)
    
    with tab3:
        st.markdown("### 💹 Current Signals")
        render_signals_table(signals_data)
    
    with tab4:
        st.markdown("### 📋 Trade History")
        render_trades_table(trades_data if trades_data else [])
    
    with tab5:
        st.markdown("### 💼 Portfolio Details")

        if portfolio_data:
            # Portfolio Summary Cards
            col1, col2, col3, col4 = st.columns(4)

            total_value = portfolio_data.get('total_value', 0)
            cash = portfolio_data.get('cash', portfolio_data.get('cash_balance', 0))
            positions_value = total_value - cash
            num_positions = len(portfolio_data.get('positions', []))

            with col1:
                st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">Total Value</div>
                        <div class="metric-value">${total_value:,.2f}</div>
                    </div>
                """, unsafe_allow_html=True)

            with col2:
                st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">Cash Balance</div>
                        <div class="metric-value">${cash:,.2f}</div>
                    </div>
                """, unsafe_allow_html=True)

            with col3:
                st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">Positions Value</div>
                        <div class="metric-value">${positions_value:,.2f}</div>
                    </div>
                """, unsafe_allow_html=True)

            with col4:
                st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">Open Positions</div>
                        <div class="metric-value">{num_positions}</div>
                    </div>
                """, unsafe_allow_html=True)

            st.markdown("---")

            # Portfolio Controls
            st.markdown("### ⚙️ Portfolio Controls")

            col1, col2 = st.columns([2, 1])

            with col1:
                new_balance = st.number_input(
                    "Adjust Cash Balance (for testing)",
                    min_value=0.0,
                    max_value=1000000.0,
                    value=float(cash),
                    step=1000.0,
                    help="Adjust your paper trading cash balance for testing different scenarios"
                )

            with col2:
                st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)
                if st.button("💰 Update Balance", use_container_width=True):
                    result = api.post('/api/portfolio/adjust-cash', {'new_balance': new_balance})
                    if result:
                        st.success(f"✅ Cash balance updated to ${new_balance:,.2f}")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("❌ Failed to update balance")

            st.markdown("---")

            # Open Positions Table
            st.markdown("### 📊 Open Positions")
            if portfolio_data.get('positions'):
                positions = portfolio_data['positions']

                # Format positions for display
                positions_display = []
                for pos in positions:
                    positions_display.append({
                        'Symbol': pos.get('symbol', 'N/A'),
                        'Amount': f"{pos.get('amount', 0):.6f}",
                        'Entry Price': f"${pos.get('entry_price', 0):.2f}",
                        'Current Price': f"${pos.get('current_price', 0):.2f}",
                        'Value': f"${pos.get('amount', 0) * pos.get('current_price', 0):,.2f}",
                        'Unrealized P&L': f"${pos.get('unrealized_pnl', 0):,.2f}",
                        'P&L %': f"{((pos.get('current_price', 0) - pos.get('entry_price', 1)) / pos.get('entry_price', 1) * 100):.2f}%"
                    })

                positions_df = pd.DataFrame(positions_display)
                st.dataframe(positions_df, use_container_width=True, hide_index=True)
            else:
                st.markdown("""
                    <div class="metric-card" style="text-align: center; padding: 3rem;">
                        <div style="font-size: 3rem; margin-bottom: 1rem;">💼</div>
                        <div class="metric-label">No Open Positions</div>
                        <div style="color: rgba(255,255,255,0.6); margin-top: 1rem;">
                            All cash available for trading.<br>
                            Bot is monitoring for high-probability entry signals.
                        </div>
                    </div>
                """, unsafe_allow_html=True)
        else:
            st.info("📊 Portfolio data requires backend API connection")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(f"❌ Application Error: {str(e)}")
        st.info("💡 **Troubleshooting:**")
        st.markdown("""
        - Check that Streamlit secrets are configured
        - Verify API URL is accessible
        - Check browser console for errors
        """)
        logger.exception("Application crashed")
