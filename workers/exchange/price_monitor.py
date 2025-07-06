"""
Real-time Price Monitor for crypto assets
Monitors prices and updates signal execution status
UPDATED: Integrated with Bybit API for real data
"""
import asyncio
import logging
import sys
import os
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from decimal import Decimal
import json

# Add backend to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '../../backend'))

try:
    import httpx
    import aiohttp
    HTTP_CLIENT_AVAILABLE = True
except ImportError:
    HTTP_CLIENT_AVAILABLE = False
    print("Warning: HTTP clients not available, using mock prices")

try:
    from sqlalchemy.orm import Session
    from app.database import get_db
    from app.models.signal import Signal
    from app.models.performance_metric import PerformanceMetric
    BACKEND_AVAILABLE = True
except ImportError:
    BACKEND_AVAILABLE = False
    print("Warning: Backend models not available")

# Import Bybit client
try:
    from .bybit_client import BybitClient
    BYBIT_AVAILABLE = True
except ImportError:
    BYBIT_AVAILABLE = False
    print("Warning: Bybit client not available")

from ..real_data_config import CRYPTO_SYMBOLS

logger = logging.getLogger(__name__)

class PriceMonitor:
    """
    Real-time price monitoring for crypto assets
    ENHANCED: Now with Bybit integration for real data
    """
    
    def __init__(self, use_real_data=True):
        self.backend_available = BACKEND_AVAILABLE
        self.http_available = HTTP_CLIENT_AVAILABLE
        self.bybit_available = BYBIT_AVAILABLE
        self.use_real_data = use_real_data
        
        # Initialize Bybit client if available
        self.bybit_client = None
        if self.bybit_available and self.use_real_data:
            self.bybit_client = BybitClient()
        
        # Exchange APIs (free tier) - fallback sources
        self.price_sources = {
            'binance': 'https://api.binance.com/api/v3/ticker/price',
            'coinbase': 'https://api.coinbase.com/v2/exchange-rates',
            'coingecko': 'https://api.coingecko.com/api/v3/simple/price'
        }
        
        # Asset mapping for different exchanges
        self.asset_mapping = {
            'BTC/USDT': {'binance': 'BTCUSDT', 'bybit': 'BTCUSDT', 'symbol': 'BTC'},
            'ETH/USDT': {'binance': 'ETHUSDT', 'bybit': 'ETHUSDT', 'symbol': 'ETH'},
            'BNB/USDT': {'binance': 'BNBUSDT', 'bybit': 'BNBUSDT', 'symbol': 'BNB'},
            'ADA/USDT': {'binance': 'ADAUSDT', 'bybit': 'ADAUSDT', 'symbol': 'ADA'},
            'SOL/USDT': {'binance': 'SOLUSDT', 'bybit': 'SOLUSDT', 'symbol': 'SOL'},
            'DOT/USDT': {'binance': 'DOTUSDT', 'bybit': 'DOTUSDT', 'symbol': 'DOT'},
            'MATIC/USDT': {'binance': 'MATICUSDT', 'bybit': 'MATICUSDT', 'symbol': 'MATIC'},
            'AVAX/USDT': {'binance': 'AVAXUSDT', 'bybit': 'AVAXUSDT', 'symbol': 'AVAX'}
        }

    async def get_price_from_bybit(self, symbol: str) -> Optional[float]:
        """Get price from Bybit API (PRIMARY SOURCE)"""
        if not self.bybit_client:
            return None
            
        try:
            bybit_symbol = self.asset_mapping.get(symbol, {}).get('bybit')
            if not bybit_symbol:
                return None
                
            async with self.bybit_client as client:
                prices = await client.get_current_prices([bybit_symbol])
                if bybit_symbol in prices:
                    return float(prices[bybit_symbol])
                    
        except Exception as e:
            logger.error(f"Error getting price from Bybit for {symbol}: {e}")
            
        return None

    async def get_price_from_binance(self, symbol: str) -> Optional[float]:
        """Get price from Binance API (FALLBACK)"""
        try:
            binance_symbol = self.asset_mapping.get(symbol, {}).get('binance')
            if not binance_symbol:
                return None
                
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.price_sources['binance']}?symbol={binance_symbol}",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return float(data['price'])
                        
        except Exception as e:
            logger.error(f"Error getting price from Binance for {symbol}: {e}")
            
        return None

    async def get_price_from_coingecko(self, symbol: str) -> Optional[float]:
        """Get price from CoinGecko API (FALLBACK)"""
        try:
            # Map symbols to CoinGecko IDs
            coingecko_ids = {
                'BTC/USDT': 'bitcoin',
                'ETH/USDT': 'ethereum',
                'BNB/USDT': 'binancecoin',
                'ADA/USDT': 'cardano',
                'SOL/USDT': 'solana',
                'DOT/USDT': 'polkadot',
                'MATIC/USDT': 'polygon',
                'AVAX/USDT': 'avalanche-2'
            }
            
            coin_id = coingecko_ids.get(symbol)
            if not coin_id:
                return None
                
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.price_sources['coingecko']}?ids={coin_id}&vs_currencies=usd",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return float(data[coin_id]['usd'])
                        
        except Exception as e:
            logger.error(f"Error getting price from CoinGecko for {symbol}: {e}")
            
        return None

    async def get_current_price(self, symbol: str) -> Optional[float]:
        """Get current price with priority: Bybit -> Binance -> CoinGecko -> Mock"""
        if not self.use_real_data:
            return self.get_mock_price(symbol)
            
        # Priority 1: Bybit (our primary exchange)
        if self.bybit_available:
            price = await self.get_price_from_bybit(symbol)
            if price:
                logger.info(f"✅ Got {symbol} price from Bybit: ${price}")
                return price
        
        # Priority 2: Binance (fast and reliable)
        if self.http_available:
            price = await self.get_price_from_binance(symbol)
            if price:
                logger.info(f"✅ Got {symbol} price from Binance: ${price}")
                return price
                
            # Priority 3: CoinGecko (backup)
            price = await self.get_price_from_coingecko(symbol)
            if price:
                logger.info(f"✅ Got {symbol} price from CoinGecko: ${price}")
                return price
        
        # Final fallback to mock
        logger.warning(f"⚠️ Using mock price for {symbol}")
        return self.get_mock_price(symbol)

    async def get_market_data_real(self, symbols: List[str] = None) -> Dict[str, Dict]:
        """Get comprehensive market data from Bybit"""
        if not self.bybit_available or not self.use_real_data:
            return {}
            
        try:
            async with self.bybit_client as client:
                market_data = await client.get_market_data(symbols or CRYPTO_SYMBOLS)
                logger.info(f"✅ Got market data for {len(market_data)} symbols from Bybit")
                return market_data
                
        except Exception as e:
            logger.error(f"Error getting market data from Bybit: {e}")
            return {}

    def get_mock_price(self, symbol: str) -> float:
        """Get mock price for testing"""
        mock_prices = {
            'BTC/USDT': 45123.45,
            'ETH/USDT': 3187.92,
            'BNB/USDT': 312.45,
            'ADA/USDT': 0.485,
            'SOL/USDT': 152.34,
            'DOT/USDT': 6.78,
            'MATIC/USDT': 0.92,
            'AVAX/USDT': 38.45
        }
        
        # Add some random variation
        import random
        base_price = mock_prices.get(symbol, 100.0)
        variation = random.uniform(-0.02, 0.02)  # ±2% variation
        return base_price * (1 + variation)

    def check_signal_execution(self, signal: Dict, current_price: float) -> Dict[str, Any]:
        """Check if signal targets or stop loss have been hit"""
        entry_price = float(signal.get('entry_price', 0))
        direction = signal.get('direction', '').upper()
        
        result = {
            'signal_id': signal.get('id'),
            'current_price': current_price,
            'entry_price': entry_price,
            'direction': direction,
            'status_changed': False,
            'new_status': signal.get('status'),
            'profit_loss': 0.0,
            'targets_hit': [],
            'stop_loss_hit': False
        }
        
        if direction == 'BUY' or direction == 'LONG':
            # Long position
            profit_loss = ((current_price - entry_price) / entry_price) * 100
            
            # Check targets
            for i, target_field in enumerate(['tp1_price', 'tp2_price', 'tp3_price'], 1):
                target_price = signal.get(target_field)
                if target_price and current_price >= float(target_price):
                    result['targets_hit'].append(f'TP{i}')
                    
            # Check stop loss
            stop_loss = signal.get('stop_loss')
            if stop_loss and current_price <= float(stop_loss):
                result['stop_loss_hit'] = True
                result['new_status'] = 'FAILED'
                result['status_changed'] = True
                
        elif direction == 'SELL' or direction == 'SHORT':
            # Short position
            profit_loss = ((entry_price - current_price) / entry_price) * 100
            
            # Check targets
            for i, target_field in enumerate(['tp1_price', 'tp2_price', 'tp3_price'], 1):
                target_price = signal.get(target_field)
                if target_price and current_price <= float(target_price):
                    result['targets_hit'].append(f'TP{i}')
                    
            # Check stop loss
            stop_loss = signal.get('stop_loss')
            if stop_loss and current_price >= float(stop_loss):
                result['stop_loss_hit'] = True
                result['new_status'] = 'FAILED'
                result['status_changed'] = True
        
        result['profit_loss'] = profit_loss
        
        # Update status based on targets hit
        if result['targets_hit'] and not result['stop_loss_hit']:
            if len(result['targets_hit']) >= 3:
                result['new_status'] = 'COMPLETED'
            elif len(result['targets_hit']) >= 1:
                result['new_status'] = 'PARTIAL'
            result['status_changed'] = True
            
        return result

    async def update_signal_status(self, db: Session, signal_id: int, execution_result: Dict) -> bool:
        """Update signal status in database"""
        try:
            signal = db.query(Signal).filter(Signal.id == signal_id).first()
            if not signal:
                return False
                
            # Update signal status
            if execution_result['status_changed']:
                signal.status = execution_result['new_status']
                signal.current_price = execution_result['current_price']
                signal.profit_loss = execution_result['profit_loss']
                signal.updated_at = datetime.now()
                
                # Create performance metric
                metric = PerformanceMetric(
                    signal_id=signal_id,
                    metric_type='PRICE_CHECK',
                    value=execution_result['current_price'],
                    timestamp=datetime.now(),
                    metadata=json.dumps({
                        'targets_hit': execution_result['targets_hit'],
                        'stop_loss_hit': execution_result['stop_loss_hit'],
                        'profit_loss': execution_result['profit_loss']
                    })
                )
                db.add(metric)
                
                db.commit()
                logger.info(f"Updated signal {signal_id} status to {execution_result['new_status']}")
                return True
                
        except Exception as e:
            logger.error(f"Error updating signal {signal_id}: {e}")
            db.rollback()
            
        return False

    async def monitor_active_signals(self) -> Dict[str, Any]:
        """Monitor all active signals and update their status"""
        if not self.backend_available:
            return await self.monitor_signals_mock()
            
        monitored_signals = 0
        updated_signals = 0
        assets_monitored = set()
        
        try:
            db = next(get_db())
            
            # Get active signals
            active_signals = db.query(Signal).filter(
                Signal.status.in_(['PENDING', 'PARTIAL']),
                Signal.created_at >= datetime.now() - timedelta(days=7)  # Only recent signals
            ).all()
            
            for signal in active_signals:
                try:
                    monitored_signals += 1
                    assets_monitored.add(signal.asset)
                    
                    # Get current price
                    current_price = await self.get_current_price(signal.asset)
                    if not current_price:
                        continue
                        
                    # Check signal execution
                    execution_result = self.check_signal_execution(
                        {
                            'id': signal.id,
                            'entry_price': signal.entry_price,
                            'direction': signal.direction,
                            'tp1_price': signal.tp1_price,
                            'tp2_price': signal.tp2_price,
                            'tp3_price': signal.tp3_price,
                            'stop_loss': signal.stop_loss,
                            'status': signal.status
                        },
                        current_price
                    )
                    
                    # Update signal if status changed
                    if execution_result['status_changed']:
                        if await self.update_signal_status(db, signal.id, execution_result):
                            updated_signals += 1
                            
                    # Small delay to avoid overwhelming the API
                    await asyncio.sleep(0.1)
                    
                except Exception as e:
                    logger.error(f"Error monitoring signal {signal.id}: {e}")
                    
            db.close()
            
        except Exception as e:
            logger.error(f"Error in signal monitoring: {e}")
            
        return {
            'status': 'success',
            'monitored_signals': monitored_signals,
            'updated_signals': updated_signals,
            'assets_monitored': len(assets_monitored),
            'timestamp': datetime.now().isoformat()
        }

    async def monitor_signals_mock(self) -> Dict[str, Any]:
        """Mock monitoring for testing"""
        logger.info("Running mock signal monitoring...")
        
        # Simulate monitoring
        await asyncio.sleep(1)
        
        return {
            'status': 'success',
            'monitored_signals': 12,
            'updated_signals': 3,
            'assets_monitored': 5,
            'mode': 'mock',
            'timestamp': datetime.now().isoformat()
        }

# Sync wrapper for Celery
def monitor_prices_sync():
    """Synchronous wrapper for Celery task"""
    monitor = PriceMonitor()
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(monitor.monitor_active_signals())
    finally:
        loop.close() 