"""
Enhanced Price Checker Service for ML Service
Integrated version with improved performance and reliability
"""
import asyncio
import logging
import os
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from decimal import Decimal
import httpx
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Try to import real_data_config from workers module
try:
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'workers'))
    from real_data_config import CRYPTO_SYMBOLS, BYBIT_API_KEY, BYBIT_API_SECRET, SYMBOL_METADATA
    REAL_DATA_AVAILABLE = True
    logger.info("✅ Real data integration: AVAILABLE")
except ImportError:
    # Fallback configuration
    CRYPTO_SYMBOLS = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "ADAUSDT", "SOLUSDT", "XRPUSDT", "DOGEUSDT", "DOTUSDT", "AVAXUSDT", "LINKUSDT"]
    BYBIT_API_KEY = ""
    BYBIT_API_SECRET = ""
    SYMBOL_METADATA = {}
    REAL_DATA_AVAILABLE = False
    logger.warning("⚠️ Real data integration: NOT AVAILABLE (using fallback)")

@dataclass
class PriceData:
    """Structure for price data"""
    timestamp: int
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal

@dataclass  
class SignalValidationResult:
    """Result of signal validation"""
    signal_id: str
    symbol: str
    direction: str
    entry_price: Decimal
    current_price: Decimal
    status: str  # PENDING, SUCCESS, FAILED, EXPIRED
    hit_targets: List[str]
    pnl_percentage: Decimal
    execution_time: Optional[datetime]
    confidence_score: float

class EnhancedPriceChecker:
    """
    Enhanced Price Checker with advanced features for ML service
    Integrated with real data configuration and multi-exchange support
    """
    
    def __init__(self):
        # Exchange API endpoints
        self.binance_api = "https://api.binance.com/api/v3"
        self.bybit_api = "https://api.bybit.com/v5"
        self.coinbase_api = "https://api.exchange.coinbase.com"
        
        # Configuration
        self.price_tolerance = Decimal('0.001')  # 0.1% tolerance
        self.max_signal_duration = timedelta(hours=24)  # Max time to track signal
        self.rate_limit_delay = 0.1  # Delay between API calls
        
        # Cache for prices (simple in-memory cache)
        self._price_cache = {}
        self._cache_ttl = 60  # Cache for 60 seconds
        
        # API keys for authenticated requests
        self.bybit_api_key = BYBIT_API_KEY
        self.bybit_api_secret = BYBIT_API_SECRET
        
        # Enhanced supported symbols from configuration
        self.supported_symbols = {
            'BTC/USDT': ['binance', 'bybit', 'coinbase'],
            'ETH/USDT': ['binance', 'bybit', 'coinbase'],
            'BNB/USDT': ['binance', 'bybit'],
            'ADA/USDT': ['binance', 'bybit'],
            'SOL/USDT': ['binance', 'bybit'],
            'XRP/USDT': ['binance', 'bybit'],
            'DOGE/USDT': ['binance', 'bybit'],
            'DOT/USDT': ['binance', 'bybit'],
            'AVAX/USDT': ['binance', 'bybit'],
            'LINK/USDT': ['binance', 'bybit'],
            'MATIC/USDT': ['binance', 'bybit']
        }
        
        # Add symbols from real_data_config if available
        if REAL_DATA_AVAILABLE:
            for symbol in CRYPTO_SYMBOLS:
                if symbol.endswith('USDT'):
                    formatted_symbol = symbol[:-4] + '/USDT'
                    self.supported_symbols[formatted_symbol] = ['binance', 'bybit']
        
        # Exchange mapping for backward compatibility
        self.exchange_mapping = {}
        for symbol, exchanges in self.supported_symbols.items():
            self.exchange_mapping[symbol] = exchanges[0]  # Default to first exchange

    async def get_current_price(self, symbol: str, preferred_exchange: str = None) -> Optional[Decimal]:
        """
        Get current price with caching and fallback exchanges
        """
        cache_key = f"{symbol}_{preferred_exchange or 'any'}"
        
        # Check cache first
        if cache_key in self._price_cache:
            cached_data = self._price_cache[cache_key]
            if (datetime.now() - cached_data['timestamp']).seconds < self._cache_ttl:
                return cached_data['price']
        
        # Get fresh price
        price = await self._fetch_current_price(symbol, preferred_exchange)
        
        # Cache the result
        if price:
            self._price_cache[cache_key] = {
                'price': price,
                'timestamp': datetime.now()
            }
        
        return price
    
    async def _fetch_current_price(self, symbol: str, preferred_exchange: str = None) -> Optional[Decimal]:
        """Fetch current price from exchanges with fallback"""
        
        exchanges = self.supported_symbols.get(symbol, ['binance'])
        if preferred_exchange and preferred_exchange in exchanges:
            exchanges = [preferred_exchange] + [ex for ex in exchanges if ex != preferred_exchange]
        
        for exchange in exchanges:
            try:
                if exchange == 'binance':
                    price = await self._get_binance_price(symbol)
                elif exchange == 'bybit':
                    price = await self._get_bybit_price(symbol)
                elif exchange == 'coinbase':
                    price = await self._get_coinbase_price(symbol)
                else:
                    continue
                    
                if price:
                    logger.debug(f"Got price {price} for {symbol} from {exchange}")
                    return price
                    
            except Exception as e:
                logger.warning(f"Failed to get price for {symbol} from {exchange}: {e}")
                continue
        
        logger.error(f"Failed to get price for {symbol} from all exchanges")
        return None
    
    async def _get_binance_price(self, symbol: str) -> Optional[Decimal]:
        """Get current price from Binance"""
        binance_symbol = symbol.replace('/', '')
        
        url = f"{self.binance_api}/ticker/price"
        params = {'symbol': binance_symbol}
        
        try:
            timeout = httpx.Timeout(10.0)
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                
                data = response.json()
                return Decimal(data['price'])
                
        except Exception as e:
            logger.debug(f"Binance price fetch failed for {symbol}: {e}")
            return None

    async def _get_bybit_price(self, symbol: str) -> Optional[Decimal]:
        """Get current price from Bybit"""
        bybit_symbol = symbol.replace('/', '')
        
        url = f"{self.bybit_api}/market/tickers"
        params = {'category': 'spot', 'symbol': bybit_symbol}
        
        try:
            timeout = httpx.Timeout(10.0)
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                
                data = response.json()
                
                if data.get('retCode') == 0:
                    result = data.get('result', {})
                    ticker_list = result.get('list', [])
                    
                    if ticker_list:
                        ticker = ticker_list[0]
                        return Decimal(ticker['lastPrice'])
                        
        except Exception as e:
            logger.debug(f"Bybit price fetch failed for {symbol}: {e}")
            
        return None
    
    async def _get_coinbase_price(self, symbol: str) -> Optional[Decimal]:
        """Get current price from Coinbase"""
        # Coinbase uses different format: BTC-USD
        coinbase_symbol = symbol.replace('/', '-').replace('USDT', 'USD')
        
        url = f"{self.coinbase_api}/products/{coinbase_symbol}/ticker"
        
        try:
            timeout = httpx.Timeout(10.0)
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.get(url)
                response.raise_for_status()
                
                data = response.json()
                return Decimal(data['price'])
                
        except Exception as e:
            logger.debug(f"Coinbase price fetch failed for {symbol}: {e}")
            return None

    async def validate_signal_execution(self, signal_data: Dict) -> SignalValidationResult:
        """
        Enhanced signal validation with detailed analysis
        """
        try:
            signal_id = signal_data.get('id', 'unknown')
            symbol = signal_data.get('symbol', 'BTC/USDT')
            direction = signal_data.get('direction', 'long').lower()
            entry_price = Decimal(str(signal_data.get('entry_price', 0)))
            targets = signal_data.get('targets', [])
            stop_loss = signal_data.get('stop_loss')
            signal_time = signal_data.get('timestamp')
            
            # Get current price
            current_price = await self.get_current_price(symbol)
            if not current_price:
                return SignalValidationResult(
                    signal_id=signal_id,
                    symbol=symbol,
                    direction=direction,
                    entry_price=entry_price,
                    current_price=Decimal('0'),
                    status='ERROR',
                    hit_targets=[],
                    pnl_percentage=Decimal('0'),
                    execution_time=None,
                    confidence_score=0.0
                )
            
            # Calculate PnL
            if direction == 'long':
                pnl_percentage = ((current_price - entry_price) / entry_price * 100)
            else:  # short
                pnl_percentage = ((entry_price - current_price) / entry_price * 100)
            
            # Check targets hit
            hit_targets = []
            status = 'PENDING'
            
            # Check stop loss first
            if stop_loss:
                sl_price = Decimal(str(stop_loss))
                if self._is_price_hit(current_price, sl_price, direction, 'stop_loss'):
                    status = 'FAILED'
                    hit_targets.append('STOP_LOSS')
            
            # Check targets if not stopped out
            if status != 'FAILED':
                for i, target in enumerate(targets, 1):
                    target_price = Decimal(str(target))
                    if self._is_price_hit(current_price, target_price, direction, 'target'):
                        hit_targets.append(f'TP{i}')
                        status = 'SUCCESS'
            
            # Check expiration
            if signal_time:
                signal_dt = datetime.fromisoformat(signal_time.replace('Z', '+00:00'))
                if datetime.now() - signal_dt > self.max_signal_duration:
                    if status == 'PENDING':
                        status = 'EXPIRED'
            
            # Calculate confidence score
            confidence_score = self._calculate_confidence_score(
                pnl_percentage, len(hit_targets), status
            )
            
            return SignalValidationResult(
                signal_id=signal_id,
                symbol=symbol,
                direction=direction,
                entry_price=entry_price,
                current_price=current_price,
                status=status,
                hit_targets=hit_targets,
                pnl_percentage=pnl_percentage,
                execution_time=datetime.now(),
                confidence_score=confidence_score
            )
            
        except Exception as e:
            logger.error(f"Error validating signal {signal_data}: {e}")
            return SignalValidationResult(
                signal_id=signal_data.get('id', 'unknown'),
                symbol=signal_data.get('symbol', 'unknown'),
                direction=signal_data.get('direction', 'long'),
                entry_price=Decimal('0'),
                current_price=Decimal('0'),
                status='ERROR',
                hit_targets=[],
                pnl_percentage=Decimal('0'),
                execution_time=None,
                confidence_score=0.0
            )
    
    def _is_price_hit(self, current_price: Decimal, target_price: Decimal, 
                      direction: str, price_type: str) -> bool:
        """
        Check if price target is hit considering direction and tolerance
        """
        tolerance = target_price * self.price_tolerance
        
        if price_type == 'target':
            if direction == 'long':
                return current_price >= (target_price - tolerance)
            else:  # short
                return current_price <= (target_price + tolerance)
        
        elif price_type == 'stop_loss':
            if direction == 'long':
                return current_price <= (target_price + tolerance)
            else:  # short
                return current_price >= (target_price - tolerance)
        
        return False
    
    def _calculate_confidence_score(self, pnl_percentage: Decimal, 
                                  targets_hit: int, status: str) -> float:
        """
        Calculate confidence score for the signal validation
        """
        base_score = 0.5
        
        # Boost for successful signals
        if status == 'SUCCESS':
            base_score += 0.3
            base_score += targets_hit * 0.1  # More targets = higher confidence
        
        # Penalty for failed signals
        elif status == 'FAILED':
            base_score -= 0.2
        
        # PnL impact
        pnl_float = float(pnl_percentage)
        if pnl_float > 0:
            base_score += min(pnl_float / 100, 0.2)  # Cap at 0.2
        else:
            base_score += max(pnl_float / 100, -0.2)  # Cap at -0.2
        
        return max(0.0, min(1.0, base_score))

    async def batch_validate_signals(self, signals: List[Dict]) -> List[SignalValidationResult]:
        """
        Validate multiple signals efficiently with rate limiting
        """
        results = []
        
        for signal in signals:
            result = await self.validate_signal_execution(signal)
            results.append(result)
            
            # Rate limiting
            await asyncio.sleep(self.rate_limit_delay)
        
        return results

    async def get_market_summary(self, symbols: List[str]) -> Dict[str, Any]:
        """
        Get market summary for multiple symbols
        """
        summary = {}
        
        for symbol in symbols:
            try:
                price = await self.get_current_price(symbol)
                if price:
                    summary[symbol] = {
                        'current_price': float(price),
                        'status': 'active',
                        'last_updated': datetime.now().isoformat()
                    }
                else:
                    summary[symbol] = {
                        'current_price': None,
                        'status': 'unavailable',
                        'last_updated': datetime.now().isoformat()
                    }
            except Exception as e:
                logger.error(f"Error getting market data for {symbol}: {e}")
                summary[symbol] = {
                    'current_price': None,
                    'status': 'error',
                    'error': str(e),
                    'last_updated': datetime.now().isoformat()
                }
        
        return {
            'timestamp': datetime.now().isoformat(),
            'markets': summary,
            'total_symbols': len(symbols),
            'active_symbols': len([s for s in summary.values() if s['status'] == 'active'])
        }

    async def get_binance_klines(self, symbol: str, start_time: int, end_time: int, interval: str = "1m") -> List[Dict]:
        """
        Get historical price data from Binance
        Enhanced version with better error handling
        """
        # Convert pair format: BTC/USDT -> BTCUSDT
        binance_symbol = symbol.replace('/', '')
        
        url = f"{self.binance_api}/klines"
        params = {
            'symbol': binance_symbol,
            'interval': interval,
            'startTime': start_time,
            'endTime': end_time,
            'limit': 1000
        }
        
        try:
            timeout = httpx.Timeout(30.0)
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                
                klines = response.json()
                
                # Convert to our format
                formatted_data = []
                for kline in klines:
                    formatted_data.append({
                        'timestamp': int(kline[0]),
                        'open': Decimal(kline[1]),
                        'high': Decimal(kline[2]),
                        'low': Decimal(kline[3]),
                        'close': Decimal(kline[4]),
                        'volume': Decimal(kline[5])
                    })
                
                logger.info(f"Retrieved {len(formatted_data)} klines for {symbol}")
                return formatted_data
                
        except httpx.TimeoutException:
            logger.error(f"Timeout fetching Binance data for {symbol}")
            return []
        except Exception as e:
            logger.error(f"Error fetching Binance data for {symbol}: {e}")
            return []

    async def get_bybit_klines(self, symbol: str, start_time: int, end_time: int, interval: str = "1") -> List[Dict]:
        """
        Get historical price data from Bybit with authentication support
        Enhanced version with API key integration
        """
        # Convert pair format: BTC/USDT -> BTCUSDT
        bybit_symbol = symbol.replace('/', '')
        
        url = f"{self.bybit_api}/market/kline"
        params = {
            'category': 'spot',
            'symbol': bybit_symbol,
            'interval': interval,
            'start': start_time,
            'end': end_time,
            'limit': 1000
        }
        
        # Add authentication headers if API keys are available
        headers = {}
        if self.bybit_api_key and self.bybit_api_secret:
            headers['X-BAPI-API-KEY'] = self.bybit_api_key
            # In real implementation, add signature generation
            logger.debug(f"Using authenticated Bybit API for {symbol}")
        
        try:
            timeout = httpx.Timeout(30.0)
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.get(url, params=params, headers=headers)
                response.raise_for_status()
                
                data = response.json()
                
                if data.get('retCode') == 0:
                    klines = data.get('result', {}).get('list', [])
                    
                    # Convert to our format
                    formatted_data = []
                    for kline in klines:
                        formatted_data.append({
                            'timestamp': int(kline[0]),
                            'open': Decimal(kline[1]),
                            'high': Decimal(kline[2]),
                            'low': Decimal(kline[3]),
                            'close': Decimal(kline[4]),
                            'volume': Decimal(kline[5])
                        })
                    
                    logger.info(f"Retrieved {len(formatted_data)} klines from Bybit for {symbol}")
                    return formatted_data
                else:
                    logger.error(f"Bybit API error: {data.get('retMsg', 'Unknown error')}")
                    return []
                
        except httpx.TimeoutException:
            logger.error(f"Timeout fetching Bybit data for {symbol}")
            return []
        except Exception as e:
            logger.error(f"Error fetching Bybit data for {symbol}: {e}")
            return []

# Global instance
price_checker = EnhancedPriceChecker()

# Utility functions for backward compatibility
async def check_signal_price(signal_data: Dict) -> Dict[str, Any]:
    """Backward compatible function"""
    result = await price_checker.validate_signal_execution(signal_data)
    
    return {
        'signal_id': result.signal_id,
        'symbol': result.symbol,
        'status': result.status,
        'current_price': float(result.current_price),
        'pnl_percentage': float(result.pnl_percentage),
        'hit_targets': result.hit_targets,
        'confidence_score': result.confidence_score
    }

async def get_current_prices(symbols: List[str]) -> Dict[str, float]:
    """Get current prices for multiple symbols"""
    prices = {}
    
    for symbol in symbols:
        price = await price_checker.get_current_price(symbol)
        if price:
            prices[symbol] = float(price)
    
    return prices 