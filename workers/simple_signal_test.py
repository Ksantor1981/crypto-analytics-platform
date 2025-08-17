"""
Упрощенный тест системы сбора сигналов
"""
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any

class SimpleSignalCollector:
    """Упрощенный сборщик сигналов для тестирования"""
    
    def __init__(self):
        self.channels = [
            {
                'username': 'signalsbitcoinandethereum',
                'name': 'Bitcoin & Ethereum Signals',
                'quality_score': 75,
                'success_rate': 0.65
            },
            {
                'username': 'CryptoCapoTG',
                'name': 'CryptoCapo',
                'quality_score': 85,
                'success_rate': 0.75
            }
        ]
    
    def simulate_signals(self) -> List[Dict[str, Any]]:
        """Симуляция сигналов"""
        signals = []
        
        for channel in self.channels:
            # Создаем тестовые сигналы для каждого канала
            channel_signals = [
                {
                    'channel_name': channel['username'],
                    'signal_date': datetime.now().isoformat(),
                    'trading_pair': 'BTC/USDT',
                    'direction': 'LONG',
                    'entry_price': 45000.0,
                    'target_price': 47000.0,
                    'stop_loss': 44000.0,
                    'forecast_rating': channel['quality_score'],
                    'signal_executed': True,
                    'actual_result': 'SUCCESS' if channel['success_rate'] > 0.7 else 'FAILURE',
                    'profit_loss': 4.44 if channel['success_rate'] > 0.7 else -2.22,
                    'execution_time': datetime.now().isoformat()
                },
                {
                    'channel_name': channel['username'],
                    'signal_date': (datetime.now() - timedelta(hours=1)).isoformat(),
                    'trading_pair': 'ETH/USDT',
                    'direction': 'SHORT',
                    'entry_price': 3200.0,
                    'target_price': 3000.0,
                    'stop_loss': 3300.0,
                    'forecast_rating': channel['quality_score'] - 5,
                    'signal_executed': True,
                    'actual_result': 'SUCCESS' if channel['success_rate'] > 0.6 else 'FAILURE',
                    'profit_loss': 6.25 if channel['success_rate'] > 0.6 else -3.13,
                    'execution_time': datetime.now().isoformat()
                }
            ]
            signals.extend(channel_signals)
        
        return signals
    
    def generate_analytics(self, signals: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Генерация аналитики"""
        if not signals:
            return {'error': 'Нет данных'}
        
        # Базовая статистика
        total_signals = len(signals)
        successful_signals = [s for s in signals if s['actual_result'] == 'SUCCESS']
        success_rate = len(successful_signals) / total_signals if total_signals > 0 else 0
        
        # Анализ по каналам
        channel_stats = {}
        for signal in signals:
            channel = signal['channel_name']
            if channel not in channel_stats:
                channel_stats[channel] = {
                    'total_signals': 0,
                    'successful_signals': 0,
                    'avg_forecast_rating': 0.0,
                    'avg_profit_loss': 0.0
                }
            
            channel_stats[channel]['total_signals'] += 1
            channel_stats[channel]['avg_forecast_rating'] += signal['forecast_rating']
            channel_stats[channel]['avg_profit_loss'] += signal['profit_loss']
            
            if signal['actual_result'] == 'SUCCESS':
                channel_stats[channel]['successful_signals'] += 1
        
        # Нормализация
        for channel in channel_stats:
            stats = channel_stats[channel]
            stats['avg_forecast_rating'] /= stats['total_signals']
            stats['avg_profit_loss'] /= stats['total_signals']
            stats['success_rate'] = stats['successful_signals'] / stats['total_signals']
        
        return {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_signals': total_signals,
                'successful_signals': len(successful_signals),
                'success_rate': success_rate,
                'avg_forecast_rating': sum(s['forecast_rating'] for s in signals) / total_signals
            },
            'channel_analytics': channel_stats,
            'top_channels': sorted(
                channel_stats.items(),
                key=lambda x: x[1]['success_rate'],
                reverse=True
            )
        }
    
    def run_test(self) -> Dict[str, Any]:
        """Запуск теста"""
        print("🚀 Запуск упрощенного теста...")
        
        # Симулируем сигналы
        signals = self.simulate_signals()
        print(f"Создано {len(signals)} тестовых сигналов")
        
        # Генерируем аналитику
        analytics = self.generate_analytics(signals)
        print(f"Сгенерирована аналитика для {len(analytics['channel_analytics'])} каналов")
        
        # Сохраняем результаты
        results = {
            'signals_data': signals,
            'analytics_report': analytics
        }
        
        with open('simple_signal_test_results.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2, default=str)
        
        print("✅ Тест завершен, результаты сохранены")
        return results

def main():
    """Основная функция"""
    collector = SimpleSignalCollector()
    
    # Показываем каналы
    print("📋 ТЕСТОВЫЕ КАНАЛЫ:")
    print("=" * 40)
    for channel in collector.channels:
        print(f"Канал: {channel['username']}")
        print(f"  Качество: {channel['quality_score']}/100")
        print(f"  Успешность: {channel['success_rate']:.1%}")
        print("-" * 30)
    
    # Запускаем тест
    print("\n🚀 ЗАПУСК ТЕСТА:")
    print("=" * 40)
    
    results = collector.run_test()
    
    # Показываем результаты
    analytics = results['analytics_report']
    print(f"\n📊 РЕЗУЛЬТАТЫ:")
    print(f"Всего сигналов: {analytics['summary']['total_signals']}")
    print(f"Успешных: {analytics['summary']['successful_signals']}")
    print(f"Общая успешность: {analytics['summary']['success_rate']:.1%}")
    print(f"Средняя оценка: {analytics['summary']['avg_forecast_rating']:.1f}/100")
    
    print(f"\n🏆 ЛУЧШИЕ КАНАЛЫ:")
    for i, (channel, stats) in enumerate(analytics['top_channels']):
        print(f"{i+1}. {channel}: {stats['success_rate']:.1%} успешность")

if __name__ == "__main__":
    main()
