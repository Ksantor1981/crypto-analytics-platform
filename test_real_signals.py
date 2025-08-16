#!/usr/bin/env python3
"""
Тест реальных сигналов
"""

import requests
import json
from datetime import datetime
import sys
import os

# Добавляем путь к workers для импорта
sys.path.append(os.path.join(os.path.dirname(__file__), 'workers'))

def test_telegram_integration():
    """Тест интеграции с Telegram"""
    print("🔍 Тестирование Telegram интеграции...")
    
    try:
        # Импортируем Telegram клиент
        from telegram.telegram_client import TelegramSignalCollector
        
        # Создаем коллектор
        collector = TelegramSignalCollector(use_real_config=True)
        
        print(f"✅ Telegram клиент создан")
        print(f"   API ID: {collector.api_id}")
        print(f"   Каналов: {len(collector.channels)}")
        
        # Проверяем конфигурацию
        for channel in collector.channels[:3]:  # Показываем первые 3
            print(f"   📺 {channel['name']} (@{channel['username']})")
            print(f"      Категория: {channel['category']}")
            print(f"      Успешность: {channel['success_rate']:.1%}")
            print(f"      Сигналов/день: {channel['avg_signals_per_day']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка Telegram интеграции: {e}")
        return False

def test_signal_parsing():
    """Тест парсинга сигналов"""
    print("\n🔍 Тестирование парсинга сигналов...")
    
    # Примеры реальных сигналов
    test_signals = [
        {
            "text": "🚀 BTC/USDT LONG\nEntry: 117,500\nTarget 1: 120,000\nTarget 2: 122,500\nStop Loss: 115,000\nLeverage: 10x",
            "channel": "@cryptosignals",
            "expected": {
                "asset": "BTC",
                "direction": "LONG",
                "entry_price": 117500,
                "target_price": 120000,
                "stop_loss": 115000
            }
        },
        {
            "text": "📉 ETH/USDT SHORT\nВход: 3,200\nЦель: 3,000\nСтоп: 3,300\nПлечо: 5x",
            "channel": "@binancesignals",
            "expected": {
                "asset": "ETH",
                "direction": "SHORT",
                "entry_price": 3200,
                "target_price": 3000,
                "stop_loss": 3300
            }
        },
        {
            "text": "🔥 SOL/USDT BUY\nEntry Price: $100\nTake Profit: $110\nStop Loss: $95\nConfidence: HIGH",
            "channel": "@cryptotradingview",
            "expected": {
                "asset": "SOL",
                "direction": "BUY",
                "entry_price": 100,
                "target_price": 110,
                "stop_loss": 95
            }
        }
    ]
    
    try:
        from telegram.signal_processor import SignalProcessor
        
        processor = SignalProcessor()
        
        for i, signal in enumerate(test_signals, 1):
            print(f"\n📊 Тест сигнала #{i}:")
            print(f"   Канал: {signal['channel']}")
            print(f"   Текст: {signal['text'][:50]}...")
            
            # Парсим сигнал
            parsed = processor.parse_signal(signal['text'], signal['channel'])
            
            if parsed:
                print(f"✅ Сигнал распознан:")
                print(f"   Актив: {parsed.get('asset', 'N/A')}")
                print(f"   Направление: {parsed.get('direction', 'N/A')}")
                print(f"   Вход: ${parsed.get('entry_price', 'N/A')}")
                print(f"   Цель: ${parsed.get('target_price', 'N/A')}")
                print(f"   Стоп: ${parsed.get('stop_loss', 'N/A')}")
                print(f"   Уверенность: {parsed.get('confidence', 'N/A')}")
            else:
                print(f"❌ Сигнал не распознан")
                
    except Exception as e:
        print(f"❌ Ошибка парсинга: {e}")

def test_backend_signals():
    """Тест сигналов в backend"""
    print("\n🔍 Тестирование сигналов в backend...")
    
    # Проверяем API endpoints
    endpoints = [
        "http://localhost:8000/api/v1/signals",
        "http://localhost:8000/api/v1/channels",
        "http://localhost:8000/api/v1/positions"
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(endpoint, timeout=5)
            print(f"📡 {endpoint}: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    print(f"   Записей: {len(data)}")
                elif isinstance(data, dict):
                    print(f"   Ключи: {list(data.keys())}")
            else:
                print(f"   Ошибка: {response.text[:100]}")
                
        except Exception as e:
            print(f"❌ {endpoint}: {e}")

def test_ml_prediction_with_real_signal():
    """Тест ML предсказания с реальным сигналом"""
    print("\n🔍 Тест ML предсказания с реальным сигналом...")
    
    # Создаем реалистичный сигнал на основе текущих цен
    try:
        # Получаем текущую цену BTC
        response = requests.get("http://localhost:8001/api/v1/predictions/market-data/BTC")
        if response.status_code == 200:
            market_data = response.json()
            current_price = market_data['data']['price']
            
            # Создаем сигнал
            signal_data = {
                "asset": "BTC",
                "entry_price": current_price,
                "target_price": current_price * 1.03,  # +3%
                "stop_loss": current_price * 0.99,     # -1%
                "direction": "LONG"
            }
            
            print(f"📈 Реальный сигнал:")
            print(f"   Актив: {signal_data['asset']}")
            print(f"   Вход: ${signal_data['entry_price']:.2f}")
            print(f"   Цель: ${signal_data['target_price']:.2f} (+3%)")
            print(f"   Стоп: ${signal_data['stop_loss']:.2f} (-1%)")
            
            # Получаем предсказание
            response = requests.post(
                "http://localhost:8001/api/v1/predictions/predict",
                json=signal_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ ML предсказание:")
                print(f"   Результат: {result['prediction']}")
                print(f"   Уверенность: {result['confidence']:.1%}")
                print(f"   Ожидаемая доходность: {result['expected_return']:.1f}%")
                print(f"   Уровень риска: {result['risk_level']}")
                print(f"   Рекомендация: {result['recommendation']}")
                
                # Проверяем источник данных
                if 'market_data' in result:
                    source = result['market_data'].get('source', 'unknown')
                    print(f"   Источник данных: {source}")
            else:
                print(f"❌ Ошибка предсказания: {response.status_code}")
                
        else:
            print(f"❌ Не удалось получить рыночные данные")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")

def main():
    """Основная функция тестирования"""
    print("🚀 ТЕСТИРОВАНИЕ РЕАЛЬНЫХ СИГНАЛОВ")
    print("=" * 50)
    print(f"Время: {datetime.now()}")
    print("=" * 50)
    
    try:
        # Тестируем все компоненты
        telegram_ok = test_telegram_integration()
        test_signal_parsing()
        test_backend_signals()
        test_ml_prediction_with_real_signal()
        
        print("\n" + "=" * 50)
        print("✅ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО!")
        
        if telegram_ok:
            print("🎯 Telegram интеграция: ГОТОВА")
        else:
            print("⚠️ Telegram интеграция: ТРЕБУЕТ НАСТРОЙКИ")
            
        print("=" * 50)
        
    except Exception as e:
        print(f"\n❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
        print("=" * 50)

if __name__ == "__main__":
    main()
