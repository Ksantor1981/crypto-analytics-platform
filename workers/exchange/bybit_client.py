"""
Bybit API Client для получения реальных данных о ценах и торгах
"""
import asyncio
import aiohttp
import hashlib
import hmac
import time
import json
from typing import Dict, List, Optional, Any
from decimal import Decimal
import logging

from ..real_data_config import BYBIT_API_KEY, BYBIT_API_SECRET, CRYPTO_SYMBOLS

logger = logging.getLogger(__name__)

class BybitClient:
    """
    Клиент для работы с Bybit API
    """
    
    def __init__(self):
        self.api_key = BYBIT_API_KEY
        self.api_secret = BYBIT_API_SECRET
        self.base_url = "https://api.bybit.com"
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def _generate_signature(self, params: str, timestamp: str) -> str:
        """Генерация подписи для аутентификации"""
        param_str = f"{timestamp}{self.api_key}{params}"
        return hmac.new(
            self.api_secret.encode('utf-8'),
            param_str.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    def _get_headers(self, params: str = "") -> Dict[str, str]:
        """Получение заголовков для запроса"""
        timestamp = str(int(time.time() * 1000))
        signature = self._generate_signature(params, timestamp)
        
        return {
            'X-BAPI-API-KEY': self.api_key,
            'X-BAPI-SIGN': signature,
            'X-BAPI-SIGN-TYPE': '2',
            'X-BAPI-TIMESTAMP': timestamp,
            'Content-Type': 'application/json'
        }
    
    async def get_current_prices(self, symbols: List[str] = None) -> Dict[str, Decimal]:
        """Получение текущих цен для криптовалют"""
        if symbols is None:
            symbols = CRYPTO_SYMBOLS
            
        prices = {}
        
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()
                
            url = f"{self.base_url}/v5/market/tickers"
            params = {"category": "spot"}
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if data.get("retCode") == 0:
                        for ticker in data.get("result", {}).get("list", []):
                            symbol = ticker.get("symbol", "")
                            if symbol in symbols:
                                try:
                                    price = Decimal(ticker.get("lastPrice", "0"))
                                    prices[symbol] = price
                                except:
                                    continue
                    else:
                        logger.error(f"Bybit API error: {data.get('retMsg', 'Unknown error')}")
                else:
                    logger.error(f"HTTP error: {response.status}")
                    
        except Exception as e:
            logger.error(f"Error fetching prices from Bybit: {e}")
            
        return prices
    
    async def get_klines(self, symbol: str, interval: str = "1", limit: int = 200) -> List[Dict]:
        """Получение данных о свечах (klines)"""
        klines = []
        
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()
                
            url = f"{self.base_url}/v5/market/kline"
            params = {
                "category": "spot",
                "symbol": symbol,
                "interval": interval,
                "limit": limit
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if data.get("retCode") == 0:
                        for kline in data.get("result", {}).get("list", []):
                            try:
                                klines.append({
                                    "timestamp": int(kline[0]),
                                    "open": Decimal(kline[1]),
                                    "high": Decimal(kline[2]),
                                    "low": Decimal(kline[3]),
                                    "close": Decimal(kline[4]),
                                    "volume": Decimal(kline[5])
                                })
                            except:
                                continue
                    else:
                        logger.error(f"Bybit API error: {data.get('retMsg', 'Unknown error')}")
                else:
                    logger.error(f"HTTP error: {response.status}")
                    
        except Exception as e:
            logger.error(f"Error fetching klines from Bybit: {e}")
            
        return klines
    
    async def get_market_data(self, symbols: List[str] = None) -> Dict[str, Dict]:
        """Получение расширенных рыночных данных"""
        if symbols is None:
            symbols = CRYPTO_SYMBOLS
            
        market_data = {}
        
        try:
            prices = await self.get_current_prices(symbols)
            
            for symbol in symbols:
                if symbol in prices:
                    # Получаем дополнительные данные для каждого символа
                    klines = await self.get_klines(symbol, "1", 24)  # 24 часа данных
                    
                    if klines:
                        # Вычисляем 24h изменение
                        current_price = prices[symbol]
                        price_24h_ago = klines[-1]["close"] if klines else current_price
                        
                        change_24h = ((current_price - price_24h_ago) / price_24h_ago * 100) if price_24h_ago > 0 else 0
                        
                        # Вычисляем максимум и минимум за 24h
                        high_24h = max([k["high"] for k in klines]) if klines else current_price
                        low_24h = min([k["low"] for k in klines]) if klines else current_price
                        
                        # Вычисляем объем торгов за 24h
                        volume_24h = sum([k["volume"] for k in klines]) if klines else 0
                        
                        market_data[symbol] = {
                            "symbol": symbol,
                            "current_price": current_price,
                            "change_24h": change_24h,
                            "high_24h": high_24h,
                            "low_24h": low_24h,
                            "volume_24h": volume_24h,
                            "timestamp": int(time.time()),
                            "source": "bybit"
                        }
                    else:
                        market_data[symbol] = {
                            "symbol": symbol,
                            "current_price": prices[symbol],
                            "timestamp": int(time.time()),
                            "source": "bybit"
                        }
                        
        except Exception as e:
            logger.error(f"Error fetching market data from Bybit: {e}")
            
        return market_data
    
    async def test_connection(self) -> bool:
        """Тестирование соединения с Bybit API"""
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()
                
            url = f"{self.base_url}/v5/market/time"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("retCode") == 0:
                        logger.info("Bybit API connection successful")
                        return True
                        
            logger.error("Bybit API connection failed")
            return False
            
        except Exception as e:
            logger.error(f"Error testing Bybit connection: {e}")
            return False

# Функция для быстрого тестирования
async def test_bybit_integration():
    """Быстрый тест интеграции с Bybit"""
    async with BybitClient() as client:
        # Тест соединения
        connection_ok = await client.test_connection()
        print(f"✅ Bybit connection: {'OK' if connection_ok else 'FAILED'}")
        
        if connection_ok:
            # Тест получения цен
            prices = await client.get_current_prices(["BTCUSDT", "ETHUSDT"])
            print(f"✅ Current prices: {prices}")
            
            # Тест получения рыночных данных
            market_data = await client.get_market_data(["BTCUSDT"])
            print(f"✅ Market data: {market_data}")
            
        return connection_ok

if __name__ == "__main__":
    asyncio.run(test_bybit_integration()) 