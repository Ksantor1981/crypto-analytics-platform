#!/usr/bin/env python3
"""
Скрипт для просмотра всех каналов для парсинга в системе
"""

import sys
import os

# Добавляем путь к workers для импорта
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'workers'))

def show_real_data_channels():
    """Показывает каналы из real_data_config.py"""
    print("🔍 КАНАЛЫ ИЗ REAL_DATA_CONFIG.PY")
    print("=" * 50)
    
    try:
        from real_data_config import REAL_TELEGRAM_CHANNELS, get_active_channels
        
        print(f"📊 Всего каналов: {len(REAL_TELEGRAM_CHANNELS)}")
        print(f"✅ Активных каналов: {len(get_active_channels())}")
        print()
        
        for i, channel in enumerate(REAL_TELEGRAM_CHANNELS, 1):
            status = "🟢 АКТИВЕН" if channel.get('active', False) else "🔴 НЕАКТИВЕН"
            print(f"{i:2d}. {channel['name']}")
            print(f"    📱 Username: {channel['username']}")
            print(f"    🏷️  Категория: {channel['category']}")
            print(f"    📈 Приоритет: {channel.get('priority', 'N/A')}")
            print(f"    🎯 Успешность: {channel.get('success_rate', 0)*100:.1f}%")
            print(f"    📊 Сигналов/день: {channel.get('avg_signals_per_day', 'N/A')}")
            print(f"    {status}")
            print()
            
    except ImportError as e:
        print(f"❌ Ошибка импорта: {e}")
    except Exception as e:
        print(f"❌ Ошибка: {e}")

def show_collector_channels():
    """Показывает каналы из real_telegram_collector.py"""
    print("🔍 КАНАЛЫ ИЗ REAL_TELEGRAM_COLLECTOR.PY")
    print("=" * 50)
    
    try:
        from telegram.real_telegram_collector import RealTelegramCollector
        
        # Создаем экземпляр для получения списка каналов
        collector = RealTelegramCollector(use_real_config=False)
        
        print(f"📊 Всего каналов: {len(collector.channels)}")
        print()
        
        for i, channel in enumerate(collector.channels, 1):
            print(f"{i:2d}. {channel}")
        print()
        
    except ImportError as e:
        print(f"❌ Ошибка импорта: {e}")
    except Exception as e:
        print(f"❌ Ошибка: {e}")

def show_config_channels():
    """Показывает каналы из telegram/config.py"""
    print("🔍 КАНАЛЫ ИЗ TELEGRAM/CONFIG.PY")
    print("=" * 50)
    
    try:
        from telegram.config import TelegramConfig
        
        config = TelegramConfig()
        channels = config.get_active_channels()
        
        print(f"📊 Всего каналов: {len(config.channels)}")
        print(f"✅ Активных каналов: {len(channels)}")
        print()
        
        for i, channel in enumerate(config.channels, 1):
            status = "🟢 АКТИВЕН" if channel.active else "🔴 НЕАКТИВЕН"
            print(f"{i:2d}. {channel.name}")
            print(f"    📱 Username: {channel.username}")
            print(f"    🆔 Channel ID: {channel.channel_id}")
            print(f"    🏷️  Категория: {channel.category}")
            print(f"    {status}")
            print()
            
    except ImportError as e:
        print(f"❌ Ошибка импорта: {e}")
    except Exception as e:
        print(f"❌ Ошибка: {e}")

def show_database_channels():
    """Показывает каналы из базы данных"""
    print("🔍 КАНАЛЫ ИЗ БАЗЫ ДАННЫХ")
    print("=" * 50)
    
    try:
        import requests
        
        # Пробуем получить каналы через API
        base_url = "http://localhost:8002"  # Используем порт 8002
        
        # Тест общего API каналов
        try:
            response = requests.get(f"{base_url}/api/v1/channels")
            if response.status_code == 200:
                data = response.json()
                channels = data.get('data', [])
                print(f"📊 Всего каналов в БД: {len(channels)}")
                print()
                
                for i, channel in enumerate(channels[:10], 1):  # Показываем первые 10
                    status = "🟢 АКТИВЕН" if channel.get('is_active', False) else "🔴 НЕАКТИВЕН"
                    print(f"{i:2d}. {channel.get('name', 'N/A')}")
                    print(f"    📱 URL: {channel.get('url', 'N/A')}")
                    print(f"    🏷️  Платформа: {channel.get('platform', 'N/A')}")
                    print(f"    📊 Сигналов: {channel.get('signals_count', 0)}")
                    print(f"    🎯 Точность: {channel.get('accuracy', 0):.1f}%")
                    print(f"    {status}")
                    print()
            else:
                print(f"❌ Ошибка API: {response.status_code}")
        except requests.exceptions.ConnectionError:
            print("❌ Не удалось подключиться к API серверу")
        except Exception as e:
            print(f"❌ Ошибка API: {e}")
            
    except ImportError:
        print("❌ requests не установлен")

def main():
    """Главная функция"""
    print("📺 СПИСОК КАНАЛОВ ДЛЯ ПАРСИНГА")
    print("=" * 60)
    print()
    
    # Показываем каналы из разных источников
    show_real_data_channels()
    print()
    
    show_collector_channels()
    print()
    
    show_config_channels()
    print()
    
    show_database_channels()
    print()
    
    print("🎯 РЕКОМЕНДАЦИИ:")
    print("=" * 30)
    print("1. Основной список каналов находится в workers/real_data_config.py")
    print("2. Для добавления новых каналов отредактируйте REAL_TELEGRAM_CHANNELS")
    print("3. Каналы в БД можно просматривать через API: http://localhost:8002/docs")
    print("4. Для автоматического поиска используйте: POST /api/v1/channels/discover")
    print()
    
    print("📝 КАК ДОБАВИТЬ НОВЫЙ КАНАЛ:")
    print("=" * 30)
    print("1. Откройте файл: workers/real_data_config.py")
    print("2. Добавьте новый канал в список REAL_TELEGRAM_CHANNELS")
    print("3. Укажите username, name, category и другие параметры")
    print("4. Перезапустите систему")
    print()
    
    print("🔧 КАК ИЗМЕНИТЬ КАНАЛЫ:")
    print("=" * 30)
    print("1. Редактируйте workers/real_data_config.py")
    print("2. Измените параметры канала (active, priority, success_rate)")
    print("3. Добавьте новые каналы в список")
    print("4. Удалите неактуальные каналы")

if __name__ == "__main__":
    main() 