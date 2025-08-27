#!/usr/bin/env python3
"""
Скрипт для создания и инициализации базы данных сигналов
"""

import sqlite3
import os
from datetime import datetime

def create_database():
    """Создает базу данных и таблицы"""
    
    # Путь к базе данных
    db_path = "workers/signals.db"
    
    # Удаляем существующий файл, если он пустой
    if os.path.exists(db_path) and os.path.getsize(db_path) == 0:
        os.remove(db_path)
        print("Удален пустой файл базы данных")
    
    # Создаем соединение с базой данных
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Создаем таблицу сигналов
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS signals (
            id TEXT PRIMARY KEY,
            asset TEXT,
            direction TEXT,
            entry_price REAL,
            target_price REAL,
            stop_loss REAL,
            leverage INTEGER,
            timeframe TEXT,
            signal_quality TEXT,
            real_confidence REAL,
            calculated_confidence REAL,
            channel TEXT,
            message_id TEXT,
            original_text TEXT,
            cleaned_text TEXT,
            signal_type TEXT,
            timestamp TEXT,
            extraction_time TEXT,
            bybit_available BOOLEAN,
            is_valid BOOLEAN,
            validation_errors TEXT,
            risk_reward_ratio REAL,
            potential_profit REAL,
            potential_loss REAL
        )
    """)
    
    # Создаем таблицу результатов сигналов
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS signal_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            signal_id TEXT,
            actual_price REAL,
            profit_loss REAL,
            status TEXT,
            closed_at TEXT,
            FOREIGN KEY (signal_id) REFERENCES signals (id)
        )
    """)
    
    # Создаем таблицу статистики каналов
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS channel_stats (
            channel_name TEXT PRIMARY KEY,
            total_signals INTEGER,
            successful_signals INTEGER,
            accuracy REAL,
            last_updated TEXT
        )
    """)
    
    # Сохраняем изменения
    conn.commit()
    conn.close()
    
    print(f"База данных создана: {db_path}")
    print("Созданы таблицы:")
    print("- signals (сигналы)")
    print("- signal_results (результаты)")
    print("- channel_stats (статистика каналов)")

def add_sample_data():
    """Добавляет тестовые данные"""
    
    conn = sqlite3.connect("workers/signals.db")
    cursor = conn.cursor()
    
    # Добавляем тестовые сигналы
    sample_signals = [
        {
            'id': 'test_1',
            'asset': 'BTC/USDT',
            'direction': 'LONG',
            'entry_price': 50000.0,
            'target_price': 55000.0,
            'stop_loss': 48000.0,
            'leverage': 1,
            'timeframe': '4H',
            'signal_quality': 'GOOD',
            'real_confidence': 78.5,
            'calculated_confidence': 75.2,
            'channel': 'CryptoCapoTG',
            'message_id': 'msg_1',
            'original_text': 'BTC LONG @ 50000, Target: 55000, SL: 48000',
            'cleaned_text': 'BTC LONG @ 50000, Target: 55000, SL: 48000',
            'signal_type': 'structured',
            'timestamp': datetime.now().isoformat(),
            'extraction_time': datetime.now().isoformat(),
            'bybit_available': True,
            'is_valid': True,
            'validation_errors': '',
            'risk_reward_ratio': 2.5,
            'potential_profit': 5000.0,
            'potential_loss': 2000.0
        },
        {
            'id': 'test_2',
            'asset': 'ETH/USDT',
            'direction': 'SHORT',
            'entry_price': 3000.0,
            'target_price': 2800.0,
            'stop_loss': 3200.0,
            'leverage': 1,
            'timeframe': '1H',
            'signal_quality': 'EXCELLENT',
            'real_confidence': 85.0,
            'calculated_confidence': 82.1,
            'channel': 'BinanceKillers_Free',
            'message_id': 'msg_2',
            'original_text': 'ETH SHORT @ 3000, Target: 2800, SL: 3200',
            'cleaned_text': 'ETH SHORT @ 3000, Target: 2800, SL: 3200',
            'signal_type': 'structured',
            'timestamp': datetime.now().isoformat(),
            'extraction_time': datetime.now().isoformat(),
            'bybit_available': True,
            'is_valid': True,
            'validation_errors': '',
            'risk_reward_ratio': 2.0,
            'potential_profit': 200.0,
            'potential_loss': 200.0
        }
    ]
    
    for signal in sample_signals:
        cursor.execute("""
            INSERT OR REPLACE INTO signals (
                id, asset, direction, entry_price, target_price, stop_loss,
                leverage, timeframe, signal_quality, real_confidence, calculated_confidence,
                channel, message_id, original_text, cleaned_text, signal_type,
                timestamp, extraction_time, bybit_available, is_valid, validation_errors,
                risk_reward_ratio, potential_profit, potential_loss
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            signal['id'], signal['asset'], signal['direction'], signal['entry_price'],
            signal['target_price'], signal['stop_loss'], signal['leverage'], signal['timeframe'],
            signal['signal_quality'], signal['real_confidence'], signal['calculated_confidence'],
            signal['channel'], signal['message_id'], signal['original_text'], signal['cleaned_text'],
            signal['signal_type'], signal['timestamp'], signal['extraction_time'],
            signal['bybit_available'], signal['is_valid'], signal['validation_errors'],
            signal['risk_reward_ratio'], signal['potential_profit'], signal['potential_loss']
        ))
    
    # Добавляем статистику каналов
    sample_channels = [
        ('CryptoCapoTG', 20, 15, 75.0, datetime.now().isoformat()),
        ('BinanceKillers_Free', 25, 20, 80.0, datetime.now().isoformat()),
        ('cryptosignals', 18, 14, 77.8, datetime.now().isoformat()),
        ('binance_signals', 12, 9, 75.0, datetime.now().isoformat()),
        ('bitcoin_signals', 15, 11, 73.3, datetime.now().isoformat())
    ]
    
    for channel in sample_channels:
        cursor.execute("""
            INSERT OR REPLACE INTO channel_stats (
                channel_name, total_signals, successful_signals, accuracy, last_updated
            ) VALUES (?, ?, ?, ?, ?)
        """, channel)
    
    conn.commit()
    conn.close()
    
    print("Добавлены тестовые данные:")
    print(f"- {len(sample_signals)} сигналов")
    print(f"- {len(sample_channels)} каналов")

if __name__ == "__main__":
    print("=== Создание базы данных ===")
    create_database()
    print()
    print("=== Добавление тестовых данных ===")
    add_sample_data()
    print()
    print("✅ База данных готова к использованию!")
