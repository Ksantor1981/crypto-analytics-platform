"""
Проверка публичных каналов
"""
import asyncio
import aiohttp
import logging
from telegram.telegram_scraper import TelegramSignalScraper

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def check_public_channels():
    """Проверка публичных каналов"""
    
    # Список публичных каналов для тестирования
    public_channels = [
        "binanceupdates",
        "coinbase",
        "cryptocom",
        "bitcoin",
        "ethereum"
    ]
    
    scraper = TelegramSignalScraper()
    
    for channel in public_channels:
        try:
            logger.info(f"Проверяем канал: {channel}")
            
            # Пробуем получить сообщения
            messages = await scraper.scrape_channel_messages(channel, months_back=1)
            logger.info(f"  Сообщений: {len(messages)}")
            
            if messages:
                # Показываем последние 3 сообщения
                for i, msg in enumerate(messages[:3]):
                    logger.info(f"  Сообщение {i+1}: {msg.get('text', '')[:100]}...")
                
                # Извлекаем сигналы
                signals = await scraper.extract_signals_from_messages(messages)
                logger.info(f"  Сигналов: {len(signals)}")
                
                if signals:
                    for signal in signals:
                        logger.info(f"    ✅ {signal['trading_pair']} {signal['direction']} Entry:{signal['entry_price']}")
            
            logger.info("-" * 50)
            
        except Exception as e:
            logger.error(f"Ошибка с каналом {channel}: {e}")

if __name__ == "__main__":
    asyncio.run(check_public_channels())
