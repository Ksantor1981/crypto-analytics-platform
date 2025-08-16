#!/usr/bin/env python3
"""
Непрерывный автоматический сбор сигналов
"""

import asyncio
import time
from datetime import datetime

async def collect_signals():
    """Сбор сигналов"""
    print("📡 Сбор сигналов...")
    
    # Имитируем сбор сигналов
    await asyncio.sleep(1)
    
    # Возвращаем mock результат
    return {
        "status": "success",
        "signals": [
            {
                "asset": "BTC/USDT",
                "direction": "LONG",
                "entry_price": 45000 + int(time.time()) % 1000,
                "channel": "@cryptosignals",
                "confidence": 0.85
            },
            {
                "asset": "ETH/USDT", 
                "direction": "SHORT",
                "entry_price": 3200 + int(time.time()) % 100,
                "channel": "@binancesignals",
                "confidence": 0.78
            }
        ],
        "total_signals": 2
    }

async def auto_collection_loop():
    """Непрерывный сбор сигналов"""
    print("🚀 ЗАПУСК НЕПРЕРЫВНОГО АВТОМАТИЧЕСКОГО СБОРА")
    print("=" * 50)
    print(f"Время запуска: {datetime.now()}")
    print("=" * 50)
    
    cycle = 1
    
    try:
        while True:
            print(f"\n🔄 Цикл #{cycle}")
            print(f"⏰ Время: {datetime.now()}")
            
            # Собираем сигналы
            result = await collect_signals()
            
            print(f"✅ Сбор завершен")
            print(f"   Статус: {result.get('status')}")
            print(f"   Сигналов: {result.get('total_signals')}")
            
            if result.get('signals'):
                print(f"   Последние сигналы:")
                for signal in result['signals']:
                    print(f"     • {signal.get('asset')} {signal.get('direction')} @ ${signal.get('entry_price')}")
            
            print(f"⏳ Ожидание 10 секунд до следующего цикла...")
            await asyncio.sleep(10)
            cycle += 1
            
    except KeyboardInterrupt:
        print(f"\n🛑 Остановка автоматического сбора")
        print(f"📊 Всего циклов: {cycle}")
        print("=" * 50)
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        print("=" * 50)

if __name__ == "__main__":
    asyncio.run(auto_collection_loop())
