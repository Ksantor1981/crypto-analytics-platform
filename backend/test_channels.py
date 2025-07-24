#!/usr/bin/env python3
"""
Simple test script for Telegram channels
"""
import requests
import json

def test_telegram_channels():
    base_url = "http://localhost:8000"
    
    print("=== Тестирование Telegram каналов ===\n")
    
    # Test health endpoint
    print("1. Проверка health endpoint...")
    try:
        response = requests.get(f"{base_url}/health")
        print(f"✅ Health: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"❌ Health error: {e}")
    
    # Test telegram channels endpoint (with DB)
    print("\n2. Проверка эндпоинта /api/v1/telegram/channels (с БД)...")
    try:
        response = requests.get(f"{base_url}/api/v1/telegram/channels")
        print(f"📊 Channels: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Успешно получено {data.get('total_channels', 0)} каналов")
            for channel in data.get('data', []):
                print(f"   - {channel['name']} (@{channel.get('username', 'N/A')}) - {channel['signals_count']} сигналов")
        else:
            print(f"❌ Ошибка: {response.json()}")
    except Exception as e:
        print(f"❌ Channels error: {e}")
    
    # Test telegram channels mock endpoint
    print("\n3. Проверка эндпоинта /api/v1/telegram/channels-mock (mock данные)...")
    try:
        response = requests.get(f"{base_url}/api/v1/telegram/channels-mock")
        print(f"📊 Channels Mock: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Успешно получено {data.get('total_channels', 0)} каналов (mock)")
            for channel in data.get('data', []):
                print(f"   - {channel['name']} - {channel['signals_count']} сигналов (точность: {channel['accuracy']}%)")
        else:
            print(f"❌ Ошибка: {response.json()}")
    except Exception as e:
        print(f"❌ Channels Mock error: {e}")
    
    # Test telegram collect signals endpoint
    print("\n4. Проверка эндпоинта сбора сигналов...")
    try:
        response = requests.get(f"{base_url}/api/v1/telegram/collect-signals-sync")
        print(f"📊 Collect Signals: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Сбор сигналов: {data.get('message', 'N/A')}")
        else:
            print(f"❌ Ошибка: {response.json()}")
    except Exception as e:
        print(f"❌ Collect Signals error: {e}")
    
    print("\n=== Тестирование завершено ===")

if __name__ == "__main__":
    test_telegram_channels() 