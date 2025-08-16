#!/usr/bin/env python3
"""
Быстрый тест основных компонентов
"""

import requests
import sqlite3
from datetime import datetime

def test_ml_service():
    """Тест ML сервиса"""
    print("🔍 Тест ML сервиса...")
    try:
        response = requests.get("http://localhost:8001/health", timeout=5)
        if response.status_code == 200:
            print("✅ ML сервис работает")
            return True
        else:
            print(f"❌ ML сервис: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ ML сервис: {e}")
        return False

def test_backend():
    """Тест backend"""
    print("🔍 Тест backend...")
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ Backend работает")
            return True
        else:
            print(f"❌ Backend: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Backend: {e}")
        return False

def test_database():
    """Тест базы данных"""
    print("🔍 Тест базы данных...")
    try:
        conn = sqlite3.connect('backend/crypto_analytics.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM signals")
        count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM channels")
        channels = cursor.fetchone()[0]
        
        conn.close()
        
        print(f"✅ База данных: {count} сигналов, {channels} каналов")
        return True
    except Exception as e:
        print(f"❌ База данных: {e}")
        return False

def test_ml_prediction():
    """Тест ML предсказания"""
    print("🔍 Тест ML предсказания...")
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
            print(f"✅ ML предсказание: {result.get('prediction', 'N/A')}")
            return True
        else:
            print(f"❌ ML предсказание: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ ML предсказание: {e}")
        return False

def main():
    print("🚀 БЫСТРЫЙ ТЕСТ КОМПОНЕНТОВ")
    print("=" * 40)
    print(f"Время: {datetime.now()}")
    print("=" * 40)
    
    tests = [
        ("ML сервис", test_ml_service),
        ("Backend", test_backend),
        ("База данных", test_database),
        ("ML предсказание", test_ml_prediction)
    ]
    
    results = []
    for name, test_func in tests:
        print(f"\n{name}:")
        result = test_func()
        results.append((name, result))
    
    print("\n" + "=" * 40)
    print("📊 РЕЗУЛЬТАТЫ:")
    
    success = 0
    for name, result in results:
        status = "✅" if result else "❌"
        print(f"   {name}: {status}")
        if result:
            success += 1
    
    print(f"\n🎯 УСПЕШНОСТЬ: {success}/{len(results)} ({success/len(results)*100:.1f}%)")
    
    if success == len(results):
        print("🎉 ВСЕ КОМПОНЕНТЫ РАБОТАЮТ!")
    else:
        print("⚠️ ЕСТЬ ПРОБЛЕМЫ")
    
    print("=" * 40)

if __name__ == "__main__":
    main()
