"""
Enhanced Signal Processor - Интегрированная система улучшения качества сигналов
Объединяет ML классификацию, анализ настроений и улучшение извлечения цен
"""

import json
import logging
import time
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, asdict

from improved_signal_parser import ImprovedSignal, ImprovedSignalExtractor, SignalDirection, SignalQuality
from signal_ml_classifier import SignalMLClassifier
from sentiment_analyzer import SentimentAnalyzer
from price_level_extractor import PriceLevelExtractor

logger = logging.getLogger(__name__)

@dataclass
class EnhancementResult:
    """Результат улучшения сигнала"""
    original_signal: ImprovedSignal
    enhanced_signal: ImprovedSignal
    ml_score: float
    sentiment_score: float
    price_confidence: float
    overall_quality: float
    improvements: List[str]
    warnings: List[str]
    recommendations: List[str]

class EnhancedSignalProcessor:
    """Интегрированная система улучшения качества сигналов"""
    
    def __init__(self):
        self.extractor = ImprovedSignalExtractor()
        self.ml_classifier = SignalMLClassifier()
        self.sentiment_analyzer = SentimentAnalyzer()
        self.price_extractor = PriceLevelExtractor()
        
        # Веса для интеграции
        self.integration_weights = {
            'ml_score': 0.4,
            'sentiment_score': 0.3,
            'price_confidence': 0.3
        }
        
        # Статистика обработки
        self.processing_stats = {
            'total_signals': 0,
            'enhanced_signals': 0,
            'quality_improvements': 0,
            'average_improvement': 0.0
        }
    
    def enhance_signal_quality(self, signal: ImprovedSignal, original_text: str = "") -> EnhancementResult:
        """Улучшает качество сигнала с помощью всех компонентов"""
        try:
            self.processing_stats['total_signals'] += 1
            
            original_signal = signal
            enhanced_signal = signal
            
            improvements = []
            warnings = []
            recommendations = []
            
            # 1. ML классификация
            ml_prediction = self.ml_classifier.predict_signal_quality(signal, original_text)
            ml_score = ml_prediction.signal_quality_score
            
            if ml_prediction.is_valid_signal:
                improvements.append(f"ML validation passed (score: {ml_score:.3f})")
            else:
                warnings.append(f"ML validation failed (score: {ml_score:.3f})")
            
            # 2. Анализ настроений
            sentiment_result = self.sentiment_analyzer.analyze_sentiment(original_text)
            sentiment_score = sentiment_result.sentiment_score
            
            if sentiment_result.overall_sentiment == "POSITIVE":
                improvements.append(f"Positive sentiment detected (score: {sentiment_score:.3f})")
            elif sentiment_result.overall_sentiment == "NEGATIVE":
                warnings.append(f"Negative sentiment detected (score: {sentiment_score:.3f})")
            
            # 3. Улучшение цен
            enhanced_signal = self.price_extractor.enhance_signal_with_price_data(signal, original_text)
            price_confidence = 0.0
            
            if hasattr(enhanced_signal, 'price_metadata') and enhanced_signal.price_metadata:
                price_confidence = enhanced_signal.price_metadata['price_confidence']
                if price_confidence > 0.7:
                    improvements.append(f"High price confidence ({price_confidence:.3f})")
                elif price_confidence < 0.3:
                    warnings.append(f"Low price confidence ({price_confidence:.3f})")
            
            # 4. Анализ настроений для улучшения сигнала
            enhanced_signal = self.sentiment_analyzer.enhance_signal_with_sentiment(enhanced_signal, original_text)
            
            # 5. Рассчитываем общее качество
            overall_quality = (
                ml_score * self.integration_weights['ml_score'] +
                (sentiment_score + 1) / 2 * self.integration_weights['sentiment_score'] +  # Нормализуем к [0,1]
                price_confidence * self.integration_weights['price_confidence']
            )
            
            # 6. Обновляем качество сигнала
            if overall_quality >= 0.8:
                enhanced_signal.signal_quality = SignalQuality.EXCELLENT
                improvements.append("Signal quality upgraded to EXCELLENT")
            elif overall_quality >= 0.6:
                enhanced_signal.signal_quality = SignalQuality.GOOD
                improvements.append("Signal quality upgraded to GOOD")
            elif overall_quality >= 0.4:
                enhanced_signal.signal_quality = SignalQuality.MEDIUM
            else:
                enhanced_signal.signal_quality = SignalQuality.POOR
                warnings.append("Signal quality downgraded to POOR")
            
            # 7. Обновляем уверенность
            enhanced_signal.real_confidence = max(enhanced_signal.real_confidence or 0, overall_quality * 100)
            enhanced_signal.calculated_confidence = overall_quality * 100
            
            # 8. Генерируем рекомендации
            recommendations = self._generate_recommendations(
                ml_prediction, sentiment_result, enhanced_signal, overall_quality
            )
            
            # 9. Обновляем статистику
            if overall_quality > (ml_score + (sentiment_score + 1) / 2 + price_confidence) / 3:
                self.processing_stats['quality_improvements'] += 1
            
            self.processing_stats['enhanced_signals'] += 1
            
            return EnhancementResult(
                original_signal=original_signal,
                enhanced_signal=enhanced_signal,
                ml_score=ml_score,
                sentiment_score=sentiment_score,
                price_confidence=price_confidence,
                overall_quality=overall_quality,
                improvements=improvements,
                warnings=warnings,
                recommendations=recommendations
            )
            
        except Exception as e:
            logger.error(f"Error enhancing signal quality: {e}")
            return EnhancementResult(
                original_signal=signal,
                enhanced_signal=signal,
                ml_score=0.0,
                sentiment_score=0.0,
                price_confidence=0.0,
                overall_quality=0.0,
                improvements=[],
                warnings=[f"Enhancement error: {str(e)}"],
                recommendations=["Check signal data and try again"]
            )
    
    def _generate_recommendations(self, ml_prediction, sentiment_result, signal, overall_quality) -> List[str]:
        """Генерирует рекомендации на основе анализа"""
        recommendations = []
        
        # Рекомендации на основе ML
        if ml_prediction.recommended_action == "TRADE":
            recommendations.append("ML model recommends trading this signal")
        elif ml_prediction.recommended_action == "MONITOR":
            recommendations.append("ML model suggests monitoring this signal")
        elif ml_prediction.recommended_action == "IGNORE":
            recommendations.append("ML model suggests ignoring this signal")
        
        # Рекомендации на основе настроений
        if sentiment_result.risk_indicators:
            recommendations.append(f"Risk indicators detected: {', '.join(sentiment_result.risk_indicators)}")
        
        if sentiment_result.market_sentiment == "BULLISH" and signal.direction == SignalDirection.LONG:
            recommendations.append("Sentiment aligns with LONG position")
        elif sentiment_result.market_sentiment == "BEARISH" and signal.direction == SignalDirection.SHORT:
            recommendations.append("Sentiment aligns with SHORT position")
        elif sentiment_result.market_sentiment != "NEUTRAL":
            recommendations.append(f"Sentiment ({sentiment_result.market_sentiment}) may contradict position direction")
        
        # Рекомендации на основе качества
        if overall_quality >= 0.8:
            recommendations.append("High quality signal - consider larger position size")
        elif overall_quality < 0.4:
            recommendations.append("Low quality signal - consider smaller position size or skip")
        
        # Рекомендации на основе цен
        if hasattr(signal, 'price_metadata') and signal.price_metadata:
            if signal.price_metadata['validation_errors']:
                recommendations.append("Price validation errors detected - review carefully")
            if signal.price_metadata['suggestions']:
                recommendations.extend(signal.price_metadata['suggestions'])
        
        return recommendations
    
    def process_text_with_enhancement(self, text: str, source: str, source_id: str) -> Dict[str, Any]:
        """Обрабатывает текст с улучшенным извлечением сигналов"""
        try:
            # Извлекаем базовые сигналы
            basic_signals = self.extractor.extract_signals_from_text(text, source, source_id)
            
            enhanced_signals = []
            enhancement_results = []
            
            for signal in basic_signals:
                # Улучшаем каждый сигнал
                enhancement_result = self.enhance_signal_quality(signal, text)
                enhanced_signals.append(enhancement_result.enhanced_signal)
                enhancement_results.append(enhancement_result)
            
            # Сортируем по общему качеству
            enhanced_signals.sort(key=lambda s: s.real_confidence or 0, reverse=True)
            
            # Рассчитываем статистику
            total_quality = sum(result.overall_quality for result in enhancement_results)
            avg_quality = total_quality / len(enhancement_results) if enhancement_results else 0.0
            
            self.processing_stats['average_improvement'] = (
                (self.processing_stats['average_improvement'] * (self.processing_stats['enhanced_signals'] - 1) + avg_quality) /
                self.processing_stats['enhanced_signals']
            )
            
            return {
                'success': True,
                'total_signals': len(basic_signals),
                'enhanced_signals': len(enhanced_signals),
                'average_quality': avg_quality,
                'signals': enhanced_signals,
                'enhancement_results': enhancement_results,
                'processing_stats': self.processing_stats.copy()
            }
            
        except Exception as e:
            logger.error(f"Error processing text with enhancement: {e}")
            return {
                'success': False,
                'error': str(e),
                'total_signals': 0,
                'enhanced_signals': 0,
                'average_quality': 0.0,
                'signals': [],
                'enhancement_results': [],
                'processing_stats': self.processing_stats.copy()
            }
    
    def batch_enhance_signals(self, signals: List[ImprovedSignal], texts: List[str] = None) -> Dict[str, Any]:
        """Улучшает качество множества сигналов"""
        try:
            enhanced_signals = []
            enhancement_results = []
            
            for i, signal in enumerate(signals):
                original_text = texts[i] if texts and i < len(texts) else signal.original_text or ""
                
                enhancement_result = self.enhance_signal_quality(signal, original_text)
                enhanced_signals.append(enhancement_result.enhanced_signal)
                enhancement_results.append(enhancement_result)
            
            # Сортируем по качеству
            enhanced_signals.sort(key=lambda s: s.real_confidence or 0, reverse=True)
            
            # Статистика
            quality_scores = [result.overall_quality for result in enhancement_results]
            avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0.0
            
            quality_distribution = {
                'excellent': len([s for s in enhanced_signals if s.signal_quality == SignalQuality.EXCELLENT]),
                'good': len([s for s in enhanced_signals if s.signal_quality == SignalQuality.GOOD]),
                'medium': len([s for s in enhanced_signals if s.signal_quality == SignalQuality.MEDIUM]),
                'poor': len([s for s in enhanced_signals if s.signal_quality == SignalQuality.POOR])
            }
            
            return {
                'success': True,
                'total_signals': len(signals),
                'enhanced_signals': len(enhanced_signals),
                'average_quality': avg_quality,
                'quality_distribution': quality_distribution,
                'signals': enhanced_signals,
                'enhancement_results': enhancement_results,
                'processing_stats': self.processing_stats.copy()
            }
            
        except Exception as e:
            logger.error(f"Error batch enhancing signals: {e}")
            return {
                'success': False,
                'error': str(e),
                'total_signals': len(signals),
                'enhanced_signals': 0,
                'average_quality': 0.0,
                'quality_distribution': {},
                'signals': [],
                'enhancement_results': [],
                'processing_stats': self.processing_stats.copy()
            }
    
    def get_enhancement_statistics(self) -> Dict[str, Any]:
        """Возвращает статистику улучшения"""
        return {
            'processing_stats': self.processing_stats,
            'integration_weights': self.integration_weights,
            'ml_performance': self.ml_classifier.get_model_performance(),
            'sentiment_stats': self.sentiment_analyzer.get_sentiment_statistics([])
        }
    
    def save_enhancement_data(self, filename: str = "enhanced_signals_data.json"):
        """Сохраняет данные улучшения"""
        try:
            data = {
                'processing_stats': self.processing_stats,
                'integration_weights': self.integration_weights,
                'timestamp': datetime.now().isoformat()
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Enhancement data saved to {filename}")
            
        except Exception as e:
            logger.error(f"Error saving enhancement data: {e}")
    
    def load_enhancement_data(self, filename: str = "enhanced_signals_data.json"):
        """Загружает данные улучшения"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.processing_stats = data.get('processing_stats', self.processing_stats)
            self.integration_weights = data.get('integration_weights', self.integration_weights)
            
            logger.info(f"Enhancement data loaded from {filename}")
            
        except Exception as e:
            logger.error(f"Error loading enhancement data: {e}")

def main():
    """Тестирование улучшенного процессора сигналов"""
    processor = EnhancedSignalProcessor()
    
    print("=== Тестирование улучшенного процессора сигналов ===")
    
    # Тестовые тексты
    test_texts = [
        "BTC LONG Entry: 50000 Target: 55000 Stop: 48000 - Strong bullish momentum with RSI oversold. This is going to the moon! 🚀",
        "ETH SHORT Entry: 3000 Target: 2800 Stop: 3200 - Bearish divergence on MACD. Market looks weak and uncertain.",
        "ADA LONG Entry: 0.45 Target: 0.55 Stop: 0.42 - Volume increasing. Excellent opportunity for profit!",
        "⚠️ WARNING: This looks like a pump and dump scheme. High risk, avoid! Too good to be true."
    ]
    
    for i, text in enumerate(test_texts, 1):
        print(f"\n{i}. Обработка текста: {text[:60]}...")
        
        # Обрабатываем с улучшением
        result = processor.process_text_with_enhancement(text, "test_source", f"test_{i}")
        
        if result['success']:
            print(f"  ✅ Обработано сигналов: {result['enhanced_signals']}")
            print(f"  📊 Среднее качество: {result['average_quality']:.3f}")
            
            for j, signal in enumerate(result['signals'][:2]):  # Показываем первые 2 сигнала
                print(f"    {j+1}. {signal.asset} {signal.direction.value}")
                print(f"       Качество: {signal.signal_quality.value}")
                print(f"       Уверенность: {signal.real_confidence:.1f}%")
                
                if hasattr(signal, 'ml_metadata') and signal.ml_metadata:
                    print(f"       ML скор: {signal.ml_metadata['quality_score']:.3f}")
                
                if hasattr(signal, 'sentiment_metadata') and signal.sentiment_metadata:
                    print(f"       Настроения: {signal.sentiment_metadata['overall_sentiment']}")
        else:
            print(f"  ❌ Ошибка: {result['error']}")
    
    # Тестируем пакетную обработку
    print(f"\n🔧 Тестирование пакетной обработки:")
    
    test_signals = [
        ImprovedSignal(
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
        ),
        ImprovedSignal(
            id="test_2",
            asset="ETH",
            direction=SignalDirection.SHORT,
            entry_price=3000,
            target_price=2800,
            stop_loss=3200,
            leverage=5,
            timeframe="1H",
            channel="test_channel",
            message_id="test_message",
            original_text="ETH SHORT Entry: 3000 Target: 2800 Stop: 3200 - Bearish divergence",
            cleaned_text="ETH SHORT Entry: 3000 Target: 2800 Stop: 3200 - Bearish divergence",
            timestamp=datetime.now(),
            extraction_time=0.1,
            signal_quality=SignalQuality.GOOD,
            real_confidence=75.0,
            calculated_confidence=70.0,
            bybit_available=True,
            is_valid=True,
            validation_errors=[],
            risk_reward_ratio=2.0,
            potential_profit=6.7,
            potential_loss=3.3
        )
    ]
    
    batch_result = processor.batch_enhance_signals(test_signals)
    
    if batch_result['success']:
        print(f"  ✅ Пакетная обработка завершена")
        print(f"  📊 Среднее качество: {batch_result['average_quality']:.3f}")
        print(f"  📈 Распределение качества: {batch_result['quality_distribution']}")
        
        for signal in batch_result['signals']:
            print(f"    - {signal.asset} {signal.direction.value}: {signal.signal_quality.value} ({signal.real_confidence:.1f}%)")
    else:
        print(f"  ❌ Ошибка пакетной обработки: {batch_result['error']}")
    
    # Показываем статистику
    print(f"\n📈 Статистика обработки:")
    stats = processor.get_enhancement_statistics()
    print(f"  Всего сигналов: {stats['processing_stats']['total_signals']}")
    print(f"  Улучшено: {stats['processing_stats']['enhanced_signals']}")
    print(f"  Улучшения качества: {stats['processing_stats']['quality_improvements']}")
    print(f"  Среднее улучшение: {stats['processing_stats']['average_improvement']:.3f}")
    
    # Сохраняем данные
    processor.save_enhancement_data()
    print(f"\n💾 Данные сохранены в enhanced_signals_data.json")

if __name__ == "__main__":
    main()
