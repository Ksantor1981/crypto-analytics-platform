#!/usr/bin/env python3
"""
Упрощенный тест Telegram клиента
"""

import sys
import os
import asyncio
from datetime import datetime

# Добавляем пути для импорта
sys.path.append(os.path.join(os.path.dirname(__file__), 'workers'))

async def test_telegram_simple():
    """Простой тест Telegram клиента"""
    print("🔍 Простой тест Telegram клиента...")
    
    try:
        from workers.telegram.telegram_client import TelegramSignalCollector
        
        print("📡 Создание коллектора...")
        collector = TelegramSignalCollector(use_real_config=True)
        
        print("🔐 Инициализация клиента...")
        if await collector.initialize_client():
            print("✅ Клиент инициализирован")
            
            print("📡 Сбор сигналов...")
            result = await collector.collect_signals()
            
            print(f"✅ Результат: {result.get('status', 'unknown')}")
            
            if result.get('signals'):
                print(f"   Сигналов собрано: {len(result['signals'])}")
                for i, signal in enumerate(result['signals'][:3], 1):
                    print(f"   {i}. {signal.get('asset', 'N/A')} {signal.get('direction', 'N/A')} @ ${signal.get('entry_price', 'N/A')}")
                    print(f"      Канал: {signal.get('channel', 'N/A')}")
            else:
                print("   Сигналов не найдено")
            
            # Закрываем клиент
            if collector.client:
                await collector.client.disconnect()
            
            return result.get('status') == 'success'
        else:
            print("❌ Не удалось инициализировать клиент")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

async def main():
    """Основная функция"""
    print("🚀 ПРОСТОЙ ТЕСТ TELEGRAM")
    print("=" * 30)
    print(f"Время: {datetime.now()}")
    print("=" * 30)
    
    success = await test_telegram_simple()
    
    print("\n" + "=" * 30)
    if success:
        print("🎉 TELEGRAM КЛИЕНТ РАБОТАЕТ!")
    else:
        print("❌ TELEGRAM КЛИЕНТ НЕ РАБОТАЕТ")
    print("=" * 30)

if __name__ == "__main__":
    asyncio.run(main())
