"""
Celery tasks для мигрированного Telegram Collector
"""

import asyncio
import logging
from celery import Celery
from sqlalchemy.orm import Session

# Импорты с fallback
try:
    from backend.app.core.database import SessionLocal
    from .telegram_collector_migrated import MigratedTelegramCollector
except ImportError as e:
    print(f"⚠️ Не удалось импортировать backend модули: {e}")
    SessionLocal = None
    MigratedTelegramCollector = None

logger = logging.getLogger(__name__)

# Создаем Celery app
celery_app = Celery('telegram_workers')

# Конфигурация Celery
celery_app.conf.update(
    broker_url='redis://localhost:6379/0',
    result_backend='redis://localhost:6379/0',
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)

@celery_app.task
def start_telegram_collector():
    """
    Запуск Telegram коллектора как Celery task
    """
    try:
        logger.info("🚀 Запуск мигрированного Telegram коллектора...")
        
        # Создаем сессию БД (с fallback)
        if SessionLocal:
            db = SessionLocal()
        else:
            logger.warning("⚠️ SessionLocal недоступен, используем None")
            db = None
        
        try:
            # Создаем коллектор (с fallback)
            if MigratedTelegramCollector:
                collector = MigratedTelegramCollector(db)
            else:
                logger.error("❌ MigratedTelegramCollector недоступен")
                return {"status": "error", "message": "MigratedTelegramCollector not available"}
            
            # Запускаем сбор в отдельном event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                loop.run_until_complete(collector.start_collection())
            finally:
                loop.close()
                
        finally:
            db.close()
            
        logger.info("✅ Telegram коллектор завершил работу")
        return {"status": "success", "message": "Telegram collector started successfully"}
        
    except Exception as e:
        logger.error(f"❌ Ошибка запуска Telegram коллектора: {e}")
        return {"status": "error", "message": str(e)}

@celery_app.task
def process_telegram_message(message_data: dict):
    """
    Обработка отдельного Telegram сообщения
    """
    try:
        logger.info(f"📨 Обработка Telegram сообщения: {message_data.get('message_id')}")
        
        # Создаем сессию БД (с fallback)
        if SessionLocal:
            db = SessionLocal()
        else:
            logger.warning("⚠️ SessionLocal недоступен, используем None")
            db = None
        
        try:
            # Создаем коллектор (с fallback)
            if MigratedTelegramCollector:
                collector = MigratedTelegramCollector(db)
            else:
                logger.error("❌ MigratedTelegramCollector недоступен")
                return {"status": "error", "message": "MigratedTelegramCollector not available"}
            
            # Создаем mock message object
            class MockMessage:
                def __init__(self, data):
                    self.text = data.get('text')
                    self.id = data.get('message_id')
                    self.date = data.get('date')
                    self.media = data.get('media')
            
            message = MockMessage(message_data)
            channel_username = message_data.get('channel_username')
            
            # Обрабатываем сообщение
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                result = loop.run_until_complete(
                    collector.process_message(message, channel_username)
                )
                
                if result:
                    logger.info(f"✅ Сообщение обработано успешно: {result}")
                    return {"status": "success", "signal": result}
                else:
                    logger.info("⏭️ Сообщение не содержит сигналов")
                    return {"status": "no_signal", "message": "No signals found"}
                    
            finally:
                loop.close()
                
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"❌ Ошибка обработки сообщения: {e}")
        return {"status": "error", "message": str(e)}

@celery_app.task
def test_telegram_connection():
    """
    Тест подключения к Telegram API
    """
    try:
        import os
        from telethon import TelegramClient
        
        api_id = os.getenv('TELEGRAM_API_ID')
        api_hash = os.getenv('TELEGRAM_API_HASH')
        
        if not api_id or not api_hash:
            return {"status": "error", "message": "TELEGRAM_API_ID and TELEGRAM_API_HASH not set"}
        
        # Тестируем подключение
        client = TelegramClient('test_session', api_id, api_hash)
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            loop.run_until_complete(client.connect())
            
            if client.is_connected():
                loop.run_until_complete(client.disconnect())
                return {"status": "success", "message": "Telegram connection successful"}
            else:
                return {"status": "error", "message": "Failed to connect to Telegram"}
                
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"❌ Ошибка тестирования подключения: {e}")
        return {"status": "error", "message": str(e)}

@celery_app.task
def get_telegram_channels_status():
    """
    Получение статуса каналов
    """
    try:
        from .telegram_collector_migrated import CHANNELS
        
        return {
            "status": "success",
            "channels": CHANNELS,
            "total_channels": len(CHANNELS),
            "monitoring_enabled": True
        }
        
    except Exception as e:
        logger.error(f"❌ Ошибка получения статуса каналов: {e}")
        return {"status": "error", "message": str(e)}

# Команды для запуска:
# celery -A workers.telegram.telegram_tasks worker --loglevel=info
# celery -A workers.telegram.telegram_tasks start_telegram_collector.delay()
