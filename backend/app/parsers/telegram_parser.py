"""
Telegram Parser Plugin - Refactored Telegram parser using BaseChannelParser
Part of Task 2.1.1: Вынос Telegram парсера в отдельный плагин
"""
import asyncio
import logging
import re
from typing import List, Optional, Any, Dict
from datetime import datetime, timedelta
from decimal import Decimal

from .base_parser import (
    BaseChannelParser, ChannelConfig, ChannelType, 
    ParsedSignal, SignalType
)

# Try to import telethon, fall back to mock if not available
try:
    from telethon import TelegramClient, events
    from telethon.tl.types import Channel, Chat, Message
    from telethon.errors import SessionPasswordNeededError, FloodWaitError
    TELETHON_AVAILABLE = True
except ImportError:
    TELETHON_AVAILABLE = False
    print("Warning: Telethon not available, using mock implementation")

logger = logging.getLogger(__name__)

class TelegramParser(BaseChannelParser):
    """
    Telegram channel parser plugin
    
    Parses crypto signals from Telegram channels using the Telethon library
    """
    
    def __init__(self, config: ChannelConfig):
        super().__init__(config)
        
        if not TELETHON_AVAILABLE:
            raise ImportError("Telethon library is required for Telegram parsing")
        
        # Extract Telegram-specific config
        parser_config = config.parser_config or {}
        self.api_id = parser_config.get('api_id')
        self.api_hash = parser_config.get('api_hash')
        self.session_name = parser_config.get('session_name', f'session_{config.name}')
        self.phone_number = parser_config.get('phone_number')
        
        # Telegram client
        self.client: Optional[TelegramClient] = None
        self.channel_entity = None
        
        # Signal parsing patterns
        self.signal_patterns = {
            'buy_patterns': [
                r'\b(buy|long|enter\s+long|go\s+long)\b',
                r'\b(bullish|pump|moon)\b',
                r'📈|🚀|💰|🔥'
            ],
            'sell_patterns': [
                r'\b(sell|short|enter\s+short|go\s+short)\b',
                r'\b(bearish|dump|crash)\b',
                r'📉|💸|🔻|⚠️'
            ],
            'price_patterns': [
                r'\$?(\d{1,3}(?:,\d{3})*(?:\.\d{1,8})?)',
                r'(\d+\.\d{1,8})',
                r'entry:?\s*(\d+\.?\d*)',
                r'target:?\s*(\d+\.?\d*)',
                r'tp:?\s*(\d+\.?\d*)',
                r'sl:?\s*(\d+\.?\d*)',
                r'stop:?\s*(\d+\.?\d*)'
            ]
        }
    
    def validate_config(self) -> bool:
        """Validate Telegram parser configuration"""
        if not self.api_id or not self.api_hash:
            self.logger.error("Telegram API ID and hash are required")
            return False
        
        if not self.config.url:
            self.logger.error("Telegram channel URL is required")
            return False
        
        return True
    
    async def connect(self) -> bool:
        """Connect to Telegram"""
        try:
            if not self.validate_config():
                return False
            
            # Create Telegram client
            self.client = TelegramClient(
                self.session_name,
                self.api_id,
                self.api_hash
            )
            
            # Connect to Telegram
            await self.client.connect()
            
            # Check if we're authorized
            if not await self.client.is_user_authorized():
                if self.phone_number:
                    await self.client.send_code_request(self.phone_number)
                    self.logger.warning(f"Authorization required for {self.config.name}")
                    return False
                else:
                    self.logger.error("Phone number required for authorization")
                    return False
            
            # Get channel entity
            channel_url = self.config.url
            if channel_url.startswith('t.me/'):
                channel_username = channel_url.replace('t.me/', '')
            elif channel_url.startswith('@'):
                channel_username = channel_url
            else:
                channel_username = channel_url
            
            try:
                self.channel_entity = await self.client.get_entity(channel_username)
                self.logger.info(f"Connected to Telegram channel: {self.config.name}")
                self._is_connected = True
                self._last_error = None
                return True
                
            except Exception as e:
                self.logger.error(f"Failed to get channel entity {channel_username}: {e}")
                self._last_error = f"Channel not found: {e}"
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to connect to Telegram: {e}")
            self._last_error = str(e)
            return False
    
    async def disconnect(self) -> None:
        """Disconnect from Telegram"""
        if self.client:
            try:
                await self.client.disconnect()
                self.logger.info(f"Disconnected from Telegram channel: {self.config.name}")
            except Exception as e:
                self.logger.error(f"Error disconnecting from Telegram: {e}")
            finally:
                self.client = None
                self.channel_entity = None
                self._is_connected = False
    
    async def parse_messages(self, limit: int = 100) -> List[ParsedSignal]:
        """Parse recent messages from Telegram channel"""
        if not self._is_connected or not self.client or not self.channel_entity:
            self.logger.error("Not connected to Telegram")
            return []
        
        signals = []
        
        try:
            # Get recent messages
            messages = await self.client.get_messages(
                self.channel_entity,
                limit=limit
            )
            
            for message in messages:
                if isinstance(message, Message) and message.text:
                    signal = await self.parse_single_message(message)
                    if signal:
                        signals.append(signal)
            
            self.logger.info(f"Parsed {len(signals)} signals from {len(messages)} messages")
            
        except Exception as e:
            self.logger.error(f"Error parsing messages: {e}")
            self._last_error = str(e)
        
        return signals
    
    async def parse_single_message(self, message: Message) -> Optional[ParsedSignal]:
        """Parse a single Telegram message"""
        if not message.text:
            return None
        
        text = message.text
        text_lower = text.lower()
        
        # Extract symbol
        symbol = self._extract_symbol(text)
        if not symbol:
            return None
        
        # Check if symbol is allowed
        if (self.config.allowed_symbols and 
            symbol not in self.config.allowed_symbols):
            return None
        
        # Detect signal type
        signal_type = self._detect_signal_type_telegram(text)
        if not signal_type:
            return None
        
        # Extract prices
        entry_price = self._extract_entry_price(text)
        target_price = self._extract_target_price(text)
        stop_loss = self._extract_stop_loss(text)
        
        # Create parsed signal
        signal = ParsedSignal(
            symbol=symbol,
            signal_type=signal_type,
            source_channel=self.config.name,
            timestamp=message.date or datetime.utcnow(),
            raw_message=text,
            entry_price=entry_price,
            target_price=target_price,
            stop_loss=stop_loss,
            message_id=str(message.id),
            author=getattr(message.sender, 'username', None) if message.sender else None,
            channel_type=ChannelType.TELEGRAM,
            additional_data={
                'channel_id': getattr(self.channel_entity, 'id', None),
                'message_views': getattr(message, 'views', None),
                'message_forwards': getattr(message, 'forwards', None)
            }
        )
        
        # Calculate confidence
        signal.confidence = self._calculate_confidence(signal)
        
        # Check minimum confidence threshold
        if signal.confidence < self.config.min_confidence:
            return None
        
        return signal
    
    def _detect_signal_type_telegram(self, text: str) -> Optional[SignalType]:
        """Detect signal type from Telegram message"""
        text_lower = text.lower()
        
        # Check for buy/long signals
        for pattern in self.signal_patterns['buy_patterns']:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return SignalType.BUY
        
        # Check for sell/short signals
        for pattern in self.signal_patterns['sell_patterns']:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return SignalType.SELL
        
        # Check for emojis and special indicators
        if any(emoji in text for emoji in ['📈', '🚀', '💰', '🔥']):
            return SignalType.BUY
        elif any(emoji in text for emoji in ['📉', '💸', '🔻', '⚠️']):
            return SignalType.SELL
        
        return None
    
    def _extract_entry_price(self, text: str) -> Optional[Decimal]:
        """Extract entry price from Telegram message"""
        patterns = [
            r'entry:?\s*(\d+\.?\d*)',
            r'enter\s+at:?\s*(\d+\.?\d*)',
            r'buy\s+at:?\s*(\d+\.?\d*)',
            r'price:?\s*(\d+\.?\d*)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text.lower())
            if match:
                try:
                    return Decimal(match.group(1))
                except (ValueError, IndexError):
                    continue
        
        return None
    
    def _extract_target_price(self, text: str) -> Optional[Decimal]:
        """Extract target price from Telegram message"""
        patterns = [
            r'target:?\s*(\d+\.?\d*)',
            r'tp:?\s*(\d+\.?\d*)',
            r'take\s+profit:?\s*(\d+\.?\d*)',
            r'goal:?\s*(\d+\.?\d*)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text.lower())
            if match:
                try:
                    return Decimal(match.group(1))
                except (ValueError, IndexError):
                    continue
        
        return None
    
    def _extract_stop_loss(self, text: str) -> Optional[Decimal]:
        """Extract stop loss from Telegram message"""
        patterns = [
            r'sl:?\s*(\d+\.?\d*)',
            r'stop\s*loss:?\s*(\d+\.?\d*)',
            r'stop:?\s*(\d+\.?\d*)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text.lower())
            if match:
                try:
                    return Decimal(match.group(1))
                except (ValueError, IndexError):
                    continue
        
        return None
    
    def _calculate_confidence(self, signal: ParsedSignal) -> float:
        """Calculate confidence score for Telegram signal"""
        confidence = super()._calculate_confidence(signal)
        
        # Telegram-specific confidence adjustments
        text_lower = signal.raw_message.lower()
        
        # Increase confidence for structured signals
        if 'entry' in text_lower and 'target' in text_lower:
            confidence += 0.1
        
        # Increase confidence for signals with stop loss
        if any(word in text_lower for word in ['sl', 'stop loss', 'stop']):
            confidence += 0.05
        
        # Increase confidence for signals with emojis
        emoji_count = sum(1 for char in signal.raw_message if ord(char) > 0x1F600)
        confidence += min(emoji_count * 0.01, 0.05)
        
        # Decrease confidence for very short messages
        if len(signal.raw_message) < 50:
            confidence -= 0.1
        
        return max(0.0, min(confidence, 1.0))


# Auto-register the Telegram parser
def register_telegram_parser():
    """Register Telegram parser with the global registry"""
    from .parser_registry import register_parser
    register_parser(ChannelType.TELEGRAM, TelegramParser)

# Register on import
if TELETHON_AVAILABLE:
    register_telegram_parser()
    logger.info("Telegram parser registered successfully")
else:
    logger.warning("Telegram parser not registered - Telethon not available")
