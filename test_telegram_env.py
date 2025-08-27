#!/usr/bin/env python3
"""
Тест Telegram подключения с данными из .env файла
"""
import os
from pathlib import Path

def load_env_file():
    """Загружает данные из .env файла"""
    env_path = Path('.env')
    if not env_path.exists():
        print("❌ Файл .env не найден")
        return False
    
    print("📁 Загрузка данных из .env файла...")
    
    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value
                print(f"   ✅ {key} = {value[:10]}...")
    
    return True

def test_telegram_connection():
    """Тестирует подключение к Telegram"""
    api_id = os.getenv('TELEGRAM_API_ID')
    api_hash = os.getenv('TELEGRAM_API_HASH')
    phone = os.getenv('TELEGRAM_PHONE')
    
    print(f"\n🔍 Проверка данных:")
    print(f"   API_ID: {api_id}")
    print(f"   API_HASH: {api_hash[:10] if api_hash else 'None'}...")
    print(f"   PHONE: {phone}")
    
    if not all([api_id, api_hash, phone]):
        print("❌ Не все данные найдены в .env")
        return False
    
    print("\n📡 Тестирование подключения к Telegram...")
    
    try:
        # Пробуем импортировать telethon
        try:
            from telethon import TelegramClient
            from telethon.errors import SessionPasswordNeededError
            print("✅ Telethon импортирован успешно")
        except ImportError:
            print("❌ Telethon не установлен")
            print("Попробуйте: pip install telethon --user")
            return False
        
        # Создаем клиент
        client = TelegramClient('crypto_signals_session', api_id, api_hash)
        
        # Подключаемся
        print("🔗 Подключение к Telegram...")
        client.connect()
        
        if not client.is_user_authorized():
            print("📱 Требуется авторизация...")
            print("Код будет отправлен в Telegram")
            client.send_code_request(phone)
            code = input("Введите код из Telegram: ").strip()
            
            try:
                client.sign_in(phone, code)
                print("✅ Авторизация успешна!")
            except SessionPasswordNeededError:
                password = input("Введите пароль двухфакторной аутентификации: ").strip()
                client.sign_in(password=password)
                print("✅ Авторизация с 2FA успешна!")
        else:
            print("✅ Уже авторизован")
        
        # Тестируем доступ к каналам
        test_channels = [
            'CryptoPapa', 'FatPigSignals', 'WallstreetQueenOfficial',
            'RocketWalletSignals', 'BinanceKiller', 'WolfOfTrading'
        ]
        
        print("\n📊 Проверка доступа к каналам:")
        accessible_channels = []
        
        for channel in test_channels:
            try:
                entity = client.get_entity(channel)
                messages = client.get_messages(entity, limit=1)
                if messages:
                    print(f"   ✅ {channel} - доступен")
                    accessible_channels.append(channel)
                else:
                    print(f"   ⚠️ {channel} - нет сообщений")
            except Exception as e:
                print(f"   ❌ {channel} - ошибка: {str(e)[:50]}")
        
        client.disconnect()
        
        if accessible_channels:
            print(f"\n🎉 Подключение успешно! Доступно каналов: {len(accessible_channels)}")
            return True
        else:
            print("\n⚠️ Подключение работает, но каналы недоступны")
            return False
        
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return False

def main():
    """Основная функция"""
    print("🎯 Тест Telegram подключения с .env данными")
    print("=" * 50)
    
    if not load_env_file():
        return
    
    if test_telegram_connection():
        print("\n✅ Все готово для сбора РЕАЛЬНЫХ данных!")
        print("Запустите: python quick_collect.py")
    else:
        print("\n❌ Проблемы с подключением")

if __name__ == '__main__':
    main()
