"""
Live Trading Engine - 5-MINUTE TIMEFRAME
High-frequency trading with Week1Refined5m strategy and real-time alerts
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np
from dataclasses import dataclass
from enum import Enum

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from trading.exchange_integration import exchange_manager, initialize_exchanges
from strategies.technical_indicators import TechnicalIndicators
from strategies.week1_refined_5m import Week1Refined5mStrategy
from data.candle_aggregator import get_candle_aggregator, start_candle_aggregator
from trading.signal_monitor import get_signal_monitor
from trading.paper_trading_monitor import PaperTradingMonitor
from data.database import get_db
from data.models import Trade as DBTrade

logger = logging.getLogger(__name__)

class OrderStatus(Enum):
    PENDING = "pending"
    FILLED = "filled"
    CANCELED = "canceled"
    FAILED = "failed"

@dataclass
class Position:
    symbol: str
    amount: float
    entry_price: float
    entry_time: datetime
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    current_price: float = 0.0
    unrealized_pnl: float = 0.0

@dataclass
class Trade:
    id: str
    symbol: str
    side: str  # 'BUY' or 'SELL'
    amount: float
    price: float
    timestamp: datetime
    strategy: str
    status: OrderStatus = OrderStatus.PENDING
    order_id: Optional[str] = None

class PortfolioManager:
    """Manages portfolio positions and risk"""

    def __init__(self, initial_balance: float = 10000.0):
        self.initial_balance = initial_balance
        self.cash_balance = initial_balance
        self.positions: Dict[str, Position] = {}
        self.trades: List[Trade] = []
        self.max_position_size = 0.07  # Max 7% per position (REDUCED FROM 30% - Critical Risk Management)
        self.stop_loss_pct = 0.15  # 15% stop loss
        self.take_profit_pct = 0.30  # 30% take profit

    def get_portfolio_value(self) -> float:
        """Calculate total portfolio value"""
        total_value = self.cash_balance

        for position in self.positions.values():
            position_value = position.amount * position.current_price
            total_value += position_value

        return total_value

    def get_position_size(self, symbol: str, current_price: float) -> float:
        """Calculate position size based on risk management"""
        portfolio_value = self.get_portfolio_value()
        max_investment = portfolio_value * self.max_position_size

        # Use available cash or max investment, whichever is smaller
        available_cash = min(self.cash_balance * 0.95, max_investment)  # Leave 5% cash buffer

        if available_cash <= 0:
            return 0.0

        return available_cash / current_price
    
    def calculate_dynamic_stop_loss(self, symbol: str, entry_price: float, market_data: dict = None) -> float:
        """Calculate dynamic stop loss based on market volatility and conditions"""
        base_sl_pct = self.stop_loss_pct  # 15% base
        
        # If we have market data, adjust based on volatility
        if market_data and 'volatility' in market_data:
            volatility = market_data['volatility']
            # Higher volatility = wider stop loss (up to 20%), lower volatility = tighter (down to 10%)
            if volatility > 0.05:  # High volatility (>5%)
                sl_pct = min(base_sl_pct * 1.33, 0.20)  # Max 20% SL
            elif volatility < 0.02:  # Low volatility (<2%)  
                sl_pct = max(base_sl_pct * 0.67, 0.08)  # Min 8% SL
            else:
                sl_pct = base_sl_pct
        else:
            # Without volatility data, use slightly tighter SL for smaller positions
            sl_pct = base_sl_pct * 0.8  # 12% instead of 15% with smaller position sizes
            
        return entry_price * (1 - sl_pct)

    def can_open_position(self, symbol: str) -> bool:
        """Check if we can open a new position"""
        return (symbol not in self.positions and
                self.cash_balance > self.initial_balance * 0.1)  # Keep 10% cash minimum

    def open_position(self, symbol: str, amount: float, price: float) -> bool:
        """Open a new position"""
        if not self.can_open_position(symbol):
            return False

        cost = amount * price
        if cost > self.cash_balance:
            return False

        self.positions[symbol] = Position(
            symbol=symbol,
            amount=amount,
            entry_price=price,
            entry_time=datetime.now(),
            stop_loss=self.calculate_dynamic_stop_loss(symbol, price),  # Dynamic SL based on volatility
            take_profit=price * (1 + self.take_profit_pct),  # 30% above entry
            current_price=price
        )

        self.cash_balance -= cost
        logger.info(f"Opened position: {amount:.6f} {symbol} at ${price:.2f}, SL: ${self.positions[symbol].stop_loss:.2f}, TP: ${self.positions[symbol].take_profit:.2f}")
        return True

    def close_position(self, symbol: str, price: float) -> Optional[float]:
        """Close a position and return P&L"""
        if symbol not in self.positions:
            return None

        position = self.positions[symbol]
        proceeds = position.amount * price
        pnl = proceeds - (position.amount * position.entry_price)

        self.cash_balance += proceeds
        del self.positions[symbol]

        logger.info(f"Closed position: {position.amount:.6f} {symbol} at ${price:.2f}, P&L: ${pnl:.2f}")
        return pnl

    def update_positions(self, prices: Dict[str, float]):
        """Update current prices and unrealized P&L"""
        for symbol, position in self.positions.items():
            if symbol in prices:
                position.current_price = prices[symbol]
                position.unrealized_pnl = (position.current_price - position.entry_price) * position.amount

    def check_stop_losses(self, prices: Dict[str, float]) -> List[str]:
        """Check for stop loss triggers"""
        stop_loss_triggers = []

        for symbol, position in self.positions.items():
            if symbol in prices and position.stop_loss:
                current_price = prices[symbol]
                if current_price <= position.stop_loss:
                    stop_loss_triggers.append(symbol)
                    logger.warning(f"Stop loss triggered for {symbol}: ${current_price:.2f} <= ${position.stop_loss:.2f}")

        return stop_loss_triggers

    def check_take_profits(self, prices: Dict[str, float]) -> List[str]:
        """Check for take profit triggers"""
        take_profit_triggers = []

        for symbol, position in self.positions.items():
            if symbol in prices and position.take_profit:
                current_price = prices[symbol]
                if current_price >= position.take_profit:
                    take_profit_triggers.append(symbol)
                    logger.info(f"Take profit triggered for {symbol}: ${current_price:.2f} >= ${position.take_profit:.2f}")

        return take_profit_triggers

class LiveTradingEngine5m:
    """
    Live Trading Engine - 5-Minute Timeframe

    Features:
    - Week1Refined5m strategy (65-75% win rate)
    - Real-time 5-minute candle aggregation
    - Signal monitoring and alerts
    - Paper trading monitor integration
    - Expected: 8-12 trades per day
    """

    def __init__(self, symbols: List[str] = None, paper_trading: bool = True, use_ai: bool = False):
        self.symbols = symbols or ['BTCUSDT', 'ETHUSDT', 'SOLUSDT']
        self.portfolio = PortfolioManager()

        # Strategy selection: AI-enhanced or base strategy
        if use_ai:
            try:
                from strategies.ai_enhanced_strategy import AIEnhancedStrategy
                self.strategy = AIEnhancedStrategy()
                logger.info(f"✨ AI-ENHANCED Strategy: {self.strategy.name} (Technical 40% + LSTM 30% + Sentiment 30%)")
            except ImportError as e:
                logger.warning(f"AI Strategy not available: {e}. Falling back to base strategy.")
                self.strategy = Week1Refined5mStrategy()
                logger.info(f"Strategy: {self.strategy.name} (5-minute timeframe)")
        else:
            # Use 5-minute optimized strategy
            self.strategy = Week1Refined5mStrategy()
            logger.info(f"Strategy: {self.strategy.name} (5-minute timeframe)")

        self.indicators = TechnicalIndicators()

        # Initialize exchanges
        initialize_exchanges()
        self.exchange = exchange_manager.get_exchange('binance')

        # Paper trading mode - NO REAL MONEY
        self.paper_trading = paper_trading

        self.running = False
        self.update_interval = 30  # Check every 30 seconds (more frequent for 5m)
        self.last_signals = {}

        # Performance tracking
        self.start_time = None
        self.total_trades = 0
        self.winning_trades = 0
        self.paper_trades = []

        # Monitoring and alerts
        self.signal_monitor = get_signal_monitor()
        self.paper_monitor = PaperTradingMonitor()

        # Candle aggregator (will be initialized on start)
        self.candle_aggregator = None

    def save_trade_to_database(self, symbol: str, side: str, amount: float, price: float, strategy: str = "Week1Refined5m"):
        """Save trade to database for dashboard display"""
        try:
            db = next(get_db())
            
            # Create database trade record
            db_trade = DBTrade(
                symbol=symbol,
                side=side.lower(),  # Database expects lowercase
                quantity=amount,
                price=price,
                timestamp=datetime.now(),
                strategy=strategy,
                profit_loss=0  # Will be calculated when position is closed
            )
            
            db.add(db_trade)
            db.commit()
            db.close()
            
            logger.info(f"💾 Trade saved to database: {side} {amount:.6f} {symbol} @ ${price:.2f}")
            
        except Exception as e:
            logger.error(f"Failed to save trade to database: {e}")
            if 'db' in locals():
                db.rollback()
                db.close()

    async def start(self):
        """Start the live trading engine"""
        if self.running:
            logger.warning("Trading engine is already running")
            return

        self.running = True
        self.start_time = datetime.now()

        mode = "📄 PAPER TRADING (5m)" if self.paper_trading else "💰 LIVE TRADING (5m)"
        logger.info(f"🚀 {mode} Engine Started")
        logger.info(f"Symbols: {self.symbols}")
        logger.info(f"Strategy: {self.strategy.name}")
        logger.info(f"Timeframe: 5 minutes")
        logger.info(f"Update Interval: {self.update_interval}s")
        logger.info(f"Initial Balance: ${self.portfolio.initial_balance:,.2f}")
        logger.info(f"Expected Trade Frequency: 8-12 per day")

        if self.paper_trading:
            logger.info("⚠️  PAPER TRADING MODE - NO REAL MONEY AT RISK")
        else:
            logger.warning("💰 LIVE TRADING MODE - REAL MONEY AT RISK!")

        # Initialize candle aggregator
        try:
            self.candle_aggregator = await start_candle_aggregator(
                symbols=self.symbols,
                timeframe_minutes=5
            )
            logger.info("5-minute candle aggregator started")
        except Exception as e:
            logger.error(f"Failed to start candle aggregator: {e}")
            self.running = False
            return

        try:
            while self.running:
                await self.trading_cycle()
                await asyncio.sleep(self.update_interval)

        except Exception as e:
            logger.error(f"Trading engine error: {e}", exc_info=True)
        finally:
            self.running = False
            logger.info("Trading engine stopped")

    async def stop(self):
        """Stop the trading engine"""
        self.running = False
        logger.info("Stopping trading engine...")

    async def trading_cycle(self):
        """Execute one trading cycle"""
        try:
            # Get current prices
            current_prices = {}
            for symbol in self.symbols:
                ticker = await self.exchange.get_ticker(symbol)
                if ticker and 'price' in ticker:
                    current_prices[symbol] = ticker['price']

            if not current_prices:
                logger.warning("No price data available")
                return

            # Update portfolio with current prices
            self.portfolio.update_positions(current_prices)

            # Check stop losses
            stop_loss_triggers = self.portfolio.check_stop_losses(current_prices)
            for symbol in stop_loss_triggers:
                await self.execute_sell(symbol, current_prices[symbol], "STOP_LOSS")

            # Check take profits
            take_profit_triggers = self.portfolio.check_take_profits(current_prices)
            for symbol in take_profit_triggers:
                await self.execute_sell(symbol, current_prices[symbol], "TAKE_PROFIT")

            # Generate signals for each symbol using 5m candles
            for symbol in self.symbols:
                if symbol in current_prices:
                    await self.process_symbol_5m(symbol, current_prices[symbol])

            # Log portfolio status periodically
            await self.log_portfolio_status()

        except Exception as e:
            logger.error(f"Error in trading cycle: {e}", exc_info=True)

    async def process_symbol_5m(self, symbol: str, current_price: float):
        """Process trading signals for a symbol using 5-minute candles"""
        try:
            import pandas as pd  # Import pandas here to avoid scoping issues
            
            # Get 5-minute candles from aggregator
            if not self.candle_aggregator:
                logger.warning("Candle aggregator not initialized")
                return

            df = self.candle_aggregator.get_candles_as_dataframe(symbol, limit=300)

            # Fallback to database if aggregator doesn't have enough candles yet
            if len(df) < 30:  # Reduced from 60 for testing
                logger.info(f"Aggregator has {len(df)} candles, fetching from database for {symbol}")
                try:
                    import os
                    from sqlalchemy import create_engine, desc
                    from sqlalchemy.orm import sessionmaker
                    from data.models import MarketData
                    from datetime import datetime, timedelta

                    db_url = os.getenv('DATABASE_URL')
                    if db_url:
                        engine = create_engine(db_url)
                        Session = sessionmaker(bind=engine)
                        session = Session()

                        # Get last 300 5-minute candles from database
                        db_symbol = symbol.replace('USDT', '/USDT')
                        cutoff = datetime.now() - timedelta(hours=25)

                        candles = session.query(MarketData).filter(
                            MarketData.symbol == db_symbol,
                            MarketData.timestamp >= cutoff
                        ).order_by(MarketData.timestamp).limit(300).all()

                        session.close()

                        if len(candles) >= 30:  # Reduced from 60 for testing
                            df = pd.DataFrame([{
                                'timestamp': c.timestamp,
                                'open': float(c.open_price),
                                'high': float(c.high_price),
                                'low': float(c.low_price),
                                'close': float(c.close_price),
                                'volume': float(c.volume)
                            } for c in candles])
                            logger.info(f"Loaded {len(df)} candles from database for {symbol}")
                        else:
                            logger.debug(f"Not enough candles in database for {symbol}: {len(candles)}/30")
                            return
                    else:
                        logger.debug(f"No database URL, skipping {symbol}")
                        return
                except Exception as e:
                    logger.error(f"Error loading candles from database: {e}")
                    return

            # Still not enough candles
            if len(df) < 30:  # Reduced from 60 for testing
                logger.debug(f"Not enough 5m candles for {symbol}: {len(df)}/30")
                return

            # Normalize column names (candle_aggregator uses *_price, strategies expect standard names)
            if 'close_price' in df.columns:
                df = df.rename(columns={
                    'open_price': 'open',
                    'high_price': 'high',
                    'low_price': 'low',
                    'close_price': 'close'
                })

            # Generate signals
            signals = self.strategy.generate_signals(df, symbol=symbol.replace('USDT', ''))

            # Handle different return types
            if isinstance(signals, pd.DataFrame):
                # DataFrame with columns
                if len(signals) == 0:
                    return
                try:
                    latest_signal = signals.iloc[-1]['signal'] if 'signal' in signals.columns else signals.iloc[-1].iloc[0]
                except (IndexError, KeyError, TypeError) as e:
                    logger.error(f"Error extracting signal from DataFrame for {symbol}: {e}")
                    return
                rsi = signals.iloc[-1].get('rsi')
                ma_fast = signals.iloc[-1].get('ma_fast')
                ma_slow = signals.iloc[-1].get('ma_slow')
                htf_fast = signals.iloc[-1].get('htf_fast')
                htf_slow = signals.iloc[-1].get('htf_slow')
                
            elif isinstance(signals, pd.Series):
                # Series - just signal values, calculate indicators ourselves
                if len(signals) == 0:
                    return
                # Handle both scalar and series returns
                try:
                    # Check if it's a scalar value (happens when Series has one element and you access it)
                    if np.isscalar(signals):
                        latest_signal = float(signals)
                    elif hasattr(signals, 'iloc') and len(signals) > 0:
                        latest_signal = float(signals.iloc[-1])
                    elif hasattr(signals, 'values') and len(signals.values) > 0:
                        latest_signal = float(signals.values[-1])
                    else:
                        latest_signal = float(signals)
                except (IndexError, TypeError, AttributeError, ValueError) as e:
                    logger.error(f"Error extracting signal value for {symbol}: {e}, signals type: {type(signals)}, signals: {signals}")
                    return
                
                # Calculate indicators for monitoring - ensure column names exist
                if 'close' not in df.columns:
                    logger.error(f"Missing 'close' column for {symbol}, columns: {df.columns.tolist()}")
                    return
                    
                rsi = self.indicators.rsi(df['close'], window=14).iloc[-1] if len(df) >= 14 else None
                ma_fast = df['close'].rolling(window=8).mean().iloc[-1] if len(df) >= 8 else None
                ma_slow = df['close'].rolling(window=21).mean().iloc[-1] if len(df) >= 21 else None
                htf_fast = df['close'].rolling(window=20).mean().iloc[-1] if len(df) >= 20 else None
                htf_slow = df['close'].rolling(window=50).mean().iloc[-1] if len(df) >= 50 else None
            else:
                # Scalar or unknown type
                latest_signal = float(signals) if signals is not None else 0.0
                rsi = None
                ma_fast = None
                ma_slow = None
                htf_fast = None
                htf_slow = None

            # Determine trend
            if htf_fast is not None and htf_slow is not None:
                trend = "BULLISH" if htf_fast > htf_slow else "BEARISH" if htf_fast < htf_slow else "NEUTRAL"
            else:
                trend = "NEUTRAL"

            # Update signal monitor
            alert = self.signal_monitor.update_signal(
                symbol=symbol,
                signal=latest_signal,
                price=current_price,
                rsi=rsi,
                ma_fast=ma_fast,
                ma_slow=ma_slow,
                trend=trend
            )

            # Store previous signal to detect changes
            prev_signal = self.last_signals.get(symbol, 0.0)
            self.last_signals[symbol] = latest_signal

            # Execute trades based on signal changes
            if latest_signal > 0 and prev_signal <= 0:  # New buy signal
                rsi_str = f"{rsi:.1f}" if rsi is not None else 'N/A'
                logger.info(f"🟢 BUY SIGNAL detected for {symbol} @ ${current_price:.2f} (RSI: {rsi_str}, Trend: {trend})")
                await self.execute_buy(symbol, current_price)
            elif latest_signal < 0 and prev_signal >= 0:  # New sell signal
                logger.info(f"🔴 SELL SIGNAL detected for {symbol} @ ${current_price:.2f}")
                await self.execute_sell(symbol, current_price, "SIGNAL")

        except Exception as e:
            logger.error(f"Error processing {symbol}: {e}", exc_info=True)

    async def execute_buy(self, symbol: str, price: float):
        """Execute a buy order"""
        try:
            # Check if position can be opened
            can_open = self.portfolio.can_open_position(symbol)
            has_position = symbol in self.portfolio.positions
            cash_available = self.portfolio.cash_balance
            min_cash_required = self.portfolio.initial_balance * 0.1
            
            if not can_open:
                if has_position:
                    logger.info(f"⚠️  Cannot open position for {symbol}: position already exists")
                elif cash_available <= min_cash_required:
                    logger.warning(f"⚠️  Cannot open position for {symbol}: insufficient cash (${cash_available:.2f} / ${min_cash_required:.2f} min required)")
                else:
                    logger.info(f"⚠️  Cannot open position for {symbol}: other reason")
                return

            # Calculate position size
            amount = self.portfolio.get_position_size(symbol, price)
            position_value = amount * price
            
            if amount <= 0:
                logger.warning(f"⚠️  Position size too small for {symbol}: ${position_value:.2f}")
                return
            
            logger.info(f"💰 Executing BUY for {symbol}: {amount:.6f} @ ${price:.2f} (${position_value:.2f})")

            # Check if paper trading mode
            if self.paper_trading:
                # Simulate successful order in paper trading mode
                order_result = {
                    'order_id': f'paper_buy_{symbol}_{int(datetime.now().timestamp())}',
                    'status': 'filled',
                    'filled_amount': amount,
                    'filled_price': price
                }
                logger.info(f"📄 PAPER TRADE: Simulated BUY order for {symbol}")
            else:
                # Place real order
                order_result = await self.exchange.place_order(
                    symbol=symbol,
                    side='BUY',
                    amount=amount * price,  # Amount in USDT for market order
                    price=None  # Market order
                )

            if 'error' not in order_result:
                # Open position in portfolio
                self.portfolio.open_position(symbol, amount, price)

                # Record trade
                trade = Trade(
                    id=f"trade_{len(self.portfolio.trades) + 1}",
                    symbol=symbol,
                    side='BUY',
                    amount=amount,
                    price=price,
                    timestamp=datetime.now(),
                    strategy="Week1Refined5m",
                    status=OrderStatus.FILLED,
                    order_id=order_result.get('order_id')
                )
                self.portfolio.trades.append(trade)
                self.total_trades += 1

                # Log to signal monitor
                self.signal_monitor.log_trade_execution(symbol, 'BUY', price, amount)

                # Log to paper trading monitor
                self.paper_monitor.log_trade({
                    'timestamp': datetime.now(),
                    'symbol': symbol,
                    'side': 'BUY',
                    'entry_price': price,
                    'amount': amount
                })

                # Save trade to database for dashboard
                self.save_trade_to_database(symbol, 'BUY', amount, price)

                logger.info(f"✅ BUY EXECUTED: {amount:.6f} {symbol} at ${price:.2f}")
            else:
                logger.error(f"❌ Buy order failed for {symbol}: {order_result['error']}")

        except Exception as e:
            logger.error(f"Error executing buy for {symbol}: {e}", exc_info=True)

    async def execute_sell(self, symbol: str, price: float, reason: str = "SIGNAL"):
        """Execute a sell order"""
        try:
            if symbol not in self.portfolio.positions:
                logger.info(f"No position to sell for {symbol}")
                return

            position = self.portfolio.positions[symbol]

            # Check if paper trading mode
            if self.paper_trading:
                # Simulate successful order in paper trading mode
                order_result = {
                    'order_id': f'paper_sell_{symbol}_{int(datetime.now().timestamp())}',
                    'status': 'filled',
                    'filled_amount': position.amount,
                    'filled_price': price
                }
                logger.info(f"📄 PAPER TRADE: Simulated SELL order for {symbol}")
            else:
                # Place real sell order
                order_result = await self.exchange.place_order(
                    symbol=symbol,
                    side='SELL',
                    amount=position.amount,
                    price=None  # Market order
                )

            if 'error' not in order_result:
                # Calculate P&L
                pnl = self.portfolio.close_position(symbol, price)
                pnl_pct = ((price - position.entry_price) / position.entry_price) * 100

                # Record trade
                trade = Trade(
                    id=f"trade_{len(self.portfolio.trades) + 1}",
                    symbol=symbol,
                    side='SELL',
                    amount=position.amount,
                    price=price,
                    timestamp=datetime.now(),
                    strategy="Week1Refined5m",
                    status=OrderStatus.FILLED,
                    order_id=order_result.get('order_id')
                )
                self.portfolio.trades.append(trade)
                self.total_trades += 1

                # Update win/loss tracking
                if pnl_pct > 0:
                    self.winning_trades += 1

                # Log to signal monitor
                self.signal_monitor.log_trade_execution(symbol, 'SELL', price, position.amount, reason)

                if reason == "STOP_LOSS":
                    self.signal_monitor.log_stop_loss(symbol, position.entry_price, price, pnl_pct)
                elif reason == "TAKE_PROFIT":
                    self.signal_monitor.log_take_profit(symbol, position.entry_price, price, pnl_pct)

                # Log to paper trading monitor
                self.paper_monitor.log_trade({
                    'timestamp': datetime.now(),
                    'symbol': symbol,
                    'side': 'SELL',
                    'entry_price': position.entry_price,
                    'exit_price': price,
                    'amount': position.amount,
                    'pnl': pnl,
                    'pnl_pct': pnl_pct,
                    'reason': reason
                })

                # Save trade to database for dashboard
                self.save_trade_to_database(symbol, 'SELL', position.amount, price)

                emoji = "🟢" if pnl_pct > 0 else "🔴"
                logger.info(f"{emoji} SELL EXECUTED: {position.amount:.6f} {symbol} at ${price:.2f} "
                          f"(P&L: {pnl_pct:+.2f}%, Reason: {reason})")
            else:
                logger.error(f"Sell order failed for {symbol}: {order_result['error']}")

        except Exception as e:
            logger.error(f"Error executing sell for {symbol}: {e}", exc_info=True)

    async def log_portfolio_status(self):
        """Log current portfolio status"""
        try:
            portfolio_value = self.portfolio.get_portfolio_value()
            positions_count = len(self.portfolio.positions)

            # Log every 5 minutes
            if not hasattr(self, '_last_log_time'):
                self._last_log_time = datetime.now()

            time_since_last_log = (datetime.now() - self._last_log_time).seconds
            if time_since_last_log < 300:  # 5 minutes
                return

            self._last_log_time = datetime.now()

            logger.info(f"Portfolio Status: ${portfolio_value:,.2f} | "
                       f"Cash: ${self.portfolio.cash_balance:,.2f} | "
                       f"Positions: {positions_count} | "
                       f"Trades: {self.total_trades}")

            # Show signal monitor summary
            perf = self.signal_monitor.get_performance_summary()
            logger.info(f"Performance: {perf['win_rate']:.1f}% win rate "
                       f"({perf['winning_trades']}/{perf['total_trades']} trades)")

        except Exception as e:
            logger.error(f"Error logging portfolio status: {e}")

    def get_performance_metrics(self) -> Dict:
        """Get performance metrics for API compatibility"""
        if self.start_time is None:
            return {}

        portfolio_value = self.portfolio.get_portfolio_value()
        total_return = (portfolio_value - self.portfolio.initial_balance) / self.portfolio.initial_balance
        win_rate = self.winning_trades / self.total_trades if self.total_trades > 0 else 0

        return {
            'portfolio_value': portfolio_value,
            'total_return': total_return,
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'win_rate': win_rate,
            'positions': len(self.portfolio.positions),
            'cash_balance': self.portfolio.cash_balance,
            'running_time': datetime.now() - self.start_time if self.start_time else timedelta(0)
        }


# Global trading engine
_trading_engine_5m: Optional[LiveTradingEngine5m] = None

def get_trading_engine_5m(symbols: List[str] = None, paper_trading: bool = True, use_ai: bool = False) -> LiveTradingEngine5m:
    """
    Get the global 5-minute trading engine
    
    Args:
        symbols: List of trading symbols
        paper_trading: Use paper trading mode (no real money)
        use_ai: Enable AI-enhanced strategy (Technical 40% + LSTM 30% + Sentiment 30%)
    """
    global _trading_engine_5m

    if _trading_engine_5m is None:
        _trading_engine_5m = LiveTradingEngine5m(symbols, paper_trading, use_ai)

    return _trading_engine_5m


if __name__ == "__main__":
    import asyncio

    async def main():
        print("=" * 70)
        print("Live Trading Engine - 5-Minute Timeframe")
        print("=" * 70)
        print("\nFeatures:")
        print("  - Week1Refined5m strategy (65-75% win rate)")
        print("  - Real-time 5-minute candles")
        print("  - Signal monitoring and alerts")
        print("  - Expected: 8-12 trades per day")
        print("\n" + "=" * 70)

        engine = get_trading_engine_5m()
        await engine.start()

    asyncio.run(main())
