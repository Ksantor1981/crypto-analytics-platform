"""
Полноценный Telegram коллектор сигналов
Основан на рабочей реализации из предыдущего проекта analyst_crypto
"""
import asyncio
import os
import re
import logging
import sys
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Optional

try:
    from telethon import TelegramClient, events
    from telethon.tl.types import MessageMediaPhoto
    TELETHON_AVAILABLE = True
except ImportError:
    TELETHON_AVAILABLE = False

# Добавляем корневую директорию в sys.path для импортов
sys.path.append(str(Path(__file__).parent.parent.parent))

# Импорты конфигурации
try:
    from workers.real_data_config import TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_BOT_TOKEN
except ImportError:
    # Fallback значения для тестирования
    TELEGRAM_API_ID = int(os.getenv("TELEGRAM_API_ID", "0"))
    TELEGRAM_API_HASH = os.getenv("TELEGRAM_API_HASH", "")
    TELEGRAM_BOT_TOKEN = None

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RealTelegramCollector:
    """Полноценный коллектор сигналов из Telegram каналов"""
    
    def __init__(self, use_real_config=True):
        self.use_real_config = use_real_config
        
        if not TELETHON_AVAILABLE:
            logger.error("❌ Telethon не установлен! Установите: pip install telethon")
            return
            
        if use_real_config:
            self.api_id = TELEGRAM_API_ID
            self.api_hash = TELEGRAM_API_HASH
            self.session_name = "real_collector"
        else:
            # Fallback для тестирования
            self.api_id = None
            self.api_hash = None
            self.session_name = "test_collector"
            
        # Список каналов для мониторинга
        self.channels = [
            "binancekillers",
            "io_altsignals", 
            "CryptoCapoTG",
            "WhaleChart",
            "Crypto_Inner_Circler",
            "learn2trade",
            "Wolf_of_Trading_singals",
            "cryptosignals",
            "binancesignals",
            "cryptotradingview",
            "cryptowhales",
            "bitcoinsignals"
        ]
        
        self.client = None
        self.collected_signals = []
        
    async def initialize(self) -> bool:
        """Инициализация Telegram клиента"""
        if not TELETHON_AVAILABLE:
            logger.error("❌ Telethon недоступен")
            return False
            
        if not self.api_id or not self.api_hash:
            logger.error("❌ Не настроены API_ID и API_HASH")
            return False
            
        try:
            self.client = TelegramClient(
                self.session_name,
                self.api_id,
                self.api_hash
            )
            
            await self.client.start()
            logger.info("✅ Telegram клиент инициализирован")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации клиента: {e}")
            return False
    
    def extract_signal_data(self, message_text: str) -> Optional[Dict]:
        """Извлечение данных сигнала из текста сообщения"""
        if not message_text:
            return None
            
        # Паттерны для поиска торговых сигналов
        patterns = {
            'coin': r'(?:SIGNAL|COIN|PAIR)[\s:]*([A-Z]{2,10}(?:USDT?|BTC|ETH)?)',
            'entry': r'(?:ENTRY|BUY)[\s:]*([0-9.,]+)',
            'target': r'(?:TARGET|TP|TAKE PROFIT)[\s:]*([0-9.,]+)',
            'stop_loss': r'(?:STOP LOSS|SL|STOPLOSS)[\s:]*([0-9.,]+)',
            'leverage': r'(?:LEVERAGE|LEV)[\s:]*([0-9x]+)',
            'direction': r'(LONG|SHORT|BUY|SELL)'
        }
        
        signal_data = {}
        
        for key, pattern in patterns.items():
            match = re.search(pattern, message_text.upper())
            if match:
                signal_data[key] = match.group(1)
        
        # Если найдена монета - это потенциальный сигнал
        if 'coin' in signal_data:
            signal_data['original_text'] = message_text
            signal_data['timestamp'] = datetime.now(timezone.utc).isoformat()
            signal_data['confidence'] = self.calculate_confidence(signal_data)
            return signal_data
            
        return None
    
    def calculate_confidence(self, signal_data: Dict) -> float:
        """Расчет уверенности в качестве сигнала"""
        confidence = 0.0
        
        # Базовая уверенность за наличие монеты
        if 'coin' in signal_data:
            confidence += 0.3
            
        # Дополнительные очки за ключевые параметры
        if 'entry' in signal_data:
            confidence += 0.2
        if 'target' in signal_data:
            confidence += 0.2
        if 'stop_loss' in signal_data:
            confidence += 0.2
        if 'direction' in signal_data:
            confidence += 0.1
            
        return min(confidence, 1.0)
    
    async def collect_recent_messages(self, limit: int = 100) -> List[Dict]:
        """Сбор последних сообщений из каналов"""
        if not self.client:
            logger.error("❌ Клиент не инициализирован")
            return []
            
        all_signals = []
        
        for channel in self.channels:
            try:
                logger.info(f"📡 Сбор сообщений из канала: {channel}")
                
                # Получаем последние сообщения
                async for message in self.client.iter_messages(channel, limit=limit):
                    if message.text:
                        signal_data = self.extract_signal_data(message.text)
                        if signal_data:
                            signal_data['channel'] = channel
                            signal_data['message_id'] = message.id
                            signal_data['message_date'] = message.date.isoformat()
                            all_signals.append(signal_data)
                            
                logger.info(f"✅ Обработан канал {channel}")
                
            except Exception as e:
                logger.error(f"❌ Ошибка при обработке канала {channel}: {e}")
                continue
                
        logger.info(f"📊 Всего найдено сигналов: {len(all_signals)}")
        self.collected_signals = all_signals
        return all_signals
    
    async def start_real_time_monitoring(self, callback=None):
        """Запуск мониторинга в реальном времени"""
        if not self.client:
            logger.error("❌ Клиент не инициализирован")
            return
            
        @self.client.on(events.NewMessage(chats=self.channels))
        async def handler(event):
            try:
                if event.text:
                    signal_data = self.extract_signal_data(event.text)
                    if signal_data:
                        signal_data['channel'] = event.chat.username or str(event.chat_id)
                        signal_data['message_id'] = event.id
                        signal_data['message_date'] = event.date.isoformat()
                        
                        logger.info(f"🚨 Новый сигнал: {signal_data['coin']} от {signal_data['channel']}")
                        
                        # Сохраняем сигнал
                        self.collected_signals.append(signal_data)
                        
                        # Вызываем callback если предоставлен
                        if callback:
                            await callback(signal_data)
                            
            except Exception as e:
                logger.error(f"❌ Ошибка обработки сообщения: {e}")
        
        logger.info("🔄 Запущен мониторинг в реальном времени...")
        await self.client.run_until_disconnected()
    
    async def get_channel_info(self) -> Dict:
        """Получение информации о доступных каналах"""
        if not self.client:
            return {}
            
        channels_info = {}
        
        for channel in self.channels:
            try:
                entity = await self.client.get_entity(channel)
                channels_info[channel] = {
                    'title': entity.title,
                    'username': entity.username,
                    'participants_count': getattr(entity, 'participants_count', 'N/A'),
                    'accessible': True
                }
            except Exception as e:
                channels_info[channel] = {
                    'error': str(e),
                    'accessible': False
                }
                
        return channels_info
    
    async def disconnect(self):
        """Отключение от Telegram"""
        if self.client:
            await self.client.disconnect()
            logger.info("🔌 Отключен от Telegram")
    
    def get_collected_signals(self) -> List[Dict]:
        """Получение собранных сигналов"""
        return self.collected_signals
    
    def get_statistics(self) -> Dict:
        """Получение статистики сбора"""
        if not self.collected_signals:
            return {"total_signals": 0}
            
        stats = {
            "total_signals": len(self.collected_signals),
            "channels_count": len(set(s.get('channel', '') for s in self.collected_signals)),
            "avg_confidence": sum(s.get('confidence', 0) for s in self.collected_signals) / len(self.collected_signals),
            "coins_found": list(set(s.get('coin', '') for s in self.collected_signals if s.get('coin')))
        }
        
        return stats

# Функция для быстрого тестирования
async def test_telegram_collector():
    """Тестирование коллектора"""
    collector = RealTelegramCollector(use_real_config=True)
    
    if not await collector.initialize():
        logger.error("❌ Не удалось инициализировать коллектор")
        return
    
    try:
        # Тест сбора последних сообщений
        logger.info("🧪 Тестирование сбора сообщений...")
        signals = await collector.collect_recent_messages(limit=50)
        
        logger.info(f"📊 Результаты теста:")
        logger.info(f"   Найдено сигналов: {len(signals)}")
        
        if signals:
            logger.info(f"   Пример сигнала: {signals[0]}")
            
        # Статистика
        stats = collector.get_statistics()
        logger.info(f"   Статистика: {stats}")
        
        # Информация о каналах
        channels_info = await collector.get_channel_info()
        logger.info(f"   Доступных каналов: {sum(1 for c in channels_info.values() if c.get('accessible'))}")
        
    finally:
        await collector.disconnect()

if __name__ == "__main__":
    if TELETHON_AVAILABLE:
        asyncio.run(test_telegram_collector())
    else:
        print("❌ Telethon не установлен. Установите: pip install telethon") 