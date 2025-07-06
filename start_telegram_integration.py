#!/usr/bin/env python3
"""
Скрипт запуска полной Telegram интеграции
Переносит рабочий код из analyst_crypto в текущий проект
"""

import os
import sys
import asyncio
import subprocess
import logging
from pathlib import Path

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_dependencies():
    """Проверка наличия необходимых зависимостей"""
    logger.info("🔍 Проверка зависимостей...")
    
    required_packages = [
        'telethon',
        'aiohttp', 
        'asyncio',
        'python-dotenv'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            # Специальная обработка для python-dotenv
            if package == 'python-dotenv':
                __import__('dotenv')
            else:
                __import__(package.replace('-', '_'))
            logger.info(f"✅ {package} установлен")
        except ImportError:
            missing_packages.append(package)
            logger.error(f"❌ {package} не установлен")
    
    if missing_packages:
        logger.error(f"❌ Отсутствуют пакеты: {', '.join(missing_packages)}")
        logger.info("💡 Установите командой: pip install " + ' '.join(missing_packages))
        return False
    
    logger.info("✅ Все зависимости установлены")
    return True

def install_dependencies():
    """Установка недостающих зависимостей"""
    logger.info("📦 Установка зависимостей...")
    
    packages = [
        'telethon>=1.36.0',
        'aiohttp>=3.9.0',
        'python-dotenv>=1.0.0'
    ]
    
    try:
        for package in packages:
            logger.info(f"📦 Установка {package}...")
            result = subprocess.run([
                sys.executable, '-m', 'pip', 'install', package
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"✅ {package} установлен успешно")
            else:
                logger.error(f"❌ Ошибка установки {package}: {result.stderr}")
                return False
        
        logger.info("✅ Все зависимости установлены")
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка установки зависимостей: {e}")
        return False

def check_backend_status():
    """Проверка статуса backend"""
    logger.info("🔍 Проверка статуса backend...")
    
    try:
        import requests
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            logger.info("✅ Backend работает")
            return True
        else:
            logger.warning(f"⚠️ Backend отвечает с кодом: {response.status_code}")
            return False
    except Exception as e:
        logger.warning(f"⚠️ Backend недоступен: {e}")
        return False

async def run_telegram_integration(mode="test"):
    """Запуск Telegram интеграции"""
    logger.info(f"🚀 Запуск Telegram интеграции в режиме: {mode}")
    
    # Добавляем путь к workers
    workers_path = Path(__file__).parent / "workers"
    sys.path.insert(0, str(workers_path))
    
    try:
        # Импортируем модули интеграции
        from workers.telegram.full_telegram_integration import FullTelegramIntegration
        
        # Создаем интеграцию
        integration = FullTelegramIntegration()
        
        if mode == "test":
            # Тестовый режим
            logger.info("🧪 Запуск тестирования...")
            results = await integration.test_full_integration()
            
            logger.info("📊 Результаты тестирования:")
            for test_name, test_result in results["tests"].items():
                status = "✅" if test_result.get("success") else "❌"
                logger.info(f"   {status} {test_name}: {test_result.get('message', test_result)}")
            
            overall_status = "✅ УСПЕХ" if results["overall_success"] else "❌ ОШИБКИ"
            logger.info(f"🏁 Общий результат: {overall_status}")
            
            return results["overall_success"]
            
        elif mode == "batch":
            # Пакетный сбор
            logger.info("📦 Запуск пакетного сбора...")
            if await integration.initialize():
                results = await integration.collect_and_send_batch(limit=50)
                logger.info(f"📊 Результаты: {results}")
                await integration.cleanup()
                return True
            return False
            
        elif mode == "realtime":
            # Реальное время
            logger.info("🔄 Запуск в реальном времени...")
            if await integration.initialize():
                await integration.start_real_time_integration()
                return True
            return False
            
        elif mode == "periodic":
            # Периодический режим
            logger.info("⏰ Запуск периодического режима...")
            if await integration.initialize():
                await integration.run_periodic_collection(interval_minutes=15)
                return True
            return False
            
    except ImportError as e:
        logger.error(f"❌ Ошибка импорта: {e}")
        logger.info("💡 Убедитесь, что все файлы созданы правильно")
        return False
    except Exception as e:
        logger.error(f"❌ Ошибка выполнения: {e}")
        return False

def show_menu():
    """Показать меню выбора режима"""
    print("\n" + "="*50)
    print("🤖 TELEGRAM INTEGRATION LAUNCHER")
    print("="*50)
    print("Выберите режим работы:")
    print("1. 🧪 Тест интеграции")
    print("2. 📦 Пакетный сбор сигналов")
    print("3. 🔄 Мониторинг в реальном времени")
    print("4. ⏰ Периодический сбор")
    print("5. 📦 Установить зависимости")
    print("6. 🔍 Проверить статус")
    print("0. ❌ Выход")
    print("="*50)

async def main():
    """Главная функция"""
    logger.info("🚀 Запуск Telegram Integration Launcher")
    
    # Проверяем зависимости
    if not check_dependencies():
        logger.info("💡 Хотите установить недостающие зависимости? (y/n)")
        choice = input().lower()
        if choice == 'y':
            if not install_dependencies():
                logger.error("❌ Не удалось установить зависимости")
                return
        else:
            logger.error("❌ Невозможно продолжить без зависимостей")
            return
    
    # Проверяем backend
    backend_available = check_backend_status()
    if not backend_available:
        logger.warning("⚠️ Backend недоступен. Некоторые функции могут не работать.")
        logger.info("💡 Запустите backend командой: python start_backend.py")
    
    # Интерактивное меню
    while True:
        try:
            show_menu()
            choice = input("Ваш выбор: ").strip()
            
            if choice == "0":
                logger.info("👋 До свидания!")
                break
            elif choice == "1":
                await run_telegram_integration("test")
            elif choice == "2":
                await run_telegram_integration("batch")
            elif choice == "3":
                logger.info("🔄 Запуск в реальном времени (Ctrl+C для остановки)")
                await run_telegram_integration("realtime")
            elif choice == "4":
                logger.info("⏰ Запуск периодического режима (Ctrl+C для остановки)")
                await run_telegram_integration("periodic")
            elif choice == "5":
                install_dependencies()
            elif choice == "6":
                check_dependencies()
                check_backend_status()
            else:
                logger.warning("⚠️ Неверный выбор. Попробуйте снова.")
                
        except KeyboardInterrupt:
            logger.info("\n⏹️ Остановка по запросу пользователя")
            break
        except Exception as e:
            logger.error(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("⏹️ Программа завершена")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}") 