#!/usr/bin/env python3
import sqlite3
from pathlib import Path

DB_PATH = 'workers/signals.db'

if not Path(DB_PATH).exists():
    print(f"❌ База данных не найдена: {DB_PATH}")
    exit(1)

try:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # Проверяем таблицы
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cur.fetchall()
    print(f"📋 Таблицы в БД: {[t[0] for t in tables]}")
    
    # Проверяем сигналы
    if 'signals' in [t[0] for t in tables]:
        cur.execute("SELECT COUNT(*) FROM signals")
        signals_count = cur.fetchone()[0]
        print(f"📊 Сигналов в БД: {signals_count}")
        
        if signals_count > 0:
            cur.execute("SELECT asset, direction, entry_price, target_price, channel FROM signals LIMIT 3")
            signals = cur.fetchall()
            print("🔍 Примеры сигналов:")
            for signal in signals:
                print(f"   {signal[0]} {signal[1]} @ ${signal[2]} -> ${signal[3]} | {signal[4]}")
    
    # Проверяем статистику каналов
    if 'channel_stats' in [t[0] for t in tables]:
        cur.execute("SELECT COUNT(*) FROM channel_stats")
        channels_count = cur.fetchone()[0]
        print(f"📈 Каналов в статистике: {channels_count}")
        
        if channels_count > 0:
            cur.execute("SELECT channel, win_rate, total_signals FROM channel_stats LIMIT 3")
            channels = cur.fetchall()
            print("🏆 Примеры каналов:")
            for channel in channels:
                print(f"   {channel[0]}: {channel[1]}% ({channel[2]} сигналов)")
    
    conn.close()
    print("✅ Проверка завершена")
    
except Exception as e:
    print(f"❌ Ошибка проверки БД: {e}")
