"""
Авторизованный скрапер Telegram с использованием пользовательского аккаунта
"""
import asyncio
import logging
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from telethon import TelegramClient, events
from telethon.tl.types import Channel, Message
from telethon.errors import SessionPasswordNeededError, PhoneCodeInvalidError

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from signal_patterns import SignalPatterns

logger = logging.getLogger(__name__)

class AuthorizedTelegramScraper:
    """
    Авторизованный скрапер для Telegram каналов
    Использует пользовательский аккаунт для доступа к приватным каналам
    """
    
    def __init__(self, api_id: int, api_hash: str, phone: str = None):
        """
        Инициализация клиента
        
        Args:
            api_id: Telegram API ID
            api_hash: Telegram API Hash
            phone: Номер телефона (опционально, можно ввести вручную)
        """
        self.api_id = api_id
        self.api_hash = api_hash
        self.phone = phone
        self.client = None
        self.patterns = SignalPatterns()
        
    async def start(self):
        """Запуск клиента и авторизация"""
        try:
            # Создаем клиент
            self.client = TelegramClient('crypto_scraper_session', self.api_id, self.api_hash)
            
            # Запускаем клиент
            await self.client.start(phone=self.phone)
            
            if await self.client.is_user_authorized():
                logger.info("✅ Успешная авторизация в Telegram")
                return True
            else:
                logger.error("❌ Не удалось авторизоваться в Telegram")
                return False
                
        except Exception as e:
            logger.error(f"Ошибка запуска клиента: {e}")
            return False
    
    async def stop(self):
        """Остановка клиента"""
        if self.client:
            await self.client.disconnect()
            logger.info("Клиент Telegram остановлен")
    
    async def get_channel_messages(self, channel_username: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Получение сообщений из канала
        
        Args:
            channel_username: Имя канала (без @)
            limit: Максимальное количество сообщений
            
        Returns:
            Список сообщений
        """
        if not self.client:
            logger.error("Клиент не инициализирован")
            return []
        
        try:
            # Получаем канал
            channel = await self.client.get_entity(channel_username)
            
            if not isinstance(channel, Channel):
                logger.error(f"Не удалось найти канал: {channel_username}")
                return []
            
            logger.info(f"Найден канал: {channel.title} ({channel_username})")
            
            # Получаем сообщения
            messages = []
            async for message in self.client.iter_messages(channel, limit=limit):
                if message.text:  # Только текстовые сообщения
                    msg_data = {
                        'id': message.id,
                        'date': message.date,
                        'text': message.text,
                        'channel_username': channel_username,
                        'channel_title': channel.title
                    }
                    messages.append(msg_data)
            
            logger.info(f"Собрано {len(messages)} сообщений из канала {channel_username}")
            return messages
            
        except Exception as e:
            logger.error(f"Ошибка получения сообщений из {channel_username}: {e}")
            return []
    
    async def get_recent_signals(self, channel_username: str, hours_back: int = 24) -> List[Dict[str, Any]]:
        """
        Получение недавних сигналов из канала
        
        Args:
            channel_username: Имя канала
            hours_back: Сколько часов назад искать
            
        Returns:
            Список сигналов
        """
        try:
            # Получаем сообщения
            messages = await self.get_channel_messages(channel_username, limit=200)
            
            if not messages:
                return []
            
            # Фильтруем по времени
            cutoff_time = datetime.now() - timedelta(hours=hours_back)
            recent_messages = [
                msg for msg in messages 
                if msg['date'] > cutoff_time
            ]
            
            logger.info(f"Найдено {len(recent_messages)} недавних сообщений")
            
            # Извлекаем сигналы
            all_signals = []
            for msg in recent_messages:
                signals = self.patterns.extract_signals_from_text(
                    msg['text'],
                    channel_username,
                    str(msg['id'])
                )
                all_signals.extend(signals)
            
            # Добавляем метаданные
            for signal in all_signals:
                signal['channel_title'] = next(
                    (msg['channel_title'] for msg in recent_messages 
                     if msg['id'] == int(signal['message_id'])), 
                    'Unknown'
                )
                signal['message_date'] = next(
                    (msg['date'].isoformat() for msg in recent_messages 
                     if msg['id'] == int(signal['message_id'])), 
                    None
                )
            
            logger.info(f"Извлечено {len(all_signals)} сигналов")
            return all_signals
            
        except Exception as e:
            logger.error(f"Ошибка получения сигналов: {e}")
            return []
    
    async def get_last_signal(self, channel_username: str) -> Optional[Dict[str, Any]]:
        """
        Получение последнего сигнала из канала
        
        Args:
            channel_username: Имя канала
            
        Returns:
            Последний сигнал или None
        """
        try:
            signals = await self.get_recent_signals(channel_username, hours_back=168)  # 7 дней
            
            if not signals:
                return None
            
            # Сортируем по дате и берем самый новый
            latest_signal = max(signals, key=lambda x: x.get('message_date', ''))
            
            return latest_signal
            
        except Exception as e:
            logger.error(f"Ошибка получения последнего сигнала: {e}")
            return None

async def main():
    """Тестовая функция"""
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from real_data_config import TELEGRAM_API_ID, TELEGRAM_API_HASH
    
    scraper = AuthorizedTelegramScraper(TELEGRAM_API_ID, TELEGRAM_API_HASH)
    
    try:
        # Запускаем клиент
        if await scraper.start():
            # Получаем последний сигнал
            last_signal = await scraper.get_last_signal("signalsbitcoinandethereum")
            
            if last_signal:
                print("🎯 ПОСЛЕДНИЙ СИГНАЛ:")
                print(f"Канал: {last_signal['channel_title']}")
                print(f"Пара: {last_signal['trading_pair']}")
                print(f"Направление: {last_signal['direction']}")
                print(f"Entry: {last_signal['entry_price']}")
                print(f"Target: {last_signal['target_price']}")
                print(f"Stop: {last_signal['stop_loss']}")
                print(f"Дата: {last_signal['message_date']}")
                print(f"Confidence: {last_signal['confidence']}")
            else:
                print("❌ Сигналы не найдены")
                
            # Получаем недавние сигналы
            recent_signals = await scraper.get_recent_signals("signalsbitcoinandethereum", hours_back=24)
            print(f"\n📊 Сигналов за последние 24 часа: {len(recent_signals)}")
            
            for i, signal in enumerate(recent_signals[:5]):
                print(f"{i+1}. {signal['trading_pair']} {signal['direction']} Entry:{signal['entry_price']}")
    
    finally:
        await scraper.stop()

if __name__ == "__main__":
    asyncio.run(main())
