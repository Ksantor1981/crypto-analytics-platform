#!/usr/bin/env python3
"""
Тест стабильности платформы
Проверяет все ключевые компоненты и их взаимодействие
"""

import requests
import time
import sys
import json
from datetime import datetime

def test_backend_api():
    """Тестирует Backend API"""
    print("🔍 Тестирование Backend API...")
    
    base_url = "http://127.0.0.1:8000"
    
    try:
        # Тест документации
        response = requests.get(f"{base_url}/docs", timeout=5)
        assert response.status_code == 200, f"Docs failed: {response.status_code}"
        print("✅ Backend Docs: OK")
        
        # Тест OpenAPI схемы
        response = requests.get(f"{base_url}/openapi.json", timeout=5)
        assert response.status_code == 200, f"OpenAPI failed: {response.status_code}"
        print("✅ Backend OpenAPI: OK")
        
        return True
        
    except Exception as e:
        print(f"❌ Backend API failed: {e}")
        return False

def test_ml_service():
    """Тестирует ML Service"""
    print("🔍 Тестирование ML Service...")
    
    base_url = "http://127.0.0.1:8001"
    
    try:
        # Тест документации
        response = requests.get(f"{base_url}/docs", timeout=5)
        assert response.status_code == 200, f"ML Docs failed: {response.status_code}"
        print("✅ ML Service Docs: OK")
        
        # Тест корневого endpoint
        response = requests.get(f"{base_url}/", timeout=5)
        assert response.status_code == 200, f"ML Root failed: {response.status_code}"
        data = response.json()
        assert data["service"] == "Crypto Analytics ML Service", "Wrong service name"
        print("✅ ML Service Root: OK")
        
        # Тест информации о сервисе
        response = requests.get(f"{base_url}/api/v1/info", timeout=5)
        assert response.status_code == 200, f"ML Info failed: {response.status_code}"
        data = response.json()
        assert "ml-service" in data["service_name"], "Wrong service info"
        print("✅ ML Service Info: OK")
        
        return True
        
    except Exception as e:
        print(f"❌ ML Service failed: {e}")
        return False

def test_ml_health():
    """Тестирует ML Health endpoints"""
    print("🔍 Тестирование ML Health...")
    
    base_url = "http://127.0.0.1:8001/api/v1/health"
    
    try:
        # Базовый health check
        response = requests.get(f"{base_url}/", timeout=5)
        assert response.status_code == 200, f"Health failed: {response.status_code}"
        data = response.json()
        assert data["status"] == "healthy", f"Service not healthy: {data}"
        print("✅ ML Health Basic: OK")
        
        # Детальный health check
        response = requests.get(f"{base_url}/detailed", timeout=10)
        assert response.status_code == 200, f"Detailed health failed: {response.status_code}"
        data = response.json()
        assert "system_metrics" in data, "Missing system metrics"
        assert "model_status" in data, "Missing model status"
        print("✅ ML Health Detailed: OK")
        
        # Readiness check
        response = requests.get(f"{base_url}/readiness", timeout=10)
        assert response.status_code == 200, f"Readiness failed: {response.status_code}"
        data = response.json()
        assert data["status"] == "ready", f"Service not ready: {data}"
        print("✅ ML Health Readiness: OK")
        
        # Liveness check
        response = requests.get(f"{base_url}/liveness", timeout=5)
        assert response.status_code == 200, f"Liveness failed: {response.status_code}"
        data = response.json()
        assert data["status"] == "alive", f"Service not alive: {data}"
        print("✅ ML Health Liveness: OK")
        
        return True
        
    except Exception as e:
        print(f"❌ ML Health failed: {e}")
        return False

def test_ml_predictions():
    """Тестирует ML Predictions"""
    print("🔍 Тестирование ML Predictions...")
    
    base_url = "http://127.0.0.1:8001/api/v1/predictions"
    
    try:
        # Тест базового предсказания
        test_data = {
            "asset": "BTCUSDT",
            "entry_price": 45000.0,
            "target_price": 46000.0,
            "stop_loss": 44000.0,
            "direction": "LONG"
        }
        
        response = requests.post(f"{base_url}/predict", json=test_data, timeout=15)
        assert response.status_code == 200, f"Prediction failed: {response.status_code} - {response.text}"
        data = response.json()
        
        # Проверяем обязательные поля
        required_fields = ["asset", "prediction", "confidence", "expected_return", "risk_level", "recommendation"]
        for field in required_fields:
            assert field in data, f"Missing field: {field}"
        
        assert data["asset"] == "BTCUSDT", "Wrong asset in response"
        assert data["prediction"] in ["SUCCESS", "FAIL"], f"Invalid prediction: {data['prediction']}"
        assert 0 <= data["confidence"] <= 1, f"Invalid confidence: {data['confidence']}"
        assert data["risk_level"] in ["LOW", "MEDIUM", "HIGH"], f"Invalid risk level: {data['risk_level']}"
        
        print("✅ ML Prediction Basic: OK")
        print(f"   Предсказание: {data['prediction']}")
        print(f"   Уверенность: {data['confidence']:.2f}")
        print(f"   Рекомендация: {data['recommendation']}")
        
        # Тест с различными активами
        test_assets = ["ETHUSDT", "BNBUSDT", "ADAUSDT"]
        for asset in test_assets:
            test_data["asset"] = asset
            response = requests.post(f"{base_url}/predict", json=test_data, timeout=10)
            assert response.status_code == 200, f"Prediction failed for {asset}: {response.status_code}"
            data = response.json()
            assert data["asset"] == asset, f"Wrong asset in response for {asset}"
        
        print("✅ ML Prediction Multiple Assets: OK")
        
        # Тест поддерживаемых активов
        response = requests.get(f"{base_url}/supported-assets", timeout=5)
        assert response.status_code == 200, f"Supported assets failed: {response.status_code}"
        data = response.json()
        assert "supported_assets" in data, "Missing supported assets"
        print("✅ ML Supported Assets: OK")
        
        return True
        
    except Exception as e:
        print(f"❌ ML Predictions failed: {e}")
        return False

def test_integration():
    """Тестирует интеграцию между сервисами"""
    print("🔍 Тестирование интеграции сервисов...")
    
    try:
        # Симуляция полного цикла работы
        start_time = time.time()
        
        # 1. Проверяем Backend
        backend_response = requests.get("http://127.0.0.1:8000/docs", timeout=5)
        assert backend_response.status_code == 200
        
        # 2. Проверяем ML Service
        ml_response = requests.get("http://127.0.0.1:8001/api/v1/health/", timeout=5)
        assert ml_response.status_code == 200
        
        # 3. Делаем предсказание
        prediction_data = {
            "asset": "BTCUSDT",
            "entry_price": 50000.0,
            "target_price": 52000.0,
            "stop_loss": 48000.0,
            "direction": "LONG"
        }
        
        prediction_response = requests.post(
            "http://127.0.0.1:8001/api/v1/predictions/predict", 
            json=prediction_data, 
            timeout=10
        )
        assert prediction_response.status_code == 200
        
        end_time = time.time()
        response_time = end_time - start_time
        
        print(f"✅ Integration Test: OK (время ответа: {response_time:.2f}s)")
        
        # Проверяем время ответа
        assert response_time < 20, f"Response time too slow: {response_time}s"
        print("✅ Performance Test: OK")
        
        return True
        
    except Exception as e:
        print(f"❌ Integration failed: {e}")
        return False

def test_stress():
    """Нагрузочное тестирование"""
    print("🔍 Нагрузочное тестирование...")
    
    try:
        success_count = 0
        total_requests = 10
        
        for i in range(total_requests):
            try:
                test_data = {
                    "asset": f"TEST{i}USDT",
                    "entry_price": 45000.0 + i * 100,
                    "target_price": 46000.0 + i * 100,
                    "stop_loss": 44000.0 + i * 100,
                    "direction": "LONG" if i % 2 == 0 else "SHORT"
                }
                
                response = requests.post(
                    "http://127.0.0.1:8001/api/v1/predictions/predict", 
                    json=test_data, 
                    timeout=5
                )
                
                if response.status_code == 200:
                    success_count += 1
                    
            except Exception as e:
                print(f"   Request {i+1} failed: {e}")
        
        success_rate = (success_count / total_requests) * 100
        print(f"✅ Stress Test: {success_count}/{total_requests} успешных запросов ({success_rate:.1f}%)")
        
        assert success_rate >= 80, f"Success rate too low: {success_rate}%"
        
        return True
        
    except Exception as e:
        print(f"❌ Stress test failed: {e}")
        return False

def main():
    """Основная функция тестирования"""
    print("🚀 Запуск тестирования стабильности платформы")
    print("=" * 60)
    
    tests = [
        ("Backend API", test_backend_api),
        ("ML Service", test_ml_service),
        ("ML Health", test_ml_health),
        ("ML Predictions", test_ml_predictions),
        ("Integration", test_integration),
        ("Stress Test", test_stress)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 40)
        
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            results[test_name] = False
    
    # Итоговый отчет
    print("\n" + "=" * 60)
    print("📊 ИТОГОВЫЙ ОТЧЕТ")
    print("=" * 60)
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:20} : {status}")
    
    print("-" * 60)
    print(f"Пройдено тестов: {passed}/{total} ({(passed/total)*100:.1f}%)")
    
    if passed == total:
        print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ! Платформа стабильна.")
        return True
    else:
        print("⚠️  ЕСТЬ ПРОБЛЕМЫ! Требуется исправление.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 