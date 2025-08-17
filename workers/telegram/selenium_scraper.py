"""
Selenium скрапер для Telegram каналов
Обрабатывает динамический контент и JavaScript
"""
import asyncio
import logging
import json
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path
import time
import random

# Selenium imports
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Добавляем корневую директорию в sys.path
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from workers.signal_patterns import SignalPatterns

logger = logging.getLogger(__name__)

class SeleniumTelegramScraper:
    """
    Selenium скрапер для Telegram каналов
    Обрабатывает динамический контент и JavaScript
    """
    
    def __init__(self, headless: bool = True):
        self.driver = None
        self.signal_patterns = SignalPatterns()
        self.headless = headless
        
        # Каналы для мониторинга
        self.target_channels = [
            "signalsbitcoinandethereum",
            "cryptosignals",
            "bitcoin_signals",
            "crypto_signals_pro",
            "trading_signals_crypto"
        ]
    
    def setup_driver(self):
        """Настройка Chrome драйвера"""
        chrome_options = Options()
        
        if self.headless:
            chrome_options.add_argument("--headless")
        
        # Настройки для обхода детекции
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # User agent
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        # Прокси (опционально)
        # chrome_options.add_argument("--proxy-server=http://proxy:port")
        
        self.driver = webdriver.Chrome(options=chrome_options)
        
        # Скрываем признаки автоматизации
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    def close_driver(self):
        """Закрытие драйвера"""
        if self.driver:
            self.driver.quit()
            self.driver = None
    
    async def scrape_channel_with_selenium(self, channel_username: str, months_back: int = 3) -> List[Dict[str, Any]]:
        """
        Скрапинг канала с помощью Selenium
        
        Args:
            channel_username: Имя канала без @
            months_back: Количество месяцев назад для сбора
            
        Returns:
            Список сообщений с сигналами
        """
        if not self.driver:
            self.setup_driver()
        
        messages = []
        target_date = datetime.now() - timedelta(days=months_back * 30)
        
        try:
            # URL канала
            url = f"https://t.me/s/{channel_username}"
            
            logger.info(f"Открываем канал: {url}")
            self.driver.get(url)
            
            # Ждем загрузки страницы
            await asyncio.sleep(3)
            
            # Скроллим вниз для загрузки большего количества сообщений
            await self._scroll_to_load_messages(target_date)
            
            # Парсим сообщения
            messages = await self._parse_messages_from_page(channel_username, target_date)
            
            logger.info(f"Собрано {len(messages)} сообщений с канала {channel_username}")
            
        except Exception as e:
            logger.error(f"Ошибка скрапинга канала {channel_username}: {e}")
        
        return messages
    
    async def _scroll_to_load_messages(self, target_date: datetime):
        """Скроллинг для загрузки большего количества сообщений"""
        try:
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            scroll_attempts = 0
            max_attempts = 20
            
            while scroll_attempts < max_attempts:
                # Скроллим вниз
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                
                # Ждем загрузки
                await asyncio.sleep(2)
                
                # Проверяем новые сообщения
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                
                if new_height == last_height:
                    scroll_attempts += 1
                else:
                    scroll_attempts = 0
                    last_height = new_height
                
                # Проверяем дату последнего сообщения
                try:
                    last_message_date = await self._get_last_message_date()
                    if last_message_date and last_message_date < target_date:
                        logger.info("Достигнута целевая дата, прекращаем скроллинг")
                        break
                except:
                    pass
                
                # Случайная задержка
                await asyncio.sleep(random.uniform(1, 3))
                
        except Exception as e:
            logger.warning(f"Ошибка скроллинга: {e}")
    
    async def _get_last_message_date(self) -> Optional[datetime]:
        """Получение даты последнего сообщения"""
        try:
            # Ищем последнее сообщение
            messages = self.driver.find_elements(By.CLASS_NAME, "tgme_widget_message")
            if messages:
                last_message = messages[-1]
                
                # Ищем дату
                date_element = last_message.find_element(By.TAG_NAME, "time")
                date_str = date_element.get_attribute("datetime")
                
                if date_str:
                    return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                    
        except Exception as e:
            logger.warning(f"Ошибка получения даты: {e}")
        
        return None
    
    async def _parse_messages_from_page(self, channel_username: str, target_date: datetime) -> List[Dict[str, Any]]:
        """Парсинг сообщений со страницы"""
        messages = []
        
        try:
            # Ищем все сообщения
            message_elements = self.driver.find_elements(By.CLASS_NAME, "tgme_widget_message")
            
            for element in message_elements:
                try:
                    message_data = await self._parse_single_message(element, channel_username)
                    if message_data and message_data['date'] >= target_date:
                        messages.append(message_data)
                    elif message_data and message_data['date'] < target_date:
                        # Прерываем если достигли целевой даты
                        break
                        
                except Exception as e:
                    logger.warning(f"Ошибка парсинга сообщения: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Ошибка парсинга страницы: {e}")
        
        return messages
    
    async def _parse_single_message(self, element, channel_username: str) -> Optional[Dict[str, Any]]:
        """Парсинг одного сообщения"""
        try:
            # Извлечение текста
            try:
                text_element = element.find_element(By.CLASS_NAME, "tgme_widget_message_text")
                text = text_element.text
            except NoSuchElementException:
                text = ""
            
            # Извлечение даты
            try:
                date_element = element.find_element(By.TAG_NAME, "time")
                date_str = date_element.get_attribute("datetime")
                if date_str:
                    date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                else:
                    date = datetime.now()
            except:
                date = datetime.now()
            
            # Извлечение ID сообщения
            try:
                message_id = element.get_attribute("data-post")
            except:
                message_id = f"sel_{hash(text)}"
            
            # Извлечение изображений
            images = []
            try:
                img_elements = element.find_elements(By.TAG_NAME, "img")
                for img in img_elements:
                    src = img.get_attribute("src")
                    if src:
                        images.append(src)
            except:
                pass
            
            # Проверка на сигнал
            if self._is_signal_message(text):
                return {
                    'channel_username': channel_username,
                    'message_id': message_id,
                    'text': text,
                    'date': date,
                    'images': images,
                    'source': 'selenium'
                }
            
        except Exception as e:
            logger.warning(f"Ошибка парсинга сообщения: {e}")
        
        return None
    
    def _is_signal_message(self, text: str) -> bool:
        """Проверка, является ли сообщение сигналом"""
        if not text:
            return False
        
        # Ключевые слова для сигналов
        signal_keywords = [
            'long', 'short', 'buy', 'sell', 'entry', 'target', 'stop loss',
            'btc', 'eth', 'usdt', 'crypto', 'signal', 'trade',
            'лонг', 'шорт', 'покупка', 'продажа', 'вход', 'цель', 'стоп',
            '🚀', '📈', '📉', '💰', '💎'
        ]
        
        text_lower = text.lower()
        
        # Проверка наличия ключевых слов
        keyword_count = sum(1 for keyword in signal_keywords if keyword in text_lower)
        
        # Проверка наличия цен (числа с точкой)
        price_pattern = r'\d+\.?\d*'
        prices = re.findall(price_pattern, text)
        
        # Проверка наличия торговых пар
        pair_pattern = r'\b[A-Z]{2,10}/[A-Z]{2,10}\b'
        pairs = re.findall(pair_pattern, text.upper())
        
        # Сообщение считается сигналом если:
        # 1. Есть ключевые слова И
        # 2. Есть цены ИЛИ торговые пары
        return keyword_count >= 2 and (len(prices) >= 2 or len(pairs) >= 1)
    
    async def extract_signals_from_messages(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Извлечение сигналов из сообщений"""
        signals = []
        
        for message in messages:
            try:
                # Извлечение сигналов из текста
                text_signals = self.signal_patterns.extract_signals_from_text(
                    message['text'], 
                    message['channel_username'],
                    message['message_id']
                )
                signals.extend(text_signals)
                
            except Exception as e:
                logger.warning(f"Ошибка извлечения сигналов из сообщения: {e}")
        
        return signals
    
    async def scrape_all_channels(self, months_back: int = 3) -> Dict[str, List[Dict[str, Any]]]:
        """Скрапинг всех целевых каналов"""
        all_signals = {}
        
        try:
            for channel in self.target_channels:
                try:
                    logger.info(f"Начинаем скрапинг канала: {channel}")
                    
                    # Скрапинг сообщений
                    messages = await self.scrape_channel_with_selenium(channel, months_back)
                    
                    # Извлечение сигналов
                    signals = await self.extract_signals_from_messages(messages)
                    
                    all_signals[channel] = signals
                    
                    logger.info(f"Канал {channel}: собрано {len(messages)} сообщений, извлечено {len(signals)} сигналов")
                    
                    # Задержка между каналами
                    await asyncio.sleep(random.uniform(10, 20))
                    
                except Exception as e:
                    logger.error(f"Ошибка скрапинга канала {channel}: {e}")
                    all_signals[channel] = []
        
        finally:
            self.close_driver()
        
        return all_signals

# Пример использования
async def main():
    scraper = SeleniumTelegramScraper(headless=True)
    
    # Скрапинг всех каналов за последние 3 месяца
    results = await scraper.scrape_all_channels(months_back=3)
    
    # Сохранение результатов
    with open('selenium_scraped_signals.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2, default=str)
    
    print(f"Собрано сигналов:")
    for channel, signals in results.items():
        print(f"{channel}: {len(signals)} сигналов")

if __name__ == "__main__":
    asyncio.run(main())
