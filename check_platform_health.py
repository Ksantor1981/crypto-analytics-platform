#!/usr/bin/env python3
"""
Проверка здоровья всей платформы Crypto Analytics
Показывает статус всех компонентов системы
"""

import asyncio
import httpx
import json
from datetime import datetime
from typing import Dict, Any

class PlatformHealthChecker:
    def __init__(self):
        self.services = {
            'backend': {
                'url': 'http://localhost:8000',
                'health_endpoint': '/health',
                'name': 'Backend API'
            },
            'ml_service': {
                'url': 'http://localhost:8001',
                'health_endpoint': '/api/v1/health/',
                'name': 'ML Service'
            },
            'frontend': {
                'url': 'http://localhost:3000',
                'health_endpoint': '/',
                'name': 'Frontend'
            }
        }
        self.results = {}
        
    async def check_service_health(self, service_key: str, service_config: Dict) -> Dict:
        """Проверка здоровья отдельного сервиса"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                url = f"{service_config['url']}{service_config['health_endpoint']}"
                response = await client.get(url)
                
                if response.status_code == 200:
                    return {
                        'status': 'healthy',
                        'response_time': response.elapsed.total_seconds(),
                        'status_code': response.status_code,
                        'data': response.json() if response.headers.get('content-type', '').startswith('application/json') else None
                    }
                else:
                    return {
                        'status': 'unhealthy',
                        'response_time': response.elapsed.total_seconds(),
                        'status_code': response.status_code,
                        'error': f"HTTP {response.status_code}"
                    }
        except Exception as e:
            return {
                'status': 'error',
                'response_time': None,
                'status_code': None,
                'error': str(e)
            }
    
    async def check_database_connection(self) -> Dict:
        """Проверка подключения к базе данных"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.services['backend']['url']}/api/v1/channels/")
                
                if response.status_code in [200, 401, 403]:
                    return {
                        'status': 'connected',
                        'response_time': response.elapsed.total_seconds(),
                        'status_code': response.status_code
                    }
                else:
                    return {
                        'status': 'error',
                        'response_time': response.elapsed.total_seconds(),
                        'status_code': response.status_code,
                        'error': f"Database connection failed: HTTP {response.status_code}"
                    }
        except Exception as e:
            return {
                'status': 'error',
                'response_time': None,
                'status_code': None,
                'error': str(e)
            }
    
    async def check_ml_prediction(self) -> Dict:
        """Проверка работы ML предсказаний"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
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
                    f"{self.services['ml_service']['url']}/api/v1/predictions/predict",
                    json=test_signal
                )
                
                if response.status_code == 200:
                    return {
                        'status': 'working',
                        'response_time': response.elapsed.total_seconds(),
                        'prediction': response.json()
                    }
                else:
                    return {
                        'status': 'error',
                        'response_time': response.elapsed.total_seconds(),
                        'error': f"ML prediction failed: HTTP {response.status_code}"
                    }
        except Exception as e:
            return {
                'status': 'error',
                'response_time': None,
                'error': str(e)
            }
    
    def print_service_status(self, service_name: str, result: Dict):
        """Вывод статуса сервиса"""
        if result['status'] == 'healthy':
            print(f"✅ {service_name}: ЗДОРОВ")
            if result.get('response_time'):
                print(f"   Время отклика: {result['response_time']:.3f}s")
            if result.get('data'):
                print(f"   Данные: {json.dumps(result['data'], ensure_ascii=False, indent=2)}")
        elif result['status'] == 'working':
            print(f"✅ {service_name}: РАБОТАЕТ")
            if result.get('response_time'):
                print(f"   Время отклика: {result['response_time']:.3f}s")
            if result.get('prediction'):
                pred = result['prediction']
                print(f"   Рекомендация: {pred.get('recommendation', 'N/A')}")
                print(f"   Уверенность: {pred.get('confidence', 'N/A')}")
        elif result['status'] == 'connected':
            print(f"✅ {service_name}: ПОДКЛЮЧЕН")
            if result.get('response_time'):
                print(f"   Время отклика: {result['response_time']:.3f}s")
        elif result['status'] == 'unhealthy':
            print(f"⚠️ {service_name}: НЕЗДОРОВ")
            print(f"   Ошибка: {result.get('error', 'Unknown error')}")
        else:
            print(f"❌ {service_name}: ОШИБКА")
            print(f"   Ошибка: {result.get('error', 'Unknown error')}")
    
    async def run_health_check(self):
        """Запуск полной проверки здоровья"""
        print("🏥 ПРОВЕРКА ЗДОРОВЬЯ ПЛАТФОРМЫ")
        print("=" * 50)
        print(f"Время проверки: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Проверка основных сервисов
        for service_key, service_config in self.services.items():
            print(f"🔍 Проверка {service_config['name']}...")
            result = await self.check_service_health(service_key, service_config)
            self.print_service_status(service_config['name'], result)
            self.results[service_key] = result
            print()
        
        # Проверка базы данных
        print("🔍 Проверка базы данных...")
        db_result = await self.check_database_connection()
        self.print_service_status("Database", db_result)
        self.results['database'] = db_result
        print()
        
        # Проверка ML предсказаний
        print("🔍 Проверка ML предсказаний...")
        ml_result = await self.check_ml_prediction()
        self.print_service_status("ML Predictions", ml_result)
        self.results['ml_predictions'] = ml_result
        print()
        
        # Итоговый отчет
        self.print_summary()
    
    def print_summary(self):
        """Вывод итогового отчета"""
        print("=" * 50)
        print("📋 ИТОГОВЫЙ ОТЧЕТ")
        print("=" * 50)
        
        total_services = len(self.results)
        healthy_services = sum(1 for result in self.results.values() 
                             if result['status'] in ['healthy', 'working', 'connected'])
        
        print(f"📊 Общий статус: {healthy_services}/{total_services} сервисов работают")
        
        if healthy_services == total_services:
            print("🎉 ВСЕ СЕРВИСЫ РАБОТАЮТ КОРРЕКТНО!")
            print("   Платформа готова к использованию")
        elif healthy_services >= total_services * 0.8:
            print("✅ БОЛЬШИНСТВО СЕРВИСОВ РАБОТАЕТ")
            print("   Есть незначительные проблемы")
        elif healthy_services >= total_services * 0.5:
            print("⚠️ ЕСТЬ ПРОБЛЕМЫ С СЕРВИСАМИ")
            print("   Требуется внимание")
        else:
            print("🚨 КРИТИЧЕСКИЕ ПРОБЛЕМЫ")
            print("   Система требует немедленного вмешательства")
        
        print()
        print("🔧 Рекомендации:")
        if healthy_services == total_services:
            print("   - Система работает стабильно")
            print("   - Можно переходить к продакшену")
        else:
            print("   - Проверить логи сервисов")
            print("   - Убедиться в доступности портов")
            print("   - Проверить конфигурацию")

async def main():
    checker = PlatformHealthChecker()
    await checker.run_health_check()

if __name__ == "__main__":
    asyncio.run(main()) 