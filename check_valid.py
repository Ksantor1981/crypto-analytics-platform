#!/usr/bin/env python3
"""
Просмотр валидных сигналов
"""
import sqlite3

DB_PATH = 'workers/signals.db'

def check_valid_signals():
    """Показывает все валидные сигналы"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    cur.execute("""
        SELECT asset, direction, entry_price, target_price, stop_loss, 
               channel, real_confidence, signal_quality, is_valid
        FROM signals 
        WHERE is_valid = 1
        ORDER BY channel, asset
    """)
    
    signals = cur.fetchall()
    
    print(f"✅ ВАЛИДНЫЕ СИГНАЛЫ ({len(signals)}):")
    print("=" * 80)
    
    for signal in signals:
        print(f"   {signal['asset']} {signal['direction']} @ ${signal['entry_price']} → ${signal['target_price']} | "
              f"{signal['channel']} | conf: {signal['real_confidence']}%")
    
    conn.close()

if __name__ == '__main__':
    check_valid_signals()
