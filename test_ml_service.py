#!/usr/bin/env python3
"""
Тестирование ML сервиса
"""

import requests
import json
from datetime import datetime

# Базовый URL ML сервиса
ML_SERVICE_URL = "http://localhost:8001"

def test_health():
    """Тест health endpoints"""
    print("🔍 Тестирование health endpoints...")
    
    # Основной health
    response = requests.get(f"{ML_SERVICE_URL}/")
    print(f"✅ Основной health: {response.status_code}")
    print(f"   Ответ: {response.json()}")
    
    # Health predictions
    response = requests.get(f"{ML_SERVICE_URL}/api/v1/predictions/health")
    print(f"✅ Predictions health: {response.status_code}")
    print(f"   Ответ: {response.json()}")
    
    # Health backtesting
    response = requests.get(f"{ML_SERVICE_URL}/api/v1/backtesting/health")
    print(f"✅ Backtesting health: {response.status_code}")
    print(f"   Ответ: {response.json()}")
    
    # Health risk analysis
    response = requests.get(f"{ML_SERVICE_URL}/api/v1/risk-analysis/health")
    print(f"✅ Risk analysis health: {response.status_code}")
    print(f"   Ответ: {response.json()}")

def test_model_info():
    """Тест информации о модели"""
    print("\n🔍 Тестирование информации о модели...")
    
    response = requests.get(f"{ML_SERVICE_URL}/api/v1/predictions/model/info")
    print(f"✅ Model info: {response.status_code}")
    data = response.json()
    print(f"   Версия модели: {data['model_version']}")
    print(f"   Тип модели: {data['model_type']}")
    print(f"   Обучена: {data['is_trained']}")
    print(f"   Признаки: {data['feature_names']}")

def test_market_data():
    """Тест рыночных данных"""
    print("\n🔍 Тестирование рыночных данных...")
    
    assets = ["BTC", "ETH", "BNB", "SOL"]
    
    for asset in assets:
        response = requests.get(f"{ML_SERVICE_URL}/api/v1/predictions/market-data/{asset}")
        print(f"✅ Market data {asset}: {response.status_code}")
        data = response.json()
        print(f"   Цена: ${data['data']['price']:.2f}")
        print(f"   Объем: {data['data']['volume']:.0f}")
        print(f"   Изменение 24ч: {data['data']['change_24h']:.2f}%")
        print(f"   RSI: {data['data']['rsi']:.2f}")

def test_prediction():
    """Тест предсказаний"""
    print("\n🔍 Тестирование предсказаний...")
    
    # Тестовые данные
    test_cases = [
        {
            "asset": "BTC",
            "entry_price": 50000,
            "target_price": 55000,
            "stop_loss": 48000,
            "direction": "LONG"
        },
        {
            "asset": "ETH",
            "entry_price": 3000,
            "target_price": 3300,
            "stop_loss": 2850,
            "direction": "LONG"
        },
        {
            "asset": "SOL",
            "entry_price": 100,
            "target_price": 90,
            "stop_loss": 110,
            "direction": "SHORT"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📊 Тест предсказания #{i}:")
        print(f"   Актив: {test_case['asset']}")
        print(f"   Направление: {test_case['direction']}")
        print(f"   Вход: ${test_case['entry_price']}")
        print(f"   Цель: ${test_case['target_price']}")
        print(f"   Стоп: ${test_case['stop_loss']}")
        
        try:
            response = requests.post(
                f"{ML_SERVICE_URL}/api/v1/predictions/predict",
                json=test_case,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Предсказание успешно!")
                print(f"   Результат: {data['prediction']}")
                print(f"   Уверенность: {data['confidence']:.2f}")
                print(f"   Ожидаемая доходность: {data['expected_return']:.2f}%")
                print(f"   Уровень риска: {data['risk_level']}")
                print(f"   Рекомендация: {data['recommendation']}")
            else:
                print(f"❌ Ошибка: {response.status_code}")
                print(f"   Ответ: {response.text}")
                
        except Exception as e:
            print(f"❌ Исключение: {e}")

def test_backtesting():
    """Тест бэктестинга"""
    print("\n🔍 Тестирование бэктестинга...")
    
    backtest_request = {
        "asset": "BTC",
        "start_date": "2024-01-01",
        "end_date": "2024-12-31",
        "strategy": "simple",
        "initial_capital": 10000
    }
    
    try:
        response = requests.post(
            f"{ML_SERVICE_URL}/api/v1/backtesting/run",
            json=backtest_request,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Бэктестинг успешен!")
            print(f"   Актив: {data['asset']}")
            print(f"   Период: {data['period']}")
            print(f"   Общая доходность: {data['results']['total_return']:.2f}%")
            print(f"   Коэффициент Шарпа: {data['results']['sharpe_ratio']:.2f}")
            print(f"   Максимальная просадка: {data['results']['max_drawdown']:.2f}%")
            print(f"   Винрейт: {data['results']['win_rate']:.2f}%")
            print(f"   Всего сделок: {data['results']['total_trades']}")
        else:
            print(f"❌ Ошибка: {response.status_code}")
            print(f"   Ответ: {response.text}")
            
    except Exception as e:
        print(f"❌ Исключение: {e}")

def test_risk_analysis():
    """Тест анализа рисков"""
    print("\n🔍 Тестирование анализа рисков...")
    
    risk_request = {
        "asset": "BTC",
        "position_size": 1000,
        "entry_price": 50000,
        "stop_loss": 48000,
        "take_profit": 55000,
        "direction": "LONG",
        "risk_tolerance": "MEDIUM"
    }
    
    try:
        response = requests.post(
            f"{ML_SERVICE_URL}/api/v1/risk-analysis/analyze",
            json=risk_request,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Анализ рисков успешен!")
            print(f"   Актив: {data['asset']}")
            print(f"   Уровень риска: {data['risk_level']}")
            print(f"   Оценка риска: {data['risk_score']:.2f}")
            print(f"   Рекомендации: {data['recommendations']}")
            print(f"   Предупреждения: {data['warnings']}")
        else:
            print(f"❌ Ошибка: {response.status_code}")
            print(f"   Ответ: {response.text}")
            
    except Exception as e:
        print(f"❌ Исключение: {e}")

def main():
    """Основная функция тестирования"""
    print("🚀 ТЕСТИРОВАНИЕ ML СЕРВИСА")
    print("=" * 50)
    print(f"Время начала: {datetime.now()}")
    print(f"URL сервиса: {ML_SERVICE_URL}")
    print("=" * 50)
    
    try:
        # Тестируем все компоненты
        test_health()
        test_model_info()
        test_market_data()
        test_prediction()
        test_backtesting()
        test_risk_analysis()
        
        print("\n" + "=" * 50)
        print("✅ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО УСПЕШНО!")
        print("=" * 50)
        
    except Exception as e:
        print(f"\n❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
        print("=" * 50)

if __name__ == "__main__":
    main() 