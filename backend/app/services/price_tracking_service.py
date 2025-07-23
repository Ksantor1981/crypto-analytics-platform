"""
Price Tracking Service - Real-time price monitoring for signal validation
Part of Task 3.1.2: Price tracking система
"""
import logging
import asyncio
import aiohttp
from typing import Dict, Any, List, Optional, Set
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_

from ..models.signal import Signal, SignalStatus
from ..database import get_db
from ..services.signal_validation_service import signal_validation_service

logger = logging.getLogger(__name__)

class PriceTrackingService:
    """
    Service for real-time cryptocurrency price tracking
    Core business logic: Monitor prices to validate signal execution
    """
    
    def __init__(self):
        self.tracked_symbols: Set[str] = set()
        self.current_prices: Dict[str, float] = {}
        self.price_history: Dict[str, List[Dict[str, Any]]] = {}
        self.active_signals: Dict[str, List[Signal]] = {}
        self.tracking_active = False
        
        # Exchange APIs configuration
        self.exchanges = {
            'binance': {
                'base_url': 'https://api.binance.com/api/v3',
                'price_endpoint': '/ticker/price',
                'symbols_endpoint': '/exchangeInfo',
                'weight_limit': 1200  # requests per minute
            },
            'bybit': {
                'base_url': 'https://api.bybit.com/v5',
                'price_endpoint': '/market/tickers',
                'symbols_endpoint': '/market/instruments-info',
                'weight_limit': 600
            },
            'coinbase': {
                'base_url': 'https://api.exchange.coinbase.com',
                'price_endpoint': '/products/{symbol}/ticker',
                'weight_limit': 300
            }
        }
        
        self.primary_exchange = 'binance'
        self.fallback_exchanges = ['bybit', 'coinbase']
    
    async def start_tracking(self, db_session_factory):
        """
        Start the price tracking service
        """
        if self.tracking_active:
            logger.warning("Price tracking is already active")
            return
        
        self.tracking_active = True
        logger.info("Starting price tracking service...")
        
        # Start background tasks
        asyncio.create_task(self._price_monitoring_loop(db_session_factory))
        asyncio.create_task(self._signal_validation_loop(db_session_factory))
        asyncio.create_task(self._cleanup_loop())
        
        logger.info("Price tracking service started successfully")
    
    async def stop_tracking(self):
        """Stop the price tracking service"""
        self.tracking_active = False
        logger.info("Price tracking service stopped")
    
    async def add_symbol_tracking(self, symbol: str, db: Session):
        """
        Add a cryptocurrency symbol to tracking
        """
        try:
            if symbol not in self.tracked_symbols:
                self.tracked_symbols.add(symbol)
                self.current_prices[symbol] = await self._get_current_price(symbol)
                self.price_history[symbol] = []
                
                logger.info(f"Added {symbol} to price tracking")
            
            # Update active signals for this symbol
            await self._update_active_signals(symbol, db)
            
        except Exception as e:
            logger.error(f"Error adding {symbol} to tracking: {e}")
    
    async def remove_symbol_tracking(self, symbol: str):
        """Remove a symbol from tracking"""
        if symbol in self.tracked_symbols:
            self.tracked_symbols.discard(symbol)
            self.current_prices.pop(symbol, None)
            self.price_history.pop(symbol, None)
            self.active_signals.pop(symbol, None)
            
            logger.info(f"Removed {symbol} from price tracking")
    
    async def get_current_price(self, symbol: str) -> Optional[float]:
        """Get current price for a symbol"""
        if symbol in self.current_prices:
            return self.current_prices[symbol]
        
        return await self._get_current_price(symbol)
    
    async def get_price_history(self, symbol: str, hours: int = 24) -> List[Dict[str, Any]]:
        """Get price history for a symbol"""
        if symbol not in self.price_history:
            return []
        
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        return [
            entry for entry in self.price_history[symbol]
            if entry['timestamp'] >= cutoff_time
        ]
    
    async def check_signal_execution(self, signal: Signal, db: Session) -> bool:
        """
        Check if a signal should be executed based on current price
        """
        try:
            current_price = await self.get_current_price(signal.symbol)
            if not current_price:
                return False
            
            # Check if signal conditions are met
            if signal.signal_type == 'buy':
                # For buy signals, check if price reached entry or below
                if current_price <= signal.entry_price * 1.02:  # 2% tolerance
                    await self._execute_signal(signal, current_price, db)
                    return True
                
                # Check if stop loss hit
                if signal.stop_loss and current_price <= signal.stop_loss:
                    await self._stop_signal(signal, current_price, db, "Stop loss hit")
                    return True
                
                # Check if target reached
                if signal.target_price and current_price >= signal.target_price:
                    await self._complete_signal(signal, current_price, db, "Target reached")
                    return True
            
            elif signal.signal_type == 'sell':
                # For sell signals, check if price reached entry or above
                if current_price >= signal.entry_price * 0.98:  # 2% tolerance
                    await self._execute_signal(signal, current_price, db)
                    return True
                
                # Check if stop loss hit
                if signal.stop_loss and current_price >= signal.stop_loss:
                    await self._stop_signal(signal, current_price, db, "Stop loss hit")
                    return True
                
                # Check if target reached
                if signal.target_price and current_price <= signal.target_price:
                    await self._complete_signal(signal, current_price, db, "Target reached")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking signal execution for {signal.id}: {e}")
            return False
    
    async def _price_monitoring_loop(self, db_session_factory):
        """
        Main price monitoring loop
        """
        while self.tracking_active:
            try:
                if self.tracked_symbols:
                    await self._update_all_prices()
                
                # Sleep for 30 seconds between updates
                await asyncio.sleep(30)
                
            except Exception as e:
                logger.error(f"Error in price monitoring loop: {e}")
                await asyncio.sleep(60)  # Longer sleep on error
    
    async def _signal_validation_loop(self, db_session_factory):
        """
        Loop to validate active signals against current prices
        """
        while self.tracking_active:
            try:
                db = next(db_session_factory())
                
                # Get all pending and active signals
                pending_signals = db.query(Signal).filter(
                    Signal.status.in_([SignalStatus.PENDING, SignalStatus.ACTIVE])
                ).all()
                
                for signal in pending_signals:
                    if signal.symbol in self.tracked_symbols:
                        await self.check_signal_execution(signal, db)
                
                db.close()
                
                # Check every 2 minutes
                await asyncio.sleep(120)
                
            except Exception as e:
                logger.error(f"Error in signal validation loop: {e}")
                await asyncio.sleep(300)  # 5 minutes on error
    
    async def _cleanup_loop(self):
        """
        Cleanup old price history and inactive signals
        """
        while self.tracking_active:
            try:
                # Clean up price history older than 7 days
                cutoff_time = datetime.utcnow() - timedelta(days=7)
                
                for symbol in self.price_history:
                    self.price_history[symbol] = [
                        entry for entry in self.price_history[symbol]
                        if entry['timestamp'] >= cutoff_time
                    ]
                
                # Sleep for 1 hour between cleanups
                await asyncio.sleep(3600)
                
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")
                await asyncio.sleep(3600)
    
    async def _update_all_prices(self):
        """Update prices for all tracked symbols"""
        try:
            # Get prices from primary exchange
            prices = await self._get_multiple_prices(list(self.tracked_symbols))
            
            timestamp = datetime.utcnow()
            
            for symbol, price in prices.items():
                if price:
                    old_price = self.current_prices.get(symbol)
                    self.current_prices[symbol] = price
                    
                    # Store in price history
                    if symbol not in self.price_history:
                        self.price_history[symbol] = []
                    
                    self.price_history[symbol].append({
                        'price': price,
                        'timestamp': timestamp,
                        'change': ((price - old_price) / old_price * 100) if old_price else 0
                    })
                    
                    # Keep only last 1000 entries per symbol
                    if len(self.price_history[symbol]) > 1000:
                        self.price_history[symbol] = self.price_history[symbol][-1000:]
            
        except Exception as e:
            logger.error(f"Error updating prices: {e}")
    
    async def _get_current_price(self, symbol: str) -> Optional[float]:
        """Get current price for a single symbol"""
        try:
            # Try primary exchange first
            price = await self._fetch_price_from_exchange(symbol, self.primary_exchange)
            if price:
                return price
            
            # Try fallback exchanges
            for exchange in self.fallback_exchanges:
                price = await self._fetch_price_from_exchange(symbol, exchange)
                if price:
                    return price
            
            logger.warning(f"Could not get price for {symbol} from any exchange")
            return None
            
        except Exception as e:
            logger.error(f"Error getting price for {symbol}: {e}")
            return None
    
    async def _get_multiple_prices(self, symbols: List[str]) -> Dict[str, Optional[float]]:
        """Get prices for multiple symbols efficiently"""
        try:
            if self.primary_exchange == 'binance':
                return await self._fetch_binance_prices(symbols)
            elif self.primary_exchange == 'bybit':
                return await self._fetch_bybit_prices(symbols)
            else:
                # Fallback to individual requests
                prices = {}
                for symbol in symbols:
                    prices[symbol] = await self._get_current_price(symbol)
                return prices
                
        except Exception as e:
            logger.error(f"Error getting multiple prices: {e}")
            return {symbol: None for symbol in symbols}
    
    async def _fetch_binance_prices(self, symbols: List[str]) -> Dict[str, Optional[float]]:
        """Fetch prices from Binance API"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.exchanges['binance']['base_url']}/ticker/price"
                
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        prices = {}
                        for item in data:
                            symbol_base = item['symbol'].replace('USDT', '').replace('BUSD', '')
                            if symbol_base in symbols:
                                prices[symbol_base] = float(item['price'])
                        
                        return prices
                    else:
                        logger.warning(f"Binance API error: {response.status}")
                        return {symbol: None for symbol in symbols}
                        
        except Exception as e:
            logger.error(f"Error fetching Binance prices: {e}")
            return {symbol: None for symbol in symbols}
    
    async def _fetch_bybit_prices(self, symbols: List[str]) -> Dict[str, Optional[float]]:
        """Fetch prices from Bybit API"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.exchanges['bybit']['base_url']}/market/tickers"
                params = {'category': 'spot'}
                
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        prices = {}
                        if 'result' in data and 'list' in data['result']:
                            for item in data['result']['list']:
                                symbol_base = item['symbol'].replace('USDT', '').replace('USDC', '')
                                if symbol_base in symbols:
                                    prices[symbol_base] = float(item['lastPrice'])
                        
                        return prices
                    else:
                        logger.warning(f"Bybit API error: {response.status}")
                        return {symbol: None for symbol in symbols}
                        
        except Exception as e:
            logger.error(f"Error fetching Bybit prices: {e}")
            return {symbol: None for symbol in symbols}
    
    async def _fetch_price_from_exchange(self, symbol: str, exchange: str) -> Optional[float]:
        """Fetch price from specific exchange"""
        try:
            if exchange == 'binance':
                return await self._fetch_binance_single_price(symbol)
            elif exchange == 'bybit':
                return await self._fetch_bybit_single_price(symbol)
            elif exchange == 'coinbase':
                return await self._fetch_coinbase_price(symbol)
            
            return None
            
        except Exception as e:
            logger.error(f"Error fetching {symbol} price from {exchange}: {e}")
            return None
    
    async def _fetch_binance_single_price(self, symbol: str) -> Optional[float]:
        """Fetch single price from Binance"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.exchanges['binance']['base_url']}/ticker/price"
                params = {'symbol': f"{symbol}USDT"}
                
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=5)) as response:
                    if response.status == 200:
                        data = await response.json()
                        return float(data['price'])
                    
        except Exception as e:
            logger.error(f"Error fetching Binance price for {symbol}: {e}")
        
        return None
    
    async def _fetch_bybit_single_price(self, symbol: str) -> Optional[float]:
        """Fetch single price from Bybit"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.exchanges['bybit']['base_url']}/market/tickers"
                params = {'category': 'spot', 'symbol': f"{symbol}USDT"}
                
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=5)) as response:
                    if response.status == 200:
                        data = await response.json()
                        if 'result' in data and 'list' in data['result'] and data['result']['list']:
                            return float(data['result']['list'][0]['lastPrice'])
                    
        except Exception as e:
            logger.error(f"Error fetching Bybit price for {symbol}: {e}")
        
        return None
    
    async def _fetch_coinbase_price(self, symbol: str) -> Optional[float]:
        """Fetch price from Coinbase"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.exchanges['coinbase']['base_url']}/products/{symbol}-USD/ticker"
                
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                    if response.status == 200:
                        data = await response.json()
                        return float(data['price'])
                    
        except Exception as e:
            logger.error(f"Error fetching Coinbase price for {symbol}: {e}")
        
        return None
    
    async def _update_active_signals(self, symbol: str, db: Session):
        """Update active signals list for a symbol"""
        try:
            active_signals = db.query(Signal).filter(
                and_(
                    Signal.symbol == symbol,
                    Signal.status.in_([SignalStatus.PENDING, SignalStatus.ACTIVE])
                )
            ).all()
            
            self.active_signals[symbol] = active_signals
            
        except Exception as e:
            logger.error(f"Error updating active signals for {symbol}: {e}")
    
    async def _execute_signal(self, signal: Signal, execution_price: float, db: Session):
        """Mark signal as executed"""
        await signal_validation_service.update_signal_status(
            signal=signal,
            new_status=SignalStatus.ACTIVE,
            db=db,
            execution_price=execution_price,
            notes=f"Signal executed at {execution_price}"
        )
        
        logger.info(f"Signal {signal.id} executed: {signal.symbol} {signal.signal_type} @ {execution_price}")
    
    async def _complete_signal(self, signal: Signal, completion_price: float, db: Session, reason: str):
        """Mark signal as completed (target reached)"""
        await signal_validation_service.update_signal_status(
            signal=signal,
            new_status=SignalStatus.COMPLETED,
            db=db,
            execution_price=completion_price,
            notes=f"Signal completed: {reason} @ {completion_price}"
        )
        
        logger.info(f"Signal {signal.id} completed: {reason} @ {completion_price}")
    
    async def _stop_signal(self, signal: Signal, stop_price: float, db: Session, reason: str):
        """Mark signal as stopped (stop loss hit)"""
        await signal_validation_service.update_signal_status(
            signal=signal,
            new_status=SignalStatus.STOPPED,
            db=db,
            execution_price=stop_price,
            notes=f"Signal stopped: {reason} @ {stop_price}"
        )
        
        logger.info(f"Signal {signal.id} stopped: {reason} @ {stop_price}")
    
    def get_tracking_stats(self) -> Dict[str, Any]:
        """Get price tracking statistics"""
        return {
            'tracked_symbols': len(self.tracked_symbols),
            'symbols': list(self.tracked_symbols),
            'tracking_active': self.tracking_active,
            'current_prices': dict(self.current_prices),
            'price_history_entries': {
                symbol: len(history) 
                for symbol, history in self.price_history.items()
            },
            'active_signals_count': {
                symbol: len(signals) 
                for symbol, signals in self.active_signals.items()
            }
        }


# Global price tracking service instance
price_tracking_service = PriceTrackingService()
