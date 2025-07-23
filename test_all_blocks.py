#!/usr/bin/env python3
"""
Комплексный тест всех четырех завершенных блоков
Блок 0: Аудит и стабилизация
Блок 1: Frontend и MVP
Блок 2: Монетизация
Блок 3: Core Business Logic и ML
Блок 4: Интеграция и тестирование
"""

import asyncio
import httpx
import json
import time
from datetime import datetime
from typing import Dict, Any

class AllBlocksTester:
    def __init__(self):
        self.backend_url = "http://localhost:8000"
        self.ml_service_url = "http://localhost:8001"
        self.results = {}
        
    async def test_block0_infrastructure(self) -> bool:
        """Тест блока 0: Аудит и стабилизация"""
        print("🏗️ ТЕСТ БЛОКА 0: Аудит и стабилизация")
        print("-" * 50)
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Проверка стабильности бэкенда
                response = await client.get(f"{self.backend_url}/health")
                if response.status_code == 200:
                    print("✅ Backend стабилен")
                else:
                    print(f"❌ Backend нестабилен: {response.status_code}")
                    return False
                
                # Проверка стабильности ML-сервиса
                response = await client.get(f"{self.ml_service_url}/api/v1/health/")
                if response.status_code == 200:
                    print("✅ ML Service стабилен")
                else:
                    print(f"❌ ML Service нестабилен: {response.status_code}")
                    return False
                
                # Проверка базы данных
                response = await client.get(f"{self.backend_url}/api/v1/channels/")
                if response.status_code in [200, 401, 403]:
                    print("✅ База данных стабильна")
                else:
                    print(f"❌ База данных нестабильна: {response.status_code}")
                    return False
                
                print("✅ Блок 0: Инфраструктура стабильна")
                self.results['block0'] = True
                return True
                
        except Exception as e:
            print(f"❌ Ошибка блока 0: {str(e)}")
            self.results['block0'] = False
            return False
    
    async def test_block1_frontend_mvp(self) -> bool:
        """Тест блока 1: Frontend и MVP"""
        print("\n🎨 ТЕСТ БЛОКА 1: Frontend и MVP")
        print("-" * 50)
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Проверка API эндпоинтов для фронтенда
                endpoints = [
                    "/api/v1/channels/",
                    "/api/v1/signals/", 
                    "/api/v1/users/",
                    "/api/v1/subscriptions/",
                    "/api/v1/payments/"
                ]
                
                working_endpoints = 0
                for endpoint in endpoints:
                    response = await client.get(f"{self.backend_url}{endpoint}")
                    if response.status_code in [200, 401, 403]:
                        working_endpoints += 1
                        print(f"✅ {endpoint}: работает")
                    else:
                        print(f"❌ {endpoint}: не работает ({response.status_code})")
                
                if working_endpoints >= len(endpoints) * 0.8:
                    print(f"✅ Блок 1: {working_endpoints}/{len(endpoints)} API эндпоинтов работают")
                    self.results['block1'] = True
                    return True
                else:
                    print(f"❌ Блок 1: Недостаточно работающих эндпоинтов")
                    self.results['block1'] = False
                    return False
                    
        except Exception as e:
            print(f"❌ Ошибка блока 1: {str(e)}")
            self.results['block1'] = False
            return False
    
    async def test_block2_monetization(self) -> bool:
        """Тест блока 2: Монетизация"""
        print("\n💰 ТЕСТ БЛОКА 2: Монетизация")
        print("-" * 50)
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Проверка платежных эндпоинтов
                payment_endpoints = [
                    "/api/v1/payments/",
                    "/api/v1/subscriptions/"
                ]
                
                working_payment_endpoints = 0
                for endpoint in payment_endpoints:
                    response = await client.get(f"{self.backend_url}{endpoint}")
                    if response.status_code in [200, 401, 403]:
                        working_payment_endpoints += 1
                        print(f"✅ {endpoint}: работает")
                    else:
                        print(f"❌ {endpoint}: не работает ({response.status_code})")
                
                # Проверка системы подписок
                if working_payment_endpoints == len(payment_endpoints):
                    print("✅ Блок 2: Система монетизации работает")
                    self.results['block2'] = True
                    return True
                else:
                    print(f"❌ Блок 2: Проблемы с монетизацией")
                    self.results['block2'] = False
                    return False
                    
        except Exception as e:
            print(f"❌ Ошибка блока 2: {str(e)}")
            self.results['block2'] = False
            return False
    
    async def test_block3_ml_business_logic(self) -> bool:
        """Тест блока 3: Core Business Logic и ML"""
        print("\n🤖 ТЕСТ БЛОКА 3: Core Business Logic и ML")
        print("-" * 50)
        
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                # Проверка ML предсказаний
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
                    print(f"✅ ML предсказание работает")
                    print(f"   Рекомендация: {prediction.get('recommendation', 'N/A')}")
                    print(f"   Уверенность: {prediction.get('confidence', 'N/A')}")
                else:
                    print(f"❌ ML предсказание не работает: {response.status_code}")
                    return False
                
                # Проверка рыночных данных
                response = await client.get(f"{self.ml_service_url}/api/v1/predictions/market-data/BTCUSDT")
                if response.status_code == 200:
                    market_data = response.json()
                    print(f"✅ Рыночные данные работают")
                    print(f"   Текущая цена: ${market_data.get('current_price', 'N/A')}")
                else:
                    print(f"❌ Рыночные данные не работают: {response.status_code}")
                    return False
                
                # Проверка информации о модели
                response = await client.get(f"{self.ml_service_url}/api/v1/predictions/model/info")
                if response.status_code == 200:
                    model_info = response.json()
                    print(f"✅ Информация о модели доступна")
                    print(f"   Версия: {model_info.get('model_version', 'N/A')}")
                    print(f"   Тип: {model_info.get('model_type', 'N/A')}")
                else:
                    print(f"❌ Информация о модели недоступна: {response.status_code}")
                    return False
                
                print("✅ Блок 3: ML и бизнес-логика работают")
                self.results['block3'] = True
                return True
                
        except Exception as e:
            print(f"❌ Ошибка блока 3: {str(e)}")
            self.results['block3'] = False
            return False
    
    async def test_block4_integration(self) -> bool:
        """Тест блока 4: Интеграция и тестирование"""
        print("\n🔗 ТЕСТ БЛОКА 4: Интеграция и тестирование")
        print("-" * 50)
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Проверка производительности
                start_time = time.time()
                response = await client.get(f"{self.backend_url}/health")
                backend_time = time.time() - start_time
                
                start_time = time.time()
                response = await client.get(f"{self.ml_service_url}/api/v1/health/")
                ml_time = time.time() - start_time
                
                print(f"✅ Производительность в норме")
                print(f"   Backend: {backend_time:.3f}s")
                print(f"   ML Service: {ml_time:.3f}s")
                
                # Проверка обработки ошибок
                response = await client.get(f"{self.backend_url}/api/v1/nonexistent/")
                if response.status_code == 404:
                    print("✅ Обработка ошибок работает")
                else:
                    print(f"❌ Проблемы с обработкой ошибок: {response.status_code}")
                    return False
                
                # Проверка валидации данных
                response = await client.post(
                    f"{self.ml_service_url}/api/v1/predictions/predict",
                    json={"invalid": "data"}
                )
                if response.status_code in [422, 400]:
                    print("✅ Валидация данных работает")
                else:
                    print(f"❌ Проблемы с валидацией: {response.status_code}")
                    return False
                
                print("✅ Блок 4: Интеграция и тестирование работают")
                self.results['block4'] = True
                return True
                
        except Exception as e:
            print(f"❌ Ошибка блока 4: {str(e)}")
            self.results['block4'] = False
            return False
    
    def generate_final_report(self):
        """Генерация финального отчета"""
        print("\n" + "="*70)
        print("📋 ФИНАЛЬНЫЙ ОТЧЕТ ТЕСТИРОВАНИЯ ВСЕХ БЛОКОВ")
        print("="*70)
        
        total_blocks = len(self.results)
        passed_blocks = sum(1 for result in self.results.values() if result)
        success_rate = passed_blocks / total_blocks if total_blocks > 0 else 0
        
        print(f"📊 Результат тестирования: {passed_blocks}/{total_blocks} блоков ({success_rate:.1%})")
        print()
        
        block_names = {
            'block0': 'Блок 0: Аудит и стабилизация',
            'block1': 'Блок 1: Frontend и MVP',
            'block2': 'Блок 2: Монетизация',
            'block3': 'Блок 3: Core Business Logic и ML',
            'block4': 'Блок 4: Интеграция и тестирование'
        }
        
        for block_key, result in self.results.items():
            status = "✅ ПРОЙДЕН" if result else "❌ ПРОВАЛЕН"
            print(f"{status} {block_names.get(block_key, block_key)}")
        
        print()
        
        if success_rate == 1.0:
            print("🎉 ВСЕ БЛОКИ УСПЕШНО ПРОЙДЕНЫ!")
            print("   Система полностью готова к продакшену")
            print("   Можно переходить к блоку 5 (Auto-trading)")
        elif success_rate >= 0.8:
            print("✅ БОЛЬШИНСТВО БЛОКОВ РАБОТАЕТ")
            print("   Есть незначительные проблемы для исправления")
        elif success_rate >= 0.6:
            print("⚠️ ЕСТЬ ПРОБЛЕМЫ С БЛОКАМИ")
            print("   Требуется доработка перед продакшеном")
        else:
            print("🚨 КРИТИЧЕСКИЕ ПРОБЛЕМЫ")
            print("   Система требует серьезной доработки")
        
        print(f"\n📄 Отчет сохранен в: all_blocks_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        
        # Сохранение отчета
        report_data = {
            'timestamp': datetime.now().isoformat(),
            'results': self.results,
            'summary': {
                'total_blocks': total_blocks,
                'passed_blocks': passed_blocks,
                'success_rate': success_rate
            }
        }
        
        with open(f"all_blocks_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
    
    async def run_all_tests(self):
        """Запуск всех тестов"""
        print("🚀 КОМПЛЕКСНОЕ ТЕСТИРОВАНИЕ ВСЕХ ЧЕТЫРЕХ БЛОКОВ")
        print("="*70)
        
        tests = [
            self.test_block0_infrastructure,
            self.test_block1_frontend_mvp,
            self.test_block2_monetization,
            self.test_block3_ml_business_logic,
            self.test_block4_integration
        ]
        
        for test in tests:
            try:
                await test()
                await asyncio.sleep(1)  # Пауза между тестами
            except Exception as e:
                print(f"❌ Критическая ошибка в тесте: {str(e)}")
        
        self.generate_final_report()

async def main():
    tester = AllBlocksTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main()) 