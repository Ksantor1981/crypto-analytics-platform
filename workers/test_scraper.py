"""
Тестовый скрипт для проверки работы скрапера
"""
import asyncio
import logging
import json
from datetime import datetime
from pathlib import Path

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

async def test_web_scraping():
    """Тест web скрапинга"""
    try:
        from telegram.telegram_scraper import TelegramSignalScraper
        
        logger.info("Тестируем Web Scraping...")
        
        scraper = TelegramSignalScraper()
        
        # Тест на одном канале
        channel = "signalsbitcoinandethereum"
        logger.info(f"Скрапим канал: {channel}")
        
        messages = await scraper.scrape_channel_messages(channel, months_back=1)
        logger.info(f"Собрано сообщений: {len(messages)}")
        
        # Извлекаем сигналы
        signals = await scraper.extract_signals_from_messages(messages)
        logger.info(f"Извлечено сигналов: {len(signals)}")
        
        # Показываем первые 3 сигнала
        for i, signal in enumerate(signals[:3]):
            logger.info(f"Сигнал {i+1}: {signal}")
        
        # Сохраняем результаты
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"test_web_scraping_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump({
                'channel': channel,
                'messages_count': len(messages),
                'signals_count': len(signals),
                'signals': signals
            }, f, ensure_ascii=False, indent=2, default=str)
        
        logger.info(f"Результаты сохранены в {filename}")
        
        return len(signals) > 0
        
    except Exception as e:
        logger.error(f"Ошибка web скрапинга: {e}")
        return False

async def test_signal_patterns():
    """Тест извлечения сигналов из текста"""
    try:
        from signal_patterns import SignalPatterns
        
        logger.info("Тестируем извлечение сигналов из текста...")
        
        patterns = SignalPatterns()
        
        # Тестовые тексты
        test_texts = [
            "BTC/USDT LONG 45000 TP: 47000 SL: 44000",
            "ETHUSDT short 3200 target 3000 stop 3300",
            "🚀 BTC 45000 📈 47000 📉 44000",
            "Bitcoin Long Entry: $45,000 Target: $47,000 Stop: $44,000",
            "Вход BTC лонг 45000 цель 47000 стоп 44000"
        ]
        
        total_signals = 0
        
        for i, text in enumerate(test_texts):
            logger.info(f"Тест {i+1}: {text}")
            
            signals = patterns.extract_signals_from_text(
                text, 
                "test_channel", 
                f"test_message_{i}"
            )
            
            logger.info(f"Извлечено сигналов: {len(signals)}")
            for signal in signals:
                logger.info(f"  - {signal}")
            
            total_signals += len(signals)
        
        logger.info(f"Всего извлечено сигналов: {total_signals}")
        
        return total_signals > 0
        
    except Exception as e:
        logger.error(f"Ошибка тестирования паттернов: {e}")
        return False

async def main():
    """Основная функция тестирования"""
    logger.info("Начинаем тестирование скрапера...")
    
    # Тест 1: Извлечение сигналов из текста
    logger.info("=" * 50)
    logger.info("ТЕСТ 1: Извлечение сигналов из текста")
    logger.info("=" * 50)
    
    pattern_success = await test_signal_patterns()
    
    # Тест 2: Web скрапинг
    logger.info("=" * 50)
    logger.info("ТЕСТ 2: Web скрапинг")
    logger.info("=" * 50)
    
    web_success = await test_web_scraping()
    
    # Результаты
    logger.info("=" * 50)
    logger.info("РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ")
    logger.info("=" * 50)
    
    logger.info(f"Паттерны сигналов: {'✅ УСПЕШНО' if pattern_success else '❌ ОШИБКА'}")
    logger.info(f"Web скрапинг: {'✅ УСПЕШНО' if web_success else '❌ ОШИБКА'}")
    
    if pattern_success and web_success:
        logger.info("🎉 ВСЕ ТЕСТЫ ПРОШЛИ УСПЕШНО!")
    else:
        logger.info("⚠️ НЕКОТОРЫЕ ТЕСТЫ НЕ ПРОШЛИ")

if __name__ == "__main__":
    asyncio.run(main())
