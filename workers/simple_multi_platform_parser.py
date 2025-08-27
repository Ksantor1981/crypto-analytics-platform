"""
Simple Multi-Platform Parser - Упрощенный мультиплатформенный парсер
Интегрирует парсинг с Telegram, Reddit и TradingView
"""

import json
import logging
import time
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor, as_completed

from real_telegram_parser import RealTelegramParser
from simple_reddit_parser import SimpleRedditParser
from simple_tradingview_parser import SimpleTradingViewParser
from improved_signal_parser import ImprovedSignal, SignalDirection, SignalQuality

class SignalJSONEncoder(json.JSONEncoder):
    """Кастомный JSON encoder для сигналов"""
    def default(self, obj):
        if isinstance(obj, (SignalDirection, SignalQuality)):
            return obj.value
        return super().default(obj)

logger = logging.getLogger(__name__)

@dataclass
class PlatformResult:
    """Результат парсинга платформы"""
    platform: str
    success: bool
    total_signals: int
    filtered_signals: int
    processing_time: float
    signals: List[Any]
    error: Optional[str] = None

class SimpleMultiPlatformParser:
    """Упрощенный мультиплатформенный парсер"""
    
    def __init__(self):
        self.telegram_parser = RealTelegramParser()
        self.reddit_parser = SimpleRedditParser()
        self.tradingview_parser = SimpleTradingViewParser()
        
        # Статистика платформ
        self.platform_stats = {
            'telegram': {'total_signals': 0, 'successful_runs': 0, 'avg_quality': 0.0},
            'reddit': {'total_signals': 0, 'successful_runs': 0, 'avg_quality': 0.0},
            'tradingview': {'total_signals': 0, 'successful_runs': 0, 'avg_quality': 0.0}
        }
    
    def parse_telegram_platform(self) -> PlatformResult:
        """Парсит Telegram платформу"""
        start_time = time.time()
        
        try:
            logger.info("Starting Telegram platform parsing")
            
            # Парсим Telegram каналы
            telegram_result = self.telegram_parser.parse_channels()
            
            if telegram_result['success']:
                signals = telegram_result.get('signals', [])
                filtered_signals = self._filter_signals_by_quality(signals)
                
                processing_time = time.time() - start_time
                
                # Обновляем статистику
                self.platform_stats['telegram']['total_signals'] += len(filtered_signals)
                self.platform_stats['telegram']['successful_runs'] += 1
                
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
                    signals=[],
                    error=telegram_result.get('error', 'Unknown error')
                )
                
        except Exception as e:
            logger.error(f"Error parsing Telegram platform: {e}")
            return PlatformResult(
                platform="telegram",
                success=False,
                total_signals=0,
                filtered_signals=0,
                processing_time=time.time() - start_time,
                signals=[],
                error=str(e)
            )
    
    def parse_reddit_platform(self) -> PlatformResult:
        """Парсит Reddit платформу"""
        start_time = time.time()
        
        try:
            logger.info("Starting Reddit platform parsing")
            
            # Парсим Reddit
            reddit_result = self.reddit_parser.parse_all_subreddits()
            
            if reddit_result['success']:
                signals = reddit_result.get('signals', [])
                filtered_signals = self._filter_signals_by_quality(signals)
                
                processing_time = time.time() - start_time
                
                # Обновляем статистику
                self.platform_stats['reddit']['total_signals'] += len(filtered_signals)
                self.platform_stats['reddit']['successful_runs'] += 1
                
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
                    signals=[],
                    error=reddit_result.get('error', 'Unknown error')
                )
                
        except Exception as e:
            logger.error(f"Error parsing Reddit platform: {e}")
            return PlatformResult(
                platform="reddit",
                success=False,
                total_signals=0,
                filtered_signals=0,
                processing_time=time.time() - start_time,
                signals=[],
                error=str(e)
            )
    
    def parse_tradingview_platform(self) -> PlatformResult:
        """Парсит TradingView платформу"""
        start_time = time.time()
        
        try:
            logger.info("Starting TradingView platform parsing")
            
            # Парсим TradingView
            tradingview_result = self.tradingview_parser.parse_all_symbols()
            
            if tradingview_result['success']:
                signals = tradingview_result.get('signals', [])
                filtered_signals = self._filter_signals_by_quality(signals)
                
                processing_time = time.time() - start_time
                
                # Обновляем статистику
                self.platform_stats['tradingview']['total_signals'] += len(filtered_signals)
                self.platform_stats['tradingview']['successful_runs'] += 1
                
                return PlatformResult(
                    platform="tradingview",
                    success=True,
                    total_signals=len(signals),
                    filtered_signals=len(filtered_signals),
                    processing_time=processing_time,
                    signals=filtered_signals
                )
            else:
                return PlatformResult(
                    platform="tradingview",
                    success=False,
                    total_signals=0,
                    filtered_signals=0,
                    processing_time=time.time() - start_time,
                    signals=[],
                    error=tradingview_result.get('error', 'Unknown error')
                )
                
        except Exception as e:
            logger.error(f"Error parsing TradingView platform: {e}")
            return PlatformResult(
                platform="tradingview",
                success=False,
                total_signals=0,
                filtered_signals=0,
                processing_time=time.time() - start_time,
                signals=[],
                error=str(e)
            )
    
    def _filter_signals_by_quality(self, signals: List[Dict]) -> List[Dict]:
        """Фильтрует сигналы по качеству"""
        filtered = []
        
        for signal in signals:
            # Проверяем базовые критерии качества
            if signal.get('is_valid', False) and signal.get('real_confidence', 0) > 30:
                filtered.append(signal)
        
        return filtered
    
    def parse_all_platforms(self, 
                          telegram_channels: Optional[List[Dict]] = None,
                          include_reddit: bool = True,
                          include_tradingview: bool = True) -> Dict[str, Any]:
        """Парсит все платформы параллельно"""
        logger.info("Starting multi-platform parsing")
        
        results = {}
        platform_results = []
        
        # Парсим Telegram (основной источник)
        telegram_result = self.parse_telegram_platform()
        results['telegram'] = telegram_result
        platform_results.append(telegram_result)
        
        # Парсим дополнительные платформы
        if include_reddit:
            reddit_result = self.parse_reddit_platform()
            results['reddit'] = reddit_result
            platform_results.append(reddit_result)
        
        if include_tradingview:
            tradingview_result = self.parse_tradingview_platform()
            results['tradingview'] = tradingview_result
            platform_results.append(tradingview_result)
        
        # Объединяем все сигналы
        all_signals = []
        for result in platform_results:
            if result.success and result.signals:
                all_signals.extend(result.signals)
        
        # Сортируем по уверенности
        all_signals.sort(key=lambda x: x.get('real_confidence', 0), reverse=True)
        
        # Создаем итоговый результат
        final_result = {
            'success': True,
            'total_signals': len(all_signals),
            'platform_results': {
                platform: {
                    'success': result.success,
                    'total_signals': result.total_signals,
                    'filtered_signals': result.filtered_signals,
                    'processing_time': result.processing_time,
                    'error': result.error
                }
                for platform, result in results.items()
            },
            'signals': all_signals,
            'platform_stats': self.platform_stats,
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"Multi-platform parsing completed. Total signals: {len(all_signals)}")
        
        return final_result
    
    def save_results(self, results: Dict[str, Any], filename: str = "multi_platform_signals.json"):
        """Сохраняет результаты в JSON файл"""
        try:
            # Подготовка данных для сериализации
            serializable_results = {
                'success': results['success'],
                'total_signals': results['total_signals'],
                'platform_results': results['platform_results'],
                'signals': results['signals'],
                'platform_stats': results['platform_stats'],
                'timestamp': results['timestamp']
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(serializable_results, f, indent=2, ensure_ascii=False, cls=SignalJSONEncoder)
            
            logger.info(f"Results saved to {filename}")
            
        except Exception as e:
            logger.error(f"Error saving results: {e}")

def main():
    """Основная функция для запуска мультиплатформенного парсера"""
    parser = SimpleMultiPlatformParser()
    
    logger.info("Starting multi-platform signal parsing...")
    results = parser.parse_all_platforms()
    
    # Сохраняем результаты
    parser.save_results(results)
    
    # Выводим статистику
    print(f"\n=== Multi-Platform Parsing Results ===")
    print(f"Total signals found: {results['total_signals']}")
    
    for platform, result in results['platform_results'].items():
        print(f"\n{platform.upper()}:")
        print(f"  Success: {result['success']}")
        print(f"  Total signals: {result['total_signals']}")
        print(f"  Filtered signals: {result['filtered_signals']}")
        print(f"  Processing time: {result['processing_time']:.2f}s")
        if result.get('error'):
            print(f"  Error: {result['error']}")
    
    return results

if __name__ == "__main__":
    main()
