#!/usr/bin/env python3
"""
Быстрый тест API без базы данных
Проверяет доступность сервисов и базовую функциональность
"""

import requests
import json
import time
from datetime import datetime

def test_backend_health():
    """Тестирует health endpoint backend"""
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ Backend health check: OK")
            return True
        else:
            print(f"❌ Backend health check: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Backend недоступен: {e}")
        return False

def test_ml_service_health():
    """Тестирует health endpoint ML сервиса"""
    try:
        response = requests.get("http://localhost:8001/api/v1/health/", timeout=5)
        if response.status_code == 200:
            print("✅ ML Service health check: OK")
            return True
        else:
            print(f"❌ ML Service health check: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ ML Service недоступен: {e}")
        return False

def test_ml_predictions():
    """Тестирует ML predictions API"""
    try:
        # Тест получения информации о модели
        response = requests.get("http://localhost:8001/api/v1/predictions/model/info", timeout=5)
        if response.status_code == 200:
            print("✅ ML Model info: OK")
            model_info = response.json()
            print(f"   📊 Модель: {model_info.get('model_name', 'Unknown')}")
            print(f"   📈 Версия: {model_info.get('model_version', 'Unknown')}")
        else:
            print(f"❌ ML Model info: {response.status_code}")
            
        # Тест price validation
        response = requests.get("http://localhost:8001/api/v1/price-validation/health", timeout=5)
        if response.status_code == 200:
            print("✅ Price Validation: OK")
        else:
            print(f"❌ Price Validation: {response.status_code}")
            
        return True
    except Exception as e:
        print(f"❌ ML API тест не прошел: {e}")
        return False

def test_backend_api_endpoints():
    """Тестирует основные API endpoints backend"""
    base_url = "http://localhost:8000/api/v1"
    
    endpoints = [
        "/channels/",
        "/signals/",
        "/users/register",
        "/users/login"
    ]
    
    print("\n🔍 Тестирование API endpoints:")
    
    for endpoint in endpoints:
        try:
            if endpoint in ["/users/register", "/users/login"]:
                # POST запросы
                response = requests.post(f"{base_url}{endpoint}", 
                                       json={"test": "data"}, 
                                       timeout=5)
            else:
                # GET запросы
                response = requests.get(f"{base_url}{endpoint}", timeout=5)
            
            if response.status_code in [200, 422, 403]:  # 422 - валидация, 403 - нет авторизации
                print(f"✅ {endpoint}: {response.status_code}")
            else:
                print(f"❌ {endpoint}: {response.status_code}")
                
        except Exception as e:
            print(f"❌ {endpoint}: Ошибка - {e}")

def generate_test_report():
    """Генерирует отчет о тестировании"""
    print("\n" + "="*60)
    print("📊 ОТЧЕТ О ТЕСТИРОВАНИИ ПЛАТФОРМЫ")
    print("="*60)
    print(f"🕐 Время тестирования: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Тестируем сервисы
    backend_ok = test_backend_health()
    ml_ok = test_ml_service_health()
    
    if ml_ok:
        test_ml_predictions()
    
    if backend_ok:
        test_backend_api_endpoints()
    
    # Итоговая оценка
    print("\n" + "="*60)
    print("📈 ИТОГОВАЯ ОЦЕНКА:")
    
    if backend_ok and ml_ok:
        print("🎉 ОТЛИЧНО! Оба сервиса работают")
        print("✅ Backend: Доступен")
        print("✅ ML Service: Доступен")
        print("✅ Готов к дальнейшей разработке")
    elif backend_ok:
        print("⚠️ ЧАСТИЧНО РАБОТАЕТ")
        print("✅ Backend: Доступен")
        print("❌ ML Service: Недоступен")
    elif ml_ok:
        print("⚠️ ЧАСТИЧНО РАБОТАЕТ")
        print("❌ Backend: Недоступен")
        print("✅ ML Service: Доступен")
    else:
        print("❌ КРИТИЧЕСКАЯ ПРОБЛЕМА")
        print("❌ Backend: Недоступен")
        print("❌ ML Service: Недоступен")
    
    print("\n🔧 РЕКОМЕНДАЦИИ:")
    if not backend_ok:
        print("   - Запустите backend: cd backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload")
    if not ml_ok:
        print("   - Запустите ML service: cd ml-service && python main.py")
    if backend_ok and ml_ok:
        print("   - Продолжайте разработку frontend")
        print("   - Настройте базу данных для полной функциональности")

if __name__ == "__main__":
    generate_test_report() 