"""
Social signals analysis and subscriber activity tracking
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass
import logging
from datetime import datetime, timedelta
import re

logger = logging.getLogger(__name__)

@dataclass
class SocialActivity:
    """Social media activity data"""
    platform: str  # "telegram", "twitter", "reddit", "rss", "tradingview"
    timestamp: datetime
    activity_type: str  # "message", "reaction", "share", "comment"
    user_id: str
    content: Optional[str] = None
    engagement_score: float = 0.0
    sentiment_score: float = 0.0

@dataclass
class SubscriberMetrics:
    """Subscriber activity and engagement metrics"""
    total_subscribers: int
    active_subscribers: int
    engagement_rate: float  # Active / Total
    avg_daily_activity: float
    peak_activity_hour: int
    activity_trend: str  # "increasing", "decreasing", "stable"
    sentiment_trend: str  # "positive", "negative", "neutral"
    viral_potential: float  # 0-1 scale
    community_health: float  # 0-1 scale

@dataclass
class SocialSignalMetrics:
    """Comprehensive social signal metrics"""
    platform: str
    message_count: int
    reaction_count: int
    share_count: int
    comment_count: int
    total_engagement: int
    engagement_rate: float
    sentiment_score: float
    trending_score: float
    reach_estimate: int
    virality_potential: float

class SocialSignalsAnalyzer:
    """Analyzer for social signals and subscriber activity"""
    
    def __init__(self):
        self.sentiment_keywords = {
            'positive': ['bull', 'moon', 'pump', 'buy', 'long', 'strong', 'breakout', 'rally', '🚀', '📈', '💎'],
            'negative': ['bear', 'dump', 'sell', 'short', 'weak', 'crash', 'correction', 'fear', '📉', '💸', '🔥'],
            'neutral': ['sideways', 'consolidation', 'range', 'stable', 'steady', 'wait', '⏳']
        }
        
        self.activity_weights = {
            'message': 1.0,
            'reaction': 0.5,
            'share': 2.0,
            'comment': 1.5,
            'mention': 1.0
        }
        
    def analyze_telegram_activity(self, messages: List[Dict[str, Any]]) -> Dict[str, float]:
        """Analyze Telegram channel activity"""
        if not messages:
            return self._get_default_social_metrics()
        
        total_messages = len(messages)
        total_reactions = sum(msg.get('reactions', 0) for msg in messages)
        total_forwards = sum(msg.get('forwards', 0) for msg in messages)
        total_views = sum(msg.get('views', 0) for msg in messages)
        
        # Calculate engagement metrics
        avg_reactions = total_reactions / total_messages if total_messages > 0 else 0
        avg_forwards = total_forwards / total_messages if total_messages > 0 else 0
        avg_views = total_views / total_messages if total_messages > 0 else 0
        
        # Engagement rate (reactions + forwards) / views
        engagement_rate = (total_reactions + total_forwards) / total_views if total_views > 0 else 0
        
        # Sentiment analysis
        sentiment_scores = []
        for msg in messages:
            text = msg.get('text', '').lower()
            sentiment = self._calculate_text_sentiment(text)
            sentiment_scores.append(sentiment)
        
        avg_sentiment = np.mean(sentiment_scores) if sentiment_scores else 0.0
        
        # Activity trend
        activity_trend = self._calculate_activity_trend(messages)
        
        return {
            'message_count': total_messages,
            'reaction_count': total_reactions,
            'forward_count': total_forwards,
            'view_count': total_views,
            'avg_reactions': float(avg_reactions),
            'avg_forwards': float(avg_forwards),
            'avg_views': float(avg_views),
            'engagement_rate': float(engagement_rate),
            'sentiment_score': float(avg_sentiment),
            'activity_trend': activity_trend,
            'viral_potential': float(min(engagement_rate * 10, 1.0))
        }
    
    def analyze_twitter_activity(self, tweets: List[Dict[str, Any]]) -> Dict[str, float]:
        """Analyze Twitter activity"""
        if not tweets:
            return self._get_default_social_metrics()
        
        total_tweets = len(tweets)
        total_likes = sum(tweet.get('likes', 0) for tweet in tweets)
        total_retweets = sum(tweet.get('retweets', 0) for tweet in tweets)
        total_replies = sum(tweet.get('replies', 0) for tweet in tweets)
        total_impressions = sum(tweet.get('impressions', 0) for tweet in tweets)
        
        # Calculate engagement metrics
        avg_likes = total_likes / total_tweets if total_tweets > 0 else 0
        avg_retweets = total_retweets / total_tweets if total_tweets > 0 else 0
        avg_replies = total_replies / total_tweets if total_tweets > 0 else 0
        
        # Engagement rate
        engagement_rate = (total_likes + total_retweets + total_replies) / total_impressions if total_impressions > 0 else 0
        
        # Sentiment analysis
        sentiment_scores = []
        for tweet in tweets:
            text = tweet.get('text', '').lower()
            sentiment = self._calculate_text_sentiment(text)
            sentiment_scores.append(sentiment)
        
        avg_sentiment = np.mean(sentiment_scores) if sentiment_scores else 0.0
        
        # Trending analysis
        trending_score = self._calculate_trending_score(tweets)
        
        return {
            'tweet_count': total_tweets,
            'like_count': total_likes,
            'retweet_count': total_retweets,
            'reply_count': total_replies,
            'impression_count': total_impressions,
            'avg_likes': float(avg_likes),
            'avg_retweets': float(avg_retweets),
            'avg_replies': float(avg_replies),
            'engagement_rate': float(engagement_rate),
            'sentiment_score': float(avg_sentiment),
            'trending_score': float(trending_score),
            'viral_potential': float(min(engagement_rate * 15, 1.0))
        }
    
    def analyze_reddit_activity(self, posts: List[Dict[str, Any]]) -> Dict[str, float]:
        """Analyze Reddit activity"""
        if not posts:
            return self._get_default_social_metrics()
        
        total_posts = len(posts)
        total_upvotes = sum(post.get('upvotes', 0) for post in posts)
        total_downvotes = sum(post.get('downvotes', 0) for post in posts)
        total_comments = sum(post.get('comments', 0) for post in posts)
        total_score = total_upvotes - total_downvotes
        
        # Calculate engagement metrics
        avg_upvotes = total_upvotes / total_posts if total_posts > 0 else 0
        avg_comments = total_comments / total_posts if total_posts > 0 else 0
        avg_score = total_score / total_posts if total_posts > 0 else 0
        
        # Engagement rate
        total_votes = total_upvotes + total_downvotes
        engagement_rate = total_comments / total_posts if total_posts > 0 else 0
        
        # Sentiment analysis
        sentiment_scores = []
        for post in posts:
            title = post.get('title', '').lower()
            content = post.get('content', '').lower()
            text = f"{title} {content}"
            sentiment = self._calculate_text_sentiment(text)
            sentiment_scores.append(sentiment)
        
        avg_sentiment = np.mean(sentiment_scores) if sentiment_scores else 0.0
        
        # Community health score
        community_health = self._calculate_community_health(posts)
        
        return {
            'post_count': total_posts,
            'upvote_count': total_upvotes,
            'downvote_count': total_downvotes,
            'comment_count': total_comments,
            'total_score': total_score,
            'avg_upvotes': float(avg_upvotes),
            'avg_comments': float(avg_comments),
            'avg_score': float(avg_score),
            'engagement_rate': float(engagement_rate),
            'sentiment_score': float(avg_sentiment),
            'community_health': float(community_health),
            'viral_potential': float(min(engagement_rate * 8, 1.0))
        }
    
    def calculate_subscriber_metrics(self, activities: List[SocialActivity], 
                                   total_subscribers: int) -> SubscriberMetrics:
        """Calculate comprehensive subscriber metrics"""
        if not activities:
            return self._get_default_subscriber_metrics(total_subscribers)
        
        # Active subscribers (unique users with activity)
        unique_users = set(activity.user_id for activity in activities)
        active_subscribers = len(unique_users)
        
        # Engagement rate
        engagement_rate = active_subscribers / total_subscribers if total_subscribers > 0 else 0.0
        
        # Daily activity analysis
        daily_activities = {}
        for activity in activities:
            date = activity.timestamp.date()
            if date not in daily_activities:
                daily_activities[date] = 0
            daily_activities[date] += 1
        
        avg_daily_activity = np.mean(list(daily_activities.values())) if daily_activities else 0.0
        
        # Peak activity hour
        hourly_activities = {}
        for activity in activities:
            hour = activity.timestamp.hour
            if hour not in hourly_activities:
                hourly_activities[hour] = 0
            hourly_activities[hour] += 1
        
        peak_activity_hour = max(hourly_activities.items(), key=lambda x: x[1])[0] if hourly_activities else 12
        
        # Activity trend
        activity_trend = self._calculate_activity_trend_from_data(activities)
        
        # Sentiment trend
        sentiment_trend = self._calculate_sentiment_trend(activities)
        
        # Viral potential
        viral_potential = self._calculate_viral_potential(activities, engagement_rate)
        
        # Community health
        community_health = self._calculate_community_health_score(activities, engagement_rate)
        
        return SubscriberMetrics(
            total_subscribers=total_subscribers,
            active_subscribers=active_subscribers,
            engagement_rate=float(engagement_rate),
            avg_daily_activity=float(avg_daily_activity),
            peak_activity_hour=peak_activity_hour,
            activity_trend=activity_trend,
            sentiment_trend=sentiment_trend,
            viral_potential=float(viral_potential),
            community_health=float(community_health)
        )
    
    def _calculate_text_sentiment(self, text: str) -> float:
        """Calculate sentiment score for text"""
        if not text:
            return 0.0
        
        text = text.lower()
        
        # Count positive and negative keywords
        positive_count = sum(1 for word in self.sentiment_keywords['positive'] if word in text)
        negative_count = sum(1 for word in self.sentiment_keywords['negative'] if word in text)
        
        # Calculate sentiment score
        if positive_count + negative_count > 0:
            sentiment = (positive_count - negative_count) / (positive_count + negative_count)
        else:
            sentiment = 0.0
        
        return float(np.clip(sentiment, -1.0, 1.0))
    
    def _calculate_activity_trend(self, messages: List[Dict[str, Any]]) -> str:
        """Calculate activity trend from messages"""
        if len(messages) < 2:
            return "stable"
        
        # Sort by timestamp
        sorted_messages = sorted(messages, key=lambda x: x.get('timestamp', datetime.now()))
        
        # Calculate activity in first and second half
        mid_point = len(sorted_messages) // 2
        first_half = len(sorted_messages[:mid_point])
        second_half = len(sorted_messages[mid_point:])
        
        if second_half > first_half * 1.2:
            return "increasing"
        elif first_half > second_half * 1.2:
            return "decreasing"
        else:
            return "stable"
    
    def _calculate_activity_trend_from_data(self, activities: List[SocialActivity]) -> str:
        """Calculate activity trend from social activities"""
        if len(activities) < 2:
            return "stable"
        
        # Sort by timestamp
        sorted_activities = sorted(activities, key=lambda x: x.timestamp)
        
        # Calculate activity in first and second half
        mid_point = len(sorted_activities) // 2
        first_half = len(sorted_activities[:mid_point])
        second_half = len(sorted_activities[mid_point:])
        
        if second_half > first_half * 1.2:
            return "increasing"
        elif first_half > second_half * 1.2:
            return "decreasing"
        else:
            return "stable"
    
    def _calculate_sentiment_trend(self, activities: List[SocialActivity]) -> str:
        """Calculate sentiment trend from activities"""
        if len(activities) < 5:
            return "neutral"
        
        # Sort by timestamp
        sorted_activities = sorted(activities, key=lambda x: x.timestamp)
        
        # Calculate sentiment in first and second half
        mid_point = len(sorted_activities) // 2
        first_half_sentiment = np.mean([a.sentiment_score for a in sorted_activities[:mid_point]])
        second_half_sentiment = np.mean([a.sentiment_score for a in sorted_activities[mid_point:]])
        
        if second_half_sentiment > first_half_sentiment + 0.1:
            return "positive"
        elif first_half_sentiment > second_half_sentiment + 0.1:
            return "negative"
        else:
            return "neutral"
    
    def _calculate_trending_score(self, tweets: List[Dict[str, Any]]) -> float:
        """Calculate trending score for tweets"""
        if not tweets:
            return 0.0
        
        # Factors for trending: engagement rate, retweet velocity, hashtag usage
        total_engagement = sum(tweet.get('likes', 0) + tweet.get('retweets', 0) for tweet in tweets)
        total_impressions = sum(tweet.get('impressions', 0) for tweet in tweets)
        
        engagement_rate = total_engagement / total_impressions if total_impressions > 0 else 0
        
        # Hashtag usage
        hashtag_count = sum(1 for tweet in tweets if '#' in tweet.get('text', ''))
        hashtag_ratio = hashtag_count / len(tweets) if tweets else 0
        
        # Trending score
        trending_score = engagement_rate * 0.6 + hashtag_ratio * 0.4
        
        return float(np.clip(trending_score, 0.0, 1.0))
    
    def _calculate_community_health(self, posts: List[Dict[str, Any]]) -> float:
        """Calculate community health score for Reddit"""
        if not posts:
            return 0.5
        
        # Factors: upvote ratio, comment quality, user diversity
        total_upvotes = sum(post.get('upvotes', 0) for post in posts)
        total_downvotes = sum(post.get('downvotes', 0) for post in posts)
        total_votes = total_upvotes + total_downvotes
        
        upvote_ratio = total_upvotes / total_votes if total_votes > 0 else 0.5
        
        # Comment quality (more comments = better engagement)
        avg_comments = np.mean([post.get('comments', 0) for post in posts])
        comment_score = min(avg_comments / 10, 1.0)  # Normalize
        
        # User diversity (unique users)
        unique_users = set(post.get('author', '') for post in posts)
        diversity_score = len(unique_users) / len(posts) if posts else 0.5
        
        # Community health score
        health_score = upvote_ratio * 0.4 + comment_score * 0.3 + diversity_score * 0.3
        
        return float(np.clip(health_score, 0.0, 1.0))
    
    def _calculate_viral_potential(self, activities: List[SocialActivity], 
                                 engagement_rate: float) -> float:
        """Calculate viral potential score"""
        if not activities:
            return 0.0
        
        # Factors: engagement rate, activity volume, sentiment
        activity_volume = len(activities)
        volume_score = min(activity_volume / 100, 1.0)  # Normalize
        
        avg_sentiment = np.mean([abs(a.sentiment_score) for a in activities])
        sentiment_score = avg_sentiment
        
        # Viral potential formula
        viral_potential = engagement_rate * 0.4 + volume_score * 0.3 + sentiment_score * 0.3
        
        return float(np.clip(viral_potential, 0.0, 1.0))
    
    def _calculate_community_health_score(self, activities: List[SocialActivity], 
                                        engagement_rate: float) -> float:
        """Calculate overall community health score"""
        if not activities:
            return 0.5
        
        # Factors: engagement rate, activity consistency, user diversity
        unique_users = set(a.user_id for a in activities)
        diversity_score = len(unique_users) / len(activities) if activities else 0.5
        
        # Activity consistency (spread over time)
        timestamps = [a.timestamp for a in activities]
        time_span = max(timestamps) - min(timestamps)
        consistency_score = min(len(activities) / max(time_span.total_seconds() / 3600, 1), 1.0)
        
        # Community health formula
        health_score = engagement_rate * 0.4 + diversity_score * 0.3 + consistency_score * 0.3
        
        return float(np.clip(health_score, 0.0, 1.0))
    
    def _get_default_social_metrics(self) -> Dict[str, float]:
        """Get default social metrics"""
        return {
            'message_count': 0,
            'reaction_count': 0,
            'engagement_rate': 0.0,
            'sentiment_score': 0.0,
            'activity_trend': 'stable',
            'viral_potential': 0.0
        }
    
    def _get_default_subscriber_metrics(self, total_subscribers: int) -> SubscriberMetrics:
        """Get default subscriber metrics"""
        return SubscriberMetrics(
            total_subscribers=total_subscribers,
            active_subscribers=0,
            engagement_rate=0.0,
            avg_daily_activity=0.0,
            peak_activity_hour=12,
            activity_trend='stable',
            sentiment_trend='neutral',
            viral_potential=0.0,
            community_health=0.5
        )


def main():
    """Test social signals analysis"""
    analyzer = SocialSignalsAnalyzer()
    
    # Mock Telegram messages
    telegram_messages = [
        {
            'text': 'Bitcoin is going to the moon! 🚀 Buy now!',
            'reactions': 150,
            'forwards': 25,
            'views': 1000,
            'timestamp': datetime.now() - timedelta(hours=1)
        },
        {
            'text': 'Market looks bearish, be careful 📉',
            'reactions': 80,
            'forwards': 10,
            'views': 800,
            'timestamp': datetime.now() - timedelta(hours=2)
        }
    ]
    
    # Analyze Telegram activity
    telegram_metrics = analyzer.analyze_telegram_activity(telegram_messages)
    print(f"Telegram Metrics: {telegram_metrics}")
    
    # Mock social activities
    activities = [
        SocialActivity('telegram', datetime.now(), 'message', 'user1', 'Great signal!', 0.8, 0.7),
        SocialActivity('telegram', datetime.now(), 'reaction', 'user2', None, 0.5, 0.0),
        SocialActivity('twitter', datetime.now(), 'share', 'user3', 'Amazing analysis', 1.0, 0.9)
    ]
    
    # Calculate subscriber metrics
    subscriber_metrics = analyzer.calculate_subscriber_metrics(activities, 1000)
    print(f"Subscriber Metrics: {subscriber_metrics}")


if __name__ == "__main__":
    main() 