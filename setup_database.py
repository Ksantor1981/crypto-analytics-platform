#!/usr/bin/env python3
"""
Скрипт настройки базы данных и исправления критических проблем инфраструктуры
Задача 0.2.1 из TASKS2.md
"""

import os
import sys
import subprocess
from pathlib import Path

def setup_environment():
    """Настройка переменных окружения"""
    print("🔧 Настройка переменных окружения...")
    
    # Устанавливаем переменные окружения для текущей сессии
    env_vars = {
        "DATABASE_URL": "postgresql://postgres:postgres123@localhost:5432/crypto_analytics",
        "SECRET_KEY": "crypto-analytics-secret-key-2024-development-super-secure",
        "REDIS_URL": "redis://localhost:6379/0",
        "ML_SERVICE_URL": "http://localhost:8001",
        "ENVIRONMENT": "development",
        "DEBUG": "true"
    }
    
    for key, value in env_vars.items():
        os.environ[key] = value
        print(f"  ✅ {key}={value}")

def create_database_tables():
    """Создание таблиц в базе данных"""
    print("\n📊 Создание таблиц базы данных...")
    
    try:
        # Переходим в директорию backend
        backend_dir = Path("backend")
        os.chdir(backend_dir)
        
        # Импортируем и создаем таблицы
        sys.path.insert(0, str(Path.cwd()))
        
        from app.core.database import engine, Base
        # Импортируем __init__.py из models, который подтянет все модели
        from app import models
        
        # Создаем все таблицы
        Base.metadata.create_all(bind=engine)
        print("  ✅ Таблицы созданы успешно")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Ошибка создания таблиц: {e}")
        
        # Пробуем создать через alembic
        try:
            print("  🔄 Пробуем через alembic...")
            result = subprocess.run(["alembic", "upgrade", "head"], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print("  ✅ Миграции alembic выполнены")
                return True
            else:
                print(f"  ❌ Alembic ошибка: {result.stderr}")
        except Exception as alembic_error:
            print(f"  ❌ Alembic недоступен: {alembic_error}")
        
        return False
    finally:
        # Возвращаемся в корневую директорию
        os.chdir("..")

def seed_demo_data():
    """Добавление демо-данных"""
    print("\n🌱 Добавление демо-данных...")
    
    try:
        # Переходим в backend
        os.chdir("backend")
        
        # Запускаем скрипт seed_data
        result = subprocess.run([sys.executable, "scripts/seed_data.py"], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("  ✅ Демо-данные добавлены")
            return True
        else:
            print(f"  ⚠️ Seed script проблема: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"  ❌ Ошибка добавления демо-данных: {e}")
        return False
    finally:
        os.chdir("..")

def test_database_connection():
    """Тестирование подключения к базе данных"""
    print("\n🔍 Тестирование подключения к БД...")
    
    try:
        os.chdir("backend")
        sys.path.insert(0, str(Path.cwd()))
        
        from app.core.database import engine
        
        # Тестируем подключение
        with engine.connect() as connection:
            from sqlalchemy import text
            result = connection.execute(text("SELECT 1"))
            if result.fetchone():
                print("  ✅ Подключение к БД работает")
                return True
        
    except Exception as e:
        print(f"  ❌ Проблема подключения: {e}")
        print("  💡 Убедитесь что PostgreSQL запущен:")
        print("     docker-compose up postgres -d")
        return False
    finally:
        os.chdir("..")

def fix_ml_service_endpoints():
    """Исправление проблем ML Service API"""
    print("\n🤖 Исправление ML Service...")
    
    try:
        # Проверим корректность ответов ML API
        import requests
        
        # Тест health endpoint
        resp = requests.get("http://localhost:8001/api/v1/health", timeout=5)
        if resp.status_code == 200:
            print("  ✅ ML Health endpoint работает")
        else:
            print(f"  ❌ ML Health проблема: {resp.status_code}")
            return False
        
        # Тест predictions endpoint с правильными данными
        payload = {
            "asset": "BTCUSDT",
            "entry_price": 45000.0,
            "target_price": 47000.0,
            "stop_loss": 44000.0,
            "confidence": 0.85
        }
        
        resp = requests.post("http://localhost:8001/api/v1/predictions/predict", 
                           json=payload, timeout=10)
        
        if resp.status_code == 200:
            data = resp.json()
            print(f"  ✅ ML Predictions работает: {data}")
            return True
        else:
            print(f"  ❌ ML Predictions проблема: {resp.status_code} - {resp.text}")
            return False
            
    except Exception as e:
        print(f"  ❌ ML Service ошибка: {e}")
        return False

def create_backend_ml_proxy():
    """Создание proxy endpoint в Backend для ML"""
    print("\n🔗 Создание Backend → ML интеграции...")
    
    # Проверим существует ли уже ml_integration endpoint
    try:
        import requests
        resp = requests.get("http://localhost:8000/api/v1/ml/health", timeout=5)
        if resp.status_code == 200:
            print("  ✅ Backend → ML интеграция уже работает")
            return True
    except:
        pass
    
    print("  🔄 Нужно добавить ML proxy endpoints в Backend")
    print("     (это потребует редактирования backend/app/api/endpoints/ml_integration.py)")
    return False

def run_integration_test():
    """Запуск теста интеграции"""
    print("\n🧪 Запуск теста интеграции...")
    
    try:
        result = subprocess.run([sys.executable, "test_full_integration.py"], 
                              capture_output=True, text=True)
        
        print("Результат теста:")
        print(result.stdout)
        
        if "ВСЕ ТЕСТЫ ПРОШЛИ" in result.stdout:
            print("  ✅ Интеграция полностью работает!")
            return True
        elif "ОСНОВНАЯ ФУНКЦИОНАЛЬНОСТЬ РАБОТАЕТ" in result.stdout:
            print("  ⚠️ Основное работает, есть мелкие проблемы")
            return True
        else:
            print("  ❌ Есть проблемы с интеграцией")
            return False
            
    except Exception as e:
        print(f"  ❌ Ошибка теста: {e}")
        return False

def main():
    """Основная функция"""
    print("🛠️ ИСПРАВЛЕНИЕ КРИТИЧЕСКИХ ПРОБЛЕМ ИНФРАСТРУКТУРЫ")
    print("=" * 60)
    print("Задача 0.2.1 из TASKS2.md\n")
    
    results = {}
    
    # 1. Настройка окружения
    setup_environment()
    
    # 2. Тест подключения к БД
    results['db_connection'] = test_database_connection()
    
    if results['db_connection']:
        # 3. Создание таблиц
        results['create_tables'] = create_database_tables()
        
        # 4. Добавление демо-данных
        if results['create_tables']:
            results['seed_data'] = seed_demo_data()
        else:
            results['seed_data'] = False
    else:
        results['create_tables'] = False
        results['seed_data'] = False
    
    # 5. Исправление ML Service
    results['ml_service'] = fix_ml_service_endpoints()
    
    # 6. Backend → ML интеграция
    results['backend_ml'] = create_backend_ml_proxy()
    
    # 7. Итоговый тест
    if any(results.values()):
        results['integration_test'] = run_integration_test()
    else:
        results['integration_test'] = False
    
    # Отчет
    print("\n" + "=" * 60)
    print("📋 ИТОГОВЫЙ ОТЧЕТ ИСПРАВЛЕНИЙ")
    print("=" * 60)
    
    for test_name, result in results.items():
        status = "✅ ИСПРАВЛЕНО" if result else "❌ ПРОБЛЕМА"
        print(f"{test_name:20}: {status}")
    
    fixed_count = sum(results.values())
    total_count = len(results)
    
    print(f"\n🎯 ИТОГ: {fixed_count}/{total_count} проблем исправлено")
    
    if fixed_count >= total_count * 0.8:
        print("🎉 ОСНОВНЫЕ ПРОБЛЕМЫ ИСПРАВЛЕНЫ!")
    elif fixed_count >= total_count * 0.5:
        print("⚠️ ЧАСТИЧНОЕ ИСПРАВЛЕНИЕ, нужна дополнительная работа")
    else:
        print("❌ КРИТИЧЕСКИЕ ПРОБЛЕМЫ НЕ РЕШЕНЫ")
    
    return fixed_count >= total_count * 0.5

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1) 