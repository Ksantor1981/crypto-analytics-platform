"""
Market sentiment analysis module
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
class SentimentMetrics:
    """Market sentiment metrics"""
    overall_sentiment: float  # -1 to 1 (negative to positive)
    confidence: float  # 0 to 1
    volume_score: float  # 0 to 1
    social_score: float  # 0 to 1
    news_score: float  # 0 to 1
    technical_score: float  # 0 to 1
    sentiment_trend: str  # "bullish", "bearish", "neutral"
    key_indicators: Dict[str, float]

class MarketSentimentAnalyzer:
    """Analyzer for market sentiment and social signals"""
    
    def __init__(self):
        self.sentiment_keywords = {
            'positive': ['bull', 'moon', 'pump', 'buy', 'long', 'strong', 'breakout', 'rally'],
            'negative': ['bear', 'dump', 'sell', 'short', 'weak', 'crash', 'correction', 'fear'],
            'neutral': ['sideways', 'consolidation', 'range', 'stable', 'steady']
        }
        
        self.volume_thresholds = {
            'low': 0.3,
            'medium': 0.7,
            'high': 1.0
        }
    
    def analyze_social_sentiment(self, social_data: Dict[str, Any]) -> Dict[str, float]:
        """Analyze sentiment from social media data"""
        sentiment_scores = {
            'telegram': 0.0,
            'twitter': 0.0,
            'reddit': 0.0,
            'overall': 0.0
        }
        
        # Analyze Telegram signals
        if 'telegram_signals' in social_data:
            telegram_sentiment = self._analyze_telegram_signals(
                social_data['telegram_signals']
            )
            sentiment_scores['telegram'] = telegram_sentiment
        
        # Analyze Twitter mentions
        if 'twitter_mentions' in social_data:
            twitter_sentiment = self._analyze_twitter_mentions(
                social_data['twitter_mentions']
            )
            sentiment_scores['twitter'] = twitter_sentiment
        
        # Analyze Reddit discussions
        if 'reddit_posts' in social_data:
            reddit_sentiment = self._analyze_reddit_posts(
                social_data['reddit_posts']
            )
            sentiment_scores['reddit'] = reddit_sentiment
        
        # Calculate overall social sentiment
        platforms = [s for s in ['telegram', 'twitter', 'reddit'] if sentiment_scores[s] != 0.0]
        if platforms:
            sentiment_scores['overall'] = sum(sentiment_scores[p] for p in platforms) / len(platforms)
        
        return sentiment_scores
    
    def _analyze_telegram_signals(self, signals: List[Dict[str, Any]]) -> float:
        """Analyze sentiment from Telegram signals"""
        if not signals:
            return 0.0
        
        total_sentiment = 0.0
        total_weight = 0.0
        
        for signal in signals:
            # Extract signal strength and direction
            signal_strength = signal.get('strength', 0.5)
            signal_direction = signal.get('direction', 'neutral')
            
            # Convert direction to sentiment score
            if signal_direction == 'buy':
                sentiment = signal_strength
            elif signal_direction == 'sell':
                sentiment = -signal_strength
            else:
                sentiment = 0.0
            
            # Weight by channel rating and subscriber count
            channel_rating = signal.get('channel_rating', 3.0) / 5.0
            subscriber_weight = min(signal.get('subscriber_count', 1000) / 10000, 1.0)
            
            weight = channel_rating * subscriber_weight
            total_sentiment += sentiment * weight
            total_weight += weight
        
        return total_sentiment / total_weight if total_weight > 0 else 0.0
    
    def _analyze_twitter_mentions(self, mentions: List[Dict[str, Any]]) -> float:
        """Analyze sentiment from Twitter mentions"""
        if not mentions:
            return 0.0
        
        total_sentiment = 0.0
        total_weight = 0.0
        
        for mention in mentions:
            text = mention.get('text', '').lower()
            
            # Count positive and negative keywords
            positive_count = sum(1 for word in self.sentiment_keywords['positive'] if word in text)
            negative_count = sum(1 for word in self.sentiment_keywords['negative'] if word in text)
            
            # Calculate sentiment score
            if positive_count + negative_count > 0:
                sentiment = (positive_count - negative_count) / (positive_count + negative_count)
            else:
                sentiment = 0.0
            
            # Weight by engagement
            engagement = mention.get('engagement', 0)
            weight = min(engagement / 1000, 1.0)  # Normalize engagement
            
            total_sentiment += sentiment * weight
            total_weight += weight
        
        return total_sentiment / total_weight if total_weight > 0 else 0.0
    
    def _analyze_reddit_posts(self, posts: List[Dict[str, Any]]) -> float:
        """Analyze sentiment from Reddit posts"""
        if not posts:
            return 0.0
        
        total_sentiment = 0.0
        total_weight = 0.0
        
        for post in posts:
            title = post.get('title', '').lower()
            content = post.get('content', '').lower()
            text = f"{title} {content}"
            
            # Count positive and negative keywords
            positive_count = sum(1 for word in self.sentiment_keywords['positive'] if word in text)
            negative_count = sum(1 for word in self.sentiment_keywords['negative'] if word in text)
            
            # Calculate sentiment score
            if positive_count + negative_count > 0:
                sentiment = (positive_count - negative_count) / (positive_count + negative_count)
            else:
                sentiment = 0.0
            
            # Weight by upvotes and comments
            upvotes = post.get('upvotes', 0)
            comments = post.get('comments', 0)
            weight = min((upvotes + comments * 2) / 1000, 1.0)  # Weight comments more than upvotes
            
            total_sentiment += sentiment * weight
            total_weight += weight
        
        return total_sentiment / total_weight if total_weight > 0 else 0.0
    
    def analyze_volume_patterns(self, volume_data: Dict[str, Any]) -> Dict[str, float]:
        """Analyze trading volume patterns"""
        volumes = volume_data.get('volume_history', [])
        if not volumes:
            return {'volume_score': 0.0, 'volume_trend': 'stable'}
        
        volumes = np.array(volumes)
        
        # Calculate volume metrics
        avg_volume = np.mean(volumes)
        current_volume = volumes[-1] if len(volumes) > 0 else avg_volume
        
        # Volume score based on current vs average
        volume_score = min(current_volume / avg_volume, 2.0) if avg_volume > 0 else 1.0
        
        # Volume trend
        if len(volumes) >= 5:
            recent_avg = np.mean(volumes[-5:])
            if current_volume > recent_avg * 1.2:
                volume_trend = 'increasing'
            elif current_volume < recent_avg * 0.8:
                volume_trend = 'decreasing'
            else:
                volume_trend = 'stable'
        else:
            volume_trend = 'stable'
        
        return {
            'volume_score': float(volume_score),
            'volume_trend': volume_trend,
            'current_volume': float(current_volume),
            'avg_volume': float(avg_volume)
        }
    
    def analyze_news_sentiment(self, news_data: List[Dict[str, Any]]) -> Dict[str, float]:
        """Analyze sentiment from news articles"""
        if not news_data:
            return {'news_score': 0.0, 'news_sentiment': 'neutral'}
        
        total_sentiment = 0.0
        total_weight = 0.0
        
        for news in news_data:
            title = news.get('title', '').lower()
            content = news.get('content', '').lower()
            text = f"{title} {content}"
            
            # Count sentiment keywords
            positive_count = sum(1 for word in self.sentiment_keywords['positive'] if word in text)
            negative_count = sum(1 for word in self.sentiment_keywords['negative'] if word in text)
            
            # Calculate sentiment
            if positive_count + negative_count > 0:
                sentiment = (positive_count - negative_count) / (positive_count + negative_count)
            else:
                sentiment = 0.0
            
            # Weight by source credibility and recency
            source_credibility = news.get('source_credibility', 0.5)
            hours_old = news.get('hours_old', 24)
            recency_weight = max(0.1, 1.0 - hours_old / 48)  # Decay over 48 hours
            
            weight = source_credibility * recency_weight
            total_sentiment += sentiment * weight
            total_weight += weight
        
        news_score = total_sentiment / total_weight if total_weight > 0 else 0.0
        
        return {
            'news_score': float(news_score),
            'news_sentiment': 'positive' if news_score > 0.1 else 'negative' if news_score < -0.1 else 'neutral'
        }
    
    def analyze_technical_sentiment(self, technical_data: Dict[str, Any]) -> Dict[str, float]:
        """Analyze sentiment from technical indicators"""
        sentiment_score = 0.0
        indicators = {}
        
        # RSI sentiment
        rsi = technical_data.get('rsi', 50)
        if rsi > 70:
            rsi_sentiment = -0.5  # Overbought
        elif rsi < 30:
            rsi_sentiment = 0.5   # Oversold
        else:
            rsi_sentiment = 0.0
        indicators['rsi_sentiment'] = rsi_sentiment
        sentiment_score += rsi_sentiment * 0.2
        
        # MACD sentiment
        macd = technical_data.get('macd', 0)
        macd_signal = technical_data.get('macd_signal', 0)
        if macd > macd_signal:
            macd_sentiment = 0.3  # Bullish crossover
        elif macd < macd_signal:
            macd_sentiment = -0.3  # Bearish crossover
        else:
            macd_sentiment = 0.0
        indicators['macd_sentiment'] = macd_sentiment
        sentiment_score += macd_sentiment * 0.2
        
        # Bollinger Bands sentiment
        bb_position = technical_data.get('bb_position', 0)
        if bb_position > 0.8:
            bb_sentiment = -0.3  # Near upper band
        elif bb_position < 0.2:
            bb_sentiment = 0.3   # Near lower band
        else:
            bb_sentiment = 0.0
        indicators['bb_sentiment'] = bb_sentiment
        sentiment_score += bb_sentiment * 0.15
        
        # Price momentum
        price_change = technical_data.get('price_change_24h', 0)
        momentum_sentiment = np.clip(price_change * 10, -0.5, 0.5)  # Scale and clip
        indicators['momentum_sentiment'] = momentum_sentiment
        sentiment_score += momentum_sentiment * 0.25
        
        # Volume sentiment
        volume_change = technical_data.get('volume_change_24h', 0)
        volume_sentiment = np.clip(volume_change * 5, -0.3, 0.3)
        indicators['volume_sentiment'] = volume_sentiment
        sentiment_score += volume_sentiment * 0.2
        
        return {
            'technical_score': float(sentiment_score),
            'technical_indicators': indicators
        }
    
    def calculate_overall_sentiment(self, 
                                  social_scores: Dict[str, float],
                                  volume_analysis: Dict[str, float],
                                  news_analysis: Dict[str, float],
                                  technical_analysis: Dict[str, float]) -> SentimentMetrics:
        """Calculate overall market sentiment"""
        
        # Weighted combination of all sentiment sources
        social_weight = 0.3
        volume_weight = 0.2
        news_weight = 0.2
        technical_weight = 0.3
        
        overall_sentiment = (
            social_scores['overall'] * social_weight +
            volume_analysis['volume_score'] * volume_weight +
            news_analysis['news_score'] * news_weight +
            technical_analysis['technical_score'] * technical_weight
        )
        
        # Calculate confidence based on data availability
        confidence_factors = []
        if social_scores['overall'] != 0:
            confidence_factors.append(0.8)
        if volume_analysis['volume_score'] != 0:
            confidence_factors.append(0.9)
        if news_analysis['news_score'] != 0:
            confidence_factors.append(0.7)
        if technical_analysis['technical_score'] != 0:
            confidence_factors.append(0.9)
        
        confidence = np.mean(confidence_factors) if confidence_factors else 0.5
        
        # Determine sentiment trend
        if overall_sentiment > 0.2:
            sentiment_trend = "bullish"
        elif overall_sentiment < -0.2:
            sentiment_trend = "bearish"
        else:
            sentiment_trend = "neutral"
        
        # Combine key indicators
        key_indicators = {
            'social_sentiment': social_scores['overall'],
            'volume_score': volume_analysis['volume_score'],
            'news_sentiment': news_analysis['news_score'],
            'technical_sentiment': technical_analysis['technical_score']
        }
        key_indicators.update(technical_analysis.get('technical_indicators', {}))
        
        return SentimentMetrics(
            overall_sentiment=float(overall_sentiment),
            confidence=float(confidence),
            volume_score=float(volume_analysis['volume_score']),
            social_score=float(social_scores['overall']),
            news_score=float(news_analysis['news_score']),
            technical_score=float(technical_analysis['technical_score']),
            sentiment_trend=sentiment_trend,
            key_indicators=key_indicators
        )
    
    def generate_sentiment_report(self, asset: str, sentiment_metrics: SentimentMetrics) -> str:
        """Generate comprehensive sentiment report"""
        report = f"""
# Market Sentiment Report for {asset}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Overall Sentiment
- **Sentiment Score**: {sentiment_metrics.overall_sentiment:.3f} (-1 to 1)
- **Trend**: {sentiment_metrics.sentiment_trend.upper()}
- **Confidence**: {sentiment_metrics.confidence:.1%}

## Component Scores
- **Social Sentiment**: {sentiment_metrics.social_score:.3f}
- **Volume Score**: {sentiment_metrics.volume_score:.3f}
- **News Sentiment**: {sentiment_metrics.news_score:.3f}
- **Technical Sentiment**: {sentiment_metrics.technical_score:.3f}

## Key Indicators
"""
        
        for indicator, value in sentiment_metrics.key_indicators.items():
            report += f"- **{indicator.replace('_', ' ').title()}**: {value:.3f}\n"
        
        report += f"""
## Recommendations
- {'🟢 Strong bullish sentiment detected' if sentiment_metrics.overall_sentiment > 0.3 else 
    '🔴 Strong bearish sentiment detected' if sentiment_metrics.overall_sentiment < -0.3 else 
    '🟡 Neutral sentiment - monitor for changes'}
- Confidence level: {'High' if sentiment_metrics.confidence > 0.8 else 'Medium' if sentiment_metrics.confidence > 0.6 else 'Low'}
"""
        
        return report


def main():
    """Test sentiment analysis functionality"""
    analyzer = MarketSentimentAnalyzer()
    
    # Mock data
    mock_social_data = {
        'telegram_signals': [
            {'strength': 0.8, 'direction': 'buy', 'channel_rating': 4.5, 'subscriber_count': 5000},
            {'strength': 0.6, 'direction': 'buy', 'channel_rating': 3.8, 'subscriber_count': 3000}
        ],
        'twitter_mentions': [
            {'text': 'Bitcoin is going to the moon! Bull run incoming', 'engagement': 500},
            {'text': 'Market looks bearish, be careful', 'engagement': 300}
        ]
    }
    
    # Test sentiment analysis
    social_scores = analyzer.analyze_social_sentiment(mock_social_data)
    print(f"Social sentiment scores: {social_scores}")
    
    # Test volume analysis
    volume_data = {'volume_history': [1000, 1200, 800, 1500, 2000]}
    volume_analysis = analyzer.analyze_volume_patterns(volume_data)
    print(f"Volume analysis: {volume_analysis}")
    
    # Test technical analysis
    technical_data = {
        'rsi': 65,
        'macd': 0.02,
        'macd_signal': 0.01,
        'bb_position': 0.6,
        'price_change_24h': 0.05,
        'volume_change_24h': 0.2
    }
    technical_analysis = analyzer.analyze_technical_sentiment(technical_data)
    print(f"Technical analysis: {technical_analysis}")
    
    # Calculate overall sentiment
    news_analysis = {'news_score': 0.1, 'news_sentiment': 'positive'}
    sentiment_metrics = analyzer.calculate_overall_sentiment(
        social_scores, volume_analysis, news_analysis, technical_analysis
    )
    
    print(f"Overall sentiment: {sentiment_metrics.overall_sentiment:.3f} ({sentiment_metrics.sentiment_trend})")
    
    # Generate report
    report = analyzer.generate_sentiment_report("BTC", sentiment_metrics)
    print("Sentiment report generated successfully")


if __name__ == "__main__":
    main() 