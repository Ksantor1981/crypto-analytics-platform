#!/usr/bin/env python3
"""
Расширенный тест ML-сервиса с реальными сценариями
"""

import requests
import json
import time
from datetime import datetime

# Конфигурация
ML_SERVICE_URL = "http://localhost:8001"

def test_performance():
    """Тест производительности"""
    print("🔍 Тестируем производительность...")
    
    # Тестовые данные для массового тестирования
    test_data = {
        "asset": "BTC",
        "direction": "LONG",
        "entry_price": 50000,
        "channel_accuracy": 0.8,
        "confidence": 0.7
    }
    
    start_time = time.time()
    successful_requests = 0
    total_requests = 10
    
    for i in range(total_requests):
        try:
            response = requests.post(
                f"{ML_SERVICE_URL}/api/v1/predictions/predict",
                json=test_data,
                headers={'Content-Type': 'application/json'},
                timeout=5
            )
            
            if response.status_code == 200:
                successful_requests += 1
            else:
                print(f"   ❌ Запрос {i+1} не прошел: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Ошибка в запросе {i+1}: {e}")
    
    end_time = time.time()
    total_time = end_time - start_time
    avg_time = total_time / total_requests
    
    print(f"   📊 Результаты производительности:")
    print(f"      Успешных запросов: {successful_requests}/{total_requests}")
    print(f"      Общее время: {total_time:.2f} сек")
    print(f"      Среднее время запроса: {avg_time:.3f} сек")
    print(f"      RPS (запросов в секунду): {total_requests/total_time:.1f}")
    
    return successful_requests == total_requests

def test_different_assets():
    """Тест с разными активами"""
    print("\n🔍 Тестируем разные активы...")
    
    assets = ["BTC", "ETH", "BNB", "ADA", "SOL", "DOT", "LINK", "UNI"]
    results = {}
    
    for asset in assets:
        test_data = {
            "asset": asset,
            "direction": "LONG",
            "entry_price": 1000,
            "channel_accuracy": 0.7,
            "confidence": 0.6
        }
        
        try:
            response = requests.post(
                f"{ML_SERVICE_URL}/api/v1/predictions/predict",
                json=test_data,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                data = response.json()
                recommendation = data.get('recommendation', 'N/A')
                confidence = data.get('confidence', 0)
                results[asset] = {
                    'recommendation': recommendation,
                    'confidence': confidence,
                    'status': 'success'
                }
                print(f"   ✅ {asset}: {recommendation} (уверенность: {confidence:.3f})")
            else:
                results[asset] = {'status': 'error', 'code': response.status_code}
                print(f"   ❌ {asset}: ошибка {response.status_code}")
                
        except Exception as e:
            results[asset] = {'status': 'exception', 'error': str(e)}
            print(f"   ❌ {asset}: исключение - {e}")
    
    success_count = sum(1 for r in results.values() if r['status'] == 'success')
    print(f"\n   📈 Результат: {success_count}/{len(assets)} активов обработано успешно")
    
    return success_count == len(assets)

def test_signal_scenarios():
    """Тест различных сценариев сигналов"""
    print("\n🔍 Тестируем различные сценарии сигналов...")
    
    scenarios = [
        {
            "name": "Сильный бычий сигнал",
            "data": {
                "asset": "BTC",
                "direction": "LONG",
                "entry_price": 50000,
                "target_price": 55000,
                "stop_loss": 48000,
                "channel_accuracy": 0.9,
                "confidence": 0.8
            }
        },
        {
            "name": "Слабый медвежий сигнал",
            "data": {
                "asset": "ETH",
                "direction": "SHORT",
                "entry_price": 3000,
                "target_price": 2800,
                "stop_loss": 3200,
                "channel_accuracy": 0.4,
                "confidence": 0.3
            }
        },
        {
            "name": "Нейтральный сигнал",
            "data": {
                "asset": "BNB",
                "direction": "LONG",
                "entry_price": 400,
                "channel_accuracy": 0.5,
                "confidence": 0.5
            }
        },
        {
            "name": "Высокий риск/прибыль",
            "data": {
                "asset": "SOL",
                "direction": "LONG",
                "entry_price": 100,
                "target_price": 150,
                "stop_loss": 95,
                "channel_accuracy": 0.6,
                "confidence": 0.7
            }
        }
    ]
    
    results = []
    
    for scenario in scenarios:
        print(f"\n   📊 Сценарий: {scenario['name']}")
        
        try:
            response = requests.post(
                f"{ML_SERVICE_URL}/api/v1/predictions/predict",
                json=scenario['data'],
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Результат:")
                print(f"      Рекомендация: {data.get('recommendation', 'N/A')}")
                print(f"      Уверенность: {data.get('confidence', 'N/A')}")
                print(f"      Оценка риска: {data.get('risk_score', 'N/A')}")
                
                results.append({
                    'scenario': scenario['name'],
                    'status': 'success',
                    'data': data
                })
            else:
                print(f"   ❌ Ошибка: {response.status_code}")
                results.append({
                    'scenario': scenario['name'],
                    'status': 'error',
                    'code': response.status_code
                })
                
        except Exception as e:
            print(f"   ❌ Исключение: {e}")
            results.append({
                'scenario': scenario['name'],
                'status': 'exception',
                'error': str(e)
            })
    
    success_count = sum(1 for r in results if r['status'] == 'success')
    print(f"\n   📈 Результат: {success_count}/{len(scenarios)} сценариев обработано успешно")
    
    return success_count == len(scenarios)

def test_concurrent_requests():
    """Тест конкурентных запросов"""
    print("\n🔍 Тестируем конкурентные запросы...")
    
    import threading
    
    results = []
    lock = threading.Lock()
    
    def make_request(thread_id):
        test_data = {
            "asset": "BTC",
            "direction": "LONG",
            "entry_price": 50000,
            "channel_accuracy": 0.7,
            "confidence": 0.6
        }
        
        try:
            response = requests.post(
                f"{ML_SERVICE_URL}/api/v1/predictions/predict",
                json=test_data,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            with lock:
                results.append({
                    'thread_id': thread_id,
                    'status_code': response.status_code,
                    'success': response.status_code == 200
                })
                
        except Exception as e:
            with lock:
                results.append({
                    'thread_id': thread_id,
                    'status_code': None,
                    'success': False,
                    'error': str(e)
                })
    
    # Запускаем 5 конкурентных запросов
    threads = []
    for i in range(5):
        thread = threading.Thread(target=make_request, args=(i,))
        threads.append(thread)
        thread.start()
    
    # Ждем завершения всех потоков
    for thread in threads:
        thread.join()
    
    # Анализируем результаты
    successful = sum(1 for r in results if r['success'])
    print(f"   📊 Результаты конкурентных запросов:")
    print(f"      Успешных запросов: {successful}/{len(results)}")
    
    for result in results:
        status = "✅" if result['success'] else "❌"
        print(f"      Поток {result['thread_id']}: {status} (код: {result['status_code']})")
    
    return successful == len(results)

def main():
    """Основная функция расширенного тестирования"""
    print("🚀 Расширенное тестирование ML-сервиса")
    print("=" * 60)
    
    # Проверяем доступность сервиса
    try:
        response = requests.get(f"{ML_SERVICE_URL}/api/v1/health", timeout=5)
        if response.status_code != 200:
            print("❌ ML-сервис недоступен")
            return
    except Exception as e:
        print(f"❌ Не удается подключиться к ML-сервису: {e}")
        return
    
    # Запускаем тесты
    tests = [
        ("Производительность", test_performance),
        ("Разные активы", test_different_assets),
        ("Сценарии сигналов", test_signal_scenarios),
        ("Конкурентные запросы", test_concurrent_requests)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Ошибка в тесте {test_name}: {e}")
            results.append((test_name, False))
    
    # Итоговый отчет
    print("\n" + "=" * 60)
    print("📊 ИТОГОВЫЙ ОТЧЕТ РАСШИРЕННОГО ТЕСТИРОВАНИЯ")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ ПРОШЕЛ" if result else "❌ НЕ ПРОШЕЛ"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n📈 Результат: {passed}/{total} тестов прошли успешно")
    
    if passed == total:
        print("🎉 Все расширенные тесты прошли успешно!")
        print("🚀 ML-сервис готов к продакшену!")
    elif passed >= total * 0.8:
        print("✅ Большинство тестов прошли успешно. Сервис работает стабильно.")
    else:
        print("⚠️  Много тестов не прошли. Требуется доработка.")
    
    print(f"\n⏰ Время тестирования: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main() 