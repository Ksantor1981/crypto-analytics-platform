#!/usr/bin/env python3
"""
Упрощенный тест парсинга сигналов
"""

import sys
import os
import sqlite3
from datetime import datetime

# Добавляем пути для импорта
sys.path.append(os.path.join(os.path.dirname(__file__), 'workers'))

def test_signal_parsing():
    """Тест парсинга сигналов"""
    print("🔍 Тестирование парсинга сигналов...")
    
    # Примеры реальных сигналов
    test_signals = [
        {
            "text": "🚀 BTC/USDT LONG\nEntry: 117,500\nTarget 1: 120,000\nTarget 2: 122,500\nStop Loss: 115,000\nLeverage: 10x",
            "channel": "@cryptosignals"
        },
        {
            "text": "📉 ETH/USDT SHORT\nВход: 3,200\nЦель: 3,000\nСтоп: 3,300\nПлечо: 5x",
            "channel": "@binancesignals"
        },
        {
            "text": "🔥 SOL/USDT BUY\nEntry Price: $100\nTake Profit: $110\nStop Loss: $95\nConfidence: HIGH",
            "channel": "@cryptotradingview"
        }
    ]
    
    # Простой парсер сигналов
    def parse_signal(text, channel):
        """Простой парсер сигналов"""
        import re
        
        # Паттерны для извлечения данных
        patterns = {
            'asset': r'([A-Z]{2,6})/?(?:USDT|USD|BTC)',
            'direction': r'\b(LONG|SHORT|BUY|SELL)\b',
            'entry': r'(?:entry|вход|цена входа|enter at)[:\s]*([0-9,]+)',
            'target': r'(?:target|tp|цель|тп|take profit)[:\s]*([0-9,]+)',
            'stop_loss': r'(?:sl|stop.?loss|стоп|стоп.?лосс|stop at)[:\s]*([0-9,]+)',
            'leverage': r'(?:leverage|плечо)[:\s]*([0-9]+)x?'
        }
        
        result = {}
        
        # Извлекаем актив
        asset_match = re.search(patterns['asset'], text, re.IGNORECASE)
        if asset_match:
            result['asset'] = asset_match.group(1)
        
        # Извлекаем направление
        direction_match = re.search(patterns['direction'], text, re.IGNORECASE)
        if direction_match:
            result['direction'] = direction_match.group(1).upper()
        
        # Извлекаем цену входа
        entry_match = re.search(patterns['entry'], text, re.IGNORECASE)
        if entry_match:
            result['entry_price'] = float(entry_match.group(1).replace(',', ''))
        else:
            # Попробуем найти цену в другом формате
            entry_match = re.search(r'Entry Price: \$?([0-9,]+)', text, re.IGNORECASE)
            if entry_match:
                result['entry_price'] = float(entry_match.group(1).replace(',', ''))
        
        # Извлекаем цель
        target_match = re.search(patterns['target'], text, re.IGNORECASE)
        if target_match:
            result['target_price'] = float(target_match.group(1).replace(',', ''))
        
        # Извлекаем стоп-лосс
        sl_match = re.search(patterns['stop_loss'], text, re.IGNORECASE)
        if sl_match:
            result['stop_loss'] = float(sl_match.group(1).replace(',', ''))
        
        # Извлекаем плечо
        leverage_match = re.search(patterns['leverage'], text, re.IGNORECASE)
        if leverage_match:
            result['leverage'] = int(leverage_match.group(1))
        
        # Добавляем метаданные
        result['channel'] = channel
        result['confidence'] = 0.7  # Базовая уверенность
        result['timestamp'] = datetime.now()
        
        return result if result.get('asset') and result.get('direction') else None
    
    # Тестируем парсинг
    for i, signal in enumerate(test_signals, 1):
        print(f"\n📊 Тест сигнала #{i}:")
        print(f"   Канал: {signal['channel']}")
        print(f"   Текст: {signal['text'][:50]}...")
        
        # Парсим сигнал
        parsed = parse_signal(signal['text'], signal['channel'])
        
        if parsed:
            print(f"✅ Сигнал распознан:")
            print(f"   Актив: {parsed.get('asset', 'N/A')}")
            print(f"   Направление: {parsed.get('direction', 'N/A')}")
            print(f"   Вход: ${parsed.get('entry_price', 'N/A')}")
            print(f"   Цель: ${parsed.get('target_price', 'N/A')}")
            print(f"   Стоп: ${parsed.get('stop_loss', 'N/A')}")
            print(f"   Плечо: {parsed.get('leverage', 'N/A')}x")
            print(f"   Уверенность: {parsed.get('confidence', 'N/A')}")
            
            # Сохраняем в базу данных
            save_to_database(parsed)
        else:
            print(f"❌ Сигнал не распознан")

def save_to_database(signal_data):
    """Сохраняем сигнал в базу данных"""
    try:
        conn = sqlite3.connect('backend/crypto_analytics.db')
        cursor = conn.cursor()
        
        # Проверяем, есть ли канал
        cursor.execute("SELECT id FROM channels WHERE url = ?", (signal_data['channel'],))
        channel_result = cursor.fetchone()
        
        if channel_result:
            channel_id = channel_result[0]
        else:
            # Создаем новый канал
            cursor.execute("""
                INSERT INTO channels (name, platform, url, category, is_active, created_at, owner_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                signal_data['channel'].replace('@', ''),
                'telegram',
                signal_data['channel'],
                'crypto',
                True,
                datetime.now(),
                1  # Default owner_id
            ))
            channel_id = cursor.lastrowid
        
        # Сохраняем сигнал
        cursor.execute("""
            INSERT INTO signals (
                channel_id, asset, direction, entry_price, tp1_price, stop_loss,
                original_text, message_timestamp, status, confidence_score, created_at, symbol
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            channel_id,
            signal_data['asset'],
            signal_data['direction'],
            signal_data['entry_price'],
            signal_data.get('target_price'),
            signal_data.get('stop_loss'),
            f"Parsed signal for {signal_data['asset']}",
            signal_data['timestamp'],
            'PENDING',
            signal_data['confidence'],
            datetime.now(),
            f"{signal_data['asset']}/USDT"  # Symbol
        ))
        
        signal_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        print(f"💾 Сигнал сохранен в БД (ID: {signal_id})")
        
    except Exception as e:
        print(f"❌ Ошибка сохранения в БД: {e}")

def check_database():
    """Проверяем базу данных"""
    print("\n🔍 Проверка базы данных...")
    
    try:
        conn = sqlite3.connect('backend/crypto_analytics.db')
        cursor = conn.cursor()
        
        # Проверяем каналы
        cursor.execute("SELECT COUNT(*) FROM channels")
        channels_count = cursor.fetchone()[0]
        print(f"📺 Каналов в БД: {channels_count}")
        
        # Проверяем сигналы
        cursor.execute("SELECT COUNT(*) FROM signals")
        signals_count = cursor.fetchone()[0]
        print(f"📈 Сигналов в БД: {signals_count}")
        
        if signals_count > 0:
            # Показываем последние сигналы
            cursor.execute("""
                SELECT s.asset, s.direction, s.entry_price, s.status, c.name
                FROM signals s
                JOIN channels c ON s.channel_id = c.id
                ORDER BY s.created_at DESC
                LIMIT 5
            """)
            
            signals = cursor.fetchall()
            print("\n📊 Последние сигналы:")
            for signal in signals:
                print(f"   {signal[0]} {signal[1]} @ ${signal[2]} - {signal[3]} (канал: {signal[4]})")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Ошибка проверки БД: {e}")

def main():
    """Основная функция"""
    print("🚀 УПРОЩЕННЫЙ ТЕСТ ПАРСИНГА СИГНАЛОВ")
    print("=" * 50)
    print(f"Время: {datetime.now()}")
    print("=" * 50)
    
    try:
        # Проверяем БД до тестов
        check_database()
        
        # Тестируем парсинг
        test_signal_parsing()
        
        # Проверяем БД после тестов
        check_database()
        
        print("\n" + "=" * 50)
        print("✅ ТЕСТ ЗАВЕРШЕН!")
        print("=" * 50)
        
    except Exception as e:
        print(f"\n❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
        print("=" * 50)

if __name__ == "__main__":
    main()
