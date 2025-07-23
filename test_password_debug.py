#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.app.core.security import get_password_hash, verify_password
from backend.app.core.database import get_db
from backend.app.models.user import User

def test_password_hashing():
    """Тестирует хеширование и проверку паролей"""
    
    print("🔐 ТЕСТ ХЕШИРОВАНИЯ ПАРОЛЕЙ")
    print("=" * 50)
    
    test_password = "testpass123"
    
    # Тест хеширования
    print(f"🧪 Тестирую пароль: {test_password}")
    hashed = get_password_hash(test_password)
    print(f"📝 Хеш: {hashed[:50]}...")
    
    # Тест проверки
    is_valid = verify_password(test_password, hashed)
    print(f"✅ Проверка хеша: {'ПРОШЛА' if is_valid else 'НЕ ПРОШЛА'}")
    
    # Тест неправильного пароля
    wrong_password = "wrongpass123"
    is_wrong = verify_password(wrong_password, hashed)
    print(f"❌ Проверка неправильного пароля: {'НЕ ПРОШЛА' if not is_wrong else 'ОШИБКА!'}")
    
    return is_valid and not is_wrong

def test_user_in_database():
    """Проверяет пользователя в базе данных"""
    
    print("\n📊 ТЕСТ ПОЛЬЗОВАТЕЛЯ В БД")
    print("=" * 50)
    
    db = next(get_db())
    
    try:
        user = db.query(User).filter(User.email == "test_debug@example.com").first()
        
        if user:
            print(f"✅ Пользователь найден: {user.email}")
            print(f"📝 ID: {user.id}")
            print(f"📝 Полное имя: {user.full_name}")
            print(f"📝 Активен: {user.is_active}")
            print(f"📝 Хеш пароля: {user.hashed_password[:50]}...")
            
            # Тест проверки пароля из БД
            test_password = "testpass123"
            is_valid = verify_password(test_password, user.hashed_password)
            print(f"🔑 Проверка пароля из БД: {'ПРОШЛА' if is_valid else 'НЕ ПРОШЛА'}")
            
            return is_valid
        else:
            print("❌ Пользователь не найден в БД")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка при проверке БД: {e}")
        return False
    finally:
        db.close()

if __name__ == "__main__":
    hash_test = test_password_hashing()
    db_test = test_user_in_database()
    
    print(f"\n📋 ИТОГ:")
    print(f"Хеширование: {'✅' if hash_test else '❌'}")
    print(f"БД пользователь: {'✅' if db_test else '❌'}") 