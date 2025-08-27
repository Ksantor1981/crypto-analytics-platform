"""
Signal Monitor - Система мониторинга и алертов
Отслеживает качество парсинга, точность сигналов и отправляет уведомления
"""

import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
from integrated_signal_processor import IntegratedSignalProcessor
from signal_quality_analyzer import QualityScore

logger = logging.getLogger(__name__)

class AlertLevel(Enum):
    """Уровни алертов"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"

@dataclass
class MonitoringAlert:
    """Алерт мониторинга"""
    id: str
    level: AlertLevel
    title: str
    message: str
    timestamp: str
    channel: Optional[str] = None
    signal_id: Optional[str] = None
    metrics: Optional[Dict] = None
    resolved: bool = False

@dataclass
class MonitoringMetrics:
    """Метрики мониторинга"""
    timestamp: str
    total_signals: int
    valid_signals: int
    invalid_signals: int
    avg_quality_score: float
    avg_confidence: float
    bybit_available_count: int
    high_quality_count: int
    low_quality_count: int
    channel_count: int
    processing_time_seconds: float
    error_count: int

class SignalMonitor:
    """Система мониторинга сигналов"""
    
    def __init__(self):
        self.processor = IntegratedSignalProcessor()
        self.alerts: List[MonitoringAlert] = []
        self.metrics_history: List[MonitoringMetrics] = []
        
        # Пороги для алертов
        self.thresholds = {
            'min_quality_score': 50.0,
            'min_confidence': 40.0,
            'max_error_rate': 0.3,  # 30% ошибок
            'min_valid_signals': 1,
            'max_processing_time': 60.0,  # секунд
            'min_bybit_available': 0.5  # 50% сигналов должны быть доступны на Bybit
        }
        
        # Настройки мониторинга
        self.monitoring_interval = 300  # 5 минут
        self.alert_retention_hours = 24
        self.metrics_retention_hours = 168  # 7 дней
    
    def run_monitoring_cycle(self) -> Dict[str, Any]:
        """Выполняет цикл мониторинга"""
        start_time = time.time()
        
        try:
            # Получаем текущие данные
            telegram_result = self.processor.process_telegram_channels()
            
            # Рассчитываем метрики
            metrics = self._calculate_metrics(telegram_result, time.time() - start_time)
            self.metrics_history.append(metrics)
            
            # Проверяем алерты
            new_alerts = self._check_alerts(metrics, telegram_result)
            self.alerts.extend(new_alerts)
            
            # Очищаем старые данные
            self._cleanup_old_data()
            
            return {
                'success': True,
                'metrics': metrics,
                'new_alerts': len(new_alerts),
                'total_alerts': len(self.alerts),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in monitoring cycle: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def _calculate_metrics(self, telegram_result: Dict[str, Any], processing_time: float) -> MonitoringMetrics:
        """Рассчитывает метрики мониторинга"""
        signals = telegram_result.get('signals', [])
        
        if not signals:
            return MonitoringMetrics(
                timestamp=datetime.now().isoformat(),
                total_signals=0,
                valid_signals=0,
                invalid_signals=0,
                avg_quality_score=0.0,
                avg_confidence=0.0,
                bybit_available_count=0,
                high_quality_count=0,
                low_quality_count=0,
                channel_count=0,
                processing_time_seconds=processing_time,
                error_count=0
            )
        
        # Базовые метрики
        total_signals = len(signals)
        valid_signals = len([s for s in signals if s.get('is_valid', False)])
        invalid_signals = total_signals - valid_signals
        
        # Качество и уверенность
        quality_scores = [s.get('real_confidence', 0) for s in signals]
        avg_quality_score = sum(quality_scores) / len(quality_scores) if quality_scores else 0.0
        avg_confidence = avg_quality_score  # Используем тот же показатель
        
        # Доступность на Bybit
        bybit_available_count = len([s for s in signals if s.get('bybit_available', False)])
        
        # Качество сигналов
        high_quality_count = len([s for s in signals if s.get('signal_quality') in ['excellent', 'good']])
        low_quality_count = len([s for s in signals if s.get('signal_quality') in ['poor', 'unreliable']])
        
        # Каналы
        channels = set(s.get('channel', '') for s in signals)
        channel_count = len(channels)
        
        return MonitoringMetrics(
            timestamp=datetime.now().isoformat(),
            total_signals=total_signals,
            valid_signals=valid_signals,
            invalid_signals=invalid_signals,
            avg_quality_score=avg_quality_score,
            avg_confidence=avg_confidence,
            bybit_available_count=bybit_available_count,
            high_quality_count=high_quality_count,
            low_quality_count=low_quality_count,
            channel_count=channel_count,
            processing_time_seconds=processing_time,
            error_count=0  # Пока не отслеживаем ошибки парсинга
        )
    
    def _check_alerts(self, metrics: MonitoringMetrics, telegram_result: Dict[str, Any]) -> List[MonitoringAlert]:
        """Проверяет условия для алертов"""
        alerts = []
        
        # Алерт на низкое качество
        if metrics.avg_quality_score < self.thresholds['min_quality_score']:
            alerts.append(MonitoringAlert(
                id=f"quality_{int(time.time())}",
                level=AlertLevel.WARNING,
                title="Низкое качество сигналов",
                message=f"Среднее качество сигналов: {metrics.avg_quality_score:.1f}% (минимум: {self.thresholds['min_quality_score']}%)",
                timestamp=datetime.now().isoformat(),
                metrics={'avg_quality_score': metrics.avg_quality_score}
            ))
        
        # Алерт на низкую уверенность
        if metrics.avg_confidence < self.thresholds['min_confidence']:
            alerts.append(MonitoringAlert(
                id=f"confidence_{int(time.time())}",
                level=AlertLevel.WARNING,
                title="Низкая уверенность сигналов",
                message=f"Средняя уверенность: {metrics.avg_confidence:.1f}% (минимум: {self.thresholds['min_confidence']}%)",
                timestamp=datetime.now().isoformat(),
                metrics={'avg_confidence': metrics.avg_confidence}
            ))
        
        # Алерт на отсутствие валидных сигналов
        if metrics.valid_signals < self.thresholds['min_valid_signals']:
            alerts.append(MonitoringAlert(
                id=f"no_valid_{int(time.time())}",
                level=AlertLevel.CRITICAL,
                title="Нет валидных сигналов",
                message=f"Валидных сигналов: {metrics.valid_signals} (минимум: {self.thresholds['min_valid_signals']})",
                timestamp=datetime.now().isoformat(),
                metrics={'valid_signals': metrics.valid_signals}
            ))
        
        # Алерт на медленную обработку
        if metrics.processing_time_seconds > self.thresholds['max_processing_time']:
            alerts.append(MonitoringAlert(
                id=f"slow_processing_{int(time.time())}",
                level=AlertLevel.WARNING,
                title="Медленная обработка",
                message=f"Время обработки: {metrics.processing_time_seconds:.1f}с (максимум: {self.thresholds['max_processing_time']}с)",
                timestamp=datetime.now().isoformat(),
                metrics={'processing_time': metrics.processing_time_seconds}
            ))
        
        # Алерт на низкую доступность Bybit
        if metrics.total_signals > 0:
            bybit_ratio = metrics.bybit_available_count / metrics.total_signals
            if bybit_ratio < self.thresholds['min_bybit_available']:
                alerts.append(MonitoringAlert(
                    id=f"bybit_availability_{int(time.time())}",
                    level=AlertLevel.WARNING,
                    title="Низкая доступность на Bybit",
                    message=f"Доступно на Bybit: {bybit_ratio:.1%} (минимум: {self.thresholds['min_bybit_available']:.1%})",
                    timestamp=datetime.now().isoformat(),
                    metrics={'bybit_ratio': bybit_ratio}
                ))
        
        # Алерт на ошибки парсинга
        if not telegram_result.get('success', False):
            alerts.append(MonitoringAlert(
                id=f"parsing_error_{int(time.time())}",
                level=AlertLevel.CRITICAL,
                title="Ошибка парсинга Telegram",
                message=f"Ошибка: {telegram_result.get('error', 'Unknown error')}",
                timestamp=datetime.now().isoformat(),
                metrics={'error': telegram_result.get('error')}
            ))
        
        return alerts
    
    def _cleanup_old_data(self):
        """Очищает старые данные"""
        current_time = datetime.now()
        
        # Очищаем старые алерты
        cutoff_time = current_time - timedelta(hours=self.alert_retention_hours)
        self.alerts = [
            alert for alert in self.alerts 
            if datetime.fromisoformat(alert.timestamp) > cutoff_time
        ]
        
        # Очищаем старые метрики
        cutoff_time = current_time - timedelta(hours=self.metrics_retention_hours)
        self.metrics_history = [
            metrics for metrics in self.metrics_history
            if datetime.fromisoformat(metrics.timestamp) > cutoff_time
        ]
    
    def get_monitoring_summary(self) -> Dict[str, Any]:
        """Получает сводку мониторинга"""
        if not self.metrics_history:
            return {
                'success': True,
                'message': 'No monitoring data available',
                'timestamp': datetime.now().isoformat()
            }
        
        # Последние метрики
        latest_metrics = self.metrics_history[-1]
        
        # Статистика за последние 24 часа
        cutoff_time = datetime.now() - timedelta(hours=24)
        recent_metrics = [
            m for m in self.metrics_history
            if datetime.fromisoformat(m.timestamp) > cutoff_time
        ]
        
        # Активные алерты
        active_alerts = [alert for alert in self.alerts if not alert.resolved]
        
        # Тренды
        if len(recent_metrics) >= 2:
            quality_trend = recent_metrics[-1].avg_quality_score - recent_metrics[0].avg_quality_score
            confidence_trend = recent_metrics[-1].avg_confidence - recent_metrics[0].avg_confidence
        else:
            quality_trend = 0.0
            confidence_trend = 0.0
        
        return {
            'success': True,
            'current_metrics': {
                'total_signals': latest_metrics.total_signals,
                'valid_signals': latest_metrics.valid_signals,
                'avg_quality_score': latest_metrics.avg_quality_score,
                'avg_confidence': latest_metrics.avg_confidence,
                'bybit_available_count': latest_metrics.bybit_available_count,
                'high_quality_count': latest_metrics.high_quality_count,
                'low_quality_count': latest_metrics.low_quality_count,
                'channel_count': latest_metrics.channel_count,
                'processing_time_seconds': latest_metrics.processing_time_seconds
            },
            'trends': {
                'quality_trend': quality_trend,
                'confidence_trend': confidence_trend
            },
            'alerts': {
                'total_alerts': len(self.alerts),
                'active_alerts': len(active_alerts),
                'critical_alerts': len([a for a in active_alerts if a.level == AlertLevel.CRITICAL]),
                'warning_alerts': len([a for a in active_alerts if a.level == AlertLevel.WARNING]),
                'info_alerts': len([a for a in active_alerts if a.level == AlertLevel.INFO])
            },
            'recent_alerts': [
                {
                    'id': alert.id,
                    'level': alert.level.value,
                    'title': alert.title,
                    'message': alert.message,
                    'timestamp': alert.timestamp,
                    'resolved': alert.resolved
                }
                for alert in active_alerts[-10:]  # Последние 10 алертов
            ],
            'summary_timestamp': datetime.now().isoformat()
        }
    
    def resolve_alert(self, alert_id: str) -> Dict[str, Any]:
        """Отмечает алерт как разрешенный"""
        for alert in self.alerts:
            if alert.id == alert_id:
                alert.resolved = True
                return {
                    'success': True,
                    'message': f'Alert {alert_id} marked as resolved',
                    'timestamp': datetime.now().isoformat()
                }
        
        return {
            'success': False,
            'error': f'Alert {alert_id} not found',
            'timestamp': datetime.now().isoformat()
        }
    
    def send_notification(self, alert: MonitoringAlert) -> Dict[str, Any]:
        """Отправляет уведомление (заглушка для интеграции с внешними системами)"""
        # Здесь можно интегрировать с Telegram, email, Slack и т.д.
        notification = {
            'level': alert.level.value,
            'title': alert.title,
            'message': alert.message,
            'timestamp': alert.timestamp,
            'channel': alert.channel,
            'signal_id': alert.signal_id
        }
        
        logger.info(f"Notification sent: {notification}")
        
        return {
            'success': True,
            'notification': notification,
            'timestamp': datetime.now().isoformat()
        }

def main():
    """Тестирование системы мониторинга"""
    monitor = SignalMonitor()
    
    print("=== Тестирование системы мониторинга ===")
    
    # Запускаем цикл мониторинга
    print("\n1. Запуск цикла мониторинга:")
    result = monitor.run_monitoring_cycle()
    
    if result['success']:
        print(f"✅ Мониторинг завершен")
        print(f"  Метрик: {result['metrics'].total_signals} сигналов")
        print(f"  Новых алертов: {result['new_alerts']}")
        print(f"  Всего алертов: {result['total_alerts']}")
    else:
        print(f"❌ Ошибка: {result['error']}")
    
    # Получаем сводку
    print("\n2. Сводка мониторинга:")
    summary = monitor.get_monitoring_summary()
    
    if summary['success']:
        current = summary['current_metrics']
        alerts = summary['alerts']
        
        print(f"✅ Текущие метрики:")
        print(f"  Сигналов: {current['total_signals']} (валидных: {current['valid_signals']})")
        print(f"  Качество: {current['avg_quality_score']:.1f}%")
        print(f"  Уверенность: {current['avg_confidence']:.1f}%")
        print(f"  Доступно на Bybit: {current['bybit_available_count']}")
        print(f"  Каналов: {current['channel_count']}")
        
        print(f"\n📊 Алерты:")
        print(f"  Всего: {alerts['total_alerts']}")
        print(f"  Активных: {alerts['active_alerts']}")
        print(f"  Критических: {alerts['critical_alerts']}")
        print(f"  Предупреждений: {alerts['warning_alerts']}")
        
        if summary['recent_alerts']:
            print(f"\n🚨 Последние алерты:")
            for alert in summary['recent_alerts'][:3]:
                print(f"  - [{alert['level'].upper()}] {alert['title']}")
    else:
        print(f"❌ Ошибка: {summary['message']}")

if __name__ == "__main__":
    main()
