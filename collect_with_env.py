#!/usr/bin/env python3
"""
Сбор РЕАЛЬНЫХ данных с загрузкой из .env файла
"""
import os
import asyncio
from pathlib import Path

def load_env_file():
    """Загружает данные из .env файла"""
    env_path = Path('.env')
    if not env_path.exists():
        print("❌ Файл .env не найден")
        return False
    
    print("📁 Загрузка данных из .env файла...")
    
    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value
    
    print("✅ Данные загружены из .env")
    return True

async def collect_real_data():
    """Сбор РЕАЛЬНЫХ данных"""
    try:
        # Проверяем данные
        api_id = os.getenv('TELEGRAM_API_ID')
        api_hash = os.getenv('TELEGRAM_API_HASH')
        phone = os.getenv('TELEGRAM_PHONE')
        
        if not phone:
            print("📱 Номер телефона не найден в .env")
            phone = input("Введите номер телефона (с кодом страны, например +7): ").strip()
            os.environ['TELEGRAM_PHONE'] = phone
        
        if not all([api_id, api_hash, phone]):
            print("❌ Не все данные Telegram API настроены")
            return 0
        
        print(f"🔍 Используемые данные:")
        print(f"   API_ID: {api_id}")
        print(f"   API_HASH: {api_hash[:10]}...")
        print(f"   PHONE: {phone}")
        
        # Импортируем и запускаем сбор
        try:
            from workers.real_data_collector import RealDataCollector
            print("✅ RealDataCollector импортирован")
        except ImportError as e:
            print(f"❌ Ошибка импорта RealDataCollector: {e}")
            return 0
        
        print("\n📡 Запуск сбора РЕАЛЬНЫХ данных...")
        collector = RealDataCollector()
        
        # Собираем из Telegram
        telegram_signals = await collector.collect_from_telegram()
        
        print(f"✅ Собрано {telegram_signals} РЕАЛЬНЫХ сигналов из Telegram")
        
        # Показываем статистику
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
        
        return telegram_signals
        
    except Exception as e:
        print(f"❌ Ошибка сбора данных: {e}")
        return 0

async def main():
    """Основная функция"""
    print("🚀 Сбор РЕАЛЬНЫХ данных из Telegram")
    print("=" * 50)
    
    if not load_env_file():
        return
    
    # Собираем данные
    signals = await collect_real_data()
    
    if signals > 0:
        print(f"\n🎉 Успешно собрано {signals} РЕАЛЬНЫХ сигналов!")
        print("✅ Теперь запустите дашборд: python start_dashboard.py")
    else:
        print("\n❌ Не удалось собрать данные")

if __name__ == '__main__':
    asyncio.run(main())
