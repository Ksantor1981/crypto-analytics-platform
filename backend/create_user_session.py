#!/usr/bin/env python3
"""
Создание USER сессии для Telegram API (не bot)
"""

import asyncio
from telethon import TelegramClient

async def create_user_session():
    # API данные из workers/telegram_config.env
    api_id = int(os.getenv("TELEGRAM_API_ID", "0"))
    api_hash = os.getenv("TELEGRAM_API_HASH", "")
    session_name = "user_session"
    
    print("Создаем USER сессию для Telegram...")
    
    # Создаем клиент как USER (не bot)
    client = TelegramClient(session_name, api_id, api_hash)
    
    await client.start()
    print("✅ USER сессия создана успешно!")
    
    # Получаем информацию о пользователе
    me = await client.get_me()
    print(f"Авторизован как: {me.first_name} ({me.username})")
    
    # Получаем список диалогов для проверки
    print("\nПолучаем диалоги...")
    dialogs = await client.get_dialogs(limit=5)
    
    for dialog in dialogs:
        print(f"- {dialog.name}")
    
    await client.disconnect()
    print(f"\n✅ Сессия сохранена как: {session_name}.session")

if __name__ == "__main__":
    asyncio.run(create_user_session())
