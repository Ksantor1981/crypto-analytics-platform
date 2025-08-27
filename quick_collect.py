#!/usr/bin/env python3
"""
Быстрый сбор РЕАЛЬНЫХ данных из Telegram
"""
import os
import asyncio
from pathlib import Path

def check_telegram_api():
    """Проверяет настройку Telegram API"""
    api_id = os.getenv('TELEGRAM_API_ID')
    api_hash = os.getenv('TELEGRAM_API_HASH')
    phone = os.getenv('TELEGRAM_PHONE')
    
    if not all([api_id, api_hash, phone]):
        print("❌ Telegram API не настроен!")
        print("Запустите: python setup_telegram.py")
        return False
    
    print("✅ Telegram API настроен")
    return True

async def collect_telegram_data():
    """Сбор данных из Telegram"""
    try:
        from workers.real_data_collector import RealDataCollector
        
        print("📡 Сбор РЕАЛЬНЫХ данных из Telegram...")
        collector = RealDataCollector()
        
        signals_count = await collector.collect_from_telegram()
        
        print(f"✅ Собрано {signals_count} РЕАЛЬНЫХ сигналов")
        return signals_count
        
    except ImportError:
        print("❌ Telethon не установлен!")
        print("Установите: pip install telethon")
        return 0
    except Exception as e:
        print(f"❌ Ошибка сбора: {e}")
        return 0

def show_statistics():
    """Показывает статистику"""
    try:
        import sqlite3
        
        conn = sqlite3.connect('workers/signals.db')
        cur = conn.cursor()
        
        # Общая статистика
        cur.execute("SELECT COUNT(*) FROM signals")
        total = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM signals WHERE signal_type = 'telegram_real'")
        real = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM signals WHERE signal_type = 'real_demo'")
        demo = cur.fetchone()[0]
        
        # Статистика по каналам
        cur.execute("""
            SELECT channel, COUNT(*) as count 
            FROM signals 
            WHERE signal_type = 'telegram_real'
            GROUP BY channel 
            ORDER BY count DESC
        """)
        channels = cur.fetchall()
        
        conn.close()
        
        print(f"\n📊 Статистика:")
        print(f"   • Всего сигналов: {total}")
        print(f"   • РЕАЛЬНЫХ из Telegram: {real}")
        print(f"   • Демо сигналов: {demo}")
        
        if channels:
            print(f"\n🏆 Топ каналов:")
            for channel, count in channels[:5]:
                print(f"   • {channel}: {count} сигналов")
        
    except Exception as e:
        print(f"❌ Ошибка статистики: {e}")

async def main():
    """Основная функция"""
    print("🚀 Быстрый сбор РЕАЛЬНЫХ данных")
    print("=" * 40)
    
    if not check_telegram_api():
        return
    
    # Собираем данные
    signals = await collect_telegram_data()
    
    if signals > 0:
        print(f"\n🎉 Успешно собрано {signals} РЕАЛЬНЫХ сигналов!")
        show_statistics()
        print("\n✅ Теперь запустите дашборд: python start_dashboard.py")
    else:
        print("\n❌ Не удалось собрать данные")

if __name__ == '__main__':
    asyncio.run(main())
