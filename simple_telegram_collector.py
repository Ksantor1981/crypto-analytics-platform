#!/usr/bin/env python3
"""
Упрощенный сборщик РЕАЛЬНЫХ данных из Telegram
Без внешних зависимостей
"""
import os
import sqlite3
import asyncio
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Загружаем данные из .env
def load_env():
    """Загружает данные из .env файла"""
    env_path = Path('.env')
    if env_path.exists():
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value

# Простые паттерны для извлечения сигналов
SIGNAL_PATTERNS = [
    r'BTC.*?(\d{4,6})[^\d]*?(\d{4,6})',
    r'ETH.*?(\d{3,5})[^\d]*?(\d{3,5})',
    r'SOL.*?(\d{2,4})[^\d]*?(\d{2,4})',
    r'ADA.*?(\d\.\d{1,3})[^\d]*?(\d\.\d{1,3})',
    r'LINK.*?(\d{1,3})[^\d]*?(\d{1,3})',
    r'MATIC.*?(\d\.\d{1,3})[^\d]*?(\d\.\d{1,3})',
]

def extract_signal_from_text(text, source, message_id):
    """Извлекает сигнал из текста"""
    if not text:
        return None
    
    import re
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
                        
                        # Простая валидация
                        if entry_price <= 0 or target_price <= 0:
                            continue
                        
                        # Определяем направление
                        direction = 'LONG' if target_price > entry_price else 'SHORT'
                        
                        # Рассчитываем stop loss
                        stop_loss = entry_price * 0.98 if direction == 'LONG' else entry_price * 1.02
                        
                        return {
                            'asset': asset,
                            'direction': direction,
                            'entry_price': entry_price,
                            'target_price': target_price,
                            'stop_loss': stop_loss,
                            'confidence': 75.0,  # Базовая уверенность
                            'is_valid': 1,
                            'source': source,
                            'message_id': message_id,
                            'original_text': text
                        }
                        
                    except (ValueError, TypeError):
                        continue
    
    return None

def save_signal_to_db(signal_data, timestamp):
    """Сохраняет сигнал в БД"""
    conn = sqlite3.connect('workers/signals.db')
    cur = conn.cursor()
    
    signal_id = f"telegram_{signal_data['asset']}_{signal_data['message_id']}"
    
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
        signal_id, signal_data['asset'], signal_data['direction'],
        signal_data['entry_price'], signal_data['target_price'], signal_data['stop_loss'],
        1, '1H', 'verified', signal_data['confidence'], signal_data['confidence'],
        signal_data['source'], signal_data['message_id'], signal_data['original_text'],
        signal_data['original_text'], 'telegram_real', timestamp.isoformat(),
        datetime.now(timezone.utc).isoformat(), True, signal_data['is_valid'],
        json.dumps([], ensure_ascii=False), 0.0, 0.0, 0.0
    ))
    
    conn.commit()
    conn.close()
    
    print(f"✅ {signal_data['asset']} @ ${signal_data['entry_price']} -> ${signal_data['target_price']} | {signal_data['source']}")

async def collect_from_telegram():
    """Собирает данные из Telegram"""
    try:
        from telethon import TelegramClient
        from telethon.errors import SessionPasswordNeededError
        print("✅ Telethon импортирован успешно")
    except ImportError:
        print("❌ Telethon не установлен")
        return 0
    
    api_id = os.getenv('TELEGRAM_API_ID')
    api_hash = os.getenv('TELEGRAM_API_HASH')
    phone = os.getenv('TELEGRAM_PHONE')
    
    if not all([api_id, api_hash, phone]):
        print("❌ Не все данные Telegram API настроены")
        return 0
    
    print(f"📡 Подключение к Telegram...")
    print(f"   API_ID: {api_id}")
    print(f"   API_HASH: {api_hash[:10]}...")
    print(f"   PHONE: {phone}")
    
    client = TelegramClient('crypto_signals_session', api_id, api_hash)
    
    try:
        await client.start(phone=phone)
        print("✅ Подключение к Telegram успешно")
        
        # Список каналов для сбора
        channels = [
            'CryptoPapa', 'FatPigSignals', 'WallstreetQueenOfficial',
            'RocketWalletSignals', 'BinanceKiller', 'WolfOfTrading',
            'CryptoSignalsOrg', 'Learn2Trade', 'UniversalCryptoSignals'
        ]
        
        total_signals = 0
        
        for channel_name in channels:
            try:
                print(f"📊 Сбор из {channel_name}...")
                entity = await client.get_entity(channel_name)
                messages = await client.get_messages(entity, limit=50)
                
                channel_signals = 0
                for msg in messages:
                    if msg.text:
                        signal = extract_signal_from_text(msg.text, f"telegram/{channel_name}", str(msg.id))
                        if signal:
                            await asyncio.sleep(0.1)  # Небольшая задержка
                            save_signal_to_db(signal, msg.date)
                            channel_signals += 1
                            total_signals += 1
                
                print(f"   📈 Собрано {channel_signals} сигналов из {channel_name}")
                
            except Exception as e:
                print(f"   ❌ Ошибка сбора из {channel_name}: {str(e)[:50]}")
        
        await client.disconnect()
        print(f"✅ Сбор завершен. Всего собрано: {total_signals} сигналов")
        return total_signals
        
    except Exception as e:
        print(f"❌ Ошибка подключения к Telegram: {e}")
        return 0

async def main():
    """Основная функция"""
    print("🚀 Упрощенный сбор РЕАЛЬНЫХ данных из Telegram")
    print("=" * 50)
    
    # Загружаем данные из .env
    load_env()
    
    # Собираем данные
    signals_count = await collect_from_telegram()
    
    if signals_count > 0:
        print(f"\n🎉 Успешно собрано {signals_count} РЕАЛЬНЫХ сигналов!")
        print("✅ Теперь запустите дашборд: python start_dashboard.py")
    else:
        print("\n❌ Не удалось собрать данные")

if __name__ == '__main__':
    asyncio.run(main())
