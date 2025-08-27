import json
import logging
import time
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, asdict

from improved_signal_parser import ImprovedSignal, ImprovedSignalExtractor, SignalDirection, SignalQuality
from signal_prioritization_system import SignalPrioritizationSystem, PrioritizationResult, SignalPriority, SignalGroup
from simple_multi_platform_parser import SimpleMultiPlatformParser

logger = logging.getLogger(__name__)

@dataclass
class IntegratedPrioritizationResult:
    raw_signals: List[ImprovedSignal]
    enhanced_signals: List[ImprovedSignal]
    prioritized_signals: List[SignalPriority]
    signal_groups: List[SignalGroup]
    processing_stats: Dict[str, Any]
    recommendations: List[str]
    execution_time: float

class IntegratedPrioritizationProcessor:
    def __init__(self):
        self.multi_platform_parser = SimpleMultiPlatformParser()
        self.prioritization_system = SignalPrioritizationSystem()
        
        logger.info("Интегрированный процессор приоритизации инициализирован")

    def process_and_prioritize_signals(self, 
                                     telegram_channels: Optional[List[Dict]] = None,
                                     include_reddit: bool = True,
                                     include_tradingview: bool = True) -> IntegratedPrioritizationResult:
        """Полный цикл обработки и приоритизации сигналов"""
        start_time = time.time()
        
        logger.info("Начинаем полный цикл обработки и приоритизации сигналов")
        
        # Шаг 1: Сбор сигналов со всех платформ
        logger.info("Шаг 1: Сбор сигналов со всех платформ")
        raw_signals = self._collect_signals_from_all_platforms(
            telegram_channels, include_reddit, include_tradingview
        )
        
        if not raw_signals:
            logger.warning("Не найдено сигналов для обработки")
            return self._create_empty_result(start_time)
        
        logger.info(f"Собрано {len(raw_signals)} сырых сигналов")
        
        # Шаг 2: Улучшение качества сигналов (упрощенная версия)
        logger.info("Шаг 2: Улучшение качества сигналов")
        enhanced_signals = self._enhance_signal_quality(raw_signals)
        logger.info(f"Улучшено {len(enhanced_signals)} сигналов")
        
        # Шаг 3: Приоритизация сигналов
        logger.info("Шаг 3: Приоритизация сигналов")
        prioritization_result = self.prioritization_system.prioritize_signals(enhanced_signals)
        logger.info(f"Приоритизировано {len(prioritization_result.prioritized_signals)} сигналов")
        
        # Шаг 4: Генерация рекомендаций
        logger.info("Шаг 4: Генерация рекомендаций")
        recommendations = self._generate_integrated_recommendations(
            raw_signals, enhanced_signals, prioritization_result
        )
        
        # Шаг 5: Сбор статистики
        processing_stats = self._collect_processing_statistics(
            raw_signals, enhanced_signals, prioritization_result
        )
        
        execution_time = time.time() - start_time
        
        result = IntegratedPrioritizationResult(
            raw_signals=raw_signals,
            enhanced_signals=enhanced_signals,
            prioritized_signals=prioritization_result.prioritized_signals,
            signal_groups=prioritization_result.signal_groups,
            processing_stats=processing_stats,
            recommendations=recommendations,
            execution_time=execution_time
        )
        
        logger.info(f"Полный цикл обработки завершен за {execution_time:.2f} секунд")
        
        return result

    def _collect_signals_from_all_platforms(self, 
                                          telegram_channels: Optional[List[Dict]] = None,
                                          include_reddit: bool = True,
                                          include_tradingview: bool = True) -> List[ImprovedSignal]:
        """Сбор сигналов со всех платформ"""
        all_signals = []
        
        try:
            # Сбор с мультиплатформенного парсера
            multi_platform_result = self.multi_platform_parser.parse_all_platforms(
                telegram_channels=telegram_channels,
                include_reddit=include_reddit,
                include_tradingview=include_tradingview
            )
            
            # Извлекаем сигналы из результатов
            for platform, signals in multi_platform_result.items():
                if isinstance(signals, list):
                    all_signals.extend(signals)
                elif isinstance(signals, dict) and 'signals' in signals:
                    all_signals.extend(signals['signals'])
            
            logger.info(f"Собрано сигналов с платформ: {len(all_signals)}")
            
        except Exception as e:
            logger.error(f"Ошибка при сборе сигналов с платформ: {e}")
        
        return all_signals

    def _enhance_signal_quality(self, signals: List[ImprovedSignal]) -> List[ImprovedSignal]:
        """Улучшение качества сигналов (упрощенная версия)"""
        enhanced_signals = []
        
        for signal in signals:
            try:
                # Проверяем, является ли сигнал словарем или объектом
                if isinstance(signal, dict):
                    # Если это словарь, создаем объект ImprovedSignal
                    enhanced_signal = ImprovedSignal(
                        id=signal.get('id', 'unknown'),
                        asset=signal.get('asset', ''),
                        direction=SignalDirection(signal.get('direction', 'LONG')),
                        entry_price=signal.get('entry_price', 0.0),
                        target_price=signal.get('target_price', 0.0),
                        stop_loss=signal.get('stop_loss', 0.0),
                        leverage=signal.get('leverage', 1),
                        timeframe=signal.get('timeframe', '4H'),
                        signal_quality=SignalQuality(signal.get('signal_quality', 'MEDIUM')),
                        real_confidence=signal.get('real_confidence', 50.0),
                        calculated_confidence=signal.get('calculated_confidence', 50.0),
                        channel=signal.get('channel', ''),
                        message_id=signal.get('message_id', ''),
                        original_text=signal.get('original_text', ''),
                        cleaned_text=signal.get('cleaned_text', ''),
                        signal_type=signal.get('signal_type', 'structured'),
                        timestamp=signal.get('timestamp', datetime.now().isoformat()),
                        extraction_time=signal.get('extraction_time', datetime.now().isoformat()),
                        bybit_available=signal.get('bybit_available', False),
                        is_valid=signal.get('is_valid', True),
                        validation_errors=signal.get('validation_errors', []),
                        risk_reward_ratio=signal.get('risk_reward_ratio', 0.0),
                        potential_profit=signal.get('potential_profit', 0.0),
                        potential_loss=signal.get('potential_loss', 0.0)
                    )
                else:
                    # Если это уже объект ImprovedSignal
                    enhanced_signal = signal
                
                # Простое улучшение - пересчитываем качество и уверенность
                enhanced_signal.calculate_quality()
                enhanced_signal.calculate_confidence()
                enhanced_signal.calculate_risk_reward()
                
                enhanced_signals.append(enhanced_signal)
                
            except Exception as e:
                logger.error(f"Ошибка при улучшении сигнала: {e}")
                # Добавляем исходный сигнал, если улучшение не удалось
                if isinstance(signal, dict):
                    # Создаем базовый объект из словаря
                    try:
                        basic_signal = ImprovedSignal(
                            id=signal.get('id', 'unknown'),
                            asset=signal.get('asset', ''),
                            direction=SignalDirection(signal.get('direction', 'LONG')),
                            entry_price=signal.get('entry_price', 0.0),
                            target_price=signal.get('target_price', 0.0),
                            stop_loss=signal.get('stop_loss', 0.0),
                            leverage=signal.get('leverage', 1),
                            timeframe=signal.get('timeframe', '4H'),
                            signal_quality=SignalQuality(signal.get('signal_quality', 'MEDIUM')),
                            real_confidence=signal.get('real_confidence', 50.0),
                            calculated_confidence=signal.get('calculated_confidence', 50.0),
                            channel=signal.get('channel', ''),
                            message_id=signal.get('message_id', ''),
                            original_text=signal.get('original_text', ''),
                            cleaned_text=signal.get('cleaned_text', ''),
                            signal_type=signal.get('signal_type', 'structured'),
                            timestamp=signal.get('timestamp', datetime.now().isoformat()),
                            extraction_time=signal.get('extraction_time', datetime.now().isoformat()),
                            bybit_available=signal.get('bybit_available', False),
                            is_valid=signal.get('is_valid', True),
                            validation_errors=signal.get('validation_errors', []),
                            risk_reward_ratio=signal.get('risk_reward_ratio', 0.0),
                            potential_profit=signal.get('potential_profit', 0.0),
                            potential_loss=signal.get('potential_loss', 0.0)
                        )
                        enhanced_signals.append(basic_signal)
                    except Exception as e2:
                        logger.error(f"Не удалось создать базовый сигнал: {e2}")
                else:
                    enhanced_signals.append(signal)
        
        return enhanced_signals

    def _generate_integrated_recommendations(self, 
                                           raw_signals: List[ImprovedSignal],
                                           enhanced_signals: List[ImprovedSignal],
                                           prioritization_result: PrioritizationResult) -> List[str]:
        """Генерация интегрированных рекомендаций"""
        recommendations = []
        
        # Добавляем рекомендации от системы приоритизации
        recommendations.extend(prioritization_result.recommendations_summary)
        
        # Анализ улучшения качества
        quality_improvements = 0
        for raw, enhanced in zip(raw_signals, enhanced_signals):
            # Получаем значения уверенности, учитывая возможные типы данных
            def get_confidence(signal):
                if hasattr(signal, 'real_confidence'):
                    return signal.real_confidence
                elif isinstance(signal, dict):
                    return signal.get('real_confidence', 0)
                return 0
            
            raw_confidence = get_confidence(raw)
            enhanced_confidence = get_confidence(enhanced)
            
            if enhanced_confidence > raw_confidence:
                quality_improvements += 1
        
        if quality_improvements > 0:
            improvement_rate = quality_improvements / len(raw_signals) * 100
            recommendations.append(f"📈 Улучшено качество {improvement_rate:.1f}% сигналов")
        
        # Анализ источников
        source_counts = {}
        for signal in enhanced_signals:
            if hasattr(signal, 'channel'):
                source = signal.channel
            elif isinstance(signal, dict):
                source = signal.get('channel', 'Unknown')
            else:
                source = 'Unknown'
            source_counts[source] = source_counts.get(source, 0) + 1
        
        top_sources = sorted(source_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        if top_sources:
            recommendations.append(f"📊 Топ источники: {', '.join(f'{source} ({count})' for source, count in top_sources)}")
        
        # Анализ временных фреймов
        timeframe_counts = {}
        for signal in enhanced_signals:
            if hasattr(signal, 'timeframe'):
                tf = signal.timeframe
            elif isinstance(signal, dict):
                tf = signal.get('timeframe', 'Unknown')
            else:
                tf = 'Unknown'
            timeframe_counts[tf] = timeframe_counts.get(tf, 0) + 1
        
        if timeframe_counts:
            dominant_tf = max(timeframe_counts.items(), key=lambda x: x[1])
            recommendations.append(f"⏰ Преобладающий таймфрейм: {dominant_tf[0]} ({dominant_tf[1]} сигналов)")
        
        # Общие рекомендации по торговле
        if len(enhanced_signals) > 10:
            recommendations.append("💡 Много сигналов - рекомендуется избирательный подход")
        elif len(enhanced_signals) < 3:
            recommendations.append("⚠️ Мало сигналов - дождитесь большего количества")
        
        return recommendations

    def _collect_processing_statistics(self, 
                                     raw_signals: List[ImprovedSignal],
                                     enhanced_signals: List[ImprovedSignal],
                                     prioritization_result: PrioritizationResult) -> Dict[str, Any]:
        """Сбор статистики обработки"""
        stats = {
            'raw_signals_count': len(raw_signals),
            'enhanced_signals_count': len(enhanced_signals),
            'prioritized_signals_count': len(prioritization_result.prioritized_signals),
            'duplicates_removed': prioritization_result.duplicates_removed,
            'signal_groups_count': len(prioritization_result.signal_groups),
            'priority_distribution': prioritization_result.priority_distribution,
            'processing_timestamp': datetime.now().isoformat()
        }
        
        # Статистика по источникам
        source_stats = {}
        for signal in enhanced_signals:
            if hasattr(signal, 'channel'):
                source = signal.channel
            elif isinstance(signal, dict):
                source = signal.get('channel', 'Unknown')
            else:
                source = 'Unknown'
                
            if hasattr(signal, 'real_confidence'):
                confidence = signal.real_confidence
            elif isinstance(signal, dict):
                confidence = signal.get('real_confidence', 0)
            else:
                confidence = 0
                
            if source not in source_stats:
                source_stats[source] = {'count': 0, 'avg_confidence': 0, 'total_confidence': 0}
            source_stats[source]['count'] += 1
            source_stats[source]['total_confidence'] += confidence
        
        for source in source_stats:
            source_stats[source]['avg_confidence'] = (
                source_stats[source]['total_confidence'] / source_stats[source]['count']
            )
        
        stats['source_statistics'] = source_stats
        
        # Статистика по активам
        asset_stats = {}
        for signal in enhanced_signals:
            if hasattr(signal, 'asset'):
                asset = signal.asset
            elif isinstance(signal, dict):
                asset = signal.get('asset', 'Unknown')
            else:
                asset = 'Unknown'
                
            if hasattr(signal, 'direction'):
                direction = signal.direction
            elif isinstance(signal, dict):
                direction = signal.get('direction', 'UNKNOWN')
            else:
                direction = 'UNKNOWN'
                
            if asset not in asset_stats:
                asset_stats[asset] = {'count': 0, 'long_count': 0, 'short_count': 0}
            asset_stats[asset]['count'] += 1
            if direction == SignalDirection.LONG:
                asset_stats[asset]['long_count'] += 1
            else:
                asset_stats[asset]['short_count'] += 1
        
        stats['asset_statistics'] = asset_stats
        
        return stats

    def _create_empty_result(self, start_time: float) -> IntegratedPrioritizationResult:
        """Создание пустого результата"""
        execution_time = time.time() - start_time
        
        return IntegratedPrioritizationResult(
            raw_signals=[],
            enhanced_signals=[],
            prioritized_signals=[],
            signal_groups=[],
            processing_stats={
                'raw_signals_count': 0,
                'enhanced_signals_count': 0,
                'prioritized_signals_count': 0,
                'duplicates_removed': 0,
                'signal_groups_count': 0,
                'priority_distribution': {},
                'processing_timestamp': datetime.now().isoformat()
            },
            recommendations=["Нет сигналов для обработки"],
            execution_time=execution_time
        )

    def save_integrated_results(self, result: IntegratedPrioritizationResult, 
                              filename: str = "integrated_prioritization_results.json"):
        """Сохранение интегрированных результатов"""
        try:
            # Подготовка данных для сериализации
            serializable_result = {
                'raw_signals': [asdict(s) for s in result.raw_signals],
                'enhanced_signals': [asdict(s) for s in result.enhanced_signals],
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
                'processing_stats': result.processing_stats,
                'recommendations': result.recommendations,
                'execution_time': result.execution_time,
                'timestamp': datetime.now().isoformat()
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(serializable_result, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Интегрированные результаты сохранены в {filename}")
            
        except Exception as e:
            logger.error(f"Ошибка сохранения интегрированных результатов: {e}")

    def get_top_signals(self, result: IntegratedPrioritizationResult, 
                       limit: int = 10, 
                       priority_level: Optional[str] = None) -> List[SignalPriority]:
        """Получение топ сигналов с фильтрацией"""
        signals = result.prioritized_signals
        
        # Фильтрация по уровню приоритета
        if priority_level:
            signals = [s for s in signals if s.priority_level.value == priority_level]
        
        # Сортировка по приоритету и ограничение
        signals.sort(key=lambda x: x.priority_score, reverse=True)
        return signals[:limit]

    def get_signal_groups_summary(self, result: IntegratedPrioritizationResult) -> Dict[str, Any]:
        """Получение сводки по группам сигналов"""
        groups = result.signal_groups
        
        summary = {
            'total_groups': len(groups),
            'strong_consensus_groups': len([g for g in groups if g.group_type == "strong_consensus"]),
            'moderate_consensus_groups': len([g for g in groups if g.group_type == "moderate_consensus"]),
            'group_types_distribution': {},
            'top_groups': []
        }
        
        # Распределение типов групп
        group_types = [g.group_type for g in groups]
        for group_type in set(group_types):
            summary['group_types_distribution'][group_type] = group_types.count(group_type)
        
        # Топ группы по счету
        top_groups = sorted(groups, key=lambda x: x.group_score, reverse=True)[:5]
        summary['top_groups'] = [
            {
                'group_id': g.group_id,
                'asset': g.common_features['asset'],
                'direction': g.common_features['direction'],
                'signal_count': g.common_features['signal_count'],
                'group_score': g.group_score,
                'group_type': g.group_type
            }
            for g in top_groups
        ]
        
        return summary

def main():
    """Тестовая функция"""
    logging.basicConfig(level=logging.INFO)
    
    # Создаем интегрированный процессор
    processor = IntegratedPrioritizationProcessor()
    
    # Запускаем полный цикл обработки
    result = processor.process_and_prioritize_signals()
    
    # Сохраняем результаты
    processor.save_integrated_results(result)
    
    # Выводим статистику
    print(f"\n=== Интегрированная обработка сигналов ===")
    print(f"Время выполнения: {result.execution_time:.2f} секунд")
    print(f"Сырых сигналов: {result.processing_stats['raw_signals_count']}")
    print(f"Улучшенных сигналов: {result.processing_stats['enhanced_signals_count']}")
    print(f"Приоритизированных сигналов: {result.processing_stats['prioritized_signals_count']}")
    print(f"Удалено дубликатов: {result.processing_stats['duplicates_removed']}")
    print(f"Создано групп: {result.processing_stats['signal_groups_count']}")
    
    print(f"\n=== Распределение приоритетов ===")
    for level, count in result.processing_stats['priority_distribution'].items():
        print(f"{level}: {count}")
    
    print(f"\n=== Рекомендации ===")
    for rec in result.recommendations:
        print(f"• {rec}")
    
    # Получаем топ сигналы
    top_signals = processor.get_top_signals(result, limit=5)
    print(f"\n=== Топ 5 сигналов ===")
    for i, priority_signal in enumerate(top_signals):
        signal = priority_signal.signal
        print(f"{i+1}. {signal.asset} {signal.direction.value} @ {signal.entry_price}")
        print(f"   Приоритет: {priority_signal.priority_level.value} ({priority_signal.priority_score:.2f})")
        print(f"   Источник: {signal.channel}")
        print()
    
    # Сводка по группам
    groups_summary = processor.get_signal_groups_summary(result)
    print(f"\n=== Сводка по группам ===")
    print(f"Всего групп: {groups_summary['total_groups']}")
    print(f"Сильный консенсус: {groups_summary['strong_consensus_groups']}")
    print(f"Умеренный консенсус: {groups_summary['moderate_consensus_groups']}")

if __name__ == "__main__":
    main()
