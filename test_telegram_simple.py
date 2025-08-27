#!/usr/bin/env python3
"""
Простой тест Telegram подключения
"""
import os
from pathlib import Path

def load_env():
    """Загружает данные из .env файла"""
    env_path = Path('.env')
    if env_path.exists():
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value

def test_telegram():
    """Тестирует Telegram подключение"""
    print("🔍 Тест Telegram подключения")
    
    # Загружаем данные
    load_env()
    
    api_id = os.getenv('TELEGRAM_API_ID')
    api_hash = os.getenv('TELEGRAM_API_HASH')
    
    print(f"API_ID: {api_id}")
    print(f"API_HASH: {api_hash[:10] if api_hash else 'None'}...")
    
    if not all([api_id, api_hash]):
        print("❌ Не все данные найдены")
        return
    
    # Пробуем импортировать telethon
    try:
        import telethon
        print(f"✅ Telethon version: {telethon.__version__}")
        
        from telethon import TelegramClient
        print("✅ TelegramClient импортирован")
        
    except ImportError as e:
        print(f"❌ Ошибка импорта: {e}")
        return
    
    print("✅ Все готово для подключения к Telegram!")

if __name__ == '__main__':
    test_telegram()
