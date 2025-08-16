#!/usr/bin/env python3
"""
Тест worker'а
"""

import sys
import os

# Добавляем пути
sys.path.append(os.path.join(os.path.dirname(__file__), 'workers'))

def test_worker_import():
    """Тест импорта worker'а"""
    print("🔍 Тест импорта worker'а...")
    try:
        from workers.tasks import collect_telegram_signals
        print("✅ Worker импортирован")
        return True
    except Exception as e:
        print(f"❌ Ошибка импорта: {e}")
        return False

def test_telegram_collection():
    """Тест сбора сигналов"""
    print("🔍 Тест сбора сигналов...")
    try:
        from workers.tasks import collect_telegram_signals
        
        print("📡 Запуск сбора...")
        result = collect_telegram_signals()
        
        print(f"✅ Результат: {result.get('status', 'unknown')}")
        if result.get('signals'):
            print(f"   Сигналов: {len(result.get('signals', []))}")
        
        return result.get('status') == 'success'
    except Exception as e:
        print(f"❌ Ошибка сбора: {e}")
        return False

def main():
    print("🚀 ТЕСТ WORKER'А")
    print("=" * 30)
    
    # Тест импорта
    if not test_worker_import():
        print("❌ Worker не работает")
        return
    
    # Тест сбора
    if test_telegram_collection():
        print("✅ Автоматический сбор работает!")
    else:
        print("❌ Автоматический сбор не работает")
    
    print("=" * 30)

if __name__ == "__main__":
    main()
