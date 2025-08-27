#!/usr/bin/env python3
"""
КОМПЛЕКСНЫЙ сборщик РЕАЛЬНЫХ данных
- OCR для изображений
- Историческая точность каналов
- Винрейт по сигналам
- Валидация цен через CoinGecko
- Детальная аналитика источников
"""
import os
import json
import sqlite3
import asyncio
import requests
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
import re
from pathlib import Path
import base64
from io import BytesIO

# OCR для изображений
try:
    import pytesseract
    from PIL import Image
    OCR_AVAILABLE = True
except ImportError:
    print("⚠️ OCR не доступен. Установите: pip install pytesseract pillow")
    OCR_AVAILABLE = False

# Telethon для Telegram
try:
    from telethon import TelegramClient
    from telethon.tl.types import MessageMediaPhoto, MessageMediaDocument
    TELEGRAM_AVAILABLE = True
except ImportError:
    print("⚠️ Telethon не установлен. Установите: pip install telethon")
    TELEGRAM_AVAILABLE = False

BASE_DIR = Path(__file__).parent
DB_PATH = str(BASE_DIR / 'signals.db')

# Конфигурация API
TELEGRAM_API_ID = os.getenv('TELEGRAM_API_ID', '')
TELEGRAM_API_HASH = os.getenv('TELEGRAM_API_HASH', '')
TELEGRAM_PHONE = os.getenv('TELEGRAM_PHONE', '')
COINGECKO_API_KEY = os.getenv('COINGECKO_API_KEY', '')

# ВСЕ РЕАЛЬНЫЕ ИСТОЧНИКИ
REAL_SOURCES = {
    'telegram': [
        'CryptoPapa', 'FatPigSignals', 'WallstreetQueenOfficial', 
        'RocketWalletSignals', 'BinanceKiller', 'WolfOfTrading',
        'CryptoSignalsOrg', 'Learn2Trade', 'UniversalCryptoSignals',
        'OnwardBTC', 'CryptoClassics', 'MyCryptoParadise',
        'SafeSignals', 'CoinSignalsPro', 'MYCSignals', 'WOLFXSignals',
        'SignalsBlue', 'CoinCodeCap', 'BitcoinBullets', 'AltSignals'
    ],
    'reddit': [
        'cryptosignals', 'CryptoMarkets', 'CryptoCurrencyTrading',
        'CryptoMoonShots', 'CryptoCurrency', 'Bitcoin', 'Ethereum',
        'Altcoin', 'DeFi', 'CryptoCurrencySignals'
    ],
    'discord': [
        'Filthy Rich Futures', 'Elite Crypto Signals', 
        'Satoshi\'s Data', 'Axion', 'Cryptohub'
    ]
}

# Паттерны для извлечения сигналов
SIGNAL_PATTERNS = [
    # BTC/USDT
    r'BTC.*?(\d{4,6})[^\d]*?(\d{4,6})',  # BTC 45000 -> 50000
    r'Bitcoin.*?(\d{4,6})[^\d]*?(\d{4,6})',  # Bitcoin 45000 -> 50000
    r'(\d{4,6})[^\d]*?BTC[^\d]*?(\d{4,6})',  # 45000 BTC -> 50000
    
    # ETH/USDT
    r'ETH.*?(\d{3,5})[^\d]*?(\d{3,5})',  # ETH 3000 -> 3500
    r'Ethereum.*?(\d{3,5})[^\d]*?(\d{3,5})',  # Ethereum 3000 -> 3500
    r'(\d{3,5})[^\d]*?ETH[^\d]*?(\d{3,5})',  # 3000 ETH -> 3500
    
    # SOL/USDT
    r'SOL.*?(\d{2,4})[^\d]*?(\d{2,4})',  # SOL 150 -> 200
    r'Solana.*?(\d{2,4})[^\d]*?(\d{2,4})',  # Solana 150 -> 200
    r'(\d{2,4})[^\d]*?SOL[^\d]*?(\d{2,4})',  # 150 SOL -> 200
    
    # ADA/USDT
    r'ADA.*?(\d\.\d{1,3})[^\d]*?(\d\.\d{1,3})',  # ADA 0.85 -> 1.00
    r'Cardano.*?(\d\.\d{1,3})[^\d]*?(\d\.\d{1,3})',  # Cardano 0.85 -> 1.00
    
    # LINK/USDT
    r'LINK.*?(\d{1,3})[^\d]*?(\d{1,3})',  # LINK 20 -> 25
    r'Chainlink.*?(\d{1,3})[^\d]*?(\d{1,3})',  # Chainlink 20 -> 25
    
    # MATIC/USDT
    r'MATIC.*?(\d\.\d{1,3})[^\d]*?(\d\.\d{1,3})',  # MATIC 0.20 -> 0.30
    r'Polygon.*?(\d\.\d{1,3})[^\d]*?(\d\.\d{1,3})',  # Polygon 0.20 -> 0.30
]

class CoinGeckoAPI:
    """API для получения реальных цен"""
    
    def __init__(self):
        self.base_url = "https://api.coingecko.com/api/v3"
        self.session = requests.Session()
        if COINGECKO_API_KEY:
            self.session.headers.update({'X-CG-API-KEY': COINGECKO_API_KEY})
    
    def get_current_price(self, asset: str) -> Optional[float]:
        """Получает текущую цену актива"""
        try:
            asset_id = self._get_asset_id(asset)
            if not asset_id:
                return None
            
            url = f"{self.base_url}/simple/price"
            params = {
                'ids': asset_id,
                'vs_currencies': 'usd'
            }
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            return data.get(asset_id, {}).get('usd')
            
        except Exception as e:
            print(f"❌ Ошибка получения цены {asset}: {e}")
            return None
    
    def get_historical_price(self, asset: str, date: datetime) -> Optional[float]:
        """Получает историческую цену на определенную дату"""
        try:
            asset_id = self._get_asset_id(asset)
            if not asset_id:
                return None
            
            url = f"{self.base_url}/coins/{asset_id}/history"
            params = {
                'date': date.strftime('%d-%m-%Y'),
                'localization': 'false'
            }
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            return data.get('market_data', {}).get('current_price', {}).get('usd')
            
        except Exception as e:
            print(f"❌ Ошибка получения исторической цены {asset}: {e}")
            return None
    
    def _get_asset_id(self, asset: str) -> Optional[str]:
        """Преобразует символ актива в ID CoinGecko"""
        mapping = {
            'BTC': 'bitcoin',
            'ETH': 'ethereum', 
            'SOL': 'solana',
            'ADA': 'cardano',
            'LINK': 'chainlink',
            'MATIC': 'matic-network'
        }
        return mapping.get(asset.upper())

class SignalTracker:
    """Отслеживание результатов сигналов"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.coingecko = CoinGeckoAPI()
        self._init_database()
    
    def _init_database(self):
        """Инициализирует БД с таблицами для отслеживания"""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        
        # Таблица для отслеживания результатов
        cur.execute("""
            CREATE TABLE IF NOT EXISTS signal_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                signal_id TEXT UNIQUE,
                entry_price REAL,
                target_price REAL,
                stop_loss REAL,
                current_price REAL,
                result TEXT,  -- 'hit_target', 'hit_stop', 'pending', 'expired'
                profit_loss REAL,
                result_date TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        """)
        
        # Таблица статистики каналов
        cur.execute("""
            CREATE TABLE IF NOT EXISTS channel_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel TEXT UNIQUE,
                total_signals INTEGER DEFAULT 0,
                successful_signals INTEGER DEFAULT 0,
                win_rate REAL DEFAULT 0.0,
                avg_profit REAL DEFAULT 0.0,
                avg_loss REAL DEFAULT 0.0,
                total_profit REAL DEFAULT 0.0,
                last_updated TEXT
            )
        """)
        
        conn.commit()
        conn.close()
    
    def track_signal_result(self, signal_id: str, entry_price: float, 
                          target_price: float, stop_loss: float, asset: str):
        """Отслеживает результат сигнала"""
        current_price = self.coingecko.get_current_price(asset)
        if not current_price:
            return
        
        result = self._calculate_result(entry_price, target_price, stop_loss, current_price)
        profit_loss = self._calculate_profit_loss(entry_price, current_price)
        
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        
        now = datetime.now(timezone.utc).isoformat()
        
        cur.execute("""
            INSERT OR REPLACE INTO signal_results 
            (signal_id, entry_price, target_price, stop_loss, current_price, 
             result, profit_loss, result_date, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (signal_id, entry_price, target_price, stop_loss, current_price,
              result, profit_loss, now, now, now))
        
        conn.commit()
        conn.close()
    
    def _calculate_result(self, entry: float, target: float, stop: float, current: float) -> str:
        """Рассчитывает результат сигнала"""
        if target > entry:  # LONG
            if current >= target:
                return 'hit_target'
            elif current <= stop:
                return 'hit_stop'
        else:  # SHORT
            if current <= target:
                return 'hit_target'
            elif current >= stop:
                return 'hit_stop'
        
        return 'pending'
    
    def _calculate_profit_loss(self, entry: float, current: float) -> float:
        """Рассчитывает прибыль/убыток в процентах"""
        return ((current - entry) / entry) * 100
    
    def update_channel_stats(self, channel: str):
        """Обновляет статистику канала"""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        
        # Получаем все результаты канала
        cur.execute("""
            SELECT sr.result, sr.profit_loss 
            FROM signal_results sr
            JOIN signals s ON sr.signal_id = s.id
            WHERE s.channel = ? AND sr.result IN ('hit_target', 'hit_stop')
        """, (channel,))
        
        results = cur.fetchall()
        if not results:
            return
        
        total = len(results)
        successful = len([r for r in results if r[0] == 'hit_target'])
        win_rate = (successful / total) * 100 if total > 0 else 0
        
        profits = [r[1] for r in results if r[1] > 0]
        losses = [r[1] for r in results if r[1] < 0]
        
        avg_profit = sum(profits) / len(profits) if profits else 0
        avg_loss = sum(losses) / len(losses) if losses else 0
        total_profit = sum(profits) + sum(losses)
        
        now = datetime.now(timezone.utc).isoformat()
        
        cur.execute("""
            INSERT OR REPLACE INTO channel_stats 
            (channel, total_signals, successful_signals, win_rate, 
             avg_profit, avg_loss, total_profit, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (channel, total, successful, win_rate, avg_profit, avg_loss, total_profit, now))
        
        conn.commit()
        conn.close()

class OCRProcessor:
    """Обработка изображений с OCR"""
    
    def __init__(self):
        if not OCR_AVAILABLE:
            raise ImportError("OCR не доступен")
    
    def extract_text_from_image(self, image_data: bytes) -> str:
        """Извлекает текст из изображения"""
        try:
            image = Image.open(BytesIO(image_data))
            text = pytesseract.image_to_string(image, config='--psm 6')
            return text
        except Exception as e:
            print(f"❌ Ошибка OCR: {e}")
            return ""

class RealDataCollector:
    """Основной сборщик РЕАЛЬНЫХ данных"""
    
    def __init__(self):
        self.tracker = SignalTracker(DB_PATH)
        self.ocr = OCRProcessor() if OCR_AVAILABLE else None
        self.coingecko = CoinGeckoAPI()
    
    def extract_signal_from_text(self, text: str, source: str, message_id: str) -> Optional[Dict[str, Any]]:
        """Извлекает сигнал из текста"""
        if not text:
            return None
        
        text_upper = text.upper()
        
        # Определяем актив
        asset = None
        if 'BTC' in text_upper or 'BITCOIN' in text_upper:
            asset = 'BTC'
        elif 'ETH' in text_upper or 'ETHEREUM' in text_upper:
            asset = 'ETH'
        elif 'SOL' in text_upper or 'SOLANA' in text_upper:
            asset = 'SOL'
        elif 'ADA' in text_upper or 'CARDANO' in text_upper:
            asset = 'ADA'
        elif 'LINK' in text_upper or 'CHAINLINK' in text_upper:
            asset = 'LINK'
        elif 'MATIC' in text_upper or 'POLYGON' in text_upper:
            asset = 'MATIC'
        
        if not asset:
            return None
        
        # Ищем цены
        for pattern in SIGNAL_PATTERNS:
            if asset in pattern.upper():
                matches = re.findall(pattern, text_upper)
                for match in matches:
                    if len(match) == 2:
                        try:
                            entry_price = float(match[0])
                            target_price = float(match[1])
                            
                            # Валидация цен через CoinGecko
                            current_price = self.coingecko.get_current_price(asset)
                            if current_price:
                                # Проверяем что цены реалистичны (не более 50% отклонения)
                                if abs(entry_price - current_price) / current_price > 0.5:
                                    continue
                            
                            # Определяем направление
                            direction = 'LONG' if target_price > entry_price else 'SHORT'
                            
                            # Рассчитываем stop loss (2% от entry)
                            stop_loss = entry_price * 0.98 if direction == 'LONG' else entry_price * 1.02
                            
                            # Получаем статистику канала
                            channel_stats = self._get_channel_stats(source)
                            confidence = channel_stats.get('win_rate', 50.0) if channel_stats else 50.0
                            
                            return {
                                'asset': asset,
                                'direction': direction,
                                'entry_price': entry_price,
                                'target_price': target_price,
                                'stop_loss': stop_loss,
                                'confidence': confidence,
                                'is_valid': 1,
                                'source': source,
                                'message_id': message_id,
                                'original_text': text
                            }
                            
                        except (ValueError, TypeError):
                            continue
        
        return None
    
    def _get_channel_stats(self, channel: str) -> Optional[Dict[str, Any]]:
        """Получает статистику канала"""
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        
        cur.execute("""
            SELECT win_rate, avg_profit, total_signals, successful_signals
            FROM channel_stats WHERE channel = ?
        """, (channel,))
        
        result = cur.fetchone()
        conn.close()
        
        if result:
            return {
                'win_rate': result[0],
                'avg_profit': result[1],
                'total_signals': result[2],
                'successful_signals': result[3]
            }
        return None
    
    async def collect_from_telegram(self):
        """Собирает данные из Telegram"""
        if not TELEGRAM_AVAILABLE or not all([TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_PHONE]):
            print("❌ Telegram API не настроен")
            return 0
        
        print("📡 Сбор из Telegram каналов...")
        
        client = TelegramClient('crypto_signals_session', TELEGRAM_API_ID, TELEGRAM_API_HASH)
        
        try:
            await client.start(phone=TELEGRAM_PHONE)
            
            total_signals = 0
            
            for channel_name in REAL_SOURCES['telegram']:
                try:
                    channel = await client.get_entity(channel_name)
                    messages = await client.get_messages(channel, limit=50)
                    
                    for msg in messages:
                        # Обрабатываем текст
                        if msg.text:
                            signal = self.extract_signal_from_text(msg.text, f"telegram/{channel_name}", str(msg.id))
                            if signal:
                                await self._save_signal(signal, msg.date)
                                total_signals += 1
                        
                        # Обрабатываем изображения с OCR
                        if msg.media and self.ocr:
                            if isinstance(msg.media, (MessageMediaPhoto, MessageMediaDocument)):
                                try:
                                    image_data = await client.download_media(msg.media, bytes)
                                    if image_data:
                                        ocr_text = self.ocr.extract_text_from_image(image_data)
                                        if ocr_text:
                                            signal = self.extract_signal_from_text(ocr_text, f"telegram/{channel_name}", str(msg.id))
                                            if signal:
                                                await self._save_signal(signal, msg.date)
                                                total_signals += 1
                                except Exception as e:
                                    print(f"❌ Ошибка OCR для {channel_name}: {e}")
                
                except Exception as e:
                    print(f"❌ Ошибка сбора из {channel_name}: {e}")
            
            await client.disconnect()
            print(f"✅ Собрано {total_signals} сигналов из Telegram")
            return total_signals
            
        except Exception as e:
            print(f"❌ Ошибка подключения к Telegram: {e}")
            return 0
    
    async def _save_signal(self, signal: Dict[str, Any], timestamp: datetime):
        """Сохраняет сигнал в БД"""
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        
        signal_id = f"{signal['source']}_{signal['asset']}_{signal['message_id']}"
        
        cur.execute("""
            INSERT OR REPLACE INTO signals (
                id, asset, direction, entry_price, target_price, stop_loss,
                leverage, timeframe, signal_quality, real_confidence,
                calculated_confidence, channel, message_id, original_text,
                cleaned_text, signal_type, timestamp, extraction_time,
                bybit_available, is_valid, validation_errors,
                risk_reward_ratio, potential_profit, potential_loss
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            signal_id, signal['asset'], signal['direction'],
            signal['entry_price'], signal['target_price'], signal['stop_loss'],
            1, '1H', 'verified', signal['confidence'], signal['confidence'],
            signal['source'], signal['message_id'], signal['original_text'],
            signal['original_text'], 'telegram_real', timestamp.isoformat(),
            datetime.now(timezone.utc).isoformat(), True, signal['is_valid'],
            json.dumps([], ensure_ascii=False), 0.0, 0.0, 0.0
        ))
        
        conn.commit()
        conn.close()
        
        # Отслеживаем результат
        self.tracker.track_signal_result(
            signal_id, signal['entry_price'], signal['target_price'], 
            signal['stop_loss'], signal['asset']
        )
        
        print(f"✅ {signal['asset']} @ ${signal['entry_price']} -> ${signal['target_price']} | {signal['source']}")

async def main():
    """Основная функция"""
    print("🚀 Запуск сбора РЕАЛЬНЫХ данных...")
    
    collector = RealDataCollector()
    
    # Собираем из Telegram
    telegram_signals = await collector.collect_from_telegram()
    
    # Обновляем статистику каналов
    print("📊 Обновление статистики каналов...")
    for channel in REAL_SOURCES['telegram']:
        collector.tracker.update_channel_stats(f"telegram/{channel}")
    
    print(f"🎯 Всего собрано: {telegram_signals} РЕАЛЬНЫХ сигналов")

if __name__ == '__main__':
    asyncio.run(main())
