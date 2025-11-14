"""
Exchange Integration Module
Provides unified interface for multiple cryptocurrency exchanges
"""
import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables - find .env in project root
project_root = Path(__file__).parent.parent.parent
dotenv_path = project_root / '.env'
load_dotenv(dotenv_path)

import ccxt
import asyncio
try:
    from binance.client import Client as BinanceClient
    from binance.enums import *
    BINANCE_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Binance client not available: {e}")
    BinanceClient = None
    BINANCE_AVAILABLE = False
from typing import Dict, List, Optional, Tuple
import pandas as pd
from datetime import datetime
import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class ExchangeInterface(ABC):
    """Abstract base class for exchange integrations"""
    
    @abstractmethod
    async def get_balance(self) -> Dict:
        pass
    
    @abstractmethod
    async def get_ticker(self, symbol: str) -> Dict:
        pass
    
    @abstractmethod
    async def place_order(self, symbol: str, side: str, amount: float, price: Optional[float] = None) -> Dict:
        pass
    
    @abstractmethod
    async def get_open_orders(self, symbol: Optional[str] = None) -> List[Dict]:
        pass
    
    @abstractmethod
    async def cancel_order(self, order_id: str, symbol: str) -> Dict:
        pass

class BinanceExchange(ExchangeInterface):
    """Binance exchange integration"""
    
    def __init__(self, api_key: str = None, api_secret: str = None, testnet: bool = True, use_us: bool = True):
        """
        Initialize Binance exchange connection
        
        Args:
            api_key: Binance API key
            api_secret: Binance API secret
            testnet: Use testnet (default True for safety)
            use_us: Use Binance.US endpoint (default True for US users)
        """
        if not BINANCE_AVAILABLE:
            logger.warning("Binance client not available - running in demo mode")
            self.demo_mode = True
            self.client = None
            return
            
        self.api_key = api_key or os.getenv("BINANCE_API_KEY")
        self.api_secret = api_secret or os.getenv("BINANCE_SECRET_KEY")  # ✅ Fixed to match .env file
        self.testnet = testnet
        self.use_us = use_us
        
        if not self.api_key or not self.api_secret or self.api_key == 'your_binance_api_key_here':
            logger.warning("Binance API credentials not found or using placeholders. Using demo mode.")
            self.demo_mode = True
            self.client = None
        else:
            self.demo_mode = False
            try:
                # Configure API endpoint based on region
                if use_us:
                    # Binance.US endpoint
                    logger.info("Configuring Binance.US endpoint for US users")
                    self.client = BinanceClient(
                        self.api_key, 
                        self.api_secret,
                        tld='us',  # Use Binance.US domain
                        requests_params={'timeout': 30}  # Increase timeout to 30 seconds
                    )
                else:
                    # Regular Binance endpoint
                    self.client = BinanceClient(
                        self.api_key, 
                        self.api_secret,
                        testnet=testnet,
                        requests_params={'timeout': 30}
                    )
            except Exception as e:
                logger.error(f"Failed to initialize Binance client: {e}")
                self.demo_mode = True
                self.client = None
    
    async def get_balance(self) -> Dict:
        """Get account balance"""
        if self.demo_mode:
            return self._demo_balance()
        
        try:
            account = self.client.get_account()
            balances = {}
            
            for balance in account['balances']:
                asset = balance['asset']
                free = float(balance['free'])
                locked = float(balance['locked'])
                total = free + locked
                
                if total > 0:  # Only include non-zero balances
                    balances[asset] = {
                        'free': free,
                        'locked': locked,
                        'total': total
                    }
            
            return balances
            
        except Exception as e:
            logger.error(f"Error getting balance: {e}")
            return {}
    
    async def get_ticker(self, symbol: str) -> Dict:
        """Get current ticker price with retry logic"""
        if self.demo_mode:
            return self._demo_ticker(symbol)
        
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                ticker = self.client.get_symbol_ticker(symbol=symbol)
                return {
                    'symbol': ticker['symbol'],
                    'price': float(ticker['price']),
                    'timestamp': datetime.now()
                }
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(f"Error getting ticker for {symbol} (attempt {attempt + 1}/{max_retries}): {e}")
                    await asyncio.sleep(retry_delay)
                else:
                    logger.error(f"Error getting ticker for {symbol} after {max_retries} attempts: {e}")
                    return {}
    
    async def place_order(self, symbol: str, side: str, amount: float, price: Optional[float] = None) -> Dict:
        """Place an order"""
        if self.demo_mode:
            return self._demo_order(symbol, side, amount, price)
        
        try:
            order_type = ORDER_TYPE_MARKET if price is None else ORDER_TYPE_LIMIT
            
            if side.upper() == 'BUY':
                if order_type == ORDER_TYPE_MARKET:
                    order = self.client.order_market_buy(
                        symbol=symbol,
                        quoteOrderQty=amount  # Amount in USDT for market buy
                    )
                else:
                    order = self.client.order_limit_buy(
                        symbol=symbol,
                        quantity=amount,
                        price=str(price)
                    )
            else:  # SELL
                if order_type == ORDER_TYPE_MARKET:
                    order = self.client.order_market_sell(
                        symbol=symbol,
                        quantity=amount
                    )
                else:
                    order = self.client.order_limit_sell(
                        symbol=symbol,
                        quantity=amount,
                        price=str(price)
                    )
            
            return {
                'order_id': order['orderId'],
                'symbol': order['symbol'],
                'side': order['side'],
                'amount': float(order['origQty']),
                'price': float(order['price']) if order['price'] != '0.00000000' else None,
                'status': order['status'],
                'timestamp': datetime.fromtimestamp(order['transactTime'] / 1000)
            }
            
        except Exception as e:
            logger.error(f"Error placing order: {e}")
            return {'error': str(e)}
    
    async def get_open_orders(self, symbol: Optional[str] = None) -> List[Dict]:
        """Get open orders"""
        if self.demo_mode:
            return []
        
        try:
            orders = self.client.get_open_orders(symbol=symbol)
            
            formatted_orders = []
            for order in orders:
                formatted_orders.append({
                    'order_id': order['orderId'],
                    'symbol': order['symbol'],
                    'side': order['side'],
                    'amount': float(order['origQty']),
                    'price': float(order['price']),
                    'status': order['status'],
                    'timestamp': datetime.fromtimestamp(order['time'] / 1000)
                })
            
            return formatted_orders
            
        except Exception as e:
            logger.error(f"Error getting open orders: {e}")
            return []
    
    async def cancel_order(self, order_id: str, symbol: str) -> Dict:
        """Cancel an order"""
        if self.demo_mode:
            return {'status': 'CANCELED', 'order_id': order_id}
        
        try:
            result = self.client.cancel_order(symbol=symbol, orderId=order_id)
            return {
                'order_id': result['orderId'],
                'symbol': result['symbol'],
                'status': result['status']
            }
        except Exception as e:
            logger.error(f"Error canceling order: {e}")
            return {'error': str(e)}
    
    def _demo_balance(self) -> Dict:
        """Demo balance for testing"""
        return {
            'USDT': {'free': 10000.0, 'locked': 0.0, 'total': 10000.0},
            'BTC': {'free': 0.0, 'locked': 0.0, 'total': 0.0},
            'ETH': {'free': 0.0, 'locked': 0.0, 'total': 0.0}
        }
    
    def _demo_ticker(self, symbol: str) -> Dict:
        """Demo ticker for testing"""
        # Mock prices for demo
        demo_prices = {
            'BTCUSDT': 32030.58,
            'ETHUSDT': 2529.55,
            'SOLUSDT': 108.04,
            'ADAUSDT': 0.55,
            'DOTUSDT': 5.23
        }
        
        return {
            'symbol': symbol,
            'price': demo_prices.get(symbol, 100.0),
            'timestamp': datetime.now()
        }
    
    def _demo_order(self, symbol: str, side: str, amount: float, price: Optional[float]) -> Dict:
        """Demo order for testing"""
        import random
        
        return {
            'order_id': f"demo_{random.randint(1000000, 9999999)}",
            'symbol': symbol,
            'side': side.upper(),
            'amount': amount,
            'price': price,
            'status': 'FILLED',
            'timestamp': datetime.now()
        }

class ExchangeManager:
    """Manager for multiple exchange connections"""
    
    def __init__(self):
        self.exchanges = {}
        self.default_exchange = None
    
    def add_exchange(self, name: str, exchange: ExchangeInterface, is_default: bool = False):
        """Add an exchange"""
        self.exchanges[name] = exchange
        if is_default or self.default_exchange is None:
            self.default_exchange = name
    
    def get_exchange(self, name: str = None) -> Optional[ExchangeInterface]:
        """Get exchange by name or default"""
        if name is None:
            name = self.default_exchange
        return self.exchanges.get(name)
    
    def list_exchanges(self) -> List[str]:
        """List available exchanges"""
        return list(self.exchanges.keys())

# Global exchange manager instance
exchange_manager = ExchangeManager()

def initialize_exchanges():
    """Initialize and register all exchange connections"""
    global exchange_manager
    
    if not BINANCE_AVAILABLE:
        logger.warning("Binance client not available - skipping exchange initialization")
        return exchange_manager
    
    try:
        # Initialize Binance.US exchange (for US users)
        # Using use_us=True to connect to Binance.US endpoint instead of regular Binance
        binance = BinanceExchange(testnet=False, use_us=True)  # ✅ Binance.US for real trading
        exchange_manager.add_exchange('binance', binance, is_default=True)
        logger.info("Exchanges initialized successfully")
    except Exception as e:
        logger.warning(f"Failed to initialize exchanges: {e}")
    
    return exchange_manager

# DON'T initialize on import - API backend will call this after loading .env
#initialize_exchanges()
