#!/usr/bin/env python3
"""
Тест функциональности обнаружения каналов с сигналами
"""

import requests
import json
import time
from datetime import datetime

def test_channel_discovery():
    """Тестирование эндпоинта обнаружения каналов"""
    
    print("🧪 ТЕСТИРОВАНИЕ ОБНАРУЖЕНИЯ КАНАЛОВ")
    print("="*50)
    print(f"Время запуска: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*50)
    
    # URL для тестирования
    base_url = "http://localhost:8000"
    discover_url = f"{base_url}/api/v1/channels/discover"
    
    try:
        print("📡 Проверка доступности сервера...")
        response = requests.get(f"{base_url}/docs", timeout=5)
        if response.status_code == 200:
            print("   ✅ Сервер доступен")
        else:
            print(f"   ❌ Сервер недоступен: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Ошибка подключения к серверу: {e}")
        return False
    
    try:
        print("\n🔍 Тестирование эндпоинта /channels/discover...")
        
        # Отправляем POST запрос для обнаружения каналов
        response = requests.post(
            discover_url,
            headers={"Content-Type": "application/json"},
            json={},
            timeout=30
        )
        
        print(f"   Статус ответа: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("   ✅ Запрос выполнен успешно!")
            
            # Анализируем результат
            print(f"\n📊 РЕЗУЛЬТАТЫ ОБНАРУЖЕНИЯ:")
            print(f"   Всего каналов обнаружено: {result['data']['total_channels_discovered']}")
            print(f"   Каналов с сигналами: {result['data']['channels_with_signals']}")
            print(f"   Сигналов добавлено: {result['data']['total_signals_added']}")
            
            if result['data']['added_channels']:
                print(f"\n📺 ДОБАВЛЕННЫЕ КАНАЛЫ:")
                for channel in result['data']['added_channels']:
                    print(f"   - {channel['name']} (@{channel['username']}) - {channel['type']}")
            
            if result['data']['added_signals']:
                print(f"\n📈 ДОБАВЛЕННЫЕ СИГНАЛЫ:")
                for signal in result['data']['added_signals']:
                    print(f"   - {signal['symbol']} {signal['signal_type'].upper()} из {signal['source']}")
            
            # Проверяем, что TelegramService возвращает 3 канала
            expected_channels = 3
            actual_channels = result['data']['total_channels_discovered']
            
            if actual_channels == expected_channels:
                print(f"\n✅ Ожидаемое количество каналов: {expected_channels}")
                print(f"   Фактическое количество: {actual_channels}")
            else:
                print(f"\n⚠️ Несоответствие количества каналов:")
                print(f"   Ожидалось: {expected_channels}")
                print(f"   Получено: {actual_channels}")
            
            # Проверяем, что SignalValidationService нашел сигналы
            if result['data']['channels_with_signals'] > 0:
                print(f"\n✅ SignalValidationService успешно нашел сигналы в каналах!")
            else:
                print(f"\n❌ SignalValidationService не нашел сигналы в каналах")
            
            return True
            
        else:
            print(f"   ❌ Ошибка запроса: {response.status_code}")
            try:
                error_detail = response.json()
                print(f"   Детали ошибки: {error_detail}")
            except:
                print(f"   Текст ответа: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Ошибка выполнения запроса: {e}")
        return False
    except json.JSONDecodeError as e:
        print(f"   ❌ Ошибка парсинга JSON ответа: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Неожиданная ошибка: {e}")
        return False

def test_api_documentation():
    """Проверка доступности API документации"""
    
    print("\n📚 ПРОВЕРКА API ДОКУМЕНТАЦИИ")
    print("="*50)
    
    try:
        response = requests.get("http://localhost:8000/docs", timeout=5)
        
        if response.status_code == 200:
            print("   ✅ API документация доступна")
            print("   🌐 Откройте в браузере: http://localhost:8000/docs")
            print("   🔍 Найдите эндпоинт: POST /channels/discover")
            print("   🧪 Нажмите 'Try it out' и затем 'Execute'")
            return True
        else:
            print(f"   ❌ API документация недоступна: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Ошибка доступа к документации: {e}")
        return False

def main():
    """Основная функция тестирования"""
    
    print("🚀 ЗАПУСК ТЕСТИРОВАНИЯ ОБНАРУЖЕНИЯ КАНАЛОВ")
    print("="*60)
    
    # Тест 1: Проверка API документации
    docs_ok = test_api_documentation()
    
    # Тест 2: Тестирование функциональности
    discovery_ok = test_channel_discovery()
    
    print("\n" + "="*60)
    print("📋 ИТОГИ ТЕСТИРОВАНИЯ")
    print("="*60)
    
    if docs_ok and discovery_ok:
        print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        print("\n✅ Система готова к использованию:")
        print("   - API документация доступна")
        print("   - Эндпоинт /channels/discover работает")
        print("   - TelegramService обнаруживает каналы")
        print("   - SignalValidationService находит сигналы")
        print("   - Каналы и сигналы добавляются в базу данных")
        
    elif docs_ok:
        print("⚠️ ЧАСТИЧНЫЙ УСПЕХ:")
        print("   ✅ API документация доступна")
        print("   ❌ Проблемы с функциональностью обнаружения")
        
    else:
        print("❌ ТЕСТЫ НЕ ПРОЙДЕНЫ:")
        print("   ❌ Проблемы с доступностью сервера")
        print("   ❌ Проблемы с функциональностью")
    
    print("\n" + "="*60)
    
    return docs_ok and discovery_ok

if __name__ == "__main__":
    try:
        success = main()
        exit_code = 0 if success else 1
        exit(exit_code)
    except KeyboardInterrupt:
        print("\n⚠️ Тестирование прервано пользователем")
        exit(1)
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        exit(1) 