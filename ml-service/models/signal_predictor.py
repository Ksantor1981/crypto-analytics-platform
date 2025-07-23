"""
Enhanced signal predictor with real market data integration
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime, timedelta

from .market_data_processor import MarketDataProcessor, MarketData, MarketMetrics
from .channel_metrics import ChannelMetricsCalculator, SignalResult, SignalStatus
from .social_signals import SocialSignalsAnalyzer, SocialActivity, SubscriberMetrics

logger = logging.getLogger(__name__)

class SignalPredictor:
    """Enhanced signal predictor with real market data integration"""
    
    def __init__(self):
        self.market_processor = MarketDataProcessor()
        self.channel_calculator = ChannelMetricsCalculator()
        self.social_analyzer = SocialSignalsAnalyzer()
        self.feature_columns = [
            # Technical indicators
            'rsi', 'macd', 'bollinger_position',
            # Market data (real)
            'volume_ratio', 'volatility', 'trend_strength', 'price_momentum',
            'volume_momentum', 'market_regime_trending', 'market_regime_volatile',
            # Signal features
            'signal_strength', 'channel_rating', 'subscriber_count', 'success_rate',
            # Time features
            'hour_of_day', 'day_of_week', 'is_weekend',
            # Historical metrics (real)
            'channel_accuracy', 'channel_roi', 'signal_frequency', 'channel_sharpe',
            'channel_consistency', 'channel_risk_score',
            # Social signals (real)
            'social_engagement_rate', 'social_sentiment', 'viral_potential',
            'community_health', 'activity_trend_score', 'subscriber_activity'
        ]
        
    def add_market_data(self, asset: str, market_data: MarketData):
        """Add real market data for processing"""
        self.market_processor.add_market_data(market_data)
        
    def get_market_features(self, asset: str) -> Dict[str, float]:
        """Get real market features for ML model"""
        metrics = self.market_processor.get_comprehensive_market_metrics()
        
        return {
            'volume_ratio': metrics.volume_ratio,
            'volatility': metrics.volatility,
            'trend_strength': metrics.trend_strength,
            'price_momentum': metrics.price_momentum,
            'volume_momentum': metrics.volume_momentum,
            'market_regime_trending': 1.0 if metrics.market_regime == 'trending' else 0.0,
            'market_regime_volatile': 1.0 if metrics.market_regime == 'volatile' else 0.0,
            'market_regime_ranging': 1.0 if metrics.market_regime == 'ranging' else 0.0
        }
    
    def calculate_technical_indicators(self, price_data: List[float], 
                                     volume_data: List[float] = None) -> Dict[str, float]:
        """Calculate technical indicators from real price data"""
        if len(price_data) < 20:
            return self._get_default_technical_indicators()
        
        prices = np.array(price_data)
        
        # RSI calculation
        delta = np.diff(prices)
        gain = np.where(delta > 0, delta, 0)
        loss = np.where(delta < 0, -delta, 0)
        
        avg_gain = np.mean(gain[-14:]) if len(gain) >= 14 else np.mean(gain)
        avg_loss = np.mean(loss[-14:]) if len(loss) >= 14 else np.mean(loss)
        
        if avg_loss == 0:
            rsi = 100
        else:
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
        
        # MACD calculation
        if len(prices) >= 26:
            ema12 = self._calculate_ema(prices, 12)
            ema26 = self._calculate_ema(prices, 26)
            macd = ema12 - ema26
            macd_signal = self._calculate_ema([macd], 9) if len([macd]) >= 9 else macd
        else:
            macd = 0.0
            macd_signal = 0.0
        
        # Bollinger Bands
        if len(prices) >= 20:
            sma = np.mean(prices[-20:])
            std = np.std(prices[-20:])
            upper_band = sma + (2 * std)
            lower_band = sma - (2 * std)
            current_price = prices[-1]
            bb_position = (current_price - lower_band) / (upper_band - lower_band) if (upper_band - lower_band) > 0 else 0.5
        else:
            bb_position = 0.5
        
        return {
            'rsi': float(rsi),
            'macd': float(macd),
            'macd_signal': float(macd_signal),
            'bollinger_position': float(bb_position)
        }
    
    def _calculate_ema(self, data: np.ndarray, period: int) -> float:
        """Calculate Exponential Moving Average"""
        if len(data) < period:
            return np.mean(data)
        
        alpha = 2 / (period + 1)
        ema = data[0]
        
        for price in data[1:]:
            ema = alpha * price + (1 - alpha) * ema
        
        return ema
    
    def extract_time_features(self, timestamp: datetime) -> Dict[str, float]:
        """Extract time-based features"""
        return {
            'hour_of_day': timestamp.hour / 24.0,  # Normalize to 0-1
            'day_of_week': timestamp.weekday() / 6.0,  # Normalize to 0-1
            'is_weekend': 1.0 if timestamp.weekday() >= 5 else 0.0,
            'is_market_open': 1.0 if 9 <= timestamp.hour <= 17 else 0.0  # Simplified market hours
        }
    
    def calculate_channel_metrics(self, channel_data: Dict[str, Any]) -> Dict[str, float]:
        """Calculate real channel performance metrics using ChannelMetricsCalculator"""
        signals = channel_data.get('signals', [])
        
        if not signals:
            return self._get_default_channel_metrics()
        
        # Convert to SignalResult objects
        signal_results = []
        for signal in signals:
            signal_result = SignalResult(
                signal_id=signal.get('id', f"signal_{len(signal_results)}"),
                channel_id=signal.get('channel_id', 'unknown'),
                timestamp=signal.get('timestamp', datetime.now()),
                entry_price=signal.get('entry_price', 0.0),
                exit_price=signal.get('exit_price'),
                status=SignalStatus.SUCCESSFUL if signal.get('success', False) else SignalStatus.FAILED,
                roi=signal.get('roi', 0.0),
                duration_hours=signal.get('duration_hours')
            )
            signal_results.append(signal_result)
        
        # Calculate metrics using ChannelMetricsCalculator
        channel_metrics = self.channel_calculator.calculate_channel_metrics(
            channel_data.get('channel_id', 'unknown'), 
            signal_results
        )
        
        return {
            'channel_accuracy': channel_metrics.accuracy,
            'channel_roi': channel_metrics.avg_roi,
            'signal_frequency': channel_metrics.signal_frequency,
            'channel_sharpe': channel_metrics.sharpe_ratio,
            'channel_consistency': channel_metrics.consistency_score,
            'channel_risk_score': channel_metrics.risk_score,
            'channel_win_rate': channel_metrics.win_rate,
            'channel_profit_factor': channel_metrics.profit_factor,
            'channel_max_drawdown': channel_metrics.max_drawdown,
            'total_signals': channel_metrics.total_signals,
            'successful_signals': channel_metrics.successful_signals
        }
    
    def predict_signal_success(self, signal_data: Dict[str, Any], 
                             market_data: Optional[MarketData] = None) -> Dict[str, Any]:
        """Predict signal success probability with real market data"""
        
        # Add market data if provided
        if market_data:
            self.market_processor.add_market_data(market_data)
        
        # Extract features
        features = self._extract_features(signal_data)
        
        # Calculate prediction (enhanced model)
        prediction = self._calculate_prediction(features)
        
        # Add market context
        market_context = self._get_market_context()
        
        return {
            'success_probability': prediction['probability'],
            'confidence': prediction['confidence'],
            'risk_score': prediction['risk_score'],
            'features': features,
            'market_context': market_context,
            'recommendation': prediction['recommendation']
        }
    
    def _extract_features(self, signal_data: Dict[str, Any]) -> Dict[str, float]:
        """Extract comprehensive feature set"""
        features = {}
        
        # Market features (real data)
        market_features = self.market_processor.get_feature_vector()
        features.update(market_features)
        
        # Technical indicators (from price history)
        price_history = signal_data.get('price_history', [])
        if price_history:
            technical_indicators = self.calculate_technical_indicators(price_history)
            features.update(technical_indicators)
        else:
            features.update(self._get_default_technical_indicators())
        
        # Signal features
        features.update({
            'signal_strength': signal_data.get('signal_strength', 0.5),
            'channel_rating': signal_data.get('channel_rating', 3.0) / 5.0,  # Normalize
            'subscriber_count': min(signal_data.get('subscriber_count', 1000) / 10000, 1.0),  # Normalize
            'success_rate': signal_data.get('success_rate', 0.6)
        })
        
        # Time features
        timestamp = signal_data.get('timestamp', datetime.now())
        time_features = self.extract_time_features(timestamp)
        features.update(time_features)
        
        # Channel metrics (real historical data)
        channel_data = signal_data.get('channel_data', {})
        channel_metrics = self.calculate_channel_metrics(channel_data)
        features.update({
            'channel_accuracy': channel_metrics['channel_accuracy'],
            'channel_roi': channel_metrics['channel_roi'],
            'signal_frequency': min(channel_metrics['signal_frequency'] / 10, 1.0),  # Normalize
            'channel_sharpe': min(channel_metrics['channel_sharpe'] / 3.0, 1.0),  # Normalize
            'channel_consistency': channel_metrics['channel_consistency'],
            'channel_risk_score': channel_metrics['channel_risk_score'] / 100.0,  # Normalize
            'channel_win_rate': channel_metrics['channel_win_rate'],
            'channel_profit_factor': min(channel_metrics['channel_profit_factor'] / 5.0, 1.0)  # Normalize
        })
        
        # Social signals (real analysis)
        social_data = signal_data.get('social_data', {})
        social_features = self.analyze_social_signals(social_data)
        features.update(social_features)
        
        return features
    
    def _calculate_prediction(self, features: Dict[str, float]) -> Dict[str, Any]:
        """Calculate prediction using enhanced model"""
        
        # Enhanced prediction logic with real market data
        base_probability = 0.5
        
        # Market regime impact
        if features.get('market_regime_trending', 0) > 0.5:
            base_probability += 0.1
        elif features.get('market_regime_volatile', 0) > 0.5:
            base_probability -= 0.05
        
        # Technical indicators impact
        rsi = features.get('rsi', 50)
        if 30 <= rsi <= 70:  # Not overbought/oversold
            base_probability += 0.05
        
        # Volume impact
        volume_ratio = features.get('volume_ratio', 1.0)
        if volume_ratio > 1.2:  # High volume
            base_probability += 0.08
        
        # Trend strength impact
        trend_strength = features.get('trend_strength', 0.0)
        base_probability += trend_strength * 0.1
        
        # Channel quality impact
        channel_accuracy = features.get('channel_accuracy', 0.5)
        base_probability += (channel_accuracy - 0.5) * 0.2
        
        # Signal strength impact
        signal_strength = features.get('signal_strength', 0.5)
        base_probability += (signal_strength - 0.5) * 0.15
        
        # Clamp probability
        probability = np.clip(base_probability, 0.0, 1.0)
        
        # Calculate confidence based on data quality
        confidence = min(0.9, 0.5 + features.get('trend_strength', 0.0) * 0.4)
        
        # Calculate risk score
        volatility = features.get('volatility', 0.2)
        risk_score = min(100, volatility * 100 + (1 - probability) * 50)
        
        # Generate recommendation
        if probability > 0.7:
            recommendation = "Strong buy signal"
        elif probability > 0.6:
            recommendation = "Moderate buy signal"
        elif probability > 0.4:
            recommendation = "Neutral signal"
        elif probability > 0.3:
            recommendation = "Moderate sell signal"
        else:
            recommendation = "Strong sell signal"
        
        return {
            'probability': float(probability),
            'confidence': float(confidence),
            'risk_score': float(risk_score),
            'recommendation': recommendation
        }
    
    def _get_market_context(self) -> Dict[str, Any]:
        """Get current market context"""
        metrics = self.market_processor.get_comprehensive_market_metrics()
        
        return {
            'market_regime': metrics.market_regime,
            'trend_direction': metrics.trend_direction,
            'volatility_level': 'high' if metrics.volatility > 0.4 else 'low' if metrics.volatility < 0.2 else 'normal',
            'volume_trend': 'increasing' if metrics.volume_momentum > 0.1 else 'decreasing' if metrics.volume_momentum < -0.1 else 'stable'
        }
    
    def _get_default_technical_indicators(self) -> Dict[str, float]:
        """Get default technical indicators"""
        return {
            'rsi': 50.0,
            'macd': 0.0,
            'macd_signal': 0.0,
            'bollinger_position': 0.5
        }
    
    def _get_default_channel_metrics(self) -> Dict[str, float]:
        """Get default channel metrics"""
        return {
            'channel_accuracy': 0.5,
            'channel_roi': 0.0,
            'signal_frequency': 0.0,
            'total_signals': 0,
            'successful_signals': 0
        }

    def analyze_social_signals(self, social_data: Dict[str, Any]) -> Dict[str, float]:
        """Analyze social signals and subscriber activity"""
        social_features = {}
        
        # Analyze Telegram activity
        if 'telegram_messages' in social_data:
            telegram_metrics = self.social_analyzer.analyze_telegram_activity(
                social_data['telegram_messages']
            )
            social_features.update({
                'telegram_engagement_rate': telegram_metrics['engagement_rate'],
                'telegram_sentiment': telegram_metrics['sentiment_score'],
                'telegram_viral_potential': telegram_metrics['viral_potential']
            })
        
        # Analyze Twitter activity
        if 'twitter_tweets' in social_data:
            twitter_metrics = self.social_analyzer.analyze_twitter_activity(
                social_data['twitter_tweets']
            )
            social_features.update({
                'twitter_engagement_rate': twitter_metrics['engagement_rate'],
                'twitter_sentiment': twitter_metrics['sentiment_score'],
                'twitter_trending_score': twitter_metrics['trending_score']
            })
        
        # Analyze Reddit activity
        if 'reddit_posts' in social_data:
            reddit_metrics = self.social_analyzer.analyze_reddit_activity(
                social_data['reddit_posts']
            )
            social_features.update({
                'reddit_engagement_rate': reddit_metrics['engagement_rate'],
                'reddit_sentiment': reddit_metrics['sentiment_score'],
                'reddit_community_health': reddit_metrics['community_health']
            })
        
        # Calculate subscriber metrics
        if 'social_activities' in social_data and 'total_subscribers' in social_data:
            activities = social_data['social_activities']
            total_subscribers = social_data['total_subscribers']
            
            subscriber_metrics = self.social_analyzer.calculate_subscriber_metrics(
                activities, total_subscribers
            )
            
            social_features.update({
                'social_engagement_rate': subscriber_metrics.engagement_rate,
                'social_sentiment': 0.5,  # Will be calculated from activities
                'viral_potential': subscriber_metrics.viral_potential,
                'community_health': subscriber_metrics.community_health,
                'activity_trend_score': 0.5 if subscriber_metrics.activity_trend == 'stable' else 
                                      0.8 if subscriber_metrics.activity_trend == 'increasing' else 0.2,
                'subscriber_activity': subscriber_metrics.avg_daily_activity / 100  # Normalize
            })
        
        # Calculate overall social sentiment
        sentiment_scores = []
        for key in ['telegram_sentiment', 'twitter_sentiment', 'reddit_sentiment']:
            if key in social_features:
                sentiment_scores.append(social_features[key])
        
        if sentiment_scores:
            social_features['social_sentiment'] = np.mean(sentiment_scores)
        
        # Calculate overall engagement rate
        engagement_rates = []
        for key in ['telegram_engagement_rate', 'twitter_engagement_rate', 'reddit_engagement_rate']:
            if key in social_features:
                engagement_rates.append(social_features[key])
        
        if engagement_rates:
            social_features['social_engagement_rate'] = np.mean(engagement_rates)
        
        return social_features if social_features else self._get_default_social_features()
    
    def _get_default_social_features(self) -> Dict[str, float]:
        """Get default social features"""
        return {
            'social_engagement_rate': 0.1,
            'social_sentiment': 0.0,
            'viral_potential': 0.0,
            'community_health': 0.5,
            'activity_trend_score': 0.5,
            'subscriber_activity': 0.0
        }


def main():
    """Test enhanced signal predictor"""
    predictor = SignalPredictor()
    
    # Generate mock market data
    market_data = MarketData(
        timestamp=datetime.now(),
        price=50000.0,
        volume=1000000.0,
        high=51000.0,
        low=49000.0,
        open_price=49500.0,
        close_price=50000.0
    )
    
    # Add market data
    predictor.add_market_data(market_data)
    
    # Test signal prediction
    signal_data = {
        'signal_strength': 0.8,
        'channel_rating': 4.5,
        'subscriber_count': 5000,
        'success_rate': 0.75,
        'timestamp': datetime.now(),
        'price_history': [48000, 48500, 49000, 49500, 50000],
        'channel_data': {
            'signals': [
                {'success': True, 'roi': 0.05, 'timestamp': datetime.now() - timedelta(days=1)},
                {'success': True, 'roi': 0.03, 'timestamp': datetime.now() - timedelta(days=2)},
                {'success': False, 'roi': -0.02, 'timestamp': datetime.now() - timedelta(days=3)}
            ]
        }
    }
    
    prediction = predictor.predict_signal_success(signal_data, market_data)
    print(f"Signal Prediction: {prediction}")


if __name__ == "__main__":
    main() 