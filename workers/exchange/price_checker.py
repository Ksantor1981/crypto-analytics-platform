"""
Price Checker Service for validating signal execution
Enhanced version with real configuration integration
"""
import asyncio
import logging
import os
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from decimal import Decimal
import httpx

from ..real_data_config import CRYPTO_SYMBOLS, BYBIT_API_KEY, BYBIT_API_SECRET

logger = logging.getLogger(__name__)

class PriceChecker:
    """
    Enhanced service for checking crypto prices and validating signal execution
    """
    
    def __init__(self):
        # Exchange API endpoints
        self.binance_api = "https://api.binance.com/api/v3"
        self.bybit_api = "https://api.bybit.com/v5"
        
        # Price tolerance for target/SL hits (0.1% by default)
        self.price_tolerance = Decimal('0.001')
        
        # Supported exchanges for different pairs
        self.exchange_mapping = {
            'BTC/USDT': 'binance',
            'ETH/USDT': 'binance', 
            'BNB/USDT': 'binance',
            'ADA/USDT': 'binance',
            'SOL/USDT': 'binance',
            'XRP/USDT': 'binance',
            'DOGE/USDT': 'binance',
            'DOT/USDT': 'binance',
            'AVAX/USDT': 'binance',
            'LINK/USDT': 'binance'
        }
        
        # Add all symbols from config
        for symbol in CRYPTO_SYMBOLS:
            if symbol.endswith('USDT'):
                formatted_symbol = symbol[:-4] + '/USDT'
                self.exchange_mapping[formatted_symbol] = 'binance'
        
        # API keys for authenticated requests
        self.bybit_api_key = BYBIT_API_KEY
        self.bybit_api_secret = BYBIT_API_SECRET

    async def get_binance_klines(self, symbol: str, start_time: int, end_time: int, interval: str = "1m") -> List[Dict]:
        """
        Get historical price data from Binance
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
        Get historical price data from Bybit
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
        
        try:
            timeout = httpx.Timeout(30.0)
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.get(url, params=params)
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

    async def get_current_price(self, symbol: str) -> Optional[Decimal]:
        """
        Get current price for a symbol from multiple exchanges
        """
        # Try Binance first
        binance_price = await self._get_binance_price(symbol)
        if binance_price:
            return binance_price
            
        # Fallback to Bybit
        bybit_price = await self._get_bybit_price(symbol)
        return bybit_price

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
            logger.warning(f"Error fetching Binance price for {symbol}: {e}")
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
                    tickers = data.get('result', {}).get('list', [])
                    if tickers:
                        return Decimal(tickers[0]['lastPrice'])
                        
        except Exception as e:
            logger.warning(f"Error fetching Bybit price for {symbol}: {e}")
            
        return None

    def check_price_hit(self, target_price: Decimal, actual_price: Decimal, direction: str, price_type: str) -> bool:
        """
        Check if a target price or stop loss was hit
        
        Args:
            target_price: The target/SL price to check
            actual_price: The actual market price
            direction: LONG or SHORT
            price_type: 'target' or 'stop_loss'
        """
        tolerance = target_price * self.price_tolerance
        
        if direction.upper() == 'LONG':
            if price_type == 'target':
                # For long targets, price should reach or exceed target
                return actual_price >= (target_price - tolerance)
            else:  # stop_loss
                # For long SL, price should hit or go below SL
                return actual_price <= (target_price + tolerance)
        else:  # SHORT
            if price_type == 'target':
                # For short targets, price should reach or go below target
                return actual_price <= (target_price + tolerance)
            else:  # stop_loss
                # For short SL, price should hit or go above SL
                return actual_price >= (target_price - tolerance)

    async def check_signal_execution(self, signal_data: Dict) -> Dict[str, Any]:
        """
        Enhanced signal execution checker with multiple exchange support
        """
        asset = signal_data['asset']
        direction = signal_data['direction']
        entry_price = Decimal(str(signal_data['entry_price']))
        message_timestamp = signal_data['message_timestamp']
        
        # Calculate time window for checking (24h for TP1, 48h for TP2/TP3)
        start_time = int(message_timestamp.timestamp() * 1000)
        end_time_24h = start_time + (24 * 60 * 60 * 1000)  # 24 hours
        end_time_48h = start_time + (48 * 60 * 60 * 1000)  # 48 hours
        
        # Try multiple exchanges for price data
        klines_24h = await self.get_binance_klines(asset, start_time, end_time_24h)
        if not klines_24h:
            klines_24h = await self.get_bybit_klines(asset, start_time, end_time_24h)
            
        klines_48h = await self.get_binance_klines(asset, start_time, end_time_48h)
        if not klines_48h:
            klines_48h = await self.get_bybit_klines(asset, start_time, end_time_48h)
        
        if not klines_24h and not klines_48h:
            logger.warning(f"No price data available for {asset}")
            return {
                'status': 'error',
                'message': f'No price data available for {asset}',
                'asset': asset,
                'direction': direction,
                'entry_price': entry_price
            }
        
        result = {
            'asset': asset,
            'direction': direction,
            'entry_price': entry_price,
            'status': 'PENDING',
            'tp1_hit': False,
            'tp2_hit': False,
            'tp3_hit': False,
            'sl_hit': False,
            'tp1_hit_at': None,
            'tp2_hit_at': None,
            'tp3_hit_at': None,
            'sl_hit_at': None,
            'final_exit_price': None,
            'final_exit_timestamp': None,
            'profit_loss_percentage': None,
            'data_source': 'binance' if klines_24h else 'bybit'
        }
        
        # Check each target and stop loss
        targets = []
        if signal_data.get('tp1_price'):
            targets.append(('tp1', Decimal(str(signal_data['tp1_price']))))
        if signal_data.get('tp2_price'):
            targets.append(('tp2', Decimal(str(signal_data['tp2_price']))))
        if signal_data.get('tp3_price'):
            targets.append(('tp3', Decimal(str(signal_data['tp3_price']))))
        
        stop_loss = Decimal(str(signal_data['stop_loss'])) if signal_data.get('stop_loss') else None
        
        # Check 24h window for TP1 and SL
        for kline in klines_24h:
            timestamp = datetime.fromtimestamp(kline['timestamp'] / 1000)
            high_price = kline['high']
            low_price = kline['low']
            
            # Check stop loss first (highest priority)
            if stop_loss and not result['sl_hit']:
                if self.check_price_hit(stop_loss, low_price if direction.upper() == 'LONG' else high_price, direction, 'stop_loss'):
                    result['sl_hit'] = True
                    result['sl_hit_at'] = timestamp
                    result['status'] = 'SL_HIT'
                    result['final_exit_price'] = stop_loss
                    result['final_exit_timestamp'] = timestamp
                    
                    # Calculate loss percentage
                    if direction.upper() == 'LONG':
                        result['profit_loss_percentage'] = float((stop_loss - entry_price) / entry_price * 100)
                    else:
                        result['profit_loss_percentage'] = float((entry_price - stop_loss) / entry_price * 100)
                    
                    break  # Stop checking once SL is hit
            
            # Check TP1 in 24h window
            if targets and not result['tp1_hit'] and not result['sl_hit']:
                tp1_price = targets[0][1]
                if self.check_price_hit(tp1_price, high_price if direction.upper() == 'LONG' else low_price, direction, 'target'):
                    result['tp1_hit'] = True
                    result['tp1_hit_at'] = timestamp
                    result['status'] = 'TP1_HIT'
                    result['final_exit_price'] = tp1_price
                    result['final_exit_timestamp'] = timestamp
                    
                    # Calculate profit percentage
                    if direction.upper() == 'LONG':
                        result['profit_loss_percentage'] = float((tp1_price - entry_price) / entry_price * 100)
                    else:
                        result['profit_loss_percentage'] = float((entry_price - tp1_price) / entry_price * 100)
        
        # If no SL hit and TP1 was hit, check 48h window for TP2/TP3
        if not result['sl_hit'] and result['tp1_hit'] and len(targets) > 1:
            for kline in klines_48h:
                if kline['timestamp'] <= end_time_24h:
                    continue  # Skip 24h data we already processed
                    
                timestamp = datetime.fromtimestamp(kline['timestamp'] / 1000)
                high_price = kline['high']
                low_price = kline['low']
                
                # Check TP2
                if len(targets) > 1 and not result['tp2_hit']:
                    tp2_price = targets[1][1]
                    if self.check_price_hit(tp2_price, high_price if direction.upper() == 'LONG' else low_price, direction, 'target'):
                        result['tp2_hit'] = True
                        result['tp2_hit_at'] = timestamp
                        result['status'] = 'TP2_HIT'
                        result['final_exit_price'] = tp2_price
                        result['final_exit_timestamp'] = timestamp
                        
                        # Update profit percentage
                        if direction.upper() == 'LONG':
                            result['profit_loss_percentage'] = float((tp2_price - entry_price) / entry_price * 100)
                        else:
                            result['profit_loss_percentage'] = float((entry_price - tp2_price) / entry_price * 100)
                
                # Check TP3
                if len(targets) > 2 and not result['tp3_hit']:
                    tp3_price = targets[2][1]
                    if self.check_price_hit(tp3_price, high_price if direction.upper() == 'LONG' else low_price, direction, 'target'):
                        result['tp3_hit'] = True
                        result['tp3_hit_at'] = timestamp
                        result['status'] = 'TP3_HIT'
                        result['final_exit_price'] = tp3_price
                        result['final_exit_timestamp'] = timestamp
                        
                        # Update profit percentage
                        if direction.upper() == 'LONG':
                            result['profit_loss_percentage'] = float((tp3_price - entry_price) / entry_price * 100)
                        else:
                            result['profit_loss_percentage'] = float((entry_price - tp3_price) / entry_price * 100)
        
        # If nothing hit within timeframes, mark as expired
        if result['status'] == 'PENDING':
            result['status'] = 'EXPIRED'
        
        # Determine if signal was successful according to our definitions
        result['is_successful'] = (
            (result['tp1_hit'] and not result['sl_hit']) or 
            result['tp2_hit'] or 
            result['tp3_hit']
        )
        
        return result

    async def check_multiple_signals(self, signals: List[Dict]) -> List[Dict[str, Any]]:
        """
        Check execution for multiple signals with enhanced error handling
        """
        results = []
        
        for signal in signals:
            try:
                result = await self.check_signal_execution(signal)
                results.append(result)
                
                # Brief delay to avoid rate limiting
                await asyncio.sleep(0.2)
                
            except Exception as e:
                logger.error(f"Error checking signal {signal.get('id', 'unknown')}: {e}")
                results.append({
                    'status': 'error',
                    'message': str(e),
                    'asset': signal.get('asset', 'unknown'),
                    'direction': signal.get('direction', 'unknown'),
                    'entry_price': signal.get('entry_price', 0)
                })
        
        return results

    async def validate_signal_data(self, signal_data: Dict) -> bool:
        """
        Validate signal data before processing
        """
        required_fields = ['asset', 'direction', 'entry_price', 'message_timestamp']
        
        for field in required_fields:
            if field not in signal_data or signal_data[field] is None:
                logger.error(f"Missing required field: {field}")
                return False
        
        # Validate asset format
        asset = signal_data['asset']
        if asset not in self.exchange_mapping:
            logger.warning(f"Unsupported asset: {asset}")
            return False
        
        # Validate direction
        direction = signal_data['direction'].upper()
        if direction not in ['LONG', 'SHORT']:
            logger.error(f"Invalid direction: {direction}")
            return False
        
        # Validate prices
        try:
            entry_price = Decimal(str(signal_data['entry_price']))
            if entry_price <= 0:
                logger.error(f"Invalid entry price: {entry_price}")
                return False
        except:
            logger.error(f"Invalid entry price format: {signal_data['entry_price']}")
            return False
        
        return True

# Mock implementation for testing without real API calls
async def check_signals_mock(signals: List[Dict]) -> Dict:
    """Mock implementation for testing signal checking"""
    logger.info(f"Running mock signal execution check for {len(signals)} signals...")
    
    # Simulate some signals hitting targets, some hitting SL
    results = []
    for i, signal in enumerate(signals):
        if i % 3 == 0:  # Every 3rd signal hits TP1
            result = {
                'asset': signal['asset'],
                'status': 'TP1_HIT',
                'tp1_hit': True,
                'profit_loss_percentage': 2.5,
                'is_successful': True
            }
        elif i % 4 == 0:  # Every 4th signal hits SL  
            result = {
                'asset': signal['asset'],
                'status': 'SL_HIT',
                'sl_hit': True,
                'profit_loss_percentage': -1.5,
                'is_successful': False
            }
        else:  # Others are still pending/expired
            result = {
                'asset': signal['asset'],
                'status': 'EXPIRED',
                'is_successful': False
            }
        
        results.append(result)
    
    # Simulate processing time
    await asyncio.sleep(1)
    
    return {
        "status": "success",
        "signals_checked": len(signals),
        "results": results,
        "timestamp": datetime.now().isoformat()
    }

def check_signal_results_sync():
    """Synchronous wrapper for Celery task"""
    
    # Mock signals data for testing
    mock_signals = [
        {
            'id': 1,
            'asset': 'BTC/USDT',
            'direction': 'LONG',
            'entry_price': '45000.00',
            'tp1_price': '46500.00',
            'stop_loss': '43500.00',
            'message_timestamp': datetime.now() - timedelta(hours=2)
        },
        {
            'id': 2,
            'asset': 'ETH/USDT',
            'direction': 'SHORT', 
            'entry_price': '3200.00',
            'tp1_price': '3100.00',
            'stop_loss': '3250.00',
            'message_timestamp': datetime.now() - timedelta(hours=6)
        }
    ]
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(check_signals_mock(mock_signals))
    finally:
        loop.close() 