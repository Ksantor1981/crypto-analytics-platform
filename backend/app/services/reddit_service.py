"""
Reddit Service for collecting crypto signals from subreddits
"""
import asyncio
import aiohttp
import logging
import re
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from ..models.channel import Channel
from ..models.signal import Signal, SignalDirection
from ..schemas.reddit import RedditChannelCreate, RedditSignalCreate
from ..core.config import get_settings

logger = logging.getLogger(__name__)

class RedditService:
    """
    Service for collecting and processing Reddit crypto signals
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.settings = get_settings()
        
        # Reddit API configuration
        self.client_id = self.settings.REDDIT_CLIENT_ID
        self.client_secret = self.settings.REDDIT_CLIENT_SECRET
        self.user_agent = self.settings.REDDIT_USER_AGENT
        
        # Reddit API endpoints
        self.base_url = "https://www.reddit.com"
        self.oauth_url = "https://oauth.reddit.com"
        
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
            r'📉.*?(\w+usdt).*?(\d+\.?\d*).*?(\d+\.?\d*).*?(\d+\.?\d*)'
        ]
        
        # Supported crypto pairs
        self.supported_pairs = [
            'BTCUSDT', 'ETHUSDT', 'ADAUSDT', 'SOLUSDT', 'DOGEUSDT',
            'BNBUSDT', 'XRPUSDT', 'DOTUSDT', 'LINKUSDT', 'MATICUSDT',
            'AVAXUSDT', 'UNIUSDT', 'ATOMUSDT', 'LTCUSDT', 'BCHUSDT'
        ]
        
        # Popular crypto subreddits
        self.default_subreddits = [
            'cryptocurrency', 'cryptomarkets', 'bitcoin', 'ethereum',
            'altcoin', 'defi', 'cryptomoonshots', 'satoshistreetbets',
            'cryptosignals', 'cryptotrading', 'binance', 'coinbase'
        ]
    
    async def collect_signals_from_subreddits(
        self, 
        subreddits: List[str], 
        limit_per_subreddit: int = 25,
        time_filter: str = "day"
    ) -> Dict[str, Any]:
        """
        Collect signals from multiple Reddit subreddits
        """
        logger.info(f"Starting Reddit signal collection from {len(subreddits)} subreddits")
        
        all_signals = []
        subreddit_stats = {}
        
        try:
            async with aiohttp.ClientSession() as session:
                for subreddit in subreddits:
                    try:
                        signals = await self._collect_from_subreddit(
                            session, subreddit, limit_per_subreddit, time_filter
                        )
                        all_signals.extend(signals)
                        subreddit_stats[subreddit] = len(signals)
                        
                        logger.info(f"Collected {len(signals)} signals from r/{subreddit}")
                        
                        # Small delay to respect rate limits
                        await asyncio.sleep(1)
                        
                    except Exception as e:
                        logger.error(f"Error collecting from r/{subreddit}: {e}")
                        subreddit_stats[subreddit] = 0
                
                # Process and save signals
                processed_signals = await self._process_signals(all_signals)
                
                return {
                    "status": "success",
                    "total_signals": len(all_signals),
                    "processed_signals": len(processed_signals),
                    "subreddit_stats": subreddit_stats,
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error in Reddit collection: {e}")
            return {
                "status": "error",
                "error": str(e),
                "total_signals": 0,
                "processed_signals": 0,
                "subreddit_stats": subreddit_stats
            }
    
    async def _collect_from_subreddit(
        self, 
        session: aiohttp.ClientSession,
        subreddit: str, 
        limit: int,
        time_filter: str
    ) -> List[Dict[str, Any]]:
        """
        Collect posts from a specific subreddit
        """
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
                            post = post_data.get('data', {})
                            signal = self._extract_signal_from_post(post, subreddit)
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
    
    def _extract_signal_from_post(self, post: Dict[str, Any], subreddit: str) -> Optional[Dict[str, Any]]:
        """
        Extract trading signal from Reddit post
        """
        title = post.get('title', '')
        selftext = post.get('selftext', '')
        content = f"{title} {selftext}".lower()
        
        # Skip non-signal posts
        skip_keywords = ['news', 'update', 'announcement', 'reminder', 'analysis only', 'discussion']
        if any(keyword in content for keyword in skip_keywords):
            return None
        
        # Look for signal patterns
        for pattern in self.signal_patterns:
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
        """
        Parse signal from regex match
        """
        try:
            # Extract components based on pattern
            if len(match) == 5:
                direction_text, asset, entry_price, target_price, stop_loss = match
            elif len(match) == 4:
                asset, direction_text, entry_price, target_price = match
                stop_loss = None
            else:
                return None
            
            # Normalize asset
            asset = asset.upper()
            if not asset.endswith('USDT'):
                asset = f"{asset}USDT"
            
            # Check if asset is supported
            if asset not in self.supported_pairs:
                return None
            
            # Determine direction
            direction = SignalDirection.LONG
            if any(word in direction_text.lower() for word in ['short', 'sell', 'bearish', 'dump', 'crash']):
                direction = SignalDirection.SHORT
            
            # Parse prices
            try:
                entry_price = float(entry_price)
                target_price = float(target_price) if target_price else None
                stop_loss = float(stop_loss) if stop_loss else None
            except ValueError:
                return None
            
            # Validate prices
            if entry_price <= 0 or (target_price and target_price <= 0) or (stop_loss and stop_loss <= 0):
                return None
            
            return {
                'asset': asset,
                'direction': direction,
                'entry_price': entry_price,
                'target_price': target_price,
                'stop_loss': stop_loss,
                'subreddit': subreddit,
                'post_id': post.get('id'),
                'post_title': post.get('title', ''),
                'post_url': f"https://reddit.com{post.get('permalink', '')}",
                'created_utc': post.get('created_utc'),
                'score': post.get('score', 0),
                'num_comments': post.get('num_comments', 0),
                'confidence': self._calculate_confidence(post)
            }
            
        except Exception as e:
            logger.error(f"Error parsing signal match: {e}")
            return None
    
    def _calculate_confidence(self, post: Dict[str, Any]) -> float:
        """
        Calculate confidence score for Reddit signal
        """
        confidence = 0.5  # Base confidence
        
        # Boost based on post score
        score = post.get('score', 0)
        if score > 100:
            confidence += 0.2
        elif score > 50:
            confidence += 0.1
        elif score < 0:
            confidence -= 0.1
        
        # Boost based on comments
        comments = post.get('num_comments', 0)
        if comments > 50:
            confidence += 0.1
        elif comments > 20:
            confidence += 0.05
        
        # Boost based on account age (if available)
        created_utc = post.get('created_utc')
        if created_utc:
            post_age = datetime.now().timestamp() - created_utc
            if post_age < 3600:  # Less than 1 hour
                confidence += 0.1
        
        return min(max(confidence, 0.1), 1.0)
    
    async def _process_signals(self, signals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process and save signals to database
        """
        processed = []
        
        for signal_data in signals:
            try:
                # Get or create channel
                channel = self._get_or_create_reddit_channel(signal_data['subreddit'])
                
                # Create signal
                signal = self._create_signal_from_reddit_data(signal_data, channel.id)
                
                if signal:
                    processed.append(signal)
                    
            except Exception as e:
                logger.error(f"Error processing Reddit signal: {e}")
        
        return processed
    
    def _get_or_create_reddit_channel(self, subreddit: str) -> Channel:
        """
        Get or create Reddit channel in database
        """
        # Check if channel exists
        channel = self.db.query(Channel).filter(
            and_(
                Channel.url.like(f"%reddit.com/r/{subreddit}%"),
                Channel.type == "reddit"
            )
        ).first()
        
        if channel:
            return channel
        
        # Create new channel
        channel = Channel(
            name=f"r/{subreddit}",
            url=f"https://reddit.com/r/{subreddit}",
            description=f"Reddit subreddit: {subreddit}",
            type="reddit",
            is_active=True,
            source="reddit"
        )
        
        self.db.add(channel)
        self.db.commit()
        self.db.refresh(channel)
        
        return channel
    
    def _create_signal_from_reddit_data(
        self, 
        signal_data: Dict[str, Any], 
        channel_id: int
    ) -> Optional[Signal]:
        """
        Create Signal object from Reddit data
        """
        try:
            signal = Signal(
                channel_id=channel_id,
                asset=signal_data['asset'],
                symbol=signal_data['asset'],
                direction=signal_data['direction'],
                entry_price=signal_data['entry_price'],
                tp1_price=signal_data.get('target_price'),
                stop_loss=signal_data.get('stop_loss'),
                original_text=signal_data.get('post_title', ''),
                message_timestamp=datetime.fromtimestamp(signal_data.get('created_utc', 0)),
                telegram_message_id=signal_data.get('post_id'),
                confidence_score=signal_data.get('confidence', 0.5) * 100,
                source="reddit"
            )
            
            self.db.add(signal)
            self.db.commit()
            self.db.refresh(signal)
            
            return signal
            
        except Exception as e:
            logger.error(f"Error creating signal from Reddit data: {e}")
            self.db.rollback()
            return None
    
    def get_monitored_subreddits(self) -> List[Dict[str, Any]]:
        """
        Get list of monitored Reddit subreddits
        """
        channels = self.db.query(Channel).filter(
            and_(
                Channel.type == "reddit",
                Channel.is_active == True
            )
        ).all()
        
        return [
            {
                "name": channel.name,
                "url": channel.url,
                "description": channel.description,
                "is_active": channel.is_active
            }
            for channel in channels
        ]
    
    def add_subreddit(self, subreddit_data: RedditChannelCreate) -> Dict[str, Any]:
        """
        Add new Reddit subreddit for monitoring
        """
        # Check if already exists
        existing = self.db.query(Channel).filter(
            and_(
                Channel.url.like(f"%reddit.com/r/{subreddit_data.name}%"),
                Channel.type == "reddit"
            )
        ).first()
        
        if existing:
            return {
                "name": existing.name,
                "url": existing.url,
                "message": "Subreddit already monitored"
            }
        
        # Create new channel
        channel = Channel(
            name=f"r/{subreddit_data.name}",
            url=f"https://reddit.com/r/{subreddit_data.name}",
            description=subreddit_data.description or f"Reddit subreddit: {subreddit_data.name}",
            type="reddit",
            is_active=True,
            source="reddit"
        )
        
        self.db.add(channel)
        self.db.commit()
        self.db.refresh(channel)
        
        return {
            "name": channel.name,
            "url": channel.url,
            "description": channel.description,
            "is_active": channel.is_active
        }
    
    def get_signals(
        self, 
        skip: int = 0, 
        limit: int = 50, 
        subreddit: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get signals collected from Reddit
        """
        query = self.db.query(Signal).join(Channel).filter(
            and_(
                Channel.type == "reddit",
                Signal.source == "reddit"
            )
        )
        
        if subreddit:
            query = query.filter(Channel.name.like(f"%{subreddit}%"))
        
        signals = query.offset(skip).limit(limit).all()
        
        return [
            {
                "id": signal.id,
                "asset": signal.asset,
                "direction": signal.direction,
                "entry_price": float(signal.entry_price),
                "target_price": float(signal.tp1_price) if signal.tp1_price else None,
                "stop_loss": float(signal.stop_loss) if signal.stop_loss else None,
                "subreddit": signal.channel.name,
                "confidence": signal.confidence_score,
                "created_at": signal.created_at.isoformat(),
                "post_url": signal.telegram_message_id
            }
            for signal in signals
        ]
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get Reddit integration statistics
        """
        # Total signals from Reddit
        total_signals = self.db.query(Signal).join(Channel).filter(
            and_(
                Channel.type == "reddit",
                Signal.source == "reddit"
            )
        ).count()
        
        # Signals by subreddit
        subreddit_stats = self.db.query(
            Channel.name,
            self.db.func.count(Signal.id).label('signal_count')
        ).join(Signal).filter(
            and_(
                Channel.type == "reddit",
                Signal.source == "reddit"
            )
        ).group_by(Channel.name).all()
        
        # Recent signals (last 24 hours)
        yesterday = datetime.now() - timedelta(days=1)
        recent_signals = self.db.query(Signal).join(Channel).filter(
            and_(
                Channel.type == "reddit",
                Signal.source == "reddit",
                Signal.created_at >= yesterday
            )
        ).count()
        
        return {
            "total_signals": total_signals,
            "recent_signals_24h": recent_signals,
            "subreddit_stats": [
                {"subreddit": name, "signals": count}
                for name, count in subreddit_stats
            ],
            "monitored_subreddits": len(self.get_monitored_subreddits())
        }
