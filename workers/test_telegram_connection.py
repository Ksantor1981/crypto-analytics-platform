import asyncio
import json
import os
from dotenv import load_dotenv

# Загружаем конфигурацию
load_dotenv('telegram_config.env')

async def test_telegram_connection():
    """Простой тест подключения к Telegram"""
    print("🔍 Тестирование подключения к Telegram...")
    
    api_id = os.getenv('TELEGRAM_API_ID')
    api_hash = os.getenv('TELEGRAM_API_HASH')
    
    print(f"API ID: {api_id}")
    print(f"API Hash: {api_hash[:10]}...")
    
    if not api_id or not api_hash:
        print("❌ API ключи не найдены!")
        return False
    
    try:
        from telethon import TelegramClient
        
        print("📱 Создание клиента Telegram...")
        client = TelegramClient('test_session', api_id, api_hash)
        
        print("🔐 Подключение к Telegram...")
        await client.start()
        
        if await client.is_user_authorized():
            print("✅ Авторизация успешна!")
            
            # Получаем информацию о пользователе
            me = await client.get_me()
            print(f"👤 Пользователь: {me.first_name} (@{me.username})")
            
            await client.disconnect()
            return True
        else:
            print("⚠️ Требуется авторизация!")
            print("Введите номер телефона в формате +7XXXXXXXXXX:")
            phone = input().strip()
            
            await client.send_code_request(phone)
            print("Введите код подтверждения из Telegram:")
            code = input().strip()
            
            try:
                await client.sign_in(phone, code)
                print("✅ Авторизация завершена!")
                await client.disconnect()
                return True
            except Exception as e:
                print(f"❌ Ошибка авторизации: {e}")
                await client.disconnect()
                return False
                
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return False

async def test_channel_access():
    """Тест доступа к каналам"""
    print("\n📡 Тестирование доступа к каналам...")
    
    api_id = os.getenv('TELEGRAM_API_ID')
    api_hash = os.getenv('TELEGRAM_API_HASH')
    
    try:
        from telethon import TelegramClient
        from telethon.errors import ChannelPrivateError, UsernameNotOccupiedError
        
        client = TelegramClient('test_session', api_id, api_hash)
        await client.start()
        
        # Список каналов для тестирования
        test_channels = [
            "signalsbitcoinandethereum",
            "CryptoCapoTG", 
            "cryptosignals",
            "binance_signals",
            "crypto_analytics"
        ]
        
        accessible_channels = []
        inaccessible_channels = []
        
        for username in test_channels:
            try:
                print(f"🔍 Проверка канала: {username}")
                entity = await client.get_entity(username)
                
                channel_info = {
                    "username": username,
                    "id": entity.id,
                    "title": getattr(entity, 'title', username),
                    "participants_count": getattr(entity, 'participants_count', 0),
                    "accessible": True
                }
                accessible_channels.append(channel_info)
                print(f"✅ {username} - доступен")
                
            except ChannelPrivateError:
                print(f"❌ {username} - приватный канал")
                inaccessible_channels.append({
                    "username": username,
                    "error": "Приватный канал",
                    "accessible": False
                })
                
            except UsernameNotOccupiedError:
                print(f"❌ {username} - канал не существует")
                inaccessible_channels.append({
                    "username": username,
                    "error": "Канал не существует",
                    "accessible": False
                })
                
            except Exception as e:
                print(f"❌ {username} - ошибка: {e}")
                inaccessible_channels.append({
                    "username": username,
                    "error": str(e),
                    "accessible": False
                })
        
        await client.disconnect()
        
        print(f"\n📊 РЕЗУЛЬТАТЫ:")
        print(f"Доступных каналов: {len(accessible_channels)}")
        print(f"Недоступных каналов: {len(inaccessible_channels)}")
        
        if accessible_channels:
            print("\n✅ ДОСТУПНЫЕ КАНАЛЫ:")
            for channel in accessible_channels:
                print(f"  - {channel['username']} ({channel['title']})")
        
        if inaccessible_channels:
            print("\n❌ НЕДОСТУПНЫЕ КАНАЛЫ:")
            for channel in inaccessible_channels:
                print(f"  - {channel['username']}: {channel['error']}")
        
        return accessible_channels, inaccessible_channels
        
    except Exception as e:
        print(f"❌ Ошибка тестирования каналов: {e}")
        return [], []

async def main():
    """Основная функция"""
    print("🚀 ЗАПУСК ТЕСТА TELEGRAM API")
    print("=" * 50)
    
    # Тест подключения
    connection_ok = await test_telegram_connection()
    
    if connection_ok:
        # Тест доступа к каналам
        accessible, inaccessible = await test_channel_access()
        
        # Сохраняем результаты
        results = {
            "connection_success": connection_ok,
            "accessible_channels": accessible,
            "inaccessible_channels": inaccessible,
            "total_accessible": len(accessible),
            "total_inaccessible": len(inaccessible)
        }
        
        with open('telegram_test_results.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Результаты сохранены в telegram_test_results.json")
        
        if accessible:
            print(f"\n🎯 ГОТОВ К СБОРУ СИГНАЛОВ!")
            print(f"Доступно каналов: {len(accessible)}")
        else:
            print(f"\n⚠️ НЕТ ДОСТУПНЫХ КАНАЛОВ")
            print("Нужно подписаться на каналы или добавить другие")
    else:
        print(f"\n❌ НЕ УДАЛОСЬ ПОДКЛЮЧИТЬСЯ К TELEGRAM")

if __name__ == "__main__":
    asyncio.run(main())
