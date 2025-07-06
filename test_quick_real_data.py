#!/usr/bin/env python3
"""
Быстрый тест интеграции реальных данных (только Bybit)
"""
import asyncio
import sys
import os
sys.path.append('workers')

from workers.real_data_config import *
from workers.exchange.bybit_client import BybitClient
from workers.exchange.price_monitor import PriceMonitor

async def quick_test():
    """Быстрый тест реальных данных"""
    print("🚀 БЫСТРЫЙ ТЕСТ РЕАЛЬНЫХ ДАННЫХ")
    print("=" * 50)
    
    # 1. Тест Bybit API
    print("🏦 Тестирование Bybit API...")
    try:
        async with BybitClient() as client:
            # Тест соединения
            connection_ok = await client.test_connection()
            print(f"   ✅ Соединение: {'OK' if connection_ok else 'FAILED'}")
            
            if connection_ok:
                # Получаем цены всех наших символов
                prices = await client.get_current_prices(CRYPTO_SYMBOLS)
                print(f"   ✅ Получено цен: {len(prices)}")
                
                # Показываем топ-5 цен
                for i, (symbol, price) in enumerate(list(prices.items())[:5]):
                    print(f"      {symbol}: ${price}")
                
                # Получаем рыночные данные для BTC
                market_data = await client.get_market_data(["BTCUSDT", "ETHUSDT"])
                print(f"   ✅ Рыночные данные: {len(market_data)} символов")
                
                for symbol, data in market_data.items():
                    print(f"      {symbol}:")
                    print(f"        Цена: ${data.get('current_price', 'N/A')}")
                    print(f"        24h: {data.get('change_24h', 0):.2f}%")
                    print(f"        Объем: {data.get('volume_24h', 0):.2f}")
                
                return True
                
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        return False
    
    return False

async def test_price_monitor():
    """Тест мониторинга цен"""
    print("\n📊 Тестирование мониторинга цен...")
    
    try:
        monitor = PriceMonitor(use_real_data=True)
        
        # Тест получения цен через монитор
        test_symbols = ["BTC/USDT", "ETH/USDT", "ADA/USDT", "SOL/USDT"]
        prices = {}
        
        for symbol in test_symbols:
            price = await monitor.get_current_price(symbol)
            if price:
                prices[symbol] = price
                print(f"   ✅ {symbol}: ${price:.4f}")
        
        print(f"   ✅ Успешно получено: {len(prices)}/{len(test_symbols)} цен")
        return len(prices) > 0
        
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        return False

async def main():
    """Главная функция"""
    # Тест Bybit
    bybit_ok = await quick_test()
    
    # Тест мониторинга
    monitor_ok = await test_price_monitor()
    
    print("\n📋 РЕЗУЛЬТАТЫ:")
    print("=" * 50)
    print(f"🏦 Bybit API: {'✅ OK' if bybit_ok else '❌ FAILED'}")
    print(f"📊 Price Monitor: {'✅ OK' if monitor_ok else '❌ FAILED'}")
    
    if bybit_ok and monitor_ok:
        print("\n🎉 ОТЛИЧНО! Реальные данные работают!")
        print("📈 Можно переходить к интеграции с ML сервисом")
    else:
        print("\n⚠️ Есть проблемы с получением реальных данных")
    
    return bybit_ok and monitor_ok

if __name__ == "__main__":
    asyncio.run(main()) 