#!/usr/bin/env python3
"""
Система отслеживания результатов сигналов и расчета реальной точности
"""
import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from price_utils import fetch_prices_usd

DB_PATH = 'workers/signals.db'

def track_signal_results():
    """Отслеживает результаты сигналов и обновляет статистику"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    # Добавляем недостающие колонки
    try:
        cur.execute("ALTER TABLE signals ADD COLUMN signal_result TEXT")
        cur.execute("ALTER TABLE signals ADD COLUMN result_checked_at TEXT")
    except sqlite3.OperationalError:
        pass  # Колонки уже существуют
    
    conn.commit()
    
    # Получаем все сигналы с уровнями
    cur.execute("""
        SELECT id, asset, direction, entry_price, target_price, stop_loss, 
               channel, timestamp, is_valid, signal_quality, real_confidence
        FROM signals 
        WHERE entry_price IS NOT NULL 
        AND (target_price IS NOT NULL OR stop_loss IS NOT NULL)
        AND asset != 'UNKNOWN'
        ORDER BY timestamp DESC
    """)
    
    signals = cur.fetchall()
    print(f"📊 Анализируем {len(signals)} сигналов с уровнями...")
    
    # Группируем по каналам
    channel_signals = {}
    for signal in signals:
        channel = signal['channel']
        if channel not in channel_signals:
            channel_signals[channel] = []
        channel_signals[channel].append(signal)
    
    # Анализируем каждый канал
    for channel, channel_sigs in channel_signals.items():
        if len(channel_sigs) < 2:
            print(f"⚠️ {channel}: недостаточно сигналов ({len(channel_sigs)})")
            continue
            
        print(f"🔍 Анализируем {channel}: {len(channel_sigs)} сигналов")
        
        # Получаем текущие цены для активов
        assets = list(set([s['asset'] for s in channel_sigs]))
        current_prices = fetch_prices_usd(assets)
        
        successful = 0
        total_analyzed = 0
        
        for signal in channel_sigs:
            result = analyze_signal_result(signal, current_prices)
            if result is not None:
                total_analyzed += 1
                if result:
                    successful += 1
                    
                # Обновляем результат в БД
                cur.execute("""
                    UPDATE signals 
                    SET signal_result = ?, result_checked_at = ?
                    WHERE id = ?
                """, (json.dumps(result), datetime.now().isoformat(), signal['id']))
        
        if total_analyzed >= 2:
            accuracy = (successful / total_analyzed) * 100.0
            print(f"✅ {channel}: {successful}/{total_analyzed} успешных ({accuracy:.1f}%)")
            
            # Обновляем confidence для всех сигналов канала
            cur.execute("""
                UPDATE signals 
                SET real_confidence = ?, 
                    signal_quality = 'verified',
                    is_valid = 1
                WHERE channel = ?
            """, (accuracy, channel))
        else:
            print(f"❌ {channel}: недостаточно проанализированных сигналов")
            # Помечаем как непроверенные
            cur.execute("""
                UPDATE signals 
                SET signal_quality = 'unverified',
                    is_valid = 0
                WHERE channel = ?
            """, (channel,))
    
    conn.commit()
    conn.close()
    print("✅ Анализ завершен")

def analyze_signal_result(signal: sqlite3.Row, current_prices: Dict[str, float]) -> bool:
    """Анализирует результат одного сигнала"""
    asset = signal['asset']
    direction = signal['direction']
    entry = signal['entry_price']
    target = signal['target_price']
    stop = signal['stop_loss']
    
    if asset not in current_prices:
        return None  # Не можем проверить
        
    current_price = current_prices[asset]
    
    # Проверяем, достиг ли сигнал цели или стопа
    if direction == 'LONG':
        if target and current_price >= target:
            return True  # Достигнута цель
        if stop and current_price <= stop:
            return False  # Сработал стоп
    elif direction == 'SHORT':
        if target and current_price <= target:
            return True  # Достигнута цель
        if stop and current_price >= stop:
            return False  # Сработал стоп
    
    # Если сигнал еще активен (не достиг ни цели, ни стопа)
    return None

def get_verified_channels() -> List[str]:
    """Возвращает список каналов с подтвержденной статистикой"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    cur.execute("""
        SELECT channel, COUNT(*) as cnt, real_confidence
        FROM signals 
        WHERE signal_quality = 'verified' 
        AND real_confidence IS NOT NULL
        GROUP BY channel
        HAVING cnt >= 2
        ORDER BY real_confidence DESC
    """)
    
    channels = [row[0] for row in cur.fetchall()]
    conn.close()
    return channels

if __name__ == '__main__':
    track_signal_results()
