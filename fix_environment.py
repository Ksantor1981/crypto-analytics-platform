#!/usr/bin/env python3
"""
Исправление проблем с виртуальным окружением
"""
import os
import sys
import subprocess
from pathlib import Path

def check_python():
    """Проверяет Python окружение"""
    print("🔍 Проверка Python окружения...")
    print(f"Python версия: {sys.version}")
    print(f"Python путь: {sys.executable}")
    print(f"Текущая директория: {os.getcwd()}")
    
    # Проверяем переменные окружения
    print(f"VIRTUAL_ENV: {os.environ.get('VIRTUAL_ENV', 'Не установлена')}")
    print(f"PYTHONPATH: {os.environ.get('PYTHONPATH', 'Не установлена')}")

def check_packages():
    """Проверяет установленные пакеты"""
    print("\n📦 Проверка пакетов...")
    
    packages_to_check = ['telethon', 'requests', 'sqlite3']
    
    for package in packages_to_check:
        try:
            if package == 'sqlite3':
                import sqlite3
                print(f"✅ {package} - встроенный модуль")
            else:
                module = __import__(package)
                version = getattr(module, '__version__', 'версия неизвестна')
                print(f"✅ {package} - {version}")
        except ImportError:
            print(f"❌ {package} - НЕ УСТАНОВЛЕН")

def install_packages():
    """Устанавливает необходимые пакеты"""
    print("\n📥 Установка пакетов...")
    
    packages = ['telethon', 'requests']
    
    for package in packages:
        try:
            print(f"Устанавливаем {package}...")
            result = subprocess.run([
                sys.executable, '-m', 'pip', 'install', '--user', package
            ], capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                print(f"✅ {package} установлен успешно")
            else:
                print(f"❌ Ошибка установки {package}: {result.stderr}")
                
        except Exception as e:
            print(f"❌ Ошибка при установке {package}: {e}")

def test_telegram_import():
    """Тестирует импорт Telegram"""
    print("\n📡 Тест Telegram импорта...")
    
    try:
        import telethon
        print(f"✅ Telethon импортирован: {telethon.__version__}")
        
        from telethon import TelegramClient
        print("✅ TelegramClient импортирован")
        
        return True
    except ImportError as e:
        print(f"❌ Ошибка импорта Telethon: {e}")
        return False

def test_telegram_connection():
    """Тестирует подключение к Telegram"""
    print("\n🔗 Тест подключения к Telegram...")
    
    # Загружаем данные из .env
    env_path = Path('.env')
    if env_path.exists():
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value
        
        api_id = os.environ.get('TELEGRAM_API_ID')
        api_hash = os.environ.get('TELEGRAM_API_HASH')
        
        if api_id and api_hash:
            print(f"✅ API данные найдены: {api_id}")
            return True
        else:
            print("❌ API данные не найдены в .env")
            return False
    else:
        print("❌ Файл .env не найден")
        return False

def main():
    """Основная функция"""
    print("🔧 ИСПРАВЛЕНИЕ ПРОБЛЕМ С ОКРУЖЕНИЕМ")
    print("=" * 50)
    
    # Проверяем окружение
    check_python()
    check_packages()
    
    # Устанавливаем пакеты если нужно
    install_packages()
    
    # Тестируем импорт
    if test_telegram_import():
        print("\n🎉 Telethon работает!")
        
        # Тестируем подключение
        if test_telegram_connection():
            print("🎉 Все готово для сбора РЕАЛЬНЫХ данных!")
            print("\nСледующие шаги:")
            print("1. Запустите: python get_real_data.py")
            print("2. Соберите РЕАЛЬНЫЕ данные из Telegram")
            print("3. Обновите дашборд")
        else:
            print("\n❌ Проблема с Telegram API данными")
    else:
        print("\n❌ Проблема с Telethon")

if __name__ == '__main__':
    main()
