#!/usr/bin/env python3
"""
Полный отчет по сигналам в БД
"""
import sqlite3
import json
from datetime import datetime
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'workers'))
from price_utils import fetch_prices_usd

DB_PATH = 'workers/signals.db'

def generate_full_report():
    """Генерирует полный отчет по всем сигналам"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    print("=" * 80)
    print("📊 ПОЛНЫЙ ОТЧЕТ ПО СИГНАЛАМ")
    print("=" * 80)
    
    # Общая статистика
    cur.execute("SELECT COUNT(*) as total FROM signals")
    total_signals = cur.fetchone()['total']
    
    cur.execute("SELECT COUNT(*) as valid FROM signals WHERE is_valid = 1")
    valid_signals = cur.fetchone()['valid']
    
    cur.execute("SELECT COUNT(*) as verified FROM signals WHERE signal_quality = 'verified'")
    verified_signals = cur.fetchone()['verified']
    
    print(f"📈 ОБЩАЯ СТАТИСТИКА:")
    print(f"   Всего сигналов: {total_signals}")
    print(f"   Валидных: {valid_signals}")
    print(f"   Проверенных: {verified_signals}")
    print()
    
    # Статистика по каналам
    print("📺 СТАТИСТИКА ПО КАНАЛАМ:")
    cur.execute("""
        SELECT channel, COUNT(*) as cnt, 
               AVG(real_confidence) as avg_conf,
               SUM(CASE WHEN is_valid = 1 THEN 1 ELSE 0 END) as valid_cnt
        FROM signals 
        GROUP BY channel 
        ORDER BY cnt DESC
    """)
    
    for row in cur.fetchall():
        print(f"   {row['channel']}: {row['cnt']} сигналов, "
              f"средняя уверенность: {row['avg_conf']:.1f}%, "
              f"валидных: {row['valid_cnt']}")
    print()
    
    # Анализ цен
    print("💰 АНАЛИЗ ЦЕН:")
    
    # Получаем текущие цены
    cur.execute("SELECT DISTINCT asset FROM signals WHERE asset != 'UNKNOWN'")
    assets = [row['asset'] for row in cur.fetchall()]
    current_prices = fetch_prices_usd(assets)
    
    print("   Текущие рыночные цены:")
    for asset, price in current_prices.items():
        print(f"     {asset}: ${price:,.2f}")
    print()
    
    # Аномальные сигналы
    print("🚨 АНОМАЛЬНЫЕ СИГНАЛЫ:")
    cur.execute("""
        SELECT asset, entry_price, target_price, stop_loss, channel, 
               real_confidence, signal_quality, is_valid
        FROM signals 
        WHERE entry_price IS NOT NULL 
        AND asset IN ('BTC', 'bitcoin', 'ETH', 'ethereum')
        ORDER BY entry_price ASC
    """)
    
    anomalies = []
    for signal in cur.fetchall():
        asset = signal['asset'].upper()
        entry = signal['entry_price']
        
        if asset in ['BTC', 'BITCOIN'] and entry < 1000:
            anomalies.append(signal)
        elif asset in ['ETH', 'ETHEREUM'] and entry < 100:
            anomalies.append(signal)
    
    for signal in anomalies[:10]:  # Показываем топ-10 аномалий
        print(f"     {signal['asset']} @ ${signal['entry_price']} -> ${signal['target_price']} "
              f"| {signal['channel']} | conf: {signal['real_confidence']}%")
    
    if len(anomalies) > 10:
        print(f"     ... и еще {len(anomalies) - 10} аномальных сигналов")
    print()
    
    # Качество извлечения
    print("🔍 КАЧЕСТВО ИЗВЛЕЧЕНИЯ:")
    cur.execute("""
        SELECT signal_quality, COUNT(*) as cnt
        FROM signals 
        GROUP BY signal_quality
    """)
    
    for row in cur.fetchall():
        print(f"   {row['signal_quality']}: {row['cnt']} сигналов")
    print()
    
    # Направления
    print("📈 НАПРАВЛЕНИЯ:")
    cur.execute("""
        SELECT direction, COUNT(*) as cnt
        FROM signals 
        GROUP BY direction
    """)
    
    for row in cur.fetchall():
        print(f"   {row['direction']}: {row['cnt']} сигналов")
    print()
    
    # Временной анализ
    print("⏰ ВРЕМЕННОЙ АНАЛИЗ:")
    cur.execute("""
        SELECT timestamp, COUNT(*) as cnt
        FROM signals 
        WHERE timestamp IS NOT NULL
        GROUP BY DATE(timestamp)
        ORDER BY DATE(timestamp) DESC
        LIMIT 5
    """)
    
    for row in cur.fetchall():
        print(f"   {row['timestamp'][:10]}: {row['cnt']} сигналов")
    print()
    
    # Рекомендации
    print("💡 РЕКОМЕНДАЦИИ:")
    print("   1. Очистить БД от аномальных сигналов")
    print("   2. Улучшить фильтрацию цен в EnhancedPriceExtractor")
    print("   3. Добавить проверку на минимальные цены для основных активов")
    print("   4. Установить лимиты: BTC >= $10,000, ETH >= $1,000")
    print("   5. Пересобрать данные с более строгими фильтрами")
    
    conn.close()

if __name__ == '__main__':
    generate_full_report()
