"""
Integrated Signal Processor - Интегрированный процессор сигналов
Объединяет все компоненты: парсинг, валидацию, анализ качества и отслеживание
"""

import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from improved_signal_parser import ImprovedSignal, ImprovedSignalExtractor
from enhanced_validator import EnhancedSignalValidator
from signal_quality_analyzer import SignalQualityAnalyzer, QualityScore
from signal_tracker import SignalTracker
from real_telegram_parser import RealTelegramParser

logger = logging.getLogger(__name__)

class IntegratedSignalProcessor:
    """Интегрированный процессор сигналов"""
    
    def __init__(self):
        self.extractor = ImprovedSignalExtractor()
        self.validator = EnhancedSignalValidator()
        self.quality_analyzer = SignalQualityAnalyzer()
        self.signal_tracker = SignalTracker()
        self.telegram_parser = RealTelegramParser()
        
        # Настройки обработки
        self.min_quality_threshold = QualityScore.BASIC
        self.save_to_database = True
        self.enable_quality_filtering = True
    
    def process_telegram_channels(self, channels: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """Обрабатывает Telegram каналы с полной интеграцией"""
        try:
            # Парсим сигналы из Telegram
            telegram_result = self.telegram_parser.parse_channels()
            
            if not telegram_result.get('success'):
                return {
                    'success': False,
                    'error': 'Failed to parse Telegram channels',
                    'details': telegram_result.get('error', 'Unknown error')
                }
            
            raw_signals = telegram_result.get('signals', [])
            processed_signals = []
            
                        # Обрабатываем каждый сигнал
            for signal_data in raw_signals:
                try:
                    # Создаем объект сигнала
                    from improved_signal_parser import SignalDirection, SignalQuality
                    
                    # Преобразуем строковые значения в enum
                    direction = SignalDirection(signal_data['direction']) if isinstance(signal_data['direction'], str) else signal_data['direction']
                    signal_quality = SignalQuality(signal_data['signal_quality']) if isinstance(signal_data['signal_quality'], str) else signal_data['signal_quality']
                    
                    signal = ImprovedSignal(
                        id=signal_data['id'],
                        asset=signal_data['asset'],
                        direction=direction,
                        entry_price=signal_data['entry_price'],
                        target_price=signal_data['target_price'],
                        stop_loss=signal_data['stop_loss'],
                        leverage=signal_data['leverage'],
                        timeframe=signal_data['timeframe'],
                        channel=signal_data['channel'],
                        message_id=signal_data['message_id'],
                        original_text=signal_data['original_text'],
                        cleaned_text=signal_data['cleaned_text'],
                        timestamp=signal_data['timestamp'],
                        extraction_time=signal_data['extraction_time'],
                        signal_quality=signal_quality,
                        real_confidence=signal_data['real_confidence'],
                        calculated_confidence=signal_data['calculated_confidence'],
                        bybit_available=signal_data['bybit_available'],
                        is_valid=signal_data['is_valid'],
                        validation_errors=signal_data['validation_errors'],
                        risk_reward_ratio=signal_data['risk_reward_ratio'],
                        potential_profit=signal_data['potential_profit'],
                        potential_loss=signal_data['potential_loss']
                    )
                    
                    # Валидируем сигнал
                    validation_results = self.validator.validate_signal(signal)
                    signal.validation_errors = [str(result) for result in validation_results]
                    signal.is_valid = all(result.level != 'CRITICAL' for result in validation_results)
                    
                    # Анализируем качество
                    quality_metrics, risk_reward = self.quality_analyzer.analyze_signal_quality(signal)
                    
                    # Обновляем сигнал с результатами анализа
                    signal.signal_quality = quality_metrics.quality_level
                    signal.real_confidence = quality_metrics.overall_score
                    signal.risk_reward_ratio = risk_reward.risk_reward_ratio
                    signal.potential_profit = risk_reward.potential_profit
                    signal.potential_loss = risk_reward.potential_loss
                    
                    # Сохраняем в базу данных
                    if self.save_to_database:
                        self.signal_tracker.add_signal(signal)
                    
                    # Добавляем к обработанным сигналам
                    processed_signals.append({
                        'signal': signal,
                        'quality_metrics': quality_metrics,
                        'risk_reward': risk_reward,
                        'validation_results': validation_results
                    })
                    
                except Exception as e:
                    logger.error(f"Error processing signal {signal_data.get('id', 'unknown')}: {e}")
                    continue
            
            # Фильтруем по качеству если включено
            if self.enable_quality_filtering:
                filtered_signals = self.quality_analyzer.filter_signals_by_quality(
                    [p['signal'] for p in processed_signals], 
                    self.min_quality_threshold
                )
                processed_signals = [p for p in processed_signals if p['signal'] in filtered_signals]
            
            # Получаем сводку по качеству
            quality_summary = self.quality_analyzer.get_quality_summary([p['signal'] for p in processed_signals])
            
            # Получаем статистику каналов
            channel_stats = self.signal_tracker.get_all_channels_stats()
            
            return {
                'success': True,
                'total_raw_signals': len(raw_signals),
                'total_processed_signals': len(processed_signals),
                'signals': [
                    {
                        'id': p['signal'].id,
                        'asset': p['signal'].asset,
                        'direction': p['signal'].direction.value,
                        'entry_price': p['signal'].entry_price,
                        'target_price': p['signal'].target_price,
                        'stop_loss': p['signal'].stop_loss,
                        'leverage': p['signal'].leverage,
                        'timeframe': p['signal'].timeframe,
                        'channel': p['signal'].channel,
                        'signal_quality': p['signal'].signal_quality.value,
                        'real_confidence': p['signal'].real_confidence,
                        'risk_reward_ratio': p['signal'].risk_reward_ratio,
                        'potential_profit': p['signal'].potential_profit,
                        'potential_loss': p['signal'].potential_loss,
                        'bybit_available': p['signal'].bybit_available,
                        'is_valid': p['signal'].is_valid,
                        'validation_errors': p['signal'].validation_errors,
                        'quality_metrics': {
                            'overall_score': p['quality_metrics'].overall_score,
                            'quality_level': p['quality_metrics'].quality_level.value,
                            'risk_reward_score': p['quality_metrics'].risk_reward_score,
                            'technical_score': p['quality_metrics'].technical_score,
                            'confidence_score': p['quality_metrics'].confidence_score,
                            'reliability_score': p['quality_metrics'].reliability_score,
                            'recommendations': p['quality_metrics'].recommendations
                        },
                        'risk_reward_analysis': {
                            'risk_reward_ratio': p['risk_reward'].risk_reward_ratio,
                            'potential_profit': p['risk_reward'].potential_profit,
                            'potential_loss': p['risk_reward'].potential_loss,
                            'profit_percent': p['risk_reward'].profit_percent,
                            'loss_percent': p['risk_reward'].loss_percent,
                            'risk_level': p['risk_reward'].risk_level,
                            'reward_level': p['risk_reward'].reward_level
                        }
                    }
                    for p in processed_signals
                ],
                'quality_summary': quality_summary,
                'channel_stats': [
                    {
                        'channel': stats.channel,
                        'total_signals': stats.total_signals,
                        'successful_signals': stats.successful_signals,
                        'failed_signals': stats.failed_signals,
                        'success_rate': stats.success_rate,
                        'avg_profit_percent': stats.avg_profit_percent,
                        'avg_loss_percent': stats.avg_loss_percent,
                        'total_profit': stats.total_profit,
                        'total_loss': stats.total_loss,
                        'net_profit': stats.net_profit,
                        'best_signal_profit': stats.best_signal_profit,
                        'worst_signal_loss': stats.worst_signal_loss,
                        'avg_execution_time': stats.avg_execution_time,
                        'last_updated': stats.last_updated
                    }
                    for stats in channel_stats
                ],
                'processing_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in process_telegram_channels: {e}")
            return {
                'success': False,
                'error': str(e),
                'processing_timestamp': datetime.now().isoformat()
            }
    
    def process_text_signals(self, text_signals: List[str], channel: str = "manual_input") -> Dict[str, Any]:
        """Обрабатывает текстовые сигналы"""
        processed_signals = []
        
        for i, text in enumerate(text_signals):
            try:
                # Извлекаем сигнал из текста
                extracted_signals = self.extractor.extract_signals_from_text(text, channel, f"manual_{i}")
                
                for signal in extracted_signals:
                    # Устанавливаем канал
                    signal.channel = channel
                    signal.message_id = f"manual_{i}_{signal.id}"
                    
                    # Валидируем сигнал
                    validation_results = self.validator.validate_signal(signal)
                    signal.validation_errors = [str(result) for result in validation_results]
                    signal.is_valid = all(result.level != 'CRITICAL' for result in validation_results)
                    
                    # Анализируем качество
                    quality_metrics, risk_reward = self.quality_analyzer.analyze_signal_quality(signal)
                    
                    # Обновляем сигнал
                    signal.signal_quality = quality_metrics.quality_level
                    signal.real_confidence = quality_metrics.overall_score
                    signal.risk_reward_ratio = risk_reward.risk_reward_ratio
                    signal.potential_profit = risk_reward.potential_profit
                    signal.potential_loss = risk_reward.potential_loss
                    
                    # Сохраняем в базу данных
                    if self.save_to_database:
                        self.signal_tracker.add_signal(signal)
                    
                    processed_signals.append({
                        'signal': signal,
                        'quality_metrics': quality_metrics,
                        'risk_reward': risk_reward,
                        'validation_results': validation_results
                    })
                    
            except Exception as e:
                logger.error(f"Error processing text signal {i}: {e}")
                continue
        
        # Фильтруем по качеству
        if self.enable_quality_filtering:
            filtered_signals = self.quality_analyzer.filter_signals_by_quality(
                [p['signal'] for p in processed_signals], 
                self.min_quality_threshold
            )
            processed_signals = [p for p in processed_signals if p['signal'] in filtered_signals]
        
        return {
            'success': True,
            'total_input_texts': len(text_signals),
            'total_processed_signals': len(processed_signals),
            'signals': [
                {
                    'id': p['signal'].id,
                    'asset': p['signal'].asset,
                    'direction': p['signal'].direction.value,
                    'entry_price': p['signal'].entry_price,
                    'target_price': p['signal'].target_price,
                    'stop_loss': p['signal'].stop_loss,
                    'leverage': p['signal'].leverage,
                    'timeframe': p['signal'].timeframe,
                    'channel': p['signal'].channel,
                    'signal_quality': p['signal'].signal_quality.value,
                    'real_confidence': p['signal'].real_confidence,
                    'risk_reward_ratio': p['signal'].risk_reward_ratio,
                    'potential_profit': p['signal'].potential_profit,
                    'potential_loss': p['signal'].potential_loss,
                    'bybit_available': p['signal'].bybit_available,
                    'is_valid': p['signal'].is_valid,
                    'validation_errors': p['signal'].validation_errors,
                    'quality_metrics': {
                        'overall_score': p['quality_metrics'].overall_score,
                        'quality_level': p['quality_metrics'].quality_level.value,
                        'risk_reward_score': p['quality_metrics'].risk_reward_score,
                        'technical_score': p['quality_metrics'].technical_score,
                        'confidence_score': p['quality_metrics'].confidence_score,
                        'reliability_score': p['quality_metrics'].reliability_score,
                        'recommendations': p['quality_metrics'].recommendations
                    },
                    'risk_reward_analysis': {
                        'risk_reward_ratio': p['risk_reward'].risk_reward_ratio,
                        'potential_profit': p['risk_reward'].potential_profit,
                        'potential_loss': p['risk_reward'].potential_loss,
                        'profit_percent': p['risk_reward'].profit_percent,
                        'loss_percent': p['risk_reward'].loss_percent,
                        'risk_level': p['risk_reward'].risk_level,
                        'reward_level': p['risk_reward'].reward_level
                    }
                }
                for p in processed_signals
            ],
            'processing_timestamp': datetime.now().isoformat()
        }
    
    def get_signals_summary(self, hours_back: int = 24) -> Dict[str, Any]:
        """Получает сводку по сигналам за последние N часов"""
        try:
            # Получаем сигналы без результатов
            pending_signals = self.signal_tracker.get_signals_without_results(hours_back)
            
            # Получаем статистику каналов
            channel_stats = self.signal_tracker.get_all_channels_stats()
            
            # Анализируем качество сигналов
            quality_summary = self.quality_analyzer.get_quality_summary([])  # Пока пустой, можно расширить
            
            return {
                'success': True,
                'pending_signals_count': len(pending_signals),
                'channel_stats': [
                    {
                        'channel': stats.channel,
                        'total_signals': stats.total_signals,
                        'successful_signals': stats.successful_signals,
                        'failed_signals': stats.failed_signals,
                        'success_rate': stats.success_rate,
                        'avg_profit_percent': stats.avg_profit_percent,
                        'avg_loss_percent': stats.avg_loss_percent,
                        'total_profit': stats.total_profit,
                        'total_loss': stats.total_loss,
                        'net_profit': stats.net_profit,
                        'best_signal_profit': stats.best_signal_profit,
                        'worst_signal_loss': stats.worst_signal_loss,
                        'avg_execution_time': stats.avg_execution_time,
                        'last_updated': stats.last_updated
                    }
                    for stats in channel_stats
                ],
                'quality_summary': quality_summary,
                'summary_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting signals summary: {e}")
            return {
                'success': False,
                'error': str(e),
                'summary_timestamp': datetime.now().isoformat()
            }
    
    def update_signal_result(self, signal_id: str, result_data: Dict[str, Any]) -> Dict[str, Any]:
        """Обновляет результат исполнения сигнала"""
        try:
            from signal_tracker import SignalResult
            
            result = SignalResult(
                signal_id=signal_id,
                channel=result_data['channel'],
                asset=result_data['asset'],
                direction=result_data['direction'],
                entry_price=result_data['entry_price'],
                target_price=result_data.get('target_price'),
                stop_loss=result_data.get('stop_loss'),
                signal_timestamp=result_data['signal_timestamp'],
                execution_timestamp=result_data['execution_timestamp'],
                success=result_data['success'],
                profit_loss=result_data['profit_loss'],
                profit_loss_percent=result_data['profit_loss_percent'],
                execution_time_hours=result_data['execution_time_hours'],
                reached_target=result_data.get('reached_target', False),
                hit_stop_loss=result_data.get('hit_stop_loss', False),
                max_profit=result_data.get('max_profit', 0.0),
                max_loss=result_data.get('max_loss', 0.0),
                notes=result_data.get('notes', '')
            )
            
            self.signal_tracker.add_signal_result(result)
            
            return {
                'success': True,
                'message': f'Result for signal {signal_id} updated successfully',
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error updating signal result: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

def main():
    """Тестирование интегрированного процессора"""
    processor = IntegratedSignalProcessor()
    
    print("=== Тестирование интегрированного процессора сигналов ===")
    
    # Тестируем обработку текстовых сигналов
    test_texts = [
        "BTC LONG Entry: 50000 Target: 55000 Stop: 48000 Leverage: 10x",
        "ETH SHORT Entry: 3000 Target: 2800 Stop: 3200 Leverage: 5x"
    ]
    
    print("\n1. Обработка текстовых сигналов:")
    result = processor.process_text_signals(test_texts, "test_channel")
    
    if result['success']:
        print(f"✅ Обработано {result['total_processed_signals']} сигналов из {result['total_input_texts']} текстов")
        for signal in result['signals']:
            print(f"  - {signal['asset']} {signal['direction']}: {signal['signal_quality']} (скор: {signal['real_confidence']:.1f})")
    else:
        print(f"❌ Ошибка: {result['error']}")
    
    # Тестируем получение сводки
    print("\n2. Получение сводки:")
    summary = processor.get_signals_summary()
    
    if summary['success']:
        print(f"✅ Сводка получена: {summary['pending_signals_count']} ожидающих сигналов")
        print(f"  Каналов: {len(summary['channel_stats'])}")
    else:
        print(f"❌ Ошибка: {summary['error']}")
    
    # Тестируем обработку Telegram каналов
    print("\n3. Обработка Telegram каналов:")
    telegram_result = processor.process_telegram_channels()
    
    if telegram_result['success']:
        print(f"✅ Telegram: {telegram_result['total_processed_signals']} сигналов из {telegram_result['total_raw_signals']}")
        for signal in telegram_result['signals'][:3]:  # Показываем первые 3
            print(f"  - {signal['asset']} {signal['direction']}: {signal['signal_quality']} (скор: {signal['real_confidence']:.1f})")
    else:
        print(f"❌ Ошибка Telegram: {telegram_result['error']}")

if __name__ == "__main__":
    main()
