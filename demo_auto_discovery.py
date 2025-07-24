#!/usr/bin/env python3
"""
ДЕМОНСТРАЦИЯ АВТОМАТИЧЕСКОГО ПОИСКА КАНАЛОВ
============================================
"""

import requests
import json
import time

def demo_automatic_discovery():
    """Демонстрация автоматического поиска каналов"""
    
    print("🤖 ДЕМОНСТРАЦИЯ АВТОМАТИЧЕСКОГО ПОИСКА КАНАЛОВ")
    print("="*60)
    print()
    
    print("📋 ЧТО ДЕЛАЕТ СИСТЕМА:")
    print("   1. 🔍 Автоматически ищет каналы по ключевым словам")
    print("   2. 📺 Анализирует каждый найденный канал")
    print("   3. 📊 Извлекает торговые сигналы из сообщений")
    print("   4. ✅ Добавляет каналы с сигналами в базу данных")
    print("   5. 📈 Возвращает подробную статистику")
    print()
    
    url = "http://localhost:8002/api/v1/channels/discover"
    
    try:
        print("🚀 ЗАПУСК АВТОМАТИЧЕСКОГО ПОИСКА...")
        print("⏳ Система ищет каналы с крипто-сигналами...")
        
        start_time = time.time()
        
        response = requests.post(
            url,
            headers={"Content-Type": "application/json"},
            json={},
            timeout=30
        )
        
        end_time = time.time()
        search_duration = round(end_time - start_time, 2)
        
        if response.status_code == 200:
            result = response.json()
            data = result.get('data', {})
            
            print("✅ ПОИСК ЗАВЕРШЕН!")
            print()
            
            print("📊 РЕЗУЛЬТАТЫ АВТОМАТИЧЕСКОГО ПОИСКА:")
            print(f"   ⏱️  Время поиска: {search_duration} секунд")
            print(f"   🔍 Всего каналов проанализировано: {data.get('total_channels_discovered', 0)}")
            print(f"   ✅ Каналов с сигналами найдено: {data.get('channels_with_signals', 0)}")
            print(f"   📈 Всего сигналов обнаружено: {data.get('total_signals_found', 0)}")
            print(f"   🤖 Метод поиска: {data.get('search_method', 'unknown')}")
            print()
            
            print("🔑 КЛЮЧЕВЫЕ СЛОВА ДЛЯ ПОИСКА:")
            keywords = data.get('keywords_used', [])
            for i, keyword in enumerate(keywords, 1):
                print(f"   {i}. {keyword}")
            print()
            
            print("📺 НАЙДЕННЫЕ КАНАЛЫ С СИГНАЛАМИ:")
            added_channels = data.get('added_channels', [])
            for i, channel in enumerate(added_channels[:5], 1):  # Показываем первые 5
                print(f"   {i}. {channel['name']} (@{channel['username']})")
                print(f"      📊 Сигналов: {channel['signals_count']}")
                print(f"      🔗 Тип: {channel['type']}")
                print()
            
            if len(added_channels) > 5:
                print(f"   ... и еще {len(added_channels) - 5} каналов")
                print()
            
            print("🎯 АВТОМАТИЧНОСТЬ СИСТЕМЫ:")
            print("   ✅ Поиск выполнен полностью автоматически")
            print("   ✅ Использованы алгоритмы машинного поиска")
            print("   ✅ Применены паттерны распознавания сигналов")
            print("   ✅ Результаты добавлены в базу данных")
            print()
            
            print("🚀 СИСТЕМА ГОТОВА К ИСПОЛЬЗОВАНИЮ!")
            print("   Теперь вы можете:")
            print("   - Просматривать найденные каналы")
            print("   - Анализировать торговые сигналы")
            print("   - Получать уведомления о новых сигналах")
            print("   - Отслеживать эффективность каналов")
            
            return True
        else:
            print(f"❌ ОШИБКА: {response.status_code}")
            try:
                error = response.json()
                print(f"   Детали: {error}")
            except:
                print(f"   Текст: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ ИСКЛЮЧЕНИЕ: {e}")
        return False

if __name__ == "__main__":
    success = demo_automatic_discovery()
    exit(0 if success else 1) 