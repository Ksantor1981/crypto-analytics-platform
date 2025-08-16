"""
Telegram Client for collecting crypto signals from channels
Enhanced version with better error handling and configuration
"""
import os
import asyncio
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import re
from decimal import Decimal

# Try to import telethon, fall back to mock if not available
try:
    from telethon import TelegramClient, events
    from telethon.tl.types import Channel, Chat
    from telethon.errors import SessionPasswordNeededError, FloodWaitError
    TELETHON_AVAILABLE = True
except ImportError:
    TELETHON_AVAILABLE = False
    print("Warning: Telethon not available, using mock implementation")

from .config import telegram_config
from ..real_data_config import (
    TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_BOT_TOKEN,
    REAL_TELEGRAM_CHANNELS, CRYPTO_SYMBOLS, PARSE_INTERVAL_MINUTES,
    SIGNAL_CONFIDENCE_THRESHOLD
)

logger = logging.getLogger(__name__)

class TelegramSignalCollector:
    """
    Enhanced Telegram client for collecting crypto signals from configured channels
    """
    
    def __init__(self, use_real_config=True):
        self.use_real_config = use_real_config
        self.config = telegram_config
        self.client = None
        
        # Use real API keys if available
        if use_real_config:
            self.api_id = TELEGRAM_API_ID
            self.api_hash = TELEGRAM_API_HASH
            self.bot_token = TELEGRAM_BOT_TOKEN
            self.channels = REAL_TELEGRAM_CHANNELS
        else:
            self.api_id = self.config.api_id
            self.api_hash = self.config.api_hash
            self.bot_token = None
            self.channels = self.config.channels
        
        # Enhanced signal patterns for parsing
        self.signal_patterns = {
            'crypto_pair': re.compile(r'([A-Z]{2,6}/?[A-Z]{2,6})', re.IGNORECASE),
            'entry': re.compile(r'(?:entry|вход|цена входа|enter at)[:\s]*([0-9.,]+)', re.IGNORECASE),
            'target': re.compile(r'(?:target|tp|цель|тп|take profit)[:\s]*([0-9.,]+)', re.IGNORECASE),
            'stop_loss': re.compile(r'(?:sl|stop.?loss|стоп|стоп.?лосс|stop at)[:\s]*([0-9.,]+)', re.IGNORECASE),
            'direction': re.compile(r'\b(long|short|buy|sell|лонг|шорт|покупк|продаж)\b', re.IGNORECASE),
            'leverage': re.compile(r'(?:leverage|плечо)[:\s]*([0-9]+)x?', re.IGNORECASE),
            'multiple_targets': re.compile(r'(?:tp|target|цель)\s*[1-3]?[:\s]*([0-9.,]+)', re.IGNORECASE | re.MULTILINE),
        }
        
        # Supported crypto pairs (расширенный список)
        self.supported_pairs = CRYPTO_SYMBOLS + [
            'BTC/USDT', 'BTCUSDT', 'BTC/USD', 'BTCUSD',
            'ETH/USDT', 'ETHUSDT', 'ETH/USD', 'ETHUSD',
            'BNB/USDT', 'BNBUSDT', 'BNB/USD', 'BNBUSD',
            'ADA/USDT', 'ADAUSDT', 'ADA/USD', 'ADAUSD',
            'SOL/USDT', 'SOLUSDT', 'SOL/USD', 'SOLUSD',
            'DOT/USDT', 'DOTUSDT', 'DOT/USD', 'DOTUSD',
            'MATIC/USDT', 'MATICUSDT', 'MATIC/USD', 'MATICUSD',
            'AVAX/USDT', 'AVAXUSDT', 'AVAX/USD', 'AVAXUSD',
            'XRP/USDT', 'XRPUSDT', 'XRP/USD', 'XRPUSD',
            'DOGE/USDT', 'DOGEUSDT', 'DOGE/USD', 'DOGEUSD',
            'LINK/USDT', 'LINKUSDT', 'LINK/USD', 'LINKUSD'
        ]
        
        # Signal quality keywords
        self.quality_keywords = {
            'high_confidence': ['confirmed', 'strong', 'breakout', 'momentum', 'bullish', 'bearish'],
            'medium_confidence': ['potential', 'watch', 'possible', 'may', 'could'],
            'low_confidence': ['risky', 'uncertain', 'volatile', 'caution']
        }

    async def initialize_client(self) -> bool:
        """Initialize Telegram client with enhanced error handling"""
        if not TELETHON_AVAILABLE:
            logger.warning("Telethon not available, using mock mode")
            return True
            
        if not self.use_real_config:
            if not self.config.is_configured():
                logger.error("Telegram API not configured")
                return False
            
        try:
            import time
            session_name = f"real_session_{self.api_id}_{int(time.time())}" if self.use_real_config else self.config.session_name
            
            self.client = TelegramClient(
                session_name,
                self.api_id,
                self.api_hash,
                timeout=30,
                request_retries=3
            )
            
            await self.client.start()
            
            # Test connection
            me = await self.client.get_me()
            logger.info(f"Telegram client initialized successfully as {me.first_name} (ID: {me.id})")
            
            return True
            
        except SessionPasswordNeededError:
            logger.error("Two-factor authentication required. Please set up session manually.")
            return False
        except FloodWaitError as e:
            logger.error(f"Rate limited by Telegram. Wait {e.seconds} seconds.")
            return False
        except Exception as e:
            logger.error(f"Failed to initialize Telegram client: {e}")
            return False

    def parse_signal_message(self, text: str, timestamp: datetime, channel_name: str = "") -> Optional[Dict]:
        """
        Enhanced signal parsing with better pattern matching and validation
        """
        if not text or len(text) < 10:
            return None
            
        # Clean and normalize text
        text = text.strip()
        text_lower = text.lower()
        
        # Skip non-signal messages
        skip_keywords = ['news', 'update', 'announcement', 'reminder', 'analysis only']
        if any(keyword in text_lower for keyword in skip_keywords):
            return None
        
        # Look for crypto pair with enhanced matching
        pair_match = self.signal_patterns['crypto_pair'].search(text)
        if not pair_match:
            return None
            
        crypto_pair = pair_match.group(1).upper()
        
        # Normalize pair format
        if '/' not in crypto_pair and len(crypto_pair) > 6:
            if crypto_pair.endswith('USDT'):
                crypto_pair = crypto_pair[:-4] + '/USDT'
            elif crypto_pair.endswith('USD'):
                crypto_pair = crypto_pair[:-3] + '/USD'
            elif crypto_pair.endswith('BTC'):
                crypto_pair = crypto_pair[:-3] + '/BTC'
            elif crypto_pair.endswith('ETH'):
                crypto_pair = crypto_pair[:-3] + '/ETH'
        
        # Check if this pair is supported
        supported = any(
            pair.replace('/', '').upper() == crypto_pair.replace('/', '').upper()
            for pair in self.supported_pairs
        )
        if not supported:
            logger.debug(f"Unsupported pair: {crypto_pair}")
            return None

        # Extract entry price with enhanced patterns
        entry_match = self.signal_patterns['entry'].search(text)
        if not entry_match:
            # Try alternative patterns
            price_patterns = [
                r'@\s*([0-9.,]+)',  # @price format
                r'price[:\s]*([0-9.,]+)',  # price: format
                r'at[:\s]*([0-9.,]+)',  # at price format
            ]
            
            for pattern in price_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    entry_match = match
                    break
            
            if not entry_match:
                logger.debug(f"No entry price found in message: {text[:100]}...")
                return None
            
        try:
            entry_price = Decimal(entry_match.group(1).replace(',', '.'))
        except (ValueError, TypeError):
            logger.debug(f"Invalid entry price format: {entry_match.group(1)}")
            return None

        # Extract targets with enhanced multiple target detection
        target_matches = self.signal_patterns['multiple_targets'].findall(text)
        targets = []
        
        for target in target_matches[:3]:  # Max 3 targets
            try:
                target_price = Decimal(target.replace(',', '.'))
                if target_price > 0:
                    targets.append(target_price)
            except (ValueError, TypeError):
                continue

        # Extract stop loss with enhanced patterns
        sl_match = self.signal_patterns['stop_loss'].search(text)
        stop_loss = None
        if sl_match:
            try:
                stop_loss = Decimal(sl_match.group(1).replace(',', '.'))
            except (ValueError, TypeError):
                pass

        # Determine direction with enhanced detection
        direction_match = self.signal_patterns['direction'].search(text)
        direction = "LONG"  # Default
        
        if direction_match:
            dir_text = direction_match.group(1).lower()
            if dir_text in ['short', 'sell', 'шорт', 'продаж']:
                direction = "SHORT"
        
        # Additional direction detection from context
        if 'short' in text_lower or 'sell' in text_lower:
            direction = "SHORT"
        elif 'long' in text_lower or 'buy' in text_lower:
            direction = "LONG"

        # Extract leverage if present
        leverage_match = self.signal_patterns['leverage'].search(text)
        leverage = None
        if leverage_match:
            try:
                leverage = int(leverage_match.group(1))
            except (ValueError, TypeError):
                pass

        # Enhanced validation
        if len(targets) == 0 and not stop_loss:
            logger.debug("No targets or stop loss found")
            return None

        # Validate price relationships
        if not self._validate_price_relationships(entry_price, targets, stop_loss, direction):
            logger.debug("Invalid price relationships")
            return None

        # Calculate confidence score with enhanced factors
        confidence = self._calculate_signal_confidence(text, targets, stop_loss, channel_name)
        
        if confidence < SIGNAL_CONFIDENCE_THRESHOLD:
            logger.debug(f"Low confidence signal: {confidence:.2f}")
            return None

        return {
            'asset': crypto_pair,
            'direction': direction,
            'entry_price': entry_price,
            'tp1_price': targets[0] if len(targets) > 0 else None,
            'tp2_price': targets[1] if len(targets) > 1 else None,
            'tp3_price': targets[2] if len(targets) > 2 else None,
            'stop_loss': stop_loss,
            'leverage': leverage,
            'confidence': confidence,
            'channel': channel_name,
            'message_timestamp': timestamp,
            'raw_message': text[:200] + "..." if len(text) > 200 else text
        }

    def _validate_price_relationships(self, entry_price: Decimal, targets: List[Decimal], 
                                    stop_loss: Optional[Decimal], direction: str) -> bool:
        """Validate that price relationships make sense"""
        try:
            if direction.upper() == 'LONG':
                # For long positions, targets should be above entry, SL below
                for target in targets:
                    if target <= entry_price:
                        return False
                
                if stop_loss and stop_loss >= entry_price:
                    return False
                    
            else:  # SHORT
                # For short positions, targets should be below entry, SL above
                for target in targets:
                    if target >= entry_price:
                        return False
                
                if stop_loss and stop_loss <= entry_price:
                    return False
            
            return True
            
        except Exception:
            return False

    def _calculate_signal_confidence(self, text: str, targets: List, stop_loss: Optional[Decimal], 
                                   channel_name: str = "") -> float:
        """
        Enhanced confidence calculation with multiple factors
        """
        confidence = 0.5  # Base confidence
        text_lower = text.lower()
        
        # Factor 1: Completeness of signal data
        if len(targets) >= 2:
            confidence += 0.15
        elif len(targets) == 1:
            confidence += 0.1
        
        if stop_loss:
            confidence += 0.1
        
        # Factor 2: Signal quality keywords
        for keyword in self.quality_keywords['high_confidence']:
            if keyword in text_lower:
                confidence += 0.05
        
        for keyword in self.quality_keywords['medium_confidence']:
            if keyword in text_lower:
                confidence += 0.02
        
        for keyword in self.quality_keywords['low_confidence']:
            if keyword in text_lower:
                confidence -= 0.05
        
        # Factor 3: Message structure and formatting
        if '🎯' in text or '📈' in text or '📊' in text:
            confidence += 0.05
        
        if re.search(r'tp\s*[1-3]', text_lower):
            confidence += 0.05
        
        # Factor 4: Channel reputation (placeholder for future enhancement)
        trusted_channels = ['@cryptosignals', '@binancesignals']
        if channel_name in trusted_channels:
            confidence += 0.1
        
        # Factor 5: Risk-reward ratio
        if targets and stop_loss:
            try:
                reward = abs(targets[0] - targets[0])  # Simplified calculation
                risk = abs(stop_loss - targets[0])
                
                if risk > 0:
                    rr_ratio = reward / risk
                    if rr_ratio >= 2:
                        confidence += 0.1
                    elif rr_ratio >= 1:
                        confidence += 0.05
            except:
                pass
        
        # Ensure confidence is within bounds
        return max(0.0, min(1.0, confidence))

    async def collect_signals_from_channel(self, channel_config) -> List[Dict]:
        """
        Enhanced signal collection with better error handling
        """
        if not TELETHON_AVAILABLE:
            logger.warning("Telethon not available, using mock data")
            return []
            
        if not self.client:
            logger.error("Telegram client not initialized")
            return []
        
        signals = []
        # Используем username для поиска канала
        if isinstance(channel_config, str):
            channel_name = channel_config
        else:
            channel_name = channel_config.get('username', channel_config.get('name', ''))
        
        try:
            # Get channel entity using username
            entity = await self.client.get_entity(channel_name)
            
            # Calculate time range for message collection
            since_time = datetime.now() - timedelta(minutes=PARSE_INTERVAL_MINUTES * 2)
            
            # Collect recent messages
            messages = await self.client.get_messages(
                entity,
                limit=50,
                offset_date=since_time
            )
            
            logger.info(f"Collected {len(messages)} messages from {channel_name}")
            
            # Parse messages for signals
            for message in messages:
                if not message.text:
                    continue
                    
                try:
                    signal = self.parse_signal_message(
                        message.text,
                        message.date,
                        channel_name
                    )
                    
                    if signal:
                        signal['message_id'] = message.id
                        signals.append(signal)
                        logger.info(f"Found signal: {signal['asset']} {signal['direction']} from {channel_name}")
                        
                except Exception as e:
                    logger.error(f"Error parsing message from {channel_name}: {e}")
                    continue
            
        except FloodWaitError as e:
            logger.warning(f"Rate limited on {channel_name}. Waiting {e.seconds} seconds.")
            await asyncio.sleep(e.seconds)
        except Exception as e:
            logger.error(f"Error collecting from {channel_name}: {e}")
        
        return signals

    async def collect_signals_real(self) -> Dict[str, Any]:
        """
        Enhanced real signal collection with parallel processing
        """
        if not await self.initialize_client():
            return {
                "status": "error",
                "message": "Failed to initialize Telegram client",
                "signals": [],
                "timestamp": datetime.now().isoformat()
            }
        
        all_signals = []
        channel_results = {}
        
        try:
            # Collect from all channels in parallel
            tasks = []
            for channel in self.channels:
                task = asyncio.create_task(self.collect_signals_from_channel(channel))
                tasks.append((channel, task))
            
            # Wait for all tasks to complete
            for channel, task in tasks:
                try:
                    signals = await task
                    # Используем username как ключ для channel_results
                    if isinstance(channel, dict):
                        channel_key = channel.get('username', channel.get('name', str(channel)))
                    else:
                        channel_key = str(channel)
                    channel_results[channel_key] = len(signals)
                    all_signals.extend(signals)
                except Exception as e:
                    logger.error(f"Error collecting from {channel}: {e}")
                    if isinstance(channel, dict):
                        channel_key = channel.get('username', channel.get('name', str(channel)))
                    else:
                        channel_key = str(channel)
                    channel_results[channel_key] = 0
            
            # Sort signals by confidence
            all_signals.sort(key=lambda x: x.get('confidence', 0), reverse=True)
            
            logger.info(f"Collected {len(all_signals)} total signals from {len(self.channels)} channels")
            
            return {
                "status": "success",
                "signals": all_signals,
                "channel_results": channel_results,
                "total_signals": len(all_signals),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in real signal collection: {e}")
            return {
                "status": "error",
                "message": str(e),
                "signals": all_signals,
                "timestamp": datetime.now().isoformat()
            }
        finally:
            if self.client:
                await self.client.disconnect()

    async def collect_signals_mock(self) -> Dict[str, Any]:
        """
        Enhanced mock implementation with realistic signal data
        """
        logger.info(f"Running mock signal collection from {len(self.channels)} channels...")
        
        # Enhanced mock signals with more realistic data
        mock_signals = [
            {
                'asset': 'BTC/USDT',
                'direction': 'LONG',
                'entry_price': Decimal('45000.00'),
                'tp1_price': Decimal('46500.00'),
                'tp2_price': Decimal('47800.00'),
                'stop_loss': Decimal('43500.00'),
                'leverage': 5,
                'confidence': 0.85,
                'channel': '@cryptosignals',
                'message_timestamp': datetime.now() - timedelta(minutes=15),
                'raw_message': '🎯 BTC/USDT LONG Entry: 45000 TP1: 46500 TP2: 47800 SL: 43500 Leverage: 5x'
            },
            {
                'asset': 'ETH/USDT',
                'direction': 'SHORT',
                'entry_price': Decimal('3200.00'),
                'tp1_price': Decimal('3100.00'),
                'tp2_price': Decimal('3000.00'),
                'stop_loss': Decimal('3280.00'),
                'leverage': 3,
                'confidence': 0.78,
                'channel': '@binancesignals',
                'message_timestamp': datetime.now() - timedelta(minutes=32),
                'raw_message': '📈 ETH/USDT SHORT Entry: 3200 Target 1: 3100 Target 2: 3000 Stop Loss: 3280'
            },
            {
                'asset': 'ADA/USDT',
                'direction': 'LONG',
                'entry_price': Decimal('0.58'),
                'tp1_price': Decimal('0.62'),
                'stop_loss': Decimal('0.55'),
                'confidence': 0.72,
                'channel': '@cryptowhales',
                'message_timestamp': datetime.now() - timedelta(minutes=45),
                'raw_message': 'ADA/USDT LONG setup Entry: 0.58 Target: 0.62 SL: 0.55'
            }
        ]
        
        # Simulate processing time
        await asyncio.sleep(2)
        
        # Create channel results dict with proper channel names
        channel_results = {}
        if self.use_real_config:
            for channel in self.channels:
                # Используем username как ключ для channel_results
                if isinstance(channel, dict):
                    channel_key = channel.get('username', channel.get('name', str(channel)))
                else:
                    channel_key = str(channel)
                channel_results[channel_key] = 1
        else:
            for channel in self.channels:
                channel_name = channel.username if hasattr(channel, 'username') else str(channel)
                channel_results[channel_name] = 1
        
        return {
            "status": "success",
            "signals": mock_signals,
            "channel_results": channel_results,
            "total_signals": len(mock_signals),
            "timestamp": datetime.now().isoformat()
        }

    async def collect_signals(self) -> Dict[str, Any]:
        """
        Main signal collection method with automatic fallback
        """
        try:
            if self.use_real_config and TELETHON_AVAILABLE:
                logger.info("Using real Telegram API for signal collection")
                return await self.collect_signals_real()
            else:
                logger.info("Using mock signal collection")
                return await self.collect_signals_mock()
        except Exception as e:
            logger.error(f"Error in signal collection: {e}")
            return {
                "status": "error",
                "message": str(e),
                "signals": [],
                "timestamp": datetime.now().isoformat()
            }

def collect_telegram_signals_sync():
    """Enhanced synchronous wrapper for Celery task"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        collector = TelegramSignalCollector(use_real_config=True)
        return loop.run_until_complete(collector.collect_signals())
    finally:
        loop.close() 