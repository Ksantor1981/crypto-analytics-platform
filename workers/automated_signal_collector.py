"""
Автоматический сборщик сигналов с учетом структуры БД
"""
import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from decimal import Decimal

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class SignalData:
    """Структура данных сигнала для анализа"""
    channel_name: str
    signal_date: datetime
    trading_pair: str
    direction: str  # LONG/SHORT
    entry_price: float
    target_price: float
    stop_loss: float
    forecast_rating: float  # Оценка прогноза (0-100)
    signal_executed: bool = False
    actual_result: Optional[str] = None  # SUCCESS/FAILURE/PENDING
    profit_loss: Optional[float] = None
    execution_time: Optional[datetime] = None

class AutomatedSignalCollector:
    """
    Автоматический сборщик сигналов с анализом и оценкой
    """
    
    def __init__(self):
        # База каналов для мониторинга
        self.monitored_channels = self._load_monitored_channels()
        
        # Статистика сбора
        self.collection_stats = {
            'total_signals_collected': 0,
            'signals_analyzed': 0,
            'high_quality_signals': 0,
            'channels_processed': 0
        }
        
        # Настройки
        self.settings = {
            'min_forecast_rating': 70.0,  # Минимальная оценка для включения
            'max_signals_per_channel': 50,
            'collection_interval_minutes': 15,
            'signal_expiry_hours': 48
        }
    
    def _load_monitored_channels(self) -> List[Dict[str, Any]]:
        """Загрузка каналов для мониторинга"""
        channels = [
            {
                'username': 'signalsbitcoinandethereum',
                'name': 'Bitcoin & Ethereum Signals',
                'type': 'signal',
                'quality_score': 75,
                'success_rate': 0.65,
                'is_active': True,
                'priority': 'high'
            },
            {
                'username': 'CryptoCapoTG',
                'name': 'CryptoCapo',
                'type': 'analysis',
                'quality_score': 85,
                'success_rate': 0.75,
                'is_active': True,
                'priority': 'high'
            },
            {
                'username': 'binancesignals',
                'name': 'Binance Trading Signals',
                'type': 'signal',
                'quality_score': 80,
                'success_rate': 0.70,
                'is_active': True,
                'priority': 'high'
            },
            {
                'username': 'cryptosignals',
                'name': 'Crypto Signals Pro',
                'type': 'signal',
                'quality_score': 65,
                'success_rate': 0.60,
                'is_active': True,
                'priority': 'medium'
            }
        ]
        
        logger.info(f"Загружено {len(channels)} каналов для мониторинга")
        return channels
    
    async def collect_signals_from_channel(self, channel: Dict[str, Any]) -> List[SignalData]:
        """
        Сбор сигналов с конкретного канала
        """
        logger.info(f"Сбор сигналов с канала: {channel['username']}")
        
        signals = []
        
        try:
            # Здесь должна быть реальная логика сбора через Telegram API
            # Пока что используем симуляцию
            
            mock_signals = self._simulate_channel_signals(channel)
            
            for mock_signal in mock_signals:
                # Анализируем качество сигнала
                forecast_rating = self._analyze_signal_quality(mock_signal, channel)
                
                if forecast_rating >= self.settings['min_forecast_rating']:
                    signal_data = SignalData(
                        channel_name=channel['username'],
                        signal_date=mock_signal['timestamp'],
                        trading_pair=mock_signal['trading_pair'],
                        direction=mock_signal['direction'],
                        entry_price=mock_signal['entry_price'],
                        target_price=mock_signal['target_price'],
                        stop_loss=mock_signal['stop_loss'],
                        forecast_rating=forecast_rating
                    )
                    signals.append(signal_data)
            
            logger.info(f"Собрано {len(signals)} качественных сигналов с {channel['username']}")
            return signals
            
        except Exception as e:
            logger.error(f"Ошибка сбора сигналов с {channel['username']}: {e}")
            return []
    
    def _simulate_channel_signals(self, channel: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Симуляция сигналов с канала"""
        # В реальной реализации здесь будет чтение сообщений через Telegram API
        
        base_signals = [
            {
                'trading_pair': 'BTC/USDT',
                'direction': 'LONG',
                'entry_price': 45000.0,
                'target_price': 47000.0,
                'stop_loss': 44000.0,
                'timestamp': datetime.now() - timedelta(hours=2),
                'original_text': '🚀 BTC LONG Entry: 45000 Target: 47000 SL: 44000'
            },
            {
                'trading_pair': 'ETH/USDT',
                'direction': 'SHORT',
                'entry_price': 3200.0,
                'target_price': 3000.0,
                'stop_loss': 3300.0,
                'timestamp': datetime.now() - timedelta(hours=1),
                'original_text': '📉 ETH SHORT Entry: 3200 Target: 3000 SL: 3300'
            },
            {
                'trading_pair': 'SOL/USDT',
                'direction': 'LONG',
                'entry_price': 95.5,
                'target_price': 100.0,
                'stop_loss': 92.0,
                'timestamp': datetime.now() - timedelta(minutes=30),
                'original_text': '🔥 SOL LONG Entry: 95.5 Target: 100 SL: 92'
            }
        ]
        
        # Адаптируем сигналы под качество канала
        if channel['quality_score'] < 70:
            # Убираем некоторые сигналы для низкокачественных каналов
            base_signals = base_signals[:1]
        
        return base_signals
    
    def _analyze_signal_quality(self, signal: Dict[str, Any], channel: Dict[str, Any]) -> float:
        """
        Анализ качества сигнала и расчет оценки прогноза
        """
        base_score = channel['quality_score']
        
        # Анализ структуры сигнала
        structure_score = self._analyze_signal_structure(signal)
        
        # Анализ риск-риворда
        risk_reward_score = self._analyze_risk_reward(signal)
        
        # Анализ рыночных условий
        market_conditions_score = self._analyze_market_conditions(signal)
        
        # Взвешенная оценка
        final_score = (
            base_score * 0.4 +  # Качество канала
            structure_score * 0.3 +  # Структура сигнала
            risk_reward_score * 0.2 +  # Риск-риворд
            market_conditions_score * 0.1  # Рыночные условия
        )
        
        return min(100.0, max(0.0, final_score))
    
    def _analyze_signal_structure(self, signal: Dict[str, Any]) -> float:
        """Анализ структуры сигнала"""
        score = 50.0  # Базовый балл
        
        # Проверяем наличие всех необходимых полей
        required_fields = ['trading_pair', 'direction', 'entry_price', 'target_price', 'stop_loss']
        for field in required_fields:
            if field in signal and signal[field] is not None:
                score += 10.0
        
        # Проверяем логику цен
        if 'entry_price' in signal and 'target_price' in signal and 'stop_loss' in signal:
            entry = signal['entry_price']
            target = signal['target_price']
            stop = signal['stop_loss']
            
            if signal['direction'] == 'LONG':
                if target > entry and stop < entry:
                    score += 20.0
            elif signal['direction'] == 'SHORT':
                if target < entry and stop > entry:
                    score += 20.0
        
        return min(100.0, score)
    
    def _analyze_risk_reward(self, signal: Dict[str, Any]) -> float:
        """Анализ риск-риворда"""
        if 'entry_price' not in signal or 'target_price' not in signal or 'stop_loss' not in signal:
            return 50.0
        
        entry = signal['entry_price']
        target = signal['target_price']
        stop = signal['stop_loss']
        
        if signal['direction'] == 'LONG':
            potential_profit = target - entry
            potential_loss = entry - stop
        else:  # SHORT
            potential_profit = entry - target
            potential_loss = stop - entry
        
        if potential_loss == 0:
            return 50.0
        
        risk_reward_ratio = potential_profit / potential_loss
        
        # Оценка риск-риворда
        if risk_reward_ratio >= 3.0:
            return 100.0
        elif risk_reward_ratio >= 2.0:
            return 80.0
        elif risk_reward_ratio >= 1.5:
            return 60.0
        elif risk_reward_ratio >= 1.0:
            return 40.0
        else:
            return 20.0
    
    def _analyze_market_conditions(self, signal: Dict[str, Any]) -> float:
        """Анализ рыночных условий"""
        # В реальной реализации здесь будет анализ текущих рыночных условий
        # Пока что возвращаем средний балл
        
        return 70.0
    
    async def track_signal_execution(self, signal: SignalData) -> Dict[str, Any]:
        """
        Отслеживание исполнения сигнала
        """
        logger.info(f"Отслеживание исполнения сигнала: {signal.trading_pair} {signal.direction}")
        
        # Здесь должна быть реальная логика отслеживания через биржевые API
        # Пока что симулируем результат
        
        # Симуляция результата
        execution_result = self._simulate_signal_execution(signal)
        
        # Обновляем данные сигнала
        signal.signal_executed = True
        signal.actual_result = execution_result['result']
        signal.profit_loss = execution_result['profit_loss']
        signal.execution_time = datetime.now()
        
        return execution_result
    
    def _simulate_signal_execution(self, signal: SignalData) -> Dict[str, Any]:
        """Симуляция исполнения сигнала"""
        import random
        
        # Симулируем результат на основе качества прогноза
        success_probability = signal.forecast_rating / 100.0
        
        if random.random() < success_probability:
            # Успешное исполнение
            if signal.direction == 'LONG':
                profit_loss = (signal.target_price - signal.entry_price) / signal.entry_price * 100
            else:
                profit_loss = (signal.entry_price - signal.target_price) / signal.entry_price * 100
            
            return {
                'result': 'SUCCESS',
                'profit_loss': profit_loss,
                'execution_time': datetime.now()
            }
        else:
            # Неуспешное исполнение
            if signal.direction == 'LONG':
                profit_loss = (signal.stop_loss - signal.entry_price) / signal.entry_price * 100
            else:
                profit_loss = (signal.entry_price - signal.stop_loss) / signal.entry_price * 100
            
            return {
                'result': 'FAILURE',
                'profit_loss': profit_loss,
                'execution_time': datetime.now()
            }
    
    def generate_analytics_report(self, signals: List[SignalData]) -> Dict[str, Any]:
        """
        Генерация аналитического отчета
        """
        if not signals:
            return {'error': 'Нет данных для анализа'}
        
        # Базовая статистика
        total_signals = len(signals)
        executed_signals = [s for s in signals if s.signal_executed]
        successful_signals = [s for s in executed_signals if s.actual_result == 'SUCCESS']
        
        # Расчет метрик
        execution_rate = len(executed_signals) / total_signals if total_signals > 0 else 0
        success_rate = len(successful_signals) / len(executed_signals) if executed_signals else 0
        
        # Анализ по каналам
        channel_stats = {}
        for signal in signals:
            channel = signal.channel_name
            if channel not in channel_stats:
                channel_stats[channel] = {
                    'total_signals': 0,
                    'executed_signals': 0,
                    'successful_signals': 0,
                    'avg_forecast_rating': 0.0,
                    'avg_profit_loss': 0.0
                }
            
            channel_stats[channel]['total_signals'] += 1
            channel_stats[channel]['avg_forecast_rating'] += signal.forecast_rating
            
            if signal.signal_executed:
                channel_stats[channel]['executed_signals'] += 1
                channel_stats[channel]['avg_profit_loss'] += signal.profit_loss or 0
                
                if signal.actual_result == 'SUCCESS':
                    channel_stats[channel]['successful_signals'] += 1
        
        # Нормализация средних значений
        for channel in channel_stats:
            stats = channel_stats[channel]
            stats['avg_forecast_rating'] /= stats['total_signals']
            if stats['executed_signals'] > 0:
                stats['avg_profit_loss'] /= stats['executed_signals']
        
        # Анализ по торговым парам
        pair_stats = {}
        for signal in signals:
            pair = signal.trading_pair
            if pair not in pair_stats:
                pair_stats[pair] = {
                    'total_signals': 0,
                    'successful_signals': 0,
                    'avg_profit_loss': 0.0
                }
            
            pair_stats[pair]['total_signals'] += 1
            if signal.signal_executed and signal.actual_result == 'SUCCESS':
                pair_stats[pair]['successful_signals'] += 1
                pair_stats[pair]['avg_profit_loss'] += signal.profit_loss or 0
        
        # Нормализация
        for pair in pair_stats:
            stats = pair_stats[pair]
            if stats['successful_signals'] > 0:
                stats['avg_profit_loss'] /= stats['successful_signals']
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_signals': total_signals,
                'executed_signals': len(executed_signals),
                'successful_signals': len(successful_signals),
                'execution_rate': execution_rate,
                'success_rate': success_rate,
                'avg_forecast_rating': sum(s.forecast_rating for s in signals) / total_signals
            },
            'channel_analytics': channel_stats,
            'pair_analytics': pair_stats,
            'top_performing_channels': sorted(
                channel_stats.items(),
                key=lambda x: x[1]['success_rate'] if x[1]['executed_signals'] > 0 else 0,
                reverse=True
            )[:5],
            'top_performing_pairs': sorted(
                pair_stats.items(),
                key=lambda x: x[1]['success_rate'] if x[1]['total_signals'] > 0 else 0,
                reverse=True
            )[:5]
        }
        
        return report
    
    async def run_full_collection_cycle(self) -> Dict[str, Any]:
        """
        Запуск полного цикла сбора и анализа сигналов
        """
        logger.info("🚀 Запуск полного цикла сбора сигналов...")
        
        start_time = datetime.now()
        all_signals = []
        
        # Собираем сигналы со всех активных каналов
        active_channels = [ch for ch in self.monitored_channels if ch['is_active']]
        
        for channel in active_channels:
            try:
                signals = await self.collect_signals_from_channel(channel)
                all_signals.extend(signals)
                
                self.collection_stats['channels_processed'] += 1
                self.collection_stats['total_signals_collected'] += len(signals)
                
            except Exception as e:
                logger.error(f"Ошибка обработки канала {channel['username']}: {e}")
        
        # Отслеживаем исполнение сигналов
        for signal in all_signals:
            try:
                await self.track_signal_execution(signal)
                self.collection_stats['signals_analyzed'] += 1
                
                if signal.forecast_rating >= 80:
                    self.collection_stats['high_quality_signals'] += 1
                    
            except Exception as e:
                logger.error(f"Ошибка отслеживания сигнала: {e}")
        
        # Генерируем аналитический отчет
        analytics_report = self.generate_analytics_report(all_signals)
        
        # Сохраняем результаты
        results = {
            'timestamp': datetime.now().isoformat(),
            'collection_stats': self.collection_stats,
            'signals_data': [
                {
                    'channel_name': signal.channel_name,
                    'signal_date': signal.signal_date.isoformat(),
                    'trading_pair': signal.trading_pair,
                    'direction': signal.direction,
                    'entry_price': signal.entry_price,
                    'target_price': signal.target_price,
                    'stop_loss': signal.stop_loss,
                    'forecast_rating': signal.forecast_rating,
                    'signal_executed': signal.signal_executed,
                    'actual_result': signal.actual_result,
                    'profit_loss': signal.profit_loss,
                    'execution_time': signal.execution_time.isoformat() if signal.execution_time else None
                }
                for signal in all_signals
            ],
            'analytics_report': analytics_report,
            'duration_seconds': (datetime.now() - start_time).total_seconds()
        }
        
        # Сохраняем в файл
        with open('signal_collection_analytics.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2, default=str)
        
        logger.info(f"✅ Цикл сбора завершен за {results['duration_seconds']:.2f} секунд")
        return results

async def main():
    """Тестовая функция"""
    collector = AutomatedSignalCollector()
    
    # Показываем каналы для мониторинга
    print("📋 КАНАЛЫ ДЛЯ МОНИТОРИНГА:")
    print("=" * 60)
    
    for channel in collector.monitored_channels:
        print(f"Канал: {channel['username']}")
        print(f"  Название: {channel['name']}")
        print(f"  Тип: {channel['type']}")
        print(f"  Качество: {channel['quality_score']}/100")
        print(f"  Успешность: {channel['success_rate']:.1%}")
        print(f"  Приоритет: {channel['priority']}")
        print("-" * 40)
    
    # Запускаем полный цикл сбора
    print("\n🚀 ЗАПУСК ПОЛНОГО ЦИКЛА СБОРА:")
    print("=" * 60)
    
    results = await collector.run_full_collection_cycle()
    
    # Показываем результаты
    print(f"\n📊 РЕЗУЛЬТАТЫ СБОРА:")
    print(f"Всего сигналов: {results['collection_stats']['total_signals_collected']}")
    print(f"Проанализировано: {results['collection_stats']['signals_analyzed']}")
    print(f"Высокое качество: {results['collection_stats']['high_quality_signals']}")
    print(f"Обработано каналов: {results['collection_stats']['channels_processed']}")
    
    # Показываем аналитику
    analytics = results['analytics_report']
    print(f"\n📈 АНАЛИТИКА:")
    print(f"Общая успешность: {analytics['summary']['success_rate']:.1%}")
    print(f"Средняя оценка прогноза: {analytics['summary']['avg_forecast_rating']:.1f}/100")
    
    if analytics['top_performing_channels']:
        print(f"\n🏆 ЛУЧШИЕ КАНАЛЫ:")
        for i, (channel, stats) in enumerate(analytics['top_performing_channels'][:3]):
            success_rate = stats['success_rate'] if stats['executed_signals'] > 0 else 0
            print(f"{i+1}. {channel}: {success_rate:.1%} успешность")

if __name__ == "__main__":
    asyncio.run(main())
