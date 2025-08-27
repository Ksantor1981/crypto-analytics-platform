#!/usr/bin/env python3
"""
Настройка Telegram API для сбора РЕАЛЬНЫХ данных
"""
import os
import sqlite3
from pathlib import Path

def setup_telegram_api():
    """Настройка Telegram API"""
    print("🔧 Настройка Telegram API для сбора РЕАЛЬНЫХ данных")
    print("=" * 60)
    
    print("\n📱 Для получения API данных:")
    print("1. Перейдите на https://my.telegram.org")
    print("2. Войдите в свой аккаунт")
    print("3. Перейдите в 'API development tools'")
    print("4. Создайте новое приложение")
    print("5. Скопируйте API_ID и API_HASH")
    
    print("\n⚙️ Введите ваши данные:")
    
    api_id = input("API_ID: ").strip()
    api_hash = input("API_HASH: ").strip()
    phone = input("Номер телефона (с кодом страны, например +7): ").strip()
    
    if not all([api_id, api_hash, phone]):
        print("❌ Все поля обязательны!")
        return False
    
    # Сохраняем в переменные окружения
    os.environ['TELEGRAM_API_ID'] = api_id
    os.environ['TELEGRAM_API_HASH'] = api_hash
    os.environ['TELEGRAM_PHONE'] = phone
    
    print(f"\n✅ Данные сохранены:")
    print(f"   API_ID: {api_id}")
    print(f"   API_HASH: {api_hash[:10]}...")
    print(f"   PHONE: {phone}")
    
    return True

def test_telegram_connection():
    """Тестирование подключения к Telegram"""
    print("\n🔍 Тестирование подключения к Telegram...")
    
    try:
        from telethon import TelegramClient
        from telethon.errors import SessionPasswordNeededError
        
        api_id = os.getenv('TELEGRAM_API_ID')
        api_hash = os.getenv('TELEGRAM_API_HASH')
        phone = os.getenv('TELEGRAM_PHONE')
        
        if not all([api_id, api_hash, phone]):
            print("❌ Данные API не настроены!")
            return False
        
        print("📡 Подключение к Telegram...")
        client = TelegramClient('crypto_signals_session', api_id, api_hash)
        
        # Подключаемся
        client.connect()
        
        if not client.is_user_authorized():
            print("📱 Отправка кода подтверждения...")
            client.send_code_request(phone)
            code = input("Введите код из Telegram: ").strip()
            
            try:
                client.sign_in(phone, code)
            except SessionPasswordNeededError:
                password = input("Введите пароль двухфакторной аутентификации: ").strip()
                client.sign_in(password=password)
        
        print("✅ Подключение успешно!")
        
        # Тестируем доступ к каналам
        test_channels = [
            'CryptoPapa', 'FatPigSignals', 'WallstreetQueenOfficial',
            'RocketWalletSignals', 'BinanceKiller', 'WolfOfTrading'
        ]
        
        print("\n📊 Проверка доступа к каналам:")
        for channel in test_channels:
            try:
                entity = client.get_entity(channel)
                messages = client.get_messages(entity, limit=1)
                if messages:
                    print(f"   ✅ {channel} - доступен")
                else:
                    print(f"   ⚠️ {channel} - нет сообщений")
            except Exception as e:
                print(f"   ❌ {channel} - ошибка: {str(e)[:50]}")
        
        client.disconnect()
        return True
        
    except ImportError:
        print("❌ Telethon не установлен!")
        print("Установите: pip install telethon")
        return False
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return False

def collect_real_data():
    """Сбор РЕАЛЬНЫХ данных"""
    print("\n🚀 Запуск сбора РЕАЛЬНЫХ данных...")
    
    try:
        from workers.real_data_collector import RealDataCollector
        import asyncio
        
        collector = RealDataCollector()
        
        # Собираем из Telegram
        print("📡 Сбор из Telegram каналов...")
        telegram_signals = asyncio.run(collector.collect_from_telegram())
        
        print(f"✅ Собрано {telegram_signals} РЕАЛЬНЫХ сигналов из Telegram")
        
        # Показываем статистику
        conn = sqlite3.connect('workers/signals.db')
        cur = conn.cursor()
        
        cur.execute("SELECT COUNT(*) FROM signals WHERE signal_type = 'telegram_real'")
        real_count = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM signals WHERE signal_type = 'real_demo'")
        demo_count = cur.fetchone()[0]
        
        print(f"\n📊 Статистика:")
        print(f"   • РЕАЛЬНЫХ сигналов: {real_count}")
        print(f"   • Демо сигналов: {demo_count}")
        print(f"   • Всего: {real_count + demo_count}")
        
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка сбора данных: {e}")
        return False

def main():
    """Основная функция"""
    print("🎯 Настройка сбора РЕАЛЬНЫХ данных из Telegram")
    print("=" * 60)
    
    # Проверяем есть ли уже данные
    if os.getenv('TELEGRAM_API_ID'):
        print("✅ Telegram API уже настроен")
        choice = input("Перенастроить? (y/n): ").lower()
        if choice != 'y':
            pass
        else:
            if not setup_telegram_api():
                return
    else:
        if not setup_telegram_api():
            return
    
    # Тестируем подключение
    if not test_telegram_connection():
        print("❌ Не удалось подключиться к Telegram")
        return
    
    # Собираем данные
    choice = input("\nСобрать РЕАЛЬНЫЕ данные сейчас? (y/n): ").lower()
    if choice == 'y':
        if collect_real_data():
            print("\n🎉 Сбор РЕАЛЬНЫХ данных завершен!")
            print("Теперь запустите дашборд: python start_dashboard.py")
        else:
            print("❌ Ошибка сбора данных")
    
    print("\n📝 Для постоянного использования добавьте в переменные окружения:")
    print("set TELEGRAM_API_ID=ваш_api_id")
    print("set TELEGRAM_API_HASH=ваш_api_hash") 
    print("set TELEGRAM_PHONE=ваш_номер")

if __name__ == '__main__':
    main()
