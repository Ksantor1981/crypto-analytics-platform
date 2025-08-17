#!/usr/bin/env python3
"""
Скрипт для проверки реальных сигналов с Telegram каналов
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

async def check_telegram_web(channel_username: str) -> List[Dict[str, Any]]:
    """Проверка публичных сообщений канала через t.me"""
    
    # Убираем @ если есть
    username = channel_username.replace('@', '')
    
    # URL для публичной страницы канала
    url = f"https://t.me/s/{username}"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    html = await response.text()
                    return parse_telegram_messages(html, channel_username)
                else:
                    print(f"❌ Ошибка {response.status} для {channel_username}")
                    return []
    except Exception as e:
        print(f"❌ Ошибка при проверке {channel_username}: {e}")
        return []

def parse_telegram_messages(html: str, channel_username: str) -> List[Dict[str, Any]]:
    """Парсинг сообщений из HTML"""
    
    soup = BeautifulSoup(html, 'html.parser')
    messages = []
    
    # Ищем сообщения
    message_elements = soup.find_all('div', class_='tgme_widget_message')
    
    for msg in message_elements[:5]:  # Берем последние 5 сообщений
        try:
            # Извлекаем текст сообщения
            text_elem = msg.find('div', class_='tgme_widget_message_text')
            if text_elem:
                text = text_elem.get_text(strip=True)
                
                # Извлекаем время
                time_elem = msg.find('time')
                timestamp = None
                if time_elem and time_elem.get('datetime'):
                    timestamp = time_elem.get('datetime')
                
                # Извлекаем дату
                date_elem = msg.find('a', class_='tgme_widget_message_date')
                date_str = None
                if date_elem:
                    date_str = date_elem.get_text(strip=True)
                
                if text and len(text) > 10:  # Фильтруем короткие сообщения
                    messages.append({
                        'channel': channel_username,
                        'text': text,
                        'timestamp': timestamp,
                        'date_str': date_str,
                        'length': len(text)
                    })
        except Exception as e:
            print(f"⚠️ Ошибка парсинга сообщения: {e}")
            continue
    
    return messages

def check_for_trading_signals(text: str) -> bool:
    """Проверка, содержит ли текст торговые сигналы"""
    
    # Паттерны для торговых сигналов
    signal_patterns = [
        r'\b(BTC|ETH|SOL|DOGE|ADA|XRP|BNB|MATIC|LINK|UNI)\b',
        r'\b(LONG|SHORT|BUY|SELL)\b',
        r'\b(Entry|Target|TP|SL|Stop Loss)\b',
        r'\$[\d,]+',
        r'\b\d+\.?\d*\b',
        r'🚀|📈|📉|🎯|🛑'
    ]
    
    text_upper = text.upper()
    
    # Проверяем наличие хотя бы 2 паттернов
    matches = 0
    for pattern in signal_patterns:
        if re.search(pattern, text_upper):
            matches += 1
    
    return matches >= 2

async def check_multiple_channels():
    """Проверка нескольких каналов"""
    
    # Список каналов для проверки
    channels = [
        "binancekillers",
        "CryptoCapoTG", 
        "io_altsignals",
        "Wolf_of_Trading_singals",
        "fatpigsignals",
        "Signals_BTC_ETH"
    ]
    
    print("🔍 ПРОВЕРКА РЕАЛЬНЫХ СИГНАЛОВ С TELEGRAM КАНАЛОВ")
    print("="*80)
    print(f"🕐 Время проверки: {datetime.now().strftime('%d.%m.%Y в %H:%M:%S')}")
    print("="*80)
    
    all_messages = []
    
    for channel in channels:
        print(f"\n📺 Проверяем канал: @{channel}")
        messages = await check_telegram_web(channel)
        
        if messages:
            print(f"✅ Найдено сообщений: {len(messages)}")
            
            # Проверяем на торговые сигналы
            signal_messages = []
            for msg in messages:
                if check_for_trading_signals(msg['text']):
                    signal_messages.append(msg)
            
            if signal_messages:
                print(f"🎯 Найдено сигналов: {len(signal_messages)}")
                all_messages.extend(signal_messages)
                
                # Показываем последний сигнал
                latest = signal_messages[0]
                print(f"📝 Последний сигнал:")
                print(f"   Время: {latest.get('date_str', 'N/A')}")
                print(f"   Текст: {latest['text'][:100]}...")
            else:
                print("❌ Торговых сигналов не найдено")
        else:
            print("❌ Сообщения не найдены или канал недоступен")
    
    # Итоговая статистика
    print(f"\n{'='*80}")
    print(f"📊 ИТОГОВАЯ СТАТИСТИКА")
    print(f"{'='*80}")
    
    if all_messages:
        print(f"🎯 Всего найдено сигналов: {len(all_messages)}")
        
        # Показываем все найденные сигналы
        for i, msg in enumerate(all_messages, 1):
            print(f"\n🔍 СИГНАЛ #{i}")
            print(f"📺 Канал: @{msg['channel']}")
            print(f"⏰ Время: {msg.get('date_str', 'N/A')}")
            print(f"📝 Текст: {msg['text']}")
            print(f"📏 Длина: {msg['length']} символов")
    else:
        print("❌ Торговых сигналов не найдено ни на одном канале")
        print("💡 Возможные причины:")
        print("   - Каналы приватные")
        print("   - Нет публичных сообщений")
        print("   - Сигналы в изображениях")
        print("   - Каналы заблокированы")

def check_alternative_sources():
    """Проверка альтернативных источников"""
    
    print(f"\n{'='*80}")
    print(f"🔍 АЛЬТЕРНАТИВНЫЕ СПОСОБЫ ПРОВЕРКИ")
    print(f"{'='*80}")
    
    print("1. 📱 Telegram Web (t.me/s/):")
    print("   - Открыть в браузере: https://t.me/s/binancekillers")
    print("   - Проверить последние сообщения")
    
    print("\n2. 🔍 Поиск в интернете:")
    print("   - Google: 'binancekillers telegram signals'")
    print("   - Twitter/X: поиск по хештегам")
    
    print("\n3. 📊 Криптобиржи:")
    print("   - Проверить актуальные цены BTC, ETH")
    print("   - Сравнить с ценами в сигналах")
    
    print("\n4. 🤖 Telegram API (если есть доступ):")
    print("   - Использовать Telethon для авторизованного доступа")
    print("   - Получить реальные сообщения")

async def main():
    """Основная функция"""
    
    print("🚨 ВНИМАНИЕ: Проверяем РЕАЛЬНЫЕ данные с каналов!")
    print("Это может занять некоторое время...")
    
    # Проверяем реальные каналы
    await check_multiple_channels()
    
    # Показываем альтернативные способы
    check_alternative_sources()
    
    print(f"\n{'='*80}")
    print(f"💡 РЕКОМЕНДАЦИИ")
    print(f"{'='*80}")
    print("1. Проверьте каналы вручную в Telegram")
    print("2. Используйте публичные веб-страницы каналов")
    print("3. Рассмотрите использование Telegram API")
    print("4. Проверьте актуальность цен на биржах")

if __name__ == "__main__":
    asyncio.run(main())
