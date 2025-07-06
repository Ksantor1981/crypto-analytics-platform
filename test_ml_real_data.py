#!/usr/bin/env python3
"""
Тест интеграции ML сервиса с реальными данными Bybit
"""
import asyncio
import requests
import json
import sys
import os
from datetime import datetime

# Add workers to path
sys.path.append('workers')

from workers.exchange.bybit_client import BybitClient
from workers.real_data_config import CRYPTO_SYMBOLS

def test_ml_service_basic():
    """Базовый тест ML сервиса"""
    print("🤖 Тестирование базовой функциональности ML сервиса...")
    
    try:
        # Health check
        response = requests.get("http://localhost:8001/health/", timeout=10)
        if response.status_code == 200:
            health_data = response.json()
            print(f"   ✅ Health Check: {health_data['status']}")
            print(f"   📊 Версия: {health_data['version']}")
        else:
            print(f"   ❌ Health Check failed: {response.status_code}")
            return False
            
        # Model info
        response = requests.get("http://localhost:8001/api/v1/predictions/model/info", timeout=10)
        if response.status_code == 200:
            model_data = response.json()
            print(f"   ✅ Model Info: {model_data['model_type']}")
            print(f"   🧠 Фичи: {len(model_data['feature_names'])}")
        else:
            print(f"   ❌ Model Info failed: {response.status_code}")
            return False
            
        return True
        
    except Exception as e:
        print(f"   ❌ Ошибка базового тестирования: {e}")
        return False

async def test_ml_with_real_bybit_data():
    """Тест ML предсказаний с реальными данными Bybit"""
    print("\n📊 Тестирование ML с реальными данными Bybit...")
    
    try:
        # Получаем реальные данные из Bybit
        async with BybitClient() as client:
            # Получаем рыночные данные для топ криптовалют
            test_symbols = ["BTCUSDT", "ETHUSDT", "ADAUSDT"]
            market_data = await client.get_market_data(test_symbols)
            
            if not market_data:
                print("   ❌ Не удалось получить данные из Bybit")
                return False
                
            print(f"   ✅ Получены данные для {len(market_data)} символов")
            
            # Тестируем предсказания для каждого символа
            success_count = 0
            
            for symbol, data in market_data.items():
                asset = symbol.replace("USDT", "")
                current_price = float(data['current_price'])
                
                # Создаем тестовый сигнал
                test_signal = {
                    "asset": asset,
                    "direction": "LONG",
                    "entry_price": current_price,
                    "target_price": current_price * 1.05,  # +5%
                    "stop_loss": current_price * 0.98      # -2%
                }
                
                print(f"\n   🔍 Тестирование {asset}:")
                print(f"      Текущая цена: ${current_price:.2f}")
                print(f"      Цель: ${test_signal['target_price']:.2f}")
                print(f"      Стоп: ${test_signal['stop_loss']:.2f}")
                
                # Отправляем запрос в ML сервис
                response = requests.post(
                    "http://localhost:8001/api/v1/predictions/predict",
                    json=test_signal,
                    timeout=15
                )
                
                if response.status_code == 200:
                    prediction = response.json()
                    print(f"      ✅ Предсказание: {prediction['prediction']}")
                    print(f"      🎯 Уверенность: {prediction['confidence']:.2f}")
                    print(f"      💰 Ожидаемая доходность: {prediction['expected_return']:.2f}%")
                    print(f"      ⚠️ Риск: {prediction['risk_level']}")
                    print(f"      📈 Рекомендация: {prediction['recommendation']}")
                    
                    # Проверяем, что используются реальные данные
                    if 'market_data' in prediction:
                        md = prediction['market_data']
                        if md.get('source') == 'bybit_real':
                            print(f"      🌐 Источник данных: Bybit (реальные)")
                            print(f"      📊 Изменение 24ч: {md.get('change_24h', 0):.2f}%")
                        else:
                            print(f"      ⚠️ Источник данных: {md.get('source', 'unknown')}")
                    
                    success_count += 1
                else:
                    print(f"      ❌ Ошибка предсказания: {response.status_code}")
                    print(f"      📝 Ответ: {response.text[:200]}")
            
            print(f"\n   📊 Результат: {success_count}/{len(market_data)} успешных предсказаний")
            return success_count > 0
            
    except Exception as e:
        print(f"   ❌ Ошибка тестирования с Bybit: {e}")
        return False

def test_ml_market_data_endpoint():
    """Тест endpoint получения рыночных данных"""
    print("\n📈 Тестирование endpoint рыночных данных...")
    
    try:
        test_assets = ["BTC", "ETH", "ADA"]
        success_count = 0
        
        for asset in test_assets:
            response = requests.get(
                f"http://localhost:8001/api/v1/predictions/market-data/{asset}",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    market_info = data['data']
                    print(f"   ✅ {asset}: ${market_info['current_price']:.2f}")
                    print(f"      📊 24h: {market_info.get('change_24h', 0):.2f}%")
                    success_count += 1
                else:
                    print(f"   ❌ {asset}: Данные не найдены")
            else:
                print(f"   ❌ {asset}: HTTP {response.status_code}")
        
        print(f"   📊 Получены данные для {success_count}/{len(test_assets)} активов")
        return success_count > 0
        
    except Exception as e:
        print(f"   ❌ Ошибка тестирования market data: {e}")
        return False

def test_ml_supported_assets():
    """Тест списка поддерживаемых активов"""
    print("\n📋 Тестирование списка поддерживаемых активов...")
    
    try:
        response = requests.get(
            "http://localhost:8001/api/v1/predictions/supported-assets",
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            assets = data.get('supported_assets', [])
            status = data.get('real_data_status', 'unknown')
            source = data.get('data_source', 'unknown')
            
            print(f"   ✅ Поддерживается {len(assets)} активов")
            print(f"   🌐 Статус реальных данных: {status}")
            print(f"   📊 Источник данных: {source}")
            print(f"   💰 Активы: {', '.join(assets[:5])}...")
            
            return len(assets) > 0
        else:
            print(f"   ❌ Ошибка получения списка: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        return False

async def main():
    """Основная функция тестирования"""
    print("🚀 ТЕСТИРОВАНИЕ ИНТЕГРАЦИИ ML СЕРВИСА С РЕАЛЬНЫМИ ДАННЫМИ")
    print("=" * 70)
    print(f"📅 Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    results = {}
    
    # Тест 1: Базовая функциональность
    results['basic'] = test_ml_service_basic()
    
    # Тест 2: Интеграция с Bybit
    results['bybit_integration'] = await test_ml_with_real_bybit_data()
    
    # Тест 3: Market data endpoint
    results['market_data'] = test_ml_market_data_endpoint()
    
    # Тест 4: Supported assets
    results['supported_assets'] = test_ml_supported_assets()
    
    # Итоги
    print("\n" + "=" * 70)
    print("📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:")
    print("=" * 70)
    
    total_tests = len(results)
    passed_tests = sum(results.values())
    
    for test_name, status in results.items():
        status_text = "✅ PASSED" if status else "❌ FAILED"
        print(f"   {test_name.upper().replace('_', ' ')}: {status_text}")
    
    print(f"\n📈 ИТОГО: {passed_tests}/{total_tests} тестов прошли успешно")
    
    if passed_tests == total_tests:
        print("🎉 ВСЕ ТЕСТЫ ПРОШЛИ! ML сервис полностью интегрирован с реальными данными!")
        print("\n🚀 СЛЕДУЮЩИЕ ШАГИ:")
        print("   1. ✅ Запустить сбор реальных сигналов из Telegram")
        print("   2. ✅ Настроить автоматическое переобучение ML модели")
        print("   3. ✅ Создать dashboard для мониторинга предсказаний")
    elif passed_tests > 0:
        print("⚠️ Частичная интеграция. Некоторые компоненты работают.")
        print("\n🔧 ТРЕБУЕТСЯ ДОРАБОТКА:")
        failed_tests = [name for name, status in results.items() if not status]
        for test in failed_tests:
            print(f"   - {test.replace('_', ' ').title()}")
    else:
        print("❌ Интеграция не работает. Проверьте сервисы и API ключи.")
    
    return passed_tests, total_tests

if __name__ == "__main__":
    passed, total = asyncio.run(main())
    
    if passed == total:
        print("\n🎯 ML СЕРВИС ГОТОВ К PRODUCTION!")
    else:
        print(f"\n⚠️ ТРЕБУЕТСЯ ИСПРАВЛЕНИЕ: {total - passed} проблем") 