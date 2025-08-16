#!/usr/bin/env python3
"""
Скрипт для создания тестовых сигналов для backtesting
"""
import sqlite3
import os
from datetime import datetime, timedelta
from decimal import Decimal

def create_test_signals():
    """Создает тестовые сигналы для backtesting"""
    db_path = "crypto_analytics.db"
    
    if not os.path.exists(db_path):
        print(f"❌ База данных {db_path} не найдена")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Создаем тестовый канал если его нет
        cursor.execute("""
            INSERT OR IGNORE INTO channels (id, name, url, description, created_at, updated_at)
            VALUES (1, 'Test Channel', 'https://t.me/test', 'Test channel for backtesting', 
                   datetime('now'), datetime('now'))
        """)
        
        # Создаем тестовые сигналы
        test_signals = [
            {
                'channel_id': 1,
                'asset': 'BTCUSDT',
                'symbol': 'BTCUSDT',
                'direction': 'LONG',
                'entry_price': 50000.0,
                'tp1_price': 52000.0,
                'tp2_price': 54000.0,
                'tp3_price': 56000.0,
                'stop_loss': 48000.0,
                'original_text': 'BTC LONG 50000 TP1:52000 TP2:54000 TP3:56000 SL:48000',
                'message_timestamp': datetime.now() - timedelta(days=30),
                'timestamp': datetime.now() - timedelta(days=30),
                'status': 'COMPLETED',
                'final_exit_price': 52500.0,
                'final_exit_timestamp': datetime.now() - timedelta(days=25),
                'profit_loss_percentage': 5.0,
                'profit_loss_absolute': 2500.0,
                'is_successful': True,
                'reached_tp1': True,
                'reached_tp2': False,
                'reached_tp3': False,
                'hit_stop_loss': False,
                'ml_success_probability': 0.85,
                'ml_predicted_roi': 4.5,
                'is_ml_prediction_correct': True,
                'confidence_score': 85.0,
                'risk_reward_ratio': 2.5
            },
            {
                'channel_id': 1,
                'asset': 'ETHUSDT',
                'symbol': 'ETHUSDT',
                'direction': 'SHORT',
                'entry_price': 3000.0,
                'tp1_price': 2800.0,
                'tp2_price': 2600.0,
                'tp3_price': 2400.0,
                'stop_loss': 3200.0,
                'original_text': 'ETH SHORT 3000 TP1:2800 TP2:2600 TP3:2400 SL:3200',
                'message_timestamp': datetime.now() - timedelta(days=25),
                'timestamp': datetime.now() - timedelta(days=25),
                'status': 'COMPLETED',
                'final_exit_price': 2750.0,
                'final_exit_timestamp': datetime.now() - timedelta(days=20),
                'profit_loss_percentage': 8.33,
                'profit_loss_absolute': 250.0,
                'is_successful': True,
                'reached_tp1': True,
                'reached_tp2': False,
                'reached_tp3': False,
                'hit_stop_loss': False,
                'ml_success_probability': 0.78,
                'ml_predicted_roi': 7.2,
                'is_ml_prediction_correct': True,
                'confidence_score': 78.0,
                'risk_reward_ratio': 3.0
            },
            {
                'channel_id': 1,
                'asset': 'BTCUSDT',
                'symbol': 'BTCUSDT',
                'direction': 'LONG',
                'entry_price': 48000.0,
                'tp1_price': 50000.0,
                'tp2_price': 52000.0,
                'tp3_price': 54000.0,
                'stop_loss': 46000.0,
                'original_text': 'BTC LONG 48000 TP1:50000 TP2:52000 TP3:54000 SL:46000',
                'message_timestamp': datetime.now() - timedelta(days=20),
                'timestamp': datetime.now() - timedelta(days=20),
                'status': 'COMPLETED',
                'final_exit_price': 46500.0,
                'final_exit_timestamp': datetime.now() - timedelta(days=15),
                'profit_loss_percentage': -3.125,
                'profit_loss_absolute': -1500.0,
                'is_successful': False,
                'reached_tp1': False,
                'reached_tp2': False,
                'reached_tp3': False,
                'hit_stop_loss': True,
                'ml_success_probability': 0.45,
                'ml_predicted_roi': -2.1,
                'is_ml_prediction_correct': True,
                'confidence_score': 45.0,
                'risk_reward_ratio': 1.8
            }
        ]
        
        for signal in test_signals:
            cursor.execute("""
                INSERT INTO signals (
                    channel_id, asset, symbol, direction, entry_price, tp1_price, tp2_price, tp3_price, stop_loss,
                    original_text, message_timestamp, timestamp, status, final_exit_price, final_exit_timestamp,
                    profit_loss_percentage, profit_loss_absolute, is_successful, reached_tp1, reached_tp2, reached_tp3, hit_stop_loss,
                    ml_success_probability, ml_predicted_roi, is_ml_prediction_correct, confidence_score, risk_reward_ratio,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                signal['channel_id'], signal['asset'], signal['symbol'], signal['direction'], 
                signal['entry_price'], signal['tp1_price'], signal['tp2_price'], signal['tp3_price'], signal['stop_loss'],
                signal['original_text'], signal['message_timestamp'], signal['timestamp'], signal['status'],
                signal['final_exit_price'], signal['final_exit_timestamp'], signal['profit_loss_percentage'],
                signal['profit_loss_absolute'], signal['is_successful'], signal['reached_tp1'], signal['reached_tp2'],
                signal['reached_tp3'], signal['hit_stop_loss'], signal['ml_success_probability'], signal['ml_predicted_roi'],
                signal['is_ml_prediction_correct'], signal['confidence_score'], signal['risk_reward_ratio'],
                datetime.now(), datetime.now()
            ))
        
        conn.commit()
        print(f"✅ Создано {len(test_signals)} тестовых сигналов")
        
        # Проверяем результат
        cursor.execute("SELECT COUNT(*) FROM signals")
        total_signals = cursor.fetchone()[0]
        print(f"📊 Всего сигналов в базе: {total_signals}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    create_test_signals()
