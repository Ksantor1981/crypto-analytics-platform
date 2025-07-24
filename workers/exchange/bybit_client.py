"""
Enhanced Bybit API Client для получения реальных данных о ценах и торгах
Production-ready version with error handling, caching, and monitoring
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
from contextlib import asynccontextmanager
import sys
import os

# Импорт конфигурации с fallback
try:
    from ..real_data_config import BYBIT_API_KEY, BYBIT_API_SECRET, CRYPTO_SYMBOLS
except ImportError:
    # Fallback for direct execution
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    from real_data_config import BYBIT_API_KEY, BYBIT_API_SECRET, CRYPTO_SYMBOLS

logger = logging.getLogger(__name__)

@dataclass
class BybitRateLimit:
    """Rate limiting information for Bybit API"""
    requests_per_second: int = 10
    requests_per_minute: int = 600
    last_request_time: float = 0
    request_count: int = 0
    reset_time: float = 0

class BybitClient:
    """
    Enhanced Bybit API client for production use
    """
    
    def __init__(self, testnet: bool = False):
        self.api_key = BYBIT_API_KEY
        self.api_secret = BYBIT_API_SECRET
        self.testnet = testnet
        
        # API endpoints
        if testnet:
            self.base_url = "https://api-testnet.bybit.com"
        else:
            self.base_url = "https://api.bybit.com"
            
        self.session = None
        self.rate_limit = BybitRateLimit()
        
        # Cache for price data
        self._price_cache = {}
        self._cache_expiry = {}
        self._cache_ttl = 30  # seconds
        
        # Connection pool settings
        self._connector = None
        self._timeout = aiohttp.ClientTimeout(total=30, connect=10)
        
        # Retry settings
        self._max_retries = 3
        self._retry_delay = 1.0
        
        # Health monitoring
        self._last_successful_request = None
        self._consecutive_failures = 0
        self._max_consecutive_failures = 5
        
        # Bybit interval mapping
        self._interval_mapping = {
            "1": "1",      # 1 minute
            "3": "3",      # 3 minutes
            "5": "5",      # 5 minutes
            "15": "15",    # 15 minutes
            "30": "30",    # 30 minutes
            "60": "60",    # 1 hour
            "120": "120",  # 2 hours
            "240": "240",  # 4 hours
            "360": "360",  # 6 hours
            "720": "720",  # 12 hours
            "D": "D",      # 1 day
            "W": "W",      # 1 week
            "M": "M"       # 1 month
        }
    
    async def __aenter__(self):
        await self._initialize_session()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._cleanup_session()
    
    async def _initialize_session(self):
        """Initialize HTTP session with connection pooling"""
        if self.session is None:
            self._connector = aiohttp.TCPConnector(
                limit=100,
                limit_per_host=10,
                ttl_dns_cache=300,
                use_dns_cache=True,
                keepalive_timeout=30,
                enable_cleanup_closed=True
            )
            
            self.session = aiohttp.ClientSession(
                connector=self._connector,
                timeout=self._timeout,
                headers={
                    'User-Agent': 'CryptoAnalytics/1.0',
                    'Accept': 'application/json',
                    'Content-Type': 'application/json'
                }
            )
            
            logger.info(f"Bybit client initialized ({'testnet' if self.testnet else 'mainnet'})")
    
    async def _cleanup_session(self):
        """Clean up HTTP session and connector"""
        if self.session:
            await self.session.close()
            self.session = None
            
        if self._connector:
            await self._connector.close()
            self._connector = None
    
    def _generate_signature(self, params: str, timestamp: str) -> str:
        """Generate signature for API authentication"""
        param_str = f"{timestamp}{self.api_key}{params}"
        return hmac.new(
            self.api_secret.encode('utf-8'),
            param_str.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    def _get_headers(self, params: str = "") -> Dict[str, str]:
        """Get headers for authenticated requests"""
        timestamp = str(int(time.time() * 1000))
        signature = self._generate_signature(params, timestamp)
        
        return {
            'X-BAPI-API-KEY': self.api_key,
            'X-BAPI-SIGN': signature,
            'X-BAPI-SIGN-TYPE': '2',
            'X-BAPI-TIMESTAMP': timestamp,
            'Content-Type': 'application/json'
        }
    
    async def _rate_limit_check(self):
        """Check and enforce rate limits"""
        current_time = time.time()
        
        # Reset counter if minute has passed
        if current_time - self.rate_limit.reset_time >= 60:
            self.rate_limit.request_count = 0
            self.rate_limit.reset_time = current_time
        
        # Check if we're hitting rate limits
        if self.rate_limit.request_count >= self.rate_limit.requests_per_minute:
            wait_time = 60 - (current_time - self.rate_limit.reset_time)
            logger.warning(f"Rate limit reached, waiting {wait_time:.1f} seconds")
            await asyncio.sleep(wait_time)
            self.rate_limit.request_count = 0
            self.rate_limit.reset_time = time.time()
        
        # Enforce per-second rate limit
        time_since_last = current_time - self.rate_limit.last_request_time
        min_interval = 1.0 / self.rate_limit.requests_per_second
        
        if time_since_last < min_interval:
            wait_time = min_interval - time_since_last
            await asyncio.sleep(wait_time)
        
        self.rate_limit.last_request_time = time.time()
        self.rate_limit.request_count += 1
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached data is still valid"""
        if cache_key not in self._cache_expiry:
            return False
        return time.time() < self._cache_expiry[cache_key]
    
    def _cache_data(self, cache_key: str, data: Any, ttl: int = None):
        """Cache data with expiry"""
        if ttl is None:
            ttl = self._cache_ttl
        
        self._price_cache[cache_key] = data
        self._cache_expiry[cache_key] = time.time() + ttl
    
    def _get_cached_data(self, cache_key: str) -> Optional[Any]:
        """Get cached data if valid"""
        if self._is_cache_valid(cache_key):
            return self._price_cache.get(cache_key)
        return None
    
    async def _make_request(self, method: str, endpoint: str, params: Dict = None, 
                          authenticated: bool = False, use_cache: bool = True) -> Optional[Dict]:
        """Make HTTP request with retry logic and error handling"""
        
        if not self.session:
            await self._initialize_session()
        
        # Check cache first for GET requests
        if method.upper() == 'GET' and use_cache:
            cache_key = f"{endpoint}_{json.dumps(params or {}, sort_keys=True)}"
            cached_data = self._get_cached_data(cache_key)
            if cached_data:
                return cached_data
        
        url = f"{self.base_url}{endpoint}"
        
        for attempt in range(self._max_retries + 1):
            try:
                await self._rate_limit_check()
                
                # Prepare headers
                headers = {}
                if authenticated:
                    param_str = json.dumps(params or {}, separators=(',', ':'))
                    headers = self._get_headers(param_str)
                
                # Make request
                async with self.session.request(
                    method, url, params=params, headers=headers
                ) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        
                        if data.get("retCode") == 0:
                            # Cache successful GET responses
                            if method.upper() == 'GET' and use_cache:
                                self._cache_data(cache_key, data)
                            
                            # Update health monitoring
                            self._last_successful_request = datetime.now()
                            self._consecutive_failures = 0
                            
                            return data
                        else:
                            error_msg = data.get('retMsg', 'Unknown API error')
                            logger.error(f"Bybit API error: {error_msg}")
                            
                            # Don't retry on certain errors
                            if data.get("retCode") in [10001, 10002, 10003]:  # Auth errors
                                break
                                
                    elif response.status == 429:  # Rate limited
                        retry_after = int(response.headers.get('Retry-After', 60))
                        logger.warning(f"Rate limited, waiting {retry_after} seconds")
                        await asyncio.sleep(retry_after)
                        continue
                        
                    else:
                        logger.error(f"HTTP error {response.status}: {await response.text()}")
                        
            except asyncio.TimeoutError:
                logger.error(f"Request timeout on attempt {attempt + 1}")
            except aiohttp.ClientError as e:
                logger.error(f"Client error on attempt {attempt + 1}: {e}")
            except Exception as e:
                logger.error(f"Unexpected error on attempt {attempt + 1}: {e}")
            
            # Wait before retry
            if attempt < self._max_retries:
                wait_time = self._retry_delay * (2 ** attempt)  # Exponential backoff
                await asyncio.sleep(wait_time)
        
        # Update failure count
        self._consecutive_failures += 1
        
        return None
    
    async def get_current_prices(self, symbols: List[str] = None) -> Dict[str, Decimal]:
        """Get current prices for cryptocurrencies with caching"""
        if symbols is None:
            symbols = CRYPTO_SYMBOLS
            
        prices = {}
        
        try:
            data = await self._make_request(
                'GET', 
                '/v5/market/tickers',
                params={"category": "spot"}
            )
            
            if data:
                for ticker in data.get("result", {}).get("list", []):
                    symbol = ticker.get("symbol", "")
                    if symbol in symbols:
                        try:
                            price = Decimal(ticker.get("lastPrice", "0"))
                            prices[symbol] = price
                        except (ValueError, TypeError):
                            continue
                            
                logger.info(f"Retrieved prices for {len(prices)} symbols from Bybit")
            else:
                logger.error("Failed to retrieve prices from Bybit")
                
        except Exception as e:
            logger.error(f"Error fetching prices from Bybit: {e}")
            
        return prices
    
    def _normalize_interval(self, interval: str) -> str:
        """Normalize interval to Bybit API format"""
        # Handle common interval formats
        interval_map = {
            "1m": "1", "1min": "1", "1minute": "1",
            "5m": "5", "5min": "5", "5minutes": "5",
            "15m": "15", "15min": "15", "15minutes": "15",
            "30m": "30", "30min": "30", "30minutes": "30",
            "1h": "60", "1hour": "60", "1hr": "60",
            "4h": "240", "4hour": "240", "4hours": "240",
            "1d": "D", "1day": "D", "1day": "D",
            "1w": "W", "1week": "W", "1week": "W",
            "1M": "M", "1month": "M", "1month": "M"
        }
        
        # Check if interval is already in correct format
        if interval in self._interval_mapping:
            return interval
            
        # Try to map from common formats
        if interval in interval_map:
            return interval_map[interval]
            
        # Default to 1 minute if unknown
        logger.warning(f"Unknown interval format '{interval}', using '1'")
        return "1"

    async def get_klines(self, symbol: str, interval: str = "1", limit: int = 200,
                        start_time: Optional[int] = None, end_time: Optional[int] = None) -> List[Dict]:
        """Get kline/candlestick data with time range support"""
        
        # Normalize interval to Bybit format
        normalized_interval = self._normalize_interval(interval)
        
        params = {
            "category": "spot",
            "symbol": symbol,
            "interval": normalized_interval,
            "limit": min(limit, 1000)  # Bybit max limit
        }
        
        if start_time:
            params["start"] = start_time
        if end_time:
            params["end"] = end_time
        
        try:
            data = await self._make_request('GET', '/v5/market/kline', params=params)
            
            if data:
                klines = []
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
                    except (ValueError, TypeError, IndexError):
                        continue
                        
                logger.info(f"Retrieved {len(klines)} klines for {symbol} (interval: {normalized_interval})")
                return klines
                
        except Exception as e:
            logger.error(f"Error fetching klines from Bybit: {e}")
            
        return []
    
    async def get_market_data(self, symbols: List[str] = None) -> Dict[str, Dict]:
        """Get comprehensive market data with 24h statistics"""
        if symbols is None:
            symbols = CRYPTO_SYMBOLS
            
        market_data = {}
        
        try:
            # Get current prices
            prices = await self.get_current_prices(symbols)
            
            # Get 24h ticker data
            ticker_data = await self._make_request(
                'GET',
                '/v5/market/tickers',
                params={"category": "spot"}
            )
            
            if ticker_data:
                ticker_map = {}
                for ticker in ticker_data.get("result", {}).get("list", []):
                    symbol = ticker.get("symbol", "")
                    if symbol in symbols:
                        ticker_map[symbol] = ticker
                
                # Combine price and ticker data
                for symbol in symbols:
                    if symbol in prices and symbol in ticker_map:
                        ticker = ticker_map[symbol]
                        
                        try:
                            market_data[symbol] = {
                                "symbol": symbol,
                                "current_price": prices[symbol],
                                "change_24h": Decimal(ticker.get("price24hPcnt", "0")) * 100,
                                "high_24h": Decimal(ticker.get("highPrice24h", "0")),
                                "low_24h": Decimal(ticker.get("lowPrice24h", "0")),
                                "volume_24h": Decimal(ticker.get("volume24h", "0")),
                                "turnover_24h": Decimal(ticker.get("turnover24h", "0")),
                                "bid_price": Decimal(ticker.get("bid1Price", "0")),
                                "ask_price": Decimal(ticker.get("ask1Price", "0")),
                                "timestamp": int(time.time()),
                                "source": "bybit"
                            }
                        except (ValueError, TypeError):
                            # Fallback to basic data
                            market_data[symbol] = {
                                "symbol": symbol,
                                "current_price": prices[symbol],
                                "timestamp": int(time.time()),
                                "source": "bybit"
                            }
                            
                logger.info(f"Retrieved market data for {len(market_data)} symbols")
                
        except Exception as e:
            logger.error(f"Error fetching market data from Bybit: {e}")
            
        return market_data
    
    async def test_connection(self) -> bool:
        """Test connection to Bybit API"""
        try:
            data = await self._make_request('GET', '/v5/market/time', use_cache=False)
            
            if data:
                # Get server time - could be string or int
                server_time_raw = data.get("result", {}).get("timeSecond", 0)
                try:
                    server_time = int(server_time_raw) if server_time_raw else 0
                except (ValueError, TypeError):
                    server_time = 0
                
                local_time = int(time.time())
                
                if server_time > 0:
                    time_diff = abs(server_time - local_time)
                    
                    if time_diff > 30:  # More than 30 seconds difference
                        logger.warning(f"Time difference with Bybit server: {time_diff} seconds")
                
                logger.info("Bybit API connection successful")
                return True
            else:
                logger.error("Bybit API connection failed")
                return False
                
        except Exception as e:
            logger.error(f"Error testing Bybit connection: {e}")
            return False
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Get health status of the Bybit client"""
        status = {
            "status": "healthy",
            "last_successful_request": self._last_successful_request,
            "consecutive_failures": self._consecutive_failures,
            "cache_size": len(self._price_cache),
            "rate_limit_remaining": self.rate_limit.requests_per_minute - self.rate_limit.request_count,
            "testnet": self.testnet
        }
        
        # Check if we're having too many failures
        if self._consecutive_failures >= self._max_consecutive_failures:
            status["status"] = "unhealthy"
            status["reason"] = f"Too many consecutive failures ({self._consecutive_failures})"
        
        # Check if last successful request was too long ago
        if self._last_successful_request:
            time_since_success = datetime.now() - self._last_successful_request
            if time_since_success > timedelta(minutes=10):
                status["status"] = "degraded"
                status["reason"] = f"No successful requests for {time_since_success}"
        
        return status
    
    def clear_cache(self):
        """Clear the price cache"""
        self._price_cache.clear()
        self._cache_expiry.clear()
        logger.info("Bybit client cache cleared")

# Context manager for easier usage
@asynccontextmanager
async def bybit_client(testnet: bool = False):
    """Context manager for Bybit client"""
    client = BybitClient(testnet=testnet)
    try:
        async with client:
            yield client
    finally:
        pass

# Enhanced test function
async def test_bybit_integration():
    """Comprehensive test of Bybit integration"""
    print("🧪 Testing Enhanced Bybit Integration...")
    print("=" * 50)
    
    async with bybit_client() as client:
        # Test 1: Connection test
        print("\n1. Testing connection...")
        connection_ok = await client.test_connection()
        print(f"   {'✅' if connection_ok else '❌'} Connection: {'OK' if connection_ok else 'FAILED'}")
        
        if not connection_ok:
            print("   Skipping further tests due to connection failure")
            return False
        
        # Test 2: Health status
        print("\n2. Testing health status...")
        health = await client.get_health_status()
        print(f"   Status: {health['status']}")
        print(f"   Cache size: {health['cache_size']}")
        print(f"   Rate limit remaining: {health['rate_limit_remaining']}")
        
        # Test 3: Get current prices
        print("\n3. Testing current prices...")
        test_symbols = ["BTCUSDT", "ETHUSDT", "ADAUSDT"]
        prices = await client.get_current_prices(test_symbols)
        
        for symbol, price in prices.items():
            print(f"   {symbol}: ${price:,.2f}")
        
        # Test 4: Get klines
        print("\n4. Testing klines...")
        klines = await client.get_klines("BTCUSDT", "1h", 24)
        if klines:
            print(f"   Retrieved {len(klines)} hourly klines for BTCUSDT")
            print(f"   Latest close: ${klines[-1]['close']:,.2f}")
        
        # Test 5: Get market data
        print("\n5. Testing market data...")
        market_data = await client.get_market_data(["BTCUSDT"])
        
        if "BTCUSDT" in market_data:
            data = market_data["BTCUSDT"]
            print(f"   BTCUSDT:")
            print(f"     Price: ${data['current_price']:,.2f}")
            print(f"     24h Change: {data.get('change_24h', 0):+.2f}%")
            print(f"     24h High: ${data.get('high_24h', 0):,.2f}")
            print(f"     24h Low: ${data.get('low_24h', 0):,.2f}")
        
        # Test 6: Cache performance
        print("\n6. Testing cache performance...")
        start_time = time.time()
        prices1 = await client.get_current_prices(["BTCUSDT"])
        first_request_time = time.time() - start_time
        
        start_time = time.time()
        prices2 = await client.get_current_prices(["BTCUSDT"])
        cached_request_time = time.time() - start_time
        
        print(f"   First request: {first_request_time:.3f}s")
        print(f"   Cached request: {cached_request_time:.3f}s")
        print(f"   Cache speedup: {first_request_time/cached_request_time:.1f}x")
        
        print("\n" + "=" * 50)
        print("✅ Bybit integration tests completed!")
        
        return True

if __name__ == "__main__":
    asyncio.run(test_bybit_integration()) 