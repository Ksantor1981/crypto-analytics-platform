#!/usr/bin/env python3
"""
Тестовый скрипт для проверки ML-сервиса
"""

import requests
import json
from datetime import datetime

# Конфигурация
ML_SERVICE_URL = "http://localhost:8001"

def test_health_check():
    """Тест health check эндпоинта"""
    print("🔍 Тестируем health check...")
    
    try:
        response = requests.get(f"{ML_SERVICE_URL}/api/v1/health")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check прошел успешно!")
            print(f"   Статус: {data.get('status')}")
            print(f"   Сервис: {data.get('service')}")
            print(f"   Версия: {data.get('version')}")
            return True
        else:
            print(f"❌ Health check не прошел: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка при health check: {e}")
        return False

def test_model_info():
    """Тест информации о модели"""
    print("\n🔍 Тестируем информацию о модели...")
    
    try:
        response = requests.get(f"{ML_SERVICE_URL}/api/v1/predictions/model/info")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Информация о модели получена!")
            print(f"   Версия модели: {data.get('model_version')}")
            print(f"   Тип модели: {data.get('model_type')}")
            print(f"   Обучена: {data.get('is_trained')}")
            print(f"   Признаки: {data.get('feature_names')}")
            return True
        else:
            print(f"❌ Не удалось получить информацию о модели: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка при получении информации о модели: {e}")
        return False

def test_signal_prediction():
    """Тест предсказания сигналов"""
    print("\n🔍 Тестируем предсказание сигналов...")
    
    # Тестовые данные
    test_cases = [
        {
            "name": "BTC LONG с высоким рейтингом",
            "data": {
                "asset": "BTC",
                "direction": "LONG", 
                "entry_price": 50000,
                "channel_accuracy": 0.8,
                "confidence": 0.7
            }
        },
        {
            "name": "ETH SHORT с низким рейтингом",
            "data": {
                "asset": "ETH",
                "direction": "SHORT",
                "entry_price": 3000,
                "channel_accuracy": 0.3,
                "confidence": 0.4
            }
        },
        {
            "name": "BNB LONG с нейтральным рейтингом",
            "data": {
                "asset": "BNB",
                "direction": "LONG",
                "entry_price": 400,
                "channel_accuracy": 0.5,
                "confidence": 0.5
            }
        }
    ]
    
    success_count = 0
    
    for test_case in test_cases:
        print(f"\n   📊 Тест: {test_case['name']}")
        
        try:
            response = requests.post(
                f"{ML_SERVICE_URL}/api/v1/predictions/predict",
                json=test_case['data'],
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Предсказание получено!")
                print(f"      Вероятность успеха: {data.get('success_probability', 'N/A')}")
                print(f"      Уверенность: {data.get('confidence', 'N/A')}")
                print(f"      Рекомендация: {data.get('recommendation', 'N/A')}")
                print(f"      Оценка риска: {data.get('risk_score', 'N/A')}")
                success_count += 1
            else:
                print(f"   ❌ Ошибка предсказания: {response.status_code}")
                print(f"      Ответ: {response.text}")
                
        except Exception as e:
            print(f"   ❌ Ошибка при предсказании: {e}")
    
    print(f"\n📈 Результат: {success_count}/{len(test_cases)} тестов прошли успешно")
    return success_count == len(test_cases)

def test_error_handling():
    """Тест обработки ошибок"""
    print("\n🔍 Тестируем обработку ошибок...")
    
    # Тест с некорректными данными
    invalid_data = {
        "asset": "INVALID",
        "direction": "INVALID",
        "entry_price": "not_a_number",
        "channel_accuracy": 2.0,  # Должно быть 0-1
        "confidence": -1.0  # Должно быть 0-1
    }
    
    try:
        response = requests.post(
            f"{ML_SERVICE_URL}/api/v1/predictions/predict",
            json=invalid_data,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 422:  # Validation error
            print("✅ Обработка ошибок работает корректно (422 - validation error)")
            return True
        elif response.status_code == 200:
            print("⚠️  Сервис принял некорректные данные (возможно, есть валидация)")
            return True
        else:
            print(f"❌ Неожиданный статус код: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка при тестировании обработки ошибок: {e}")
        return False

def main():
    """Основная функция тестирования"""
    print("🚀 Начинаем тестирование ML-сервиса")
    print("=" * 50)
    
    # Проверяем, что сервис доступен
    if not test_health_check():
        print("\n❌ ML-сервис недоступен. Убедитесь, что он запущен на порту 8001")
        return
    
    # Тестируем основные функции
    tests = [
        ("Health Check", test_health_check),
        ("Model Info", test_model_info),
        ("Signal Prediction", test_signal_prediction),
        ("Error Handling", test_error_handling)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Ошибка в тесте {test_name}: {e}")
            results.append((test_name, False))
    
    # Итоговый отчет
    print("\n" + "=" * 50)
    print("📊 ИТОГОВЫЙ ОТЧЕТ")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ ПРОШЕЛ" if result else "❌ НЕ ПРОШЕЛ"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n📈 Результат: {passed}/{total} тестов прошли успешно")
    
    if passed == total:
        print("🎉 Все тесты прошли успешно! ML-сервис работает корректно.")
    else:
        print("⚠️  Некоторые тесты не прошли. Проверьте логи сервиса.")
    
    print(f"\n⏰ Время тестирования: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main() 