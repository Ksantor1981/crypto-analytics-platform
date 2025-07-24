#!/usr/bin/env python3
"""
Тест эндпоинта discover на порту 8002
"""

import requests
import json

def test_discover_endpoint():
    """Тестирование эндпоинта discover"""
    
    print("🧪 ТЕСТ ЭНДПОИНТА DISCOVER НА ПОРТУ 8002")
    print("="*50)
    
    url = "http://localhost:8002/api/v1/channels/discover"
    
    try:
        print(f"📡 Отправка POST запроса на {url}")
        
        response = requests.post(
            url,
            headers={"Content-Type": "application/json"},
            json={},
            timeout=10
        )
        
        print(f"   Статус: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("   ✅ УСПЕХ!")
            print(f"   Ответ: {json.dumps(result, indent=2, ensure_ascii=False)}")
            
            # Анализируем результат
            data = result.get('data', {})
            print(f"\n📊 РЕЗУЛЬТАТЫ:")
            print(f"   Всего каналов обнаружено: {data.get('total_channels_discovered', 0)}")
            print(f"   Каналов с сигналами: {data.get('channels_with_signals', 0)}")
            print(f"   Сигналов добавлено: {data.get('total_signals_added', 0)}")
            
            if data.get('added_channels'):
                print(f"\n📺 ДОБАВЛЕННЫЕ КАНАЛЫ:")
                for channel in data['added_channels']:
                    print(f"   - {channel['name']} (@{channel['username']})")
            
            if data.get('added_signals'):
                print(f"\n📈 ДОБАВЛЕННЫЕ СИГНАЛЫ:")
                for signal in data['added_signals']:
                    print(f"   - {signal['symbol']} {signal['signal_type'].upper()} из {signal['source']}")
            
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