#!/usr/bin/env python3
"""
Подробный отчет о всех каналах для парсинга в системе
"""

import sys
import os

# Добавляем путь к workers для импорта
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'workers'))

def show_detailed_real_data_channels():
    """Показывает подробную информацию о каналах из real_data_config.py"""
    print("🔍 ПОДРОБНАЯ ИНФОРМАЦИЯ О КАНАЛАХ")
    print("=" * 60)
    
    try:
        from real_data_config import REAL_TELEGRAM_CHANNELS, get_active_channels, get_channels_by_category
        
        active_channels = get_active_channels()
        
        print(f"📊 СТАТИСТИКА:")
        print(f"   Всего каналов: {len(REAL_TELEGRAM_CHANNELS)}")
        print(f"   Активных каналов: {len(active_channels)}")
        print(f"   Неактивных каналов: {len(REAL_TELEGRAM_CHANNELS) - len(active_channels)}")
        print()
        
        # Группируем по категориям
        categories = {}
        for channel in REAL_TELEGRAM_CHANNELS:
            category = channel.get('category', 'unknown')
            if category not in categories:
                categories[category] = []
            categories[category].append(channel)
        
        print("📂 КАНАЛЫ ПО КАТЕГОРИЯМ:")
        print("-" * 40)
        for category, channels in categories.items():
            active_count = len([ch for ch in channels if ch.get('active', False)])
            print(f"   {category.upper()}: {len(channels)} каналов ({active_count} активных)")
        print()
        
        print("📋 ДЕТАЛЬНЫЙ СПИСОК КАНАЛОВ:")
        print("-" * 40)
        
        for i, channel in enumerate(REAL_TELEGRAM_CHANNELS, 1):
            status = "🟢 АКТИВЕН" if channel.get('active', False) else "🔴 НЕАКТИВЕН"
            priority = channel.get('priority', 'N/A')
            success_rate = channel.get('success_rate', 0) * 100
            avg_signals = channel.get('avg_signals_per_day', 'N/A')
            confidence_mult = channel.get('confidence_multiplier', 1.0)
            
            print(f"{i:2d}. {channel['name']}")
            print(f"    📱 Username: {channel['username']}")
            print(f"    🏷️  Категория: {channel['category']}")
            print(f"    📈 Приоритет: {priority}")
            print(f"    🎯 Успешность: {success_rate:.1f}%")
            print(f"    📊 Сигналов/день: {avg_signals}")
            print(f"    ⚡ Множитель уверенности: {confidence_mult}")
            print(f"    🌍 Языки: {', '.join(channel.get('languages', ['N/A']))}")
            print(f"    📝 Типы сигналов: {', '.join(channel.get('signal_types', ['N/A']))}")
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

def show_management_commands():
    """Показывает команды для управления каналами"""
    print("🔧 КОМАНДЫ ДЛЯ УПРАВЛЕНИЯ КАНАЛАМИ")
    print("=" * 50)
    
    print("📝 ДОБАВЛЕНИЕ НОВОГО КАНАЛА:")
    print("1. Откройте файл: workers/real_data_config.py")
    print("2. Найдите список REAL_TELEGRAM_CHANNELS")
    print("3. Добавьте новый канал в формате:")
    print("""
    {
        "username": "@your_channel_name",
        "name": "Your Channel Display Name",
        "category": "premium",  # или другой категории
        "confidence_multiplier": 1.0,
        "active": True,
        "priority": 1,
        "languages": ["en"],
        "signal_types": ["spot", "futures"],
        "avg_signals_per_day": 10,
        "success_rate": 0.7
    }
    """)
    
    print("📝 ИЗМЕНЕНИЕ КАНАЛА:")
    print("1. Найдите канал в REAL_TELEGRAM_CHANNELS")
    print("2. Измените нужные параметры:")
    print("   - active: True/False (активность)")
    print("   - priority: 1-5 (приоритет)")
    print("   - success_rate: 0.0-1.0 (успешность)")
    print("   - confidence_multiplier: 0.5-2.0 (множитель уверенности)")
    
    print("📝 УДАЛЕНИЕ КАНАЛА:")
    print("1. Найдите канал в списке")
    print("2. Установите active: False или удалите запись")
    
    print("📝 ПЕРЕЗАПУСК СИСТЕМЫ:")
    print("1. Остановите все сервисы")
    print("2. Запустите заново:")
    print("   - python start_ml_service.py")
    print("   - python start_telegram_integration.py")

def show_api_endpoints():
    """Показывает API эндпоинты для работы с каналами"""
    print("🌐 API ЭНДПОИНТЫ ДЛЯ КАНАЛОВ")
    print("=" * 40)
    
    print("📋 ОСНОВНЫЕ ЭНДПОИНТЫ:")
    print("1. GET /api/v1/channels - Список всех каналов")
    print("2. GET /api/v1/channels/{id} - Информация о канале")
    print("3. POST /api/v1/channels - Создать новый канал")
    print("4. PUT /api/v1/channels/{id} - Обновить канал")
    print("5. DELETE /api/v1/channels/{id} - Удалить канал")
    print()
    
    print("🔍 СПЕЦИАЛЬНЫЕ ЭНДПОИНТЫ:")
    print("1. POST /api/v1/channels/discover - Автоматический поиск каналов")
    print("2. GET /api/v1/telegram/channels - Telegram каналы")
    print("3. POST /api/v1/telegram/collect - Сбор сигналов")
    print()
    
    print("📊 ДОСТУП К API:")
    print("1. Swagger UI: http://localhost:8002/docs")
    print("2. ReDoc: http://localhost:8002/redoc")
    print("3. OpenAPI JSON: http://localhost:8002/openapi.json")

def main():
    """Главная функция"""
    print("📺 ПОДРОБНЫЙ ОТЧЕТ О КАНАЛАХ ДЛЯ ПАРСИНГА")
    print("=" * 70)
    print()
    
    # Показываем подробную информацию о каналах
    show_detailed_real_data_channels()
    print()
    
    show_collector_channels()
    print()
    
    show_config_channels()
    print()
    
    show_management_commands()
    print()
    
    show_api_endpoints()
    print()
    
    print("🎯 ВАЖНЫЕ ЗАМЕЧАНИЯ:")
    print("=" * 30)
    print("1. Основной список каналов: workers/real_data_config.py")
    print("2. Для реального парсинга нужны Telegram API ключи")
    print("3. Каналы в БД синхронизируются с конфигурацией")
    print("4. Автоматический поиск работает через /discover эндпоинт")
    print("5. Все изменения требуют перезапуска системы")

if __name__ == "__main__":
    main() 