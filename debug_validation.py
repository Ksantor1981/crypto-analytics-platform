#!/usr/bin/env python3
"""
Отладка валидации
"""
import sqlite3
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'workers'))
from enhanced_price_extractor import EnhancedPriceExtractor

DB_PATH = 'workers/signals.db'

def debug_validation():
    """Отлаживает валидацию сигналов"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    extractor = EnhancedPriceExtractor()
    
    # Получаем валидные сигналы
    cur.execute("SELECT * FROM signals WHERE is_valid = 1")
    signals = cur.fetchall()
    
    print(f"🔍 ОТЛАДКА ВАЛИДАЦИИ ({len(signals)} сигналов):")
    print("=" * 80)
    
    for signal in signals:
        asset = signal['asset']
        entry_price = signal['entry_price']
        target_price = signal['target_price']
        stop_loss = signal['stop_loss']
        
        print(f"\n📊 Сигнал: {asset} @ ${entry_price} → ${target_price}")
        
        # Проверяем каждый этап валидации
        is_valid = extractor.validate_prices(asset, entry_price, target_price, stop_loss)
        print(f"   validate_prices() = {is_valid}")
        
        # Проверяем отдельные условия
        if not entry_price:
            print("   ❌ entry_price is None/0")
        else:
            print(f"   ✅ entry_price = {entry_price}")
            
        if target_price:
            if target_price <= 0:
                print(f"   ❌ target_price <= 0: {target_price}")
            elif target_price == entry_price:
                print(f"   ❌ target_price == entry_price: {target_price}")
            else:
                print(f"   ✅ target_price = {target_price}")
        
        # Проверяем лимиты цен
        asset_upper = asset.upper()
        price_limits = {
            'BTC': (10000, 200000), 'bitcoin': (10000, 200000),
            'ETH': (1000, 10000), 'ethereum': (1000, 10000),
            'SOL': (50, 500), 'solana': (50, 500),
            'ADA': (0.1, 10), 'cardano': (0.1, 10),
            'LINK': (5, 100), 'chainlink': (5, 100),
            'MATIC': (0.1, 5), 'polygon': (0.1, 5)
        }
        
        price_limit = price_limits.get(asset_upper, (0.01, 1000000))
        min_price, max_price = price_limit
        
        if entry_price < min_price or entry_price > max_price:
            print(f"   ❌ entry_price {entry_price} вне лимитов [{min_price}, {max_price}]")
        else:
            print(f"   ✅ entry_price {entry_price} в лимитах [{min_price}, {max_price}]")
    
    conn.close()

if __name__ == '__main__':
    debug_validation()
