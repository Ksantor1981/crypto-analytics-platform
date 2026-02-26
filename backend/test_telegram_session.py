#!/usr/bin/env python3
"""
Тестирование Telegram сессии в Docker
"""

import asyncio
import sys
import os

async def test_session():
    try:
        from telethon import TelegramClient
        
        api_id = int(os.getenv("TELEGRAM_API_ID", "0"))
        api_hash = os.getenv("TELEGRAM_API_HASH", "")
        session_file = "telegram_session"
        
        print(f"🔍 Testing session: {session_file}")
        
        client = TelegramClient(session_file, api_id, api_hash)
        
        await client.connect()
        print("✅ Connected to Telegram")
        
        is_authorized = await client.is_user_authorized()
        print(f"🔐 User authorized: {is_authorized}")
        
        if is_authorized:
            me = await client.get_me()
            print(f"👤 User: {me.first_name} (@{me.username})")
            
            # Test channel access
            try:
                entity = await client.get_entity('crypto')
                print(f"🏢 Channel access test: {entity.title}")
                
                messages = await client.get_messages('crypto', limit=2)
                print(f"📨 Messages retrieved: {len(messages)}")
                
            except Exception as e:
                print(f"❌ Channel test failed: {e}")
        
        await client.disconnect()
        return is_authorized
        
    except Exception as e:
        print(f"❌ Session test failed: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_session())
    print(f"🎯 Session is {'VALID' if result else 'INVALID'}")
