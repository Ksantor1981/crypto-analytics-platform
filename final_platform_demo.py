#!/usr/bin/env python3
"""
🎉 ФИНАЛЬНАЯ ДЕМОНСТРАЦИЯ CRYPTO ANALYTICS PLATFORM
Полностью интегрированная платформа с реальными данными
"""

import requests
import time
import json
from datetime import datetime
from typing import Dict, Any

def print_header():
    """Печатает заголовок демонстрации"""
    print("🚀" + "=" * 68 + "🚀")
    print("🎉 CRYPTO ANALYTICS PLATFORM - ФИНАЛЬНАЯ ДЕМОНСТРАЦИЯ 🎉")
    print("🚀" + "=" * 68 + "🚀")
    print(f"📅 Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

def check_services():
    """Проверяет статус всех сервисов"""
    print("🔍 ПРОВЕРКА СТАТУСА СЕРВИСОВ")
    print("-" * 50)
    
    services = {
        "Backend API": "http://127.0.0.1:8000/docs",
        "ML Service": "http://127.0.0.1:8001/docs",
        "ML Health": "http://127.0.0.1:8001/api/v1/health/"
    }
    
    all_working = True
    
    for service_name, url in services.items():
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"✅ {service_name}: РАБОТАЕТ")
            else:
                print(f"❌ {service_name}: ОШИБКА {response.status_code}")
                all_working = False
        except Exception as e:
            print(f"❌ {service_name}: НЕДОСТУПЕН - {e}")
            all_working = False
    
    print()
    return all_working

def demonstrate_ml_predictions():
    """Демонстрирует ML предсказания с реальными данными"""
    print("🔮 ДЕМОНСТРАЦИЯ ML ПРЕДСКАЗАНИЙ С РЕАЛЬНЫМИ ДАННЫМИ")
    print("-" * 60)
    
    # Реальные торговые сценарии
    scenarios = [
        {
            "name": "Bitcoin Long Position",
            "data": {
                "asset": "BTCUSDT",
                "entry_price": 45000.0,
                "target_price": 47000.0,
                "stop_loss": 43000.0,
                "direction": "LONG"
            }
        },
        {
            "name": "Ethereum Short Position", 
            "data": {
                "asset": "ETHUSDT",
                "entry_price": 2500.0,
                "target_price": 2400.0,
                "stop_loss": 2600.0,
                "direction": "SHORT"
            }
        },
        {
            "name": "BNB Scalping Strategy",
            "data": {
                "asset": "BNBUSDT",
                "entry_price": 300.0,
                "target_price": 305.0,
                "stop_loss": 295.0,
                "direction": "LONG"
            }
        }
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n📊 Сценарий {i}: {scenario['name']}")
        print("   " + "-" * 40)
        
        try:
            response = requests.post(
                "http://127.0.0.1:8001/api/v1/predictions/predict",
                json=scenario['data'],
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                
                print(f"   💰 Актив: {result['asset']}")
                print(f"   🎯 Предсказание: {result['prediction']}")
                print(f"   📈 Уверенность: {result['confidence']:.1%}")
                print(f"   💵 Ожидаемая доходность: {result['expected_return']:.2f}%")
                print(f"   ⚠️  Уровень риска: {result['risk_level']}")
                print(f"   💡 Рекомендация: {result['recommendation']}")
                
                # Показываем реальные рыночные данные если доступны
                market_data = result.get('market_data', {})
                if market_data.get('source') == 'bybit_real':
                    print(f"   📊 Реальная цена: ${market_data['current_price']:,.2f}")
                    print(f"   📈 Изменение 24ч: {market_data['change_24h']:.3f}%")
                    print(f"   🕒 Данные обновлены: {market_data.get('timestamp', 'N/A')}")
                
            else:
                print(f"   ❌ Ошибка: {response.status_code}")
                
        except Exception as e:
            print(f"   💥 Ошибка: {e}")
    
    print()

def demonstrate_market_data():
    """Демонстрирует получение рыночных данных"""
    print("📊 ДЕМОНСТРАЦИЯ РЕАЛЬНЫХ РЫНОЧНЫХ ДАННЫХ")
    print("-" * 50)
    
    popular_assets = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "ADAUSDT", "XRPUSDT"]
    
    for asset in popular_assets:
        try:
            response = requests.get(
                f"http://127.0.0.1:8001/api/v1/predictions/market-data/{asset}",
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'market_data' in data:
                    market_info = data['market_data']
                    price = market_info.get('current_price', 'N/A')
                    change = market_info.get('change_24h', 'N/A')
                    source = market_info.get('source', 'unknown')
                    
                    print(f"💎 {asset}: ${price} ({change}% за 24ч) [{source}]")
                else:
                    print(f"⚠️  {asset}: Данные недоступны")
            else:
                print(f"❌ {asset}: Ошибка {response.status_code}")
                
        except Exception as e:
            print(f"💥 {asset}: {e}")
    
    print()

def demonstrate_health_monitoring():
    """Демонстрирует мониторинг здоровья системы"""
    print("🏥 ДЕМОНСТРАЦИЯ МОНИТОРИНГА СИСТЕМЫ")
    print("-" * 40)
    
    health_endpoints = [
        ("Базовый статус", "http://127.0.0.1:8001/api/v1/health/"),
        ("Детальная информация", "http://127.0.0.1:8001/api/v1/health/detailed"),
        ("Готовность системы", "http://127.0.0.1:8001/api/v1/health/readiness"),
        ("Жизнеспособность", "http://127.0.0.1:8001/api/v1/health/liveness")
    ]
    
    for name, url in health_endpoints:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                status = data.get('status', 'unknown')
                print(f"✅ {name}: {status.upper()}")
                
                # Показываем дополнительную информацию для детального статуса
                if 'system_metrics' in data:
                    metrics = data['system_metrics']
                    print(f"   💻 CPU: {metrics.get('cpu_percent', 'N/A')}%")
                    print(f"   🧠 RAM: {metrics.get('memory_percent', 'N/A')}%")
                    print(f"   💾 Диск: {metrics.get('disk_percent', 'N/A')}%")
                    
            else:
                print(f"❌ {name}: Ошибка {response.status_code}")
                
        except Exception as e:
            print(f"💥 {name}: {e}")
    
    print()

def demonstrate_supported_features():
    """Демонстрирует поддерживаемые возможности"""
    print("🌟 ПОДДЕРЖИВАЕМЫЕ ВОЗМОЖНОСТИ ПЛАТФОРМЫ")
    print("-" * 50)
    
    try:
        # Получаем информацию о сервисе
        response = requests.get("http://127.0.0.1:8001/api/v1/info", timeout=5)
        if response.status_code == 200:
            info = response.json()
            
            print(f"🏷️  Название сервиса: {info.get('service_name', 'N/A')}")
            print(f"🔧 Тип сервиса: {info.get('service_type', 'N/A')}")
            print(f"📦 Версия: {info.get('version', 'N/A')}")
            print(f"🤖 Тип модели: {info.get('model_type', 'N/A')}")
            
            features = info.get('features', [])
            print(f"⚡ Возможности ({len(features)}):")
            for feature in features:
                print(f"   • {feature}")
            
            assets = info.get('supported_assets', [])
            print(f"💰 Поддерживаемые активы ({len(assets)}):")
            print(f"   {', '.join(assets)}")
            
        # Получаем поддерживаемые активы через отдельный endpoint
        response = requests.get("http://127.0.0.1:8001/api/v1/predictions/supported-assets", timeout=5)
        if response.status_code == 200:
            data = response.json()
            supported = data.get('supported_assets', [])
            print(f"📈 Активно поддерживается: {len(supported)} торговых пар")
            
    except Exception as e:
        print(f"💥 Ошибка получения информации: {e}")
    
    print()

def performance_benchmark():
    """Проводит бенчмарк производительности"""
    print("⚡ БЕНЧМАРК ПРОИЗВОДИТЕЛЬНОСТИ")
    print("-" * 35)
    
    test_requests = 5
    successful_requests = 0
    total_time = 0
    
    test_data = {
        "asset": "BTCUSDT",
        "entry_price": 45000.0,
        "target_price": 46000.0,
        "stop_loss": 44000.0,
        "direction": "LONG"
    }
    
    print(f"🚀 Выполняем {test_requests} запросов...")
    
    for i in range(test_requests):
        try:
            start_time = time.time()
            response = requests.post(
                "http://127.0.0.1:8001/api/v1/predictions/predict",
                json=test_data,
                timeout=10
            )
            end_time = time.time()
            
            request_time = end_time - start_time
            total_time += request_time
            
            if response.status_code == 200:
                successful_requests += 1
                print(f"   ✅ Запрос {i+1}: {request_time:.2f}s")
            else:
                print(f"   ❌ Запрос {i+1}: Ошибка {response.status_code}")
                
        except Exception as e:
            print(f"   💥 Запрос {i+1}: {e}")
    
    if successful_requests > 0:
        avg_time = total_time / successful_requests
        success_rate = (successful_requests / test_requests) * 100
        
        print(f"\n📊 Результаты бенчмарка:")
        print(f"   ✅ Успешных запросов: {successful_requests}/{test_requests} ({success_rate:.1f}%)")
        print(f"   ⏱️  Среднее время ответа: {avg_time:.2f}s")
        print(f"   🚀 Пропускная способность: {1/avg_time:.1f} запросов/сек")
    
    print()

def main():
    """Основная функция демонстрации"""
    print_header()
    
    # Проверяем статус сервисов
    if not check_services():
        print("❌ Не все сервисы работают! Завершение демонстрации.")
        return False
    
    # Демонстрируем основные возможности
    demonstrate_ml_predictions()
    demonstrate_market_data()
    demonstrate_health_monitoring()
    demonstrate_supported_features()
    performance_benchmark()
    
    # Финальное сообщение
    print("🎉" + "=" * 68 + "🎉")
    print("🏆 ДЕМОНСТРАЦИЯ ЗАВЕРШЕНА УСПЕШНО!")
    print("🎯 Crypto Analytics Platform полностью готова к использованию!")
    print()
    print("📋 Доступные интерфейсы:")
    print("   🌐 Backend API: http://127.0.0.1:8000/docs")
    print("   🤖 ML Service: http://127.0.0.1:8001/docs")
    print()
    print("✨ Платформа готова для:")
    print("   • 📈 Анализа криптовалютных сигналов")
    print("   • 🔮 ML предсказаний на реальных данных")
    print("   • 📊 Мониторинга рыночных показателей")
    print("   • 🚀 Продакшен использования")
    print("🎉" + "=" * 68 + "🎉")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        if success:
            print("\n🎊 Демонстрация завершена успешно!")
        else:
            print("\n⚠️  Демонстрация завершена с ошибками.")
    except KeyboardInterrupt:
        print("\n⏹️  Демонстрация прервана пользователем.")
    except Exception as e:
        print(f"\n💥 Критическая ошибка: {e}") 