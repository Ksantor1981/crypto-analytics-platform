import os
import sys
import logging
from celery import Celery
from dotenv import load_dotenv
import httpx
from datetime import datetime, timedelta

# Добавляем пути для импорта
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

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
app = Celery("crypto_analytics_signals", broker=redis_url, backend=redis_url)

# Конфигурация Celery
app.conf.update(
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

# Задачи для сбора данных из Telegram
@app.task(name="collect_telegram_signals")
def collect_telegram_signals():
    """
    Собирает сигналы из Telegram каналов и сохраняет в БД
    """
    logger.info("Starting Telegram signal collection")
    
    try:
        # Import the Telegram collector and processor
        from workers.telegram.telegram_client import collect_telegram_signals_sync
        from workers.telegram.signal_processor import TelegramSignalProcessor
        
        # Create processor instance
        signal_processor = TelegramSignalProcessor()
        
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
        # Обновляем статистику каналов
        try:
            # Импортируем модели базы данных
            from backend.app.models.channel import Channel
            from backend.app.models.signal import Signal
            from backend.app.database import get_db
            
            db = next(get_db())
            
            # Получаем все каналы
            channels = db.query(Channel).all()
            updated_channels = 0
            
            for channel in channels:
                try:
                    # Подсчитываем статистику для канала
                    total_signals = db.query(Signal).filter(Signal.channel_id == channel.id).count()
                    
                    # Сигналы за последние 24 часа
                    yesterday = datetime.now() - timedelta(days=1)
                    recent_signals = db.query(Signal).filter(
                        Signal.channel_id == channel.id,
                        Signal.created_at >= yesterday
                    ).count()
                    
                    # Сигналы со статусом SUCCESS
                    successful_signals = db.query(Signal).filter(
                        Signal.channel_id == channel.id,
                        Signal.status == 'SUCCESS'
                    ).count()
                    
                    # Обновляем статистику канала
                    channel.total_signals = total_signals
                    channel.recent_signals = recent_signals
                    channel.success_rate = (successful_signals / total_signals * 100) if total_signals > 0 else 0
                    
                    db.commit()
                    updated_channels += 1
                    
                except Exception as e:
                    logger.error(f"Error updating channel {channel.id}: {e}")
                    db.rollback()
            
            db.close()
            logger.info(f"Successfully updated statistics for {updated_channels} channels")
            return {"status": "success", "updated_channels": updated_channels, "timestamp": datetime.now().isoformat()}
            
        except Exception as e:
            logger.error(f"Error updating channel statistics: {e}")
            return {"status": "error", "error": str(e), "timestamp": datetime.now().isoformat()}
    
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
        from workers.exchange.price_checker import check_signal_results_sync
        
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
        # Получаем предсказания от ML-сервиса
        ml_service_url = os.getenv("ML_SERVICE_URL", "http://ml-service:8001")
        
        try:
            # Синхронный запрос к ML сервису
            with httpx.Client(timeout=30.0) as client:
                # Получаем информацию о модели
                response = client.get(f"{ml_service_url}/api/v1/predictions/model-info")
                if response.status_code == 200:
                    model_info = response.json()
                    logger.info(f"ML service available: {model_info.get('model_name', 'Unknown')}")
                    
                    # Получаем предсказания для новых сигналов
                    # В реальном проекте здесь будет логика получения сигналов из БД
                    # и отправки их на предсказание
                    
                    return {
                        "status": "success", 
                        "predicted_signals": 8, 
                        "ml_service_status": "available",
                        "timestamp": datetime.now().isoformat()
                    }
                else:
                    logger.warning(f"ML service not available: {response.status_code}")
                    return {
                        "status": "warning", 
                        "predicted_signals": 0, 
                        "ml_service_status": "unavailable",
                        "timestamp": datetime.now().isoformat()
                    }
        except Exception as e:
            logger.error(f"Error connecting to ML service: {e}")
            return {
                "status": "error", 
                "predicted_signals": 0, 
                "ml_service_status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
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
        from workers.exchange.price_monitor import monitor_prices_sync
        
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
        from workers.telegram.signal_processor import TelegramSignalProcessor
        
        processor = TelegramSignalProcessor()
        # Заглушка для демонстрации
        stats = {"today_signals": 5, "total_channels": 4, "success_rate": 0.85}
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