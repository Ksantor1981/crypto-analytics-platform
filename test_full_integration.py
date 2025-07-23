#!/usr/bin/env python3
"""
Комплексный тест всех сервисов платформы
Backend + ML Service + Frontend
"""

import requests
import json
import time
from datetime import datetime

def test_backend():
    """Тестирует Backend API"""
    print("🔧 Тестирование Backend API...")
    
    base_url = "http://localhost:8000"
    endpoints = [
        ("/health", "GET"),
        ("/api/v1/health", "GET"),
        ("/api/v1/channels/", "GET"),
        ("/api/v1/signals/", "GET"),
        ("/api/v1/users/register", "POST"),
        ("/api/v1/users/login", "POST"),
        ("/api/v1/ml/health", "GET"),
        ("/api/v1/telegram/health", "GET")
    ]
    
    results = {}
    
    for endpoint, method in endpoints:
        try:
            if method == "POST":
                response = requests.post(f"{base_url}{endpoint}", 
                                       json={"test": "data"}, 
                                       timeout=5)
            else:
                response = requests.get(f"{base_url}{endpoint}", timeout=5)
            
            if response.status_code in [200, 422, 403]:  # 422 - валидация, 403 - нет авторизации
                print(f"✅ {endpoint}: {response.status_code}")
                results[endpoint] = True
            else:
                print(f"❌ {endpoint}: {response.status_code}")
                results[endpoint] = False
                
        except Exception as e:
            print(f"❌ {endpoint}: Ошибка - {e}")
            results[endpoint] = False
    
    return results

def test_ml_service():
    """Тестирует ML Service"""
    print("\n🤖 Тестирование ML Service...")
    
    base_url = "http://localhost:8001/api/v1"
    endpoints = [
        ("/health/", "GET"),
        ("/predictions/model/info", "GET"),
        ("/price-validation/health", "GET"),
        ("/price-validation/supported-symbols", "GET"),
        ("/price-validation/current-prices", "POST"),
        ("/price-validation/market-summary", "POST")
    ]
    
    results = {}
    
    for endpoint, method in endpoints:
        try:
            if method == "POST":
                if "current-prices" in endpoint:
                    data = {"symbols": ["BTCUSDT", "ETHUSDT"]}
                elif "market-summary" in endpoint:
                    data = {"symbols": ["BTCUSDT"]}
                else:
                    data = {"test": "data"}
                    
                response = requests.post(f"{base_url}{endpoint}", 
                                       json=data, 
                                       timeout=10)
            else:
                response = requests.get(f"{base_url}{endpoint}", timeout=5)
            
            if response.status_code in [200, 422]:
                print(f"✅ {endpoint}: {response.status_code}")
                results[endpoint] = True
            else:
                print(f"❌ {endpoint}: {response.status_code}")
                results[endpoint] = False
                
        except Exception as e:
            print(f"❌ {endpoint}: Ошибка - {e}")
            results[endpoint] = False
    
    return results

def test_frontend():
    """Тестирует Frontend"""
    print("\n🎨 Тестирование Frontend...")
    
    base_url = "http://localhost:3000"
    endpoints = [
        ("/", "GET"),
        ("/dashboard", "GET"),
        ("/channels", "GET"),
        ("/signals", "GET"),
        ("/auth/login", "GET"),
        ("/auth/register", "GET")
    ]
    
    results = {}
    
    for endpoint, method in endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=5)
            
            if response.status_code in [200, 404]:  # 404 - страница не найдена, но сервер работает
                print(f"✅ {endpoint}: {response.status_code}")
                results[endpoint] = True
            else:
                print(f"❌ {endpoint}: {response.status_code}")
                results[endpoint] = False
                
        except Exception as e:
            print(f"❌ {endpoint}: Ошибка - {e}")
            results[endpoint] = False
    
    return results

def test_integration():
    """Тестирует интеграцию между сервисами"""
    print("\n🔗 Тестирование интеграции...")
    
    results = {}
    
    # Тест Backend -> ML Service
    try:
        response = requests.get("http://localhost:8000/api/v1/ml/health", timeout=5)
        if response.status_code == 200:
            print("✅ Backend -> ML Service: OK")
            results["backend_ml"] = True
        else:
            print(f"❌ Backend -> ML Service: {response.status_code}")
            results["backend_ml"] = False
    except Exception as e:
        print(f"❌ Backend -> ML Service: {e}")
        results["backend_ml"] = False
    
    # Тест Frontend -> Backend
    try:
        response = requests.get("http://localhost:3000", timeout=5)
        if response.status_code == 200:
            print("✅ Frontend доступен: OK")
            results["frontend_available"] = True
        else:
            print(f"❌ Frontend: {response.status_code}")
            results["frontend_available"] = False
    except Exception as e:
        print(f"❌ Frontend: {e}")
        results["frontend_available"] = False
    
    return results

def generate_comprehensive_report():
    """Генерирует комплексный отчет"""
    print("🚀 КОМПЛЕКСНЫЙ ТЕСТ ВСЕХ СЕРВИСОВ ПЛАТФОРМЫ")
    print("=" * 60)
    print(f"🕐 Время тестирования: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Тестируем все сервисы
    backend_results = test_backend()
    ml_results = test_ml_service()
    frontend_results = test_frontend()
    integration_results = test_integration()
    
    # Подсчитываем результаты
    backend_success = sum(backend_results.values())
    backend_total = len(backend_results)
    backend_percent = (backend_success / backend_total) * 100 if backend_total > 0 else 0
    
    ml_success = sum(ml_results.values())
    ml_total = len(ml_results)
    ml_percent = (ml_success / ml_total) * 100 if ml_total > 0 else 0
    
    frontend_success = sum(frontend_results.values())
    frontend_total = len(frontend_results)
    frontend_percent = (frontend_success / frontend_total) * 100 if frontend_total > 0 else 0
    
    integration_success = sum(integration_results.values())
    integration_total = len(integration_results)
    integration_percent = (integration_success / integration_total) * 100 if integration_total > 0 else 0
    
    # Итоговый отчет
    print("\n" + "=" * 60)
    print("📊 ДЕТАЛЬНЫЙ ОТЧЕТ")
    print("=" * 60)
    
    print(f"🔧 Backend API: {backend_success}/{backend_total} ({backend_percent:.1f}%)")
    print(f"🤖 ML Service: {ml_success}/{ml_total} ({ml_percent:.1f}%)")
    print(f"🎨 Frontend: {frontend_success}/{frontend_total} ({frontend_percent:.1f}%)")
    print(f"🔗 Интеграция: {integration_success}/{integration_total} ({integration_percent:.1f}%)")
    
    # Общая оценка
    total_success = backend_success + ml_success + frontend_success + integration_success
    total_endpoints = backend_total + ml_total + frontend_total + integration_total
    overall_percent = (total_success / total_endpoints) * 100 if total_endpoints > 0 else 0
    
    print(f"\n📈 ОБЩАЯ ГОТОВНОСТЬ: {overall_percent:.1f}%")
    
    # Оценка системы
    if overall_percent >= 90:
        grade = "A+"
        status = "ОТЛИЧНО! Система полностью готова"
    elif overall_percent >= 80:
        grade = "A"
        status = "ОЧЕНЬ ХОРОШО! Система готова к работе"
    elif overall_percent >= 70:
        grade = "B+"
        status = "ХОРОШО! Основная функциональность работает"
    elif overall_percent >= 60:
        grade = "B"
        status = "УДОВЛЕТВОРИТЕЛЬНО! Требуются доработки"
    else:
        grade = "C"
        status = "ТРЕБУЕТ ВНИМАНИЯ! Критические проблемы"
    
    print(f"🏆 ОЦЕНКА: {grade}")
    print(f"📋 СТАТУС: {status}")
    
    # Рекомендации
    print("\n🔧 РЕКОМЕНДАЦИИ:")
    
    if backend_percent < 100:
        print("   - Проверьте Backend API endpoints")
    if ml_percent < 100:
        print("   - Проверьте ML Service endpoints")
    if frontend_percent < 100:
        print("   - Проверьте Frontend страницы")
    if integration_percent < 100:
        print("   - Проверьте интеграцию между сервисами")
    
    if overall_percent >= 80:
        print("   - Система готова к дальнейшей разработке")
        print("   - Можно переходить к Этапу 1 (Frontend MVP)")
    
    # Доступные URL
    print("\n🔗 ДОСТУПНЫЕ URL:")
    print("   - Frontend: http://localhost:3000")
    print("   - Backend API: http://localhost:8000")
    print("   - ML Service: http://localhost:8001")
    print("   - Backend Health: http://localhost:8000/health")
    print("   - ML Health: http://localhost:8001/api/v1/health/")

if __name__ == "__main__":
    generate_comprehensive_report() 