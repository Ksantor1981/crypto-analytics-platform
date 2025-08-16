#!/usr/bin/env python3
"""
Скрипт для исправления NULL значений в boolean полях SQLite
"""
import sqlite3
import os

def fix_sqlite_boolean_fields():
    """Исправляет NULL значения в boolean полях в SQLite"""
    db_path = "crypto_analytics.db"
    
    if not os.path.exists(db_path):
        print(f"❌ База данных {db_path} не найдена")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Проверяем структуру таблицы
        cursor.execute("PRAGMA table_info(signals)")
        columns = cursor.fetchall()
        print("📋 Структура таблицы signals:")
        for col in columns:
            print(f"  {col[1]} ({col[2]}) - nullable: {col[3]}")
        
        # Обновляем NULL значения в boolean полях
        cursor.execute("""
            UPDATE signals 
            SET reached_tp1 = 0, reached_tp2 = 0, reached_tp3 = 0, hit_stop_loss = 0 
            WHERE reached_tp1 IS NULL OR reached_tp2 IS NULL OR reached_tp3 IS NULL OR hit_stop_loss IS NULL
        """)
        
        updated_count = cursor.rowcount
        conn.commit()
        print(f"✅ Обновлено {updated_count} записей в таблице signals")
        
        # Проверяем результат
        cursor.execute("""
            SELECT COUNT(*) FROM signals 
            WHERE reached_tp1 IS NULL OR reached_tp2 IS NULL OR reached_tp3 IS NULL OR hit_stop_loss IS NULL
        """)
        null_count = cursor.fetchone()[0]
        
        if null_count == 0:
            print("✅ Все boolean поля исправлены")
        else:
            print(f"⚠️ Осталось {null_count} записей с NULL значениями")
        
        # Показываем статистику
        cursor.execute("SELECT COUNT(*) FROM signals")
        total_signals = cursor.fetchone()[0]
        print(f"📊 Всего сигналов в базе: {total_signals}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    fix_sqlite_boolean_fields()
