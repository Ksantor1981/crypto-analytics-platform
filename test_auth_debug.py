#!/usr/bin/env python3

import requests
import json

def test_auth_registration():
    """Тестирует регистрацию пользователя"""
    
    base_url = "http://localhost:8000"
    
    print("🔐 ТЕСТ АУТЕНТИФИКАЦИИ")
    print("=" * 50)
    
    # Тест регистрации
    registration_data = {
        "email": "test_debug@example.com",
        "password": "testpass123",
        "confirm_password": "testpass123",
        "full_name": "Test Debug User"
    }
    
    print(f"📝 Тестирую регистрацию: {registration_data['email']}")
    
    try:
        # Сразу пробуем войти
        print(f"\n🔑 Тестирую вход...")
        login_data = {
            "email": registration_data["email"],
            "password": registration_data["password"]
        }
        
        login_response = requests.post(
            f"{base_url}/api/v1/users/login",
            json=login_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Статус входа: {login_response.status_code}")
        print(f"Ответ входа: {login_response.text}")
        
        if login_response.status_code == 200:
            print("✅ Вход прошел успешно!")
            tokens = login_response.json()
            print(f"Получен токен доступа: {tokens.get('access_token', 'NONE')[:50]}...")
            return True
        else:
            print("❌ Ошибка входа!")
            return False
            
    except Exception as e:
        print(f"❌ Исключение: {e}")
        return False

if __name__ == "__main__":
    test_auth_registration() 