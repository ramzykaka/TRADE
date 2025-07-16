from binance.client import Client
from binance.exceptions import BinanceAPIException
import logging
from typing import Dict, List, Optional
from datetime import datetime
import asyncio
from utils.config import load_config

class BinanceAPI:
    def __init__(self, testnet: bool = False):
        """
        Initialize Binance API client
        
        :param testnet: Use testnet environment (default: False)
        """
        self.config = load_config()
        self.testnet = testnet
        self.client = None
        self.logger = logging.getLogger(__name__)
        self._initialize_client()
        self.last_update = datetime.now()

    def _initialize_client(self):
        """Initialize Binance client with proper configuration"""
        try:
            self.client = Client(
                api_key=self.config['BINANCE_API_KEY'],
                api_secret=self.config['BINANCE_API_SECRET'],
                testnet=self.testnet,
                requests_params={'timeout': 10}
            )
            self.logger.info("Binance client initialized successfully")
        except BinanceAPIException as e:
            self.logger.error(f"Failed to initialize Binance client: {e}")
            raise

    async def get_balances(self) -> List[Dict]:
        """Get all non-zero balances"""
        try:
            account = await self.client.get_account()
            return [
                {
                    'asset': item['asset'],
                    'free': float(item['free']),
                    'locked': float(item['locked'])
                }
                for item in account['balances']
                if float(item['free']) > 0 or float(item['locked']) > 0
            ]
        except BinanceAPIException as e:
            self.logger.error(f"Balance check failed: {e}")
            return []

    async def create_order(self, symbol: str, side: str, quantity: float, 
                         order_type: str = 'MARKET') -> Optional[Dict]:
        """Create a new trade order"""
        try:
            order = await self.client.create_order(
                symbol=symbol,
                side=side.upper(),
                type=order_type,
                quantity=quantity
            )
            self.last_update = datetime.now()
            return order
        except BinanceAPIException as e:
            self.logger.error(f"Order failed for {symbol}: {e}")
            return None

    async def get_ticker(self, symbol: str) -> Optional[Dict]:
        """Get current price for a symbol"""
        try:
            return await self.client.get_symbol_ticker(symbol=symbol)
        except BinanceAPIException as e:
            self.logger.error(f"Price check failed for {symbol}: {e}")
            return None

    def health_check(self) -> bool:
        """Check if API connection is healthy"""
        try:
            self.client.get_account()
            return True
        except:
            return False