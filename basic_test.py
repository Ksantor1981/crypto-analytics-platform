#!/usr/bin/env python3
"""
Базовый тест функциональности
"""

import requests
import sqlite3
from datetime import datetime

def test_services():
    """Тест всех сервисов"""
    print("🚀 БАЗОВЫЙ ТЕСТ СИСТЕМЫ")
    print("=" * 40)
    print(f"Время: {datetime.now()}")
    print("=" * 40)
    
    # Тест 1: ML сервис
    print("\n1️⃣ ML сервис:")
    try:
        response = requests.get("http://localhost:8001/health", timeout=5)
        if response.status_code == 200:
            print("   ✅ Работает")
        else:
            print(f"   ❌ Ошибка: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
    
    # Тест 2: Backend
    print("\n2️⃣ Backend:")
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("   ✅ Работает")
        else:
            print(f"   ❌ Ошибка: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
    
    # Тест 3: База данных
    print("\n3️⃣ База данных:")
    try:
        conn = sqlite3.connect('backend/crypto_analytics.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM signals")
        signals = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM channels")
        channels = cursor.fetchone()[0]
        
        conn.close()
        
        print(f"   ✅ Сигналов: {signals}, Каналов: {channels}")
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
    
    # Тест 4: ML предсказание
    print("\n4️⃣ ML предсказание:")
    try:
        test_data = {
            "asset": "BTC",
            "entry_price": 45000,
            "target_price": 46500,
            "stop_loss": 43500,
            "direction": "LONG"
        }
        
        response = requests.post(
            "http://localhost:8001/api/v1/predictions/predict",
            json=test_data,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Результат: {result.get('prediction', 'N/A')}")
        else:
            print(f"   ❌ Ошибка: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
    
    print("\n" + "=" * 40)
    print("✅ БАЗОВЫЙ ТЕСТ ЗАВЕРШЕН")
    print("=" * 40)

if __name__ == "__main__":
    test_services()
