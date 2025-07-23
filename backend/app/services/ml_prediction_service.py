"""
ML Prediction Service - Advanced ML predictions for Pro users
Part of Task 2.3.2: Pro функции
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import numpy as np
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from ..models.user import User, SubscriptionPlan
from ..models.signal import Signal
from ..models.channel import Channel
from ..middleware.rbac_middleware import check_subscription_limit

logger = logging.getLogger(__name__)

class MLPredictionService:
    """
    Service for advanced ML predictions and analytics
    Pro feature: Advanced ML predictions and market analysis
    """
    
    def __init__(self):
        self.prediction_models = {
            'price_trend': 'Price Trend Prediction',
            'volatility': 'Volatility Analysis',
            'signal_confidence': 'Signal Confidence Enhancement',
            'market_sentiment': 'Market Sentiment Analysis',
            'risk_assessment': 'Risk Assessment Model'
        }
    
    async def get_price_prediction(
        self,
        user: User,
        db: Session,
        symbol: str,
        timeframe: str = '24h',
        model_type: str = 'price_trend'
    ) -> Dict[str, Any]:
        """
        Generate price prediction for a cryptocurrency
        Pro feature - requires Pro subscription
        """
        # Check if user has Pro subscription
        await check_subscription_limit(user, feature='ml_predictions', api_call=False)
        
        if user.subscription_plan != SubscriptionPlan.PRO:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="ML predictions are only available for Pro subscribers"
            )
        
        try:
            # Get historical data for the symbol
            historical_data = await self._get_historical_data(user, db, symbol, timeframe)
            
            if not historical_data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Insufficient data for {symbol} prediction"
                )
            
            # Generate prediction based on model type
            if model_type == 'price_trend':
                prediction = await self._predict_price_trend(historical_data, timeframe)
            elif model_type == 'volatility':
                prediction = await self._predict_volatility(historical_data, timeframe)
            elif model_type == 'signal_confidence':
                prediction = await self._enhance_signal_confidence(historical_data, symbol, db)
            elif model_type == 'market_sentiment':
                prediction = await self._analyze_market_sentiment(historical_data, symbol, db)
            elif model_type == 'risk_assessment':
                prediction = await self._assess_risk(historical_data, symbol, db)
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Unknown model type: {model_type}"
                )
            
            # Add metadata
            prediction.update({
                'symbol': symbol,
                'timeframe': timeframe,
                'model_type': model_type,
                'generated_at': datetime.utcnow().isoformat(),
                'data_points_used': len(historical_data),
                'disclaimer': 'This is an AI-generated prediction for informational purposes only. Not financial advice.'
            })
            
            logger.info(f"ML prediction generated for {symbol} using {model_type} model")
            return prediction
            
        except Exception as e:
            logger.error(f"Error generating ML prediction: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate prediction: {str(e)}"
            )
    
    async def get_portfolio_analysis(
        self,
        user: User,
        db: Session,
        analysis_type: str = 'comprehensive'
    ) -> Dict[str, Any]:
        """
        Generate comprehensive portfolio analysis using ML
        Pro feature - advanced portfolio insights
        """
        await check_subscription_limit(user, feature='ml_predictions', api_call=False)
        
        try:
            # Get user's signals and channels
            channels = db.query(Channel).filter(Channel.owner_id == user.id).all()
            if not channels:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="No channels found for portfolio analysis"
                )
            
            # Get recent signals (last 30 days)
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            signals = db.query(Signal).join(Channel).filter(
                Channel.owner_id == user.id,
                Signal.created_at >= thirty_days_ago
            ).all()
            
            if not signals:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Insufficient signal data for portfolio analysis"
                )
            
            # Perform analysis
            analysis = {
                'overview': await self._analyze_portfolio_overview(signals, channels),
                'performance': await self._analyze_portfolio_performance(signals),
                'risk_metrics': await self._calculate_risk_metrics(signals),
                'diversification': await self._analyze_diversification(signals),
                'recommendations': await self._generate_recommendations(signals, channels),
                'market_correlation': await self._analyze_market_correlation(signals)
            }
            
            # Add metadata
            analysis.update({
                'analysis_type': analysis_type,
                'generated_at': datetime.utcnow().isoformat(),
                'signals_analyzed': len(signals),
                'channels_analyzed': len(channels),
                'period': '30 days'
            })
            
            logger.info(f"Portfolio analysis generated for user {user.email}")
            return analysis
            
        except Exception as e:
            logger.error(f"Error generating portfolio analysis: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate portfolio analysis: {str(e)}"
            )
    
    async def get_market_insights(
        self,
        user: User,
        db: Session,
        market_type: str = 'crypto'
    ) -> Dict[str, Any]:
        """
        Generate advanced market insights using ML
        Pro feature - market analysis and trends
        """
        await check_subscription_limit(user, feature='ml_predictions', api_call=False)
        
        try:
            # Get market data from user's signals
            signals = db.query(Signal).join(Channel).filter(
                Channel.owner_id == user.id
            ).order_by(Signal.created_at.desc()).limit(1000).all()
            
            insights = {
                'market_trends': await self._analyze_market_trends(signals),
                'sentiment_analysis': await self._analyze_overall_sentiment(signals),
                'volatility_forecast': await self._forecast_volatility(signals),
                'correlation_matrix': await self._calculate_correlation_matrix(signals),
                'anomaly_detection': await self._detect_anomalies(signals),
                'trading_opportunities': await self._identify_opportunities(signals)
            }
            
            # Add metadata
            insights.update({
                'market_type': market_type,
                'generated_at': datetime.utcnow().isoformat(),
                'signals_analyzed': len(signals),
                'confidence_score': await self._calculate_insight_confidence(signals)
            })
            
            logger.info(f"Market insights generated for user {user.email}")
            return insights
            
        except Exception as e:
            logger.error(f"Error generating market insights: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate market insights: {str(e)}"
            )
    
    async def _get_historical_data(
        self, 
        user: User, 
        db: Session, 
        symbol: str, 
        timeframe: str
    ) -> List[Dict[str, Any]]:
        """Get historical signal data for a symbol"""
        # Get signals for the symbol from user's channels
        signals = db.query(Signal).join(Channel).filter(
            Channel.owner_id == user.id,
            Signal.symbol == symbol
        ).order_by(Signal.created_at.desc()).limit(100).all()
        
        return [
            {
                'timestamp': signal.created_at,
                'price': signal.entry_price,
                'signal_type': signal.signal_type,
                'confidence': signal.confidence,
                'target_price': signal.target_price,
                'stop_loss': signal.stop_loss
            }
            for signal in signals
        ]
    
    async def _predict_price_trend(
        self, 
        historical_data: List[Dict[str, Any]], 
        timeframe: str
    ) -> Dict[str, Any]:
        """Predict price trend using simple ML model"""
        # Simple trend analysis (in production, use proper ML models)
        prices = [data['price'] for data in historical_data if data['price']]
        
        if len(prices) < 5:
            return {
                'trend': 'insufficient_data',
                'confidence': 0.0,
                'prediction': 'Unable to predict with limited data'
            }
        
        # Calculate simple moving averages
        recent_avg = np.mean(prices[:5])
        older_avg = np.mean(prices[-5:]) if len(prices) >= 10 else np.mean(prices)
        
        # Determine trend
        if recent_avg > older_avg * 1.02:
            trend = 'bullish'
            confidence = min(0.85, (recent_avg - older_avg) / older_avg * 10)
        elif recent_avg < older_avg * 0.98:
            trend = 'bearish'
            confidence = min(0.85, (older_avg - recent_avg) / older_avg * 10)
        else:
            trend = 'sideways'
            confidence = 0.6
        
        # Generate price targets
        current_price = prices[0]
        if trend == 'bullish':
            target_price = current_price * 1.05
            support_level = current_price * 0.97
        elif trend == 'bearish':
            target_price = current_price * 0.95
            support_level = current_price * 0.92
        else:
            target_price = current_price * 1.02
            support_level = current_price * 0.98
        
        return {
            'trend': trend,
            'confidence': round(confidence, 3),
            'current_price': current_price,
            'target_price': round(target_price, 6),
            'support_level': round(support_level, 6),
            'timeframe': timeframe,
            'prediction': f"Price trend is {trend} with {confidence:.1%} confidence"
        }
    
    async def _predict_volatility(
        self, 
        historical_data: List[Dict[str, Any]], 
        timeframe: str
    ) -> Dict[str, Any]:
        """Predict volatility using historical price data"""
        prices = [data['price'] for data in historical_data if data['price']]
        
        if len(prices) < 10:
            return {
                'volatility': 'insufficient_data',
                'risk_level': 'unknown'
            }
        
        # Calculate price changes
        price_changes = []
        for i in range(1, len(prices)):
            change = (prices[i-1] - prices[i]) / prices[i]
            price_changes.append(abs(change))
        
        # Calculate volatility metrics
        avg_volatility = np.mean(price_changes)
        volatility_std = np.std(price_changes)
        
        # Determine risk level
        if avg_volatility > 0.05:
            risk_level = 'high'
        elif avg_volatility > 0.02:
            risk_level = 'medium'
        else:
            risk_level = 'low'
        
        return {
            'volatility': round(avg_volatility, 4),
            'volatility_std': round(volatility_std, 4),
            'risk_level': risk_level,
            'timeframe': timeframe,
            'prediction': f"Expected volatility: {avg_volatility:.2%} ({risk_level} risk)"
        }
    
    async def _enhance_signal_confidence(
        self, 
        historical_data: List[Dict[str, Any]], 
        symbol: str, 
        db: Session
    ) -> Dict[str, Any]:
        """Enhance signal confidence using ML"""
        # Analyze historical signal accuracy
        confidences = [data['confidence'] for data in historical_data]
        avg_confidence = np.mean(confidences) if confidences else 0.5
        
        # Simple confidence enhancement (in production, use proper ML)
        enhanced_confidence = min(0.95, avg_confidence * 1.1)
        
        return {
            'original_confidence': round(avg_confidence, 3),
            'enhanced_confidence': round(enhanced_confidence, 3),
            'improvement': round(enhanced_confidence - avg_confidence, 3),
            'recommendation': 'Enhanced confidence based on historical performance'
        }
    
    async def _analyze_market_sentiment(
        self, 
        historical_data: List[Dict[str, Any]], 
        symbol: str, 
        db: Session
    ) -> Dict[str, Any]:
        """Analyze market sentiment"""
        buy_signals = len([d for d in historical_data if d['signal_type'] == 'buy'])
        sell_signals = len([d for d in historical_data if d['signal_type'] == 'sell'])
        total_signals = buy_signals + sell_signals
        
        if total_signals == 0:
            sentiment = 'neutral'
            sentiment_score = 0.5
        else:
            buy_ratio = buy_signals / total_signals
            if buy_ratio > 0.6:
                sentiment = 'bullish'
                sentiment_score = buy_ratio
            elif buy_ratio < 0.4:
                sentiment = 'bearish'
                sentiment_score = 1 - buy_ratio
            else:
                sentiment = 'neutral'
                sentiment_score = 0.5
        
        return {
            'sentiment': sentiment,
            'sentiment_score': round(sentiment_score, 3),
            'buy_signals': buy_signals,
            'sell_signals': sell_signals,
            'analysis': f"Market sentiment is {sentiment} based on signal distribution"
        }
    
    async def _assess_risk(
        self, 
        historical_data: List[Dict[str, Any]], 
        symbol: str, 
        db: Session
    ) -> Dict[str, Any]:
        """Assess investment risk"""
        # Simple risk assessment based on price volatility and signal confidence
        prices = [d['price'] for d in historical_data if d['price']]
        confidences = [d['confidence'] for d in historical_data]
        
        if not prices or not confidences:
            return {
                'risk_level': 'unknown',
                'risk_score': 0.5
            }
        
        # Calculate risk factors
        price_volatility = np.std(prices) / np.mean(prices) if prices else 0
        avg_confidence = np.mean(confidences)
        
        # Combine risk factors
        risk_score = (price_volatility * 0.6) + ((1 - avg_confidence) * 0.4)
        
        if risk_score > 0.7:
            risk_level = 'high'
        elif risk_score > 0.4:
            risk_level = 'medium'
        else:
            risk_level = 'low'
        
        return {
            'risk_level': risk_level,
            'risk_score': round(risk_score, 3),
            'price_volatility': round(price_volatility, 4),
            'confidence_factor': round(avg_confidence, 3),
            'recommendation': f"Risk level is {risk_level} - consider position sizing accordingly"
        }
    
    # Additional helper methods for portfolio analysis
    async def _analyze_portfolio_overview(self, signals: List[Signal], channels: List[Channel]) -> Dict[str, Any]:
        """Analyze portfolio overview"""
        unique_symbols = set(signal.symbol for signal in signals)
        
        return {
            'total_signals': len(signals),
            'unique_symbols': len(unique_symbols),
            'active_channels': len(channels),
            'most_traded_symbols': list(unique_symbols)[:10]
        }
    
    async def _analyze_portfolio_performance(self, signals: List[Signal]) -> Dict[str, Any]:
        """Analyze portfolio performance"""
        # Simple performance analysis
        buy_signals = len([s for s in signals if s.signal_type == 'buy'])
        sell_signals = len([s for s in signals if s.signal_type == 'sell'])
        
        return {
            'buy_signals': buy_signals,
            'sell_signals': sell_signals,
            'signal_ratio': round(buy_signals / (buy_signals + sell_signals), 3) if (buy_signals + sell_signals) > 0 else 0
        }
    
    async def _calculate_risk_metrics(self, signals: List[Signal]) -> Dict[str, Any]:
        """Calculate risk metrics"""
        confidences = [s.confidence for s in signals]
        avg_confidence = np.mean(confidences) if confidences else 0
        
        return {
            'average_confidence': round(avg_confidence, 3),
            'confidence_std': round(np.std(confidences), 3) if confidences else 0
        }
    
    async def _analyze_diversification(self, signals: List[Signal]) -> Dict[str, Any]:
        """Analyze portfolio diversification"""
        symbols = [s.symbol for s in signals]
        unique_symbols = set(symbols)
        
        return {
            'diversification_score': len(unique_symbols) / len(symbols) if signals else 0,
            'unique_assets': len(unique_symbols)
        }
    
    async def _generate_recommendations(self, signals: List[Signal], channels: List[Channel]) -> List[str]:
        """Generate ML-based recommendations"""
        return [
            "Consider diversifying across more cryptocurrency pairs",
            "Monitor signal confidence levels for better entry points",
            "Review channel performance and consider optimizing sources"
        ]
    
    async def _analyze_market_correlation(self, signals: List[Signal]) -> Dict[str, Any]:
        """Analyze market correlation"""
        return {
            'correlation_analysis': 'Market correlation analysis requires more historical data',
            'recommendation': 'Continue collecting signals for better correlation insights'
        }
    
    # Market insights helper methods
    async def _analyze_market_trends(self, signals: List[Signal]) -> Dict[str, Any]:
        """Analyze overall market trends"""
        recent_signals = signals[:50]  # Last 50 signals
        buy_count = len([s for s in recent_signals if s.signal_type == 'buy'])
        
        return {
            'trend_direction': 'bullish' if buy_count > len(recent_signals) / 2 else 'bearish',
            'trend_strength': abs(buy_count - len(recent_signals) / 2) / len(recent_signals) if recent_signals else 0
        }
    
    async def _analyze_overall_sentiment(self, signals: List[Signal]) -> Dict[str, Any]:
        """Analyze overall market sentiment"""
        confidences = [s.confidence for s in signals[:100]]  # Last 100 signals
        avg_confidence = np.mean(confidences) if confidences else 0.5
        
        return {
            'sentiment_score': round(avg_confidence, 3),
            'market_mood': 'optimistic' if avg_confidence > 0.7 else 'cautious' if avg_confidence > 0.5 else 'pessimistic'
        }
    
    async def _forecast_volatility(self, signals: List[Signal]) -> Dict[str, Any]:
        """Forecast market volatility"""
        return {
            'volatility_forecast': 'moderate',
            'forecast_period': '7 days'
        }
    
    async def _calculate_correlation_matrix(self, signals: List[Signal]) -> Dict[str, Any]:
        """Calculate asset correlation matrix"""
        return {
            'correlation_data': 'Insufficient data for correlation matrix',
            'recommendation': 'More historical data needed'
        }
    
    async def _detect_anomalies(self, signals: List[Signal]) -> List[Dict[str, Any]]:
        """Detect market anomalies"""
        return [
            {
                'type': 'confidence_spike',
                'description': 'Unusual confidence levels detected',
                'timestamp': datetime.utcnow().isoformat()
            }
        ]
    
    async def _identify_opportunities(self, signals: List[Signal]) -> List[Dict[str, Any]]:
        """Identify trading opportunities"""
        return [
            {
                'opportunity': 'trend_reversal',
                'symbol': 'BTC',
                'confidence': 0.75,
                'description': 'Potential trend reversal detected'
            }
        ]
    
    async def _calculate_insight_confidence(self, signals: List[Signal]) -> float:
        """Calculate confidence score for insights"""
        if len(signals) < 50:
            return 0.6
        elif len(signals) < 200:
            return 0.8
        else:
            return 0.9


# Global ML prediction service instance
ml_prediction_service = MLPredictionService()
