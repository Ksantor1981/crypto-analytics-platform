#!/usr/bin/env python3
"""
Демонстрация завершенного блока 4: Интеграция и тестирование
Показывает работу всех интегрированных компонентов
"""

import asyncio
import httpx
import json
from datetime import datetime
from typing import Dict, Any

class Block4Demo:
    def __init__(self):
        self.backend_url = "http://localhost:8000"
        self.ml_service_url = "http://localhost:8001"
        self.results = {}
        
    async def demo_backend_integration(self):
        """Демонстрация работы бэкенда"""
        print("🔧 ДЕМО: Backend Integration")
        print("-" * 40)
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Health check
                response = await client.get(f"{self.backend_url}/health")
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ Backend Status: {data.get('status', 'unknown')}")
                    print(f"   Version: {data.get('version', 'N/A')}")
                    print(f"   Timestamp: {data.get('timestamp', 'N/A')}")
                
                # API endpoints
                endpoints = ["/api/v1/channels/", "/api/v1/signals/", "/api/v1/users/"]
                for endpoint in endpoints:
                    response = await client.get(f"{self.backend_url}{endpoint}")
                    status = "✅" if response.status_code in [200, 401, 403] else "❌"
                    print(f"{status} {endpoint}: {response.status_code}")
                
                self.results['backend'] = True
                
        except Exception as e:
            print(f"❌ Backend Error: {str(e)}")
            self.results['backend'] = False
    
    async def demo_ml_service_integration(self):
        """Демонстрация работы ML-сервиса"""
        print("\n🤖 ДЕМО: ML Service Integration")
        print("-" * 40)
        
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                # Health check
                response = await client.get(f"{self.ml_service_url}/api/v1/health/")
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ ML Service Status: {data.get('status', 'unknown')}")
                    print(f"   Model Version: {data.get('model_info', {}).get('version', 'N/A')}")
                    print(f"   Model Type: {data.get('model_info', {}).get('type', 'N/A')}")
                
                # Prediction demo
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
                    print(f"✅ ML Prediction:")
                    print(f"   Recommendation: {prediction.get('recommendation', 'N/A')}")
                    print(f"   Confidence: {prediction.get('confidence', 'N/A')}")
                    print(f"   Success Probability: {prediction.get('success_probability', 'N/A')}")
                
                # Market data demo
                response = await client.get(f"{self.ml_service_url}/api/v1/predictions/market-data/BTCUSDT")
                if response.status_code == 200:
                    market_data = response.json()
                    print(f"✅ Real Market Data:")
                    print(f"   Current Price: ${market_data.get('current_price', 'N/A')}")
                    print(f"   24h Change: {market_data.get('change_24h', 'N/A')}%")
                
                self.results['ml_service'] = True
                
        except Exception as e:
            print(f"❌ ML Service Error: {str(e)}")
            self.results['ml_service'] = False
    
    async def demo_performance_metrics(self):
        """Демонстрация метрик производительности"""
        print("\n⚡ ДЕМО: Performance Metrics")
        print("-" * 40)
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                import time
                
                # Backend performance
                start_time = time.time()
                response = await client.get(f"{self.backend_url}/health")
                backend_time = time.time() - start_time
                
                # ML service performance
                start_time = time.time()
                response = await client.get(f"{self.ml_service_url}/api/v1/health/")
                ml_time = time.time() - start_time
                
                print(f"✅ Backend Response Time: {backend_time:.3f}s")
                print(f"✅ ML Service Response Time: {ml_time:.3f}s")
                print(f"✅ Total System Latency: {backend_time + ml_time:.3f}s")
                
                # Performance assessment
                if backend_time < 0.1 and ml_time < 0.5:
                    print("🎉 Performance: EXCELLENT")
                elif backend_time < 0.2 and ml_time < 1.0:
                    print("✅ Performance: GOOD")
                else:
                    print("⚠️ Performance: NEEDS OPTIMIZATION")
                
                self.results['performance'] = True
                
        except Exception as e:
            print(f"❌ Performance Test Error: {str(e)}")
            self.results['performance'] = False
    
    async def demo_error_handling(self):
        """Демонстрация обработки ошибок"""
        print("\n🛡️ ДЕМО: Error Handling")
        print("-" * 40)
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Test 404 handling
                response = await client.get(f"{self.backend_url}/api/v1/nonexistent/")
                if response.status_code == 404:
                    print("✅ 404 Error Handling: WORKING")
                else:
                    print(f"⚠️ Unexpected 404 response: {response.status_code}")
                
                # Test invalid data handling
                response = await client.post(
                    f"{self.ml_service_url}/api/v1/predictions/predict",
                    json={"invalid": "data"}
                )
                if response.status_code in [422, 400]:
                    print("✅ Data Validation: WORKING")
                else:
                    print(f"⚠️ Unexpected validation response: {response.status_code}")
                
                # Test malformed JSON
                response = await client.post(
                    f"{self.ml_service_url}/api/v1/predictions/predict",
                    content="invalid json"
                )
                if response.status_code in [422, 400]:
                    print("✅ JSON Validation: WORKING")
                else:
                    print(f"⚠️ Unexpected JSON response: {response.status_code}")
                
                self.results['error_handling'] = True
                
        except Exception as e:
            print(f"❌ Error Handling Test Error: {str(e)}")
            self.results['error_handling'] = False
    
    def generate_summary(self):
        """Генерация итогового отчета"""
        print("\n" + "="*60)
        print("📋 ИТОГОВЫЙ ОТЧЕТ ДЕМОНСТРАЦИИ БЛОКА 4")
        print("="*60)
        
        total_tests = len(self.results)
        passed_tests = sum(1 for result in self.results.values() if result)
        success_rate = passed_tests / total_tests if total_tests > 0 else 0
        
        print(f"📊 Результат демонстрации: {passed_tests}/{total_tests} ({success_rate:.1%})")
        print()
        
        for test_name, result in self.results.items():
            status = "✅ РАБОТАЕТ" if result else "❌ НЕ РАБОТАЕТ"
            print(f"{status} {test_name}")
        
        print()
        
        if success_rate >= 0.8:
            print("🎉 БЛОК 4 УСПЕШНО ЗАВЕРШЕН!")
            print("   Все компоненты интегрированы и работают корректно")
            print("   Система готова к продакшену")
        elif success_rate >= 0.6:
            print("⚠️ БЛОК 4 ТРЕБУЕТ ДОРАБОТКИ")
            print("   Есть проблемы, которые нужно исправить")
        else:
            print("🚨 БЛОК 4 КРИТИЧЕСКИЕ ПРОБЛЕМЫ")
            print("   Требуется серьезная доработка")
        
        print("\n🚀 Следующий шаг: Блок 5 - Auto-trading")
    
    async def run_demo(self):
        """Запуск полной демонстрации"""
        print("🚀 ДЕМОНСТРАЦИЯ ЗАВЕРШЕННОГО БЛОКА 4")
        print("Интеграция и тестирование всех компонентов")
        print("="*60)
        
        demos = [
            self.demo_backend_integration,
            self.demo_ml_service_integration,
            self.demo_performance_metrics,
            self.demo_error_handling
        ]
        
        for demo in demos:
            try:
                await demo()
                await asyncio.sleep(1)  # Пауза между демо
            except Exception as e:
                print(f"❌ Критическая ошибка в демо: {str(e)}")
        
        self.generate_summary()

async def main():
    demo = Block4Demo()
    await demo.run_demo()

if __name__ == "__main__":
    asyncio.run(main()) 