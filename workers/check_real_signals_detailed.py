#!/usr/bin/env python3
"""
Улучшенный скрипт для проверки реальных сигналов с полными датами
"""

import asyncio
import aiohttp
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
from bs4 import BeautifulSoup
import re

# Добавляем пути для импортов
sys.path.append(str(Path(__file__).parent))

async def check_telegram_web_detailed(channel_username: str) -> List[Dict[str, Any]]:
    """Проверка публичных сообщений канала с детальной информацией"""
    
    # Убираем @ если есть
    username = channel_username.replace('@', '')
    
    # URL для публичной страницы канала
    url = f"https://t.me/s/{username}"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    html = await response.text()
                    return parse_telegram_messages_detailed(html, channel_username)
                else:
                    print(f"❌ Ошибка {response.status} для {channel_username}")
                    return []
    except Exception as e:
        print(f"❌ Ошибка при проверке {channel_username}: {e}")
        return []

def parse_telegram_messages_detailed(html: str, channel_username: str) -> List[Dict[str, Any]]:
    """Парсинг сообщений с детальной информацией о датах"""
    
    soup = BeautifulSoup(html, 'html.parser')
    messages = []
    
    # Ищем сообщения
    message_elements = soup.find_all('div', class_='tgme_widget_message')
    
    for msg in message_elements[:10]:  # Берем последние 10 сообщений
        try:
            # Извлекаем текст сообщения
            text_elem = msg.find('div', class_='tgme_widget_message_text')
            if text_elem:
                text = text_elem.get_text(strip=True)
                
                # Извлекаем полную дату и время
                time_elem = msg.find('time')
                full_datetime = None
                if time_elem and time_elem.get('datetime'):
                    full_datetime = time_elem.get('datetime')
                
                # Извлекаем отображаемую дату
                date_elem = msg.find('a', class_='tgme_widget_message_date')
                display_date = None
                if date_elem:
                    display_date = date_elem.get_text(strip=True)
                
                # Извлекаем ID сообщения
                message_id = None
                message_link = msg.find('a', class_='tgme_widget_message_date')
                if message_link and message_link.get('href'):
                    href = message_link.get('href')
                    # Извлекаем ID из ссылки вида /s/channel/123
                    if '/' in href:
                        message_id = href.split('/')[-1]
                
                if text and len(text) > 10:  # Фильтруем короткие сообщения
                    messages.append({
                        'channel': channel_username,
                        'text': text,
                        'full_datetime': full_datetime,
                        'display_date': display_date,
                        'message_id': message_id,
                        'length': len(text)
                    })
        except Exception as e:
            print(f"⚠️ Ошибка парсинга сообщения: {e}")
            continue
    
    return messages

def format_datetime(full_datetime: str) -> str:
    """Форматирование даты и времени"""
    if not full_datetime:
        return "N/A"
    
    try:
        # Парсим ISO формат
        dt = datetime.fromisoformat(full_datetime.replace('Z', '+00:00'))
        now = datetime.now(dt.tzinfo)
        
        # Вычисляем разницу
        diff = now - dt
        
        if diff.days > 0:
            return f"{dt.strftime('%d.%m.%Y в %H:%M')} ({diff.days} дн. назад)"
        elif diff.seconds >= 3600:
            hours = diff.seconds // 3600
            return f"{dt.strftime('%d.%m.%Y в %H:%M')} ({hours} ч. назад)"
        else:
            minutes = diff.seconds // 60
            return f"{dt.strftime('%d.%m.%Y в %H:%M')} ({minutes} мин. назад)"
    except:
        return full_datetime

def check_for_trading_signals(text: str) -> bool:
    """Проверка, содержит ли текст торговые сигналы"""
    
    # Паттерны для торговых сигналов
    signal_patterns = [
        r'\b(BTC|ETH|SOL|DOGE|ADA|XRP|BNB|MATIC|LINK|UNI|TRX|TON)\b',
        r'\b(LONG|SHORT|BUY|SELL)\b',
        r'\b(Entry|Target|TP|SL|Stop Loss)\b',
        r'\$[\d,]+',
        r'\b\d+\.?\d*\b',
        r'🚀|📈|📉|🎯|🛑|📍|✅|🔥'
    ]
    
    text_upper = text.upper()
    
    # Проверяем наличие хотя бы 2 паттернов
    matches = 0
    for pattern in signal_patterns:
        if re.search(pattern, text_upper):
            matches += 1
    
    return matches >= 2

async def check_channels_detailed():
    """Детальная проверка каналов"""
    
    # Список каналов для проверки
    channels = [
        "binancekillers",
        "CryptoCapoTG", 
        "io_altsignals",
        "Wolf_of_Trading_singals",
        "fatpigsignals",
        "Signals_BTC_ETH"
    ]
    
    print("🔍 ДЕТАЛЬНАЯ ПРОВЕРКА РЕАЛЬНЫХ СИГНАЛОВ")
    print("="*100)
    print(f"🕐 Время проверки: {datetime.now().strftime('%d.%m.%Y в %H:%M:%S')}")
    print("="*100)
    
    all_messages = []
    
    for channel in channels:
        print(f"\n📺 Проверяем канал: @{channel}")
        messages = await check_telegram_web_detailed(channel)
        
        if messages:
            print(f"✅ Найдено сообщений: {len(messages)}")
            
            # Показываем последние 3 сообщения с полными датами
            print(f"📅 Последние сообщения:")
            for i, msg in enumerate(messages[:3], 1):
                formatted_date = format_datetime(msg.get('full_datetime'))
                print(f"   {i}. {formatted_date}")
                print(f"      ID: {msg.get('message_id', 'N/A')}")
                print(f"      Текст: {msg['text'][:80]}...")
            
            # Проверяем на торговые сигналы
            signal_messages = []
            for msg in messages:
                if check_for_trading_signals(msg['text']):
                    signal_messages.append(msg)
            
            if signal_messages:
                print(f"🎯 Найдено сигналов: {len(signal_messages)}")
                all_messages.extend(signal_messages)
                
                # Показываем последний сигнал с полной датой
                latest = signal_messages[0]
                formatted_date = format_datetime(latest.get('full_datetime'))
                print(f"📝 Последний сигнал:")
                print(f"   Время: {formatted_date}")
                print(f"   ID: {latest.get('message_id', 'N/A')}")
                print(f"   Текст: {latest['text'][:100]}...")
            else:
                print("❌ Торговых сигналов не найдено")
        else:
            print("❌ Сообщения не найдены или канал недоступен")
    
    # Итоговая статистика
    print(f"\n{'='*100}")
    print(f"📊 ИТОГОВАЯ СТАТИСТИКА")
    print(f"{'='*100}")
    
    if all_messages:
        print(f"🎯 Всего найдено сигналов: {len(all_messages)}")
        
        # Показываем все найденные сигналы с полными датами
        for i, msg in enumerate(all_messages, 1):
            formatted_date = format_datetime(msg.get('full_datetime'))
            print(f"\n🔍 СИГНАЛ #{i}")
            print(f"📺 Канал: @{msg['channel']}")
            print(f"⏰ Полная дата: {formatted_date}")
            print(f"🆔 ID сообщения: {msg.get('message_id', 'N/A')}")
            print(f"📝 Текст: {msg['text']}")
            print(f"📏 Длина: {msg['length']} символов")
    else:
        print("❌ Торговых сигналов не найдено ни на одном канале")

async def main():
    """Основная функция"""
    
    print("🚨 ДЕТАЛЬНАЯ ПРОВЕРКА РЕАЛЬНЫХ ДАННЫХ С КАНАЛОВ!")
    print("Показываем полные даты и время...")
    
    await check_channels_detailed()
    
    print(f"\n{'='*100}")
    print(f"💡 РЕКОМЕНДАЦИИ ДЛЯ ПРОВЕРКИ")
    print(f"{'='*100}")
    print("1. 📱 Откройте каналы вручную в Telegram")
    print("2. 🌐 Используйте t.me/s/channel_name")
    print("3. 🔍 Проверьте ID сообщений")
    print("4. 📅 Сравните даты с текущими")

if __name__ == "__main__":
    asyncio.run(main())
