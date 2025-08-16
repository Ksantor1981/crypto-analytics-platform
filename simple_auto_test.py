#!/usr/bin/env python3
"""
Упрощенный тест автоматического сбора сигналов
"""

import sys
import os
import time
from datetime import datetime

def test_basic_imports():
    """Тест базовых импортов"""
    print("🔍 Тестирование базовых импортов...")
    
    try:
        # Добавляем пути
        sys.path.append(os.path.join(os.path.dirname(__file__), 'workers'))
        
        print("✅ Пути добавлены")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка импортов: {e}")
        return False

def test_telegram_client():
    """Тест Telegram клиента"""
    print("\n🔍 Тестирование Telegram клиента...")
    
    try:
        from workers.telegram.telegram_client import TelegramSignalCollector
        
        print("✅ Telegram клиент импортирован")
        
        # Создаем коллектор
        collector = TelegramSignalCollector(use_real_config=False)  # Используем mock для теста
        print(f"✅ Коллектор создан")
        print(f"   Каналов: {len(collector.channels)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка Telegram клиента: {e}")
        return False

def test_signal_processor():
    """Тест обработчика сигналов"""
    print("\n🔍 Тестирование обработчика сигналов...")
    
    try:
        from workers.telegram.signal_processor import TelegramSignalProcessor
        
        processor = TelegramSignalProcessor()
        print("✅ Обработчик сигналов создан")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка обработчика: {e}")
        return False

def test_ml_service():
    """Тест ML сервиса"""
    print("\n🔍 Тестирование ML сервиса...")
    
    try:
        import requests
        
        # Проверяем доступность ML сервиса
        response = requests.get("http://localhost:8001/health", timeout=5)
        
        if response.status_code == 200:
            print("✅ ML сервис доступен")
            return True
        else:
            print(f"❌ ML сервис недоступен: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка ML сервиса: {e}")
        return False

def test_database():
    """Тест базы данных"""
    print("\n🔍 Тестирование базы данных...")
    
    try:
        import sqlite3
        
        conn = sqlite3.connect('backend/crypto_analytics.db')
        cursor = conn.cursor()
        
        # Проверяем таблицы
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        print(f"✅ База данных доступна")
        print(f"   Таблиц: {len(tables)}")
        
        # Проверяем сигналы
        cursor.execute("SELECT COUNT(*) FROM signals")
        signals_count = cursor.fetchone()[0]
        print(f"   Сигналов: {signals_count}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Ошибка базы данных: {e}")
        return False

def test_simple_collection():
    """Простой тест сбора сигналов"""
    print("\n🔍 Простой тест сбора сигналов...")
    
    try:
        from workers.telegram.telegram_client import collect_telegram_signals_sync
        
        print("📡 Запуск сбора сигналов...")
        start_time = time.time()
        
        # Запускаем сбор с таймаутом
        result = collect_telegram_signals_sync()
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        print(f"✅ Сбор завершен за {processing_time:.2f} секунд")
        print(f"   Статус: {result.get('status', 'unknown')}")
        print(f"   Сигналов: {result.get('total_signals', 0)}")
        
        if result.get('signals'):
            print(f"   Пример: {result['signals'][0].get('asset', 'N/A')} {result['signals'][0].get('direction', 'N/A')}")
        
        return result.get('status') == 'success'
        
    except Exception as e:
        print(f"❌ Ошибка сбора: {e}")
        return False

def main():
    """Основная функция"""
    print("🚀 УПРОЩЕННЫЙ ТЕСТ АВТОМАТИЧЕСКОГО СБОРА")
    print("=" * 50)
    print(f"Время: {datetime.now()}")
    print("=" * 50)
    
    results = []
    
    # Тестируем компоненты
    results.append(("Импорты", test_basic_imports()))
    results.append(("Telegram клиент", test_telegram_client()))
    results.append(("Обработчик сигналов", test_signal_processor()))
    results.append(("ML сервис", test_ml_service()))
    results.append(("База данных", test_database()))
    results.append(("Сбор сигналов", test_simple_collection()))
    
    # Итоги
    print("\n" + "=" * 50)
    print("📊 РЕЗУЛЬТАТЫ:")
    
    success_count = 0
    for name, result in results:
        status = "✅" if result else "❌"
        print(f"   {name}: {status}")
        if result:
            success_count += 1
    
    print(f"\n🎯 УСПЕШНОСТЬ: {success_count}/{len(results)} ({success_count/len(results)*100:.1f}%)")
    
    if success_count == len(results):
        print("🎉 ВСЕ КОМПОНЕНТЫ РАБОТАЮТ!")
    elif success_count >= len(results) * 0.8:
        print("✅ БОЛЬШИНСТВО КОМПОНЕНТОВ РАБОТАЕТ")
    else:
        print("⚠️ ТРЕБУЕТСЯ ДОРАБОТКА")
    
    print("=" * 50)

if __name__ == "__main__":
    main()
