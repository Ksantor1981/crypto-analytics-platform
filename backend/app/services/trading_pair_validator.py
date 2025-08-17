"""
Trading Pair Validator - Comprehensive validation system
Part of Task 1.2: Реализация comprehensive валидации
"""
import asyncio
import logging
import aiohttp
from typing import Dict, List, Any, Optional, Set
from datetime import datetime, timedelta
from decimal import Decimal
import json

logger = logging.getLogger(__name__)

class TradingPairValidator:
    """
    Comprehensive trading pair validation system
    Validates existence, liquidity, and market conditions
    """
    
    def __init__(self):
        # Exchange API endpoints
        self.exchanges = {
            'binance': {
                'base_url': 'https://api.binance.com/api/v3',
                'symbols_endpoint': '/exchangeInfo',
                'ticker_endpoint': '/ticker/24hr',
                'price_endpoint': '/ticker/price',
                'weight_limit': 1200  # requests per minute
            },
            'bybit': {
                'base_url': 'https://api.bybit.com/v5',
                'symbols_endpoint': '/market/instruments-info',
                'ticker_endpoint': '/market/tickers',
                'price_endpoint': '/market/tickers',
                'weight_limit': 600
            },
            'coinbase': {
                'base_url': 'https://api.exchange.coinbase.com',
                'symbols_endpoint': '/products',
                'ticker_endpoint': '/products/{symbol}/ticker',
                'weight_limit': 300
            }
        }
        
        # Cache for validation results
        self._validation_cache = {}
        self._cache_ttl = 300  # 5 minutes
        
        # Supported pairs by category
        self.supported_pairs = {
            'major': [
                'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'SOLUSDT',
                'XRPUSDT', 'DOTUSDT', 'DOGEUSDT', 'AVAXUSDT', 'LINKUSDT'
            ],
            'altcoins': [
                'MATICUSDT', 'UNIUSDT', 'ATOMUSDT', 'LTCUSDT', 'BCHUSDT',
                'ETCUSDT', 'FILUSDT', 'NEARUSDT', 'ALGOUSDT', 'VETUSDT'
            ],
            'defi': [
                'AAVEUSDT', 'COMPUSDT', 'MKRUSDT', 'SUSHIUSDT', 'CRVUSDT',
                'YFIUSDT', 'SNXUSDT', 'BALUSDT', 'RENUSDT', 'ZRXUSDT'
            ],
            'meme': [
                'SHIBUSDT', 'PEPEUSDT', 'FLOKIUSDT', 'BONKUSDT', 'WIFUSDT',
                'MYROUSDT', 'POPCATUSDT', 'BOOKUSDT', 'TURBOUSDT', 'MOONUSDT'
            ],
            'new_listings': []  # Dynamic list
        }
        
        # Liquidity thresholds
        self.liquidity_thresholds = {
            'high': 1000000,      # $1M+ daily volume
            'medium': 100000,     # $100K+ daily volume
            'low': 10000,         # $10K+ daily volume
            'very_low': 1000      # $1K+ daily volume
        }
        
        # Price change thresholds for volatility check
        self.volatility_thresholds = {
            'extreme': 0.20,      # 20%+ price change
            'high': 0.10,         # 10%+ price change
            'medium': 0.05,       # 5%+ price change
            'low': 0.02           # 2%+ price change
        }
    
    async def validate_trading_pair(self, pair: str) -> Dict[str, Any]:
        """
        Comprehensive validation of trading pair
        """
        # Check cache first
        cache_key = f"validation_{pair}"
        if cache_key in self._validation_cache:
            cached_result = self._validation_cache[cache_key]
            if datetime.now() - cached_result['timestamp'] < timedelta(seconds=self._cache_ttl):
                return cached_result['data']
        
        validation_result = {
            'pair': pair,
            'is_valid': False,
            'exists_on_exchanges': [],
            'liquidity_score': 0.0,
            'volatility_level': 'unknown',
            'price_accuracy': 'unknown',
            'recommendations': [],
            'warnings': [],
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            # Step 1: Check if pair exists on exchanges
            exchange_status = await self._check_exchange_availability(pair)
            validation_result['exists_on_exchanges'] = exchange_status['available_exchanges']
            
            if not exchange_status['available_exchanges']:
                validation_result['warnings'].append(f"Pair {pair} not found on any supported exchange")
                validation_result['recommendations'].append("Check if pair symbol is correct")
                return validation_result
            
            # Step 2: Check liquidity
            liquidity_data = await self._check_liquidity(pair, exchange_status['available_exchanges'])
            validation_result['liquidity_score'] = liquidity_data['score']
            validation_result['daily_volume'] = liquidity_data['daily_volume']
            
            if liquidity_data['score'] < 0.3:
                validation_result['warnings'].append(f"Low liquidity for {pair}")
                validation_result['recommendations'].append("Consider higher liquidity pairs for better execution")
            
            # Step 3: Check volatility
            volatility_data = await self._check_volatility(pair, exchange_status['available_exchanges'])
            validation_result['volatility_level'] = volatility_data['level']
            validation_result['price_change_24h'] = volatility_data['price_change_24h']
            
            if volatility_data['level'] == 'extreme':
                validation_result['warnings'].append(f"Extreme volatility detected for {pair}")
                validation_result['recommendations'].append("Consider reducing position size or waiting for stabilization")
            
            # Step 4: Check price accuracy
            price_accuracy = await self._check_price_accuracy(pair, exchange_status['available_exchanges'])
            validation_result['price_accuracy'] = price_accuracy['accuracy']
            validation_result['price_spread'] = price_accuracy['spread']
            
            if price_accuracy['accuracy'] == 'low':
                validation_result['warnings'].append(f"High price spread for {pair}")
                validation_result['recommendations'].append("Consider using limit orders instead of market orders")
            
            # Step 5: Determine overall validity
            validation_result['is_valid'] = (
                len(validation_result['exists_on_exchanges']) > 0 and
                validation_result['liquidity_score'] > 0.1 and
                validation_result['volatility_level'] != 'extreme'
            )
            
            # Cache the result
            self._validation_cache[cache_key] = {
                'data': validation_result,
                'timestamp': datetime.now()
            }
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Error validating pair {pair}: {e}")
            validation_result['warnings'].append(f"Validation error: {str(e)}")
            return validation_result
    
    async def _check_exchange_availability(self, pair: str) -> Dict[str, Any]:
        """Check if pair exists on supported exchanges"""
        available_exchanges = []
        
        async with aiohttp.ClientSession() as session:
            for exchange_name, exchange_config in self.exchanges.items():
                try:
                    if exchange_name == 'binance':
                        is_available = await self._check_binance_availability(session, pair, exchange_config)
                    elif exchange_name == 'bybit':
                        is_available = await self._check_bybit_availability(session, pair, exchange_config)
                    elif exchange_name == 'coinbase':
                        is_available = await self._check_coinbase_availability(session, pair, exchange_config)
                    else:
                        continue
                    
                    if is_available:
                        available_exchanges.append(exchange_name)
                        
                except Exception as e:
                    logger.warning(f"Error checking {exchange_name} for {pair}: {e}")
                    continue
        
        return {
            'available_exchanges': available_exchanges,
            'total_exchanges_checked': len(self.exchanges)
        }
    
    async def _check_binance_availability(self, session: aiohttp.ClientSession, pair: str, config: Dict) -> bool:
        """Check if pair is available on Binance"""
        try:
            url = f"{config['base_url']}{config['symbols_endpoint']}"
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    symbols = data.get('symbols', [])
                    
                    for symbol in symbols:
                        if (symbol['symbol'] == pair and 
                            symbol['status'] == 'TRADING' and
                            symbol['isSpotTradingAllowed']):
                            return True
                    
                    return False
                else:
                    return False
        except Exception as e:
            logger.warning(f"Error checking Binance availability: {e}")
            return False
    
    async def _check_bybit_availability(self, session: aiohttp.ClientSession, pair: str, config: Dict) -> bool:
        """Check if pair is available on Bybit"""
        try:
            url = f"{config['base_url']}{config['symbols_endpoint']}"
            params = {'category': 'spot'}
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    instruments = data.get('result', {}).get('list', [])
                    
                    for instrument in instruments:
                        if (instrument['symbol'] == pair and 
                            instrument['status'] == 'Trading'):
                            return True
                    
                    return False
                else:
                    return False
        except Exception as e:
            logger.warning(f"Error checking Bybit availability: {e}")
            return False
    
    async def _check_coinbase_availability(self, session: aiohttp.ClientSession, pair: str, config: Dict) -> bool:
        """Check if pair is available on Coinbase"""
        try:
            url = f"{config['base_url']}{config['symbols_endpoint']}"
            
            async with session.get(url) as response:
                if response.status == 200:
                    products = await response.json()
                    
                    for product in products:
                        if (product['id'] == pair and 
                            product['status'] == 'online'):
                            return True
                    
                    return False
                else:
                    return False
        except Exception as e:
            logger.warning(f"Error checking Coinbase availability: {e}")
            return False
    
    async def _check_liquidity(self, pair: str, exchanges: List[str]) -> Dict[str, Any]:
        """Check liquidity across exchanges"""
        total_volume = 0.0
        exchange_volumes = {}
        
        async with aiohttp.ClientSession() as session:
            for exchange in exchanges:
                try:
                    if exchange == 'binance':
                        volume = await self._get_binance_volume(session, pair)
                    elif exchange == 'bybit':
                        volume = await self._get_bybit_volume(session, pair)
                    elif exchange == 'coinbase':
                        volume = await self._get_coinbase_volume(session, pair)
                    else:
                        continue
                    
                    if volume > 0:
                        exchange_volumes[exchange] = volume
                        total_volume += volume
                        
                except Exception as e:
                    logger.warning(f"Error getting volume from {exchange}: {e}")
                    continue
        
        # Calculate liquidity score
        liquidity_score = 0.0
        if total_volume >= self.liquidity_thresholds['high']:
            liquidity_score = 1.0
        elif total_volume >= self.liquidity_thresholds['medium']:
            liquidity_score = 0.7
        elif total_volume >= self.liquidity_thresholds['low']:
            liquidity_score = 0.4
        elif total_volume >= self.liquidity_thresholds['very_low']:
            liquidity_score = 0.2
        else:
            liquidity_score = 0.1
        
        return {
            'score': liquidity_score,
            'daily_volume': total_volume,
            'exchange_volumes': exchange_volumes
        }
    
    async def _get_binance_volume(self, session: aiohttp.ClientSession, pair: str) -> float:
        """Get 24h volume from Binance"""
        try:
            url = f"https://api.binance.com/api/v3/ticker/24hr"
            params = {'symbol': pair}
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return float(data.get('quoteVolume', 0))
                return 0.0
        except Exception as e:
            logger.warning(f"Error getting Binance volume: {e}")
            return 0.0
    
    async def _get_bybit_volume(self, session: aiohttp.ClientSession, pair: str) -> float:
        """Get 24h volume from Bybit"""
        try:
            url = f"https://api.bybit.com/v5/market/tickers"
            params = {'category': 'spot', 'symbol': pair}
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    tickers = data.get('result', {}).get('list', [])
                    if tickers:
                        return float(tickers[0].get('turnover24h', 0))
                return 0.0
        except Exception as e:
            logger.warning(f"Error getting Bybit volume: {e}")
            return 0.0
    
    async def _get_coinbase_volume(self, session: aiohttp.ClientSession, pair: str) -> float:
        """Get 24h volume from Coinbase"""
        try:
            url = f"https://api.exchange.coinbase.com/products/{pair}/stats"
            
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return float(data.get('volume', 0))
                return 0.0
        except Exception as e:
            logger.warning(f"Error getting Coinbase volume: {e}")
            return 0.0
    
    async def _check_volatility(self, pair: str, exchanges: List[str]) -> Dict[str, Any]:
        """Check price volatility"""
        price_changes = []
        
        async with aiohttp.ClientSession() as session:
            for exchange in exchanges:
                try:
                    if exchange == 'binance':
                        change = await self._get_binance_price_change(session, pair)
                    elif exchange == 'bybit':
                        change = await self._get_bybit_price_change(session, pair)
                    elif exchange == 'coinbase':
                        change = await self._get_coinbase_price_change(session, pair)
                    else:
                        continue
                    
                    if change is not None:
                        price_changes.append(abs(change))
                        
                except Exception as e:
                    logger.warning(f"Error getting price change from {exchange}: {e}")
                    continue
        
        if not price_changes:
            return {
                'level': 'unknown',
                'price_change_24h': 0.0
            }
        
        avg_change = sum(price_changes) / len(price_changes)
        
        # Determine volatility level
        if avg_change >= self.volatility_thresholds['extreme']:
            level = 'extreme'
        elif avg_change >= self.volatility_thresholds['high']:
            level = 'high'
        elif avg_change >= self.volatility_thresholds['medium']:
            level = 'medium'
        elif avg_change >= self.volatility_thresholds['low']:
            level = 'low'
        else:
            level = 'very_low'
        
        return {
            'level': level,
            'price_change_24h': avg_change
        }
    
    async def _get_binance_price_change(self, session: aiohttp.ClientSession, pair: str) -> Optional[float]:
        """Get 24h price change from Binance"""
        try:
            url = f"https://api.binance.com/api/v3/ticker/24hr"
            params = {'symbol': pair}
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return float(data.get('priceChangePercent', 0))
                return None
        except Exception as e:
            logger.warning(f"Error getting Binance price change: {e}")
            return None
    
    async def _get_bybit_price_change(self, session: aiohttp.ClientSession, pair: str) -> Optional[float]:
        """Get 24h price change from Bybit"""
        try:
            url = f"https://api.bybit.com/v5/market/tickers"
            params = {'category': 'spot', 'symbol': pair}
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    tickers = data.get('result', {}).get('list', [])
                    if tickers:
                        return float(tickers[0].get('price24hPcnt', 0)) * 100
                return None
        except Exception as e:
            logger.warning(f"Error getting Bybit price change: {e}")
            return None
    
    async def _get_coinbase_price_change(self, session: aiohttp.ClientSession, pair: str) -> Optional[float]:
        """Get 24h price change from Coinbase"""
        try:
            url = f"https://api.exchange.coinbase.com/products/{pair}/stats"
            
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    open_price = float(data.get('open', 0))
                    last_price = float(data.get('last', 0))
                    
                    if open_price > 0:
                        return ((last_price - open_price) / open_price) * 100
                return None
        except Exception as e:
            logger.warning(f"Error getting Coinbase price change: {e}")
            return None
    
    async def _check_price_accuracy(self, pair: str, exchanges: List[str]) -> Dict[str, Any]:
        """Check price accuracy and spread"""
        prices = []
        
        async with aiohttp.ClientSession() as session:
            for exchange in exchanges:
                try:
                    if exchange == 'binance':
                        price = await self._get_binance_price(session, pair)
                    elif exchange == 'bybit':
                        price = await self._get_bybit_price(session, pair)
                    elif exchange == 'coinbase':
                        price = await self._get_coinbase_price(session, pair)
                    else:
                        continue
                    
                    if price > 0:
                        prices.append(price)
                        
                except Exception as e:
                    logger.warning(f"Error getting price from {exchange}: {e}")
                    continue
        
        if len(prices) < 2:
            return {
                'accuracy': 'unknown',
                'spread': 0.0
            }
        
        # Calculate price spread
        min_price = min(prices)
        max_price = max(prices)
        avg_price = sum(prices) / len(prices)
        
        if avg_price > 0:
            spread = (max_price - min_price) / avg_price
        else:
            spread = 0.0
        
        # Determine accuracy level
        if spread <= 0.001:  # 0.1% or less
            accuracy = 'high'
        elif spread <= 0.01:  # 1% or less
            accuracy = 'medium'
        else:
            accuracy = 'low'
        
        return {
            'accuracy': accuracy,
            'spread': spread,
            'min_price': min_price,
            'max_price': max_price,
            'avg_price': avg_price
        }
    
    async def _get_binance_price(self, session: aiohttp.ClientSession, pair: str) -> float:
        """Get current price from Binance"""
        try:
            url = f"https://api.binance.com/api/v3/ticker/price"
            params = {'symbol': pair}
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return float(data.get('price', 0))
                return 0.0
        except Exception as e:
            logger.warning(f"Error getting Binance price: {e}")
            return 0.0
    
    async def _get_bybit_price(self, session: aiohttp.ClientSession, pair: str) -> float:
        """Get current price from Bybit"""
        try:
            url = f"https://api.bybit.com/v5/market/tickers"
            params = {'category': 'spot', 'symbol': pair}
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    tickers = data.get('result', {}).get('list', [])
                    if tickers:
                        return float(tickers[0].get('lastPrice', 0))
                return 0.0
        except Exception as e:
            logger.warning(f"Error getting Bybit price: {e}")
            return 0.0
    
    async def _get_coinbase_price(self, session: aiohttp.ClientSession, pair: str) -> float:
        """Get current price from Coinbase"""
        try:
            url = f"https://api.exchange.coinbase.com/products/{pair}/ticker"
            
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return float(data.get('price', 0))
                return 0.0
        except Exception as e:
            logger.warning(f"Error getting Coinbase price: {e}")
            return 0.0
    
    def validate_signal_format(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """Validate signal format and required fields"""
        validation_result = {
            'is_valid': False,
            'missing_fields': [],
            'invalid_fields': [],
            'warnings': [],
            'recommendations': []
        }
        
        # Required fields
        required_fields = ['symbol', 'signal_type', 'entry_price']
        optional_fields = ['target_price', 'stop_loss', 'leverage', 'confidence']
        
        # Check required fields
        for field in required_fields:
            if field not in signal or signal[field] is None:
                validation_result['missing_fields'].append(field)
        
        # Check field types and values
        if 'symbol' in signal:
            if not isinstance(signal['symbol'], str) or len(signal['symbol']) < 3:
                validation_result['invalid_fields'].append('symbol')
        
        if 'signal_type' in signal:
            if signal['signal_type'] not in ['LONG', 'SHORT', 'BUY', 'SELL']:
                validation_result['invalid_fields'].append('signal_type')
        
        if 'entry_price' in signal:
            try:
                price = float(signal['entry_price'])
                if price <= 0:
                    validation_result['invalid_fields'].append('entry_price')
            except (ValueError, TypeError):
                validation_result['invalid_fields'].append('entry_price')
        
        # Check price logic
        if all(field in signal for field in ['entry_price', 'target_price', 'stop_loss']):
            try:
                entry = float(signal['entry_price'])
                target = float(signal['target_price'])
                stop = float(signal['stop_loss'])
                
                if signal.get('signal_type') in ['LONG', 'BUY']:
                    if target <= entry:
                        validation_result['warnings'].append('Target price should be higher than entry for LONG signals')
                    if stop >= entry:
                        validation_result['warnings'].append('Stop loss should be lower than entry for LONG signals')
                elif signal.get('signal_type') in ['SHORT', 'SELL']:
                    if target >= entry:
                        validation_result['warnings'].append('Target price should be lower than entry for SHORT signals')
                    if stop <= entry:
                        validation_result['warnings'].append('Stop loss should be higher than entry for SHORT signals')
                        
            except (ValueError, TypeError):
                validation_result['invalid_fields'].extend(['entry_price', 'target_price', 'stop_loss'])
        
        # Determine overall validity
        validation_result['is_valid'] = (
            len(validation_result['missing_fields']) == 0 and
            len(validation_result['invalid_fields']) == 0
        )
        
        # Add recommendations
        if validation_result['missing_fields']:
            validation_result['recommendations'].append(f"Add missing fields: {', '.join(validation_result['missing_fields'])}")
        
        if validation_result['invalid_fields']:
            validation_result['recommendations'].append(f"Fix invalid fields: {', '.join(validation_result['invalid_fields'])}")
        
        if validation_result['warnings']:
            validation_result['recommendations'].append("Review price logic and signal parameters")
        
        return validation_result
    
    async def check_market_conditions(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """Check market conditions for signal execution"""
        market_conditions = {
            'is_executable': False,
            'market_status': 'unknown',
            'volatility_warning': False,
            'liquidity_warning': False,
            'timing_warning': False,
            'recommendations': []
        }
        
        try:
            # Check if pair is valid
            pair_validation = await self.validate_trading_pair(signal.get('symbol', ''))
            
            if not pair_validation['is_valid']:
                market_conditions['recommendations'].append("Trading pair validation failed")
                return market_conditions
            
            # Check volatility
            if pair_validation['volatility_level'] in ['extreme', 'high']:
                market_conditions['volatility_warning'] = True
                market_conditions['recommendations'].append("High volatility detected - consider reducing position size")
            
            # Check liquidity
            if pair_validation['liquidity_score'] < 0.3:
                market_conditions['liquidity_warning'] = True
                market_conditions['recommendations'].append("Low liquidity - consider using limit orders")
            
            # Check market hours (simplified - crypto markets are 24/7)
            current_hour = datetime.now().hour
            if current_hour in [0, 1, 2, 3, 4, 5]:  # Low activity hours
                market_conditions['timing_warning'] = True
                market_conditions['recommendations'].append("Low market activity hours - consider waiting")
            
            # Determine if signal is executable
            market_conditions['is_executable'] = (
                pair_validation['is_valid'] and
                not market_conditions['volatility_warning'] and
                pair_validation['liquidity_score'] > 0.2
            )
            
            # Set market status
            if market_conditions['is_executable']:
                market_conditions['market_status'] = 'favorable'
            elif pair_validation['is_valid']:
                market_conditions['market_status'] = 'caution'
            else:
                market_conditions['market_status'] = 'unfavorable'
            
            return market_conditions
            
        except Exception as e:
            logger.error(f"Error checking market conditions: {e}")
            market_conditions['recommendations'].append(f"Error checking market conditions: {str(e)}")
            return market_conditions

# Global validator instance
trading_pair_validator = TradingPairValidator()

# Test function
async def test_validator():
    """Test the trading pair validator"""
    validator = TradingPairValidator()
    
    test_pairs = ['BTCUSDT', 'ETHUSDT', 'INVALIDPAIR', 'SHIBUSDT']
    
    print("🧪 Testing Trading Pair Validator")
    print("=" * 50)
    
    for pair in test_pairs:
        print(f"\n🔍 Validating {pair}:")
        result = await validator.validate_trading_pair(pair)
        
        print(f"  Valid: {result['is_valid']}")
        print(f"  Exchanges: {result['exists_on_exchanges']}")
        print(f"  Liquidity Score: {result['liquidity_score']:.2f}")
        print(f"  Volatility: {result['volatility_level']}")
        print(f"  Price Accuracy: {result['price_accuracy']}")
        
        if result['warnings']:
            print(f"  ⚠️ Warnings: {result['warnings']}")
        
        if result['recommendations']:
            print(f"  💡 Recommendations: {result['recommendations']}")

if __name__ == "__main__":
    asyncio.run(test_validator())
