"""
Основной скрипт для автоматического скрапинга сигналов с Telegram каналов
Собирает данные за последние 3 месяца без использования API
"""
import asyncio
import logging
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# Добавляем корневую директорию в sys.path
sys.path.append(str(Path(__file__).parent.parent))

from workers.telegram.telegram_scraper import TelegramSignalScraper
from workers.telegram.selenium_scraper import SeleniumTelegramScraper

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('signal_scraping.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class SignalScrapingOrchestrator:
    """
    Оркестратор для автоматического скрапинга сигналов
    """
    
    def __init__(self):
        self.web_scraper = TelegramSignalScraper()
        self.selenium_scraper = SeleniumTelegramScraper(headless=True)
        
        # Целевые каналы для мониторинга
        self.target_channels = [
            "signalsbitcoinandethereum",  # Основной канал
            "cryptosignals",
            "bitcoin_signals", 
            "crypto_signals_pro",
            "trading_signals_crypto",
            "cryptotrading_signals",
            "bitcoin_ethereum_signals",
            "crypto_signals_daily"
        ]
    
    async def run_comprehensive_scraping(self, months_back: int = 3) -> Dict[str, List[Dict[str, Any]]]:
        """
        Комплексный скрапинг всех каналов
        
        Args:
            months_back: Количество месяцев назад для сбора
            
        Returns:
            Словарь с сигналами по каналам
        """
        logger.info(f"Начинаем комплексный скрапинг за последние {months_back} месяцев")
        
        all_signals = {}
        
        for channel in self.target_channels:
            try:
                logger.info(f"Обрабатываем канал: {channel}")
                channel_signals = []
                
                # Метод 1: Web Scraping
                try:
                    logger.info(f"Метод 1: Web Scraping для {channel}")
                    web_signals = await self._scrape_with_web_method(channel, months_back)
                    channel_signals.extend(web_signals)
                    logger.info(f"Web Scraping: {len(web_signals)} сигналов")
                except Exception as e:
                    logger.error(f"Ошибка Web Scraping для {channel}: {e}")
                
                # Метод 2: Selenium (если web scraping не дал результатов)
                if len(channel_signals) < 10:  # Если мало сигналов
                    try:
                        logger.info(f"Метод 2: Selenium для {channel}")
                        selenium_signals = await self._scrape_with_selenium_method(channel, months_back)
                        channel_signals.extend(selenium_signals)
                        logger.info(f"Selenium: {len(selenium_signals)} сигналов")
                    except Exception as e:
                        logger.error(f"Ошибка Selenium для {channel}: {e}")
                
                # Удаление дубликатов
                unique_signals = self._remove_duplicate_signals(channel_signals)
                
                all_signals[channel] = unique_signals
                
                logger.info(f"Канал {channel}: итого {len(unique_signals)} уникальных сигналов")
                
                # Задержка между каналами
                await asyncio.sleep(5)
                
            except Exception as e:
                logger.error(f"Критическая ошибка обработки канала {channel}: {e}")
                all_signals[channel] = []
        
        return all_signals
    
    async def _scrape_with_web_method(self, channel: str, months_back: int) -> List[Dict[str, Any]]:
        """Скрапинг через web метод"""
        try:
            messages = await self.web_scraper.scrape_channel_messages(channel, months_back)
            signals = await self.web_scraper.extract_signals_from_messages(messages)
            return signals
        except Exception as e:
            logger.error(f"Ошибка web метода для {channel}: {e}")
            return []
    
    async def _scrape_with_selenium_method(self, channel: str, months_back: int) -> List[Dict[str, Any]]:
        """Скрапинг через Selenium метод"""
        try:
            messages = await self.selenium_scraper.scrape_channel_with_selenium(channel, months_back)
            signals = await self.selenium_scraper.extract_signals_from_messages(messages)
            return signals
        except Exception as e:
            logger.error(f"Ошибка Selenium метода для {channel}: {e}")
            return []
    
    def _remove_duplicate_signals(self, signals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Удаление дубликатов сигналов"""
        unique_signals = []
        seen = set()
        
        for signal in signals:
            # Создаем ключ для сравнения
            key = (
                signal.get('trading_pair', ''),
                signal.get('direction', ''),
                signal.get('entry_price', 0),
                signal.get('target_price', 0),
                signal.get('stop_loss', 0),
                signal.get('date', '')
            )
            
            if key not in seen:
                seen.add(key)
                unique_signals.append(signal)
        
        return unique_signals
    
    def save_results(self, results: Dict[str, List[Dict[str, Any]]], filename: str = None):
        """Сохранение результатов в файл"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"scraped_signals_{timestamp}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2, default=str)
            
            logger.info(f"Результаты сохранены в {filename}")
            
            # Статистика
            total_signals = sum(len(signals) for signals in results.values())
            logger.info(f"Всего собрано сигналов: {total_signals}")
            
            for channel, signals in results.items():
                logger.info(f"{channel}: {len(signals)} сигналов")
                
        except Exception as e:
            logger.error(f"Ошибка сохранения результатов: {e}")
    
    async def run_single_channel_scraping(self, channel: str, months_back: int = 3) -> List[Dict[str, Any]]:
        """Скрапинг одного канала"""
        logger.info(f"Скрапинг одного канала: {channel}")
        
        signals = []
        
        # Web Scraping
        try:
            web_signals = await self._scrape_with_web_method(channel, months_back)
            signals.extend(web_signals)
            logger.info(f"Web Scraping: {len(web_signals)} сигналов")
        except Exception as e:
            logger.error(f"Ошибка Web Scraping: {e}")
        
        # Selenium (если нужно)
        if len(signals) < 5:
            try:
                selenium_signals = await self._scrape_with_selenium_method(channel, months_back)
                signals.extend(selenium_signals)
                logger.info(f"Selenium: {len(selenium_signals)} сигналов")
            except Exception as e:
                logger.error(f"Ошибка Selenium: {e}")
        
        # Удаление дубликатов
        unique_signals = self._remove_duplicate_signals(signals)
        
        logger.info(f"Итого для {channel}: {len(unique_signals)} уникальных сигналов")
        
        return unique_signals

async def main():
    """Основная функция"""
    orchestrator = SignalScrapingOrchestrator()
    
    # Проверяем аргументы командной строки
    if len(sys.argv) > 1:
        if sys.argv[1] == "--single":
            # Скрапинг одного канала
            if len(sys.argv) > 2:
                channel = sys.argv[2]
                months = int(sys.argv[3]) if len(sys.argv) > 3 else 3
                
                signals = await orchestrator.run_single_channel_scraping(channel, months)
                
                # Сохранение результатов
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"scraped_signals_{channel}_{timestamp}.json"
                
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump({channel: signals}, f, ensure_ascii=False, indent=2, default=str)
                
                print(f"Собрано {len(signals)} сигналов для канала {channel}")
                print(f"Результаты сохранены в {filename}")
            else:
                print("Использование: python run_signal_scraping.py --single <channel_name> [months]")
        else:
            print("Неизвестный аргумент. Используйте --single для одного канала")
    else:
        # Комплексный скрапинг всех каналов
        print("Начинаем комплексный скрапинг всех каналов...")
        
        results = await orchestrator.run_comprehensive_scraping(months_back=3)
        
        # Сохранение результатов
        orchestrator.save_results(results)
        
        # Вывод статистики
        total_signals = sum(len(signals) for signals in results.values())
        print(f"\n=== СТАТИСТИКА СКРАПИНГА ===")
        print(f"Всего каналов: {len(results)}")
        print(f"Всего сигналов: {total_signals}")
        print(f"Среднее сигналов на канал: {total_signals / len(results):.1f}")
        
        for channel, signals in results.items():
            print(f"{channel}: {len(signals)} сигналов")

if __name__ == "__main__":
    asyncio.run(main())
