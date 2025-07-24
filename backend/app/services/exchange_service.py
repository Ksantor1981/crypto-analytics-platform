"""
Exchange Service for integrating with cryptocurrency exchanges
"""
import asyncio
import aiohttp
import hmac
import hashlib
import time
import json
import logging
from typing import Dict, Any, Optional, List
from decimal import Decimal
from urllib.parse import urlencode

from app.models.trading import ExchangeType
from app.core.config import get_settings

logger = logging.getLogger(__name__)

class ExchangeService:
    """Service for interacting with cryptocurrency exchanges"""
    
    def __init__(self):
        self.settings = get_settings()
        self.session = None
        
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    def validate_credentials(self, exchange: ExchangeType, api_key: str, api_secret: str, passphrase: Optional[str] = None) -> bool:
        """Validate API credentials with the exchange"""
        try:
            if exchange == ExchangeType.BYBIT:
                return self._validate_bybit_credentials(api_key, api_secret)
            elif exchange == ExchangeType.BINANCE:
                return self._validate_binance_credentials(api_key, api_secret)
            else:
                logger.warning(f"Unsupported exchange: {exchange}")
                return False
        except Exception as e:
            logger.error(f"Error validating credentials for {exchange}: {e}")
            return False
    
    def _validate_bybit_credentials(self, api_key: str, api_secret: str) -> bool:
        """Validate Bybit API credentials"""
        try:
            # Test API credentials by getting account info
            timestamp = int(time.time() * 1000)
            params = {
                "api_key": api_key,
                "timestamp": timestamp,
                "recv_window": 5000
            }
            
            # Create signature
            query_string = urlencode(params)
            signature = hmac.new(
                api_secret.encode('utf-8'),
                query_string.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            params["sign"] = signature
            
            # This would make an actual API call in production
            # For now, we'll simulate a successful validation
            logger.info("Bybit credentials validation simulated")
            return True
            
        except Exception as e:
            logger.error(f"Error validating Bybit credentials: {e}")
            return False
    
    def _validate_binance_credentials(self, api_key: str, api_secret: str) -> bool:
        """Validate Binance API credentials"""
        try:
            # Test API credentials by getting account info
            timestamp = int(time.time() * 1000)
            params = {
                "timestamp": timestamp,
                "recvWindow": 5000
            }
            
            # Create signature
            query_string = urlencode(params)
            signature = hmac.new(
                api_secret.encode('utf-8'),
                query_string.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            params["signature"] = signature
            
            # This would make an actual API call in production
            # For now, we'll simulate a successful validation
            logger.info("Binance credentials validation simulated")
            return True
            
        except Exception as e:
            logger.error(f"Error validating Binance credentials: {e}")
            return False
    
    async def place_order(self, exchange: ExchangeType, api_key: str, api_secret: str, passphrase: Optional[str],
                         symbol: str, side: str, order_type: str, quantity: Decimal, 
                         price: Optional[Decimal] = None, time_in_force: str = "GTC") -> Dict[str, Any]:
        """Place an order on the exchange"""
        try:
            if exchange == ExchangeType.BYBIT:
                return await self._place_bybit_order(
                    api_key, api_secret, symbol, side, order_type, quantity, price, time_in_force
                )
            elif exchange == ExchangeType.BINANCE:
                return await self._place_binance_order(
                    api_key, api_secret, symbol, side, order_type, quantity, price, time_in_force
                )
            else:
                raise ValueError(f"Unsupported exchange: {exchange}")
                
        except Exception as e:
            logger.error(f"Error placing order on {exchange}: {e}")
            raise
    
    async def _place_bybit_order(self, api_key: str, api_secret: str, symbol: str, side: str, 
                                order_type: str, quantity: Decimal, price: Optional[Decimal], 
                                time_in_force: str) -> Dict[str, Any]:
        """Place order on Bybit"""
        try:
            timestamp = int(time.time() * 1000)
            
            # Prepare order parameters
            order_params = {
                "symbol": symbol,
                "side": side.upper(),
                "order_type": order_type.upper(),
                "qty": str(quantity),
                "time_in_force": time_in_force,
                "api_key": api_key,
                "timestamp": timestamp,
                "recv_window": 5000
            }
            
            if price:
                order_params["price"] = str(price)
            
            # Create signature
            query_string = urlencode(order_params)
            signature = hmac.new(
                api_secret.encode('utf-8'),
                query_string.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            order_params["sign"] = signature
            
            # In production, this would make an actual API call
            # For now, we'll simulate a successful order placement
            logger.info(f"Bybit order simulated: {symbol} {side} {quantity}")
            
            return {
                "order_id": f"bybit_{int(time.time())}",
                "client_order_id": f"client_{int(time.time())}",
                "symbol": symbol,
                "side": side,
                "order_type": order_type,
                "quantity": quantity,
                "price": price,
                "status": "NEW",
                "timestamp": timestamp
            }
            
        except Exception as e:
            logger.error(f"Error placing Bybit order: {e}")
            raise
    
    async def _place_binance_order(self, api_key: str, api_secret: str, symbol: str, side: str,
                                  order_type: str, quantity: Decimal, price: Optional[Decimal],
                                  time_in_force: str) -> Dict[str, Any]:
        """Place order on Binance"""
        try:
            timestamp = int(time.time() * 1000)
            
            # Prepare order parameters
            order_params = {
                "symbol": symbol,
                "side": side.upper(),
                "type": order_type.upper(),
                "quantity": str(quantity),
                "timeInForce": time_in_force,
                "timestamp": timestamp,
                "recvWindow": 5000
            }
            
            if price:
                order_params["price"] = str(price)
            
            # Create signature
            query_string = urlencode(order_params)
            signature = hmac.new(
                api_secret.encode('utf-8'),
                query_string.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            order_params["signature"] = signature
            
            # In production, this would make an actual API call
            # For now, we'll simulate a successful order placement
            logger.info(f"Binance order simulated: {symbol} {side} {quantity}")
            
            return {
                "orderId": f"binance_{int(time.time())}",
                "clientOrderId": f"client_{int(time.time())}",
                "symbol": symbol,
                "side": side,
                "type": order_type,
                "quantity": quantity,
                "price": price,
                "status": "NEW",
                "timestamp": timestamp
            }
            
        except Exception as e:
            logger.error(f"Error placing Binance order: {e}")
            raise
    
    async def get_current_price(self, exchange: ExchangeType, api_key: str, api_secret: str, 
                               passphrase: Optional[str], symbol: str) -> Optional[Decimal]:
        """Get current price for a symbol"""
        try:
            if exchange == ExchangeType.BYBIT:
                return await self._get_bybit_price(symbol)
            elif exchange == ExchangeType.BINANCE:
                return await self._get_binance_price(symbol)
            else:
                logger.warning(f"Unsupported exchange for price: {exchange}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting price from {exchange}: {e}")
            return None
    
    async def _get_bybit_price(self, symbol: str) -> Optional[Decimal]:
        """Get current price from Bybit"""
        try:
            # In production, this would make an actual API call
            # For now, we'll simulate a price
            import random
            base_price = 50000 if "BTC" in symbol else 3000 if "ETH" in symbol else 100
            price_variation = random.uniform(-0.01, 0.01)  # ±1% variation
            price = base_price * (1 + price_variation)
            
            logger.info(f"Bybit price simulated for {symbol}: {price}")
            return Decimal(str(price))
            
        except Exception as e:
            logger.error(f"Error getting Bybit price: {e}")
            return None
    
    async def _get_binance_price(self, symbol: str) -> Optional[Decimal]:
        """Get current price from Binance"""
        try:
            # In production, this would make an actual API call
            # For now, we'll simulate a price
            import random
            base_price = 50000 if "BTC" in symbol else 3000 if "ETH" in symbol else 100
            price_variation = random.uniform(-0.01, 0.01)  # ±1% variation
            price = base_price * (1 + price_variation)
            
            logger.info(f"Binance price simulated for {symbol}: {price}")
            return Decimal(str(price))
            
        except Exception as e:
            logger.error(f"Error getting Binance price: {e}")
            return None
    
    async def get_account_balance(self, exchange: ExchangeType, api_key: str, api_secret: str,
                                 passphrase: Optional[str]) -> Dict[str, Any]:
        """Get account balance from exchange"""
        try:
            if exchange == ExchangeType.BYBIT:
                return await self._get_bybit_balance(api_key, api_secret)
            elif exchange == ExchangeType.BINANCE:
                return await self._get_binance_balance(api_key, api_secret)
            else:
                logger.warning(f"Unsupported exchange for balance: {exchange}")
                return {}
                
        except Exception as e:
            logger.error(f"Error getting balance from {exchange}: {e}")
            return {}
    
    async def _get_bybit_balance(self, api_key: str, api_secret: str) -> Dict[str, Any]:
        """Get balance from Bybit"""
        try:
            timestamp = int(time.time() * 1000)
            params = {
                "api_key": api_key,
                "timestamp": timestamp,
                "recv_window": 5000
            }
            
            # Create signature
            query_string = urlencode(params)
            signature = hmac.new(
                api_secret.encode('utf-8'),
                query_string.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            params["sign"] = signature
            
            # In production, this would make an actual API call
            # For now, we'll simulate a balance
            logger.info("Bybit balance simulated")
            
            return {
                "total_balance": 10000.0,
                "available_balance": 9500.0,
                "used_balance": 500.0,
                "currencies": {
                    "USDT": {"total": 10000.0, "available": 9500.0},
                    "BTC": {"total": 0.1, "available": 0.09},
                    "ETH": {"total": 1.5, "available": 1.4}
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting Bybit balance: {e}")
            return {}
    
    async def _get_binance_balance(self, api_key: str, api_secret: str) -> Dict[str, Any]:
        """Get balance from Binance"""
        try:
            timestamp = int(time.time() * 1000)
            params = {
                "timestamp": timestamp,
                "recvWindow": 5000
            }
            
            # Create signature
            query_string = urlencode(params)
            signature = hmac.new(
                api_secret.encode('utf-8'),
                query_string.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            params["signature"] = signature
            
            # In production, this would make an actual API call
            # For now, we'll simulate a balance
            logger.info("Binance balance simulated")
            
            return {
                "total_balance": 10000.0,
                "available_balance": 9500.0,
                "used_balance": 500.0,
                "currencies": {
                    "USDT": {"total": 10000.0, "available": 9500.0},
                    "BTC": {"total": 0.1, "available": 0.09},
                    "ETH": {"total": 1.5, "available": 1.4}
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting Binance balance: {e}")
            return {}
    
    async def cancel_order(self, exchange: ExchangeType, api_key: str, api_secret: str,
                          passphrase: Optional[str], symbol: str, order_id: str) -> bool:
        """Cancel an order on the exchange"""
        try:
            if exchange == ExchangeType.BYBIT:
                return await self._cancel_bybit_order(api_key, api_secret, symbol, order_id)
            elif exchange == ExchangeType.BINANCE:
                return await self._cancel_binance_order(api_key, api_secret, symbol, order_id)
            else:
                logger.warning(f"Unsupported exchange for cancel: {exchange}")
                return False
                
        except Exception as e:
            logger.error(f"Error canceling order on {exchange}: {e}")
            return False
    
    async def _cancel_bybit_order(self, api_key: str, api_secret: str, symbol: str, order_id: str) -> bool:
        """Cancel order on Bybit"""
        try:
            timestamp = int(time.time() * 1000)
            params = {
                "symbol": symbol,
                "order_id": order_id,
                "api_key": api_key,
                "timestamp": timestamp,
                "recv_window": 5000
            }
            
            # Create signature
            query_string = urlencode(params)
            signature = hmac.new(
                api_secret.encode('utf-8'),
                query_string.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            params["sign"] = signature
            
            # In production, this would make an actual API call
            logger.info(f"Bybit order cancel simulated: {order_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error canceling Bybit order: {e}")
            return False
    
    async def _cancel_binance_order(self, api_key: str, api_secret: str, symbol: str, order_id: str) -> bool:
        """Cancel order on Binance"""
        try:
            timestamp = int(time.time() * 1000)
            params = {
                "symbol": symbol,
                "orderId": order_id,
                "timestamp": timestamp,
                "recvWindow": 5000
            }
            
            # Create signature
            query_string = urlencode(params)
            signature = hmac.new(
                api_secret.encode('utf-8'),
                query_string.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            params["signature"] = signature
            
            # In production, this would make an actual API call
            logger.info(f"Binance order cancel simulated: {order_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error canceling Binance order: {e}")
            return False 