import os
import logging
from celery import Celery
from dotenv import load_dotenv
import httpx
from datetime import datetime, timedelta

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Настройка Celery
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
app = Celery("crypto_analytics_tasks", broker=redis_url, backend=redis_url)

# Конфигурация Celery
app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    worker_hijack_root_logger=False,
)

# Задачи для сбора данных из Telegram
@app.task(name="collect_telegram_signals")
def collect_telegram_signals():
    """
    Собирает сигналы из Telegram каналов и сохраняет в БД
    """
    logger.info("Starting Telegram signal collection")
    
    try:
        # Import the Telegram collector and processor
        from telegram.telegram_client import collect_telegram_signals_sync
        from telegram.signal_processor import signal_processor
        
        # Collect signals using our Telegram client
        result = collect_telegram_signals_sync()
        logger.info(f"Successfully collected {result.get('total_signals_collected', 0)} signals from Telegram")
        
        # Process and save signals to database
        if result.get('status') == 'success' and result.get('signals'):
            processing_result = signal_processor.process_signals(result['signals'])
            logger.info(f"Processed {processing_result.get('processed', 0)} signals, saved {processing_result.get('saved', 0)}")
            
            # Merge results
            result.update({
                'processing_result': processing_result,
                'signals_saved': processing_result.get('saved', 0),
                'processing_errors': processing_result.get('errors', 0)
            })
        
        return result
    
    except Exception as e:
        logger.error(f"Error collecting Telegram signals: {str(e)}")
        return {"status": "error", "error": str(e), "timestamp": datetime.now().isoformat()}

# Задача для обновления статистики каналов
@app.task(name="update_channel_statistics")
def update_channel_statistics():
    """
    Обновляет статистику каналов на основе последних сигналов
    """
    logger.info("Starting channel statistics update")
    
    try:
        # В реальном проекте здесь будет код для обновления статистики
        # Например:
        # from statistics_calculator import ChannelStatisticsCalculator
        # calculator = ChannelStatisticsCalculator()
        # stats = calculator.update_all_channels()
        
        # Заглушка для демонстрации
        logger.info("Successfully updated channel statistics")
        return {"status": "success", "updated_channels": 5, "timestamp": datetime.now().isoformat()}
    
    except Exception as e:
        logger.error(f"Error updating channel statistics: {str(e)}")
        return {"status": "error", "error": str(e), "timestamp": datetime.now().isoformat()}

# Задача для проверки результатов сигналов
@app.task(name="check_signal_results")
def check_signal_results():
    """
    Проверяет результаты сигналов, сравнивая с текущими ценами
    """
    logger.info("Starting signal results check")
    
    try:
        # Import the price checker
        from exchange.price_checker import check_signal_results_sync
        
        # Check signal execution results
        result = check_signal_results_sync()
        logger.info(f"Successfully checked {result.get('signals_checked', 0)} signal results")
        
        return result
    
    except Exception as e:
        logger.error(f"Error checking signal results: {str(e)}")
        return {"status": "error", "error": str(e), "timestamp": datetime.now().isoformat()}

# Задача для получения ML-предсказаний для сигналов
@app.task(name="get_ml_predictions")
def get_ml_predictions():
    """
    Получает ML-предсказания для новых сигналов
    """
    logger.info("Starting ML predictions for signals")
    
    try:
        # В реальном проекте здесь будет код для получения предсказаний от ML-сервиса
        # Например:
        # from ml_client import MLServiceClient
        # client = MLServiceClient()
        # predictions = client.get_predictions_for_new_signals()
        
        # Заглушка для демонстрации
        logger.info("Successfully got ML predictions")
        return {"status": "success", "predicted_signals": 8, "timestamp": datetime.now().isoformat()}
    
    except Exception as e:
        logger.error(f"Error getting ML predictions: {str(e)}")
        return {"status": "error", "error": str(e), "timestamp": datetime.now().isoformat()}

# Задача для мониторинга цен в реальном времени
@app.task(name="monitor_prices")
def monitor_prices():
    """
    Мониторит цены активов в реальном времени и обновляет статусы сигналов
    """
    logger.info("Starting real-time price monitoring")
    
    try:
        # Import the price monitor
        from exchange.price_monitor import monitor_prices_sync
        
        # Monitor prices and update signal statuses
        result = monitor_prices_sync()
        logger.info(f"Successfully monitored prices for {result.get('assets_monitored', 0)} assets")
        
        return result
    
    except Exception as e:
        logger.error(f"Error monitoring prices: {str(e)}")
        return {"status": "error", "error": str(e), "timestamp": datetime.now().isoformat()}

# Задача для получения статистики Telegram интеграции
@app.task(name="get_telegram_stats")
def get_telegram_stats():
    """
    Получает статистику работы Telegram интеграции
    """
    logger.info("Getting Telegram integration statistics")
    
    try:
        from telegram.signal_processor import signal_processor
        
        stats = signal_processor.get_processing_stats()
        logger.info(f"Telegram stats: {stats.get('today_signals', 0)} signals today")
        
        return stats
    
    except Exception as e:
        logger.error(f"Error getting Telegram stats: {str(e)}")
        return {"status": "error", "error": str(e), "timestamp": datetime.now().isoformat()}

# Настройка периодических задач
@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    # Сбор сигналов каждый час
    sender.add_periodic_task(
        3600.0,
        collect_telegram_signals.s(),
        name="collect_telegram_signals_hourly",
    )
    
    # Обновление статистики каждые 6 часов
    sender.add_periodic_task(
        21600.0,
        update_channel_statistics.s(),
        name="update_channel_statistics_6h",
    )
    
    # Проверка результатов сигналов каждые 15 минут
    sender.add_periodic_task(
        900.0,
        check_signal_results.s(),
        name="check_signal_results_15min",
    )
    
    # Получение ML-предсказаний каждые 30 минут
    sender.add_periodic_task(
        1800.0,
        get_ml_predictions.s(),
        name="get_ml_predictions_30min",
    )
    
    # Мониторинг цен каждые 5 минут
    sender.add_periodic_task(
        300.0,
        monitor_prices.s(),
        name="monitor_prices_5min",
    )
    
    # Статистика Telegram интеграции каждые 2 часа
    sender.add_periodic_task(
        7200.0,
        get_telegram_stats.s(),
        name="get_telegram_stats_2h",
    ) 