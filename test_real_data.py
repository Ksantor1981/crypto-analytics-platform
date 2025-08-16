#!/usr/bin/env python3
"""
Тест реальных данных
"""

import requests
import json
from datetime import datetime

def test_real_market_data():
    """Тест получения реальных рыночных данных"""
    print("🔍 Тестирование реальных рыночных данных...")
    
    # Тестируем разные источники данных
    test_sources = [
        {
            "name": "ML Service Mock Data",
            "url": "http://localhost:8001/api/v1/predictions/market-data/BTC"
        },
        {
            "name": "Backend API",
            "url": "http://localhost:8000/api/v1/signals"
        }
    ]
    
    for source in test_sources:
        print(f"\n📊 {source['name']}:")
        try:
            response = requests.get(source['url'], timeout=10)
            print(f"   Статус: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if source['name'] == "ML Service Mock Data":
                    print(f"   Цена BTC: ${data['data']['price']:.2f}")
                    print(f"   Объем: {data['data']['volume']:.0f}")
                    print(f"   Изменение 24ч: {data['data']['change_24h']:.2f}%")
                    print(f"   Источник: {data['source']}")
                else:
                    print(f"   Данные: {len(data) if isinstance(data, list) else 'N/A'} записей")
            else:
                print(f"   Ошибка: {response.text}")
                
        except Exception as e:
            print(f"   ❌ Ошибка: {e}")

def test_real_prediction():
    """Тест предсказания с реальными ценами"""
    print("\n🔍 Тестирование предсказания с реальными ценами...")
    
    # Получаем текущую цену BTC
    try:
        response = requests.get("http://localhost:8001/api/v1/predictions/market-data/BTC")
        if response.status_code == 200:
            market_data = response.json()
            current_price = market_data['data']['price']
            
            print(f"📈 Текущая цена BTC: ${current_price:.2f}")
            
            # Создаем реалистичный сигнал
            entry_price = current_price
            target_price = current_price * 1.05  # +5%
            stop_loss = current_price * 0.98     # -2%
            
            prediction_data = {
                "asset": "BTC",
                "entry_price": entry_price,
                "target_price": target_price,
                "stop_loss": stop_loss,
                "direction": "LONG"
            }
            
            print(f"🎯 Сигнал:")
            print(f"   Вход: ${entry_price:.2f}")
            print(f"   Цель: ${target_price:.2f} (+5%)")
            print(f"   Стоп: ${stop_loss:.2f} (-2%)")
            
            # Получаем предсказание
            response = requests.post(
                "http://localhost:8001/api/v1/predictions/predict",
                json=prediction_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Предсказание:")
                print(f"   Результат: {result['prediction']}")
                print(f"   Уверенность: {result['confidence']:.1%}")
                print(f"   Ожидаемая доходность: {result['expected_return']:.1f}%")
                print(f"   Уровень риска: {result['risk_level']}")
                print(f"   Рекомендация: {result['recommendation']}")
                
                # Проверяем, используются ли реальные данные
                if 'market_data' in result:
                    print(f"📊 Рыночные данные в ответе:")
                    print(f"   Цена: ${result['market_data']['price']:.2f}")
                    print(f"   Объем: {result['market_data']['volume']:.0f}")
                    print(f"   Изменение: {result['market_data']['change_24h']:.2f}%")
            else:
                print(f"❌ Ошибка предсказания: {response.status_code}")
                
        else:
            print(f"❌ Не удалось получить рыночные данные: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")

def test_data_sources():
    """Тест доступности источников данных"""
    print("\n🔍 Тестирование источников данных...")
    
    # Проверяем доступность внешних API (без API ключей)
    external_sources = [
        {
            "name": "CoinGecko API (BTC)",
            "url": "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
        },
        {
            "name": "Binance Public API (BTCUSDT)",
            "url": "https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT"
        }
    ]
    
    for source in external_sources:
        print(f"\n🌐 {source['name']}:")
        try:
            response = requests.get(source['url'], timeout=10)
            print(f"   Статус: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if 'bitcoin' in data:
                    print(f"   Цена BTC: ${data['bitcoin']['usd']:.2f}")
                elif 'price' in data:
                    print(f"   Цена BTC: ${float(data['price']):.2f}")
                else:
                    print(f"   Данные: {data}")
            else:
                print(f"   Ошибка: {response.text}")
                
        except Exception as e:
            print(f"   ❌ Ошибка: {e}")

def main():
    """Основная функция тестирования"""
    print("🚀 ТЕСТИРОВАНИЕ РЕАЛЬНЫХ ДАННЫХ")
    print("=" * 50)
    print(f"Время: {datetime.now()}")
    print("=" * 50)
    
    try:
        test_real_market_data()
        test_real_prediction()
        test_data_sources()
        
        print("\n" + "=" * 50)
        print("✅ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО!")
        print("=" * 50)
        
    except Exception as e:
        print(f"\n❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
        print("=" * 50)

if __name__ == "__main__":
    main()
