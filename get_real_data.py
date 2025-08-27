#!/usr/bin/env python3
"""
Сбор РЕАЛЬНЫХ данных из Telegram и других источников
"""
import os
import sqlite3
import json
import re
from datetime import datetime, timezone
from pathlib import Path

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
        print("✅ Данные из .env загружены")

def test_telegram_connection():
    """Тестирует подключение к Telegram"""
    print("🔍 Проверка Telegram API...")
    
    api_id = os.getenv('TELEGRAM_API_ID')
    api_hash = os.getenv('TELEGRAM_API_HASH')
    
    print(f"API_ID: {api_id}")
    print(f"API_HASH: {api_hash[:10] if api_hash else 'None'}...")
    
    if not all([api_id, api_hash]):
        print("❌ Telegram API данные не настроены")
        return False
    
    try:
        import telethon
        print(f"✅ Telethon установлен: {telethon.__version__}")
        return True
    except ImportError:
        print("❌ Telethon не установлен")
        return False

def collect_from_telegram():
    """Собирает РЕАЛЬНЫЕ данные из Telegram"""
    print("📡 Сбор РЕАЛЬНЫХ данных из Telegram...")
    
    try:
        from telethon import TelegramClient
        from telethon.errors import SessionPasswordNeededError
    except ImportError:
        print("❌ Telethon не установлен")
        return 0
    
    api_id = os.getenv('TELEGRAM_API_ID')
    api_hash = os.getenv('TELEGRAM_API_HASH')
    phone = os.getenv('TELEGRAM_PHONE')
    
    if not phone:
        print("📱 Введите номер телефона:")
        phone = input("Номер (с кодом страны, например +7): ").strip()
    
    if not all([api_id, api_hash, phone]):
        print("❌ Не все данные Telegram API настроены")
        return 0
    
    print(f"🔗 Подключение к Telegram...")
    print(f"   API_ID: {api_id}")
    print(f"   API_HASH: {api_hash[:10]}...")
    print(f"   PHONE: {phone}")
    
    client = TelegramClient('crypto_signals_session', api_id, api_hash)
    
    try:
        client.connect()
        
        if not client.is_user_authorized():
            print("📱 Требуется авторизация...")
            client.send_code_request(phone)
            code = input("Введите код из Telegram: ").strip()
            
            try:
                client.sign_in(phone, code)
                print("✅ Авторизация успешна!")
            except SessionPasswordNeededError:
                password = input("Введите пароль 2FA: ").strip()
                client.sign_in(password=password)
                print("✅ Авторизация с 2FA успешна!")
        else:
            print("✅ Уже авторизован")
        
        # Список РЕАЛЬНЫХ каналов для сбора
        channels = [
            'CryptoPapa', 'FatPigSignals', 'WallstreetQueenOfficial',
            'RocketWalletSignals', 'BinanceKiller', 'WolfOfTrading',
            'CryptoSignalsOrg', 'Learn2Trade', 'UniversalCryptoSignals',
            'OnwardBTC', 'CryptoClassics', 'MyCryptoParadise'
        ]
        
        total_signals = 0
        
        for channel_name in channels:
            try:
                print(f"📊 Сбор из {channel_name}...")
                entity = client.get_entity(channel_name)
                messages = client.get_messages(entity, limit=100)
                
                channel_signals = 0
                for msg in messages:
                    if msg.text:
                        signal = extract_signal_from_text(msg.text, f"telegram/{channel_name}", str(msg.id))
                        if signal:
                            save_signal_to_db(signal, msg.date)
                            channel_signals += 1
                            total_signals += 1
                
                print(f"   📈 Собрано {channel_signals} РЕАЛЬНЫХ сигналов из {channel_name}")
                
            except Exception as e:
                print(f"   ❌ Ошибка сбора из {channel_name}: {str(e)[:50]}")
        
        client.disconnect()
        print(f"✅ Сбор завершен. Всего собрано: {total_signals} РЕАЛЬНЫХ сигналов")
        return total_signals
        
    except Exception as e:
        print(f"❌ Ошибка подключения к Telegram: {e}")
        return 0

def extract_signal_from_text(text, source, message_id):
    """Извлекает РЕАЛЬНЫЙ сигнал из текста"""
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
    
    # Ищем РЕАЛЬНЫЕ цены
    price_patterns = [
        rf'{asset}.*?(\d{{4,6}})[^\d]*?(\d{{4,6}})',
        rf'(\d{{4,6}})[^\d]*?{asset}[^\d]*?(\d{{4,6}})',
        rf'{asset}.*?(\d{{3,5}})[^\d]*?(\d{{3,5}})',
        rf'(\d{{3,5}})[^\d]*?{asset}[^\d]*?(\d{{3,5}})',
    ]
    
    for pattern in price_patterns:
        matches = re.findall(pattern, text_upper)
        for match in matches:
            if len(match) == 2:
                try:
                    entry_price = float(match[0])
                    target_price = float(match[1])
                    
                    # Валидация РЕАЛЬНЫХ цен
                    if entry_price <= 0 or target_price <= 0:
                        continue
                    
                    # Проверяем разумность цен
                    if asset == 'BTC' and (entry_price < 10000 or entry_price > 200000):
                        continue
                    elif asset == 'ETH' and (entry_price < 1000 or entry_price > 10000):
                        continue
                    elif asset == 'SOL' and (entry_price < 10 or entry_price > 1000):
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
                        'confidence': 75.0,
                        'is_valid': 1,
                        'source': source,
                        'message_id': message_id,
                        'original_text': text[:200]
                    }
                    
                except (ValueError, TypeError):
                    continue
    
    return None

def save_signal_to_db(signal_data, timestamp):
    """Сохраняет РЕАЛЬНЫЙ сигнал в БД"""
    conn = sqlite3.connect('workers/signals.db')
    cur = conn.cursor()
    
    signal_id = f"real_{signal_data['asset']}_{signal_data['message_id']}"
    
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
    
    print(f"✅ РЕАЛЬНЫЙ сигнал: {signal_data['asset']} @ ${signal_data['entry_price']} -> ${signal_data['target_price']} | {signal_data['source']}")

def main():
    """Основная функция"""
    print("🚀 Сбор РЕАЛЬНЫХ данных из Telegram")
    print("=" * 50)
    
    # Загружаем данные из .env
    load_env()
    
    # Проверяем Telegram
    if test_telegram_connection():
        # Собираем РЕАЛЬНЫЕ данные
        signals_count = collect_from_telegram()
        
        if signals_count > 0:
            print(f"\n🎉 Успешно собрано {signals_count} РЕАЛЬНЫХ сигналов!")
            print("✅ Теперь у вас есть РЕАЛЬНЫЕ данные!")
        else:
            print("\n❌ Не удалось собрать РЕАЛЬНЫЕ данные")
    else:
        print("\n❌ Telegram не настроен")

if __name__ == '__main__':
    main()
