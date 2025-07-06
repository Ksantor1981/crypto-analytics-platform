#!/usr/bin/env python3
"""
Тест интеграции реальных данных
Проверяет работу с Telegram, Bybit API и получение реальных цен
"""
import asyncio
import sys
import os
sys.path.append('workers')

from workers.real_data_config import *
from workers.exchange.bybit_client import BybitClient
from workers.telegram.telegram_client import TelegramSignalCollector
from workers.exchange.price_monitor import PriceMonitor

async def test_bybit_integration():
    """Тест интеграции с Bybit API"""
    print("🏦 Тестирование Bybit API...")
    
    try:
        async with BybitClient() as client:
            # Тест соединения
            connection_ok = await client.test_connection()
            print(f"   ✅ Соединение: {'OK' if connection_ok else 'FAILED'}")
            
            if connection_ok:
                # Тест получения цен
                test_symbols = ["BTCUSDT", "ETHUSDT", "ADAUSDT"]
                prices = await client.get_current_prices(test_symbols)
                print(f"   ✅ Цены получены: {len(prices)} символов")
                for symbol, price in prices.items():
                    print(f"      {symbol}: ${price}")
                
                # Тест рыночных данных
                market_data = await client.get_market_data(["BTCUSDT"])
                if market_data:
                    btc_data = market_data.get("BTCUSDT", {})
                    print(f"   ✅ Рыночные данные BTC:")
                    print(f"      Цена: ${btc_data.get('current_price', 'N/A')}")
                    print(f"      Изменение 24ч: {btc_data.get('change_24h', 'N/A'):.2f}%")
                    print(f"      Объем 24ч: {btc_data.get('volume_24h', 'N/A')}")
                
                return True
            
    except Exception as e:
        print(f"   ❌ Ошибка Bybit: {e}")
        
    return False

async def test_telegram_integration():
    """Тест интеграции с Telegram"""
    print("📱 Тестирование Telegram API...")
    
    try:
        collector = TelegramSignalCollector(use_real_config=True)
        
        # Тест инициализации
        init_ok = await collector.initialize_client()
        print(f"   ✅ Инициализация: {'OK' if init_ok else 'FAILED'}")
        
        if init_ok:
            print(f"   ✅ Конфигурация:")
            print(f"      API ID: {TELEGRAM_API_ID}")
            print(f"      Каналы: {len(REAL_TELEGRAM_CHANNELS)} шт")
            print(f"      Символы: {len(CRYPTO_SYMBOLS)} шт")
            
            # Тест парсинга сигналов (mock)
            test_message = """
            🚀 BTC/USDT SIGNAL
            Direction: LONG
            Entry: 45000
            Target 1: 46000
            Target 2: 47000
            Stop Loss: 44000
            """
            
            from datetime import datetime
            signal = collector.parse_signal_message(test_message, datetime.now(), "test_channel")
            if signal:
                print(f"   ✅ Парсинг сигналов работает:")
                print(f"      Актив: {signal['asset']}")
                print(f"      Направление: {signal['direction']}")
                print(f"      Вход: {signal['entry_price']}")
                print(f"      Уверенность: {signal['confidence']:.2f}")
            
            return True
            
    except Exception as e:
        print(f"   ❌ Ошибка Telegram: {e}")
        
    return False

async def test_price_monitor():
    """Тест мониторинга цен"""
    print("📊 Тестирование мониторинга цен...")
    
    try:
        monitor = PriceMonitor(use_real_data=True)
        
        # Тест получения цен
        test_symbols = ["BTC/USDT", "ETH/USDT", "ADA/USDT"]
        prices = {}
        
        for symbol in test_symbols:
            price = await monitor.get_current_price(symbol)
            if price:
                prices[symbol] = price
                print(f"   ✅ {symbol}: ${price:.2f}")
        
        print(f"   ✅ Получено цен: {len(prices)}/{len(test_symbols)}")
        
        # Тест рыночных данных
        market_data = await monitor.get_market_data_real(["BTCUSDT", "ETHUSDT"])
        if market_data:
            print(f"   ✅ Рыночные данные: {len(market_data)} символов")
        
        return len(prices) > 0
        
    except Exception as e:
        print(f"   ❌ Ошибка мониторинга: {e}")
        
    return False

async def test_full_integration():
    """Полный тест интеграции"""
    print("🔄 Полный тест интеграции реальных данных...")
    print("=" * 60)
    
    results = {}
    
    # Тест Bybit
    results['bybit'] = await test_bybit_integration()
    print()
    
    # Тест Telegram
    results['telegram'] = await test_telegram_integration()
    print()
    
    # Тест мониторинга цен
    results['price_monitor'] = await test_price_monitor()
    print()
    
    # Итоги
    print("📋 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:")
    print("=" * 60)
    
    total_tests = len(results)
    passed_tests = sum(results.values())
    
    for component, status in results.items():
        status_text = "✅ PASSED" if status else "❌ FAILED"
        print(f"   {component.upper()}: {status_text}")
    
    print()
    print(f"📊 ИТОГО: {passed_tests}/{total_tests} тестов прошли успешно")
    
    if passed_tests == total_tests:
        print("🎉 ВСЕ ТЕСТЫ ПРОШЛИ! Интеграция реальных данных готова!")
    elif passed_tests > 0:
        print("⚠️ Частичная интеграция. Некоторые компоненты работают.")
    else:
        print("❌ Интеграция не работает. Проверьте API ключи и соединение.")
    
    return passed_tests, total_tests

async def main():
    """Главная функция"""
    print("🚀 ТЕСТИРОВАНИЕ ИНТЕГРАЦИИ РЕАЛЬНЫХ ДАННЫХ")
    print("=" * 60)
    print(f"📍 Проект: crypto-analytics-platform")
    print(f"🔑 API ключи из: analyst_crypto")
    print(f"📅 Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    passed, total = await test_full_integration()
    
    print()
    print("🎯 СЛЕДУЮЩИЕ ШАГИ:")
    if passed == total:
        print("   1. ✅ Запустить сбор реальных данных")
        print("   2. ✅ Переобучить ML модель на реальных данных")
        print("   3. ✅ Настроить автоматический мониторинг")
    else:
        print("   1. 🔧 Исправить проблемы с API")
        print("   2. 🔧 Проверить сетевое соединение")
        print("   3. 🔧 Обновить зависимости")

if __name__ == "__main__":
    from datetime import datetime
    asyncio.run(main()) 