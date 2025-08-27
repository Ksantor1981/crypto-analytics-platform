#!/usr/bin/env python3
"""
Создание реалистичных сигналов с вариациями и неполными данными
"""

import json
import sqlite3
import sys
import os
from datetime import datetime, timedelta
import random
sys.path.append('workers')

from enhanced_price_extractor import EnhancedPriceExtractor

def create_realistic_signals():
    """Создает реалистичные сигналы с вариациями"""
    
    print("🎯 Создаем реалистичные сигналы с вариациями...")
    
    # Подключаемся к базе данных
    conn = sqlite3.connect('workers/signals.db')
    cursor = conn.cursor()
    
    # Очищаем старые данные
    print("🗑️ Очищаем старые данные...")
    cursor.execute("DELETE FROM signals")
    cursor.execute("DELETE FROM channel_stats")
    
    # Создаем экстрактор
    extractor = EnhancedPriceExtractor()
    
    # Реалистичные сообщения с вариациями
    realistic_messages = [
        # Высокое качество сигналы
        {
            "text": "BTC/USDT: Strong bullish momentum! Long entry at 110000, target 115000, stop loss at 108000. Volume spike confirmed.",
            "channel": "cryptosignals",
            "hours_ago": 1,
            "confidence_boost": 15
        },
        {
            "text": "ETH/USDT: Breakout confirmed! Long entry at 3500, target 3700, stop loss at 3430. RSI bullish divergence.",
            "channel": "BinanceKillers_Free",
            "hours_ago": 2,
            "confidence_boost": 10
        },
        # Среднее качество сигналы
        {
            "text": "ADA/USDT: Support test at 0.45. Long entry at 0.46, target 0.52. Stop loss not specified.",
            "channel": "CryptoCapoTG",
            "hours_ago": 3,
            "confidence_boost": 0
        },
        {
            "text": "SOL/USDT: Resistance breakout attempt. Long entry at 95, target 105. No stop loss mentioned.",
            "channel": "binance_signals",
            "hours_ago": 4,
            "confidence_boost": -5
        },
        # Низкое качество сигналы
        {
            "text": "BTC/USDT: Might go up or down. Entry around 109500. Target unclear.",
            "channel": "bitcoin_signals",
            "hours_ago": 5,
            "confidence_boost": -20
        },
        {
            "text": "DOT/USDT: Consolidation pattern. Long entry at 5.2, target 5.8. Weak signal.",
            "channel": "CryptoSignalsPro",
            "hours_ago": 6,
            "confidence_boost": -10
        },
        # Сигналы без некоторых данных
        {
            "text": "LINK/USDT: Bearish flag pattern. Short entry at 12.5, target 11.5. Stop loss at 13.0.",
            "channel": "TradingViewAlerts",
            "hours_ago": 7,
            "confidence_boost": 5
        },
        {
            "text": "MATIC/USDT: Bullish pennant. Long entry at 0.65, target 0.75. Breakout imminent.",
            "channel": "CoinbaseSignals",
            "hours_ago": 8,
            "confidence_boost": 8
        },
        # Сигналы с ошибками
        {
            "text": "AVAX/USDT: Double top formation. Short entry at 28, target 25. Reversal pattern.",
            "channel": "cryptosignals",
            "hours_ago": 9,
            "confidence_boost": -15
        },
        {
            "text": "ETH SHORT @ 3480, TP: 3350, SL: 3520. Bearish divergence on 4H.",
            "channel": "BinanceKillers_Free",
            "hours_ago": 10,
            "confidence_boost": 12
        },
        # Дополнительные вариации
        {
            "text": "BTC LONG @ 110500, TP: 113000, SL: 109000. Bullish engulfing on daily.",
            "channel": "CryptoCapoTG",
            "hours_ago": 11,
            "confidence_boost": 18
        },
        {
            "text": "ADA SHORT @ 0.47, TP: 0.42, SL: 0.49. Head and shoulders pattern.",
            "channel": "binance_signals",
            "hours_ago": 12,
            "confidence_boost": 7
        },
        {
            "text": "SOL LONG @ 96, TP: 108, SL: 93. Ascending triangle breakout.",
            "channel": "bitcoin_signals",
            "hours_ago": 13,
            "confidence_boost": 14
        },
        {
            "text": "DOT SHORT @ 5.4, TP: 5.0, SL: 5.6. Descending channel.",
            "channel": "CryptoSignalsPro",
            "hours_ago": 14,
            "confidence_boost": 3
        },
        {
            "text": "LINK LONG @ 12.0, TP: 13.5, SL: 11.5. Bull flag pattern.",
            "channel": "TradingViewAlerts",
            "hours_ago": 15,
            "confidence_boost": 9
        },
        {
            "text": "MATIC SHORT @ 0.68, TP: 0.62, SL: 0.71. Bearish wedge.",
            "channel": "CoinbaseSignals",
            "hours_ago": 16,
            "confidence_boost": -8
        },
        {
            "text": "AVAX LONG @ 26, TP: 30, SL: 25. Cup and handle formation.",
            "channel": "cryptosignals",
            "hours_ago": 17,
            "confidence_boost": 11
        },
        {
            "text": "BTC/USDT: Key level test. Long entry at 110200, target 112000. Stop loss not clear.",
            "channel": "BinanceKillers_Free",
            "hours_ago": 18,
            "confidence_boost": -5
        },
        {
            "text": "ETH/USDT: Support bounce. Long entry at 3450, target 3600, stop loss at 3400. RSI oversold.",
            "channel": "CryptoCapoTG",
            "hours_ago": 19,
            "confidence_boost": 6
        },
        {
            "text": "ADA/USDT: Resistance test. Short entry at 0.48, target 0.43. MACD bearish.",
            "channel": "binance_signals",
            "hours_ago": 20,
            "confidence_boost": -12
        },
        {
            "text": "SOL/USDT: Breakout retest. Long entry at 94, target 102, stop loss at 91. Strong momentum.",
            "channel": "bitcoin_signals",
            "hours_ago": 21,
            "confidence_boost": 16
        },
        {
            "text": "DOT/USDT: Accumulation zone. Long entry at 5.1, target 5.9. Low volume.",
            "channel": "CryptoSignalsPro",
            "hours_ago": 22,
            "confidence_boost": -3
        },
        {
            "text": "LINK/USDT: Distribution phase. Short entry at 12.8, target 11.8, stop loss at 13.3. High volume.",
            "channel": "TradingViewAlerts",
            "hours_ago": 23,
            "confidence_boost": 4
        },
        {
            "text": "MATIC/USDT: Bullish continuation. Long entry at 0.64, target 0.74, stop loss at 0.61. Trend intact.",
            "channel": "CoinbaseSignals",
            "hours_ago": 24,
            "confidence_boost": 13
        }
    ]
    
    signals = []
    
    print(f"📊 Обрабатываем {len(realistic_messages)} реалистичных сообщений...")
    
    for i, message_data in enumerate(realistic_messages):
        try:
            text = message_data["text"]
            channel = message_data["channel"]
            hours_ago = message_data["hours_ago"]
            confidence_boost = message_data["confidence_boost"]
            
            # Создаем правильный timestamp
            timestamp = datetime.now() - timedelta(hours=hours_ago)
            
            # Создаем сигнал с помощью экстрактора
            signal = extractor.extract_signal(text, channel, f"msg_{i}")
            
            # Обновляем ID для уникальности
            signal['id'] = f"{signal['asset']}_{int(timestamp.timestamp())}_{i}"
            
            # Обновляем timestamp
            signal['timestamp'] = timestamp.isoformat()
            
            # Добавляем реалистичные вариации уверенности
            base_confidence = signal['real_confidence']
            final_confidence = max(45.0, min(95.0, base_confidence + confidence_boost + random.uniform(-3, 3)))
            signal['real_confidence'] = final_confidence
            signal['calculated_confidence'] = final_confidence
            
            # Добавляем случайное плечо
            signal['leverage'] = random.choice([1, 2, 3, 5, 10])
            
            # Добавляем случайный таймфрейм
            timeframes = ['1H', '4H', '1D', '1W']
            signal['timeframe'] = random.choice(timeframes)
            
            # Иногда убираем некоторые данные для реалистичности
            if random.random() < 0.2:  # 20% сигналов без stop loss
                signal['stop_loss'] = None
            if random.random() < 0.1:  # 10% сигналов без target
                signal['target_price'] = None
            
            signals.append(signal)
            print(f"✅ Создан сигнал: {signal['asset']} {signal['direction']} @ {signal['entry_price']} -> {signal['target_price']} (SL: {signal['stop_loss']}) | Confidence: {signal['real_confidence']:.1f}%")
            
        except Exception as e:
            print(f"❌ Ошибка создания сигнала {i}: {e}")
    
    # Сохраняем сигналы в базу данных
    print("💾 Сохраняем сигналы в базу данных...")
    
    for signal in signals:
        try:
            cursor.execute("""
                INSERT INTO signals (
                    id, asset, direction, entry_price, target_price, stop_loss,
                    leverage, timeframe, signal_quality, real_confidence,
                    calculated_confidence, channel, message_id, original_text,
                    cleaned_text, signal_type, timestamp, extraction_time,
                    bybit_available, is_valid, validation_errors,
                    risk_reward_ratio, potential_profit, potential_loss
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                signal['id'],
                signal['asset'],
                signal['direction'],
                signal['entry_price'],
                signal['target_price'],
                signal['stop_loss'],
                signal['leverage'],
                signal['timeframe'],
                signal['signal_quality'],
                signal['real_confidence'],
                signal['calculated_confidence'],
                signal['channel'],
                signal['message_id'],
                signal['original_text'],
                signal['cleaned_text'],
                signal['signal_type'],
                signal['timestamp'],
                signal['extraction_time'],
                signal['bybit_available'],
                signal['is_valid'],
                json.dumps(signal['validation_errors']),
                signal['risk_reward_ratio'],
                signal['potential_profit'],
                signal['potential_loss']
            ))
        except Exception as e:
            print(f"❌ Ошибка сохранения сигнала: {e}")
    
    # Создаем статистику каналов
    print("📈 Создаем статистику каналов...")
    channel_stats = {}
    for signal in signals:
        channel = signal['channel']
        if channel not in channel_stats:
            channel_stats[channel] = {'total': 0, 'successful': 0}
        channel_stats[channel]['total'] += 1
        if signal['real_confidence'] > 70:
            channel_stats[channel]['successful'] += 1
    
    # Сохраняем статистику каналов
    for channel, stats in channel_stats.items():
        accuracy = (stats['successful'] / stats['total']) * 100 if stats['total'] > 0 else 0
        cursor.execute("""
            INSERT INTO channel_stats (channel_name, total_signals, successful_signals, accuracy, last_updated)
            VALUES (?, ?, ?, ?, ?)
        """, (channel, stats['total'], stats['successful'], accuracy, datetime.now().isoformat()))
    
    # Сохраняем изменения
    conn.commit()
    
    # Проверяем количество загруженных сигналов
    cursor.execute("SELECT COUNT(*) FROM signals")
    count = cursor.fetchone()[0]
    print(f"📊 Всего сигналов в базе: {count}")
    
    # Проверяем вариации confidence
    cursor.execute("SELECT MIN(real_confidence), MAX(real_confidence), AVG(real_confidence) FROM signals")
    min_conf, max_conf, avg_conf = cursor.fetchone()
    print(f"📈 Вариации confidence:")
    print(f"   Минимум: {min_conf:.1f}%")
    print(f"   Максимум: {max_conf:.1f}%")
    print(f"   Среднее: {avg_conf:.1f}%")
    
    # Проверяем сигналы с ценами
    cursor.execute("SELECT COUNT(*), SUM(CASE WHEN entry_price IS NOT NULL THEN 1 ELSE 0 END), SUM(CASE WHEN target_price IS NOT NULL THEN 1 ELSE 0 END), SUM(CASE WHEN stop_loss IS NOT NULL THEN 1 ELSE 0 END) FROM signals")
    total, with_entry, with_target, with_stop = cursor.fetchone()
    print(f"📈 Статистика цен:")
    print(f"   Всего сигналов: {total}")
    print(f"   С entry price: {with_entry}")
    print(f"   С target price: {with_target}")
    print(f"   С stop loss: {with_stop}")
    
    conn.close()
    
    print("✅ Реалистичные сигналы с вариациями созданы!")

if __name__ == "__main__":
    create_realistic_signals()
