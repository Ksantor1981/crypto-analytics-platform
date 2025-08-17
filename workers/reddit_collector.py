"""
Reddit Signal Collector - Active Reddit integration
Part of Task 1.1.1: Активация Reddit интеграции
"""
import asyncio
import logging
import os
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import aiohttp
import json

from .real_data_config import REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT
from .telegram.telegram_client import TelegramSignalCollector

logger = logging.getLogger(__name__)

class RedditSignalCollector:
    """
    Active Reddit signal collector for crypto analytics platform
    Collects signals from popular crypto subreddits
    """
    
    def __init__(self):
        # Reddit API configuration
        self.client_id = REDDIT_CLIENT_ID
        self.client_secret = REDDIT_CLIENT_SECRET
        self.user_agent = REDDIT_USER_AGENT
        
        # Reddit API endpoints
        self.base_url = "https://www.reddit.com"
        self.oauth_url = "https://oauth.reddit.com"
        
        # Popular crypto subreddits for signal collection
        self.crypto_subreddits = [
            'cryptocurrency',      # General crypto discussion
            'cryptomarkets',       # Market analysis
            'bitcoin',             # Bitcoin specific
            'ethereum',            # Ethereum specific
            'altcoin',             # Altcoin discussion
            'defi',                # DeFi projects
            'cryptomoonshots',     # High-risk altcoins
            'satoshistreetbets',   # Meme coins and speculation
            'cryptosignals',       # Trading signals
            'cryptotrading',       # Trading discussion
            'binance',             # Binance specific
            'coinbase'             # Coinbase specific
        ]
        
        # Signal patterns for Reddit posts
        self.signal_patterns = [
            # Pattern for LONG signals
            r'(?i)(long|buy|bullish|moon|pump).*?(\w+usdt).*?(\d+\.?\d*).*?(\d+\.?\d*).*?(\d+\.?\d*)',
            # Pattern for SHORT signals  
            r'(?i)(short|sell|bearish|dump|crash).*?(\w+usdt).*?(\d+\.?\d*).*?(\d+\.?\d*).*?(\d+\.?\d*)',
            # Generic crypto pattern
            r'(\w+usdt).*?(long|short|buy|sell).*?(\d+\.?\d*).*?(\d+\.?\d*).*?(\d+\.?\d*)',
            # Pattern with emojis
            r'🚀.*?(\w+usdt).*?(\d+\.?\d*).*?(\d+\.?\d*).*?(\d+\.?\d*)',
            r'📉.*?(\w+usdt).*?(\d+\.?\d*).*?(\d+\.?\d*).*?(\d+\.?\d*)',
            # Pattern with $ symbols
            r'\$(\w+).*?(long|short|buy|sell).*?\$(\d+\.?\d*).*?\$(\d+\.?\d*).*?\$(\d+\.?\d*)'
        ]
        
        # Supported crypto pairs
        self.supported_pairs = [
            'BTCUSDT', 'ETHUSDT', 'ADAUSDT', 'SOLUSDT', 'DOGEUSDT',
            'BNBUSDT', 'XRPUSDT', 'DOTUSDT', 'LINKUSDT', 'MATICUSDT',
            'AVAXUSDT', 'UNIUSDT', 'ATOMUSDT', 'LTCUSDT', 'BCHUSDT',
            'SHIBUSDT', 'PEPEUSDT', 'FLOKIUSDT', 'BONKUSDT'
        ]
        
        # Collection settings
        self.collection_interval = 300  # 5 minutes
        self.max_posts_per_subreddit = 25
        self.time_filter = "day"  # day, week, month, year, all
        
        # Statistics
        self.stats = {
            'total_signals_collected': 0,
            'last_collection_time': None,
            'subreddit_stats': {},
            'errors': []
        }
    
    async def start_collection_loop(self):
        """Start continuous Reddit signal collection"""
        logger.info("🚀 Starting Reddit signal collection loop")
        
        while True:
            try:
                await self.collect_signals_from_all_subreddits()
                logger.info(f"✅ Reddit collection completed. Total signals: {self.stats['total_signals_collected']}")
                
                # Wait for next collection cycle
                await asyncio.sleep(self.collection_interval)
                
            except Exception as e:
                logger.error(f"❌ Error in Reddit collection loop: {e}")
                self.stats['errors'].append({
                    'timestamp': datetime.now().isoformat(),
                    'error': str(e)
                })
                await asyncio.sleep(60)  # Wait 1 minute on error
    
    async def collect_signals_from_all_subreddits(self) -> Dict[str, Any]:
        """Collect signals from all configured subreddits"""
        logger.info(f"📡 Collecting signals from {len(self.crypto_subreddits)} subreddits")
        
        all_signals = []
        subreddit_stats = {}
        
        async with aiohttp.ClientSession() as session:
            for subreddit in self.crypto_subreddits:
                try:
                    signals = await self._collect_from_subreddit(
                        session, subreddit, self.max_posts_per_subreddit, self.time_filter
                    )
                    all_signals.extend(signals)
                    subreddit_stats[subreddit] = len(signals)
                    
                    logger.info(f"📊 Collected {len(signals)} signals from r/{subreddit}")
                    
                    # Respect Reddit rate limits
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    logger.error(f"❌ Error collecting from r/{subreddit}: {e}")
                    subreddit_stats[subreddit] = 0
        
        # Process and save signals
        processed_signals = await self._process_signals(all_signals)
        
        # Update statistics
        self.stats['total_signals_collected'] += len(processed_signals)
        self.stats['last_collection_time'] = datetime.now().isoformat()
        self.stats['subreddit_stats'] = subreddit_stats
        
        return {
            "status": "success",
            "total_signals": len(all_signals),
            "processed_signals": len(processed_signals),
            "subreddit_stats": subreddit_stats,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _collect_from_subreddit(
        self, 
        session: aiohttp.ClientSession,
        subreddit: str, 
        limit: int,
        time_filter: str
    ) -> List[Dict[str, Any]]:
        """Collect posts from a specific subreddit"""
        url = f"{self.base_url}/r/{subreddit}/new.json"
        params = {
            'limit': min(limit, 100),
            't': time_filter,
            'raw_json': 1
        }
        
        headers = {
            'User-Agent': self.user_agent
        }
        
        try:
            async with session.get(url, params=params, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if 'data' in data and 'children' in data['data']:
                        posts = data['data']['children']
                        signals = []
                        
                        for post_data in posts:
                            post = post_data['data']
                            signal = await self._extract_signal_from_post(post, subreddit)
                            if signal:
                                signals.append(signal)
                        
                        return signals
                    else:
                        logger.warning(f"No data found for r/{subreddit}")
                        return []
                else:
                    logger.error(f"HTTP {response.status} for r/{subreddit}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error fetching from r/{subreddit}: {e}")
            return []
    
    async def _extract_signal_from_post(self, post: Dict[str, Any], subreddit: str) -> Optional[Dict[str, Any]]:
        """Extract trading signal from Reddit post"""
        title = post.get('title', '')
        selftext = post.get('selftext', '')
        content = f"{title} {selftext}".lower()
        
        # Skip non-signal posts
        skip_keywords = ['news', 'update', 'announcement', 'reminder', 'analysis only', 'discussion', 'question']
        if any(keyword in content for keyword in skip_keywords):
            return None
        
        # Look for signal patterns
        for pattern in self.signal_patterns:
            import re
            matches = re.findall(pattern, content, re.IGNORECASE)
            
            for match in matches:
                if len(match) >= 3:
                    signal = self._parse_signal_match(match, post, subreddit)
                    if signal:
                        return signal
        
        return None
    
    def _parse_signal_match(
        self, 
        match: tuple, 
        post: Dict[str, Any], 
        subreddit: str
    ) -> Optional[Dict[str, Any]]:
        """Parse signal from regex match"""
        try:
            # Extract components based on pattern
            if len(match) >= 5:
                if match[0].lower() in ['long', 'buy', 'bullish', 'moon', 'pump']:
                    symbol = match[1].upper()
                    signal_type = 'LONG'
                    entry_price = float(match[2])
                    target_price = float(match[3])
                    stop_loss = float(match[4])
                elif match[0].lower() in ['short', 'sell', 'bearish', 'dump', 'crash']:
                    symbol = match[1].upper()
                    signal_type = 'SHORT'
                    entry_price = float(match[2])
                    target_price = float(match[3])
                    stop_loss = float(match[4])
                else:
                    # Generic pattern
                    symbol = match[0].upper()
                    signal_type = 'LONG' if match[1].lower() in ['long', 'buy'] else 'SHORT'
                    entry_price = float(match[2])
                    target_price = float(match[3])
                    stop_loss = float(match[4])
            else:
                return None
            
            # Validate symbol
            if symbol not in self.supported_pairs:
                return None
            
            # Create timestamp from Reddit post time
            created_utc = post.get('created_utc', 0)
            timestamp = datetime.utcfromtimestamp(created_utc) if created_utc else datetime.utcnow()
            
            # Calculate confidence based on post metrics
            score = post.get('score', 0)
            upvote_ratio = post.get('upvote_ratio', 0)
            num_comments = post.get('num_comments', 0)
            
            confidence = self._calculate_confidence(score, upvote_ratio, num_comments)
            
            return {
                'symbol': symbol,
                'signal_type': signal_type,
                'entry_price': entry_price,
                'target_price': target_price,
                'stop_loss': stop_loss,
                'source': f"r/{subreddit}",
                'timestamp': timestamp.isoformat(),
                'confidence': confidence,
                'raw_text': f"{post.get('title', '')} {post.get('selftext', '')}",
                'post_id': post.get('id'),
                'author': post.get('author'),
                'score': score,
                'upvote_ratio': upvote_ratio,
                'num_comments': num_comments,
                'url': post.get('url'),
                'permalink': post.get('permalink')
            }
            
        except Exception as e:
            logger.warning(f"Error parsing signal match: {e}")
            return None
    
    def _calculate_confidence(self, score: int, upvote_ratio: float, num_comments: int) -> float:
        """Calculate confidence score for Reddit signal"""
        # Base confidence
        confidence = 0.5
        
        # Adjust based on score (upvotes - downvotes)
        if score > 10:
            confidence += 0.2
        elif score > 5:
            confidence += 0.1
        elif score < 0:
            confidence -= 0.1
        
        # Adjust based on upvote ratio
        if upvote_ratio > 0.8:
            confidence += 0.15
        elif upvote_ratio > 0.6:
            confidence += 0.1
        elif upvote_ratio < 0.4:
            confidence -= 0.1
        
        # Adjust based on engagement (comments)
        if num_comments > 20:
            confidence += 0.1
        elif num_comments > 10:
            confidence += 0.05
        
        return max(0.1, min(1.0, confidence))
    
    async def _process_signals(self, signals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process and validate collected signals"""
        processed_signals = []
        
        for signal in signals:
            # Basic validation
            if self._validate_signal(signal):
                processed_signals.append(signal)
                logger.info(f"✅ Valid signal: {signal['symbol']} {signal['signal_type']} @ {signal['entry_price']}")
            else:
                logger.debug(f"❌ Invalid signal: {signal.get('symbol', 'UNKNOWN')}")
        
        return processed_signals
    
    def _validate_signal(self, signal: Dict[str, Any]) -> bool:
        """Validate signal data"""
        required_fields = ['symbol', 'signal_type', 'entry_price', 'target_price', 'stop_loss']
        
        # Check required fields
        for field in required_fields:
            if field not in signal:
                return False
        
        # Check symbol support
        if signal['symbol'] not in self.supported_pairs:
            return False
        
        # Check price validity
        if (signal['entry_price'] <= 0 or 
            signal['target_price'] <= 0 or 
            signal['stop_loss'] <= 0):
            return False
        
        # Check signal type
        if signal['signal_type'] not in ['LONG', 'SHORT']:
            return False
        
        # Check price logic
        if signal['signal_type'] == 'LONG':
            if signal['target_price'] <= signal['entry_price'] or signal['stop_loss'] >= signal['entry_price']:
                return False
        else:  # SHORT
            if signal['target_price'] >= signal['entry_price'] or signal['stop_loss'] <= signal['entry_price']:
                return False
        
        return True
    
    def get_stats(self) -> Dict[str, Any]:
        """Get collection statistics"""
        return self.stats.copy()

# Main execution for testing
async def main():
    """Test Reddit collector"""
    collector = RedditSignalCollector()
    
    print("🚀 Testing Reddit Signal Collector")
    print("=" * 50)
    
    # Test single collection
    result = await collector.collect_signals_from_all_subreddits()
    
    print(f"📊 Collection Result:")
    print(f"Status: {result['status']}")
    print(f"Total signals: {result['total_signals']}")
    print(f"Processed signals: {result['processed_signals']}")
    print(f"Timestamp: {result['timestamp']}")
    
    print(f"\n📈 Subreddit Statistics:")
    for subreddit, count in result['subreddit_stats'].items():
        print(f"  r/{subreddit}: {count} signals")
    
    print(f"\n📊 Overall Stats:")
    stats = collector.get_stats()
    print(f"Total signals collected: {stats['total_signals_collected']}")
    print(f"Last collection: {stats['last_collection_time']}")

if __name__ == "__main__":
    asyncio.run(main())
