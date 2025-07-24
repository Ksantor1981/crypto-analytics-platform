#!/usr/bin/env python3
"""
Простой тест эндпоинта discover
"""

import requests
import json

def test_discover_endpoint():
    """Тестирование эндпоинта discover"""
    
    print("🧪 ПРОСТОЙ ТЕСТ ЭНДПОИНТА DISCOVER")
    print("="*40)
    
    url = "http://localhost:8000/api/v1/channels/discover"
    
    try:
        print(f"📡 Отправка POST запроса на {url}")
        
        response = requests.post(
            url,
            headers={"Content-Type": "application/json"},
            json={},
            timeout=10
        )
        
        print(f"   Статус: {response.status_code}")
        print(f"   Заголовки: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print("   ✅ УСПЕХ!")
            print(f"   Ответ: {json.dumps(result, indent=2, ensure_ascii=False)}")
            return True
        else:
            print(f"   ❌ ОШИБКА: {response.status_code}")
            try:
                error = response.json()
                print(f"   Детали: {error}")
            except:
                print(f"   Текст: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ ИСКЛЮЧЕНИЕ: {e}")
        return False

if __name__ == "__main__":
    success = test_discover_endpoint()
    exit(0 if success else 1) 