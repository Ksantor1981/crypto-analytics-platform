#!/usr/bin/env python3
"""
Создание USER сессии для Telegram API (не bot)
Требует номер телефона для авторизации
"""

import asyncio
import os
from telethon import TelegramClient

async def create_user_session():
    """Создает пользовательскую сессию для Telegram"""
    
    # API данные из workers/telegram_config.env
    api_id = 21073808
    api_hash = "2e3adb8940912dd295fe20c1d2ce5368"
    session_name = "user_telegram_session"
    
    print("🚀 Создание USER сессии для Telegram...")
    print("=" * 50)
    
    # Запрашиваем номер телефона
    phone = input("📱 Введите номер телефона (с кодом страны, например +7): ")
    
    if not phone.startswith('+'):
        phone = '+' + phone
    
    print(f"📞 Используем номер: {phone}")
    
    # Создаем клиент как USER (не bot)
    client = TelegramClient(session_name, api_id, api_hash)
    
    try:
        print("🔗 Подключение к Telegram...")
        await client.start(phone=phone)
        
        # Получаем информацию о пользователе
        me = await client.get_me()
        print(f"✅ Авторизован как: {me.first_name} {me.last_name or ''} (@{me.username or 'no_username'})")
        
        # Тестируем доступ к каналам
        print("\n🔍 Тестирование доступа к каналам...")
        test_channels = ['crypto', 'bitcoin', 'ethereum']
        
        accessible_channels = []
        for channel in test_channels:
            try:
                entity = await client.get_entity(channel)
                print(f"  ✅ @{channel} - доступен ({entity.title})")
                accessible_channels.append(channel)
            except Exception as e:
                print(f"  ❌ @{channel} - недоступен: {str(e)[:50]}")
        
        print(f"\n📊 Доступно каналов: {len(accessible_channels)}")
        
        # Тестируем получение сообщений
        if accessible_channels:
            test_channel = accessible_channels[0]
            print(f"\n📨 Тестирование сообщений из @{test_channel}...")
            try:
                messages = await client.get_messages(test_channel, limit=3)
                print(f"  ✅ Получено {len(messages)} сообщений")
                
                for i, msg in enumerate(messages[:2], 1):
                    if msg.text:
                        preview = msg.text[:60].replace('\n', ' ')
                        print(f"  {i}. {preview}...")
                    
            except Exception as e:
                print(f"  ❌ Ошибка получения сообщений: {e}")
        
        await client.disconnect()
        
        print(f"\n✅ USER сессия успешно создана: {session_name}.session")
        print("📋 Теперь скопируйте этот файл в Docker контейнер:")
        print(f"   docker cp {session_name}.session crypto-analytics-backend:/app/telegram_session.session")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка создания сессии: {e}")
        await client.disconnect()
        return False

if __name__ == "__main__":
    print("📱 СОЗДАНИЕ TELEGRAM USER SESSION")
    print("=" * 50)
    print("⚠️  ВАЖНО: Этот скрипт требует:")
    print("   - Доступ к SMS/звонкам на указанный номер")
    print("   - Код подтверждения из Telegram")
    print("   - Возможно 2FA пароль (если включен)")
    print("=" * 50)
    
    confirm = input("Продолжить? (y/N): ")
    if confirm.lower() in ['y', 'yes', 'да']:
        asyncio.run(create_user_session())
    else:
        print("❌ Отменено пользователем")
