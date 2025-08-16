#!/usr/bin/env python3
"""
Тест подключения к реальным Telegram каналам
"""

import sys
import os
import asyncio
from datetime import datetime

# Добавляем пути для импорта
sys.path.append(os.path.join(os.path.dirname(__file__), 'workers'))

async def test_telegram_connection():
    """Тест подключения к Telegram"""
    print("🔍 Тест подключения к Telegram...")
    
    try:
        from workers.telegram.telegram_client import TelegramSignalCollector
        from workers.real_data_config import REAL_TELEGRAM_CHANNELS
        
        print(f"📡 Найдено каналов: {len(REAL_TELEGRAM_CHANNELS)}")
        
        # Создаем коллектор с реальной конфигурацией
        collector = TelegramSignalCollector(use_real_config=True)
        
        print("🔐 Инициализация клиента...")
        if await collector.initialize_client():
            print("✅ Клиент инициализирован")
            
            # Проверяем подключение к каналам
            print("📺 Проверка каналов...")
            for channel in REAL_TELEGRAM_CHANNELS[:3]:  # Проверяем первые 3 канала
                username = channel['username']
                print(f"   Проверяем {username}...")
                
                try:
                    # Пытаемся получить информацию о канале через client
                    if collector.client:
                        entity = await collector.client.get_entity(username)
                        if entity:
                            title = getattr(entity, 'title', 'N/A')
                            participants_count = getattr(entity, 'participants_count', 'N/A')
                            print(f"   ✅ {username}: {title} ({participants_count} участников)")
                        else:
                            print(f"   ⚠️ {username}: не удалось получить информацию")
                    else:
                        print(f"   ⚠️ {username}: клиент не инициализирован")
                except Exception as e:
                    print(f"   ❌ {username}: ошибка - {e}")
            
            return True
        else:
            print("❌ Не удалось инициализировать клиент")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

async def test_signal_collection():
    """Тест сбора сигналов"""
    print("\n🔍 Тест сбора сигналов...")
    
    try:
        from workers.telegram.telegram_client import TelegramSignalCollector
        
        print("📡 Запуск сбора сигналов...")
        
        # Создаем коллектор и собираем сигналы
        collector = TelegramSignalCollector(use_real_config=True)
        try:
            result = await collector.collect_signals()
            
            print(f"✅ Результат: {result.get('status', 'unknown')}")
            
            if result.get('signals'):
                print(f"   Сигналов собрано: {len(result['signals'])}")
                for i, signal in enumerate(result['signals'][:3], 1):
                    print(f"   {i}. {signal.get('asset', 'N/A')} {signal.get('direction', 'N/A')} @ ${signal.get('entry_price', 'N/A')}")
                    print(f"      Канал: {signal.get('channel', 'N/A')}")
                    print(f"      Уверенность: {signal.get('confidence', 'N/A')}")
            else:
                print("   Сигналов не найдено")
            
            return result.get('status') == 'success'
        finally:
            # Закрываем клиент
            if collector.client:
                await collector.client.disconnect()
        
    except Exception as e:
        print(f"❌ Ошибка сбора: {e}")
        return False

async def main():
    """Основная функция"""
    print("🚀 ТЕСТ РЕАЛЬНЫХ TELEGRAM КАНАЛОВ")
    print("=" * 50)
    print(f"Время: {datetime.now()}")
    print("=" * 50)
    
    # Тест подключения
    connection_ok = await test_telegram_connection()
    
    if connection_ok:
        # Тест сбора сигналов
        collection_ok = await test_signal_collection()
        
        print("\n" + "=" * 50)
        print("📊 РЕЗУЛЬТАТЫ:")
        
        if connection_ok and collection_ok:
            print("🎉 РЕАЛЬНЫЕ TELEGRAM КАНАЛЫ РАБОТАЮТ!")
            print("✅ Подключение: успешно")
            print("✅ Сбор сигналов: работает")
        elif connection_ok:
            print("⚠️ Подключение работает, но сбор сигналов не работает")
            print("✅ Подключение: успешно")
            print("❌ Сбор сигналов: не работает")
        else:
            print("❌ Проблемы с подключением")
            print("❌ Подключение: не работает")
            print("❌ Сбор сигналов: не работает")
    else:
        print("\n❌ Не удалось подключиться к Telegram")
    
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(main())
