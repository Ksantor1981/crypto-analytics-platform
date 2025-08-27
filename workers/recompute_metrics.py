#!/usr/bin/env python3
import sqlite3
from datetime import datetime, timedelta
from typing import Dict
from price_utils import fetch_prices_usd

DB_PATH = 'workers/signals.db'
MIN_SIGNALS = 10
ANOMALY_FACTOR = 3.0  # entry не должен отличаться более чем в 3 раза от рынка


def recompute():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Текущие цены
    cur.execute("SELECT DISTINCT asset FROM signals WHERE asset IS NOT NULL")
    assets = [r[0] for r in cur.fetchall() if r[0] and r[0] != 'UNKNOWN']
    market = fetch_prices_usd(assets)

    # Историческая точность по каналам
    # success: если для LONG target > entry, для SHORT target < entry (грубая метрика)
    cur.execute("SELECT channel, COUNT(*) as cnt FROM signals GROUP BY channel")
    channel_counts = {r['channel']: r['cnt'] for r in cur.fetchall()}

    for channel, cnt in channel_counts.items():
        if cnt < MIN_SIGNALS:
            continue
        cur.execute("SELECT asset, direction, entry_price, target_price FROM signals WHERE channel=?", (channel,))
        rows = cur.fetchall()
        total = 0
        success = 0
        for r in rows:
            e = r['entry_price']; t = r['target_price']
            d = (r['direction'] or '').upper()
            if e is None or t is None:
                continue
            total += 1
            if d == 'SHORT' and t < e:
                success += 1
            if d == 'LONG' and t > e:
                success += 1
        if total >= MIN_SIGNALS:
            accuracy = (success / total) * 100.0
            # применяем к real_confidence всех сигналов канала
            cur.execute("UPDATE signals SET real_confidence=? WHERE channel=?", (accuracy, channel))

    # Валидация аномалий цен
    cur.execute("SELECT id, asset, entry_price FROM signals")
    for row in cur.fetchall():
        asset = (row['asset'] or '').upper()
        entry = row['entry_price']
        if not asset or not entry or asset not in market:
            continue
        m = market[asset]
        if m <= 0:
            continue
        ratio = max(entry, m) / min(entry, m)
        if ratio >= ANOMALY_FACTOR:
            # помечаем как невалидный
            cur.execute("UPDATE signals SET is_valid=0, signal_quality='poor' WHERE id=?", (row['id'],))

    conn.commit()
    conn.close()


if __name__ == '__main__':
    recompute()
