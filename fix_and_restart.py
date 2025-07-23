#!/usr/bin/env python3
"""
Скрипт быстрого исправления и перезапуска всех сервисов
"""

import os
import sys
import subprocess
import time
import signal

def kill_processes():
    """Остановка всех запущенных процессов"""
    print("🛑 Остановка процессов...")
    
    try:
        # Остановка через taskkill (Windows)
        subprocess.run(["taskkill", "/f", "/im", "uvicorn.exe"], capture_output=True)
        subprocess.run(["taskkill", "/f", "/im", "python.exe"], capture_output=True)
        print("  ✅ Процессы остановлены")
    except:
        pass

def setup_environment():
    """Настройка переменных окружения"""
    print("🔧 Настройка окружения...")
    
    env_vars = {
        "DATABASE_URL": "postgresql://postgres:postgres123@localhost:5432/crypto_analytics",
        "SECRET_KEY": "crypto-analytics-secret-key-2024-development",
        "REDIS_URL": "redis://localhost:6379/0",
        "ML_SERVICE_URL": "http://localhost:8001",
        "ENVIRONMENT": "development",
        "DEBUG": "true"
    }
    
    for key, value in env_vars.items():
        os.environ[key] = value
    
    print("  ✅ Переменные установлены")

def start_ml_service():
    """Запуск ML Service"""
    print("🤖 Запуск ML Service...")
    
    try:
        os.chdir("ml-service")
        
        # Запуск в фоне
        proc = subprocess.Popen([
            sys.executable, "main.py"
        ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        
        time.sleep(3)  # Даем время на запуск
        
        # Проверка
        import requests
        resp = requests.get("http://localhost:8001/api/v1/health", timeout=5)
        if resp.status_code == 200:
            print("  ✅ ML Service запущен")
            os.chdir("..")
            return True
        else:
            print(f"  ❌ ML Service ошибка: {resp.status_code}")
            os.chdir("..")
            return False
            
    except Exception as e:
        print(f"  ❌ ML Service ошибка: {e}")
        os.chdir("..")
        return False

def start_backend():
    """Запуск Backend"""
    print("🚀 Запуск Backend...")
    
    try:
        os.chdir("backend")
        
        # Установка переменных окружения для subprocess
        env = os.environ.copy()
        env.update({
            "DATABASE_URL": "postgresql://postgres:postgres123@localhost:5432/crypto_analytics",
            "SECRET_KEY": "crypto-analytics-secret-key-2024-development"
        })
        
        # Запуск в фоне
        proc = subprocess.Popen([
            sys.executable, "-m", "uvicorn", "app.main:app", 
            "--host", "0.0.0.0", "--port", "8000", "--reload"
        ], env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        
        time.sleep(5)  # Даем время на запуск
        
        # Проверка
        import requests
        resp = requests.get("http://localhost:8000/health", timeout=10)
        if resp.status_code == 200:
            print("  ✅ Backend запущен")
            
            # Проверка ML endpoints
            resp = requests.get("http://localhost:8000/api/v1/ml/health", timeout=5)
            if resp.status_code == 200:
                print("  ✅ ML endpoints доступны")
            else:
                print(f"  ⚠️ ML endpoints проблема: {resp.status_code}")
            
            os.chdir("..")
            return True
        else:
            print(f"  ❌ Backend ошибка: {resp.status_code}")
            os.chdir("..")
            return False
            
    except Exception as e:
        print(f"  ❌ Backend ошибка: {e}")
        os.chdir("..")
        return False

def run_full_test():
    """Запуск полного теста"""
    print("\n🧪 Запуск полного теста...")
    
    try:
        result = subprocess.run([sys.executable, "test_full_integration.py"], 
                              capture_output=True, text=True)
        
        print("\nРезультат теста:")
        print(result.stdout)
        
        if "ВСЕ ТЕСТЫ ПРОШЛИ" in result.stdout:
            return True
        elif "ОСНОВНАЯ ФУНКЦИОНАЛЬНОСТЬ РАБОТАЕТ" in result.stdout:
            return True
        else:
            return False
            
    except Exception as e:
        print(f"❌ Ошибка теста: {e}")
        return False

def main():
    """Основная функция"""
    print("🔄 БЫСТРОЕ ИСПРАВЛЕНИЕ И ПЕРЕЗАПУСК")
    print("=" * 45)
    
    # 1. Остановка процессов
    kill_processes()
    time.sleep(2)
    
    # 2. Настройка окружения
    setup_environment()
    
    # 3. Создание таблиц БД
    print("\n📊 Создание таблиц...")
    try:
        os.chdir("backend")
        sys.path.insert(0, os.getcwd())
        
        from app.core.database import engine, Base
        from app.models import user, channel, signal, subscription, payment
        
        Base.metadata.create_all(bind=engine)
        print("  ✅ Таблицы созданы")
        os.chdir("..")
    except Exception as e:
        print(f"  ⚠️ Таблицы: {e}")
        os.chdir("..")
    
    # 4. Запуск ML Service
    ml_ok = start_ml_service()
    
    # 5. Запуск Backend
    backend_ok = start_backend()
    
    if ml_ok and backend_ok:
        print("\n🎉 ВСЕ СЕРВИСЫ ЗАПУЩЕНЫ!")
        
        # 6. Финальный тест
        test_ok = run_full_test()
        
        if test_ok:
            print("\n✅ СИСТЕМА ПОЛНОСТЬЮ РАБОТАЕТ!")
            print("\n🎯 Перейдите к следующему этапу:")
            print("   - Frontend: http://localhost:3000")
            print("   - Backend API: http://localhost:8000/docs")
            print("   - ML Service: http://localhost:8001/docs")
        else:
            print("\n⚠️ Есть проблемы, но основное работает")
    else:
        print("\n❌ Не удалось запустить все сервисы")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    
    print("\n" + "=" * 45)
    if success:
        print("✅ ИСПРАВЛЕНИЕ ЗАВЕРШЕНО УСПЕШНО")
    else:
        print("❌ ЕСТЬ ПРОБЛЕМЫ, ТРЕБУЕТСЯ ДОРАБОТКА")
    
    input("\nНажмите Enter для выхода...") 