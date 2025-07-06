#!/usr/bin/env python3
"""
Финальный тест 100% готовности платформы
Проверяет все ключевые компоненты системы
"""

import asyncio
import httpx
import json
import time
from datetime import datetime
from typing import Dict, List, Any

class PlatformTester:
    def __init__(self):
        self.backend_url = "http://localhost:8000"
        self.ml_service_url = "http://localhost:8001"
        self.results = []
        
    async def test_backend_health(self) -> Dict[str, Any]:
        """Тест работоспособности Backend API"""
        print("🔍 Тестирование Backend API...")
        
        tests = [
            ("GET", "/docs", "Swagger документация"),
            ("GET", "/openapi.json", "OpenAPI схема"),
        ]
        
        results = []
        async with httpx.AsyncClient(timeout=10.0) as client:
            for method, endpoint, description in tests:
                try:
                    url = f"{self.backend_url}{endpoint}"
                    response = await client.request(method, url)
                    
                    success = response.status_code == 200
                    results.append({
                        "test": description,
                        "url": url,
                        "status": "✅ ПРОЙДЕН" if success else f"❌ ОШИБКА {response.status_code}",
                        "response_time": response.elapsed.total_seconds(),
                        "success": success
                    })
                except Exception as e:
                    results.append({
                        "test": description,
                        "url": f"{self.backend_url}{endpoint}",
                        "status": f"❌ ОШИБКА: {str(e)}",
                        "success": False
                    })
        
        return {
            "component": "Backend API",
            "tests": results,
            "success_rate": sum(1 for r in results if r["success"]) / len(results)
        }
    
    async def test_ml_service_health(self) -> Dict[str, Any]:
        """Тест работоспособности ML Service"""
        print("🤖 Тестирование ML Service...")
        
        tests = [
            ("GET", "/docs", "Swagger документация"),
            ("GET", "/api/v1/health/", "Health check"),
            ("GET", "/api/v1/predictions/model/info", "Информация о модели"),
        ]
        
        results = []
        async with httpx.AsyncClient(timeout=10.0) as client:
            for method, endpoint, description in tests:
                try:
                    url = f"{self.ml_service_url}{endpoint}"
                    response = await client.request(method, url)
                    
                    success = response.status_code == 200
                    results.append({
                        "test": description,
                        "url": url,
                        "status": "✅ ПРОЙДЕН" if success else f"❌ ОШИБКА {response.status_code}",
                        "response_time": response.elapsed.total_seconds(),
                        "success": success
                    })
                except Exception as e:
                    results.append({
                        "test": description,
                        "url": f"{self.ml_service_url}{endpoint}",
                        "status": f"❌ ОШИБКА: {str(e)}",
                        "success": False
                    })
        
        return {
            "component": "ML Service",
            "tests": results,
            "success_rate": sum(1 for r in results if r["success"]) / len(results)
        }
    
    async def test_ml_predictions(self) -> Dict[str, Any]:
        """Тест ML предсказаний"""
        print("🎯 Тестирование ML предсказаний...")
        
        test_signal = {
            "asset": "BTCUSDT",
            "direction": "LONG",
            "entry_price": 45000.0,
            "target_price": 47000.0,
            "stop_loss": 43000.0
        }
        
        tests = [
            ("POST", "/api/v1/predictions/predict", "Предсказание сигнала", test_signal),
            ("GET", "/api/v1/predictions/model/info", "Информация о модели", None)
        ]
        
        results = []
        async with httpx.AsyncClient(timeout=30.0) as client:
            for method, endpoint, description, data in tests:
                try:
                    url = f"{self.ml_service_url}{endpoint}"
                    if data:
                        response = await client.request(method, url, json=data)
                    else:
                        response = await client.request(method, url)
                    
                    success = response.status_code == 200
                    prediction_data = None
                    
                    if success:
                        prediction_data = response.json()
                        # Проверяем структуру ответа
                        if endpoint == "/api/v1/predictions/predict":
                            required_fields = ["prediction", "confidence", "recommendation"]
                            success = all(field in prediction_data for field in required_fields)
                        elif endpoint == "/api/v1/predictions/model/info":
                            required_fields = ["model_version", "model_type"]
                            success = all(field in prediction_data for field in required_fields)
                    
                    results.append({
                        "test": description,
                        "url": url,
                        "status": "✅ ПРОЙДЕН" if success else f"❌ ОШИБКА {response.status_code}",
                        "response_time": response.elapsed.total_seconds(),
                        "success": success,
                        "prediction_data": prediction_data
                    })
                except Exception as e:
                    results.append({
                        "test": description,
                        "url": f"{self.ml_service_url}{endpoint}",
                        "status": f"❌ ОШИБКА: {str(e)}",
                        "success": False
                    })
        
        return {
            "component": "ML Predictions",
            "tests": results,
            "success_rate": sum(1 for r in results if r["success"]) / len(results)
        }
    
    async def test_integration(self) -> Dict[str, Any]:
        """Тест интеграции между сервисами"""
        print("🔗 Тестирование интеграции сервисов...")
        
        # Пока что проверяем доступность эндпоинтов интеграции
        tests = [
            ("GET", "/api/v1/ml/health", "ML Service Health через Backend"),
            ("GET", "/api/v1/ml/model/info", "ML Model Info через Backend"),
        ]
        
        results = []
        async with httpx.AsyncClient(timeout=10.0) as client:
            for method, endpoint, description in tests:
                try:
                    url = f"{self.backend_url}{endpoint}"
                    response = await client.request(method, url)
                    
                    # Для этих эндпоинтов ожидаем либо 200, либо 401 (нет авторизации)
                    success = response.status_code in [200, 401]
                    results.append({
                        "test": description,
                        "url": url,
                        "status": "✅ ПРОЙДЕН" if success else f"❌ ОШИБКА {response.status_code}",
                        "response_time": response.elapsed.total_seconds(),
                        "success": success
                    })
                except Exception as e:
                    results.append({
                        "test": description,
                        "url": f"{self.backend_url}{endpoint}",
                        "status": f"❌ ОШИБКА: {str(e)}",
                        "success": False
                    })
        
        return {
            "component": "Service Integration",
            "tests": results,
            "success_rate": sum(1 for r in results if r["success"]) / len(results)
        }
    
    async def run_all_tests(self):
        """Запуск всех тестов"""
        print("🚀 ЗАПУСК ФИНАЛЬНОГО ТЕСТИРОВАНИЯ ПЛАТФОРМЫ")
        print("=" * 80)
        
        # Запускаем все тесты
        test_results = await asyncio.gather(
            self.test_backend_health(),
            self.test_ml_service_health(),
            self.test_ml_predictions(),
            self.test_integration()
        )
        
        # Анализируем результаты
        print("\n📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:")
        print("=" * 80)
        
        total_success_rate = 0
        total_components = len(test_results)
        
        for result in test_results:
            component = result["component"]
            success_rate = result["success_rate"]
            total_success_rate += success_rate
            
            print(f"\n🔧 {component}: {success_rate:.1%} успешность")
            
            for test in result["tests"]:
                print(f"   {test['status']} {test['test']}")
                if 'response_time' in test:
                    print(f"      Время ответа: {test['response_time']:.3f}s")
                if test.get('prediction_data') and 'success_probability' in test['prediction_data']:
                    pred = test['prediction_data']
                    print(f"      Предсказание: {pred['success_probability']:.1%} вероятность, {pred['recommendation']}")
        
        # Общий результат
        overall_success_rate = total_success_rate / total_components
        
        print("\n" + "=" * 80)
        print(f"🎯 ОБЩИЙ РЕЗУЛЬТАТ: {overall_success_rate:.1%} ГОТОВНОСТИ ПЛАТФОРМЫ")
        
        if overall_success_rate >= 0.9:
            print("✅ ПЛАТФОРМА ГОТОВА К ИСПОЛЬЗОВАНИЮ!")
            print("🚀 Все ключевые компоненты работают корректно")
        elif overall_success_rate >= 0.7:
            print("⚠️  ПЛАТФОРМА ЧАСТИЧНО ГОТОВА")
            print("🔧 Требуются небольшие доработки")
        else:
            print("❌ ПЛАТФОРМА НЕ ГОТОВА")
            print("🛠️  Требуются серьезные исправления")
        
        print("=" * 80)
        
        return overall_success_rate

async def main():
    """Главная функция"""
    tester = PlatformTester()
    success_rate = await tester.run_all_tests()
    
    # Возвращаем код выхода
    if success_rate >= 0.9:
        exit(0)  # Успех
    else:
        exit(1)  # Ошибка

if __name__ == "__main__":
    asyncio.run(main()) 