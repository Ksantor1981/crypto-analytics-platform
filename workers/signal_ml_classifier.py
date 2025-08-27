"""
Signal ML Classifier - Система машинного обучения для классификации сигналов
Улучшает качество извлечения сигналов с помощью ML
"""

import json
import logging
import time
import re
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict
from collections import Counter
import math

from improved_signal_parser import ImprovedSignal, ImprovedSignalExtractor, SignalDirection, SignalQuality

logger = logging.getLogger(__name__)

@dataclass
class SignalFeatures:
    """Признаки сигнала для ML"""
    # Текстовые признаки
    text_length: int
    has_entry_price: bool
    has_target_price: bool
    has_stop_loss: bool
    has_leverage: bool
    has_timeframe: bool
    
    # Ключевые слова
    keyword_count: int
    technical_terms: int
    price_terms: int
    direction_terms: int
    
    # Структурные признаки
    has_structured_format: bool
    has_emoji: bool
    has_links: bool
    has_mentions: bool
    
    # Числовые признаки
    price_precision: float
    risk_reward_ratio: float
    confidence_score: float
    
    # Источник
    source_quality: float
    author_reputation: float

@dataclass
class MLPrediction:
    """Предсказание ML модели"""
    signal_quality_score: float
    is_valid_signal: bool
    confidence: float
    risk_level: str
    recommended_action: str
    feature_importance: Dict[str, float]

class SignalMLClassifier:
    """Система машинного обучения для классификации сигналов"""
    
    def __init__(self):
        self.extractor = ImprovedSignalExtractor()
        
        # Ключевые слова для анализа
        self.technical_keywords = [
            'rsi', 'macd', 'bollinger', 'support', 'resistance', 'trend', 'breakout',
            'consolidation', 'divergence', 'fibonacci', 'elliot', 'volume', 'momentum',
            'oversold', 'overbought', 'bullish', 'bearish', 'accumulation', 'distribution'
        ]
        
        self.price_keywords = [
            'entry', 'target', 'stop loss', 'take profit', 'price', 'level', 'zone',
            'high', 'low', 'peak', 'bottom', 'top', 'range', 'channel'
        ]
        
        self.direction_keywords = [
            'long', 'short', 'buy', 'sell', 'bull', 'bear', 'uptrend', 'downtrend',
            'moon', 'pump', 'dump', 'rally', 'crash', 'recovery'
        ]
        
        # Веса для простой ML модели
        self.feature_weights = {
            'text_length': 0.05,
            'has_entry_price': 0.15,
            'has_target_price': 0.15,
            'has_stop_loss': 0.15,
            'has_leverage': 0.05,
            'has_timeframe': 0.05,
            'keyword_count': 0.10,
            'technical_terms': 0.08,
            'price_terms': 0.08,
            'direction_terms': 0.08,
            'has_structured_format': 0.10,
            'has_emoji': -0.02,
            'has_links': -0.01,
            'has_mentions': -0.01,
            'price_precision': 0.05,
            'risk_reward_ratio': 0.08,
            'confidence_score': 0.10,
            'source_quality': 0.08,
            'author_reputation': 0.05
        }
        
        # Пороги для классификации
        self.quality_threshold = 0.6
        self.confidence_threshold = 0.7
        
        # Статистика обучения
        self.training_data = []
        self.model_performance = {
            'accuracy': 0.0,
            'precision': 0.0,
            'recall': 0.0,
            'f1_score': 0.0,
            'total_predictions': 0,
            'correct_predictions': 0
        }
    
    def extract_features(self, signal: ImprovedSignal, original_text: str = "") -> SignalFeatures:
        """Извлекает признаки из сигнала для ML"""
        try:
            # Анализируем оригинальный текст
            text = original_text or signal.original_text or ""
            text_lower = text.lower()
            
            # Текстовые признаки
            text_length = len(text)
            has_entry_price = signal.entry_price is not None
            has_target_price = signal.target_price is not None
            has_stop_loss = signal.stop_loss is not None
            has_leverage = signal.leverage is not None
            has_timeframe = bool(signal.timeframe)
            
            # Подсчет ключевых слов
            keyword_count = 0
            technical_terms = sum(1 for word in self.technical_keywords if word in text_lower)
            price_terms = sum(1 for word in self.price_keywords if word in text_lower)
            direction_terms = sum(1 for word in self.direction_keywords if word in text_lower)
            keyword_count = technical_terms + price_terms + direction_terms
            
            # Структурные признаки
            has_structured_format = self._check_structured_format(text)
            has_emoji = bool(re.search(r'[^\w\s]', text))
            has_links = bool(re.search(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', text))
            has_mentions = bool(re.search(r'@\w+', text))
            
            # Числовые признаки
            price_precision = self._calculate_price_precision(signal)
            risk_reward_ratio = signal.risk_reward_ratio or 0.0
            confidence_score = signal.real_confidence or 0.0
            
            # Источник
            source_quality = self._calculate_source_quality(signal)
            author_reputation = self._calculate_author_reputation(signal)
            
            return SignalFeatures(
                text_length=text_length,
                has_entry_price=has_entry_price,
                has_target_price=has_target_price,
                has_stop_loss=has_stop_loss,
                has_leverage=has_leverage,
                has_timeframe=has_timeframe,
                keyword_count=keyword_count,
                technical_terms=technical_terms,
                price_terms=price_terms,
                direction_terms=direction_terms,
                has_structured_format=has_structured_format,
                has_emoji=has_emoji,
                has_links=has_links,
                has_mentions=has_mentions,
                price_precision=price_precision,
                risk_reward_ratio=risk_reward_ratio,
                confidence_score=confidence_score,
                source_quality=source_quality,
                author_reputation=author_reputation
            )
            
        except Exception as e:
            logger.error(f"Error extracting features: {e}")
            # Возвращаем дефолтные признаки
            return SignalFeatures(
                text_length=0, has_entry_price=False, has_target_price=False,
                has_stop_loss=False, has_leverage=False, has_timeframe=False,
                keyword_count=0, technical_terms=0, price_terms=0, direction_terms=0,
                has_structured_format=False, has_emoji=False, has_links=False,
                has_mentions=False, price_precision=0.0, risk_reward_ratio=0.0,
                confidence_score=0.0, source_quality=0.0, author_reputation=0.0
            )
    
    def _check_structured_format(self, text: str) -> bool:
        """Проверяет структурированный формат сигнала"""
        structured_patterns = [
            r'entry[:\s]+[\d\.]+',
            r'target[:\s]+[\d\.]+',
            r'stop[:\s]+[\d\.]+',
            r'long[:\s]+[\w]+',
            r'short[:\s]+[\w]+',
            r'buy[:\s]+[\w]+',
            r'sell[:\s]+[\w]+'
        ]
        
        matches = sum(1 for pattern in structured_patterns if re.search(pattern, text.lower()))
        return matches >= 2
    
    def _calculate_price_precision(self, signal: ImprovedSignal) -> float:
        """Рассчитывает точность цен"""
        prices = []
        if signal.entry_price:
            prices.append(signal.entry_price)
        if signal.target_price:
            prices.append(signal.target_price)
        if signal.stop_loss:
            prices.append(signal.stop_loss)
        
        if not prices:
            return 0.0
        
        # Проверяем логичность цен
        if signal.direction == SignalDirection.LONG:
            if signal.entry_price and signal.target_price:
                if signal.entry_price >= signal.target_price:
                    return 0.3  # Низкая точность
            if signal.entry_price and signal.stop_loss:
                if signal.entry_price <= signal.stop_loss:
                    return 0.3  # Низкая точность
        elif signal.direction == SignalDirection.SHORT:
            if signal.entry_price and signal.target_price:
                if signal.entry_price <= signal.target_price:
                    return 0.3  # Низкая точность
            if signal.entry_price and signal.stop_loss:
                if signal.entry_price >= signal.stop_loss:
                    return 0.3  # Низкая точность
        
        return 1.0  # Высокая точность
    
    def _calculate_source_quality(self, signal: ImprovedSignal) -> float:
        """Рассчитывает качество источника"""
        source_quality_map = {
            'telegram': 0.8,
            'reddit': 0.6,
            'tradingview': 0.9,
            'twitter': 0.7
        }
        
        source_type = signal.signal_type or 'unknown'
        return source_quality_map.get(source_type, 0.5)
    
    def _calculate_author_reputation(self, signal: ImprovedSignal) -> float:
        """Рассчитывает репутацию автора"""
        # Простая эвристика на основе канала
        channel = signal.channel or ""
        
        if 'binance' in channel.lower():
            return 0.9
        elif 'crypto' in channel.lower():
            return 0.7
        elif 'signals' in channel.lower():
            return 0.6
        else:
            return 0.5
    
    def predict_signal_quality(self, signal: ImprovedSignal, original_text: str = "") -> MLPrediction:
        """Предсказывает качество сигнала с помощью ML"""
        try:
            # Извлекаем признаки
            features = self.extract_features(signal, original_text)
            
            # Рассчитываем взвешенную оценку
            score = 0.0
            feature_importance = {}
            
            for feature_name, weight in self.feature_weights.items():
                feature_value = getattr(features, feature_name)
                
                # Нормализуем числовые признаки
                if isinstance(feature_value, (int, float)):
                    if feature_name in ['text_length', 'keyword_count', 'technical_terms', 'price_terms', 'direction_terms']:
                        normalized_value = min(feature_value / 10.0, 1.0)  # Нормализация
                    elif feature_name in ['price_precision', 'risk_reward_ratio', 'confidence_score', 'source_quality', 'author_reputation']:
                        normalized_value = feature_value
                    else:
                        normalized_value = float(feature_value)
                else:
                    normalized_value = float(feature_value)
                
                score += normalized_value * weight
                feature_importance[feature_name] = normalized_value * weight
            
            # Определяем валидность сигнала
            is_valid_signal = score >= self.quality_threshold
            
            # Рассчитываем уверенность
            confidence = min(score, 1.0)
            
            # Определяем уровень риска
            if score >= 0.8:
                risk_level = "LOW"
            elif score >= 0.6:
                risk_level = "MEDIUM"
            else:
                risk_level = "HIGH"
            
            # Рекомендуемое действие
            if is_valid_signal and confidence >= self.confidence_threshold:
                recommended_action = "TRADE"
            elif is_valid_signal:
                recommended_action = "MONITOR"
            else:
                recommended_action = "IGNORE"
            
            # Обновляем статистику
            self.model_performance['total_predictions'] += 1
            
            return MLPrediction(
                signal_quality_score=score,
                is_valid_signal=is_valid_signal,
                confidence=confidence,
                risk_level=risk_level,
                recommended_action=recommended_action,
                feature_importance=feature_importance
            )
            
        except Exception as e:
            logger.error(f"Error predicting signal quality: {e}")
            return MLPrediction(
                signal_quality_score=0.0,
                is_valid_signal=False,
                confidence=0.0,
                risk_level="HIGH",
                recommended_action="IGNORE",
                feature_importance={}
            )
    
    def improve_signal_extraction(self, text: str, source: str, source_id: str) -> List[ImprovedSignal]:
        """Улучшает извлечение сигналов с помощью ML"""
        try:
            # Извлекаем сигналы обычным способом
            signals = self.extractor.extract_signals_from_text(text, source, source_id)
            
            improved_signals = []
            
            for signal in signals:
                # Предсказываем качество
                prediction = self.predict_signal_quality(signal, text)
                
                # Улучшаем сигнал на основе предсказания
                improved_signal = self._enhance_signal(signal, prediction, text)
                
                if improved_signal:
                    improved_signals.append(improved_signal)
            
            # Сортируем по качеству
            improved_signals.sort(key=lambda s: s.real_confidence or 0, reverse=True)
            
            return improved_signals
            
        except Exception as e:
            logger.error(f"Error improving signal extraction: {e}")
            return []
    
    def _enhance_signal(self, signal: ImprovedSignal, prediction: MLPrediction, text: str) -> Optional[ImprovedSignal]:
        """Улучшает сигнал на основе ML предсказания"""
        try:
            # Обновляем уверенность на основе ML
            if prediction.is_valid_signal:
                signal.real_confidence = max(signal.real_confidence or 0, prediction.confidence * 100)
                signal.calculated_confidence = prediction.signal_quality_score * 100
            else:
                signal.real_confidence = min(signal.real_confidence or 0, prediction.confidence * 100)
                signal.calculated_confidence = prediction.signal_quality_score * 100
            
            # Улучшаем качество сигнала
            if prediction.signal_quality_score >= 0.8:
                signal.signal_quality = SignalQuality.EXCELLENT
            elif prediction.signal_quality_score >= 0.6:
                signal.signal_quality = SignalQuality.GOOD
            elif prediction.signal_quality_score >= 0.4:
                signal.signal_quality = SignalQuality.MEDIUM
            else:
                signal.signal_quality = SignalQuality.POOR
            
            # Добавляем ML метаданные
            signal.ml_metadata = {
                'quality_score': prediction.signal_quality_score,
                'risk_level': prediction.risk_level,
                'recommended_action': prediction.recommended_action,
                'feature_importance': prediction.feature_importance
            }
            
            return signal
            
        except Exception as e:
            logger.error(f"Error enhancing signal: {e}")
            return signal
    
    def train_on_feedback(self, signal: ImprovedSignal, was_correct: bool, actual_profit: float = 0.0):
        """Обучает модель на обратной связи"""
        try:
            # Сохраняем данные для обучения
            training_example = {
                'signal': asdict(signal),
                'was_correct': was_correct,
                'actual_profit': actual_profit,
                'timestamp': datetime.now().isoformat()
            }
            
            self.training_data.append(training_example)
            
            # Обновляем статистику производительности
            if was_correct:
                self.model_performance['correct_predictions'] += 1
            
            # Пересчитываем метрики
            total = self.model_performance['total_predictions']
            correct = self.model_performance['correct_predictions']
            
            if total > 0:
                self.model_performance['accuracy'] = correct / total
                
                # Простое обновление весов на основе обратной связи
                if was_correct:
                    # Увеличиваем веса для успешных признаков
                    for feature_name in self.feature_weights:
                        self.feature_weights[feature_name] *= 1.01
                else:
                    # Уменьшаем веса для неуспешных признаков
                    for feature_name in self.feature_weights:
                        self.feature_weights[feature_name] *= 0.99
                
                # Нормализуем веса
                total_weight = sum(self.feature_weights.values())
                for feature_name in self.feature_weights:
                    self.feature_weights[feature_name] /= total_weight
            
            logger.info(f"Model trained on feedback. Accuracy: {self.model_performance['accuracy']:.3f}")
            
        except Exception as e:
            logger.error(f"Error training on feedback: {e}")
    
    def get_model_performance(self) -> Dict[str, Any]:
        """Возвращает производительность модели"""
        return {
            'performance': self.model_performance,
            'feature_weights': self.feature_weights,
            'training_data_size': len(self.training_data),
            'quality_threshold': self.quality_threshold,
            'confidence_threshold': self.confidence_threshold
        }
    
    def save_model(self, filename: str = "signal_ml_model.json"):
        """Сохраняет модель"""
        try:
            model_data = {
                'feature_weights': self.feature_weights,
                'model_performance': self.model_performance,
                'training_data': self.training_data,
                'thresholds': {
                    'quality_threshold': self.quality_threshold,
                    'confidence_threshold': self.confidence_threshold
                },
                'keywords': {
                    'technical': self.technical_keywords,
                    'price': self.price_keywords,
                    'direction': self.direction_keywords
                },
                'timestamp': datetime.now().isoformat()
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(model_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Model saved to {filename}")
            
        except Exception as e:
            logger.error(f"Error saving model: {e}")
    
    def load_model(self, filename: str = "signal_ml_model.json"):
        """Загружает модель"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                model_data = json.load(f)
            
            self.feature_weights = model_data.get('feature_weights', self.feature_weights)
            self.model_performance = model_data.get('model_performance', self.model_performance)
            self.training_data = model_data.get('training_data', [])
            
            thresholds = model_data.get('thresholds', {})
            self.quality_threshold = thresholds.get('quality_threshold', self.quality_threshold)
            self.confidence_threshold = thresholds.get('confidence_threshold', self.confidence_threshold)
            
            keywords = model_data.get('keywords', {})
            self.technical_keywords = keywords.get('technical', self.technical_keywords)
            self.price_keywords = keywords.get('price', self.price_keywords)
            self.direction_keywords = keywords.get('direction', self.direction_keywords)
            
            logger.info(f"Model loaded from {filename}")
            
        except Exception as e:
            logger.error(f"Error loading model: {e}")

def main():
    """Тестирование ML классификатора сигналов"""
    classifier = SignalMLClassifier()
    
    print("=== Тестирование ML классификатора сигналов ===")
    
    # Тестовые тексты
    test_texts = [
        "BTC LONG Entry: 50000 Target: 55000 Stop: 48000 - Strong bullish momentum with RSI oversold",
        "ETH SHORT opportunity - Entry: 3000 Target: 2800 Stop: 3200 - Bearish divergence on MACD",
        "Random text without any trading signals",
        "ADA breakout confirmed - LONG Entry: 0.45 Target: 0.55 Stop: 0.42 - Volume increasing"
    ]
    
    for i, text in enumerate(test_texts, 1):
        print(f"\n{i}. Анализ текста: {text[:50]}...")
        
        # Извлекаем сигналы
        signals = classifier.improve_signal_extraction(text, "test_source", f"test_{i}")
        
        if signals:
            for signal in signals:
                prediction = classifier.predict_signal_quality(signal, text)
                
                print(f"  📊 Сигнал: {signal.asset} {signal.direction.value}")
                print(f"     Качество: {prediction.signal_quality_score:.3f}")
                print(f"     Валидность: {prediction.is_valid_signal}")
                print(f"     Уверенность: {prediction.confidence:.3f}")
                print(f"     Риск: {prediction.risk_level}")
                print(f"     Действие: {prediction.recommended_action}")
        else:
            print("  ❌ Сигналы не найдены")
    
    # Показываем производительность модели
    print(f"\n📈 Производительность модели:")
    performance = classifier.get_model_performance()
    print(f"  Точность: {performance['performance']['accuracy']:.3f}")
    print(f"  Всего предсказаний: {performance['performance']['total_predictions']}")
    print(f"  Правильных: {performance['performance']['correct_predictions']}")
    
    # Сохраняем модель
    classifier.save_model()
    print(f"\n💾 Модель сохранена в signal_ml_model.json")

if __name__ == "__main__":
    main()
