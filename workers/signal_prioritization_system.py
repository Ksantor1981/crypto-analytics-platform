import json
import logging
import re
import hashlib
from typing import Dict, List, Optional, Any, Tuple, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from collections import defaultdict, Counter
import difflib
from enum import Enum

from improved_signal_parser import ImprovedSignal, ImprovedSignalExtractor, SignalDirection, SignalQuality

logger = logging.getLogger(__name__)

class PriorityLevel(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class DuplicateType(Enum):
    EXACT = "exact"
    SIMILAR = "similar"
    PARTIAL = "partial"
    NONE = "none"

@dataclass
class SignalPriority:
    signal: ImprovedSignal
    priority_score: float
    priority_level: PriorityLevel
    ranking_factors: Dict[str, float]
    duplicate_info: Dict[str, Any]
    group_id: Optional[str] = None
    recommendations: List[str] = None

@dataclass
class SignalGroup:
    group_id: str
    signals: List[ImprovedSignal]
    primary_signal: ImprovedSignal
    group_score: float
    group_type: str
    common_features: Dict[str, Any]
    recommendations: List[str]

@dataclass
class PrioritizationResult:
    prioritized_signals: List[SignalPriority]
    signal_groups: List[SignalGroup]
    duplicates_removed: int
    total_signals_processed: int
    priority_distribution: Dict[str, int]
    recommendations_summary: List[str]

class SignalPrioritizationSystem:
    def __init__(self):
        self.extractor = ImprovedSignalExtractor()
        
        # Веса для различных факторов приоритизации
        self.priority_weights = {
            'confidence': 0.25,
            'quality': 0.20,
            'risk_reward': 0.15,
            'recency': 0.15,
            'source_reliability': 0.10,
            'asset_popularity': 0.05,
            'leverage': 0.05,
            'timeframe': 0.05
        }
        
        # Пороги для уровней приоритета
        self.priority_thresholds = {
            PriorityLevel.CRITICAL: 0.85,
            PriorityLevel.HIGH: 0.70,
            PriorityLevel.MEDIUM: 0.50,
            PriorityLevel.LOW: 0.30
        }
        
        # Настройки для определения дубликатов
        self.similarity_threshold = 0.8
        self.time_window_hours = 24
        
        # Популярные активы (можно обновлять динамически)
        self.popular_assets = {
            'BTC': 1.0, 'ETH': 0.9, 'BNB': 0.8, 'ADA': 0.7, 'SOL': 0.7,
            'DOT': 0.6, 'AVAX': 0.6, 'MATIC': 0.6, 'LINK': 0.5, 'UNI': 0.5
        }
        
        # Надежность источников (можно обновлять на основе исторических данных)
        self.source_reliability = {
            'binance_killers': 0.8,
            'crypto_signals': 0.7,
            'trading_signals': 0.6,
            'reddit': 0.5,
            'tradingview': 0.6
        }

    def prioritize_signals(self, signals: List[ImprovedSignal]) -> PrioritizationResult:
        """Основной метод для приоритизации сигналов"""
        logger.info(f"Начинаем приоритизацию {len(signals)} сигналов")
        
        # Шаг 1: Фильтрация дубликатов
        unique_signals, duplicates_removed = self._filter_duplicates(signals)
        logger.info(f"Удалено {duplicates_removed} дубликатов, осталось {len(unique_signals)} уникальных сигналов")
        
        # Шаг 2: Ранжирование по важности
        prioritized_signals = []
        for signal in unique_signals:
            priority = self._calculate_signal_priority(signal)
            prioritized_signals.append(priority)
        
        # Сортировка по приоритету
        prioritized_signals.sort(key=lambda x: x.priority_score, reverse=True)
        
        # Шаг 3: Группировка похожих сигналов
        signal_groups = self._group_similar_signals(prioritized_signals)
        
        # Шаг 4: Генерация рекомендаций
        recommendations_summary = self._generate_recommendations_summary(prioritized_signals, signal_groups)
        
        # Статистика распределения приоритетов
        priority_distribution = Counter([p.priority_level.value for p in prioritized_signals])
        
        result = PrioritizationResult(
            prioritized_signals=prioritized_signals,
            signal_groups=signal_groups,
            duplicates_removed=duplicates_removed,
            total_signals_processed=len(signals),
            priority_distribution=dict(priority_distribution),
            recommendations_summary=recommendations_summary
        )
        
        logger.info(f"Приоритизация завершена. Критических: {priority_distribution.get('critical', 0)}, "
                   f"Высоких: {priority_distribution.get('high', 0)}")
        
        return result

    def _filter_duplicates(self, signals: List[ImprovedSignal]) -> Tuple[List[ImprovedSignal], int]:
        """Фильтрация дубликатов сигналов"""
        unique_signals = []
        duplicates_removed = 0
        seen_hashes = set()
        
        for signal in signals:
            # Создаем хеш для сигнала
            signal_hash = self._create_signal_hash(signal)
            
            if signal_hash not in seen_hashes:
                # Проверяем на похожие сигналы
                is_duplicate = False
                for existing_signal in unique_signals:
                    duplicate_type = self._check_similarity(signal, existing_signal)
                    if duplicate_type != DuplicateType.NONE:
                        is_duplicate = True
                        duplicates_removed += 1
                        logger.debug(f"Найден дубликат типа {duplicate_type.value}: {signal.asset} {signal.direction.value}")
                        break
                
                if not is_duplicate:
                    unique_signals.append(signal)
                    seen_hashes.add(signal_hash)
        
        return unique_signals, duplicates_removed

    def _create_signal_hash(self, signal: ImprovedSignal) -> str:
        """Создание хеша для сигнала"""
        # Создаем строку с ключевыми параметрами
        key_params = f"{signal.asset}_{signal.direction.value}_{signal.entry_price}_{signal.target_price}_{signal.stop_loss}"
        return hashlib.md5(key_params.encode()).hexdigest()

    def _check_similarity(self, signal1: ImprovedSignal, signal2: ImprovedSignal) -> DuplicateType:
        """Проверка схожести двух сигналов"""
        # Проверяем временное окно
        time_diff = abs((signal1.timestamp - signal2.timestamp).total_seconds() / 3600)
        if time_diff > self.time_window_hours:
            return DuplicateType.NONE
        
        # Проверяем точное совпадение
        if (signal1.asset == signal2.asset and 
            signal1.direction == signal2.direction and
            abs(signal1.entry_price - signal2.entry_price) < 0.01):
            return DuplicateType.EXACT
        
        # Проверяем схожесть текста
        text_similarity = self._calculate_text_similarity(
            signal1.cleaned_text, signal2.cleaned_text
        )
        
        if text_similarity > self.similarity_threshold:
            return DuplicateType.SIMILAR
        
        # Проверяем частичное совпадение параметров
        if (signal1.asset == signal2.asset and 
            signal1.direction == signal2.direction and
            abs(signal1.entry_price - signal2.entry_price) / signal1.entry_price < 0.05):
            return DuplicateType.PARTIAL
        
        return DuplicateType.NONE

    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Вычисление схожести текста"""
        if not text1 or not text2:
            return 0.0
        
        # Используем SequenceMatcher для вычисления схожести
        similarity = difflib.SequenceMatcher(None, text1.lower(), text2.lower()).ratio()
        return similarity

    def _calculate_signal_priority(self, signal: ImprovedSignal) -> SignalPriority:
        """Вычисление приоритета сигнала"""
        factors = {}
        
        # Фактор уверенности
        factors['confidence'] = (signal.real_confidence + signal.calculated_confidence) / 2
        
        # Фактор качества
        quality_scores = {
            SignalQuality.EXCELLENT: 1.0,
            SignalQuality.GOOD: 0.8,
            SignalQuality.BASIC: 0.6,
            SignalQuality.POOR: 0.4,
            SignalQuality.BASIC: 0.5
        }
        factors['quality'] = quality_scores.get(signal.signal_quality, 0.5)
        
        # Фактор риск/прибыль
        if signal.risk_reward_ratio and signal.risk_reward_ratio > 0:
            factors['risk_reward'] = min(signal.risk_reward_ratio / 3.0, 1.0)  # Нормализуем к 1.0
        else:
            factors['risk_reward'] = 0.5
        
        # Фактор актуальности
        if signal.timestamp:
            try:
                # Проверяем, является ли timestamp строкой или datetime объектом
                if isinstance(signal.timestamp, str):
                    # Парсим строку в datetime
                    if 'T' in signal.timestamp:
                        # ISO формат
                        timestamp_dt = datetime.fromisoformat(signal.timestamp.replace('Z', '+00:00'))
                    else:
                        # Простой формат
                        timestamp_dt = datetime.strptime(signal.timestamp, '%Y-%m-%d %H:%M:%S')
                else:
                    # Уже datetime объект
                    timestamp_dt = signal.timestamp
                
                hours_old = (datetime.now() - timestamp_dt).total_seconds() / 3600
                factors['recency'] = max(0, 1 - hours_old / 24)  # Снижается за 24 часа
            except Exception as e:
                logger.warning(f"Ошибка парсинга timestamp {signal.timestamp}: {e}")
                factors['recency'] = 0.5
        else:
            factors['recency'] = 0.5
        
        # Фактор надежности источника
        source = signal.channel.lower()
        factors['source_reliability'] = self.source_reliability.get(source, 0.5)
        
        # Фактор популярности актива
        factors['asset_popularity'] = self.popular_assets.get(signal.asset, 0.3)
        
        # Фактор кредитного плеча
        if signal.leverage:
            factors['leverage'] = min(signal.leverage / 10.0, 1.0)  # Нормализуем к 1.0
        else:
            factors['leverage'] = 0.5
        
        # Фактор временного фрейма
        timeframe_scores = {
            '1m': 0.3, '5m': 0.4, '15m': 0.5, '30m': 0.6,
            '1h': 0.7, '4h': 0.8, '1d': 0.9, '1w': 1.0
        }
        factors['timeframe'] = timeframe_scores.get(signal.timeframe, 0.5)
        
        # Вычисляем общий приоритет
        priority_score = sum(factors[factor] * self.priority_weights[factor] 
                           for factor in self.priority_weights)
        
        # Определяем уровень приоритета
        priority_level = PriorityLevel.LOW
        for level, threshold in self.priority_thresholds.items():
            if priority_score >= threshold:
                priority_level = level
                break
        
        # Информация о дубликатах
        duplicate_info = {
            'type': DuplicateType.NONE.value,
            'similar_signals': 0
        }
        
        return SignalPriority(
            signal=signal,
            priority_score=priority_score,
            priority_level=priority_level,
            ranking_factors=factors,
            duplicate_info=duplicate_info,
            recommendations=[]
        )

    def _group_similar_signals(self, prioritized_signals: List[SignalPriority]) -> List[SignalGroup]:
        """Группировка похожих сигналов"""
        groups = []
        processed_signals = set()
        
        for i, priority_signal in enumerate(prioritized_signals):
            if i in processed_signals:
                continue
            
            # Создаем новую группу
            group_signals = [priority_signal.signal]
            processed_signals.add(i)
            
            # Ищем похожие сигналы
            for j, other_priority_signal in enumerate(prioritized_signals[i+1:], i+1):
                if j in processed_signals:
                    continue
                
                if self._signals_belong_to_group(priority_signal.signal, other_priority_signal.signal):
                    group_signals.append(other_priority_signal.signal)
                    processed_signals.add(j)
            
            if len(group_signals) > 1:
                # Создаем группу
                group = self._create_signal_group(group_signals)
                groups.append(group)
                
                # Обновляем group_id для всех сигналов в группе
                for signal in group_signals:
                    for priority_signal in prioritized_signals:
                        if priority_signal.signal.id == signal.id:
                            priority_signal.group_id = group.group_id
                            break
        
        return groups

    def _signals_belong_to_group(self, signal1: ImprovedSignal, signal2: ImprovedSignal) -> bool:
        """Проверка, принадлежат ли сигналы к одной группе"""
        # Одинаковый актив и направление
        if signal1.asset != signal2.asset or signal1.direction != signal2.direction:
            return False
        
        # Временное окно (в пределах 6 часов)
        try:
            # Обрабатываем timestamp для обоих сигналов
            def parse_timestamp(ts):
                if isinstance(ts, str):
                    if 'T' in ts:
                        return datetime.fromisoformat(ts.replace('Z', '+00:00'))
                    else:
                        return datetime.strptime(ts, '%Y-%m-%d %H:%M:%S')
                return ts
            
            ts1 = parse_timestamp(signal1.timestamp)
            ts2 = parse_timestamp(signal2.timestamp)
            
            time_diff = abs((ts1 - ts2).total_seconds() / 3600)
            if time_diff > 6:
                return False
        except Exception as e:
            logger.warning(f"Ошибка сравнения timestamp: {e}")
            return False
        
        # Схожие цены входа (в пределах 5%)
        if abs(signal1.entry_price - signal2.entry_price) / signal1.entry_price > 0.05:
            return False
        
        return True

    def _create_signal_group(self, signals: List[ImprovedSignal]) -> SignalGroup:
        """Создание группы сигналов"""
        group_id = f"group_{signals[0].asset}_{signals[0].direction.value}_{int(signals[0].timestamp.timestamp())}"
        
        # Основной сигнал (с наивысшим приоритетом)
        primary_signal = max(signals, key=lambda s: s.real_confidence)
        
        # Общий счет группы
        group_score = sum(s.real_confidence for s in signals) / len(signals)
        
        # Тип группы
        if len(signals) >= 3:
            group_type = "strong_consensus"
        elif len(signals) == 2:
            group_type = "moderate_consensus"
        else:
            group_type = "single_signal"
        
        # Общие характеристики
        common_features = {
            'asset': signals[0].asset,
            'direction': signals[0].direction.value,
            'avg_entry_price': sum(s.entry_price for s in signals) / len(signals),
            'avg_confidence': sum(s.real_confidence for s in signals) / len(signals),
            'signal_count': len(signals)
        }
        
        # Рекомендации для группы
        recommendations = self._generate_group_recommendations(signals, group_type)
        
        return SignalGroup(
            group_id=group_id,
            signals=signals,
            primary_signal=primary_signal,
            group_score=group_score,
            group_type=group_type,
            common_features=common_features,
            recommendations=recommendations
        )

    def _generate_recommendations_summary(self, prioritized_signals: List[SignalPriority], 
                                        signal_groups: List[SignalGroup]) -> List[str]:
        """Генерация общих рекомендаций"""
        recommendations = []
        
        # Анализ распределения приоритетов
        critical_count = sum(1 for s in prioritized_signals if s.priority_level == PriorityLevel.CRITICAL)
        high_count = sum(1 for s in prioritized_signals if s.priority_level == PriorityLevel.HIGH)
        
        if critical_count > 0:
            recommendations.append(f"⚠️ Критических сигналов: {critical_count}. Рекомендуется приоритетное внимание.")
        
        if high_count > 3:
            recommendations.append(f"📈 Много высокоприоритетных сигналов ({high_count}). Рассмотрите диверсификацию.")
        
        # Анализ групп
        strong_groups = [g for g in signal_groups if g.group_type == "strong_consensus"]
        if strong_groups:
            recommendations.append(f"🎯 Найдено {len(strong_groups)} групп с сильным консенсусом. Высокая надежность.")
        
        # Анализ активов
        asset_counts = Counter(s.signal.asset for s in prioritized_signals)
        top_assets = asset_counts.most_common(3)
        if top_assets:
            recommendations.append(f"🔥 Топ активы: {', '.join(f'{asset} ({count})' for asset, count in top_assets)}")
        
        # Анализ направлений
        direction_counts = Counter(s.signal.direction.value for s in prioritized_signals)
        if direction_counts:
            dominant_direction = max(direction_counts.items(), key=lambda x: x[1])
            recommendations.append(f"📊 Преобладающее направление: {dominant_direction[0]} ({dominant_direction[1]} сигналов)")
        
        return recommendations

    def _generate_group_recommendations(self, signals: List[ImprovedSignal], group_type: str) -> List[str]:
        """Генерация рекомендаций для группы сигналов"""
        recommendations = []
        
        if group_type == "strong_consensus":
            recommendations.append("✅ Сильный консенсус - высокая вероятность успеха")
            recommendations.append("💡 Рекомендуется увеличить размер позиции")
        elif group_type == "moderate_consensus":
            recommendations.append("⚠️ Умеренный консенсус - стандартный размер позиции")
        
        # Анализ цен
        avg_entry = sum(s.entry_price for s in signals) / len(signals)
        price_variance = sum((s.entry_price - avg_entry) ** 2 for s in signals) / len(signals)
        
        if price_variance < 0.01:  # Низкая дисперсия цен
            recommendations.append("🎯 Цены входа согласованы - четкий уровень входа")
        else:
            recommendations.append("📊 Разброс цен входа - используйте среднюю цену")
        
        # Анализ уверенности
        avg_confidence = sum(s.real_confidence for s in signals) / len(signals)
        if avg_confidence > 0.8:
            recommendations.append("🚀 Высокая средняя уверенность группы")
        elif avg_confidence < 0.5:
            recommendations.append("⚠️ Низкая уверенность группы - осторожность")
        
        return recommendations

    def save_prioritization_results(self, result: PrioritizationResult, filename: str = "prioritized_signals.json"):
        """Сохранение результатов приоритизации"""
        try:
            # Подготовка данных для сериализации
            serializable_result = {
                'prioritized_signals': [
                    {
                        'signal': asdict(p.signal),
                        'priority_score': p.priority_score,
                        'priority_level': p.priority_level.value,
                        'ranking_factors': p.ranking_factors,
                        'duplicate_info': p.duplicate_info,
                        'group_id': p.group_id,
                        'recommendations': p.recommendations
                    }
                    for p in result.prioritized_signals
                ],
                'signal_groups': [
                    {
                        'group_id': g.group_id,
                        'signals': [asdict(s) for s in g.signals],
                        'primary_signal': asdict(g.primary_signal),
                        'group_score': g.group_score,
                        'group_type': g.group_type,
                        'common_features': g.common_features,
                        'recommendations': g.recommendations
                    }
                    for g in result.signal_groups
                ],
                'statistics': {
                    'duplicates_removed': result.duplicates_removed,
                    'total_signals_processed': result.total_signals_processed,
                    'priority_distribution': result.priority_distribution,
                    'recommendations_summary': result.recommendations_summary
                },
                'timestamp': datetime.now().isoformat()
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(serializable_result, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Результаты приоритизации сохранены в {filename}")
            
        except Exception as e:
            logger.error(f"Ошибка сохранения результатов приоритизации: {e}")

def main():
    """Тестовая функция"""
    logging.basicConfig(level=logging.INFO)
    
    # Создаем тестовые сигналы
    test_signals = [
        ImprovedSignal(
            id="1", asset="BTC", direction=SignalDirection.LONG,
            entry_price=45000, target_price=48000, stop_loss=44000,
            leverage=2, timeframe="4h", channel="binance_killers",
            message_id="123", original_text="BTC LONG 45000", cleaned_text="BTC LONG 45000",
            timestamp=datetime.now(), extraction_time=datetime.now(),
            signal_quality=SignalQuality.GOOD, real_confidence=0.8, calculated_confidence=0.75,
            bybit_available=True, is_valid=True, validation_errors=[],
            risk_reward_ratio=2.5, potential_profit=3000, potential_loss=1000
        ),
        ImprovedSignal(
            id="2", asset="BTC", direction=SignalDirection.LONG,
            entry_price=45100, target_price=48500, stop_loss=44100,
            leverage=3, timeframe="4h", channel="crypto_signals",
            message_id="124", original_text="BTC LONG 45100", cleaned_text="BTC LONG 45100",
            timestamp=datetime.now(), extraction_time=datetime.now(),
            signal_quality=SignalQuality.EXCELLENT, real_confidence=0.9, calculated_confidence=0.85,
            bybit_available=True, is_valid=True, validation_errors=[],
            risk_reward_ratio=3.0, potential_profit=3400, potential_loss=1000
        ),
        ImprovedSignal(
            id="3", asset="ETH", direction=SignalDirection.SHORT,
            entry_price=3200, target_price=3000, stop_loss=3300,
            leverage=2, timeframe="1h", channel="trading_signals",
            message_id="125", original_text="ETH SHORT 3200", cleaned_text="ETH SHORT 3200",
            timestamp=datetime.now(), extraction_time=datetime.now(),
            signal_quality=SignalQuality.AVERAGE, real_confidence=0.6, calculated_confidence=0.55,
            bybit_available=True, is_valid=True, validation_errors=[],
            risk_reward_ratio=2.0, potential_profit=200, potential_loss=100
        )
    ]
    
    # Создаем систему приоритизации
    prioritization_system = SignalPrioritizationSystem()
    
    # Приоритизируем сигналы
    result = prioritization_system.prioritize_signals(test_signals)
    
    # Сохраняем результаты
    prioritization_system.save_prioritization_results(result)
    
    # Выводим статистику
    print(f"\n=== Результаты приоритизации ===")
    print(f"Обработано сигналов: {result.total_signals_processed}")
    print(f"Удалено дубликатов: {result.duplicates_removed}")
    print(f"Распределение приоритетов: {result.priority_distribution}")
    print(f"Создано групп: {len(result.signal_groups)}")
    
    print(f"\n=== Рекомендации ===")
    for rec in result.recommendations_summary:
        print(f"• {rec}")
    
    print(f"\n=== Топ сигналы ===")
    for i, priority_signal in enumerate(result.prioritized_signals[:3]):
        signal = priority_signal.signal
        print(f"{i+1}. {signal.asset} {signal.direction.value} @ {signal.entry_price}")
        print(f"   Приоритет: {priority_signal.priority_level.value} ({priority_signal.priority_score:.2f})")
        print(f"   Источник: {signal.channel}")
        print()

if __name__ == "__main__":
    main()
