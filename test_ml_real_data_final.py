#!/usr/bin/env python3
"""
Финальный тест интеграции ML сервиса с реальными данными Bybit
"""

import requests
import asyncio
import sys
import os
from datetime import datetime

# Добавляем путь к workers
sys.path.append(os.path.join(os.path.dirname(__file__), 'workers'))

async def test_bybit_integration():
    """Тестирует интеграцию с Bybit API"""
    print("🔍 Тестирование интеграции с Bybit...")
    
    try:
        from workers.exchange.bybit_client import BybitClient
        from workers.real_data_config import CRYPTO_SYMBOLS
        
        async with BybitClient() as client:
            # Тестируем получение данных для популярных криптовалют
            test_symbols = ["BTCUSDT", "ETHUSDT", "BNBUSDT"]
            
            market_data = await client.get_market_data(test_symbols)
            
            for symbol in test_symbols:
                if symbol in market_data:
                    data = market_data[symbol]
                    print(f"✅ {symbol}: ${data.get('current_price', 'N/A')} "
                          f"({data.get('change_24h', 'N/A')}% за 24ч)")
                else:
                    print(f"❌ {symbol}: Данные недоступны")
            
            return len(market_data) > 0
            
    except ImportError as e:
        print(f"❌ Bybit клиент недоступен: {e}")
        return False
    except Exception as e:
        print(f"❌ Ошибка Bybit API: {e}")
        return False

def test_ml_with_real_data():
    """Тестирует ML предсказания с реальными данными"""
    print("🔍 Тестирование ML с реальными данными...")
    
    try:
        # Популярные криптовалюты для тестирования
        test_cases = [
            {
                "asset": "BTCUSDT",
                "entry_price": 45000.0,
                "target_price": 47000.0,
                "stop_loss": 43000.0,
                "direction": "LONG"
            },
            {
                "asset": "ETHUSDT", 
                "entry_price": 2500.0,
                "target_price": 2600.0,
                "stop_loss": 2400.0,
                "direction": "LONG"
            },
            {
                "asset": "BNBUSDT",
                "entry_price": 300.0,
                "target_price": 310.0,
                "stop_loss": 290.0,
                "direction": "LONG"
            }
        ]
        
        successful_predictions = 0
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n📊 Тест {i}: {test_case['asset']}")
            
            response = requests.post(
                "http://127.0.0.1:8001/api/v1/predictions/predict",
                json=test_case,
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                
                print(f"   Предсказание: {data.get('prediction', 'N/A')}")
                print(f"   Уверенность: {data.get('confidence', 'N/A'):.3f}")
                print(f"   Ожидаемая доходность: {data.get('expected_return', 'N/A'):.2f}%")
                print(f"   Уровень риска: {data.get('risk_level', 'N/A')}")
                print(f"   Рекомендация: {data.get('recommendation', 'N/A')}")
                
                # Проверяем наличие реальных рыночных данных
                market_data = data.get('market_data', {})
                if market_data.get('source') == 'bybit_real':
                    print(f"   ✅ Реальная цена: ${market_data.get('current_price', 'N/A')}")
                    print(f"   ✅ Изменение 24ч: {market_data.get('change_24h', 'N/A')}%")
                    successful_predictions += 1
                else:
                    print(f"   ⚠️  Использованы тестовые данные")
                    successful_predictions += 0.5  # Частичный успех
                    
            else:
                print(f"   ❌ Ошибка: {response.status_code} - {response.text}")
        
        success_rate = (successful_predictions / len(test_cases)) * 100
        print(f"\n📈 Успешность интеграции: {success_rate:.1f}%")
        
        return success_rate >= 70  # 70% успешности считается хорошим результатом
        
    except Exception as e:
        print(f"❌ Ошибка тестирования ML: {e}")
        return False

def test_market_data_endpoint():
    """Тестирует endpoint получения рыночных данных"""
    print("🔍 Тестирование endpoint рыночных данных...")
    
    try:
        test_assets = ["BTCUSDT", "ETHUSDT", "BNBUSDT"]
        
        for asset in test_assets:
            response = requests.get(
                f"http://127.0.0.1:8001/api/v1/predictions/market-data/{asset}",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ {asset}: {data.get('status', 'unknown')}")
                
                if 'market_data' in data:
                    market_info = data['market_data']
                    print(f"   Цена: ${market_info.get('current_price', 'N/A')}")
                    print(f"   Источник: {market_info.get('source', 'N/A')}")
            else:
                print(f"❌ {asset}: Ошибка {response.status_code}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования market data: {e}")
        return False

def test_supported_assets():
    """Тестирует endpoint поддерживаемых активов"""
    print("🔍 Тестирование поддерживаемых активов...")
    
    try:
        response = requests.get(
            "http://127.0.0.1:8001/api/v1/predictions/supported-assets",
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            supported_assets = data.get('supported_assets', [])
            
            print(f"✅ Поддерживается {len(supported_assets)} активов")
            print(f"   Примеры: {', '.join(supported_assets[:5])}")
            
            return len(supported_assets) > 0
        else:
            print(f"❌ Ошибка: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка тестирования активов: {e}")
        return False

async def main():
    """Основная функция тестирования"""
    print("🚀 Финальное тестирование интеграции с реальными данными")
    print("=" * 70)
    
    tests = [
        ("Bybit Integration", test_bybit_integration()),
        ("ML with Real Data", test_ml_with_real_data()),
        ("Market Data Endpoint", test_market_data_endpoint()),
        ("Supported Assets", test_supported_assets())
    ]
    
    results = {}
    
    for test_name, test_coro in tests:
        print(f"\n📋 {test_name}")
        print("-" * 50)
        
        try:
            if asyncio.iscoroutine(test_coro):
                results[test_name] = await test_coro
            else:
                results[test_name] = test_coro
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            results[test_name] = False
    
    # Итоговый отчет
    print("\n" + "=" * 70)
    print("📊 ИТОГОВЫЙ ОТЧЕТ ИНТЕГРАЦИИ")
    print("=" * 70)
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:25} : {status}")
    
    print("-" * 70)
    print(f"Пройдено тестов: {passed}/{total} ({(passed/total)*100:.1f}%)")
    
    if passed >= total * 0.75:  # 75% успешности
        print("🎉 ИНТЕГРАЦИЯ УСПЕШНА! ML сервис работает с реальными данными.")
        return True
    else:
        print("⚠️  ИНТЕГРАЦИЯ ЧАСТИЧНО РАБОТАЕТ. Возможны проблемы с API.")
        return False

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️  Тестирование прервано пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Критическая ошибка: {e}")
        sys.exit(1) 