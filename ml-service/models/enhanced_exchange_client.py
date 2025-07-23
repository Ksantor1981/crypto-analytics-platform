"""
Enhanced Exchange Client for ML Service
Integrates multiple exchanges including Bybit for production use
"""
import asyncio
import aiohttp
import hashlib
import hmac
import time
import json
from typing import Dict, List, Optional, Any, Tuple
from decimal import Decimal
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ExchangeConfig:
    """Configuration for exchange APIs"""
    name: str
    base_url: str
    rate_limit_per_second: int = 10
    rate_limit_per_minute: int = 600
    cache_ttl: int = 30

@dataclass
class PriceData:
    """Standardized price data structure"""
    symbol: str
    price: Decimal
    timestamp: datetime
    exchange: str
    volume_24h: Optional[Decimal] = None
    price_change_24h: Optional[Decimal] = None

class EnhancedExchangeClient:
    """
    Enhanced multi-exchange client for production use
    Supports Binance, Bybit, and other major exchanges
    """
    
    def __init__(self, bybit_api_key: str = None, bybit_api_secret: str = None):
        # Exchange configurations
        self.exchanges = {
            'binance': ExchangeConfig(
                name='binance',
                base_url='https://api.binance.com',
                rate_limit_per_second=10,
                rate_limit_per_minute=1200,
                cache_ttl=30
            ),
            'bybit': ExchangeConfig(
                name='bybit',
                base_url='https://api.bybit.com',
                rate_limit_per_second=10,
                rate_limit_per_minute=600,
                cache_ttl=30
            ),
            'coinbase': ExchangeConfig(
                name='coinbase',
                base_url='https://api.exchange.coinbase.com',
                rate_limit_per_second=5,
                rate_limit_per_minute=1000,
                cache_ttl=30
            )
        }
        
        # Bybit authentication
        self.bybit_api_key = bybit_api_key
        self.bybit_api_secret = bybit_api_secret
        
        # Session management
        self.sessions = {}
        self.rate_limits = {}
        
        # Caching
        self._price_cache = {}
        self._cache_expiry = {}
        
        # Health monitoring
        self._exchange_health = {}
        self._last_successful_requests = {}
        self._consecutive_failures = {}
        
    async def __aenter__(self):
        await self._initialize_sessions()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._cleanup_sessions()
    
    async def _initialize_sessions(self):
        """Initialize HTTP sessions for all exchanges"""
        for exchange_name, config in self.exchanges.items():
            if exchange_name not in self.sessions:
                timeout = aiohttp.ClientTimeout(total=30, connect=10)
                connector = aiohttp.TCPConnector(
                    limit=50,
                    limit_per_host=10,
                    ttl_dns_cache=300,
                    keepalive_timeout=30
                )
                
                self.sessions[exchange_name] = aiohttp.ClientSession(
                    connector=connector,
                    timeout=timeout,
                    headers={
                        'User-Agent': 'CryptoAnalyticsML/1.0',
                        'Accept': 'application/json'
                    }
                )
                
                # Initialize rate limiting
                self.rate_limits[exchange_name] = {
                    'requests_count': 0,
                    'reset_time': time.time(),
                    'last_request': 0
                }
                
                # Initialize health monitoring
                self._exchange_health[exchange_name] = True
                self._consecutive_failures[exchange_name] = 0
                
        logger.info(f"Initialized sessions for {len(self.sessions)} exchanges")
    
    async def _cleanup_sessions(self):
        """Clean up all HTTP sessions"""
        for session in self.sessions.values():
            if session and not session.closed:
                await session.close()
        self.sessions.clear()
    
    def _generate_bybit_signature(self, params: str, timestamp: str) -> str:
        """Generate signature for Bybit API authentication"""
        if not self.bybit_api_secret:
            return ""
            
        param_str = f"{timestamp}{self.bybit_api_key}{params}"
        return hmac.new(
            self.bybit_api_secret.encode('utf-8'),
            param_str.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    def _get_bybit_headers(self, params: str = "") -> Dict[str, str]:
        """Get headers for Bybit authenticated requests"""
        if not self.bybit_api_key or not self.bybit_api_secret:
            return {}
            
        timestamp = str(int(time.time() * 1000))
        signature = self._generate_bybit_signature(params, timestamp)
        
        return {
            'X-BAPI-API-KEY': self.bybit_api_key,
            'X-BAPI-SIGN': signature,
            'X-BAPI-SIGN-TYPE': '2',
            'X-BAPI-TIMESTAMP': timestamp,
            'Content-Type': 'application/json'
        }
    
    async def _check_rate_limit(self, exchange: str):
        """Check and enforce rate limits for exchange"""
        config = self.exchanges[exchange]
        rate_limit = self.rate_limits[exchange]
        current_time = time.time()
        
        # Reset minute counter
        if current_time - rate_limit['reset_time'] >= 60:
            rate_limit['requests_count'] = 0
            rate_limit['reset_time'] = current_time
        
        # Check minute limit
        if rate_limit['requests_count'] >= config.rate_limit_per_minute:
            wait_time = 60 - (current_time - rate_limit['reset_time'])
            logger.warning(f"Rate limit reached for {exchange}, waiting {wait_time:.1f}s")
            await asyncio.sleep(wait_time)
            rate_limit['requests_count'] = 0
            rate_limit['reset_time'] = time.time()
        
        # Check per-second limit
        time_since_last = current_time - rate_limit['last_request']
        min_interval = 1.0 / config.rate_limit_per_second
        
        if time_since_last < min_interval:
            await asyncio.sleep(min_interval - time_since_last)
        
        rate_limit['last_request'] = time.time()
        rate_limit['requests_count'] += 1
    
    def _is_cache_valid(self, cache_key: str, exchange: str) -> bool:
        """Check if cached data is still valid"""
        if cache_key not in self._cache_expiry:
            return False
        return time.time() < self._cache_expiry[cache_key]
    
    def _cache_data(self, cache_key: str, data: Any, exchange: str):
        """Cache data with appropriate TTL"""
        ttl = self.exchanges[exchange].cache_ttl
        self._price_cache[cache_key] = data
        self._cache_expiry[cache_key] = time.time() + ttl
    
    async def _make_request(self, exchange: str, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """Make HTTP request to exchange with error handling"""
        
        if exchange not in self.sessions:
            await self._initialize_sessions()
        
        session = self.sessions[exchange]
        config = self.exchanges[exchange]
        
        # Check cache first
        cache_key = f"{exchange}_{endpoint}_{json.dumps(params or {}, sort_keys=True)}"
        if self._is_cache_valid(cache_key, exchange):
            cached_data = self._price_cache.get(cache_key)
            if cached_data:
                return cached_data
        
        # Rate limiting
        await self._check_rate_limit(exchange)
        
        url = f"{config.base_url}{endpoint}"
        headers = {}
        
        # Add authentication headers for Bybit if needed
        if exchange == 'bybit' and self.bybit_api_key:
            headers.update(self._get_bybit_headers())
        
        try:
            async with session.get(url, params=params, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Cache successful response
                    self._cache_data(cache_key, data, exchange)
                    
                    # Update health status
                    self._exchange_health[exchange] = True
                    self._consecutive_failures[exchange] = 0
                    self._last_successful_requests[exchange] = datetime.now()
                    
                    return data
                else:
                    logger.warning(f"{exchange} API returned status {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error making request to {exchange}: {e}")
            self._consecutive_failures[exchange] += 1
            
            # Mark exchange as unhealthy after consecutive failures
            if self._consecutive_failures[exchange] >= 3:
                self._exchange_health[exchange] = False
            
            return None
    
    async def get_binance_price(self, symbol: str) -> Optional[PriceData]:
        """Get current price from Binance"""
        binance_symbol = symbol.replace('/', '')
        
        data = await self._make_request('binance', '/api/v3/ticker/24hr', {'symbol': binance_symbol})
        
        if data:
            return PriceData(
                symbol=symbol,
                price=Decimal(data['lastPrice']),
                timestamp=datetime.now(),
                exchange='binance',
                volume_24h=Decimal(data['volume']),
                price_change_24h=Decimal(data['priceChangePercent'])
            )
        return None
    
    async def get_bybit_price(self, symbol: str) -> Optional[PriceData]:
        """Get current price from Bybit"""
        bybit_symbol = symbol.replace('/', '')
        
        data = await self._make_request('bybit', '/v5/market/tickers', {
            'category': 'spot',
            'symbol': bybit_symbol
        })
        
        if data and data.get('retCode') == 0:
            result = data.get('result', {})
            ticker_list = result.get('list', [])
            
            if ticker_list:
                ticker = ticker_list[0]
                return PriceData(
                    symbol=symbol,
                    price=Decimal(ticker['lastPrice']),
                    timestamp=datetime.now(),
                    exchange='bybit',
                    volume_24h=Decimal(ticker['volume24h']),
                    price_change_24h=Decimal(ticker['price24hPcnt'])
                )
        return None
    
    async def get_coinbase_price(self, symbol: str) -> Optional[PriceData]:
        """Get current price from Coinbase"""
        coinbase_symbol = symbol.replace('/', '-').replace('USDT', 'USD')
        
        data = await self._make_request('coinbase', f'/products/{coinbase_symbol}/ticker')
        
        if data:
            return PriceData(
                symbol=symbol,
                price=Decimal(data['price']),
                timestamp=datetime.now(),
                exchange='coinbase',
                volume_24h=Decimal(data.get('volume', 0))
            )
        return None
    
    async def get_best_price(self, symbol: str) -> Optional[PriceData]:
        """Get best available price from multiple exchanges"""
        
        # Try exchanges in order of preference
        exchange_methods = [
            ('binance', self.get_binance_price),
            ('bybit', self.get_bybit_price),
            ('coinbase', self.get_coinbase_price)
        ]
        
        for exchange_name, method in exchange_methods:
            if not self._exchange_health.get(exchange_name, True):
                continue  # Skip unhealthy exchanges
            
            try:
                price_data = await method(symbol)
                if price_data:
                    return price_data
            except Exception as e:
                logger.warning(f"Failed to get price from {exchange_name}: {e}")
                continue
        
        return None
    
    async def get_prices_from_all_exchanges(self, symbol: str) -> List[PriceData]:
        """Get prices from all available exchanges for comparison"""
        
        prices = []
        
        # Get from all exchanges concurrently
        tasks = []
        if self._exchange_health.get('binance', True):
            tasks.append(('binance', self.get_binance_price(symbol)))
        if self._exchange_health.get('bybit', True):
            tasks.append(('bybit', self.get_bybit_price(symbol)))
        if self._exchange_health.get('coinbase', True):
            tasks.append(('coinbase', self.get_coinbase_price(symbol)))
        
        if not tasks:
            return prices
        
        results = await asyncio.gather(
            *[task[1] for task in tasks],
            return_exceptions=True
        )
        
        for i, result in enumerate(results):
            if isinstance(result, PriceData):
                prices.append(result)
            elif isinstance(result, Exception):
                exchange_name = tasks[i][0]
                logger.warning(f"Error getting price from {exchange_name}: {result}")
        
        return prices
    
    async def get_market_summary(self, symbols: List[str]) -> Dict[str, Dict]:
        """Get market summary for multiple symbols from best available exchange"""
        
        summary = {}
        
        for symbol in symbols:
            try:
                price_data = await self.get_best_price(symbol)
                if price_data:
                    summary[symbol] = {
                        'price': float(price_data.price),
                        'exchange': price_data.exchange,
                        'timestamp': price_data.timestamp.isoformat(),
                        'volume_24h': float(price_data.volume_24h) if price_data.volume_24h else None,
                        'price_change_24h': float(price_data.price_change_24h) if price_data.price_change_24h else None,
                        'status': 'active'
                    }
                else:
                    summary[symbol] = {
                        'price': None,
                        'exchange': None,
                        'timestamp': datetime.now().isoformat(),
                        'status': 'unavailable'
                    }
            except Exception as e:
                logger.error(f"Error getting market data for {symbol}: {e}")
                summary[symbol] = {
                    'price': None,
                    'exchange': None,
                    'timestamp': datetime.now().isoformat(),
                    'status': 'error',
                    'error': str(e)
                }
        
        return summary
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get health status of all exchanges"""
        
        status = {
            'overall_healthy': any(self._exchange_health.values()),
            'exchanges': {},
            'total_exchanges': len(self.exchanges),
            'healthy_exchanges': sum(self._exchange_health.values()),
            'cache_size': len(self._price_cache)
        }
        
        for exchange_name in self.exchanges.keys():
            status['exchanges'][exchange_name] = {
                'healthy': self._exchange_health.get(exchange_name, True),
                'consecutive_failures': self._consecutive_failures.get(exchange_name, 0),
                'last_successful_request': (
                    self._last_successful_requests[exchange_name].isoformat()
                    if exchange_name in self._last_successful_requests else None
                ),
                'rate_limit_count': self.rate_limits.get(exchange_name, {}).get('requests_count', 0)
            }
        
        return status
    
    def clear_cache(self):
        """Clear all cached data"""
        self._price_cache.clear()
        self._cache_expiry.clear()
        logger.info("Exchange client cache cleared")

# Global instance for ML service
exchange_client = EnhancedExchangeClient()

# Utility functions for backward compatibility
async def get_enhanced_price(symbol: str) -> Optional[Dict]:
    """Get enhanced price data for a symbol"""
    price_data = await exchange_client.get_best_price(symbol)
    
    if price_data:
        return {
            'symbol': price_data.symbol,
            'price': float(price_data.price),
            'exchange': price_data.exchange,
            'timestamp': price_data.timestamp.isoformat(),
            'volume_24h': float(price_data.volume_24h) if price_data.volume_24h else None,
            'price_change_24h': float(price_data.price_change_24h) if price_data.price_change_24h else None
        }
    return None

async def get_multi_exchange_prices(symbol: str) -> List[Dict]:
    """Get prices from multiple exchanges for comparison"""
    prices = await exchange_client.get_prices_from_all_exchanges(symbol)
    
    return [
        {
            'symbol': price.symbol,
            'price': float(price.price),
            'exchange': price.exchange,
            'timestamp': price.timestamp.isoformat(),
            'volume_24h': float(price.volume_24h) if price.volume_24h else None,
            'price_change_24h': float(price.price_change_24h) if price.price_change_24h else None
        }
        for price in prices
    ] 