#!/usr/bin/env python3
"""
Запуск парсинга реальных сигналов
"""

import sys
import os
import asyncio
import logging
from datetime import datetime

# Добавляем пути для импорта
sys.path.append(os.path.join(os.path.dirname(__file__), 'workers'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

async def test_telegram_parsing():
    """Тест парсинга Telegram сигналов"""
    print("🔍 Тестирование парсинга Telegram сигналов...")
    
    try:
        # Импортируем необходимые модули
        from workers.telegram.telegram_client import TelegramSignalCollector
        from workers.telegram.signal_processor import TelegramSignalProcessor
        
        # Создаем коллектор
        collector = TelegramSignalCollector(use_real_config=True)
        processor = TelegramSignalProcessor()
        
        print(f"✅ Telegram клиент создан")
        print(f"   API ID: {collector.api_id}")
        print(f"   Каналов: {len(collector.channels)}")
        
        # Показываем конфигурацию каналов
        for i, channel in enumerate(collector.channels[:5], 1):
            print(f"   {i}. {channel['name']} (@{channel['username']})")
            print(f"      Категория: {channel['category']}")
            print(f"      Успешность: {channel['success_rate']:.1%}")
            print(f"      Сигналов/день: {channel['avg_signals_per_day']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка Telegram парсинга: {e}")
        return False

async def test_signal_processing():
    """Тест обработки сигналов"""
    print("\n🔍 Тестирование обработки сигналов...")
    
    try:
        from workers.telegram.signal_processor import TelegramSignalProcessor
        
        processor = TelegramSignalProcessor()
        
        # Тестовые сигналы
        test_signals = [
            {
                "text": "🚀 BTC/USDT LONG\nEntry: 117,500\nTarget 1: 120,000\nTarget 2: 122,500\nStop Loss: 115,000\nLeverage: 10x",
                "channel": "@cryptosignals",
                "timestamp": datetime.now()
            },
            {
                "text": "📉 ETH/USDT SHORT\nВход: 3,200\nЦель: 3,000\nСтоп: 3,300\nПлечо: 5x",
                "channel": "@binancesignals", 
                "timestamp": datetime.now()
            },
            {
                "text": "🔥 SOL/USDT BUY\nEntry Price: $100\nTake Profit: $110\nStop Loss: $95\nConfidence: HIGH",
                "channel": "@cryptotradingview",
                "timestamp": datetime.now()
            }
        ]
        
        for i, signal in enumerate(test_signals, 1):
            print(f"\n📊 Обработка сигнала #{i}:")
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
                
                # Сохраняем в базу данных
                try:
                    from backend.app.database import get_db
                    from backend.app.models.signal import Signal
                    from backend.app.models.channel import Channel
                    
                    db = next(get_db())
                    
                    # Создаем канал если не существует
                    channel = db.query(Channel).filter(Channel.url == signal['channel']).first()
                    if not channel:
                        channel = Channel(
                            name=signal['channel'].replace('@', ''),
                            platform="telegram",
                            url=signal['channel'],
                            category="crypto",
                            description=f"Telegram канал {signal['channel']}",
                            is_active=True
                        )
                        db.add(channel)
                        db.commit()
                        db.refresh(channel)
                    
                    # Создаем сигнал
                    new_signal = Signal(
                        channel_id=channel.id,
                        asset=parsed.get('asset', 'UNKNOWN'),
                        direction=parsed.get('direction', 'LONG'),
                        entry_price=parsed.get('entry_price', 0),
                        tp1_price=parsed.get('target_price'),
                        stop_loss=parsed.get('stop_loss'),
                        original_text=signal['text'],
                        message_timestamp=signal['timestamp'],
                        status='PENDING',
                        confidence_score=parsed.get('confidence', 0.5)
                    )
                    
                    db.add(new_signal)
                    db.commit()
                    
                    print(f"💾 Сигнал сохранен в БД (ID: {new_signal.id})")
                    
                except Exception as db_error:
                    print(f"❌ Ошибка сохранения в БД: {db_error}")
            else:
                print(f"❌ Сигнал не распознан")
                
    except Exception as e:
        print(f"❌ Ошибка обработки сигналов: {e}")

async def test_real_telegram_collection():
    """Тест реального сбора сигналов из Telegram"""
    print("\n🔍 Тестирование реального сбора сигналов...")
    
    try:
        from workers.telegram.real_telegram_collector import RealTelegramCollector
        
        collector = RealTelegramCollector()
        
        print("📡 Подключение к Telegram...")
        
        # Пытаемся собрать сигналы (в демо режиме)
        result = await collector.collect_signals_demo()
        
        if result['status'] == 'success':
            print(f"✅ Собрано сигналов: {result.get('total_signals', 0)}")
            print(f"   Обработано: {result.get('processed', 0)}")
            print(f"   Сохранено: {result.get('saved', 0)}")
            
            if result.get('signals'):
                print("\n📊 Примеры собранных сигналов:")
                for i, signal in enumerate(result['signals'][:3], 1):
                    print(f"   {i}. {signal.get('asset', 'N/A')} {signal.get('direction', 'N/A')}")
                    print(f"      Вход: ${signal.get('entry_price', 'N/A')}")
                    print(f"      Канал: {signal.get('channel', 'N/A')}")
        else:
            print(f"❌ Ошибка сбора: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Ошибка реального сбора: {e}")

async def main():
    """Основная функция"""
    print("🚀 ЗАПУСК ПАРСИНГА РЕАЛЬНЫХ СИГНАЛОВ")
    print("=" * 60)
    print(f"Время: {datetime.now()}")
    print("=" * 60)
    
    try:
        # Тестируем все компоненты
        telegram_ok = await test_telegram_parsing()
        await test_signal_processing()
        await test_real_telegram_collection()
        
        print("\n" + "=" * 60)
        print("✅ ПАРСИНГ ЗАВЕРШЕН!")
        
        if telegram_ok:
            print("🎯 Telegram парсинг: ГОТОВ")
        else:
            print("⚠️ Telegram парсинг: ТРЕБУЕТ НАСТРОЙКИ")
            
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
        print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
