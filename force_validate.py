#!/usr/bin/env python3
"""
Принудительная валидация всех сигналов в БД
"""
import sqlite3
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'workers'))
from enhanced_price_extractor import EnhancedPriceExtractor

DB_PATH = 'workers/signals.db'

def force_validate_all():
    """Принудительно валидирует все сигналы"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    extractor = EnhancedPriceExtractor()
    
    # Получаем все сигналы
    cur.execute("SELECT * FROM signals")
    signals = cur.fetchall()
    
    print(f"🔍 Валидируем {len(signals)} сигналов...")
    
    validated = 0
    invalidated = 0
    
    for signal in signals:
        asset = signal['asset']
        entry_price = signal['entry_price']
        target_price = signal['target_price']
        stop_loss = signal['stop_loss']
        
        # Проверяем валидность цен
        is_valid = extractor.validate_prices(asset, entry_price, target_price, stop_loss)
        
        # Обновляем в БД
        cur.execute("""
            UPDATE signals 
            SET is_valid = ?, signal_quality = ?
            WHERE id = ?
        """, (1 if is_valid else 0, 'verified' if is_valid else 'poor', signal['id']))
        
        if is_valid:
            validated += 1
        else:
            invalidated += 1
            print(f"❌ {asset} @ ${entry_price} -> ${target_price} | {signal['channel']}")
    
    conn.commit()
    conn.close()
    
    print(f"✅ Валидировано: {validated}")
    print(f"❌ Отклонено: {invalidated}")

if __name__ == '__main__':
    force_validate_all()
