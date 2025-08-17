#!/usr/bin/env python3
"""
Улучшенный анализатор каналов с детальной информацией и фильтрацией
"""

import asyncio
import aiohttp
import json
import sys
import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional, Set
from bs4 import BeautifulSoup
import logging

# Добавляем пути для импортов
sys.path.append(str(Path(__file__).parent))

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedChannelAnalyzer:
    """Улучшенный анализатор каналов"""
    
    def __init__(self):
        self.analyzed_channels = []
        self.channel_categories = {
            'signals': [],
            'news': [],
            'analysis': [],
            'educational': [],
            'mixed': []
        }
        
        # Приоритетные каналы для мониторинга
        self.priority_channels = [
            "binancekillers", "CryptoCapoTG", "io_altsignals", 
            "fatpigsignals", "cryptoceo_alex", "Wolf_of_Trading_singals"
        ]
    
    async def analyze_channel_detailed(self, channel_username: str) -> Optional[Dict[str, Any]]:
        """Детальный анализ канала"""
        
        try:
            # Проверяем статус канала
            is_active = await self.check_channel_status(channel_username)
            if not is_active:
                return None
            
            # Получаем детальную информацию
            channel_info = await self.get_detailed_channel_info(channel_username)
            if not channel_info:
                return None
            
            # Анализируем активность
            activity_info = await self.analyze_channel_activity(channel_username)
            channel_info.update(activity_info)
            
            # Определяем приоритет
            channel_info['priority'] = self.calculate_priority(channel_info)
            
            # Классифицируем контент
            channel_info['content_quality'] = self.assess_content_quality(channel_info)
            
            return channel_info
            
        except Exception as e:
            logger.error(f"Ошибка анализа канала {channel_username}: {e}")
            return None
    
    async def check_channel_status(self, channel_username: str) -> bool:
        """Проверка статуса канала"""
        
        username = channel_username.replace('@', '')
        url = f"https://t.me/s/{username}"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    return response.status == 200
        except:
            return False
    
    async def get_detailed_channel_info(self, channel_username: str) -> Optional[Dict[str, Any]]:
        """Получение детальной информации о канале"""
        
        username = channel_username.replace('@', '')
        url = f"https://t.me/{username}"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        html = await response.text()
                        return self.parse_detailed_channel_info(html, channel_username)
        except Exception as e:
            logger.error(f"Ошибка получения информации о канале {channel_username}: {e}")
        
        return None
    
    def parse_detailed_channel_info(self, html: str, channel_username: str) -> Dict[str, Any]:
        """Парсинг детальной информации о канале"""
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # Извлекаем название канала
        title_elem = soup.find('div', class_='tgme_channel_info_header_title')
        title = title_elem.get_text(strip=True) if title_elem else channel_username
        
        # Извлекаем описание
        description_elem = soup.find('div', class_='tgme_channel_info_description')
        description = description_elem.get_text(strip=True) if description_elem else ""
        
        # Извлекаем количество подписчиков
        subscribers_elem = soup.find('div', class_='tgme_channel_info_counter')
        subscribers_text = subscribers_elem.get_text(strip=True) if subscribers_elem else "N/A"
        
        # Парсим количество подписчиков
        subscribers_count = self.parse_subscribers_count(subscribers_text)
        
        # Определяем тип контента
        content_type = self.classify_channel_content(description, title)
        
        # Извлекаем аватар
        avatar_elem = soup.find('img', class_='tgme_channel_info_header_photo')
        avatar_url = avatar_elem.get('src') if avatar_elem else None
        
        return {
            'username': channel_username,
            'title': title,
            'description': description,
            'subscribers_text': subscribers_text,
            'subscribers_count': subscribers_count,
            'content_type': content_type,
            'platform': 'telegram',
            'url': f"https://t.me/{channel_username.replace('@', '')}",
            'avatar_url': avatar_url,
            'analyzed_at': datetime.now().isoformat(),
            'is_active': True
        }
    
    def parse_subscribers_count(self, subscribers_text: str) -> int:
        """Парсинг количества подписчиков"""
        
        if not subscribers_text or subscribers_text == "N/A":
            return 0
        
        # Убираем лишние символы
        clean_text = re.sub(r'[^\d]', '', subscribers_text)
        
        try:
            return int(clean_text) if clean_text else 0
        except:
            return 0
    
    def classify_channel_content(self, description: str, title: str) -> str:
        """Классификация типа контента канала"""
        
        text = f"{title} {description}".lower()
        
        # Паттерны для классификации
        signal_patterns = ['signal', 'trade', 'trading', 'buy', 'sell', 'long', 'short', 'entry', 'target', 'tp', 'sl']
        news_patterns = ['news', 'update', 'announcement', 'breaking', 'latest', 'alert']
        analysis_patterns = ['analysis', 'technical', 'fundamental', 'chart', 'price', 'market', 'trend']
        educational_patterns = ['learn', 'education', 'tutorial', 'guide', 'how to', 'course', 'academy']
        
        # Подсчитываем совпадения
        signal_score = sum(1 for pattern in signal_patterns if pattern in text)
        news_score = sum(1 for pattern in news_patterns if pattern in text)
        analysis_score = sum(1 for pattern in analysis_patterns if pattern in text)
        educational_score = sum(1 for pattern in educational_patterns if pattern in text)
        
        # Определяем доминирующий тип
        scores = {
            'signals': signal_score,
            'news': news_score,
            'analysis': analysis_score,
            'educational': educational_score
        }
        
        max_score = max(scores.values())
        if max_score == 0:
            return 'mixed'
        
        # Возвращаем тип с максимальным количеством совпадений
        for content_type, score in scores.items():
            if score == max_score:
                return content_type
        
        return 'mixed'
    
    async def analyze_channel_activity(self, channel_username: str) -> Dict[str, Any]:
        """Анализ активности канала"""
        
        username = channel_username.replace('@', '')
        url = f"https://t.me/s/{username}"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        html = await response.text()
                        return self.parse_channel_activity(html)
        except Exception as e:
            logger.error(f"Ошибка анализа активности канала {channel_username}: {e}")
        
        return {
            'recent_messages': 0,
            'last_message_date': None,
            'activity_level': 'unknown',
            'has_images': False,
            'has_links': False
        }
    
    def parse_channel_activity(self, html: str) -> Dict[str, Any]:
        """Парсинг активности канала"""
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # Ищем сообщения
        messages = soup.find_all('div', class_='tgme_widget_message')
        
        recent_messages = len(messages)
        
        # Анализируем последнее сообщение
        last_message_date = None
        has_images = False
        has_links = False
        
        if messages:
            last_message = messages[0]  # Первое сообщение - самое новое
            
            # Дата последнего сообщения
            time_elem = last_message.find('time')
            if time_elem and time_elem.get('datetime'):
                last_message_date = time_elem.get('datetime')
            
            # Проверяем наличие изображений
            img_elements = last_message.find_all('img', class_='tgme_widget_message_photo_wrap')
            has_images = len(img_elements) > 0
            
            # Проверяем наличие ссылок
            link_elements = last_message.find_all('a')
            has_links = len(link_elements) > 0
        
        # Определяем уровень активности
        if recent_messages >= 20:
            activity_level = 'high'
        elif recent_messages >= 10:
            activity_level = 'medium'
        elif recent_messages >= 5:
            activity_level = 'low'
        else:
            activity_level = 'very_low'
        
        return {
            'recent_messages': recent_messages,
            'last_message_date': last_message_date,
            'activity_level': activity_level,
            'has_images': has_images,
            'has_links': has_links
        }
    
    def calculate_priority(self, channel_info: Dict[str, Any]) -> int:
        """Расчет приоритета канала"""
        
        priority = 1
        
        # Приоритетные каналы
        if channel_info['username'] in self.priority_channels:
            priority += 10
        
        # По количеству подписчиков
        subscribers = channel_info.get('subscribers_count', 0)
        if subscribers > 100000:
            priority += 5
        elif subscribers > 10000:
            priority += 3
        elif subscribers > 1000:
            priority += 1
        
        # По типу контента
        content_type = channel_info.get('content_type', 'mixed')
        if content_type == 'signals':
            priority += 3
        elif content_type == 'analysis':
            priority += 2
        elif content_type == 'news':
            priority += 1
        
        # По активности
        activity_level = channel_info.get('activity_level', 'unknown')
        if activity_level == 'high':
            priority += 3
        elif activity_level == 'medium':
            priority += 2
        elif activity_level == 'low':
            priority += 1
        
        return priority
    
    def assess_content_quality(self, channel_info: Dict[str, Any]) -> str:
        """Оценка качества контента"""
        
        score = 0
        
        # По количеству подписчиков
        subscribers = channel_info.get('subscribers_count', 0)
        if subscribers > 50000:
            score += 3
        elif subscribers > 10000:
            score += 2
        elif subscribers > 1000:
            score += 1
        
        # По активности
        activity_level = channel_info.get('activity_level', 'unknown')
        if activity_level == 'high':
            score += 2
        elif activity_level == 'medium':
            score += 1
        
        # По типу контента
        content_type = channel_info.get('content_type', 'mixed')
        if content_type == 'signals':
            score += 2
        elif content_type == 'analysis':
            score += 1
        
        # Определяем качество
        if score >= 5:
            return 'excellent'
        elif score >= 3:
            return 'good'
        elif score >= 1:
            return 'average'
        else:
            return 'poor'
    
    async def analyze_channels_list(self, channels_list: List[str]) -> List[Dict[str, Any]]:
        """Анализ списка каналов"""
        
        print("🔍 ДЕТАЛЬНЫЙ АНАЛИЗ КАНАЛОВ")
        print("="*100)
        print(f"🕐 Время начала: {datetime.now().strftime('%d.%m.%Y в %H:%M:%S')}")
        print("="*100)
        
        analyzed_channels = []
        
        for i, channel in enumerate(channels_list, 1):
            print(f"\n📺 Анализируем канал {i}/{len(channels_list)}: @{channel}")
            
            channel_analysis = await self.analyze_channel_detailed(channel)
            if channel_analysis:
                analyzed_channels.append(channel_analysis)
                
                # Показываем краткую информацию
                subscribers = channel_analysis.get('subscribers_count', 0)
                content_type = channel_analysis.get('content_type', 'mixed')
                activity = channel_analysis.get('activity_level', 'unknown')
                priority = channel_analysis.get('priority', 1)
                quality = channel_analysis.get('content_quality', 'poor')
                
                print(f"   ✅ АКТИВЕН - {subscribers} подписчиков")
                print(f"   📝 Тип: {content_type} | Активность: {activity}")
                print(f"   🎯 Приоритет: {priority} | Качество: {quality}")
            else:
                print(f"   ❌ Неактивен или недоступен")
        
        return analyzed_channels
    
    def categorize_channels(self, channels: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Категоризация каналов"""
        
        categorized = {
            'signals': [],
            'news': [],
            'analysis': [],
            'educational': [],
            'mixed': []
        }
        
        for channel in channels:
            content_type = channel.get('content_type', 'mixed')
            if content_type in categorized:
                categorized[content_type].append(channel)
            else:
                categorized['mixed'].append(channel)
        
        return categorized
    
    def sort_channels_by_priority(self, channels: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Сортировка каналов по приоритету"""
        
        return sorted(channels, key=lambda x: x.get('priority', 1), reverse=True)
    
    async def create_enhanced_report(self, channels: List[Dict[str, Any]]):
        """Создание улучшенного отчета"""
        
        # Сортируем по приоритету
        sorted_channels = self.sort_channels_by_priority(channels)
        
        # Категоризируем
        categorized = self.categorize_channels(channels)
        
        # Создаем отчет
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_filename = f"enhanced_channel_report_{timestamp}.md"
        
        with open(report_filename, 'w', encoding='utf-8') as f:
            f.write("# 📊 УЛУЧШЕННЫЙ ОТЧЕТ О КАНАЛАХ\n\n")
            f.write(f"**Дата:** {datetime.now().strftime('%d.%m.%Y в %H:%M:%S')}\n")
            f.write(f"**Всего каналов:** {len(channels)}\n\n")
            
            # Общая статистика
            f.write("## 📈 ОБЩАЯ СТАТИСТИКА\n\n")
            
            total_subscribers = sum(c.get('subscribers_count', 0) for c in channels)
            f.write(f"- **Общее количество подписчиков:** {total_subscribers:,}\n")
            
            avg_priority = sum(c.get('priority', 1) for c in channels) / len(channels)
            f.write(f"- **Средний приоритет:** {avg_priority:.1f}\n")
            
            quality_distribution = {}
            for channel in channels:
                quality = channel.get('content_quality', 'poor')
                quality_distribution[quality] = quality_distribution.get(quality, 0) + 1
            
            f.write("- **Распределение по качеству:**\n")
            for quality, count in quality_distribution.items():
                f.write(f"  - {quality}: {count} каналов\n")
            
            # Топ каналы по приоритету
            f.write("\n## 🏆 ТОП-10 КАНАЛОВ ПО ПРИОРИТЕТУ\n\n")
            for i, channel in enumerate(sorted_channels[:10], 1):
                f.write(f"### {i}. {channel['username']}\n")
                f.write(f"- **Название:** {channel['title']}\n")
                f.write(f"- **Подписчики:** {channel.get('subscribers_count', 0):,}\n")
                f.write(f"- **Тип контента:** {channel.get('content_type', 'mixed')}\n")
                f.write(f"- **Приоритет:** {channel.get('priority', 1)}\n")
                f.write(f"- **Качество:** {channel.get('content_quality', 'poor')}\n")
                f.write(f"- **Активность:** {channel.get('activity_level', 'unknown')}\n")
                f.write(f"- **URL:** {channel['url']}\n")
                f.write(f"- **Описание:** {channel['description'][:150]}...\n\n")
            
            # Категории
            for category, category_channels in categorized.items():
                if category_channels:
                    f.write(f"## {category.upper()}\n")
                    f.write(f"**Количество каналов:** {len(category_channels)}\n\n")
                    
                    # Сортируем каналы в категории по приоритету
                    sorted_category = self.sort_channels_by_priority(category_channels)
                    
                    for channel in sorted_category[:5]:  # Показываем топ-5 в каждой категории
                        f.write(f"### {channel['username']}\n")
                        f.write(f"- **Приоритет:** {channel.get('priority', 1)}\n")
                        f.write(f"- **Подписчики:** {channel.get('subscribers_count', 0):,}\n")
                        f.write(f"- **Качество:** {channel.get('content_quality', 'poor')}\n\n")
        
        print(f"\n📋 Улучшенный отчет создан: {report_filename}")
        return report_filename

async def main():
    """Основная функция"""
    
    print("🚀 ЗАПУСК УЛУЧШЕННОГО АНАЛИЗАТОРА КАНАЛОВ")
    
    # Список каналов для анализа
    channels_to_analyze = [
        "binancekillers", "CryptoCapoTG", "io_altsignals", 
        "Wolf_of_Trading_singals", "fatpigsignals", "Signals_BTC_ETH",
        "cryptoceo_alex", "Crypto_Futures_Signals", "TradingViewIdeas",
        "Crypto_Inner_Circler", "CryptoSignalsPro", "BitcoinSignals",
        "AltcoinSignals", "FuturesSignals", "SpotSignals"
    ]
    
    analyzer = EnhancedChannelAnalyzer()
    analyzed_channels = await analyzer.analyze_channels_list(channels_to_analyze)
    
    if analyzed_channels:
        # Создаем улучшенный отчет
        report_filename = await analyzer.create_enhanced_report(analyzed_channels)
        
        # Итоговая статистика
        print(f"\n{'='*100}")
        print(f"📊 ИТОГОВАЯ СТАТИСТИКА")
        print(f"{'='*100}")
        
        total_subscribers = sum(c.get('subscribers_count', 0) for c in analyzed_channels)
        avg_priority = sum(c.get('priority', 1) for c in analyzed_channels) / len(analyzed_channels)
        
        print(f"📺 Проанализировано каналов: {len(analyzed_channels)}")
        print(f"👥 Общее количество подписчиков: {total_subscribers:,}")
        print(f"🎯 Средний приоритет: {avg_priority:.1f}")
        
        # Показываем топ-5 по приоритету
        sorted_channels = analyzer.sort_channels_by_priority(analyzed_channels)
        print(f"\n🏆 ТОП-5 КАНАЛОВ ПО ПРИОРИТЕТУ:")
        for i, channel in enumerate(sorted_channels[:5], 1):
            print(f"   {i}. @{channel['username']} - Приоритет: {channel.get('priority', 1)}")
        
        print(f"\n✅ Анализ завершен! Отчет: {report_filename}")
    else:
        print("❌ Не удалось проанализировать ни одного канала")

if __name__ == "__main__":
    asyncio.run(main())
