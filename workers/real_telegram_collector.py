#!/usr/bin/env python3
"""
Сборщик РЕАЛЬНЫХ сигналов из Telegram каналов
Использует Telethon для подключения к реальным каналам
"""
import os
import json
import sqlite3
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List
import re
from pathlib import Path

# Telethon для работы с Telegram API
try:
    from telethon import TelegramClient, events
    from telethon.tl.types import Channel, Message
except ImportError:
    print("❌ Telethon не установлен. Установите: pip install telethon")
    exit(1)

BASE_DIR = Path(__file__).parent
DB_PATH = str(BASE_DIR / 'signals.db')

# Конфигурация Telegram API (заполните своими данными)
API_ID = os.getenv('TELEGRAM_API_ID', '')
API_HASH = os.getenv('TELEGRAM_API_HASH', '')
PHONE_NUMBER = os.getenv('TELEGRAM_PHONE', '')

# Реальные Telegram каналы с сигналами
REAL_CHANNELS = [
    'CryptoPapa',
    'FatPigSignals', 
    'WallstreetQueenOfficial',
    'RocketWalletSignals',
    'BinanceKiller',
    'WolfOfTrading',
    'CryptoSignalsOrg',
    'Learn2Trade',
    'UniversalCryptoSignals',
    'OnwardBTC'
]

# Паттерны для извлечения реальных сигналов
SIGNAL_PATTERNS = [
    # BTC/USDT
    r'BTC.*?(\d{4,6})[^\d]*?(\d{4,6})',  # BTC 45000 -> 50000
    r'Bitcoin.*?(\d{4,6})[^\d]*?(\d{4,6})',  # Bitcoin 45000 -> 50000
    
    # ETH/USDT
    r'ETH.*?(\d{3,5})[^\d]*?(\d{3,5})',  # ETH 3000 -> 3500
    r'Ethereum.*?(\d{3,5})[^\d]*?(\d{3,5})',  # Ethereum 3000 -> 3500
    
    # SOL/USDT
    r'SOL.*?(\d{2,4})[^\d]*?(\d{2,4})',  # SOL 150 -> 200
    r'Solana.*?(\d{2,4})[^\d]*?(\d{2,4})',  # Solana 150 -> 200
    
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

def extract_signal_from_text(text: str) -> Dict[str, Any]:
    """Извлекает сигнал из текста сообщения"""
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
                        
                        # Определяем направление
                        direction = 'LONG' if target_price > entry_price else 'SHORT'
                        
                        # Рассчитываем stop loss (примерно 2% от entry)
                        stop_loss = entry_price * 0.98 if direction == 'LONG' else entry_price * 1.02
                        
                        return {
                            'asset': asset,
                            'direction': direction,
                            'entry_price': entry_price,
                            'target_price': target_price,
                            'stop_loss': stop_loss,
                            'confidence': 75.0,  # базовая уверенность
                            'is_valid': 1
                        }
                    except (ValueError, TypeError):
                        continue
    
    return None

def upsert_signal(cur: sqlite3.Cursor, signal_data: Dict[str, Any]) -> None:
    """Сохраняет сигнал в БД"""
    cur.execute(
        """
        INSERT OR REPLACE INTO signals (
            id, asset, direction, entry_price, target_price, stop_loss,
            leverage, timeframe, signal_quality, real_confidence,
            calculated_confidence, channel, message_id, original_text,
            cleaned_text, signal_type, timestamp, extraction_time,
            bybit_available, is_valid, validation_errors,
            risk_reward_ratio, potential_profit, potential_loss
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            signal_data['id'], signal_data['asset'], signal_data['direction'],
            signal_data['entry_price'], signal_data['target_price'], signal_data['stop_loss'],
            signal_data.get('leverage', 1), signal_data.get('timeframe', '1H'),
            signal_data.get('signal_quality', 'verified'), signal_data.get('real_confidence', 0.0),
            signal_data.get('calculated_confidence', 0.0), signal_data.get('channel', ''),
            signal_data.get('message_id', ''), signal_data.get('original_text', ''),
            signal_data.get('original_text', ''), signal_data.get('signal_type', 'telegram_real'),
            signal_data.get('timestamp'), signal_data.get('extraction_time'),
            True, signal_data.get('is_valid', 1),
            json.dumps(signal_data.get('validation_errors', []), ensure_ascii=False),
            signal_data.get('risk_reward_ratio', 0.0), signal_data.get('potential_profit', 0.0),
            signal_data.get('potential_loss', 0.0)
        ),
    )

async def collect_from_channel(client: TelegramClient, channel_name: str, limit: int = 50) -> List[Dict[str, Any]]:
    """Собирает сообщения из канала"""
    try:
        print(f"📡 Подключение к каналу: {channel_name}")
        
        # Получаем канал
        channel = await client.get_entity(channel_name)
        
        # Получаем последние сообщения
        messages = await client.get_messages(channel, limit=limit)
        
        signals = []
        for msg in messages:
            if not msg.text:
                continue
                
            signal = extract_signal_from_text(msg.text)
            if signal:
                # Добавляем метаданные
                signal.update({
                    'id': f"tg_{channel_name}_{msg.id}_{int(msg.date.timestamp())}",
                    'channel': f"telegram/{channel_name}",
                    'message_id': str(msg.id),
                    'original_text': msg.text,
                    'timestamp': msg.date.isoformat(),
                    'extraction_time': datetime.now(timezone.utc).isoformat(),
                    'signal_type': 'telegram_real',
                    'signal_quality': 'verified',
                    'real_confidence': signal['confidence'],
                    'calculated_confidence': signal['confidence'],
                    'timeframe': '1H',
                    'leverage': 1,
                    'bybit_available': True,
                    'validation_errors': [],
                    'risk_reward_ratio': abs((signal['target_price'] - signal['entry_price']) / (signal['entry_price'] - signal['stop_loss'])),
                    'potential_profit': abs(signal['target_price'] - signal['entry_price']),
                    'potential_loss': abs(signal['entry_price'] - signal['stop_loss'])
                })
                signals.append(signal)
                print(f"✅ {signal['asset']} @ ${signal['entry_price']} -> ${signal['target_price']} | {channel_name}")
        
        return signals
        
    except Exception as e:
        print(f"❌ Ошибка сбора из {channel_name}: {e}")
        return []

async def run_telegram_collection():
    """Запускает сбор из Telegram каналов"""
    if not API_ID or not API_HASH or not PHONE_NUMBER:
        print("❌ Не заданы Telegram API данные. Установите переменные окружения:")
        print("   TELEGRAM_API_ID - ваш API ID")
        print("   TELEGRAM_API_HASH - ваш API Hash") 
        print("   TELEGRAM_PHONE - ваш номер телефона")
        return 0
    
    print("🚀 Запуск сбора РЕАЛЬНЫХ сигналов из Telegram...")
    
    # Создаем клиент
    client = TelegramClient('crypto_signals_session', API_ID, API_HASH)
    
    try:
        await client.start(phone=PHONE_NUMBER)
        print("✅ Подключение к Telegram успешно")
        
        # Очищаем БД
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("DELETE FROM signals WHERE signal_type = 'telegram_real'")
        print("🗑️ Очищены старые Telegram сигналы")
        
        total_signals = 0
        
        # Собираем из каждого канала
        for channel_name in REAL_CHANNELS:
            signals = await collect_from_channel(client, channel_name)
            
            for signal in signals:
                try:
                    upsert_signal(cur, signal)
                    total_signals += 1
                except Exception as e:
                    print(f"❌ Ошибка сохранения сигнала: {e}")
        
        conn.commit()
        conn.close()
        
        print(f"🎯 Собрано {total_signals} РЕАЛЬНЫХ сигналов из Telegram")
        return total_signals
        
    except Exception as e:
        print(f"❌ Ошибка подключения к Telegram: {e}")
        return 0
    finally:
        await client.disconnect()

def run_collection():
    """Запускает асинхронный сбор"""
    return asyncio.run(run_telegram_collection())

if __name__ == '__main__':
    run_collection()
