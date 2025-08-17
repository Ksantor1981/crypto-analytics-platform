"""
Получение последнего сигнала с канала
"""
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from telegram.authorized_scraper import AuthorizedTelegramScraper
from real_data_config import TELEGRAM_API_ID, TELEGRAM_API_HASH

async def get_last_signal():
    """Получение последнего сигнала"""
    
    # Запрашиваем номер телефона
    phone = input("Введите номер телефона (например, +79001234567): ").strip()
    
    if not phone:
        print("❌ Номер телефона не введен")
        return
    
    scraper = AuthorizedTelegramScraper(TELEGRAM_API_ID, TELEGRAM_API_HASH, phone)
    
    try:
        print("🔐 Подключение к Telegram...")
        
        # Запускаем клиент
        if await scraper.start():
            print("✅ Успешное подключение!")
            
            # Получаем последний сигнал
            print("🔍 Поиск последнего сигнала...")
            last_signal = await scraper.get_last_signal("signalsbitcoinandethereum")
            
            if last_signal:
                print("\n🎯 ПОСЛЕДНИЙ СИГНАЛ:")
                print("=" * 50)
                print(f"Канал: {last_signal['channel_title']}")
                print(f"Пара: {last_signal['trading_pair']}")
                print(f"Направление: {last_signal['direction']}")
                print(f"Entry: {last_signal['entry_price']}")
                print(f"Target: {last_signal['target_price']}")
                print(f"Stop: {last_signal['stop_loss']}")
                print(f"Дата: {last_signal['message_date']}")
                print(f"Confidence: {last_signal['confidence']}")
                print("=" * 50)
                
                # Получаем недавние сигналы
                print("\n📊 Недавние сигналы (за 24 часа):")
                recent_signals = await scraper.get_recent_signals("signalsbitcoinandethereum", hours_back=24)
                print(f"Найдено сигналов: {len(recent_signals)}")
                
                for i, signal in enumerate(recent_signals[:5]):
                    print(f"{i+1}. {signal['trading_pair']} {signal['direction']} Entry:{signal['entry_price']} Target:{signal['target_price']}")
                
            else:
                print("❌ Сигналы не найдены")
                print("Возможные причины:")
                print("- Канал не содержит сигналов в нужном формате")
                print("- Нет доступа к каналу")
                print("- Сигналы слишком старые")
        
        else:
            print("❌ Не удалось подключиться к Telegram")
    
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    
    finally:
        await scraper.stop()

if __name__ == "__main__":
    asyncio.run(get_last_signal())
