#!/usr/bin/env python3
"""
Тест настоящего автоматического поиска каналов
"""

import requests
import json
import time

def test_real_discovery():
    """Тестирование настоящего автоматического поиска каналов"""
    
    print("🔍 ТЕСТ НАСТОЯЩЕГО АВТОМАТИЧЕСКОГО ПОИСКА КАНАЛОВ")
    print("="*60)
    
    url = "http://localhost:8002/api/v1/channels/discover"
    
    try:
        print(f"📡 Отправка POST запроса на {url}")
        print("⏳ Ожидаю результаты автоматического поиска...")
        
        start_time = time.time()
        
        response = requests.post(
            url,
            headers={"Content-Type": "application/json"},
            json={},
            timeout=30  # Увеличиваем таймаут для поиска
        )
        
        end_time = time.time()
        search_duration = round(end_time - start_time, 2)
        
        print(f"   Статус: {response.status_code}")
        print(f"   Время поиска: {search_duration} секунд")
        
        if response.status_code == 200:
            result = response.json()
            print("   ✅ УСПЕХ!")
            print(f"   Ответ: {json.dumps(result, indent=2, ensure_ascii=False)}")
            
            # Анализируем результат
            data = result.get('data', {})
            print(f"\n📊 РЕЗУЛЬТАТЫ АВТОМАТИЧЕСКОГО ПОИСКА:")
            print(f"   Всего каналов проанализировано: {data.get('total_channels_discovered', 0)}")
            print(f"   Каналов с сигналами найдено: {data.get('channels_with_signals', 0)}")
            print(f"   Всего сигналов обнаружено: {data.get('total_signals_found', 0)}")
            print(f"   Метод поиска: {data.get('search_method', 'unknown')}")
            print(f"   Ключевых слов использовано: {len(data.get('keywords_used', []))}")
            print(f"   Паттернов поиска: {data.get('patterns_used', 0)}")
            
            if data.get('added_channels'):
                print(f"\n📺 ДОБАВЛЕННЫЕ КАНАЛЫ:")
                for channel in data['added_channels']:
                    print(f"   - {channel['name']} (@{channel['username']}) - {channel['signals_count']} сигналов")
            
            # Проверяем автоматичность
            if data.get('search_method') == 'automatic_telegram_api':
                print(f"\n🤖 АВТОМАТИЧНОСТЬ:")
                print(f"   ✅ Поиск выполнен автоматически через Telegram API")
                print(f"   ✅ Использованы ключевые слова: {', '.join(data.get('keywords_used', [])[:5])}...")
                print(f"   ✅ Применены паттерны поиска сигналов")
                print(f"   ✅ Время выполнения: {search_duration} сек")
            else:
                print(f"\n⚠️ ВНИМАНИЕ: Поиск может быть не полностью автоматическим")
            
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
    success = test_real_discovery()
    exit(0 if success else 1) 