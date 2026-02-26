#!/usr/bin/env python3
"""
Быстрое создание USER сессии
"""
import asyncio
import sys

async def quick_session():
    try:
        from telethon import TelegramClient
        
        api_id = int(os.getenv("TELEGRAM_API_ID", "0"))
        api_hash = os.getenv("TELEGRAM_API_HASH", "")
        
        print("📱 Создание USER сессии...")
        print("Введите номер телефона (например +79123456789):")
        
        phone = input("📞 Номер: ")
        
        client = TelegramClient('user_crypto_session', api_id, api_hash)
        await client.start(phone=phone)
        
        me = await client.get_me()
        print(f"✅ USER сессия создана: {me.first_name}")
        print(f"📁 Файл: user_crypto_session.session")
        
        await client.disconnect()
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(quick_session())
