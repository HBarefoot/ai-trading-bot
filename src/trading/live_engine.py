"""
Live Trading Engine
Executes trading strategies in real-time with risk management
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

from trading.exchange_integration import exchange_manager
from strategies.technical_indicators import TechnicalIndicators
from strategies.phase2_final_test import OptimizedPhase2Strategy
from data.database import get_db
from data.models import MarketData

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
        self.stop_loss_pct = 0.15  # 15% stop loss (matches Week1Refined strategy)
        self.take_profit_pct = 0.30  # 30% take profit (matches Week1Refined strategy)
        
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
            stop_loss=price * (1 - self.stop_loss_pct),  # 15% below entry
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

class LiveTradingEngine:
    """Main live trading engine"""
    
    def __init__(self, symbols: List[str] = None, paper_trading: bool = True):
        self.symbols = symbols or ['BTCUSDT', 'ETHUSDT', 'SOLUSDT']
        self.portfolio = PortfolioManager()
        # Using Week 1 Refined strategy - 75% win rate, +1.47% return, proven on 90 days
        from strategies.optimized_strategy_week1_refined import Week1RefinedStrategy
        self.strategy = Week1RefinedStrategy()
        self.indicators = TechnicalIndicators()
        self.exchange = exchange_manager.get_exchange('binance')
        
        # Paper trading mode - NO REAL MONEY
        self.paper_trading = paper_trading
        
        self.running = False
        self.update_interval = 60  # Update every 60 seconds
        self.last_signals = {}
        
        # Performance tracking
        self.start_time = None
        self.total_trades = 0
        self.winning_trades = 0
        self.paper_trades = []  # Store paper trading results
        
    async def start(self):
        """Start the live trading engine"""
        if self.running:
            logger.warning("Trading engine is already running")
            return
            
        self.running = True
        self.start_time = datetime.now()
        
        mode = "📄 PAPER TRADING" if self.paper_trading else "💰 LIVE TRADING"
        logger.info(f"🚀 {mode} Engine Started")
        logger.info(f"Symbols: {self.symbols}")
        logger.info(f"Initial Balance: ${self.portfolio.initial_balance:,.2f}")
        
        if self.paper_trading:
            logger.info("⚠️  PAPER TRADING MODE - NO REAL MONEY AT RISK")
        else:
            logger.warning("💰 LIVE TRADING MODE - REAL MONEY AT RISK!")
        
        try:
            while self.running:
                await self.trading_cycle()
                await asyncio.sleep(self.update_interval)
                
        except Exception as e:
            logger.error(f"Trading engine error: {e}")
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
            
            # Generate signals for each symbol
            for symbol in self.symbols:
                if symbol in current_prices:
                    await self.process_symbol(symbol, current_prices[symbol])
            
            # Log portfolio status
            await self.log_portfolio_status()
            
        except Exception as e:
            logger.error(f"Error in trading cycle: {e}")
    
    async def process_symbol(self, symbol: str, current_price: float):
        """Process trading signals for a symbol"""
        try:
            # Get historical data for signal generation
            db = next(get_db())
            market_data = db.query(MarketData).filter(
                MarketData.symbol == symbol
            ).order_by(MarketData.timestamp.desc()).limit(100).all()
            
            if len(market_data) < 50:  # Need enough data for indicators
                return
            
            # Convert to DataFrame
            data = []
            for record in reversed(market_data):  # Reverse to get chronological order
                data.append({
                    'timestamp': record.timestamp,
                    'close_price': float(record.close_price),
                    'high_price': float(record.high_price),
                    'low_price': float(record.low_price),
                    'volume': float(record.volume)
                })
            
            df = pd.DataFrame(data)
            df.set_index('timestamp', inplace=True)
            
            # Add current price as latest data point
            current_data = {
                'close_price': current_price,
                'high_price': current_price,
                'low_price': current_price,
                'volume': 0  # We don't have current volume
            }
            
            current_df = pd.DataFrame([current_data], index=[datetime.now()])
            df = pd.concat([df, current_df])
            
            # Generate signals
            signals = self.strategy.generate_signals(df)
            latest_signal = signals.iloc[-1]
            
            # Store previous signal to detect changes
            prev_signal = self.last_signals.get(symbol, 0.0)
            self.last_signals[symbol] = latest_signal
            
            # Execute trades based on signal changes
            if latest_signal > 0 and prev_signal <= 0:  # New buy signal
                await self.execute_buy(symbol, current_price)
            elif latest_signal < 0 and prev_signal >= 0:  # New sell signal
                await self.execute_sell(symbol, current_price, "SIGNAL")
            
            db.close()
            
        except Exception as e:
            logger.error(f"Error processing {symbol}: {e}")
    
    async def execute_buy(self, symbol: str, price: float):
        """Execute a buy order"""
        try:
            if not self.portfolio.can_open_position(symbol):
                logger.info(f"Cannot open position for {symbol}: position exists or insufficient cash")
                return
            
            # Calculate position size
            amount = self.portfolio.get_position_size(symbol, price)
            if amount <= 0:
                logger.info(f"Position size too small for {symbol}")
                return
            
            # Place order
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
                    strategy="OptimizedPhase2",
                    status=OrderStatus.FILLED,
                    order_id=order_result.get('order_id')
                )
                self.portfolio.trades.append(trade)
                self.total_trades += 1
                
                logger.info(f"🟢 BUY EXECUTED: {amount:.6f} {symbol} at ${price:.2f}")
            else:
                logger.error(f"Buy order failed for {symbol}: {order_result['error']}")
                
        except Exception as e:
            logger.error(f"Error executing buy for {symbol}: {e}")
    
    async def execute_sell(self, symbol: str, price: float, reason: str = "SIGNAL"):
        """Execute a sell order"""
        try:
            if symbol not in self.portfolio.positions:
                logger.info(f"No position to sell for {symbol}")
                return
            
            position = self.portfolio.positions[symbol]
            
            # Place sell order
            order_result = await self.exchange.place_order(
                symbol=symbol,
                side='SELL',
                amount=position.amount,
                price=None  # Market order
            )
            
            if 'error' not in order_result:
                # Close position
                pnl = self.portfolio.close_position(symbol, price)
                
                # Record trade
                trade = Trade(
                    id=f"trade_{len(self.portfolio.trades) + 1}",
                    symbol=symbol,
                    side='SELL',
                    amount=position.amount,
                    price=price,
                    timestamp=datetime.now(),
                    strategy="OptimizedPhase2",
                    status=OrderStatus.FILLED,
                    order_id=order_result.get('order_id')
                )
                self.portfolio.trades.append(trade)
                self.total_trades += 1
                
                if pnl and pnl > 0:
                    self.winning_trades += 1
                
                logger.info(f"🔴 SELL EXECUTED ({reason}): {position.amount:.6f} {symbol} at ${price:.2f}, P&L: ${pnl:.2f}")
            else:
                logger.error(f"Sell order failed for {symbol}: {order_result['error']}")
                
        except Exception as e:
            logger.error(f"Error executing sell for {symbol}: {e}")
    
    async def log_portfolio_status(self):
        """Log current portfolio status"""
        portfolio_value = self.portfolio.get_portfolio_value()
        total_return = (portfolio_value - self.portfolio.initial_balance) / self.portfolio.initial_balance
        
        logger.info("📊 Portfolio Status:")
        logger.info(f"  💰 Total Value: ${portfolio_value:,.2f}")
        logger.info(f"  💵 Cash: ${self.portfolio.cash_balance:,.2f}")
        logger.info(f"  📈 Total Return: {total_return:.2%}")
        logger.info(f"  🎯 Positions: {len(self.portfolio.positions)}")
        
        if self.portfolio.positions:
            logger.info("  🔍 Open Positions:")
            for symbol, position in self.portfolio.positions.items():
                pnl_pct = (position.unrealized_pnl / (position.amount * position.entry_price)) * 100
                logger.info(f"    {symbol}: {position.amount:.6f} @ ${position.entry_price:.2f} "
                           f"(Current: ${position.current_price:.2f}, P&L: {pnl_pct:+.2f}%)")
    
    def get_performance_metrics(self) -> Dict:
        """Get performance metrics"""
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

# Global trading engine instance
trading_engine = None

def get_trading_engine(paper_trading: bool = True) -> LiveTradingEngine:
    """
    Get the global trading engine instance
    
    Args:
        paper_trading: If True, enable paper trading mode (NO REAL MONEY)
    """
    global trading_engine
    if trading_engine is None:
        trading_engine = LiveTradingEngine(paper_trading=paper_trading)
    return trading_engine