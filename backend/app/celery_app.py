"""
Celery configuration for signal collection and automation
"""
import os
from celery import Celery
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Redis configuration
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Create Celery app
celery_app = Celery(
    "crypto_analytics_signals",
    broker=redis_url,
    backend=redis_url,
    include=['workers.tasks']
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    worker_hijack_root_logger=False,
    task_always_eager=False,
    task_eager_propagates=True,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_max_tasks_per_child=1000,
    broker_connection_retry_on_startup=True,
)

# Beat schedule for periodic tasks
celery_app.conf.beat_schedule = {
    # Сбор сигналов каждый час
    'collect_telegram_signals_hourly': {
        'task': 'collect_telegram_signals',
        'schedule': 3600.0,  # 1 hour
    },
    
    # Обновление статистики каждые 6 часов
    'update_channel_statistics_6h': {
        'task': 'update_channel_statistics',
        'schedule': 21600.0,  # 6 hours
    },
    
    # Проверка результатов сигналов каждые 15 минут
    'check_signal_results_15min': {
        'task': 'check_signal_results',
        'schedule': 900.0,  # 15 minutes
    },
    
    # Получение ML-предсказаний каждые 30 минут
    'get_ml_predictions_30min': {
        'task': 'get_ml_predictions',
        'schedule': 1800.0,  # 30 minutes
    },
    
    # Мониторинг цен каждые 5 минут
    'monitor_prices_5min': {
        'task': 'monitor_prices',
        'schedule': 300.0,  # 5 minutes
    },
    
    # Статистика Telegram интеграции каждые 2 часа
    'get_telegram_stats_2h': {
        'task': 'get_telegram_stats',
        'schedule': 7200.0,  # 2 hours
    },
}

if __name__ == '__main__':
    celery_app.start()
