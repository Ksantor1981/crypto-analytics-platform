"""
Migrated Telegram Collector from analyst_crypto
Адаптирован под новую архитектуру с PostgreSQL и Celery
"""

import asyncio
import os
import re
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from telethon import TelegramClient, events
from telethon.tl.types import MessageMediaPhoto
import easyocr

# Импорты для новой архитектуры
from sqlalchemy.orm import Session
from sqlalchemy import create_engine

# Импорты моделей (с обработкой ошибок)
try:
    from backend.app.models.signal import Signal, TelegramSignal
    from backend.app.models.channel import Channel
    from backend.app.core.database import get_db
    from backend.app.services.ocr_service import AdvancedOCRService
    from backend.app.services.trading_pair_validator import TradingPairValidator
except ImportError as e:
    print(f"⚠️ Не удалось импортировать backend модули: {e}")
    print("🔄 Используем fallback импорты...")
    
    # Fallback импорты для тестирования
    Signal = None
    TelegramSignal = None
    Channel = None
    get_db = None
    AdvancedOCRService = None
    TradingPairValidator = None

load_dotenv()

logger = logging.getLogger(__name__)

# Конфигурация каналов из analyst_crypto
CHANNELS = [
    "binancekillers",
    "io_altsignals",
    "CryptoCapoTG", 
    "WhaleChart",
    "Crypto_Inner_Circler",
    "learn2trade",
    "Wolf_of_Trading_singals",
    "fatpigsignals",
    "Fat_Pig_Signals"
]

KEYWORDS = ['buy', 'sell', 'long', 'short', 'target', 'stop loss', 'take profit']

CRYPTO_PATTERN = r'\b(btc|eth|sol|bnb|ada|xrp|dot|link|ltc|doge|matic|avax|uni|atom|near|apt|arb|op|ftm|rndr|etc|cake|sand|mana|shib|pepe|floki|sui|sei|not|wif|tether|usdt|usdc|usd|eur|rub)\b'
PRICE_PATTERN = r'\$?\s*(\d{2,6}(?:[\.,]\d{1,8})?)'
DEADLINE_PATTERN = r'(\d{1,2}[\.\-/]\d{1,2}[\.\-/]\d{2,4})'

class MigratedTelegramCollector:
    """
    Мигрированный Telegram Collector
    Адаптирован под новую архитектуру с PostgreSQL и Celery
    """
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.media_dir = Path("workers/media")
        self.media_dir.mkdir(exist_ok=True, parents=True)
        
        # Инициализируем OCR (с проверкой доступности)
        if AdvancedOCRService:
            self.ocr_service = AdvancedOCRService(db_session)
        else:
            self.ocr_service = None
            logger.warning("⚠️ AdvancedOCRService недоступен, OCR отключен")
        
        # Инициализируем валидатор торговых пар (с проверкой доступности)
        if TradingPairValidator:
            self.trading_pair_validator = TradingPairValidator()
        else:
            self.trading_pair_validator = None
            logger.warning("⚠️ TradingPairValidator недоступен, валидация отключена")
        
        # Telegram API credentials
        self.api_id = os.getenv('TELEGRAM_API_ID')
        self.api_hash = os.getenv('TELEGRAM_API_HASH')
        
        if not self.api_id or not self.api_hash:
            raise ValueError("TELEGRAM_API_ID and TELEGRAM_API_HASH must be set")
        
        # Список каналов для мониторинга
        self.channels = CHANNELS
        
        # Убираем ограничение по датам для продакшена
        logger.info("🚀 Telegram коллектор инициализирован для продакшена")
    
    async def process_message(self, message, channel_username: str) -> Optional[Dict[str, Any]]:
        """
        Обработка сообщения с извлечением сигналов
        """
        try:
            # Обрабатываем текст
            if message.text:
                logger.info(f"📨 Обрабатываем текстовое сообщение из {channel_username}")
                
                # Извлекаем сигнал
                signal_data = self.extract_signal_from_text(message.text, channel_username)
                
                if signal_data:
                    # Валидируем торговую пару (если доступен валидатор)
                    if self.trading_pair_validator:
                        if self.trading_pair_validator.validate_trading_pair(signal_data['asset']):
                            # Сохраняем в базу данных
                            await self.save_signal_to_db(signal_data, message, channel_username, "text")
                            logger.info(f"✅ Сохранен сигнал: {signal_data['asset']} {signal_data['direction']}")
                            return signal_data
                        else:
                            logger.warning(f"⚠️ Невалидная торговая пара: {signal_data['asset']}")
                    else:
                        # Если валидатор недоступен, сохраняем без валидации
                        await self.save_signal_to_db(signal_data, message, channel_username, "text")
                        logger.info(f"✅ Сохранен сигнал (без валидации): {signal_data['asset']} {signal_data['direction']}")
                        return signal_data
            
            # Обрабатываем фото
            if message.media and isinstance(message.media, MessageMediaPhoto):
                logger.info(f"📸 Обрабатываем изображение из {channel_username}")
                
                # Сохраняем фото
                photo_path = self.media_dir / f"{channel_username}_{message.id}_{message.date.strftime('%Y%m%d_%H%M')}.jpg"
                await message.download_media(file=photo_path)
                
                # Извлекаем текст через OCR (если доступен)
                if self.ocr_service:
                    with open(photo_path, 'rb') as f:
                        image_data = f.read()
                    
                    ocr_signals = await self.ocr_service.extract_signals_from_image(
                        image_data=image_data,
                        channel_id=await self.get_channel_id(channel_username),
                        message_id=str(message.id)
                    )
                    
                    if ocr_signals:
                        for signal in ocr_signals:
                            await self.save_signal_to_db(signal, message, channel_username, "image")
                        logger.info(f"✅ Извлечено {len(ocr_signals)} сигналов из изображения")
                        return ocr_signals
                else:
                    logger.warning("⚠️ OCR недоступен, изображение не обработано")
                
        except Exception as e:
            logger.error(f"❌ Ошибка обработки сообщения из {channel_username}: {e}")
        
        return None
    
    def extract_signal_from_text(self, text: str, channel_username: str) -> Optional[Dict[str, Any]]:
        """
        Извлечение сигнала из текста с использованием паттернов из analyst_crypto
        """
        try:
            # Используем улучшенные паттерны из enhanced_signal_extractor
            symbol, prediction_type, target_value, deadline = self.parse_forecast(text)
            
            if symbol and prediction_type:
                # Извлекаем дополнительные данные
                entry_price = self.extract_entry_price(text)
                stop_loss = self.extract_stop_loss(text)
                
                return {
                    'channel_name': channel_username,
                    'asset': symbol,
                    'direction': prediction_type.upper(),
                    'entry_price': entry_price,
                    'target_price': target_value,
                    'stop_loss': stop_loss,
                    'original_text': text,
                    'message_timestamp': datetime.now(timezone.utc),
                    'confidence_score': self.calculate_confidence(text, channel_username)
                }
                
        except Exception as e:
            logger.error(f"❌ Ошибка извлечения сигнала: {e}")
        
        return None
    
    def parse_forecast(self, text: str):
        """
        Парсинг прогноза из текста (из analyst_crypto)
        """
        symbol = None
        prediction_type = None
        target_value = None
        deadline = None
        
        # Символ и тип (например, # BTCUSD BUY 102600)
        m = re.search(r'#?\s*([A-Z]{3,6}\/?[A-Z]{0,6})\s+(BUY|SELL|LONG|SHORT)\s+(\d{4,7})', text, re.IGNORECASE)
        if m:
            symbol = m.group(1).upper()
            prediction_type = m.group(2).upper()
            target_value = float(m.group(3))
        else:
            # Старый способ
            symbol_match = re.search(CRYPTO_PATTERN, text, re.IGNORECASE)
            if symbol_match:
                symbol = symbol_match.group(1).upper()
            for k in KEYWORDS:
                if k in text.lower():
                    prediction_type = k
                    break
            price_match = re.search(PRICE_PATTERN, text.replace(",", "."))
            if price_match:
                try:
                    target_value = float(price_match.group(1).replace(",", "."))
                except Exception:
                    target_value = None
        
        # Цели (Target 1/2/3)
        targets = re.findall(r'Target\s*\d+\s*[:\-]?\s*(\d{4,7})', text, re.IGNORECASE)
        if targets:
            try:
                target_value = float(targets[0])
            except Exception:
                pass
        
        # Стоп-лосс
        stoploss = None
        m = re.search(r'Stop ?loss (At)?\s*(\d{4,7})', text, re.IGNORECASE)
        if m:
            stoploss = float(m.group(2))
        
        # Дедлайн (ищем дату)
        deadline_match = re.search(DEADLINE_PATTERN, text)
        if deadline_match:
            try:
                deadline = datetime.strptime(deadline_match.group(1), "%d.%m.%Y")
            except Exception:
                try:
                    deadline = datetime.strptime(deadline_match.group(1), "%d/%m/%Y")
                except Exception:
                    deadline = None
        
        return symbol, prediction_type, target_value, deadline
    
    def extract_entry_price(self, text: str) -> Optional[float]:
        """Извлечение цены входа"""
        patterns = [
            r'entry[:\s@]+\$?(\d+[\d,]*\.?\d*)',
            r'buy[:\s@]+\$?(\d+[\d,]*\.?\d*)',
            r'enter[:\s@]+\$?(\d+[\d,]*\.?\d*)',
            r'Entry[:\s]+(\d+\.?\d*)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    return float(match.group(1).replace(',', ''))
                except:
                    continue
        
        return None
    
    def extract_stop_loss(self, text: str) -> Optional[float]:
        """Извлечение стоп-лосса"""
        patterns = [
            r'stop[\s-]*loss[:\s@]+\$?(\d+[\d,]*\.?\d*)',
            r'sl[:\s@]+\$?(\d+[\d,]*\.?\d*)',
            r'Stop ?loss (At)?\s*(\d{4,7})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    return float(match.group(1).replace(',', ''))
                except:
                    continue
        
        return None
    
    def calculate_confidence(self, text: str, channel_username: str) -> float:
        """Расчет уверенности в сигнале"""
        confidence = 50.0  # Базовая уверенность
        
        # Увеличиваем уверенность за наличие ключевых элементов
        if re.search(r'entry|buy|enter', text, re.IGNORECASE):
            confidence += 10
        if re.search(r'target|tp', text, re.IGNORECASE):
            confidence += 10
        if re.search(r'stop|sl', text, re.IGNORECASE):
            confidence += 10
        if re.search(CRYPTO_PATTERN, text, re.IGNORECASE):
            confidence += 10
        
        # Учитываем качество канала (можно добавить из БД)
        # confidence += channel_quality_score
        
        return min(100.0, confidence)
    
    async def get_channel_id(self, channel_username: str) -> int:
        """Получение ID канала из БД"""
        if Channel and self.db:
            channel = self.db.query(Channel).filter(Channel.username == channel_username).first()
            if channel:
                return channel.id
            else:
                # Создаем новый канал если не существует
                new_channel = Channel(
                    username=channel_username,
                    name=channel_username,
                    platform="telegram",
                    is_active=True
                )
                self.db.add(new_channel)
                self.db.commit()
                return new_channel.id
        else:
            # Fallback: возвращаем хеш от username как ID
            return hash(channel_username) % 1000000
    
    async def save_signal_to_db(self, signal_data: Dict[str, Any], message, channel_username: str, source_type: str):
        """Сохранение сигнала в базу данных"""
        try:
            channel_id = await self.get_channel_id(channel_username)
            
            if Signal and self.db:
                # Создаем объект сигнала
                signal = Signal(
                    channel_id=channel_id,
                    asset=signal_data['asset'],
                    direction=signal_data['direction'],
                    entry_price=signal_data.get('entry_price'),
                    tp1_price=signal_data.get('target_price'),
                    stop_loss=signal_data.get('stop_loss'),
                    original_text=signal_data.get('original_text', ''),
                    message_timestamp=signal_data.get('message_timestamp'),
                    confidence_score=signal_data.get('confidence_score', 50.0)
                )
                
                self.db.add(signal)
                self.db.commit()
                
                logger.info(f"✅ Сигнал сохранен в БД: {signal.id}")
            else:
                # Fallback: логируем сигнал без сохранения в БД
                logger.info(f"📝 Сигнал (fallback): {signal_data['asset']} {signal_data['direction']} Entry: {signal_data.get('entry_price')} Target: {signal_data.get('target_price')}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения сигнала: {e}")
            if self.db:
                self.db.rollback()
    
    async def start_collection(self):
        """Запуск сбора сообщений"""
        client = TelegramClient('crypto_collector_migrated', self.api_id, self.api_hash)
        
        @client.on(events.NewMessage(chats=self.channels))
        async def handler(event):
            try:
                message = event.message
                channel_username = event.chat.username
                
                logger.info(f"📨 Новое сообщение из {channel_username}")
                
                # Обрабатываем сообщение
                result = await self.process_message(message, channel_username)
                
                if result:
                    logger.info(f"✅ Обработано сообщение из {channel_username}")
                else:
                    logger.debug(f"⏭️ Сообщение из {channel_username} не содержит сигналов")
                
            except Exception as e:
                logger.error(f"❌ Ошибка обработки сообщения: {e}")
        
        # Запускаем клиент
        await client.start()
        logger.info("🚀 Мигрированный Telegram коллектор запущен")
        logger.info(f"📺 Мониторинг каналов: {', '.join(self.channels)}")
        
        # Держим клиент запущенным
        await client.run_until_disconnected()

async def main():
    """Тестовая функция"""
    # Создаем сессию БД (с fallback)
    try:
        from backend.app.core.database import SessionLocal
        db = SessionLocal()
    except ImportError:
        logger.warning("⚠️ Не удалось создать сессию БД, используем None")
        db = None
    
    try:
        collector = MigratedTelegramCollector(db)
        await collector.start_collection()
    finally:
        if db:
            db.close()

if __name__ == "__main__":
    asyncio.run(main())
