#!/usr/bin/env python3

import sys
import os

# Добавляем путь к приложению
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.app.core.database import engine, Base
from backend.app.models import user, channel, signal, subscription, payment, api_key, performance_metric

def create_all_tables():
    """Создает все таблицы в базе данных"""
    
    print("🗄️ СОЗДАНИЕ ТАБЛИЦ БАЗЫ ДАННЫХ")
    print("=" * 50)
    
    try:
        # Импортируем все модели для регистрации в Base
        print("📦 Импортирую модели...")
        
        # Создаем все таблицы
        print("🔨 Создаю таблицы...")
        Base.metadata.create_all(bind=engine)
        
        print("✅ Все таблицы созданы успешно!")
        
        # Проверяем созданные таблицы
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        print(f"\n📋 Созданные таблицы ({len(tables)}):")
        for table in sorted(tables):
            print(f"  - {table}")
            
        return True
        
    except Exception as e:
        print(f"❌ Ошибка создания таблиц: {e}")
        return False

if __name__ == "__main__":
    success = create_all_tables()
    sys.exit(0 if success else 1) 