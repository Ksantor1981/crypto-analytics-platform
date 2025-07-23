"""
Base Channel Parser - Abstract base class for all channel parsers
Part of Task 2.1.1: Рефакторинг системы парсеров
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from enum import Enum
from dataclasses import dataclass
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

class ChannelType(str, Enum):
    """Types of channels supported by the platform"""
    TELEGRAM = "telegram"
    DISCORD = "discord"
    REDDIT = "reddit"
    RSS = "rss"
    TWITTER = "twitter"
    TRADINGVIEW = "tradingview"

class SignalType(Enum):
    """Types of signals that can be parsed"""
    BUY = "buy"
    SELL = "sell"
    LONG = "long"
    SHORT = "short"
    HOLD = "hold"
    ALERT = "alert"

@dataclass
class ParsedSignal:
    """Standardized signal format from any parser"""
    # Required fields
    symbol: str  # e.g., "BTC", "ETH"
    signal_type: SignalType
    source_channel: str
    timestamp: datetime
    raw_message: str
    
    # Optional trading fields
    entry_price: Optional[Decimal] = None
    target_price: Optional[Decimal] = None
    stop_loss: Optional[Decimal] = None
    confidence: Optional[float] = None  # 0.0 to 1.0
    
    # Metadata
    message_id: Optional[str] = None
    author: Optional[str] = None
    channel_type: Optional[ChannelType] = None
    additional_data: Optional[Dict[str, Any]] = None

@dataclass
class ChannelConfig:
    """Configuration for a channel parser"""
    name: str
    url: str
    channel_type: ChannelType
    description: Optional[str] = None
    category: Optional[str] = None
    enabled: bool = True
    
    # Parser-specific config
    parser_config: Optional[Dict[str, Any]] = None
    
    # Rate limiting
    max_requests_per_minute: int = 60
    retry_attempts: int = 3
    
    # Signal filtering
    min_confidence: float = 0.5
    allowed_symbols: Optional[List[str]] = None

class BaseChannelParser(ABC):
    """
    Abstract base class for all channel parsers
    
    This class defines the interface that all parsers must implement
    to ensure consistent behavior across different channel types.
    """
    
    def __init__(self, config: ChannelConfig):
        self.config = config
        self.logger = logging.getLogger(f"{self.__class__.__name__}")
        self._is_connected = False
        self._last_error = None
        
    @property
    def channel_type(self) -> ChannelType:
        """Return the type of channel this parser handles"""
        return self.config.channel_type
    
    @property
    def is_connected(self) -> bool:
        """Check if parser is connected and ready"""
        return self._is_connected
    
    @property
    def last_error(self) -> Optional[str]:
        """Get the last error message"""
        return self._last_error
    
    @abstractmethod
    async def connect(self) -> bool:
        """
        Connect to the channel/service
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from the channel/service"""
        pass
    
    @abstractmethod
    async def parse_messages(self, limit: int = 100) -> List[ParsedSignal]:
        """
        Parse recent messages from the channel
        
        Args:
            limit: Maximum number of messages to parse
            
        Returns:
            List of parsed signals
        """
        pass
    
    @abstractmethod
    async def parse_single_message(self, message: Any) -> Optional[ParsedSignal]:
        """
        Parse a single message into a signal
        
        Args:
            message: Raw message object from the channel
            
        Returns:
            ParsedSignal if message contains a valid signal, None otherwise
        """
        pass
    
    @abstractmethod
    def validate_config(self) -> bool:
        """
        Validate the parser configuration
        
        Returns:
            bool: True if config is valid, False otherwise
        """
        pass
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform a health check on the parser
        
        Returns:
            Dict with health status information
        """
        try:
            is_healthy = await self.connect() if not self._is_connected else True
            
            return {
                "status": "healthy" if is_healthy else "unhealthy",
                "channel_type": self.channel_type.value,
                "channel_name": self.config.name,
                "is_connected": self._is_connected,
                "last_error": self._last_error,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return {
                "status": "unhealthy",
                "channel_type": self.channel_type.value,
                "channel_name": self.config.name,
                "is_connected": False,
                "last_error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def _extract_symbol(self, text: str) -> Optional[str]:
        """
        Extract cryptocurrency symbol from text
        
        Args:
            text: Text to search for symbols
            
        Returns:
            Symbol if found, None otherwise
        """
        import re
        
        # Common crypto symbols pattern
        symbol_pattern = r'\b([A-Z]{2,10})(?:USD|USDT|BTC|ETH)?\b'
        
        # Known crypto symbols (can be extended)
        known_symbols = {
            'BTC', 'ETH', 'ADA', 'DOT', 'LINK', 'XRP', 'LTC', 'BCH',
            'BNB', 'SOL', 'MATIC', 'AVAX', 'ATOM', 'NEAR', 'FTM', 'ALGO'
        }
        
        matches = re.findall(symbol_pattern, text.upper())
        for match in matches:
            if match in known_symbols:
                return match
                
        return None
    
    def _extract_price(self, text: str) -> Optional[Decimal]:
        """
        Extract price from text
        
        Args:
            text: Text to search for price
            
        Returns:
            Price as Decimal if found, None otherwise
        """
        import re
        
        # Price patterns: $1234.56, 1234.56, 1,234.56
        price_patterns = [
            r'\$?(\d{1,3}(?:,\d{3})*(?:\.\d{1,8})?)',
            r'(\d+\.\d{1,8})',
            r'(\d+)'
        ]
        
        for pattern in price_patterns:
            matches = re.findall(pattern, text)
            if matches:
                try:
                    # Remove commas and convert to Decimal
                    price_str = matches[0].replace(',', '')
                    return Decimal(price_str)
                except (ValueError, IndexError):
                    continue
                    
        return None
    
    def _detect_signal_type(self, text: str) -> Optional[SignalType]:
        """
        Detect signal type from text
        
        Args:
            text: Text to analyze
            
        Returns:
            SignalType if detected, None otherwise
        """
        text_lower = text.lower()
        
        # Signal keywords mapping
        signal_keywords = {
            SignalType.BUY: ['buy', 'long', 'enter long', 'go long', 'bullish'],
            SignalType.SELL: ['sell', 'short', 'enter short', 'go short', 'bearish'],
            SignalType.HOLD: ['hold', 'hodl', 'keep holding'],
            SignalType.ALERT: ['alert', 'watch', 'monitor', 'attention']
        }
        
        for signal_type, keywords in signal_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                return signal_type
                
        return None
    
    def _calculate_confidence(self, signal: ParsedSignal) -> float:
        """
        Calculate confidence score for a signal
        
        Args:
            signal: The parsed signal
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        confidence = 0.5  # Base confidence
        
        # Increase confidence based on available data
        if signal.entry_price:
            confidence += 0.2
        if signal.target_price:
            confidence += 0.15
        if signal.stop_loss:
            confidence += 0.15
        
        # Adjust based on signal clarity
        text_lower = signal.raw_message.lower()
        clear_indicators = ['target', 'entry', 'stop', 'tp', 'sl']
        confidence += sum(0.02 for indicator in clear_indicators if indicator in text_lower)
        
        return min(confidence, 1.0)
    
    def __str__(self) -> str:
        return f"{self.__class__.__name__}({self.config.name})"
    
    def __repr__(self) -> str:
        return (f"{self.__class__.__name__}("
                f"name='{self.config.name}', "
                f"type='{self.channel_type.value}', "
                f"connected={self._is_connected})")
