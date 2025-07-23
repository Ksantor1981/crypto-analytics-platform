#!/usr/bin/env python3
"""
Скрипт для запуска всех сервисов платформы
Backend + ML Service + Frontend
"""

import subprocess
import time
import requests
import sys
import os
from pathlib import Path

def start_backend():
    """Запускает Backend сервис"""
    print("🚀 Запуск Backend сервиса...")
    try:
        # Переходим в директорию backend
        backend_path = Path(__file__).parent / "backend"
        os.chdir(backend_path)
        
        # Запускаем backend
        process = subprocess.Popen([
            "python", "-m", "uvicorn", "app.main:app", 
            "--host", "0.0.0.0", "--port", "8000", "--reload"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Ждем запуска
        time.sleep(5)
        
        # Проверяем доступность
        try:
            response = requests.get("http://localhost:8000/health", timeout=5)
            if response.status_code == 200:
                print("✅ Backend запущен успешно!")
                return process
            else:
                print(f"❌ Backend не отвечает: {response.status_code}")
                return None
        except:
            print("❌ Backend не доступен")
            return None
            
    except Exception as e:
        print(f"❌ Ошибка запуска Backend: {e}")
        return None

def start_ml_service():
    """Запускает ML сервис"""
    print("🤖 Запуск ML сервиса...")
    try:
        # Переходим в директорию ml-service
        ml_path = Path(__file__).parent / "ml-service"
        os.chdir(ml_path)
        
        # Запускаем ML service
        process = subprocess.Popen([
            "python", "main.py"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Ждем запуска
        time.sleep(5)
        
        # Проверяем доступность
        try:
            response = requests.get("http://localhost:8001/api/v1/health/", timeout=5)
            if response.status_code == 200:
                print("✅ ML Service запущен успешно!")
                return process
            else:
                print(f"❌ ML Service не отвечает: {response.status_code}")
                return None
        except:
            print("❌ ML Service не доступен")
            return None
            
    except Exception as e:
        print(f"❌ Ошибка запуска ML Service: {e}")
        return None

def start_frontend():
    """Запускает Frontend"""
    print("🎨 Запуск Frontend...")
    try:
        # Переходим в директорию frontend
        frontend_path = Path(__file__).parent / "frontend"
        os.chdir(frontend_path)
        
        # Запускаем frontend
        process = subprocess.Popen([
            "npm", "run", "dev"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Ждем запуска
        time.sleep(10)
        
        # Проверяем доступность
        try:
            response = requests.get("http://localhost:3000", timeout=5)
            if response.status_code == 200:
                print("✅ Frontend запущен успешно!")
                return process
            else:
                print(f"❌ Frontend не отвечает: {response.status_code}")
                return None
        except:
            print("❌ Frontend не доступен")
            return None
            
    except Exception as e:
        print(f"❌ Ошибка запуска Frontend: {e}")
        return None

def test_all_services():
    """Тестирует все сервисы"""
    print("\n🔍 Тестирование всех сервисов...")
    
    services = [
        ("Backend", "http://localhost:8000/health"),
        ("ML Service", "http://localhost:8001/api/v1/health/"),
        ("Frontend", "http://localhost:3000")
    ]
    
    results = {}
    
    for name, url in services:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"✅ {name}: OK")
                results[name] = True
            else:
                print(f"❌ {name}: {response.status_code}")
                results[name] = False
        except Exception as e:
            print(f"❌ {name}: Недоступен - {e}")
            results[name] = False
    
    return results

def main():
    """Основная функция"""
    print("🚀 ЗАПУСК ВСЕХ СЕРВИСОВ ПЛАТФОРМЫ")
    print("=" * 50)
    
    # Возвращаемся в корневую директорию
    os.chdir(Path(__file__).parent)
    
    # Запускаем сервисы
    backend_process = start_backend()
    ml_process = start_ml_service()
    frontend_process = start_frontend()
    
    # Ждем дополнительное время для полного запуска
    print("\n⏳ Ожидание полного запуска сервисов...")
    time.sleep(10)
    
    # Тестируем все сервисы
    results = test_all_services()
    
    # Итоговый отчет
    print("\n" + "=" * 50)
    print("📊 ИТОГОВЫЙ ОТЧЕТ")
    print("=" * 50)
    
    working_services = sum(results.values())
    total_services = len(results)
    
    print(f"✅ Работающих сервисов: {working_services}/{total_services}")
    
    if working_services == total_services:
        print("🎉 ВСЕ СЕРВИСЫ РАБОТАЮТ!")
        print("\n🔗 Доступные URL:")
        print("   - Frontend: http://localhost:3000")
        print("   - Backend API: http://localhost:8000")
        print("   - ML Service: http://localhost:8001")
        print("\n📋 Для остановки сервисов нажмите Ctrl+C")
        
        # Держим скрипт запущенным
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Остановка сервисов...")
            if backend_process:
                backend_process.terminate()
            if ml_process:
                ml_process.terminate()
            if frontend_process:
                frontend_process.terminate()
            print("✅ Сервисы остановлены")
    
    else:
        print("⚠️ НЕ ВСЕ СЕРВИСЫ РАБОТАЮТ")
        print("\n🔧 Рекомендации:")
        if not results.get("Backend"):
            print("   - Проверьте зависимости backend")
        if not results.get("ML Service"):
            print("   - Проверьте зависимости ml-service")
        if not results.get("Frontend"):
            print("   - Проверьте npm install в frontend")

if __name__ == "__main__":
    main() 