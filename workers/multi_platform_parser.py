"""
Multi-Platform Parser - Интегрированный парсер для всех платформ
Объединяет парсинг Telegram, Reddit, TradingView и других источников
"""

import json
import logging
import time
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed

from real_telegram_parser import RealTelegramParser
from reddit_parser import RedditParser
from tradingview_parser import TradingViewParser
from integrated_signal_processor import IntegratedSignalProcessor
from signal_quality_analyzer import SignalQualityAnalyzer, QualityScore

logger = logging.getLogger(__name__)

@dataclass
class PlatformResult:
    """Результат парсинга платформы"""
    platform: str
    success: bool
    total_signals: int
    filtered_signals: int
    processing_time: float
    error: Optional[str] = None
    signals: List[Any] = None

class MultiPlatformParser:
    """Интегрированный парсер для всех платформ"""
    
    def __init__(self):
        self.telegram_parser = RealTelegramParser()
        self.reddit_parser = RedditParser()
        self.tradingview_parser = TradingViewParser()
        self.signal_processor = IntegratedSignalProcessor()
        self.quality_analyzer = SignalQualityAnalyzer()
        
        # Настройки качества
        self.min_quality_threshold = QualityScore.BASIC
        self.enable_parallel_processing = True
        self.max_workers = 4
        
        # Статистика платформ
        self.platform_stats = {
            'telegram': {'total_signals': 0, 'success_rate': 0.0},
            'reddit': {'total_signals': 0, 'success_rate': 0.0},
            'tradingview': {'total_signals': 0, 'success_rate': 0.0}
        }
    
    def parse_telegram_platform(self) -> PlatformResult:
        """Парсит Telegram платформу"""
        start_time = time.time()
        
        try:
            logger.info("Starting Telegram platform parsing...")
            
            result = self.telegram_parser.parse_channels()
            
            if result['success']:
                signals = result.get('signals', [])
                filtered_signals = self._filter_signals_by_quality(signals)
                
                processing_time = time.time() - start_time
                
                return PlatformResult(
                    platform="telegram",
                    success=True,
                    total_signals=len(signals),
                    filtered_signals=len(filtered_signals),
                    processing_time=processing_time,
                    signals=filtered_signals
                )
            else:
                return PlatformResult(
                    platform="telegram",
                    success=False,
                    total_signals=0,
                    filtered_signals=0,
                    processing_time=time.time() - start_time,
                    error=result.get('error', 'Unknown error')
                )
                
        except Exception as e:
            logger.error(f"Error parsing Telegram platform: {e}")
            return PlatformResult(
                platform="telegram",
                success=False,
                total_signals=0,
                filtered_signals=0,
                processing_time=time.time() - start_time,
                error=str(e)
            )
    
    def parse_reddit_platform(self) -> PlatformResult:
        """Парсит Reddit платформу"""
        start_time = time.time()
        
        try:
            logger.info("Starting Reddit platform parsing...")
            
            result = self.reddit_parser.parse_all_subreddits()
            
            if result['success']:
                signals = result.get('all_signals', [])
                filtered_signals = self._filter_signals_by_quality(signals)
                
                processing_time = time.time() - start_time
                
                return PlatformResult(
                    platform="reddit",
                    success=True,
                    total_signals=len(signals),
                    filtered_signals=len(filtered_signals),
                    processing_time=processing_time,
                    signals=filtered_signals
                )
            else:
                return PlatformResult(
                    platform="reddit",
                    success=False,
                    total_signals=0,
                    filtered_signals=0,
                    processing_time=time.time() - start_time,
                    error=result.get('error', 'Unknown error')
                )
                
        except Exception as e:
            logger.error(f"Error parsing Reddit platform: {e}")
            return PlatformResult(
                platform="reddit",
                success=False,
                total_signals=0,
                filtered_signals=0,
                processing_time=time.time() - start_time,
                error=str(e)
            )
    
    def parse_tradingview_platform(self) -> PlatformResult:
        """Парсит TradingView платформу"""
        start_time = time.time()
        
        try:
            logger.info("Starting TradingView platform parsing...")
            
            # Парсим только популярные символы для экономии времени
            popular_symbols = ['BTCUSD', 'ETHUSD', 'ADAUSD', 'SOLUSD', 'DOTUSD']
            
            all_signals = []
            for symbol in popular_symbols:
                try:
                    result = self.tradingview_parser.parse_symbol(symbol)
                    if result['success']:
                        all_signals.extend(result.get('signals', []))
                    time.sleep(1)  # Пауза между запросами
                except Exception as e:
                    logger.error(f"Error parsing symbol {symbol}: {e}")
                    continue
            
            filtered_signals = self._filter_signals_by_quality(all_signals)
            processing_time = time.time() - start_time
            
            return PlatformResult(
                platform="tradingview",
                success=True,
                total_signals=len(all_signals),
                filtered_signals=len(filtered_signals),
                processing_time=processing_time,
                signals=filtered_signals
            )
                
        except Exception as e:
            logger.error(f"Error parsing TradingView platform: {e}")
            return PlatformResult(
                platform="tradingview",
                success=False,
                total_signals=0,
                filtered_signals=0,
                processing_time=time.time() - start_time,
                error=str(e)
            )
    
    def _filter_signals_by_quality(self, signals: List[Any]) -> List[Any]:
        """Фильтрует сигналы по качеству"""
        if not signals:
            return []
        
        # Конвертируем в ImprovedSignal если нужно
        improved_signals = []
        for signal in signals:
            if hasattr(signal, 'signal_quality'):
                improved_signals.append(signal)
            else:
                # Пытаемся создать ImprovedSignal из словаря
                try:
                    from improved_signal_parser import ImprovedSignal, SignalDirection, SignalQuality
                    
                    if isinstance(signal, dict):
                        direction = SignalDirection(signal['direction']) if isinstance(signal['direction'], str) else signal['direction']
                        signal_quality = SignalQuality(signal['signal_quality']) if isinstance(signal['signal_quality'], str) else signal['signal_quality']
                        
                        improved_signal = ImprovedSignal(
                            id=signal['id'],
                            asset=signal['asset'],
                            direction=direction,
                            entry_price=signal.get('entry_price'),
                            target_price=signal.get('target_price'),
                            stop_loss=signal.get('stop_loss'),
                            leverage=signal.get('leverage'),
                            timeframe=signal.get('timeframe'),
                            channel=signal.get('channel'),
                            message_id=signal.get('message_id'),
                            original_text=signal.get('original_text'),
                            cleaned_text=signal.get('cleaned_text'),
                            timestamp=signal.get('timestamp'),
                            extraction_time=signal.get('extraction_time'),
                            signal_quality=signal_quality,
                            real_confidence=signal.get('real_confidence'),
                            calculated_confidence=signal.get('calculated_confidence'),
                            bybit_available=signal.get('bybit_available', True),
                            is_valid=signal.get('is_valid', True),
                            validation_errors=signal.get('validation_errors', []),
                            risk_reward_ratio=signal.get('risk_reward_ratio'),
                            potential_profit=signal.get('potential_profit'),
                            potential_loss=signal.get('potential_loss')
                        )
                        improved_signals.append(improved_signal)
                except Exception as e:
                    logger.error(f"Error converting signal to ImprovedSignal: {e}")
                    continue
        
        # Фильтруем по качеству
        filtered_signals = self.quality_analyzer.filter_signals_by_quality(
            improved_signals, self.min_quality_threshold
        )
        
        return filtered_signals
    
    def parse_all_platforms_parallel(self) -> Dict[str, Any]:
        """Парсит все платформы параллельно"""
        start_time = time.time()
        
        logger.info("Starting multi-platform parsing...")
        
        if self.enable_parallel_processing:
            # Параллельный парсинг
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                future_to_platform = {
                    executor.submit(self.parse_telegram_platform): "telegram",
                    executor.submit(self.parse_reddit_platform): "reddit",
                    executor.submit(self.parse_tradingview_platform): "tradingview"
                }
                
                platform_results = []
                for future in as_completed(future_to_platform):
                    platform = future_to_platform[future]
                    try:
                        result = future.result()
                        platform_results.append(result)
                        logger.info(f"Completed parsing {platform}: {result.filtered_signals} signals")
                    except Exception as e:
                        logger.error(f"Error parsing {platform}: {e}")
                        platform_results.append(PlatformResult(
                            platform=platform,
                            success=False,
                            total_signals=0,
                            filtered_signals=0,
                            processing_time=0,
                            error=str(e)
                        ))
        else:
            # Последовательный парсинг
            platform_results = [
                self.parse_telegram_platform(),
                self.parse_reddit_platform(),
                self.parse_tradingview_platform()
            ]
        
        # Объединяем результаты
        all_signals = []
        total_processing_time = time.time() - start_time
        
        for result in platform_results:
            if result.success and result.signals:
                all_signals.extend(result.signals)
        
        # Дополнительная фильтрация и ранжирование
        final_signals = self._final_filter_and_rank(all_signals)
        
        # Обновляем статистику
        self._update_platform_stats(platform_results)
        
        return {
            'success': True,
            'total_platforms': len(platform_results),
            'successful_platforms': len([r for r in platform_results if r.success]),
            'total_signals': len(all_signals),
            'final_signals': len(final_signals),
            'total_processing_time': total_processing_time,
            'platform_results': [
                {
                    'platform': r.platform,
                    'success': r.success,
                    'total_signals': r.total_signals,
                    'filtered_signals': r.filtered_signals,
                    'processing_time': r.processing_time,
                    'error': r.error
                }
                for r in platform_results
            ],
            'signals': final_signals,
            'quality_summary': self.quality_analyzer.get_quality_summary(final_signals),
            'timestamp': datetime.now().isoformat()
        }
    
    def _final_filter_and_rank(self, signals: List[Any]) -> List[Any]:
        """Финальная фильтрация и ранжирование сигналов"""
        if not signals:
            return []
        
        # Убираем дубликаты по ID
        unique_signals = {}
        for signal in signals:
            if hasattr(signal, 'id'):
                unique_signals[signal.id] = signal
        
        signals = list(unique_signals.values())
        
        # Ранжируем по качеству
        signals.sort(key=lambda s: s.real_confidence or 0, reverse=True)
        
        # Возвращаем топ-100 сигналов
        return signals[:100]
    
    def _update_platform_stats(self, platform_results: List[PlatformResult]):
        """Обновляет статистику платформ"""
        for result in platform_results:
            if result.platform in self.platform_stats:
                self.platform_stats[result.platform]['total_signals'] += result.total_signals
                
                # Обновляем success rate
                if result.success:
                    self.platform_stats[result.platform]['success_rate'] = 1.0
                else:
                    self.platform_stats[result.platform]['success_rate'] = 0.0
    
    def get_platform_comparison(self) -> Dict[str, Any]:
        """Получает сравнение эффективности платформ"""
        return {
            'platform_stats': self.platform_stats,
            'recommendations': self._generate_platform_recommendations(),
            'timestamp': datetime.now().isoformat()
        }
    
    def _generate_platform_recommendations(self) -> List[str]:
        """Генерирует рекомендации по платформам"""
        recommendations = []
        
        for platform, stats in self.platform_stats.items():
            if stats['total_signals'] == 0:
                recommendations.append(f"Платформа {platform}: Нет сигналов - проверить доступность")
            elif stats['success_rate'] < 0.5:
                recommendations.append(f"Платформа {platform}: Низкая успешность - оптимизировать парсинг")
            elif stats['total_signals'] > 50:
                recommendations.append(f"Платформа {platform}: Высокая активность - отличный источник")
        
        return recommendations
    
    def save_results(self, results: Dict[str, Any], filename: str = "multi_platform_signals.json"):
        """Сохраняет результаты в файл"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            logger.info(f"Results saved to {filename}")
        except Exception as e:
            logger.error(f"Error saving results: {e}")

def main():
    """Тестирование мультиплатформенного парсера"""
    parser = MultiPlatformParser()
    
    print("=== Тестирование мультиплатформенного парсера ===")
    
    # Парсим все платформы
    print("\n1. Парсинг всех платформ:")
    results = parser.parse_all_platforms_parallel()
    
    if results['success']:
        print(f"✅ Обработано {results['successful_platforms']} платформ из {results['total_platforms']}")
        print(f"  Всего сигналов: {results['total_signals']}")
        print(f"  Финальных сигналов: {results['final_signals']}")
        print(f"  Время обработки: {results['total_processing_time']:.1f}с")
        
        print(f"\n📊 Результаты по платформам:")
        for platform_result in results['platform_results']:
            status = "✅" if platform_result['success'] else "❌"
            print(f"  {status} {platform_result['platform']}: {platform_result['filtered_signals']} сигналов ({platform_result['processing_time']:.1f}с)")
        
        # Качество сигналов
        quality_summary = results['quality_summary']
        print(f"\n📈 Качество сигналов:")
        print(f"  Средний скор: {quality_summary.get('avg_overall_score', 0):.1f}")
        print(f"  Высокое качество: {quality_summary.get('high_quality_count', 0)}")
        print(f"  Низкое качество: {quality_summary.get('low_quality_count', 0)}")
        
        # Сохраняем результаты
        parser.save_results(results)
        
    else:
        print(f"❌ Ошибка при парсинге платформ")
    
    # Сравнение платформ
    print("\n2. Сравнение платформ:")
    comparison = parser.get_platform_comparison()
    
    print(f"📊 Статистика платформ:")
    for platform, stats in comparison['platform_stats'].items():
        print(f"  {platform}: {stats['total_signals']} сигналов (успешность: {stats['success_rate']:.1%})")
    
    if comparison['recommendations']:
        print(f"\n💡 Рекомендации:")
        for rec in comparison['recommendations']:
            print(f"  - {rec}")

if __name__ == "__main__":
    main()
