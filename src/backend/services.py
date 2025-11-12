"""
Business logic services for trading operations
"""
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Optional
import logging

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from data.models import Trade, Portfolio, MarketData
from .schemas import TradeRequest

logger = logging.getLogger(__name__)


class TradingService:
    """Service for handling trading operations"""
    
    async def execute_trade(self, trade_request: TradeRequest, db: Session) -> Trade:
        """Execute a trade order"""
        try:
            # Get current market price if no price specified
            current_price = trade_request.price
            if not current_price:
                market_data = db.query(MarketData).filter(
                    MarketData.symbol == trade_request.symbol.replace('/', '')
                ).order_by(MarketData.timestamp.desc()).first()
                
                if not market_data:
                    raise ValueError("No market data available for symbol")
                
                current_price = float(market_data.close_price)
            
            # Create trade record
            trade = Trade(
                symbol=trade_request.symbol.replace('/', ''),
                side=trade_request.side,
                quantity=trade_request.quantity,
                price=current_price,
                timestamp=datetime.utcnow(),
                strategy=trade_request.strategy
            )
            
            # Save trade
            db.add(trade)
            db.commit()
            db.refresh(trade)
            
            # Update portfolio
            await self._update_portfolio(trade, db)
            
            logger.info(f"Executed trade: {trade.side} {trade.quantity} {trade.symbol} @ {trade.price}")
            return trade
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error executing trade: {e}")
            raise
    
    async def _update_portfolio(self, trade: Trade, db: Session):
        """Update portfolio after trade execution"""
        try:
            # Find existing position
            position = db.query(Portfolio).filter(
                Portfolio.symbol == trade.symbol
            ).first()
            
            if not position:
                # Create new position
                position = Portfolio(
                    symbol=trade.symbol,
                    quantity=0,
                    avg_cost=0
                )
                db.add(position)
            
            # Update position based on trade
            if trade.side == 'buy':
                # Calculate new average cost
                total_cost = (position.quantity * (position.avg_cost or 0)) + (trade.quantity * trade.price)
                total_quantity = position.quantity + trade.quantity
                
                position.quantity = total_quantity
                position.avg_cost = total_cost / total_quantity if total_quantity > 0 else 0
                
            elif trade.side == 'sell':
                # Reduce position
                position.quantity -= trade.quantity
                
                # Calculate P&L
                if position.avg_cost:
                    pnl = (trade.price - position.avg_cost) * trade.quantity
                    trade.profit_loss = pnl
            
            position.updated_at = datetime.utcnow()
            db.commit()
            
        except Exception as e:
            logger.error(f"Error updating portfolio: {e}")
            raise


class PortfolioService:
    """Service for portfolio management"""
    
    async def get_portfolio(self, db: Session) -> List[Portfolio]:
        """Get current portfolio positions"""
        try:
            positions = db.query(Portfolio).filter(Portfolio.quantity > 0).all()
            return positions
        except Exception as e:
            logger.error(f"Error fetching portfolio: {e}")
            raise
    
    async def calculate_portfolio_value(self, db: Session) -> float:
        """Calculate total portfolio value in USDT"""
        try:
            total_value = 0.0
            positions = await self.get_portfolio(db)
            
            # Symbol mapping for market data lookup
            symbol_map = {
                "BTC": "BTCUSDT",
                "ETH": "ETHUSDT", 
                "ADA": "ADAUSDT",
                "DOT": "DOTUSDT",
                "SOL": "SOLUSDT"
            }
            
            for position in positions:
                # Get current market price using symbol mapping
                market_symbol = symbol_map.get(position.symbol, position.symbol)
                market_data = db.query(MarketData).filter(
                    MarketData.symbol == market_symbol
                ).order_by(MarketData.timestamp.desc()).first()
                
                if market_data:
                    current_price = float(market_data.close_price)
                    position_value = float(position.quantity) * current_price
                    total_value += position_value
                else:
                    # Fallback to average cost if no market data
                    position_value = float(position.quantity) * float(position.avg_cost or 0)
                    total_value += position_value
            
            return total_value
            
        except Exception as e:
            logger.error(f"Error calculating portfolio value: {e}")
            raise
    
    async def get_position_pnl(self, symbol: str, db: Session) -> dict:
        """Calculate unrealized P&L for a position"""
        try:
            position = db.query(Portfolio).filter(Portfolio.symbol == symbol).first()
            if not position:
                return {"unrealized_pnl": 0, "percentage": 0}
            
            # Get current market price
            market_data = db.query(MarketData).filter(
                MarketData.symbol == symbol
            ).order_by(MarketData.timestamp.desc()).first()
            
            if not market_data or not position.avg_cost:
                return {"unrealized_pnl": 0, "percentage": 0}
            
            current_price = float(market_data.close_price)
            avg_cost = float(position.avg_cost)
            quantity = float(position.quantity)
            
            unrealized_pnl = (current_price - avg_cost) * quantity
            percentage = ((current_price - avg_cost) / avg_cost) * 100 if avg_cost > 0 else 0
            
            return {
                "unrealized_pnl": unrealized_pnl,
                "percentage": percentage,
                "current_price": current_price,
                "avg_cost": avg_cost
            }
            
        except Exception as e:
            logger.error(f"Error calculating position P&L: {e}")
            raise


class RiskService:
    """Service for risk management"""
    
    def __init__(self, max_position_size: float = 0.1, stop_loss: float = 0.05):
        self.max_position_size = max_position_size  # 10% of portfolio
        self.stop_loss = stop_loss  # 5% stop loss
    
    async def validate_trade(self, trade_request: TradeRequest, db: Session) -> bool:
        """Validate trade against risk parameters"""
        try:
            # Check position size limits
            portfolio_service = PortfolioService()
            total_value = await portfolio_service.calculate_portfolio_value(db)
            
            trade_value = trade_request.quantity * (trade_request.price or 0)
            
            if total_value > 0:
                position_percentage = trade_value / total_value
                if position_percentage > self.max_position_size:
                    logger.warning(f"Trade exceeds position size limit: {position_percentage:.2%}")
                    return False
            
            # Additional risk checks can be added here
            return True
            
        except Exception as e:
            logger.error(f"Error validating trade: {e}")
            return False