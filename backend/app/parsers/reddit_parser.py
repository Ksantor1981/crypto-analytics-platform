"""
Reddit Parser Plugin - Reddit subreddit parser using BaseChannelParser
Part of Task 2.1.2: Реализация Reddit парсера
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

class RedditParser(BaseChannelParser):
    """
    Reddit subreddit parser plugin
    
    Parses crypto signals from Reddit subreddits using Reddit API
    """
    
    def __init__(self, config: ChannelConfig):
        super().__init__(config)
        
        # Extract Reddit-specific config
        parser_config = config.parser_config or {}
        self.client_id = parser_config.get('client_id')
        self.client_secret = parser_config.get('client_secret')
        self.user_agent = parser_config.get('user_agent', 'CryptoAnalytics/1.0')
        
        # Reddit API settings
        self.base_url = 'https://www.reddit.com'
        self.oauth_url = 'https://oauth.reddit.com'
        self.access_token = None
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Extract subreddit from URL
        self.subreddit = self._extract_subreddit_from_url(config.url)
        
        # Signal parsing patterns for Reddit
        self.crypto_keywords = [
            'buy', 'sell', 'long', 'short', 'bullish', 'bearish',
            'pump', 'dump', 'moon', 'crash', 'hodl', 'dip',
            'breakout', 'resistance', 'support', 'target', 'stop loss'
        ]
        
        # Common crypto subreddits
        self.crypto_subreddits = [
            'cryptocurrency', 'cryptomarkets', 'bitcoin', 'ethereum',
            'altcoin', 'defi', 'cryptomoonshots', 'satoshistreetbets'
        ]
    
    def _extract_subreddit_from_url(self, url: str) -> str:
        """Extract subreddit name from Reddit URL"""
        # Handle various Reddit URL formats
        if 'reddit.com/r/' in url:
            # https://www.reddit.com/r/cryptocurrency/
            parts = url.split('/r/')
            if len(parts) > 1:
                subreddit = parts[1].split('/')[0]
                return subreddit
        elif url.startswith('r/'):
            # r/cryptocurrency
            return url[2:]
        else:
            # Just subreddit name
            return url
        
        return url
    
    def validate_config(self) -> bool:
        """Validate Reddit parser configuration"""
        if not self.subreddit:
            self.logger.error("Reddit subreddit is required")
            return False
        
        # Client credentials are optional for read-only access
        # Reddit allows some access without authentication
        
        return True
    
    async def connect(self) -> bool:
        """Connect to Reddit API"""
        try:
            if not self.validate_config():
                return False
            
            # Create HTTP session
            self.session = aiohttp.ClientSession(
                headers={'User-Agent': self.user_agent}
            )
            
            # Try to get access token if credentials provided
            if self.client_id and self.client_secret:
                success = await self._authenticate()
                if not success:
                    self.logger.warning("Authentication failed, using read-only access")
            
            # Test connection by fetching subreddit info
            test_url = f"{self.base_url}/r/{self.subreddit}/about.json"
            
            async with self.session.get(test_url) as response:
                if response.status == 200:
                    data = await response.json()
                    if 'data' in data:
                        self.logger.info(f"Connected to Reddit subreddit: r/{self.subreddit}")
                        self._is_connected = True
                        self._last_error = None
                        return True
                    else:
                        self.logger.error(f"Invalid subreddit: r/{self.subreddit}")
                        self._last_error = "Invalid subreddit"
                        return False
                else:
                    self.logger.error(f"Failed to connect to Reddit: HTTP {response.status}")
                    self._last_error = f"HTTP {response.status}"
                    return False
                    
        except Exception as e:
            self.logger.error(f"Failed to connect to Reddit: {e}")
            self._last_error = str(e)
            return False
    
    async def _authenticate(self) -> bool:
        """Authenticate with Reddit API"""
        try:
            auth_data = {
                'grant_type': 'client_credentials'
            }
            
            auth = aiohttp.BasicAuth(self.client_id, self.client_secret)
            
            async with self.session.post(
                'https://www.reddit.com/api/v1/access_token',
                data=auth_data,
                auth=auth
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    self.access_token = data.get('access_token')
                    
                    # Update session headers with token
                    self.session.headers.update({
                        'Authorization': f'Bearer {self.access_token}'
                    })
                    
                    self.logger.info("Reddit authentication successful")
                    return True
                else:
                    self.logger.error(f"Reddit authentication failed: HTTP {response.status}")
                    return False
                    
        except Exception as e:
            self.logger.error(f"Reddit authentication error: {e}")
            return False
    
    async def disconnect(self) -> None:
        """Disconnect from Reddit API"""
        if self.session:
            try:
                await self.session.close()
                self.logger.info(f"Disconnected from Reddit subreddit: r/{self.subreddit}")
            except Exception as e:
                self.logger.error(f"Error disconnecting from Reddit: {e}")
            finally:
                self.session = None
                self.access_token = None
                self._is_connected = False
    
    async def parse_messages(self, limit: int = 100) -> List[ParsedSignal]:
        """Parse recent posts from Reddit subreddit"""
        if not self._is_connected or not self.session:
            self.logger.error("Not connected to Reddit")
            return []
        
        signals = []
        
        try:
            # Get recent posts from subreddit
            # Use different endpoints based on authentication
            if self.access_token:
                url = f"{self.oauth_url}/r/{self.subreddit}/new"
            else:
                url = f"{self.base_url}/r/{self.subreddit}/new.json"
            
            params = {
                'limit': min(limit, 100),  # Reddit API limit
                'raw_json': 1
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if 'data' in data and 'children' in data['data']:
                        posts = data['data']['children']
                        
                        for post_data in posts:
                            post = post_data.get('data', {})
                            signal = await self.parse_single_message(post)
                            if signal:
                                signals.append(signal)
                    
                    self.logger.info(f"Parsed {len(signals)} signals from {len(posts)} Reddit posts")
                else:
                    self.logger.error(f"Failed to fetch Reddit posts: HTTP {response.status}")
                    self._last_error = f"HTTP {response.status}"
            
        except Exception as e:
            self.logger.error(f"Error parsing Reddit messages: {e}")
            self._last_error = str(e)
        
        return signals
    
    async def parse_single_message(self, post: Dict[str, Any]) -> Optional[ParsedSignal]:
        """Parse a single Reddit post"""
        if not post:
            return None
        
        # Combine title and selftext for analysis
        title = post.get('title', '')
        selftext = post.get('selftext', '')
        text = f"{title}\n{selftext}".strip()
        
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
        signal_type = self._detect_signal_type_reddit(text)
        if not signal_type:
            return None
        
        # Extract prices
        entry_price = self._extract_price(text)
        
        # Create timestamp from Reddit post time
        created_utc = post.get('created_utc', 0)
        timestamp = datetime.utcfromtimestamp(created_utc) if created_utc else datetime.utcnow()
        
        # Create parsed signal
        signal = ParsedSignal(
            symbol=symbol,
            signal_type=signal_type,
            source_channel=f"r/{self.subreddit}",
            timestamp=timestamp,
            raw_message=text,
            entry_price=entry_price,
            message_id=post.get('id'),
            author=post.get('author'),
            channel_type=ChannelType.REDDIT,
            additional_data={
                'subreddit': self.subreddit,
                'score': post.get('score', 0),
                'upvote_ratio': post.get('upvote_ratio', 0),
                'num_comments': post.get('num_comments', 0),
                'url': post.get('url'),
                'permalink': post.get('permalink'),
                'flair_text': post.get('link_flair_text')
            }
        )
        
        # Calculate confidence
        signal.confidence = self._calculate_confidence_reddit(signal, post)
        
        # Check minimum confidence threshold
        if signal.confidence < self.config.min_confidence:
            return None
        
        return signal
    
    def _detect_signal_type_reddit(self, text: str) -> Optional[SignalType]:
        """Detect signal type from Reddit post"""
        text_lower = text.lower()
        
        # Reddit-specific signal detection
        buy_indicators = [
            'buy', 'long', 'bullish', 'pump', 'moon', 'hodl',
            'accumulate', 'dip buy', 'buy the dip', 'going up',
            'breakout', 'bull run', 'to the moon'
        ]
        
        sell_indicators = [
            'sell', 'short', 'bearish', 'dump', 'crash',
            'take profit', 'exit', 'going down', 'bear market',
            'correction', 'bubble', 'overvalued'
        ]
        
        # Count indicators
        buy_count = sum(1 for indicator in buy_indicators if indicator in text_lower)
        sell_count = sum(1 for indicator in sell_indicators if indicator in text_lower)
        
        if buy_count > sell_count and buy_count > 0:
            return SignalType.BUY
        elif sell_count > buy_count and sell_count > 0:
            return SignalType.SELL
        
        # Check for discussion/analysis posts
        if any(word in text_lower for word in ['analysis', 'discussion', 'thoughts', 'opinion']):
            return SignalType.ALERT
        
        return None
    
    def _calculate_confidence_reddit(self, signal: ParsedSignal, post: Dict[str, Any]) -> float:
        """Calculate confidence score for Reddit signal"""
        confidence = super()._calculate_confidence(signal)
        
        # Reddit-specific confidence adjustments
        score = post.get('score', 0)
        upvote_ratio = post.get('upvote_ratio', 0)
        num_comments = post.get('num_comments', 0)
        
        # Increase confidence based on community engagement
        if score > 10:
            confidence += min(score / 100, 0.2)  # Max 0.2 boost
        
        if upvote_ratio > 0.8:
            confidence += 0.1
        
        if num_comments > 5:
            confidence += min(num_comments / 50, 0.1)  # Max 0.1 boost
        
        # Increase confidence for posts with flair
        if post.get('link_flair_text'):
            confidence += 0.05
        
        # Decrease confidence for very new posts (less community validation)
        created_utc = post.get('created_utc', 0)
        if created_utc:
            post_age_hours = (datetime.utcnow().timestamp() - created_utc) / 3600
            if post_age_hours < 1:  # Less than 1 hour old
                confidence -= 0.1
        
        # Adjust based on subreddit type
        if self.subreddit.lower() in ['cryptomoonshots', 'satoshistreetbets']:
            # These are more speculative subreddits
            confidence -= 0.1
        elif self.subreddit.lower() in ['cryptocurrency', 'bitcoin', 'ethereum']:
            # These are more established subreddits
            confidence += 0.05
        
        return max(0.0, min(confidence, 1.0))


# Auto-register the Reddit parser
def register_reddit_parser():
    """Register Reddit parser with the global registry"""
    from .parser_registry import register_parser
    register_parser(ChannelType.REDDIT, RedditParser)

# Register on import
register_reddit_parser()
logger.info("Reddit parser registered successfully")
