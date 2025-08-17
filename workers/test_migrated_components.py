"""
Тестирование мигрированных компонентов из analyst_crypto
"""

import sys
import os
import asyncio
import logging
from pathlib import Path

# Добавляем пути для импортов
sys.path.append(str(Path(__file__).parent.parent))

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_signal_extractor():
    """Тестирование мигрированного Signal Extractor"""
    try:
        logger.info("🧪 Тестирование Signal Extractor...")
        
        from workers.shared.parsers.signal_extractor_migrated import MigratedSignalExtractor
        
        extractor = MigratedSignalExtractor()
        
        # Тестовые тексты
        test_texts = [
            "🚀 BTC LONG Entry: $45,000 Target: $48,000 SL: $42,000",
            "ETH SHORT @ 3200 TP: 3000 SL: 3300",
            "SOL/USDT BUY Entry: 100 Target: 120 Stop Loss: 95",
            "📈 Bitcoin Long Entry: 45000 Target: 48000 Stop: 42000",
            "📉 Ethereum Short @ 3200 TP: 3000 SL: 3300",
            "DOGE LONG Entry: 0.15 Target: 0.18 SL: 0.12"
        ]
        
        total_signals = 0
        successful_extractions = 0
        
        for i, text in enumerate(test_texts, 1):
            logger.info(f"\n📝 Тест {i}: {text}")
            
            signals = extractor.extract_from_text(text)
            
            if signals:
                successful_extractions += 1
                for signal in signals:
                    total_signals += 1
                    logger.info(f"✅ Извлечен сигнал: {signal.asset} {signal.direction}")
                    logger.info(f"   Entry: {signal.entry_price}, Target: {signal.target_price}, SL: {signal.stop_loss}")
                    logger.info(f"   Confidence: {signal.confidence_score}%")
            else:
                logger.warning(f"❌ Не удалось извлечь сигнал из текста {i}")
        
        success_rate = (successful_extractions / len(test_texts)) * 100
        logger.info(f"\n📊 Результаты тестирования Signal Extractor:")
        logger.info(f"   Всего тестов: {len(test_texts)}")
        logger.info(f"   Успешных извлечений: {successful_extractions}")
        logger.info(f"   Всего сигналов: {total_signals}")
        logger.info(f"   Успешность: {success_rate:.1f}%")
        
        return success_rate >= 80  # Требуем минимум 80% успешности
        
    except Exception as e:
        logger.error(f"❌ Ошибка тестирования Signal Extractor: {e}")
        return False

def test_telegram_channels_config():
    """Тестирование конфигурации каналов"""
    try:
        logger.info("🧪 Тестирование конфигурации каналов...")
        
        import json
        config_path = Path(__file__).parent.parent / "database" / "seeds" / "telegram_channels.json"
        
        if not config_path.exists():
            logger.error(f"❌ Файл конфигурации не найден: {config_path}")
            return False
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        channels = config.get('telegram_channels', {}).get('channels', [])
        
        logger.info(f"📋 Найдено каналов: {len(channels)}")
        
        for channel in channels:
            logger.info(f"   📺 {channel.get('name')} (@{channel.get('username')})")
            logger.info(f"      Категория: {channel.get('category')}")
            logger.info(f"      Приоритет: {channel.get('priority')}")
            logger.info(f"      Ожидаемая точность: {channel.get('expected_accuracy')}")
            logger.info(f"      Статус: {channel.get('status')}")
        
        return len(channels) > 0
        
    except Exception as e:
        logger.error(f"❌ Ошибка тестирования конфигурации каналов: {e}")
        return False

def test_telegram_collector_structure():
    """Тестирование структуры Telegram Collector"""
    try:
        logger.info("🧪 Тестирование структуры Telegram Collector...")
        
        from workers.telegram.telegram_collector_migrated import MigratedTelegramCollector, CHANNELS
        
        # Проверяем наличие каналов
        logger.info(f"📺 Каналы для мониторинга: {len(CHANNELS)}")
        for channel in CHANNELS:
            logger.info(f"   - {channel}")
        
        # Проверяем наличие методов
        collector_class = MigratedTelegramCollector
        required_methods = [
            'process_message',
            'extract_signal_from_text', 
            'parse_forecast',
            'extract_entry_price',
            'extract_stop_loss',
            'calculate_confidence',
            'start_collection'
        ]
        
        missing_methods = []
        for method in required_methods:
            if not hasattr(collector_class, method):
                missing_methods.append(method)
        
        if missing_methods:
            logger.error(f"❌ Отсутствуют методы: {missing_methods}")
            return False
        
        logger.info("✅ Все необходимые методы присутствуют")
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка тестирования структуры Telegram Collector: {e}")
        return False

def test_celery_tasks():
    """Тестирование Celery tasks"""
    try:
        logger.info("🧪 Тестирование Celery tasks...")
        
        from workers.telegram.telegram_tasks import (
            start_telegram_collector,
            process_telegram_message,
            test_telegram_connection,
            get_telegram_channels_status
        )
        
        # Проверяем наличие всех tasks
        tasks = [
            start_telegram_collector,
            process_telegram_message,
            test_telegram_connection,
            get_telegram_channels_status
        ]
        
        for task in tasks:
            if not hasattr(task, 'delay'):
                logger.error(f"❌ Task {task.__name__} не является Celery task")
                return False
        
        logger.info("✅ Все Celery tasks корректно определены")
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка тестирования Celery tasks: {e}")
        return False

def main():
    """Основная функция тестирования"""
    logger.info("🚀 Начало тестирования мигрированных компонентов...")
    
    tests = [
        ("Signal Extractor", test_signal_extractor),
        ("Telegram Channels Config", test_telegram_channels_config),
        ("Telegram Collector Structure", test_telegram_collector_structure),
        ("Celery Tasks", test_celery_tasks),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"🧪 ТЕСТ: {test_name}")
        logger.info(f"{'='*50}")
        
        try:
            result = test_func()
            results.append((test_name, result))
            
            if result:
                logger.info(f"✅ {test_name}: ПРОЙДЕН")
            else:
                logger.error(f"❌ {test_name}: ПРОВАЛЕН")
                
        except Exception as e:
            logger.error(f"❌ {test_name}: ОШИБКА - {e}")
            results.append((test_name, False))
    
    # Итоговый отчет
    logger.info(f"\n{'='*50}")
    logger.info("📊 ИТОГОВЫЙ ОТЧЕТ")
    logger.info(f"{'='*50}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ ПРОЙДЕН" if result else "❌ ПРОВАЛЕН"
        logger.info(f"   {test_name}: {status}")
    
    logger.info(f"\n📈 Результат: {passed}/{total} тестов пройдено")
    
    if passed == total:
        logger.info("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ! Миграция успешна!")
        return True
    else:
        logger.error(f"⚠️ {total - passed} тестов провалено. Требуется доработка.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
