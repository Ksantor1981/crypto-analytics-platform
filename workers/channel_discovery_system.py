#!/usr/bin/env python3
"""
Комплексная система обнаружения и сбора активных каналов со всех ресурсов
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

class ChannelDiscoverySystem:
    """Система обнаружения каналов со всех ресурсов"""
    
    def __init__(self):
        self.discovered_channels = set()
        self.active_channels = []
        self.channel_sources = {
            'telegram': [],
            'reddit': [],
            'discord': [],  # Для будущего использования
            'twitter': [],  # Для будущего использования
            'youtube': []   # Для будущего использования
        }
        
        # Известные каналы из разных источников
        self.known_channels = {
            'telegram': [
                # Основные сигнальные каналы
                "binancekillers", "CryptoCapoTG", "io_altsignals", 
                "Wolf_of_Trading_singals", "fatpigsignals", "Signals_BTC_ETH",
                "cryptoceo_alex", "Crypto_Futures_Signals", "TradingViewIdeas",
                "Crypto_Inner_Circler", "CryptoSignalsPro", "BitcoinSignals",
                "AltcoinSignals", "FuturesSignals", "SpotSignals",
                
                # Аналитические каналы
                "CryptoCompass", "TradingView", "CoinDesk", "CoinTelegraph",
                "CryptoNews", "BitcoinNews", "EthereumNews", "AltcoinNews",
                
                # VIP и премиум каналы
                "VIP_Crypto_Signals", "PremiumSignals", "EliteTraders",
                "CryptoMasters", "TradingElite", "SignalMasters",
                
                # Новостные каналы
                "CryptoNews", "BitcoinNews", "EthereumNews", "AltcoinNews",
                "DeFiNews", "NFTNews", "MetaverseNews", "Web3News",
                
                # Образовательные каналы
                "CryptoTutorials", "TradingEducation", "CryptoAcademy",
                "BlockchainBasics", "DeFiEducation", "NFTEducation"
            ],
            'reddit': [
                # Основные subreddit'ы
                "CryptoCurrency", "Bitcoin", "Ethereum", "CryptoMarkets",
                "CryptoMoonShots", "CryptoCurrencyTrading", "CryptoSignals",
                "BitcoinMarkets", "EthereumMarkets", "AltcoinMarkets",
                
                # Торговые subreddit'ы
                "CryptoCurrencyTrading", "CryptoSignals", "CryptoMoonShots",
                "CryptoCurrency", "BitcoinMarkets", "EthereumMarkets",
                "AltcoinMarkets", "CryptoCurrencyTrading", "CryptoSignals",
                
                # Новостные subreddit'ы
                "CryptoNews", "BitcoinNews", "EthereumNews", "AltcoinNews",
                "DeFiNews", "NFTNews", "MetaverseNews", "Web3News"
            ]
        }
    
    async def discover_telegram_channels(self) -> List[Dict[str, Any]]:
        """Обнаружение активных Telegram каналов"""
        
        print("🔍 ОБНАРУЖЕНИЕ TELEGRAM КАНАЛОВ")
        print("="*80)
        
        discovered_channels = []
        
        # Проверяем известные каналы
        for channel in self.known_channels['telegram']:
            try:
                is_active = await self.check_telegram_channel_status(channel)
                if is_active:
                    channel_info = await self.get_telegram_channel_info(channel)
                    if channel_info:
                        discovered_channels.append(channel_info)
                        print(f"✅ @{channel}: АКТИВЕН - {channel_info.get('subscribers', 'N/A')} подписчиков")
                    else:
                        print(f"⚠️ @{channel}: Доступен, но информация не получена")
                else:
                    print(f"❌ @{channel}: Неактивен или недоступен")
            except Exception as e:
                print(f"❌ @{channel}: Ошибка проверки - {e}")
        
        # Поиск новых каналов через рекомендации
        new_channels = await self.find_telegram_recommendations(discovered_channels)
        discovered_channels.extend(new_channels)
        
        return discovered_channels
    
    async def check_telegram_channel_status(self, channel_username: str) -> bool:
        """Проверка статуса Telegram канала"""
        
        username = channel_username.replace('@', '')
        url = f"https://t.me/s/{username}"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    return response.status == 200
        except:
            return False
    
    async def get_telegram_channel_info(self, channel_username: str) -> Optional[Dict[str, Any]]:
        """Получение информации о Telegram канале"""
        
        username = channel_username.replace('@', '')
        url = f"https://t.me/{username}"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        html = await response.text()
                        return self.parse_telegram_channel_info(html, channel_username)
        except Exception as e:
            logger.error(f"Ошибка получения информации о канале {channel_username}: {e}")
        
        return None
    
    def parse_telegram_channel_info(self, html: str, channel_username: str) -> Dict[str, Any]:
        """Парсинг информации о канале"""
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # Извлекаем название канала
        title_elem = soup.find('div', class_='tgme_channel_info_header_title')
        title = title_elem.get_text(strip=True) if title_elem else channel_username
        
        # Извлекаем описание
        description_elem = soup.find('div', class_='tgme_channel_info_description')
        description = description_elem.get_text(strip=True) if description_elem else ""
        
        # Извлекаем количество подписчиков
        subscribers_elem = soup.find('div', class_='tgme_channel_info_counter')
        subscribers = subscribers_elem.get_text(strip=True) if subscribers_elem else "N/A"
        
        # Определяем тип контента
        content_type = self.classify_channel_content(description, title)
        
        return {
            'username': channel_username,
            'title': title,
            'description': description,
            'subscribers': subscribers,
            'content_type': content_type,
            'platform': 'telegram',
            'url': f"https://t.me/{channel_username.replace('@', '')}",
            'discovered_at': datetime.now().isoformat(),
            'is_active': True
        }
    
    def classify_channel_content(self, description: str, title: str) -> str:
        """Классификация типа контента канала"""
        
        text = f"{title} {description}".lower()
        
        # Паттерны для классификации
        signal_patterns = ['signal', 'trade', 'trading', 'buy', 'sell', 'long', 'short', 'entry', 'target']
        news_patterns = ['news', 'update', 'announcement', 'breaking', 'latest']
        analysis_patterns = ['analysis', 'technical', 'fundamental', 'chart', 'price']
        educational_patterns = ['learn', 'education', 'tutorial', 'guide', 'how to']
        
        if any(pattern in text for pattern in signal_patterns):
            return 'signals'
        elif any(pattern in text for pattern in news_patterns):
            return 'news'
        elif any(pattern in text for pattern in analysis_patterns):
            return 'analysis'
        elif any(pattern in text for pattern in educational_patterns):
            return 'educational'
        else:
            return 'mixed'
    
    async def find_telegram_recommendations(self, known_channels: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Поиск рекомендаций новых каналов"""
        
        print("\n🔍 ПОИСК РЕКОМЕНДАЦИЙ НОВЫХ КАНАЛОВ")
        
        new_channels = []
        
        # Ищем упоминания других каналов в описаниях
        for channel in known_channels:
            if channel.get('description'):
                mentioned_channels = self.extract_mentioned_channels(channel['description'])
                for mentioned in mentioned_channels:
                    if mentioned not in [c['username'] for c in known_channels]:
                        try:
                            is_active = await self.check_telegram_channel_status(mentioned)
                            if is_active:
                                channel_info = await self.get_telegram_channel_info(mentioned)
                                if channel_info:
                                    new_channels.append(channel_info)
                                    print(f"🎯 Найден новый канал: @{mentioned}")
                        except:
                            continue
        
        return new_channels
    
    def extract_mentioned_channels(self, text: str) -> List[str]:
        """Извлечение упомянутых каналов из текста"""
        
        # Паттерны для поиска упоминаний каналов
        patterns = [
            r'@(\w+)',
            r't\.me/(\w+)',
            r'telegram\.me/(\w+)',
            r'канал (\w+)',
            r'channel (\w+)'
        ]
        
        mentioned = set()
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            mentioned.update(matches)
        
        return list(mentioned)
    
    async def discover_reddit_channels(self) -> List[Dict[str, Any]]:
        """Обнаружение активных Reddit каналов"""
        
        print("\n🔍 ОБНАРУЖЕНИЕ REDDIT КАНАЛОВ")
        print("="*80)
        
        discovered_channels = []
        
        for subreddit in self.known_channels['reddit']:
            try:
                subreddit_info = await self.get_reddit_subreddit_info(subreddit)
                if subreddit_info:
                    discovered_channels.append(subreddit_info)
                    print(f"✅ r/{subreddit}: АКТИВЕН - {subreddit_info.get('subscribers', 'N/A')} подписчиков")
                else:
                    print(f"❌ r/{subreddit}: Неактивен или недоступен")
            except Exception as e:
                print(f"❌ r/{subreddit}: Ошибка проверки - {e}")
        
        return discovered_channels
    
    async def get_reddit_subreddit_info(self, subreddit: str) -> Optional[Dict[str, Any]]:
        """Получение информации о Reddit subreddit"""
        
        url = f"https://www.reddit.com/r/{subreddit}/about.json"
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self.parse_reddit_subreddit_info(data, subreddit)
        except Exception as e:
            logger.error(f"Ошибка получения информации о subreddit {subreddit}: {e}")
        
        return None
    
    def parse_reddit_subreddit_info(self, data: Dict[str, Any], subreddit: str) -> Dict[str, Any]:
        """Парсинг информации о Reddit subreddit"""
        
        if 'data' not in data:
            return None
        
        subreddit_data = data['data']
        
        return {
            'username': f"r/{subreddit}",
            'title': subreddit_data.get('title', subreddit),
            'description': subreddit_data.get('public_description', ''),
            'subscribers': subreddit_data.get('subscribers', 'N/A'),
            'content_type': 'mixed',  # Reddit subreddit'ы обычно смешанные
            'platform': 'reddit',
            'url': f"https://www.reddit.com/r/{subreddit}",
            'discovered_at': datetime.now().isoformat(),
            'is_active': True
        }
    
    async def discover_all_channels(self) -> Dict[str, List[Dict[str, Any]]]:
        """Обнаружение каналов со всех платформ"""
        
        print("🚀 КОМПЛЕКСНОЕ ОБНАРУЖЕНИЕ КАНАЛОВ СО ВСЕХ РЕСУРСОВ")
        print("="*100)
        print(f"🕐 Время начала: {datetime.now().strftime('%d.%m.%Y в %H:%M:%S')}")
        print("="*100)
        
        all_channels = {}
        
        # Telegram каналы
        print("\n📱 TELEGRAM КАНАЛЫ")
        telegram_channels = await self.discover_telegram_channels()
        all_channels['telegram'] = telegram_channels
        
        # Reddit каналы
        print("\n🔴 REDDIT КАНАЛЫ")
        reddit_channels = await self.discover_reddit_channels()
        all_channels['reddit'] = reddit_channels
        
        # Сохраняем результаты
        await self.save_discovered_channels(all_channels)
        
        return all_channels
    
    async def save_discovered_channels(self, all_channels: Dict[str, List[Dict[str, Any]]]):
        """Сохранение обнаруженных каналов"""
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Сохраняем в JSON
        filename = f"discovered_channels_{timestamp}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(all_channels, f, ensure_ascii=False, indent=2)
        
        # Создаем отчет
        await self.create_discovery_report(all_channels, filename)
        
        print(f"\n💾 Результаты сохранены в: {filename}")
    
    async def create_discovery_report(self, all_channels: Dict[str, List[Dict[str, Any]]], filename: str):
        """Создание отчета об обнаружении каналов"""
        
        report_filename = f"channel_discovery_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        
        with open(report_filename, 'w', encoding='utf-8') as f:
            f.write("# 📊 ОТЧЕТ ОБ ОБНАРУЖЕНИИ КАНАЛОВ\n\n")
            f.write(f"**Дата:** {datetime.now().strftime('%d.%m.%Y в %H:%M:%S')}\n")
            f.write(f"**Файл данных:** {filename}\n\n")
            
            total_channels = sum(len(channels) for channels in all_channels.values())
            f.write(f"**Всего обнаружено каналов:** {total_channels}\n\n")
            
            for platform, channels in all_channels.items():
                f.write(f"## {platform.upper()}\n")
                f.write(f"**Количество каналов:** {len(channels)}\n\n")
                
                for channel in channels:
                    f.write(f"### {channel['username']}\n")
                    f.write(f"- **Название:** {channel['title']}\n")
                    f.write(f"- **Подписчики:** {channel['subscribers']}\n")
                    f.write(f"- **Тип контента:** {channel['content_type']}\n")
                    f.write(f"- **URL:** {channel['url']}\n")
                    f.write(f"- **Описание:** {channel['description'][:100]}...\n\n")
        
        print(f"📋 Отчет создан: {report_filename}")

async def main():
    """Основная функция"""
    
    print("🚀 ЗАПУСК СИСТЕМЫ ОБНАРУЖЕНИЯ КАНАЛОВ")
    print("Собираем активные каналы со всех ресурсов...")
    
    discovery_system = ChannelDiscoverySystem()
    all_channels = await discovery_system.discover_all_channels()
    
    # Итоговая статистика
    print(f"\n{'='*100}")
    print(f"📊 ИТОГОВАЯ СТАТИСТИКА")
    print(f"{'='*100}")
    
    total_channels = 0
    for platform, channels in all_channels.items():
        print(f"\n📱 {platform.upper()}: {len(channels)} каналов")
        total_channels += len(channels)
        
        # Показываем топ-5 каналов по подписчикам
        sorted_channels = sorted(channels, key=lambda x: str(x.get('subscribers', '0')), reverse=True)
        for i, channel in enumerate(sorted_channels[:5], 1):
            print(f"   {i}. {channel['username']} - {channel.get('subscribers', 'N/A')} подписчиков")
    
    print(f"\n🎯 ВСЕГО ОБНАРУЖЕНО: {total_channels} каналов")
    print("✅ Система обнаружения каналов завершена!")

if __name__ == "__main__":
    asyncio.run(main())
