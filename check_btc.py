#!/usr/bin/env python3
import sqlite3

conn = sqlite3.connect('workers/signals.db')
c = conn.cursor()

# Проверяем BTC сигналы
c.execute("SELECT asset, entry_price, target_price, is_valid, signal_quality, real_confidence FROM signals WHERE asset='bitcoin' OR asset='BTC' LIMIT 5")
print('BTC сигналы:')
for r in c.fetchall():
    print(f'{r[0]} @ {r[1]} -> {r[2]} | valid:{r[3]} quality:{r[4]} conf:{r[5]:.1f}%')

# Проверяем аномальные цены
c.execute("SELECT asset, entry_price, target_price, is_valid, signal_quality FROM signals WHERE entry_price < 100 AND (asset='BTC' OR asset='bitcoin')")
print('\nАномальные BTC цены:')
for r in c.fetchall():
    print(f'{r[0]} @ {r[1]} -> {r[2]} | valid:{r[3]} quality:{r[4]}')

conn.close()
