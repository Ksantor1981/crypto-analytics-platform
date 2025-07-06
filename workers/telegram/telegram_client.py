"""
Telegram Client for collecting crypto signals from channels
Real implementation using Telethon API
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
    REAL_TELEGRAM_CHANNELS, CRYPTO_SYMBOLS, PARSE_INTERVAL_MINUTES
)

logger = logging.getLogger(__name__)

class TelegramSignalCollector:
    """
    Telegram client for collecting crypto signals from configured channels
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
        
        # Signal patterns for parsing
        self.signal_patterns = {
            'crypto_pair': re.compile(r'([A-Z]{2,6}/?[A-Z]{2,6})', re.IGNORECASE),
            'entry': re.compile(r'(?:entry|вход|цена входа)[:\s]*([0-9.,]+)', re.IGNORECASE),
            'target': re.compile(r'(?:target|tp|цель|тп)[:\s]*([0-9.,]+)', re.IGNORECASE),
            'stop_loss': re.compile(r'(?:sl|stop.?loss|стоп|стоп.?лосс)[:\s]*([0-9.,]+)', re.IGNORECASE),
            'direction': re.compile(r'\b(long|short|buy|sell|лонг|шорт|покупк|продаж)\b', re.IGNORECASE),
            'leverage': re.compile(r'(?:leverage|плечо)[:\s]*([0-9]+)x?', re.IGNORECASE),
        }
        
        # Supported crypto pairs (расширенный список)
        self.supported_pairs = CRYPTO_SYMBOLS + [
            'BTC/USDT', 'BTCUSDT', 'BTC/USD',
            'ETH/USDT', 'ETHUSDT', 'ETH/USD',
            'BNB/USDT', 'BNBUSDT', 'BNB/USD',
            'ADA/USDT', 'ADAUSDT', 'ADA/USD',
            'SOL/USDT', 'SOLUSDT', 'SOL/USD',
            'DOT/USDT', 'DOTUSDT', 'DOT/USD',
            'MATIC/USDT', 'MATICUSDT', 'MATIC/USD',
            'AVAX/USDT', 'AVAXUSDT', 'AVAX/USD'
        ]

    async def initialize_client(self) -> bool:
        """Initialize Telegram client with real API keys"""
        if not TELETHON_AVAILABLE:
            logger.warning("Telethon not available, using mock mode")
            return True
            
        if not self.use_real_config:
            if not self.config.is_configured():
                logger.error("Telegram API not configured")
                return False
            
        try:
            session_name = f"real_session_{self.api_id}" if self.use_real_config else self.config.session_name
            
            self.client = TelegramClient(
                session_name,
                self.api_id,
                self.api_hash
            )
            
            await self.client.start()
            logger.info(f"Telegram client initialized successfully with {'real' if self.use_real_config else 'test'} config")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Telegram client: {e}")
            return False

    def parse_signal_message(self, text: str, timestamp: datetime, channel_name: str = "") -> Optional[Dict]:
        """
        Parse a message text to extract trading signal information
        Enhanced version with better pattern matching
        """
        if not text or len(text) < 10:
            return None
            
        # Clean text
        text = text.strip()
        
        # Look for crypto pair
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
        
        # Check if this pair is supported
        supported = any(
            pair.replace('/', '') == crypto_pair.replace('/', '') 
            for pair in self.supported_pairs
        )
        if not supported:
            return None

        # Extract entry price
        entry_match = self.signal_patterns['entry'].search(text)
        if not entry_match:
            return None
            
        try:
            entry_price = Decimal(entry_match.group(1).replace(',', '.'))
        except:
            return None

        # Extract targets (multiple targets possible)
        target_matches = self.signal_patterns['target'].findall(text)
        targets = []
        for target in target_matches[:3]:  # Max 3 targets
            try:
                targets.append(Decimal(target.replace(',', '.')))
            except:
                continue

        # Extract stop loss
        sl_match = self.signal_patterns['stop_loss'].search(text)
        stop_loss = None
        if sl_match:
            try:
                stop_loss = Decimal(sl_match.group(1).replace(',', '.'))
            except:
                pass

        # Determine direction
        direction_match = self.signal_patterns['direction'].search(text)
        direction = "LONG"  # Default
        if direction_match:
            dir_text = direction_match.group(1).lower()
            if dir_text in ['short', 'sell', 'шорт', 'продаж']:
                direction = "SHORT"

        # Extract leverage if present
        leverage_match = self.signal_patterns['leverage'].search(text)
        leverage = None
        if leverage_match:
            try:
                leverage = int(leverage_match.group(1))
            except:
                pass

        # Basic validation
        if len(targets) == 0 and not stop_loss:
            return None  # Need at least one target or stop loss

        # Calculate confidence score
        confidence = self._calculate_signal_confidence(text, targets, stop_loss)
        
        if confidence < self.config.min_signal_confidence:
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
            'original_text': text,
            'message_timestamp': timestamp,
            'channel_name': channel_name,
            'confidence': confidence,
            'status': 'PENDING'
        }

    def _calculate_signal_confidence(self, text: str, targets: List, stop_loss: Optional[Decimal]) -> float:
        """Calculate confidence score for a signal based on completeness and quality"""
        score = 0.0
        
        # Base score for having entry price
        score += 0.3
        
        # Points for targets
        if len(targets) >= 1:
            score += 0.2
        if len(targets) >= 2:
            score += 0.1
        if len(targets) >= 3:
            score += 0.1
            
        # Points for stop loss
        if stop_loss:
            score += 0.2
            
        # Points for clear direction
        if any(word in text.lower() for word in ['long', 'short', 'buy', 'sell']):
            score += 0.1
            
        return min(score, 1.0)

    async def collect_signals_from_channel(self, channel_config) -> List[Dict]:
        """Collect signals from a specific channel"""
        signals = []
        
        if not TELETHON_AVAILABLE or not self.client:
            return []
            
        try:
            # Get channel entity
            channel = await self.client.get_entity(channel_config.username)
            
            # Get recent messages
            messages = await self.client.get_messages(
                channel,
                limit=self.config.max_messages_per_channel
            )
            
            for message in messages:
                if not message.text:
                    continue
                    
                # Parse signal from message
                signal = self.parse_signal_message(
                    message.text,
                    message.date,
                    channel_config.name
                )
                
                if signal:
                    signal['message_id'] = message.id
                    signal['channel_id'] = channel_config.channel_id
                    signals.append(signal)
                    
            logger.info(f"Collected {len(signals)} signals from {channel_config.name}")
            
        except FloodWaitError as e:
            logger.warning(f"Rate limited for {e.seconds} seconds on {channel_config.name}")
        except Exception as e:
            logger.error(f"Error collecting from {channel_config.name}: {e}")
            
        return signals

    async def collect_signals_real(self) -> Dict[str, Any]:
        """Real implementation using Telethon API"""
        logger.info("Starting real Telegram signal collection...")
        
        if not await self.initialize_client():
            return await self.collect_signals_mock()
            
        all_signals = []
        channels_processed = 0
        
        try:
            active_channels = self.config.get_active_channels()
            
            for channel_config in active_channels:
                channel_signals = await self.collect_signals_from_channel(channel_config)
                all_signals.extend(channel_signals)
                channels_processed += 1
                
                # Small delay between channels to avoid rate limiting
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"Error in signal collection: {e}")
            
        finally:
            if self.client:
                await self.client.disconnect()
        
        return {
            "status": "success",
            "total_signals_collected": len(all_signals),
            "channels_processed": channels_processed,
            "signals": all_signals,
            "timestamp": datetime.now().isoformat()
        }

    async def collect_signals_mock(self) -> Dict[str, Any]:
        """Mock implementation for testing without real Telegram API"""
        logger.info("Running mock Telegram signal collection...")
        
        # Enhanced mock signals with more realistic data
        mock_signals = [
            {
                'asset': 'BTC/USDT',
                'direction': 'LONG',
                'entry_price': Decimal('45000.00'),
                'tp1_price': Decimal('46500.00'),
                'tp2_price': Decimal('47500.00'),
                'stop_loss': Decimal('43500.00'),
                'leverage': 10,
                'original_text': '🚀 BTC/USDT LONG\nEntry: 45000\nTP1: 46500\nTP2: 47500\nSL: 43500\nLeverage: 10x',
                'channel_name': 'Crypto Signals Pro',
                'confidence': 0.9,
                'message_timestamp': datetime.now(),
                'status': 'PENDING'
            },
            {
                'asset': 'ETH/USDT', 
                'direction': 'SHORT',
                'entry_price': Decimal('3200.00'),
                'tp1_price': Decimal('3100.00'),
                'tp2_price': Decimal('3000.00'),
                'stop_loss': Decimal('3250.00'),
                'leverage': 5,
                'original_text': '📉 ETH/USDT SHORT\nEntry: 3200\nTarget 1: 3100\nTarget 2: 3000\nSL: 3250\nLeverage: 5x',
                'channel_name': 'ETH Signals',
                'confidence': 0.85,
                'message_timestamp': datetime.now() - timedelta(minutes=30),
                'status': 'PENDING'
            },
            {
                'asset': 'SOL/USDT',
                'direction': 'LONG', 
                'entry_price': Decimal('150.00'),
                'tp1_price': Decimal('155.00'),
                'stop_loss': Decimal('145.00'),
                'leverage': 3,
                'original_text': '🌟 SOL/USDT LONG\nEntry: 150.00\nTarget: 155.00\nStop Loss: 145.00\nLeverage: 3x',
                'channel_name': 'Altcoin Signals',
                'confidence': 0.75,
                'message_timestamp': datetime.now() - timedelta(hours=1),
                'status': 'PENDING'
            }
        ]
        
        # Simulate processing time
        await asyncio.sleep(2)
        
        return {
            "status": "success",
            "total_signals_collected": len(mock_signals),
            "channels_processed": 3,
            "signals": mock_signals,
            "timestamp": datetime.now().isoformat(),
            "mode": "mock"
        }

    async def collect_signals(self) -> Dict[str, Any]:
        """Main method to collect signals (tries real API, falls back to mock)"""
        if TELETHON_AVAILABLE and self.config.is_configured():
            return await self.collect_signals_real()
        else:
            return await self.collect_signals_mock()

# Sync wrapper function for Celery
def collect_telegram_signals_sync():
    """Synchronous wrapper for Celery task"""
    collector = TelegramSignalCollector()
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(collector.collect_signals())
    finally:
        loop.close() 