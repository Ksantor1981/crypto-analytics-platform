"""
Sentiment Analyzer - Система анализа настроений для крипто-сигналов
Улучшает качество извлечения сигналов с помощью анализа настроений
"""

import json
import logging
import time
import re
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict
from collections import Counter

from improved_signal_parser import ImprovedSignal, ImprovedSignalExtractor, SignalDirection, SignalQuality

logger = logging.getLogger(__name__)

@dataclass
class SentimentResult:
    """Результат анализа настроений"""
    overall_sentiment: str  # POSITIVE, NEGATIVE, NEUTRAL
    sentiment_score: float  # -1.0 to 1.0
    confidence: float  # 0.0 to 1.0
    emotion_breakdown: Dict[str, float]  # fear, greed, optimism, pessimism
    market_sentiment: str  # BULLISH, BEARISH, NEUTRAL
    key_phrases: List[str]
    risk_indicators: List[str]

class SentimentAnalyzer:
    """Система анализа настроений для крипто-сигналов"""
    
    def __init__(self):
        # Словари настроений
        self.positive_words = {
            'moon', 'pump', 'bullish', 'uptrend', 'breakout', 'rally', 'recovery',
            'accumulation', 'buy', 'long', 'strong', 'excellent', 'perfect', 'amazing',
            'incredible', 'massive', 'huge', 'big', 'great', 'good', 'positive',
            'optimistic', 'confident', 'sure', 'guaranteed', 'promising', 'potential',
            'opportunity', 'chance', 'profit', 'gain', 'win', 'success', 'victory'
        }
        
        self.negative_words = {
            'dump', 'crash', 'bearish', 'downtrend', 'breakdown', 'fall', 'drop',
            'distribution', 'sell', 'short', 'weak', 'terrible', 'awful', 'horrible',
            'bad', 'negative', 'pessimistic', 'worried', 'scared', 'fear', 'panic',
            'loss', 'lose', 'fail', 'failure', 'risk', 'danger', 'warning', 'avoid'
        }
        
        # Эмоциональные слова
        self.fear_words = {
            'fear', 'panic', 'scared', 'worried', 'anxious', 'nervous', 'stress',
            'danger', 'risk', 'warning', 'caution', 'careful', 'avoid', 'stay away',
            'crash', 'dump', 'fall', 'drop', 'lose', 'loss', 'fail', 'failure'
        }
        
        self.greed_words = {
            'greed', 'moon', 'pump', 'massive', 'huge', 'big', 'profit', 'gain',
            'win', 'success', 'victory', 'rich', 'wealth', 'money', 'cash',
            'lamborghini', 'yacht', 'mansion', 'million', 'billion', '100x', '1000x'
        }
        
        self.optimism_words = {
            'optimistic', 'confident', 'sure', 'guaranteed', 'promising', 'potential',
            'opportunity', 'chance', 'hope', 'believe', 'trust', 'faith', 'positive',
            'good', 'great', 'excellent', 'perfect', 'amazing', 'incredible'
        }
        
        self.pessimism_words = {
            'pessimistic', 'worried', 'scared', 'fear', 'panic', 'negative',
            'bad', 'terrible', 'awful', 'horrible', 'doubt', 'skeptical', 'uncertain',
            'unsure', 'risk', 'danger', 'warning', 'caution', 'careful'
        }
        
        # Технические индикаторы настроений
        self.bullish_indicators = {
            'rsi oversold', 'macd bullish', 'golden cross', 'support', 'accumulation',
            'breakout', 'uptrend', 'higher high', 'higher low', 'volume increase',
            'buy signal', 'long position', 'bull flag', 'cup and handle'
        }
        
        self.bearish_indicators = {
            'rsi overbought', 'macd bearish', 'death cross', 'resistance', 'distribution',
            'breakdown', 'downtrend', 'lower high', 'lower low', 'volume decrease',
            'sell signal', 'short position', 'bear flag', 'head and shoulders'
        }
        
        # Рисковые индикаторы
        self.risk_indicators = {
            'high risk', 'dangerous', 'volatile', 'uncertain', 'unpredictable',
            'manipulation', 'pump and dump', 'scam', 'fake', 'false', 'misleading',
            'too good to be true', 'guaranteed profit', 'no risk', 'sure thing'
        }
        
        # Веса для анализа
        self.word_weights = {
            'positive': 1.0,
            'negative': -1.0,
            'fear': -0.8,
            'greed': 0.6,
            'optimism': 0.7,
            'pessimism': -0.7
        }
        
        # Пороги для классификации
        self.sentiment_thresholds = {
            'positive': 0.3,
            'negative': -0.3,
            'confidence': 0.5
        }
    
    def analyze_sentiment(self, text: str) -> SentimentResult:
        """Анализирует настроения в тексте"""
        try:
            text_lower = text.lower()
            words = re.findall(r'\b\w+\b', text_lower)
            
            # Подсчитываем слова по категориям
            positive_count = sum(1 for word in words if word in self.positive_words)
            negative_count = sum(1 for word in words if word in self.negative_words)
            
            fear_count = sum(1 for word in words if word in self.fear_words)
            greed_count = sum(1 for word in words if word in self.greed_words)
            optimism_count = sum(1 for word in words if word in self.optimism_words)
            pessimism_count = sum(1 for word in words if word in self.pessimism_words)
            
            # Рассчитываем общий скор настроений
            total_words = len(words)
            if total_words == 0:
                return self._create_neutral_result()
            
            positive_score = (positive_count * self.word_weights['positive']) / total_words
            negative_score = (negative_count * self.word_weights['negative']) / total_words
            
            overall_score = positive_score + negative_score
            
            # Эмоциональный анализ
            emotion_breakdown = {
                'fear': fear_count / total_words,
                'greed': greed_count / total_words,
                'optimism': optimism_count / total_words,
                'pessimism': pessimism_count / total_words
            }
            
            # Определяем общее настроение
            if overall_score > self.sentiment_thresholds['positive']:
                overall_sentiment = "POSITIVE"
            elif overall_score < self.sentiment_thresholds['negative']:
                overall_sentiment = "NEGATIVE"
            else:
                overall_sentiment = "NEUTRAL"
            
            # Анализируем рыночное настроение
            market_sentiment = self._analyze_market_sentiment(text_lower)
            
            # Извлекаем ключевые фразы
            key_phrases = self._extract_key_phrases(text_lower)
            
            # Ищем рисковые индикаторы
            risk_indicators = self._find_risk_indicators(text_lower)
            
            # Рассчитываем уверенность
            confidence = self._calculate_confidence(
                positive_count, negative_count, total_words, emotion_breakdown
            )
            
            return SentimentResult(
                overall_sentiment=overall_sentiment,
                sentiment_score=overall_score,
                confidence=confidence,
                emotion_breakdown=emotion_breakdown,
                market_sentiment=market_sentiment,
                key_phrases=key_phrases,
                risk_indicators=risk_indicators
            )
            
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {e}")
            return self._create_neutral_result()
    
    def _create_neutral_result(self) -> SentimentResult:
        """Создает нейтральный результат"""
        return SentimentResult(
            overall_sentiment="NEUTRAL",
            sentiment_score=0.0,
            confidence=0.0,
            emotion_breakdown={'fear': 0.0, 'greed': 0.0, 'optimism': 0.0, 'pessimism': 0.0},
            market_sentiment="NEUTRAL",
            key_phrases=[],
            risk_indicators=[]
        )
    
    def _analyze_market_sentiment(self, text: str) -> str:
        """Анализирует рыночное настроение"""
        bullish_count = sum(1 for indicator in self.bullish_indicators if indicator in text)
        bearish_count = sum(1 for indicator in self.bearish_indicators if indicator in text)
        
        if bullish_count > bearish_count:
            return "BULLISH"
        elif bearish_count > bullish_count:
            return "BEARISH"
        else:
            return "NEUTRAL"
    
    def _extract_key_phrases(self, text: str) -> List[str]:
        """Извлекает ключевые фразы"""
        key_phrases = []
        
        # Ищем технические паттерны
        technical_patterns = [
            r'rsi\s+(oversold|overbought)',
            r'macd\s+(bullish|bearish)',
            r'(golden|death)\s+cross',
            r'(support|resistance)\s+level',
            r'(breakout|breakdown)',
            r'(uptrend|downtrend)',
            r'volume\s+(increase|decrease)',
            r'(buy|sell)\s+signal'
        ]
        
        for pattern in technical_patterns:
            matches = re.findall(pattern, text)
            key_phrases.extend(matches)
        
        # Ищем эмоциональные фразы
        emotional_patterns = [
            r'(moon|pump|dump|crash)',
            r'(bullish|bearish)',
            r'(strong|weak)',
            r'(excellent|terrible)',
            r'(opportunity|risk)',
            r'(profit|loss)'
        ]
        
        for pattern in emotional_patterns:
            matches = re.findall(pattern, text)
            key_phrases.extend(matches)
        
        return list(set(key_phrases))[:10]  # Возвращаем топ-10 уникальных фраз
    
    def _find_risk_indicators(self, text: str) -> List[str]:
        """Находит рисковые индикаторы"""
        risk_indicators = []
        
        for indicator in self.risk_indicators:
            if indicator in text:
                risk_indicators.append(indicator)
        
        return risk_indicators
    
    def _calculate_confidence(self, positive_count: int, negative_count: int, 
                            total_words: int, emotion_breakdown: Dict[str, float]) -> float:
        """Рассчитывает уверенность анализа"""
        # Базовая уверенность на основе количества найденных слов
        base_confidence = min((positive_count + negative_count) / max(total_words, 1), 1.0)
        
        # Дополнительная уверенность на основе эмоционального разнообразия
        emotion_variance = sum(emotion_breakdown.values())
        emotion_confidence = min(emotion_variance, 1.0)
        
        # Общая уверенность
        confidence = (base_confidence + emotion_confidence) / 2
        
        return min(confidence, 1.0)
    
    def enhance_signal_with_sentiment(self, signal: ImprovedSignal, text: str) -> ImprovedSignal:
        """Улучшает сигнал с помощью анализа настроений"""
        try:
            # Анализируем настроения
            sentiment = self.analyze_sentiment(text)
            
            # Корректируем уверенность сигнала
            sentiment_adjustment = sentiment.sentiment_score * 0.2  # Максимум ±20%
            
            if signal.real_confidence:
                signal.real_confidence = max(0, min(100, 
                    signal.real_confidence + (sentiment_adjustment * 100)))
            
            if signal.calculated_confidence:
                signal.calculated_confidence = max(0, min(100, 
                    signal.calculated_confidence + (sentiment_adjustment * 100)))
            
            # Корректируем качество сигнала
            if sentiment.overall_sentiment == "POSITIVE" and sentiment.confidence > 0.6:
                if signal.signal_quality == SignalQuality.POOR:
                    signal.signal_quality = SignalQuality.MEDIUM
                elif signal.signal_quality == SignalQuality.MEDIUM:
                    signal.signal_quality = SignalQuality.GOOD
            
            elif sentiment.overall_sentiment == "NEGATIVE" and sentiment.confidence > 0.6:
                if signal.signal_quality == SignalQuality.EXCELLENT:
                    signal.signal_quality = SignalQuality.GOOD
                elif signal.signal_quality == SignalQuality.GOOD:
                    signal.signal_quality = SignalQuality.MEDIUM
            
            # Добавляем метаданные настроений
            signal.sentiment_metadata = {
                'overall_sentiment': sentiment.overall_sentiment,
                'sentiment_score': sentiment.sentiment_score,
                'confidence': sentiment.confidence,
                'emotion_breakdown': sentiment.emotion_breakdown,
                'market_sentiment': sentiment.market_sentiment,
                'key_phrases': sentiment.key_phrases,
                'risk_indicators': sentiment.risk_indicators
            }
            
            # Добавляем предупреждения о рисках
            if sentiment.risk_indicators:
                if not hasattr(signal, 'warnings') or signal.warnings is None:
                    signal.warnings = []
                signal.warnings.extend([
                    f"Risk indicator: {indicator}" for indicator in sentiment.risk_indicators
                ])
            
            return signal
            
        except Exception as e:
            logger.error(f"Error enhancing signal with sentiment: {e}")
            return signal
    
    def analyze_signal_quality_with_sentiment(self, signal: ImprovedSignal, text: str) -> Dict[str, Any]:
        """Анализирует качество сигнала с учетом настроений"""
        try:
            sentiment = self.analyze_sentiment(text)
            
            # Оценка качества на основе настроений
            quality_score = 0.0
            quality_factors = []
            
            # Фактор 1: Соответствие направления и настроений
            if signal.direction == SignalDirection.LONG and sentiment.market_sentiment == "BULLISH":
                quality_score += 0.3
                quality_factors.append("Direction matches bullish sentiment")
            elif signal.direction == SignalDirection.SHORT and sentiment.market_sentiment == "BEARISH":
                quality_score += 0.3
                quality_factors.append("Direction matches bearish sentiment")
            else:
                quality_score -= 0.2
                quality_factors.append("Direction contradicts market sentiment")
            
            # Фактор 2: Эмоциональная стабильность
            emotion_variance = sum(sentiment.emotion_breakdown.values())
            if emotion_variance < 0.3:
                quality_score += 0.2
                quality_factors.append("Low emotional volatility")
            elif emotion_variance > 0.7:
                quality_score -= 0.2
                quality_factors.append("High emotional volatility")
            
            # Фактор 3: Рисковые индикаторы
            if not sentiment.risk_indicators:
                quality_score += 0.2
                quality_factors.append("No risk indicators detected")
            else:
                quality_score -= 0.3
                quality_factors.append(f"Risk indicators: {', '.join(sentiment.risk_indicators)}")
            
            # Фактор 4: Уверенность анализа
            if sentiment.confidence > 0.7:
                quality_score += 0.2
                quality_factors.append("High sentiment confidence")
            elif sentiment.confidence < 0.3:
                quality_score -= 0.1
                quality_factors.append("Low sentiment confidence")
            
            # Фактор 5: Технические ключевые фразы
            technical_phrases = [phrase for phrase in sentiment.key_phrases 
                               if any(tech in phrase for tech in ['rsi', 'macd', 'support', 'resistance', 'breakout'])]
            if technical_phrases:
                quality_score += 0.1
                quality_factors.append(f"Technical analysis: {', '.join(technical_phrases)}")
            
            return {
                'quality_score': quality_score,
                'quality_factors': quality_factors,
                'sentiment_analysis': asdict(sentiment),
                'recommendation': self._get_sentiment_recommendation(quality_score, sentiment)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing signal quality with sentiment: {e}")
            return {
                'quality_score': 0.0,
                'quality_factors': ["Error in sentiment analysis"],
                'sentiment_analysis': asdict(self._create_neutral_result()),
                'recommendation': "Unable to analyze"
            }
    
    def _get_sentiment_recommendation(self, quality_score: float, sentiment: SentimentResult) -> str:
        """Получает рекомендацию на основе анализа настроений"""
        if quality_score >= 0.5:
            return "STRONG_BUY" if sentiment.market_sentiment == "BULLISH" else "STRONG_SELL"
        elif quality_score >= 0.2:
            return "BUY" if sentiment.market_sentiment == "BULLISH" else "SELL"
        elif quality_score >= -0.2:
            return "HOLD"
        else:
            return "AVOID"
    
    def get_sentiment_statistics(self, signals: List[ImprovedSignal]) -> Dict[str, Any]:
        """Получает статистику настроений по сигналам"""
        try:
            sentiment_stats = {
                'total_signals': len(signals),
                'sentiment_distribution': {'POSITIVE': 0, 'NEGATIVE': 0, 'NEUTRAL': 0},
                'market_sentiment_distribution': {'BULLISH': 0, 'BEARISH': 0, 'NEUTRAL': 0},
                'average_sentiment_score': 0.0,
                'risk_indicators_found': 0,
                'high_confidence_signals': 0
            }
            
            total_score = 0.0
            
            for signal in signals:
                if hasattr(signal, 'sentiment_metadata') and signal.sentiment_metadata:
                    metadata = signal.sentiment_metadata
                    
                    # Распределение настроений
                    sentiment_stats['sentiment_distribution'][metadata['overall_sentiment']] += 1
                    sentiment_stats['market_sentiment_distribution'][metadata['market_sentiment']] += 1
                    
                    # Суммируем скоры
                    total_score += metadata['sentiment_score']
                    
                    # Рисковые индикаторы
                    if metadata['risk_indicators']:
                        sentiment_stats['risk_indicators_found'] += 1
                    
                    # Высокая уверенность
                    if metadata['confidence'] > 0.7:
                        sentiment_stats['high_confidence_signals'] += 1
            
            # Средний скор
            if sentiment_stats['total_signals'] > 0:
                sentiment_stats['average_sentiment_score'] = total_score / sentiment_stats['total_signals']
            
            return sentiment_stats
            
        except Exception as e:
            logger.error(f"Error getting sentiment statistics: {e}")
            return {}

def main():
    """Тестирование анализатора настроений"""
    analyzer = SentimentAnalyzer()
    
    print("=== Тестирование анализатора настроений ===")
    
    # Тестовые тексты
    test_texts = [
        "BTC LONG Entry: 50000 Target: 55000 Stop: 48000 - Strong bullish momentum with RSI oversold. This is going to the moon! 🚀",
        "ETH SHORT opportunity - Entry: 3000 Target: 2800 Stop: 3200 - Bearish divergence on MACD. Market looks weak and uncertain.",
        "ADA breakout confirmed - LONG Entry: 0.45 Target: 0.55 Stop: 0.42 - Volume increasing. Excellent opportunity for profit!",
        "Random text without any trading signals or emotions.",
        "⚠️ WARNING: This looks like a pump and dump scheme. High risk, avoid! Too good to be true."
    ]
    
    for i, text in enumerate(test_texts, 1):
        print(f"\n{i}. Анализ текста: {text[:60]}...")
        
        # Анализируем настроения
        sentiment = analyzer.analyze_sentiment(text)
        
        print(f"  📊 Общее настроение: {sentiment.overall_sentiment}")
        print(f"     Скор: {sentiment.sentiment_score:.3f}")
        print(f"     Уверенность: {sentiment.confidence:.3f}")
        print(f"     Рыночное настроение: {sentiment.market_sentiment}")
        print(f"     Эмоции: {sentiment.emotion_breakdown}")
        
        if sentiment.key_phrases:
            print(f"     Ключевые фразы: {', '.join(sentiment.key_phrases[:3])}")
        
        if sentiment.risk_indicators:
            print(f"     ⚠️ Риски: {', '.join(sentiment.risk_indicators)}")
    
    # Тестируем улучшение сигналов
    print(f"\n🔧 Тестирование улучшения сигналов:")
    
    test_signal = ImprovedSignal(
        id="test_1",
        asset="BTC",
        direction=SignalDirection.LONG,
        entry_price=50000,
        target_price=55000,
        stop_loss=48000,
        leverage=10,
        timeframe="4H",
        channel="test_channel",
        message_id="test_message",
        original_text="BTC LONG Entry: 50000 Target: 55000 Stop: 48000 - Strong bullish momentum! 🚀",
        cleaned_text="BTC LONG Entry: 50000 Target: 55000 Stop: 48000 - Strong bullish momentum",
        timestamp=datetime.now(),
        extraction_time=0.1,
        signal_quality=SignalQuality.MEDIUM,
        real_confidence=65.0,
        calculated_confidence=60.0,
        bybit_available=True,
        is_valid=True,
        validation_errors=[],
        risk_reward_ratio=2.5,
        potential_profit=10.0,
        potential_loss=4.0
    )
    
    enhanced_signal = analyzer.enhance_signal_with_sentiment(test_signal, test_signal.original_text)
    
    print(f"  📈 Сигнал до улучшения: {test_signal.real_confidence:.1f}% уверенности")
    print(f"  📈 Сигнал после улучшения: {enhanced_signal.real_confidence:.1f}% уверенности")
    
    if hasattr(enhanced_signal, 'sentiment_metadata') and enhanced_signal.sentiment_metadata:
        print(f"  🎭 Настроения: {enhanced_signal.sentiment_metadata['overall_sentiment']}")
        print(f"  📊 Рыночное настроение: {enhanced_signal.sentiment_metadata['market_sentiment']}")

if __name__ == "__main__":
    main()
