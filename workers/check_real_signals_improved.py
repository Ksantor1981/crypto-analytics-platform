#!/usr/bin/env python3
"""
Улучшенный скрипт для проверки реальных сигналов с расширенным поиском
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

async def check_telegram_web_extended(channel_username: str, max_messages: int = 50) -> List[Dict[str, Any]]:
    """Расширенная проверка публичных сообщений канала"""
    
    # Убираем @ если есть
    username = channel_username.replace('@', '')
    
    # URL для публичной страницы канала
    url = f"https://t.me/s/{username}"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=15) as response:
                if response.status == 200:
                    html = await response.text()
                    return parse_telegram_messages_extended(html, channel_username, max_messages)
                else:
                    print(f"❌ Ошибка {response.status} для {channel_username}")
                    return []
    except Exception as e:
        print(f"❌ Ошибка при проверке {channel_username}: {e}")
        return []

def parse_telegram_messages_extended(html: str, channel_username: str, max_messages: int) -> List[Dict[str, Any]]:
    """Расширенный парсинг сообщений"""
    
    soup = BeautifulSoup(html, 'html.parser')
    messages = []
    
    # Ищем сообщения
    message_elements = soup.find_all('div', class_='tgme_widget_message')
    
    for msg in message_elements[:max_messages]:
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
                    if '/' in href:
                        message_id = href.split('/')[-1]
                
                if text and len(text) > 5:  # Фильтруем очень короткие сообщения
                    messages.append({
                        'channel': channel_username,
                        'text': text,
                        'full_datetime': full_datetime,
                        'display_date': display_date,
                        'message_id': message_id,
                        'length': len(text)
                    })
        except Exception as e:
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
    """Улучшенная проверка торговых сигналов"""
    
    # Расширенные паттерны для торговых сигналов
    signal_patterns = [
        r'\b(BTC|ETH|SOL|DOGE|ADA|XRP|BNB|MATIC|LINK|UNI|TRX|TON|ENS|ENA)\b',
        r'\b(LONG|SHORT|BUY|SELL)\b',
        r'\b(Entry|Target|TP|SL|Stop Loss)\b',
        r'\$[\d,]+',
        r'\b\d+\.?\d*\b',
        r'🚀|📈|📉|🎯|🛑|📍|✅|🔥|💎|⚡️',
        r'\bSIGNAL\b',
        r'\bTake-Profit\b',
        r'\bProfit\b',
        r'\bUSDT\b'
    ]
    
    text_upper = text.upper()
    
    # Проверяем наличие хотя бы 2 паттернов
    matches = 0
    for pattern in signal_patterns:
        if re.search(pattern, text_upper):
            matches += 1
    
    return matches >= 2

def check_for_recent_signals(messages: List[Dict[str, Any]], days_threshold: int = 3) -> List[Dict[str, Any]]:
    """Проверка на свежие сигналы"""
    
    recent_signals = []
    now = datetime.now()
    
    for msg in messages:
        if msg.get('full_datetime'):
            try:
                dt = datetime.fromisoformat(msg['full_datetime'].replace('Z', '+00:00'))
                diff = now - dt
                
                if diff.days <= days_threshold and check_for_trading_signals(msg['text']):
                    recent_signals.append(msg)
            except:
                continue
    
    return recent_signals

async def check_channels_improved():
    """Улучшенная проверка каналов"""
    
    # Расширенный список каналов
    channels = [
        "binancekillers",
        "CryptoCapoTG", 
        "io_altsignals",
        "Wolf_of_Trading_singals",
        "fatpigsignals",
        "Signals_BTC_ETH",
        "cryptoceo_alex",  # Новый канал
        "Crypto_Futures_Signals",
        "TradingViewIdeas",
        "Crypto_Inner_Circler"
    ]
    
    print("🔍 УЛУЧШЕННАЯ ПРОВЕРКА РЕАЛЬНЫХ СИГНАЛОВ")
    print("="*120)
    print(f"🕐 Время проверки: {datetime.now().strftime('%d.%m.%Y в %H:%M:%S')}")
    print("="*120)
    
    all_recent_signals = []
    
    for channel in channels:
        print(f"\n📺 Проверяем канал: @{channel}")
        messages = await check_telegram_web_extended(channel, max_messages=50)
        
        if messages:
            print(f"✅ Найдено сообщений: {len(messages)}")
            
            # Ищем свежие сигналы (за последние 3 дня)
            recent_signals = check_for_recent_signals(messages, days_threshold=3)
            
            if recent_signals:
                print(f"🎯 Найдено свежих сигналов: {len(recent_signals)}")
                all_recent_signals.extend(recent_signals)
                
                # Показываем все свежие сигналы
                for i, signal in enumerate(recent_signals, 1):
                    formatted_date = format_datetime(signal.get('full_datetime'))
                    print(f"   {i}. {formatted_date}")
                    print(f"      ID: {signal.get('message_id', 'N/A')}")
                    print(f"      Текст: {signal['text'][:100]}...")
            else:
                print("❌ Свежих сигналов не найдено")
                
                # Показываем последние 3 сообщения для анализа
                print(f"📅 Последние сообщения:")
                for i, msg in enumerate(messages[:3], 1):
                    formatted_date = format_datetime(msg.get('full_datetime'))
                    print(f"   {i}. {formatted_date}")
                    print(f"      ID: {msg.get('message_id', 'N/A')}")
                    print(f"      Текст: {msg['text'][:80]}...")
        else:
            print("❌ Сообщения не найдены или канал недоступен")
    
    # Итоговая статистика
    print(f"\n{'='*120}")
    print(f"📊 ИТОГОВАЯ СТАТИСТИКА СВЕЖИХ СИГНАЛОВ")
    print(f"{'='*120}")
    
    if all_recent_signals:
        print(f"🎯 Всего найдено свежих сигналов: {len(all_recent_signals)}")
        
        # Сортируем по дате (новые сначала)
        all_recent_signals.sort(key=lambda x: x.get('full_datetime', ''), reverse=True)
        
        # Показываем все свежие сигналы
        for i, msg in enumerate(all_recent_signals, 1):
            formatted_date = format_datetime(msg.get('full_datetime'))
            print(f"\n🔍 СВЕЖИЙ СИГНАЛ #{i}")
            print(f"📺 Канал: @{msg['channel']}")
            print(f"⏰ Дата: {formatted_date}")
            print(f"🆔 ID: {msg.get('message_id', 'N/A')}")
            print(f"📝 Текст: {msg['text']}")
            print(f"📏 Длина: {msg['length']} символов")
    else:
        print("❌ Свежих сигналов не найдено ни на одном канале")
        print("💡 Возможные причины:")
        print("   - Каналы приватные")
        print("   - Сигналы в изображениях")
        print("   - Сигналы в защищенных каналах")
        print("   - Нужен авторизованный доступ")

async def main():
    """Основная функция"""
    
    print("🚨 УЛУЧШЕННАЯ ПРОВЕРКА РЕАЛЬНЫХ ДАННЫХ!")
    print("Ищем свежие сигналы за последние 3 дня...")
    
    await check_channels_improved()
    
    print(f"\n{'='*120}")
    print(f"💡 РЕКОМЕНДАЦИИ")
    print(f"{'='*120}")
    print("1. 📱 Проверьте защищенные каналы вручную")
    print("2. 🖼️ Обратите внимание на сигналы в изображениях")
    print("3. 🔍 Используйте авторизованный доступ для приватных каналов")
    print("4. 📅 Проверьте актуальность цен на биржах")

if __name__ == "__main__":
    asyncio.run(main())
