#!/usr/bin/env python3
"""
Простой тест API без зависания
"""

import requests
import json
import time

def test_api_simple():
    print("🧪 ПРОСТОЙ ТЕСТ API")
    print("=" * 40)
    
    # Тест 1: Проверка доступности портов
    print("\n1️⃣ Проверяем порты...")
    try:
        # Тест Backend API
        print("   Backend API (8000): ", end="")
        response = requests.get("http://localhost:8000/health", timeout=3)
        if response.status_code == 200:
            print("✅ РАБОТАЕТ")
        else:
            print(f"❌ Ошибка {response.status_code}")
    except Exception as e:
        print("❌ НЕДОСТУПЕН")
    
    try:
        # Тест ML Service
        print("   ML Service (8001): ", end="")
        response = requests.get("http://localhost:8001/health", timeout=3)
        if response.status_code == 200:
            print("✅ РАБОТАЕТ")
        else:
            print(f"❌ Ошибка {response.status_code}")
    except Exception as e:
        print("❌ НЕДОСТУПЕН")
    
    # Тест 2: Проверка данных
    print("\n2️⃣ Проверяем данные...")
    try:
        print("   Сигналы: ", end="")
        response = requests.get("http://localhost:8000/api/v1/signals/", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ {len(data)} сигналов")
            if len(data) > 0:
                print(f"   Первый сигнал: {data[0]['asset']} {data[0]['direction']}")
        else:
            print(f"❌ Ошибка {response.status_code}")
    except Exception as e:
        print("❌ НЕДОСТУПЕН")
    
    try:
        print("   Каналы: ", end="")
        response = requests.get("http://localhost:8000/api/v1/channels/", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ {len(data)} каналов")
            if len(data) > 0:
                print(f"   Первый канал: {data[0]['name']}")
        else:
            print(f"❌ Ошибка {response.status_code}")
    except Exception as e:
        print("❌ НЕДОСТУПЕН")
    
    print("\n" + "=" * 40)
    print("🎯 РЕЗУЛЬТАТ ТЕСТА")
    print("=" * 40)
    print("Если все тесты провалились - сервисы не запущены")
    print("Запустите: cd backend && python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload")

if __name__ == "__main__":
    test_api_simple()
