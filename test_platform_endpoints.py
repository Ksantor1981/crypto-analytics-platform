#!/usr/bin/env python3
"""
Скрипт для комплексного тестирования Crypto Analytics Platform
Проверяет все основные endpoints и функциональность
"""

import requests
import json
import time
from datetime import datetime

def test_endpoint(url, description, method="GET", data=None, headers=None):
    """Универсальная функция для тестирования endpoints"""
    try:
        print(f"\n🔍 Тестируем: {description}")
        print(f"   URL: {url}")
        
        if method == "GET":
            response = requests.get(url, headers=headers)
        elif method == "POST":
            response = requests.post(url, json=data, headers=headers)
        
        print(f"   Статус: {response.status_code}")
        
        if response.status_code < 300:
            print(f"   ✅ Успешно")
            try:
                result = response.json()
                if isinstance(result, dict) and len(str(result)) < 200:
                    print(f"   Ответ: {result}")
                else:
                    print(f"   Размер ответа: {len(str(result))} символов")
                return True, result
            except:
                print(f"   Ответ: {response.text[:100]}...")
                return True, response.text
        else:
            print(f"   ❌ Ошибка: {response.text[:100]}")
            return False, response.text
            
    except Exception as e:
        print(f"   ❌ Исключение: {str(e)}")
        return False, str(e)

def main():
    print("=" * 70)
    print("🚀 ПОЛНОЕ ТЕСТИРОВАНИЕ CRYPTO ANALYTICS PLATFORM")
    print("=" * 70)
    
    # Backend endpoints
    backend_base = "http://127.0.0.1:8000"
    ml_base = "http://127.0.0.1:8001"
    
    results = {}
    
    # 1. Backend Health Check
    success, data = test_endpoint(f"{backend_base}/health", "Backend Health Check")
    results["backend_health"] = success
    
    # 2. Backend Channels
    success, data = test_endpoint(f"{backend_base}/api/v1/channels/", "Channels List")
    results["channels"] = success
    
    # 3. ML Service Health
    success, data = test_endpoint(f"{ml_base}/api/v1/health/", "ML Service Health")
    results["ml_health"] = success
    
    # 4. ML Prediction Test
    test_data = {
        "symbol": "BTCUSDT",
        "current_price": 45000.0,
        "volume_24h": 1000000.0,
        "price_change_24h": 2.5
    }
    success, data = test_endpoint(
        f"{ml_base}/api/v1/predictions/predict/", 
        "ML Prediction Test", 
        method="POST", 
        data=test_data
    )
    results["ml_prediction"] = success
    
    # 5. Backend Signals (может требовать аутентификации)
    success, data = test_endpoint(f"{backend_base}/api/v1/signals/", "Signals List")
    results["signals"] = success
    
    # Итоговый отчет
    print("\n" + "=" * 70)
    print("📊 ИТОГОВЫЙ ОТЧЕТ ТЕСТИРОВАНИЯ")
    print("=" * 70)
    
    total_tests = len(results)
    passed_tests = sum(1 for v in results.values() if v)
    
    for test_name, status in results.items():
        status_emoji = "✅" if status else "❌"
        print(f"{status_emoji} {test_name}: {'ПРОШЕЛ' if status else 'НЕ ПРОШЕЛ'}")
    
    print(f"\n📈 Статистика: {passed_tests}/{total_tests} тестов прошли успешно")
    success_rate = (passed_tests / total_tests) * 100
    print(f"📊 Процент успешности: {success_rate:.1f}%")
    
    # Анализ готовности платформы
    print("\n" + "=" * 70)
    print("🎯 АНАЛИЗ ГОТОВНОСТИ ПЛАТФОРМЫ ДЛЯ ПОЛЬЗОВАТЕЛЕЙ")
    print("=" * 70)
    
    if results.get("backend_health", False):
        print("✅ Backend API работает и доступен")
    else:
        print("❌ Backend API недоступен - КРИТИЧЕСКАЯ ПРОБЛЕМА")
    
    if results.get("ml_health", False):
        print("✅ ML Service работает и готов к прогнозированию")
    else:
        print("❌ ML Service недоступен")
    
    if results.get("channels", False):
        print("✅ Система каналов функционирует")
    else:
        print("❌ Система каналов недоступна")
    
    if results.get("ml_prediction", False):
        print("✅ ML предсказания работают")
    else:
        print("❌ ML предсказания не работают")
    
    # Общая оценка
    if success_rate >= 80:
        print("\n🟢 ПЛАТФОРМА ГОТОВА К ИСПОЛЬЗОВАНИЮ")
        print("   Основная функциональность работает стабильно")
    elif success_rate >= 60:
        print("\n🟡 ПЛАТФОРМА ЧАСТИЧНО ГОТОВА")
        print("   Есть проблемы, но основные функции доступны")
    else:
        print("\n🔴 ПЛАТФОРМА НЕ ГОТОВА К ИСПОЛЬЗОВАНИЮ")
        print("   Критические проблемы требуют исправления")
    
    print(f"\nВремя тестирования: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main() 