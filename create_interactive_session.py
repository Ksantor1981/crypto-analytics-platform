#!/usr/bin/env python3
"""
Создание интерактивной USER сессии в Docker
"""

import asyncio
from telethon import TelegramClient

async def create_session():
    api_id = int(os.getenv("TELEGRAM_API_ID", "0"))  
    api_hash = os.getenv("TELEGRAM_API_HASH", "")
    session_name = "user_session"
    
    print("🚀 Создание USER сессии (не bot)")
    
    client = TelegramClient(session_name, api_id, api_hash)
    
    # НЕ используем bot_token - это создаст USER сессию
    await client.start()  # Без phone= будет запрашивать интерактивно
    
    me = await client.get_me()
    print(f"✅ Создана USER сессия: {me.first_name}")
    
    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(create_session())
