"""
Автоматический скрапер Telegram каналов для сбора сигналов
Работает без API, используя web scraping и альтернативные методы
"""
import asyncio
import aiohttp
import re
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
import json
import time
import random
from pathlib import Path

# Добавляем корневую директорию в sys.path
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from workers.real_data_config import TELEGRAM_API_ID, TELEGRAM_API_HASH
from workers.signal_patterns import SignalPatterns

logger = logging.getLogger(__name__)

class TelegramSignalScraper:
    """
    Автоматический скрапер сигналов с Telegram каналов
    Собирает данные за последние 3 месяца без использования API
    """
    
    def __init__(self):
        self.session = None
        self.signal_patterns = SignalPatterns()
        
        # Каналы для мониторинга
        self.target_channels = [
            "signalsbitcoinandethereum",
            "cryptosignals",
            "bitcoin_signals",
            "crypto_signals_pro",
            "trading_signals_crypto",
            "cryptotrading_signals",
            "bitcoin_ethereum_signals",
            "crypto_signals_daily"
        ]
        
        # User agents для имитации браузера
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
        ]
        
        # Прокси для обхода блокировок (опционально)
        self.proxies = [
            # Добавить прокси если нужно
        ]
    
    async def start_session(self):
        """Создание HTTP сессии"""
        if self.session is None:
            connector = aiohttp.TCPConnector(limit=10, limit_per_host=5)
            timeout = aiohttp.ClientTimeout(total=30)
            
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers={
                    'User-Agent': random.choice(self.user_agents),
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Accept-Encoding': 'gzip, deflate',
                    'Connection': 'keep-alive',
                }
            )
    
    async def close_session(self):
        """Закрытие HTTP сессии"""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def scrape_channel_messages(self, channel_username: str, months_back: int = 3) -> List[Dict[str, Any]]:
        """
        Скрапинг сообщений с канала за последние N месяцев
        
        Args:
            channel_username: Имя канала без @
            months_back: Количество месяцев назад для сбора
            
        Returns:
            Список сообщений с сигналами
        """
        await self.start_session()
        
        messages = []
        target_date = datetime.now() - timedelta(days=months_back * 30)
        
        try:
            # Метод 1: Telegram Web Scraping
            web_messages = await self._scrape_telegram_web(channel_username, target_date)
            messages.extend(web_messages)
            
            # Метод 2: Telegram Export Scraping
            export_messages = await self._scrape_telegram_export(channel_username, target_date)
            messages.extend(export_messages)
            
            # Метод 3: Alternative Sources
            alt_messages = await self._scrape_alternative_sources(channel_username, target_date)
            messages.extend(alt_messages)
            
            logger.info(f"Собрано {len(messages)} сообщений с канала {channel_username}")
            
        except Exception as e:
            logger.error(f"Ошибка скрапинга канала {channel_username}: {e}")
        
        return messages
    
    async def _scrape_telegram_web(self, channel_username: str, target_date: datetime) -> List[Dict[str, Any]]:
        """Скрапинг через Telegram Web"""
        messages = []
        
        try:
            # URL для Telegram Web
            url = f"https://t.me/s/{channel_username}"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Поиск сообщений
                    message_elements = soup.find_all('div', class_='tgme_widget_message')
                    
                    for element in message_elements:
                        try:
                            message_data = await self._parse_telegram_message(element, channel_username)
                            if message_data and message_data['date'] >= target_date:
                                messages.append(message_data)
                        except Exception as e:
                            logger.warning(f"Ошибка парсинга сообщения: {e}")
                            continue
                            
        except Exception as e:
            logger.error(f"Ошибка скрапинга Telegram Web: {e}")
        
        return messages
    
    async def _scrape_telegram_export(self, channel_username: str, target_date: datetime) -> List[Dict[str, Any]]:
        """Скрапинг через Telegram Export"""
        messages = []
        
        try:
            # Попытка получить данные через export
            export_url = f"https://t.me/s/{channel_username}?before="
            
            # Получаем несколько страниц
            for page in range(1, 11):  # 10 страниц
                try:
                    url = f"{export_url}{page * 20}"
                    async with self.session.get(url) as response:
                        if response.status == 200:
                            html = await response.text()
                            soup = BeautifulSoup(html, 'html.parser')
                            
                            message_elements = soup.find_all('div', class_='tgme_widget_message')
                            
                            for element in message_elements:
                                try:
                                    message_data = await self._parse_telegram_message(element, channel_username)
                                    if message_data and message_data['date'] >= target_date:
                                        messages.append(message_data)
                                    elif message_data and message_data['date'] < target_date:
                                        # Прерываем если достигли целевой даты
                                        return messages
                                except Exception as e:
                                    continue
                    
                    # Задержка между запросами
                    await asyncio.sleep(random.uniform(1, 3))
                    
                except Exception as e:
                    logger.warning(f"Ошибка страницы {page}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Ошибка скрапинга Telegram Export: {e}")
        
        return messages
    
    async def _scrape_alternative_sources(self, channel_username: str, target_date: datetime) -> List[Dict[str, Any]]:
        """Скрапинг через альтернативные источники"""
        messages = []
        
        try:
            # Метод 1: Telegram Archive Sites
            archive_urls = [
                f"https://telegram.me/s/{channel_username}",
                f"https://t.me/s/{channel_username}",
                f"https://telegram-store.com/channel/{channel_username}",
            ]
            
            for url in archive_urls:
                try:
                    async with self.session.get(url) as response:
                        if response.status == 200:
                            html = await response.text()
                            soup = BeautifulSoup(html, 'html.parser')
                            
                            # Поиск сообщений в разных форматах
                            message_elements = soup.find_all(['div', 'article'], class_=re.compile(r'message|post|entry'))
                            
                            for element in message_elements:
                                try:
                                    message_data = await self._parse_generic_message(element, channel_username)
                                    if message_data and message_data['date'] >= target_date:
                                        messages.append(message_data)
                                except Exception as e:
                                    continue
                    
                    await asyncio.sleep(random.uniform(2, 5))
                    
                except Exception as e:
                    logger.warning(f"Ошибка альтернативного источника {url}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Ошибка альтернативных источников: {e}")
        
        return messages
    
    async def _parse_telegram_message(self, element, channel_username: str) -> Optional[Dict[str, Any]]:
        """Парсинг сообщения из Telegram Web"""
        try:
            # Извлечение текста
            text_element = element.find('div', class_='tgme_widget_message_text')
            if not text_element:
                return None
            
            text = text_element.get_text(strip=True)
            
            # Извлечение даты
            date_element = element.find('time')
            if date_element:
                date_str = date_element.get('datetime', '')
                try:
                    date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                except:
                    date = datetime.now()
            else:
                date = datetime.now()
            
            # Извлечение ID сообщения
            message_id = element.get('data-post', '')
            
            # Извлечение изображений
            images = []
            img_elements = element.find_all('img')
            for img in img_elements:
                src = img.get('src', '')
                if src:
                    images.append(src)
            
            # Проверка на сигнал
            if self._is_signal_message(text):
                return {
                    'channel_username': channel_username,
                    'message_id': message_id,
                    'text': text,
                    'date': date,
                    'images': images,
                    'source': 'telegram_web'
                }
            
        except Exception as e:
            logger.warning(f"Ошибка парсинга Telegram сообщения: {e}")
        
        return None
    
    async def _parse_generic_message(self, element, channel_username: str) -> Optional[Dict[str, Any]]:
        """Парсинг сообщения из альтернативных источников"""
        try:
            # Извлечение текста
            text = element.get_text(strip=True)
            
            # Извлечение даты (попытка найти в разных форматах)
            date = datetime.now()
            date_elements = element.find_all(['time', 'span', 'div'], class_=re.compile(r'date|time'))
            for date_elem in date_elements:
                try:
                    date_str = date_elem.get_text(strip=True)
                    # Попытка парсинга разных форматов даты
                    for fmt in ['%Y-%m-%d', '%d.%m.%Y', '%Y-%m-%d %H:%M:%S']:
                        try:
                            date = datetime.strptime(date_str, fmt)
                            break
                        except:
                            continue
                except:
                    continue
            
            # Извлечение изображений
            images = []
            img_elements = element.find_all('img')
            for img in img_elements:
                src = img.get('src', '')
                if src:
                    images.append(src)
            
            # Проверка на сигнал
            if self._is_signal_message(text):
                return {
                    'channel_username': channel_username,
                    'message_id': f"alt_{hash(text)}",
                    'text': text,
                    'date': date,
                    'images': images,
                    'source': 'alternative'
                }
            
        except Exception as e:
            logger.warning(f"Ошибка парсинга generic сообщения: {e}")
        
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
                
                # Извлечение сигналов из изображений (если есть OCR)
                if message.get('images'):
                    for img_url in message['images']:
                        try:
                            # Скачиваем изображение
                            img_data = await self._download_image(img_url)
                            if img_data:
                                # Здесь можно добавить OCR обработку
                                # ocr_signals = await ocr_service.extract_signals_from_image(img_data)
                                # signals.extend(ocr_signals)
                                pass
                        except Exception as e:
                            logger.warning(f"Ошибка обработки изображения: {e}")
                
            except Exception as e:
                logger.warning(f"Ошибка извлечения сигналов из сообщения: {e}")
        
        return signals
    
    async def _download_image(self, url: str) -> Optional[bytes]:
        """Скачивание изображения"""
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    return await response.read()
        except Exception as e:
            logger.warning(f"Ошибка скачивания изображения {url}: {e}")
        
        return None
    
    async def scrape_all_channels(self, months_back: int = 3) -> Dict[str, List[Dict[str, Any]]]:
        """Скрапинг всех целевых каналов"""
        all_signals = {}
        
        for channel in self.target_channels:
            try:
                logger.info(f"Начинаем скрапинг канала: {channel}")
                
                # Скрапинг сообщений
                messages = await self.scrape_channel_messages(channel, months_back)
                
                # Извлечение сигналов
                signals = await self.extract_signals_from_messages(messages)
                
                all_signals[channel] = signals
                
                logger.info(f"Канал {channel}: собрано {len(messages)} сообщений, извлечено {len(signals)} сигналов")
                
                # Задержка между каналами
                await asyncio.sleep(random.uniform(5, 10))
                
            except Exception as e:
                logger.error(f"Ошибка скрапинга канала {channel}: {e}")
                all_signals[channel] = []
        
        await self.close_session()
        return all_signals

# Пример использования
async def main():
    scraper = TelegramSignalScraper()
    
    # Скрапинг всех каналов за последние 3 месяца
    results = await scraper.scrape_all_channels(months_back=3)
    
    # Сохранение результатов
    with open('scraped_signals.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2, default=str)
    
    print(f"Собрано сигналов:")
    for channel, signals in results.items():
        print(f"{channel}: {len(signals)} сигналов")

if __name__ == "__main__":
    asyncio.run(main())
