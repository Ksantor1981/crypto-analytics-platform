#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.app.services.user_service import UserService
from backend.app.core.database import get_db
from backend.app.core.security import create_user_tokens

def test_login_process():
    """Детальный тест процесса входа"""
    
    print("🔐 ДЕТАЛЬНЫЙ ТЕСТ ВХОДА")
    print("=" * 50)
    
    db = next(get_db())
    
    try:
        user_service = UserService(db)
        
        email = "test_debug@example.com"
        password = "testpass123"
        
        print(f"👤 Тестирую вход: {email}")
        
        # Шаг 1: Аутентификация
        print("1️⃣ Проверяю аутентификацию...")
        user = user_service.authenticate(email, password)
        
        if user:
            print(f"✅ Аутентификация прошла: {user.email} (ID: {user.id})")
            print(f"📝 Активен: {user.is_active}")
            print(f"📝 Роль: {user.role}")
        else:
            print("❌ Аутентификация не прошла")
            return False
        
        # Шаг 2: Создание токенов
        print("2️⃣ Создаю токены...")
        try:
            tokens = create_user_tokens(user)
            print("✅ Токены созданы успешно")
            print(f"📝 Access token: {tokens['access_token'][:50]}...")
            print(f"📝 Refresh token: {tokens['refresh_token'][:50]}...")
            print(f"📝 Token type: {tokens['token_type']}")
            
            return True
            
        except Exception as e:
            print(f"❌ Ошибка создания токенов: {e}")
            return False
        
    except Exception as e:
        print(f"❌ Общая ошибка: {e}")
        return False
    finally:
        db.close()

if __name__ == "__main__":
    success = test_login_process()
    print(f"\n🎯 РЕЗУЛЬТАТ: {'✅ УСПЕХ' if success else '❌ НЕУДАЧА'}") 