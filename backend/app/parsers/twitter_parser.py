"""
Twitter/X Parser Plugin - Twitter/X parser using BaseChannelParser
Part of Task 2.1.3: Реализация Twitter/X парсера
"""
import asyncio
import logging
import re
from typing import List, Optional, Any, Dict
from datetime import datetime, timedelta
from decimal import Decimal
import aiohttp
import json

from .base_parser import (
    BaseChannelParser, ChannelConfig, ChannelType, 
    ParsedSignal, SignalType
)

logger = logging.getLogger(__name__)

class TwitterParser(BaseChannelParser):
    """
    Twitter/X parser plugin
    
    Parses crypto signals from Twitter/X using Twitter API v2
    """
    
    def __init__(self, config: ChannelConfig):
        super().__init__(config)
        
        # Extract Twitter-specific config
        parser_config = config.parser_config or {}
        self.bearer_token = parser_config.get('bearer_token')
        self.api_key = parser_config.get('api_key')
        self.api_secret = parser_config.get('api_secret')
        self.access_token = parser_config.get('access_token')
        self.access_token_secret = parser_config.get('access_token_secret')
        
        # Twitter API settings
        self.base_url = 'https://api.twitter.com/2'
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Extract username from URL or config
        self.username = self._extract_username_from_url(config.url)
        self.user_id = None
        
        # Twitter-specific patterns
        self.crypto_hashtags = [
            '#bitcoin', '#btc', '#ethereum', '#eth', '#crypto',
            '#cryptocurrency', '#defi', '#nft', '#web3', '#blockchain'
        ]
        
        # Signal patterns for Twitter
        self.buy_indicators = [
            'buy', 'long', 'bullish', 'pump', 'moon', 'hodl',
            'accumulate', 'dip', 'breakout', 'bull', 'rocket',
            '🚀', '📈', '💎', '🌙', '🔥'
        ]
        
        self.sell_indicators = [
            'sell', 'short', 'bearish', 'dump', 'crash',
            'exit', 'take profit', 'tp', 'bear', 'correction',
            '📉', '⚠️', '🔻', '💀'
        ]
        
        # Influential crypto Twitter accounts
        self.crypto_influencers = [
            'elonmusk', 'michael_saylor', 'cz_binance', 'vitalikbuterin',
            'aantonop', 'naval', 'balajis', 'coinbase', 'binance'
        ]
    
    def _extract_username_from_url(self, url: str) -> str:
        """Extract username from Twitter URL"""
        # Handle various Twitter URL formats
        if 'twitter.com/' in url or 'x.com/' in url:
            # https://twitter.com/username or https://x.com/username
            parts = url.split('/')
            for i, part in enumerate(parts):
                if part in ['twitter.com', 'x.com'] and i + 1 < len(parts):
                    username = parts[i + 1]
                    # Remove @ if present
                    return username.lstrip('@')
        elif url.startswith('@'):
            # @username
            return url[1:]
        else:
            # Just username
            return url
        
        return url
    
    def validate_config(self) -> bool:
        """Validate Twitter parser configuration"""
        if not self.username:
            self.logger.error("Twitter username is required")
            return False
        
        if not self.bearer_token:
            self.logger.error("Twitter Bearer Token is required")
            return False
        
        return True
    
    async def connect(self) -> bool:
        """Connect to Twitter API"""
        try:
            if not self.validate_config():
                return False
            
            # Create HTTP session with authentication
            headers = {
                'Authorization': f'Bearer {self.bearer_token}',
                'User-Agent': 'CryptoAnalytics/1.0'
            }
            
            self.session = aiohttp.ClientSession(headers=headers)
            
            # Get user ID from username
            user_url = f"{self.base_url}/users/by/username/{self.username}"
            params = {
                'user.fields': 'id,name,username,public_metrics,verified'
            }
            
            async with self.session.get(user_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if 'data' in data:
                        user_data = data['data']
                        self.user_id = user_data['id']
                        
                        self.logger.info(f"Connected to Twitter user: @{self.username} (ID: {self.user_id})")
                        self._is_connected = True
                        self._last_error = None
                        return True
                    else:
                        self.logger.error(f"User not found: @{self.username}")
                        self._last_error = "User not found"
                        return False
                elif response.status == 401:
                    self.logger.error("Twitter API authentication failed")
                    self._last_error = "Authentication failed"
                    return False
                elif response.status == 429:
                    self.logger.error("Twitter API rate limit exceeded")
                    self._last_error = "Rate limit exceeded"
                    return False
                else:
                    self.logger.error(f"Failed to connect to Twitter: HTTP {response.status}")
                    self._last_error = f"HTTP {response.status}"
                    return False
                    
        except Exception as e:
            self.logger.error(f"Failed to connect to Twitter: {e}")
            self._last_error = str(e)
            return False
    
    async def disconnect(self) -> None:
        """Disconnect from Twitter API"""
        if self.session:
            try:
                await self.session.close()
                self.logger.info(f"Disconnected from Twitter user: @{self.username}")
            except Exception as e:
                self.logger.error(f"Error disconnecting from Twitter: {e}")
            finally:
                self.session = None
                self.user_id = None
                self._is_connected = False
    
    async def parse_messages(self, limit: int = 100) -> List[ParsedSignal]:
        """Parse recent tweets from user"""
        if not self._is_connected or not self.session or not self.user_id:
            self.logger.error("Not connected to Twitter")
            return []
        
        signals = []
        
        try:
            # Get user tweets
            tweets_url = f"{self.base_url}/users/{self.user_id}/tweets"
            params = {
                'max_results': min(limit, 100),  # Twitter API limit
                'tweet.fields': 'id,text,created_at,public_metrics,context_annotations,entities',
                'exclude': 'retweets,replies'  # Focus on original tweets
            }
            
            async with self.session.get(tweets_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if 'data' in data:
                        tweets = data['data']
                        
                        for tweet in tweets:
                            signal = await self.parse_single_message(tweet)
                            if signal:
                                signals.append(signal)
                    
                    self.logger.info(f"Parsed {len(signals)} signals from {len(tweets)} tweets")
                elif response.status == 429:
                    self.logger.warning("Twitter API rate limit exceeded")
                    self._last_error = "Rate limit exceeded"
                else:
                    self.logger.error(f"Failed to fetch tweets: HTTP {response.status}")
                    self._last_error = f"HTTP {response.status}"
            
        except Exception as e:
            self.logger.error(f"Error parsing Twitter messages: {e}")
            self._last_error = str(e)
        
        return signals
    
    async def parse_single_message(self, tweet: Dict[str, Any]) -> Optional[ParsedSignal]:
        """Parse a single tweet"""
        if not tweet:
            return None
        
        text = tweet.get('text', '')
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
        signal_type = self._detect_signal_type_twitter(text)
        if not signal_type:
            return None
        
        # Extract prices
        entry_price = self._extract_price(text)
        
        # Parse timestamp
        created_at = tweet.get('created_at')
        timestamp = self._parse_twitter_date(created_at) if created_at else datetime.utcnow()
        
        # Create parsed signal
        signal = ParsedSignal(
            symbol=symbol,
            signal_type=signal_type,
            source_channel=f"@{self.username}",
            timestamp=timestamp,
            raw_message=text,
            entry_price=entry_price,
            message_id=tweet.get('id'),
            author=self.username,
            channel_type=ChannelType.TWITTER,
            additional_data={
                'tweet_id': tweet.get('id'),
                'username': self.username,
                'public_metrics': tweet.get('public_metrics', {}),
                'context_annotations': tweet.get('context_annotations', []),
                'entities': tweet.get('entities', {}),
                'url': f"https://twitter.com/{self.username}/status/{tweet.get('id')}"
            }
        )
        
        # Calculate confidence
        signal.confidence = self._calculate_confidence_twitter(signal, tweet)
        
        # Check minimum confidence threshold
        if signal.confidence < self.config.min_confidence:
            return None
        
        return signal
    
    def _detect_signal_type_twitter(self, text: str) -> Optional[SignalType]:
        """Detect signal type from tweet"""
        text_lower = text.lower()
        
        # Count indicators
        buy_count = sum(1 for indicator in self.buy_indicators if indicator in text_lower)
        sell_count = sum(1 for indicator in self.sell_indicators if indicator in text_lower)
        
        # Check for price targets and technical analysis
        if any(pattern in text_lower for pattern in ['target', 'tp', 'take profit']):
            if buy_count > sell_count:
                return SignalType.BUY
            elif sell_count > buy_count:
                return SignalType.SELL
        
        if buy_count > sell_count and buy_count > 0:
            return SignalType.BUY
        elif sell_count > buy_count and sell_count > 0:
            return SignalType.SELL
        
        # Check for analysis/discussion tweets
        if any(word in text_lower for word in ['analysis', 'thoughts', 'opinion', 'update']):
            return SignalType.ALERT
        
        return None
    
    def _calculate_confidence_twitter(self, signal: ParsedSignal, tweet: Dict[str, Any]) -> float:
        """Calculate confidence score for Twitter signal"""
        confidence = super()._calculate_confidence(signal)
        
        # Twitter-specific confidence adjustments
        public_metrics = tweet.get('public_metrics', {})
        
        # Increase confidence based on engagement
        retweet_count = public_metrics.get('retweet_count', 0)
        like_count = public_metrics.get('like_count', 0)
        reply_count = public_metrics.get('reply_count', 0)
        
        if retweet_count > 10:
            confidence += min(retweet_count / 100, 0.2)
        
        if like_count > 50:
            confidence += min(like_count / 500, 0.15)
        
        if reply_count > 5:
            confidence += min(reply_count / 50, 0.1)
        
        # Increase confidence for verified/influential accounts
        if self.username.lower() in self.crypto_influencers:
            confidence += 0.2
        
        # Increase confidence for crypto-related context
        context_annotations = tweet.get('context_annotations', [])
        crypto_contexts = ['Cryptocurrency', 'Bitcoin', 'Blockchain', 'Finance']
        if any(ctx.get('domain', {}).get('name') in crypto_contexts for ctx in context_annotations):
            confidence += 0.1
        
        # Increase confidence for hashtags
        entities = tweet.get('entities', {})
        hashtags = entities.get('hashtags', [])
        crypto_hashtag_count = sum(1 for tag in hashtags 
                                 if f"#{tag.get('tag', '').lower()}" in self.crypto_hashtags)
        if crypto_hashtag_count > 0:
            confidence += min(crypto_hashtag_count * 0.05, 0.15)
        
        # Decrease confidence for very recent tweets (less validation time)
        if signal.timestamp:
            age_minutes = (datetime.utcnow() - signal.timestamp).total_seconds() / 60
            if age_minutes < 30:  # Less than 30 minutes old
                confidence -= 0.1
        
        return max(0.0, min(confidence, 1.0))
    
    def _parse_twitter_date(self, date_str: str) -> datetime:
        """Parse Twitter date string to datetime"""
        if not date_str:
            return datetime.utcnow()
        
        try:
            # Twitter API v2 uses ISO 8601 format
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except ValueError:
            self.logger.warning(f"Could not parse Twitter date: {date_str}")
            return datetime.utcnow()


# Auto-register the Twitter parser
def register_twitter_parser():
    """Register Twitter parser with the global registry"""
    from .parser_registry import register_parser
    register_parser(ChannelType.TWITTER, TwitterParser)

# Register on import
register_twitter_parser()
logger.info("Twitter parser registered successfully")
