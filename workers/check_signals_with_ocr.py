#!/usr/bin/env python3
"""
Интегрированный скрипт для проверки сигналов с OCR из изображений
"""

import asyncio
import aiohttp
import json
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
import re
import base64
import io

# Добавляем пути для импортов
sys.path.append(str(Path(__file__).parent))

# Импорты OCR
try:
    import easyocr
    import cv2
    import numpy as np
    from PIL import Image, ImageEnhance, ImageFilter
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    print("⚠️ OCR библиотеки не установлены. Установите: pip install easyocr opencv-python pillow")

async def check_telegram_web_with_images(channel_username: str, max_messages: int = 20) -> List[Dict[str, Any]]:
    """Проверка публичных сообщений канала с изображениями"""
    
    # Убираем @ если есть
    username = channel_username.replace('@', '')
    
    # URL для публичной страницы канала
    url = f"https://t.me/s/{username}"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=15) as response:
                if response.status == 200:
                    html = await response.text()
                    return parse_telegram_messages_with_images(html, channel_username, max_messages)
                else:
                    print(f"❌ Ошибка {response.status} для {channel_username}")
                    return []
    except Exception as e:
        print(f"❌ Ошибка при проверке {channel_username}: {e}")
        return []

def parse_telegram_messages_with_images(html: str, channel_username: str, max_messages: int) -> List[Dict[str, Any]]:
    """Парсинг сообщений с изображениями"""
    
    soup = BeautifulSoup(html, 'html.parser')
    messages = []
    
    # Ищем сообщения
    message_elements = soup.find_all('div', class_='tgme_widget_message')
    
    for msg in message_elements[:max_messages]:
        try:
            # Извлекаем текст сообщения
            text_elem = msg.find('div', class_='tgme_widget_message_text')
            text = text_elem.get_text(strip=True) if text_elem else ""
            
            # Извлекаем изображения
            images = []
            img_elements = msg.find_all('img', class_='tgme_widget_message_photo_wrap')
            for img in img_elements:
                img_src = img.get('src')
                if img_src:
                    images.append(img_src)
            
            # Извлекаем полную дату и время
            time_elem = msg.find('time')
            full_datetime = None
            if time_elem and time_elem.get('datetime'):
                full_datetime = time_elem.get('datetime')
            
            # Извлекаем ID сообщения
            message_id = None
            message_link = msg.find('a', class_='tgme_widget_message_date')
            if message_link and message_link.get('href'):
                href = message_link.get('href')
                if '/' in href:
                    message_id = href.split('/')[-1]
            
            if text or images:  # Сообщение с текстом или изображениями
                messages.append({
                    'channel': channel_username,
                    'text': text,
                    'images': images,
                    'full_datetime': full_datetime,
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

class SimpleOCRProcessor:
    """Простой OCR процессор для изображений"""
    
    def __init__(self):
        self.reader = None
        if OCR_AVAILABLE:
            try:
                # Инициализация EasyOCR
                self.reader = easyocr.Reader(['en', 'ru'], gpu=False)
                print("✅ OCR инициализирован успешно")
            except Exception as e:
                print(f"❌ Ошибка инициализации OCR: {e}")
                self.reader = None
    
    async def download_image(self, image_url: str) -> Optional[bytes]:
        """Загрузка изображения по URL"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(image_url, timeout=10) as response:
                    if response.status == 200:
                        return await response.read()
        except Exception as e:
            print(f"❌ Ошибка загрузки изображения: {e}")
        return None
    
    def extract_text_from_image(self, image_data: bytes) -> List[str]:
        """Извлечение текста из изображения"""
        if not self.reader:
            return []
        
        try:
            # Конвертируем bytes в numpy array
            nparr = np.frombuffer(image_data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            # Извлекаем текст
            results = self.reader.readtext(img)
            
            # Собираем текст
            texts = []
            for (bbox, text, prob) in results:
                if prob > 0.5:  # Фильтруем по уверенности
                    texts.append(text.strip())
            
            return texts
        except Exception as e:
            print(f"❌ Ошибка OCR: {e}")
            return []
    
    def check_for_trading_signals(self, texts: List[str]) -> List[Dict[str, Any]]:
        """Проверка текста на торговые сигналы"""
        signals = []
        
        # Паттерны для торговых сигналов
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
        
        for text in texts:
            text_upper = text.upper()
            
            # Проверяем наличие хотя бы 2 паттернов
            matches = 0
            for pattern in signal_patterns:
                if re.search(pattern, text_upper):
                    matches += 1
            
            if matches >= 2:
                signals.append({
                    'text': text,
                    'confidence': matches,
                    'patterns_found': matches
                })
        
        return signals

async def process_messages_with_ocr(messages: List[Dict[str, Any]], ocr_processor: SimpleOCRProcessor) -> List[Dict[str, Any]]:
    """Обработка сообщений с OCR"""
    
    processed_messages = []
    
    for msg in messages:
        processed_msg = msg.copy()
        ocr_signals = []
        
        # Обрабатываем изображения
        if msg.get('images'):
            print(f"🖼️ Обрабатываем {len(msg['images'])} изображений...")
            
            for i, image_url in enumerate(msg['images']):
                try:
                    # Загружаем изображение
                    image_data = await ocr_processor.download_image(image_url)
                    if image_data:
                        # Извлекаем текст
                        texts = ocr_processor.extract_text_from_image(image_data)
                        if texts:
                            print(f"   📝 Изображение {i+1}: найдено {len(texts)} текстовых блоков")
                            
                            # Проверяем на сигналы
                            signals = ocr_processor.check_for_trading_signals(texts)
                            if signals:
                                print(f"   🎯 Изображение {i+1}: найдено {len(signals)} сигналов!")
                                ocr_signals.extend(signals)
                        else:
                            print(f"   ❌ Изображение {i+1}: текст не найден")
                    else:
                        print(f"   ❌ Изображение {i+1}: не удалось загрузить")
                except Exception as e:
                    print(f"   ❌ Ошибка обработки изображения {i+1}: {e}")
        
        # Добавляем OCR сигналы к сообщению
        if ocr_signals:
            processed_msg['ocr_signals'] = ocr_signals
            processed_messages.append(processed_msg)
        else:
            processed_messages.append(processed_msg)
    
    return processed_messages

async def check_channels_with_ocr():
    """Проверка каналов с OCR"""
    
    # Список каналов для проверки
    channels = [
        "binancekillers",
        "CryptoCapoTG", 
        "io_altsignals",
        "fatpigsignals",
        "cryptoceo_alex"
    ]
    
    print("🔍 ПРОВЕРКА СИГНАЛОВ С OCR ИЗ ИЗОБРАЖЕНИЙ")
    print("="*120)
    print(f"🕐 Время проверки: {datetime.now().strftime('%d.%m.%Y в %H:%M:%S')}")
    print("="*120)
    
    # Инициализация OCR
    ocr_processor = SimpleOCRProcessor()
    if not ocr_processor.reader:
        print("❌ OCR недоступен, продолжаем без обработки изображений")
    
    all_signals = []
    
    for channel in channels:
        print(f"\n📺 Проверяем канал: @{channel}")
        messages = await check_telegram_web_with_images(channel, max_messages=10)
        
        if messages:
            print(f"✅ Найдено сообщений: {len(messages)}")
            
            # Обрабатываем с OCR
            processed_messages = await process_messages_with_ocr(messages, ocr_processor)
            
            # Ищем свежие сигналы (за последние 3 дня)
            recent_signals = []
            for msg in processed_messages:
                if msg.get('full_datetime'):
                    try:
                        dt = datetime.fromisoformat(msg['full_datetime'].replace('Z', '+00:00'))
                        now = datetime.now(dt.tzinfo)
                        diff = now - dt
                        
                        if diff.days <= 3:
                            # Проверяем текст сообщения
                            if msg.get('text') and len(msg['text']) > 10:
                                recent_signals.append(msg)
                            
                            # Проверяем OCR сигналы
                            if msg.get('ocr_signals'):
                                recent_signals.append(msg)
                    except:
                        continue
            
            if recent_signals:
                print(f"🎯 Найдено свежих сообщений: {len(recent_signals)}")
                all_signals.extend(recent_signals)
                
                # Показываем результаты
                for i, signal in enumerate(recent_signals, 1):
                    formatted_date = format_datetime(signal.get('full_datetime'))
                    print(f"   {i}. {formatted_date}")
                    print(f"      ID: {signal.get('message_id', 'N/A')}")
                    if signal.get('text'):
                        print(f"      Текст: {signal['text'][:80]}...")
                    if signal.get('images'):
                        print(f"      Изображения: {len(signal['images'])}")
                    if signal.get('ocr_signals'):
                        print(f"      OCR сигналы: {len(signal['ocr_signals'])}")
                        for j, ocr_signal in enumerate(signal['ocr_signals'], 1):
                            print(f"         {j}. {ocr_signal['text'][:60]}...")
            else:
                print("❌ Свежих сигналов не найдено")
        else:
            print("❌ Сообщения не найдены или канал недоступен")
    
    # Итоговая статистика
    print(f"\n{'='*120}")
    print(f"📊 ИТОГОВАЯ СТАТИСТИКА")
    print(f"{'='*120}")
    
    if all_signals:
        print(f"🎯 Всего найдено сообщений: {len(all_signals)}")
        
        # Сортируем по дате (новые сначала)
        all_signals.sort(key=lambda x: x.get('full_datetime', ''), reverse=True)
        
        # Показываем все найденные сигналы
        for i, msg in enumerate(all_signals, 1):
            formatted_date = format_datetime(msg.get('full_datetime'))
            print(f"\n🔍 СИГНАЛ #{i}")
            print(f"📺 Канал: @{msg['channel']}")
            print(f"⏰ Дата: {formatted_date}")
            print(f"🆔 ID: {msg.get('message_id', 'N/A')}")
            if msg.get('text'):
                print(f"📝 Текст: {msg['text']}")
            if msg.get('images'):
                print(f"🖼️ Изображения: {len(msg['images'])}")
            if msg.get('ocr_signals'):
                print(f"🎯 OCR сигналы:")
                for j, ocr_signal in enumerate(msg['ocr_signals'], 1):
                    print(f"   {j}. {ocr_signal['text']}")
    else:
        print("❌ Свежих сигналов не найдено ни на одном канале")

async def main():
    """Основная функция"""
    
    print("🚨 ПРОВЕРКА СИГНАЛОВ С OCR ИЗ ИЗОБРАЖЕНИЙ!")
    print("Активируем OCR для поиска сигналов в изображениях...")
    
    await check_channels_with_ocr()
    
    print(f"\n{'='*120}")
    print(f"💡 РЕЗУЛЬТАТЫ")
    print(f"{'='*120}")
    print("1. ✅ OCR активирован для изображений")
    print("2. 🔍 Поиск сигналов в тексте и изображениях")
    print("3. 📅 Фильтрация по свежести (3 дня)")
    print("4. 🎯 Извлечение структурированных данных")

if __name__ == "__main__":
    asyncio.run(main())
