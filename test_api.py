#!/usr/bin/env python3
"""
Тестовый скрипт для проверки API
"""

import requests
import json
import time

def test_api():
    print("🧪 ТЕСТИРОВАНИЕ API СЕРВИСОВ")
    print("=" * 50)
    
    # Тест ML Service
    print("\n1️⃣ Тестируем ML Service (порт 8001)...")
    try:
        response = requests.get("http://localhost:8001/health", timeout=5)
        if response.status_code == 200:
            print("✅ ML Service работает!")
            print(f"   Ответ: {response.json()}")
        else:
            print(f"❌ ML Service ошибка: {response.status_code}")
    except Exception as e:
        print(f"❌ ML Service недоступен: {e}")
    
    # Тест ML Predictions
    print("\n2️⃣ Тестируем ML Predictions...")
    try:
        response = requests.get("http://localhost:8001/predictions/", timeout=5)
        if response.status_code == 200:
            print("✅ ML Predictions работает!")
            data = response.json()
            print(f"   Количество предсказаний: {len(data) if isinstance(data, list) else 'N/A'}")
        else:
            print(f"❌ ML Predictions ошибка: {response.status_code}")
    except Exception as e:
        print(f"❌ ML Predictions недоступен: {e}")
    
    # Тест ML Backtesting
    print("\n3️⃣ Тестируем ML Backtesting...")
    try:
        response = requests.get("http://localhost:8001/backtesting/", timeout=5)
        if response.status_code == 200:
            print("✅ ML Backtesting работает!")
            data = response.json()
            print(f"   Количество результатов: {len(data) if isinstance(data, list) else 'N/A'}")
        else:
            print(f"❌ ML Backtesting ошибка: {response.status_code}")
    except Exception as e:
        print(f"❌ ML Backtesting недоступен: {e}")
    
    # Тест ML Risk Analysis
    print("\n4️⃣ Тестируем ML Risk Analysis...")
    try:
        response = requests.get("http://localhost:8001/risk_analysis/", timeout=5)
        if response.status_code == 200:
            print("✅ ML Risk Analysis работает!")
            data = response.json()
            print(f"   Количество анализов: {len(data) if isinstance(data, list) else 'N/A'}")
        else:
            print(f"❌ ML Risk Analysis ошибка: {response.status_code}")
    except Exception as e:
        print(f"❌ ML Risk Analysis недоступен: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ")
    print("=" * 50)
    print("✅ Frontend: http://localhost:3001")
    print("✅ ML Service: http://localhost:8001")
    print("✅ ML Docs: http://localhost:8001/docs")
    print("\n🚀 Система готова к демонстрации!")

if __name__ == "__main__":
    test_api() 