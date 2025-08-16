#!/usr/bin/env python3
"""
Тест исправленного worker'а
"""

import sys
import os

# Добавляем пути
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def test_worker_import():
    """Тест импорта worker'а"""
    print("🔍 Тест импорта worker'а...")
    try:
        from workers.tasks import collect_telegram_signals
        print("✅ Worker импортирован успешно")
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
    print("🚀 ТЕСТ ИСПРАВЛЕННОГО WORKER'А")
    print("=" * 40)
    
    # Тест импорта
    if not test_worker_import():
        print("❌ Worker не работает")
        return
    
    # Тест сбора
    if test_telegram_collection():
        print("\n✅ АВТОМАТИЧЕСКИЙ СБОР РАБОТАЕТ!")
    else:
        print("\n❌ Автоматический сбор не работает")
    
    print("=" * 40)

if __name__ == "__main__":
    main()
