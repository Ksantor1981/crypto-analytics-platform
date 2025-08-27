import sqlite3
import json

def check_database():
    try:
        conn = sqlite3.connect('workers/signals.db')
        cursor = conn.cursor()
        
        # Проверяем количество сигналов
        cursor.execute('SELECT COUNT(*) FROM signals')
        signal_count = cursor.fetchone()[0]
        print(f"📊 Количество сигналов в базе: {signal_count}")
        
        # Проверяем структуру таблицы
        cursor.execute("PRAGMA table_info(signals)")
        columns = cursor.fetchall()
        print(f"📋 Структура таблицы signals ({len(columns)} колонок):")
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
        
        # Показываем первые 3 сигнала
        if signal_count > 0:
            cursor.execute('SELECT id, channel, asset, entry_price, target_price, stop_loss, direction, real_confidence, timestamp FROM signals LIMIT 3')
            signals = cursor.fetchall()
            print(f"\n🔍 Первые 3 сигнала:")
            for i, signal in enumerate(signals, 1):
                print(f"  {i}. ID: {signal[0]}, Канал: {signal[1]}, Актив: {signal[2]}")
                print(f"     Entry: {signal[3]}, Target: {signal[4]}, Stop: {signal[5]}")
                print(f"     Направление: {signal[6]}, Уверенность: {signal[7]}")
                print(f"     Дата: {signal[8]}")
                print()
        
        # Проверяем каналы
        cursor.execute('SELECT COUNT(*) FROM channel_stats')
        channel_count = cursor.fetchone()[0]
        print(f"📺 Количество каналов: {channel_count}")
        
        if channel_count > 0:
            cursor.execute('SELECT channel, total_signals, accuracy, avg_profit FROM channel_stats LIMIT 5')
            channels = cursor.fetchall()
            print(f"📊 Топ 5 каналов:")
            for channel in channels:
                print(f"  - {channel[0]}: {channel[1]} сигналов, точность {channel[2]}%, средняя прибыль {channel[3]}%")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при проверке базы данных: {e}")
        return False

if __name__ == "__main__":
    check_database()
