#!/usr/bin/env python3
"""
Тест сбора сигналов
"""

import sys
import os

# Добавляем пути
sys.path.append(os.path.join(os.path.dirname(__file__), 'workers'))

def test_signal_collection():
    """Тест сбора сигналов"""
    print("🔍 Тест сбора сигналов...")
    
    try:
        # Импортируем функцию сбора
        from workers.telegram.telegram_client import collect_telegram_signals_sync
        
        print("📡 Запуск сбора сигналов...")
        
        # Запускаем сбор
        result = collect_telegram_signals_sync()
        
        print(f"✅ Результат: {result.get('status', 'unknown')}")
        
        if result.get('signals'):
            print(f"   Сигналов собрано: {len(result['signals'])}")
            for i, signal in enumerate(result['signals'][:3], 1):
                print(f"   {i}. {signal.get('asset', 'N/A')} {signal.get('direction', 'N/A')} @ ${signal.get('entry_price', 'N/A')}")
        
        return result.get('status') == 'success'
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

def main():
    print("🚀 ТЕСТ СБОРА СИГНАЛОВ")
    print("=" * 30)
    
    if test_signal_collection():
        print("\n✅ Сбор сигналов работает!")
    else:
        print("\n❌ Сбор сигналов не работает")
    
    print("=" * 30)

if __name__ == "__main__":
    main()
