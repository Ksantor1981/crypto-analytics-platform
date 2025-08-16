#!/usr/bin/env python3
"""
Запуск автоматического сбора сигналов
"""

import sys
import os
import time
from datetime import datetime

# Добавляем пути
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def run_auto_collection():
    """Запуск автоматического сбора"""
    print("🚀 ЗАПУСК АВТОМАТИЧЕСКОГО СБОРА СИГНАЛОВ")
    print("=" * 50)
    print(f"Время: {datetime.now()}")
    print("=" * 50)
    
    try:
        # Импортируем функцию сбора
        from workers.telegram.telegram_client import collect_telegram_signals_sync
        
        print("📡 Запуск сбора сигналов...")
        start_time = time.time()
        
        # Запускаем сбор
        result = collect_telegram_signals_sync()
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        print(f"✅ Сбор завершен за {processing_time:.2f} секунд")
        print(f"   Статус: {result.get('status', 'unknown')}")
        print(f"   Сигналов: {result.get('total_signals', 0)}")
        
        if result.get('signals'):
            print(f"\n📊 Собранные сигналы:")
            for i, signal in enumerate(result['signals'][:5], 1):
                print(f"   {i}. {signal.get('asset', 'N/A')} {signal.get('direction', 'N/A')}")
                print(f"      Вход: ${signal.get('entry_price', 'N/A')}")
                print(f"      Канал: {signal.get('channel', 'N/A')}")
                print()
        
        # Проверяем базу данных
        print("🔍 Проверка базы данных...")
        import sqlite3
        conn = sqlite3.connect('backend/crypto_analytics.db')
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM signals")
        total_signals = cursor.fetchone()[0]
        conn.close()
        
        print(f"   Всего сигналов в БД: {total_signals}")
        
        print("\n" + "=" * 50)
        if result.get('status') == 'success':
            print("🎉 АВТОМАТИЧЕСКИЙ СБОР РАБОТАЕТ!")
        else:
            print("⚠️ Сбор завершился с ошибкой")
        print("=" * 50)
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        print("=" * 50)

if __name__ == "__main__":
    run_auto_collection()
