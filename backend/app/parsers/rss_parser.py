"""
RSS Parser Plugin - RSS feed parser using BaseChannelParser
Part of Task 2.1.3: Реализация RSS парсера
"""
import asyncio
import logging
import re
from typing import List, Optional, Any, Dict
from datetime import datetime, timedelta
from decimal import Decimal
import aiohttp
import xml.etree.ElementTree as ET
from urllib.parse import urlparse

from .base_parser import (
    BaseChannelParser, ChannelConfig, ChannelType, 
    ParsedSignal, SignalType
)

logger = logging.getLogger(__name__)

class RSSParser(BaseChannelParser):
    """
    RSS feed parser plugin
    
    Parses crypto signals from RSS feeds (news sites, blogs, etc.)
    """
    
    def __init__(self, config: ChannelConfig):
        super().__init__(config)
        
        # Extract RSS-specific config
        parser_config = config.parser_config or {}
        self.user_agent = parser_config.get('user_agent', 'CryptoAnalytics/1.0')
        self.timeout = parser_config.get('timeout', 30)
        self.max_items = parser_config.get('max_items', 50)
        
        # RSS feed URL
        self.feed_url = config.url
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Extract feed info
        self.feed_title = None
        self.feed_description = None
        
        # Common crypto news sources patterns
        self.crypto_news_sources = [
            'coindesk.com', 'cointelegraph.com', 'decrypt.co',
            'coinbase.com', 'binance.com', 'cryptonews.com',
            'bitcoinist.com', 'newsbtc.com', 'cryptoslate.com'
        ]
        
        # Signal detection patterns for news
        self.bullish_keywords = [
            'adoption', 'partnership', 'integration', 'launch',
            'upgrade', 'bullish', 'positive', 'growth', 'surge',
            'rally', 'breakout', 'all-time high', 'ath', 'moon'
        ]
        
        self.bearish_keywords = [
            'crash', 'dump', 'bearish', 'negative', 'decline',
            'drop', 'fall', 'correction', 'sell-off', 'regulatory',
            'ban', 'hack', 'exploit', 'scam', 'warning'
        ]
        
        self.neutral_keywords = [
            'analysis', 'report', 'update', 'news', 'announcement',
            'development', 'technology', 'blockchain', 'defi'
        ]
    
    def validate_config(self) -> bool:
        """Validate RSS parser configuration"""
        if not self.feed_url:
            self.logger.error("RSS feed URL is required")
            return False
        
        # Validate URL format
        try:
            parsed = urlparse(self.feed_url)
            if not parsed.scheme or not parsed.netloc:
                self.logger.error(f"Invalid RSS feed URL: {self.feed_url}")
                return False
        except Exception as e:
            self.logger.error(f"Invalid RSS feed URL format: {e}")
            return False
        
        return True
    
    async def connect(self) -> bool:
        """Connect to RSS feed"""
        try:
            if not self.validate_config():
                return False
            
            # Create HTTP session
            self.session = aiohttp.ClientSession(
                headers={'User-Agent': self.user_agent},
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            )
            
            # Test connection by fetching feed
            async with self.session.get(self.feed_url) as response:
                if response.status == 200:
                    content = await response.text()
                    
                    # Parse XML to validate feed
                    try:
                        root = ET.fromstring(content)
                        
                        # Try to extract feed info
                        if root.tag == 'rss':
                            channel = root.find('channel')
                            if channel is not None:
                                self.feed_title = self._get_text(channel.find('title'))
                                self.feed_description = self._get_text(channel.find('description'))
                        elif root.tag.endswith('feed'):  # Atom feed
                            self.feed_title = self._get_text(root.find('.//{http://www.w3.org/2005/Atom}title'))
                            self.feed_description = self._get_text(root.find('.//{http://www.w3.org/2005/Atom}subtitle'))
                        
                        self.logger.info(f"Connected to RSS feed: {self.feed_title or self.feed_url}")
                        self._is_connected = True
                        self._last_error = None
                        return True
                        
                    except ET.ParseError as e:
                        self.logger.error(f"Invalid RSS/XML format: {e}")
                        self._last_error = f"Invalid XML: {e}"
                        return False
                else:
                    self.logger.error(f"Failed to connect to RSS feed: HTTP {response.status}")
                    self._last_error = f"HTTP {response.status}"
                    return False
                    
        except Exception as e:
            self.logger.error(f"Failed to connect to RSS feed: {e}")
            self._last_error = str(e)
            return False
    
    async def disconnect(self) -> None:
        """Disconnect from RSS feed"""
        if self.session:
            try:
                await self.session.close()
                self.logger.info(f"Disconnected from RSS feed: {self.feed_title or self.feed_url}")
            except Exception as e:
                self.logger.error(f"Error disconnecting from RSS feed: {e}")
            finally:
                self.session = None
                self._is_connected = False
    
    def _get_text(self, element) -> Optional[str]:
        """Safely extract text from XML element"""
        if element is not None:
            return element.text
        return None
    
    async def parse_messages(self, limit: int = 100) -> List[ParsedSignal]:
        """Parse recent items from RSS feed"""
        if not self._is_connected or not self.session:
            self.logger.error("Not connected to RSS feed")
            return []
        
        signals = []
        
        try:
            async with self.session.get(self.feed_url) as response:
                if response.status == 200:
                    content = await response.text()
                    root = ET.fromstring(content)
                    
                    items = []
                    
                    # Parse RSS format
                    if root.tag == 'rss':
                        channel = root.find('channel')
                        if channel is not None:
                            items = channel.findall('item')
                    
                    # Parse Atom format
                    elif root.tag.endswith('feed'):
                        items = root.findall('.//{http://www.w3.org/2005/Atom}entry')
                    
                    # Limit items
                    items = items[:min(limit, self.max_items)]
                    
                    for item in items:
                        signal = await self.parse_single_message(item)
                        if signal:
                            signals.append(signal)
                    
                    self.logger.info(f"Parsed {len(signals)} signals from {len(items)} RSS items")
                else:
                    self.logger.error(f"Failed to fetch RSS feed: HTTP {response.status}")
                    self._last_error = f"HTTP {response.status}"
            
        except Exception as e:
            self.logger.error(f"Error parsing RSS messages: {e}")
            self._last_error = str(e)
        
        return signals
    
    async def parse_single_message(self, item) -> Optional[ParsedSignal]:
        """Parse a single RSS item"""
        if item is None:
            return None
        
        try:
            # Extract content based on format
            if item.tag == 'item':  # RSS format
                title = self._get_text(item.find('title')) or ''
                description = self._get_text(item.find('description')) or ''
                link = self._get_text(item.find('link')) or ''
                pub_date = self._get_text(item.find('pubDate'))
                guid = self._get_text(item.find('guid'))
                
            elif item.tag.endswith('entry'):  # Atom format
                title = self._get_text(item.find('.//{http://www.w3.org/2005/Atom}title')) or ''
                summary = item.find('.//{http://www.w3.org/2005/Atom}summary')
                description = self._get_text(summary) or ''
                link_elem = item.find('.//{http://www.w3.org/2005/Atom}link')
                link = link_elem.get('href') if link_elem is not None else ''
                updated = self._get_text(item.find('.//{http://www.w3.org/2005/Atom}updated'))
                pub_date = updated
                guid = self._get_text(item.find('.//{http://www.w3.org/2005/Atom}id'))
            
            else:
                return None
            
            # Combine title and description for analysis
            text = f"{title}\n{description}".strip()
            
            if not text:
                return None
            
            # Extract symbol
            symbol = self._extract_symbol(text)
            if not symbol:
                return None
            
            # Check if symbol is allowed
            if (self.config.allowed_symbols and 
                symbol not in self.config.allowed_symbols):
                return None
            
            # Detect signal type
            signal_type = self._detect_signal_type_rss(text)
            if not signal_type:
                return None
            
            # Parse timestamp
            timestamp = self._parse_rss_date(pub_date) if pub_date else datetime.utcnow()
            
            # Extract price if mentioned
            entry_price = self._extract_price(text)
            
            # Create parsed signal
            signal = ParsedSignal(
                symbol=symbol,
                signal_type=signal_type,
                source_channel=self.feed_title or urlparse(self.feed_url).netloc,
                timestamp=timestamp,
                raw_message=text,
                entry_price=entry_price,
                message_id=guid or link,
                channel_type=ChannelType.RSS,
                additional_data={
                    'title': title,
                    'description': description,
                    'link': link,
                    'feed_url': self.feed_url,
                    'feed_title': self.feed_title
                }
            )
            
            # Calculate confidence
            signal.confidence = self._calculate_confidence_rss(signal, text)
            
            # Check minimum confidence threshold
            if signal.confidence < self.config.min_confidence:
                return None
            
            return signal
            
        except Exception as e:
            self.logger.error(f"Error parsing RSS item: {e}")
            return None
    
    def _detect_signal_type_rss(self, text: str) -> Optional[SignalType]:
        """Detect signal type from RSS content"""
        text_lower = text.lower()
        
        # Count keyword occurrences
        bullish_count = sum(1 for keyword in self.bullish_keywords if keyword in text_lower)
        bearish_count = sum(1 for keyword in self.bearish_keywords if keyword in text_lower)
        neutral_count = sum(1 for keyword in self.neutral_keywords if keyword in text_lower)
        
        # Determine signal type
        if bullish_count > bearish_count and bullish_count > 0:
            return SignalType.BUY
        elif bearish_count > bullish_count and bearish_count > 0:
            return SignalType.SELL
        elif neutral_count > 0 or any(keyword in text_lower for keyword in ['analysis', 'report', 'update']):
            return SignalType.ALERT
        
        return None
    
    def _calculate_confidence_rss(self, signal: ParsedSignal, text: str) -> float:
        """Calculate confidence score for RSS signal"""
        confidence = super()._calculate_confidence(signal)
        
        # RSS-specific confidence adjustments
        text_lower = text.lower()
        
        # Increase confidence for reputable sources
        feed_domain = urlparse(self.feed_url).netloc.lower()
        if any(source in feed_domain for source in self.crypto_news_sources):
            confidence += 0.15
        
        # Increase confidence for detailed analysis
        if len(text) > 500:  # Longer articles tend to be more detailed
            confidence += 0.1
        
        # Increase confidence for specific price mentions
        if signal.entry_price:
            confidence += 0.1
        
        # Increase confidence for technical terms
        technical_terms = ['support', 'resistance', 'fibonacci', 'rsi', 'macd', 'bollinger']
        tech_count = sum(1 for term in technical_terms if term in text_lower)
        if tech_count > 0:
            confidence += min(tech_count * 0.05, 0.15)
        
        # Decrease confidence for very old articles
        if signal.timestamp:
            age_hours = (datetime.utcnow() - signal.timestamp).total_seconds() / 3600
            if age_hours > 24:  # Older than 24 hours
                confidence -= min((age_hours - 24) / 24 * 0.2, 0.3)
        
        return max(0.0, min(confidence, 1.0))
    
    def _parse_rss_date(self, date_str: str) -> datetime:
        """Parse RSS date string to datetime"""
        if not date_str:
            return datetime.utcnow()
        
        # Common RSS date formats
        formats = [
            '%a, %d %b %Y %H:%M:%S %z',  # RFC 822
            '%a, %d %b %Y %H:%M:%S GMT',
            '%Y-%m-%dT%H:%M:%S%z',       # ISO 8601
            '%Y-%m-%dT%H:%M:%SZ',
            '%Y-%m-%d %H:%M:%S',
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        # If all formats fail, return current time
        self.logger.warning(f"Could not parse date: {date_str}")
        return datetime.utcnow()


# Auto-register the RSS parser
def register_rss_parser():
    """Register RSS parser with the global registry"""
    from .parser_registry import register_parser
    register_parser(ChannelType.RSS, RSSParser)

# Register on import
register_rss_parser()
logger.info("RSS parser registered successfully")
