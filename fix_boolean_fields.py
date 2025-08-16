#!/usr/bin/env python3
"""
Скрипт для исправления NULL значений в boolean полях
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.app.database import get_db
from backend.app.models.signal import Signal

def fix_boolean_fields():
    """Исправляет NULL значения в boolean полях"""
    db = next(get_db())
    
    try:
        # Обновляем все записи с NULL значениями в boolean полях
        updated_count = db.query(Signal).filter(
            (Signal.reached_tp1.is_(None)) |
            (Signal.reached_tp2.is_(None)) |
            (Signal.reached_tp3.is_(None)) |
            (Signal.hit_stop_loss.is_(None))
        ).update({
            Signal.reached_tp1: False,
            Signal.reached_tp2: False,
            Signal.reached_tp3: False,
            Signal.hit_stop_loss: False
        })
        
        db.commit()
        print(f"✅ Обновлено {updated_count} записей в таблице signals")
        
        # Проверяем результат
        null_count = db.query(Signal).filter(
            (Signal.reached_tp1.is_(None)) |
            (Signal.reached_tp2.is_(None)) |
            (Signal.reached_tp3.is_(None)) |
            (Signal.hit_stop_loss.is_(None))
        ).count()
        
        if null_count == 0:
            print("✅ Все boolean поля исправлены")
        else:
            print(f"⚠️ Осталось {null_count} записей с NULL значениями")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    fix_boolean_fields()
