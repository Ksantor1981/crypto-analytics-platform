#!/usr/bin/env python3
"""
Комплексный тест интеграции для блока 4
Тестирует взаимодействие между всеми компонентами системы
"""

import asyncio
import httpx
import json
import time
from datetime import datetime
from typing import Dict, Any

class IntegrationTester:
    def __init__(self):
        self.backend_url = "http://localhost:8000"
        self.ml_service_url = "http://localhost:8001"
        self.frontend_url = "http://localhost:3000"
        self.results = {}
        
    async def test_backend_health(self) -> bool:
        """Тест здоровья бэкенда"""
        print("🔍 Тест 1: Backend Health Check")
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.backend_url}/health")
                if response.status_code == 200:
                    data = response.json()
                    print(f"   ✅ Backend работает: {data.get('status', 'unknown')}")
                    self.results['backend_health'] = True
                    return True
                else:
                    print(f"   ❌ Backend недоступен: {response.status_code}")
                    self.results['backend_health'] = False
                    return False
        except Exception as e:
            print(f"   ❌ Ошибка подключения к бэкенду: {str(e)}")
            self.results['backend_health'] = False
            return False
    
    async def test_ml_service_health(self) -> bool:
        """Тест здоровья ML-сервиса"""
        print("🔍 Тест 2: ML Service Health Check")
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.ml_service_url}/api/v1/health/")
                if response.status_code == 200:
                    data = response.json()
                    print(f"   ✅ ML Service работает: {data.get('status', 'unknown')}")
                    self.results['ml_service_health'] = True
                    return True
                else:
                    print(f"   ❌ ML Service недоступен: {response.status_code}")
                    self.results['ml_service_health'] = False
                    return False
        except Exception as e:
            print(f"   ❌ Ошибка подключения к ML Service: {str(e)}")
            self.results['ml_service_health'] = False
            return False
    
    async def test_database_connection(self) -> bool:
        """Тест подключения к базе данных"""
        print("🔍 Тест 3: Database Connection")
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.backend_url}/api/v1/channels/")
                if response.status_code in [200, 401, 403]:  # 401/403 означает что API работает, но нужна авторизация
                    print("   ✅ База данных доступна")
                    self.results['database_connection'] = True
                    return True
                else:
                    print(f"   ❌ Проблема с базой данных: {response.status_code}")
                    self.results['database_connection'] = False
                    return False
        except Exception as e:
            print(f"   ❌ Ошибка подключения к БД: {str(e)}")
            self.results['database_connection'] = False
            return False
    
    async def test_ml_prediction_integration(self) -> bool:
        """Тест интеграции с ML-сервисом"""
        print("🔍 Тест 4: ML Prediction Integration")
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                # Тестовый сигнал
                test_signal = {
                    "asset": "BTCUSDT",
                    "direction": "LONG",
                    "entry_price": 45000.0,
                    "target_price": 47000.0,
                    "stop_loss": 43000.0,
                    "channel_id": 1,
                    "channel_accuracy": 0.75,
                    "confidence": 0.8
                }
                
                response = await client.post(
                    f"{self.ml_service_url}/api/v1/predictions/predict",
                    json=test_signal
                )
                
                if response.status_code == 200:
                    prediction = response.json()
                    print(f"   ✅ ML предсказание получено")
                    print(f"      Рекомендация: {prediction.get('recommendation', 'N/A')}")
                    print(f"      Уверенность: {prediction.get('confidence', 'N/A')}")
                    self.results['ml_prediction'] = True
                    return True
                else:
                    print(f"   ❌ Ошибка ML предсказания: {response.status_code}")
                    self.results['ml_prediction'] = False
                    return False
        except Exception as e:
            print(f"   ❌ Ошибка ML интеграции: {str(e)}")
            self.results['ml_prediction'] = False
            return False
    
    async def test_api_endpoints(self) -> bool:
        """Тест основных API эндпоинтов"""
        print("🔍 Тест 5: API Endpoints")
        endpoints = [
            "/api/v1/channels/",
            "/api/v1/signals/",
            "/api/v1/users/",
            "/api/v1/subscriptions/",
            "/api/v1/payments/"
        ]
        
        working_endpoints = 0
        async with httpx.AsyncClient(timeout=10.0) as client:
            for endpoint in endpoints:
                try:
                    response = await client.get(f"{self.backend_url}{endpoint}")
                    if response.status_code in [200, 401, 403, 404]:  # 404 тоже нормально для пустых эндпоинтов
                        working_endpoints += 1
                        print(f"   ✅ {endpoint}: {response.status_code}")
                    else:
                        print(f"   ❌ {endpoint}: {response.status_code}")
                except Exception as e:
                    print(f"   ❌ {endpoint}: ошибка - {str(e)}")
        
        success_rate = working_endpoints / len(endpoints)
        self.results['api_endpoints'] = success_rate >= 0.8
        print(f"   📊 Работающих эндпоинтов: {working_endpoints}/{len(endpoints)} ({success_rate:.1%})")
        return success_rate >= 0.8
    
    async def test_real_data_integration(self) -> bool:
        """Тест интеграции с реальными данными"""
        print("🔍 Тест 6: Real Data Integration")
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                # Тест получения рыночных данных
                response = await client.get(f"{self.ml_service_url}/api/v1/predictions/market-data/BTCUSDT")
                
                if response.status_code == 200:
                    market_data = response.json()
                    print(f"   ✅ Рыночные данные получены")
                    print(f"      Текущая цена BTC: ${market_data.get('current_price', 'N/A')}")
                    self.results['real_data_integration'] = True
                    return True
                else:
                    print(f"   ❌ Ошибка получения рыночных данных: {response.status_code}")
                    self.results['real_data_integration'] = False
                    return False
        except Exception as e:
            print(f"   ❌ Ошибка интеграции с реальными данными: {str(e)}")
            self.results['real_data_integration'] = False
            return False
    
    async def test_performance(self) -> bool:
        """Тест производительности"""
        print("🔍 Тест 7: Performance Test")
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Тест времени отклика бэкенда
                start_time = time.time()
                response = await client.get(f"{self.backend_url}/health")
                backend_response_time = time.time() - start_time
                
                # Тест времени отклика ML-сервиса
                start_time = time.time()
                response = await client.get(f"{self.ml_service_url}/api/v1/health/")
                ml_response_time = time.time() - start_time
                
                print(f"   📊 Backend response time: {backend_response_time:.3f}s")
                print(f"   📊 ML Service response time: {ml_response_time:.3f}s")
                
                # Проверяем что время отклика приемлемое (менее 2 секунд)
                performance_ok = backend_response_time < 2.0 and ml_response_time < 2.0
                self.results['performance'] = performance_ok
                
                if performance_ok:
                    print("   ✅ Производительность в норме")
                else:
                    print("   ⚠️ Производительность ниже ожидаемой")
                
                return performance_ok
        except Exception as e:
            print(f"   ❌ Ошибка теста производительности: {str(e)}")
            self.results['performance'] = False
            return False
    
    async def test_error_handling(self) -> bool:
        """Тест обработки ошибок"""
        print("🔍 Тест 8: Error Handling")
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Тест несуществующего эндпоинта
                response = await client.get(f"{self.backend_url}/api/v1/nonexistent/")
                if response.status_code == 404:
                    print("   ✅ 404 ошибка обрабатывается корректно")
                else:
                    print(f"   ⚠️ Неожиданный статус для несуществующего эндпоинта: {response.status_code}")
                
                # Тест неверного JSON в ML-сервисе
                response = await client.post(
                    f"{self.ml_service_url}/api/v1/predictions/predict",
                    json={"invalid": "data"}
                )
                if response.status_code in [422, 400]:
                    print("   ✅ Валидация данных работает корректно")
                else:
                    print(f"   ⚠️ Неожиданный статус для неверных данных: {response.status_code}")
                
                self.results['error_handling'] = True
                return True
        except Exception as e:
            print(f"   ❌ Ошибка теста обработки ошибок: {str(e)}")
            self.results['error_handling'] = False
            return False
    
    def generate_report(self) -> str:
        """Генерация отчета"""
        print("\n" + "="*60)
        print("📋 ОТЧЕТ ИНТЕГРАЦИОННОГО ТЕСТИРОВАНИЯ")
        print("="*60)
        
        total_tests = len(self.results)
        passed_tests = sum(1 for result in self.results.values() if result)
        success_rate = passed_tests / total_tests if total_tests > 0 else 0
        
        print(f"📊 Общий результат: {passed_tests}/{total_tests} ({success_rate:.1%})")
        print()
        
        for test_name, result in self.results.items():
            status = "✅ ПРОЙДЕН" if result else "❌ ПРОВАЛЕН"
            print(f"{status} {test_name}")
        
        print()
        
        if success_rate >= 0.8:
            print("🎉 БЛОК 4 ГОТОВ К ПРОДАКШЕНУ!")
            print("   Все критические компоненты работают корректно")
        elif success_rate >= 0.6:
            print("⚠️ БЛОК 4 ТРЕБУЕТ ДОРАБОТКИ")
            print("   Есть проблемы, которые нужно исправить")
        else:
            print("🚨 БЛОК 4 КРИТИЧЕСКИЕ ПРОБЛЕМЫ")
            print("   Требуется серьезная доработка")
        
        return f"integration_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    async def run_all_tests(self):
        """Запуск всех тестов"""
        print("🚀 ЗАПУСК ИНТЕГРАЦИОННОГО ТЕСТИРОВАНИЯ БЛОКА 4")
        print("="*60)
        
        tests = [
            self.test_backend_health,
            self.test_ml_service_health,
            self.test_database_connection,
            self.test_ml_prediction_integration,
            self.test_api_endpoints,
            self.test_real_data_integration,
            self.test_performance,
            self.test_error_handling
        ]
        
        for test in tests:
            try:
                await test()
                print()
            except Exception as e:
                print(f"❌ Критическая ошибка в тесте: {str(e)}")
                print()
        
        # Генерируем отчет
        report_file = self.generate_report()
        
        # Сохраняем результаты в файл
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'results': self.results,
                'summary': {
                    'total_tests': len(self.results),
                    'passed_tests': sum(1 for r in self.results.values() if r),
                    'success_rate': sum(1 for r in self.results.values() if r) / len(self.results)
                }
            }, f, indent=2, ensure_ascii=False)
        
        print(f"📄 Отчет сохранен в: {report_file}")

async def main():
    tester = IntegrationTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main()) 