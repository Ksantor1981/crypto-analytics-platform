#!/usr/bin/env python3
import sqlite3

try:
    conn = sqlite3.connect('backend/crypto_analytics.db')
    cursor = conn.cursor()
    
    # Получаем список таблиц
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    
    print("📊 Таблицы в базе данных:")
    for table in tables:
        print(f"   - {table[0]}")
    
    # Проверяем таблицу signals
    if ('signals',) in tables:
        cursor.execute("SELECT COUNT(*) FROM signals")
        count = cursor.fetchone()[0]
        print(f"\n📈 Сигналов в базе: {count}")
        
        if count > 0:
            cursor.execute("SELECT asset, direction, entry_price, status FROM signals LIMIT 5")
            signals = cursor.fetchall()
            print("\n🔍 Последние сигналы:")
            for signal in signals:
                print(f"   {signal[0]} {signal[1]} @ ${signal[2]} - {signal[3]}")
    else:
        print("\n❌ Таблица signals не найдена!")
    
    conn.close()
    
except Exception as e:
    print(f"❌ Ошибка: {e}")
