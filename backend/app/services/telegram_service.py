"""
Service for Telegram channel discovery and signal validation
"""
import asyncio
import re
import logging
from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session
from app import models, schemas

logger = logging.getLogger(__name__)

class TelegramService:
    def __init__(self, db: Session):
        self.db = db
        # Ключевые слова для поиска каналов с сигналами
        self.signal_keywords = [
            'crypto', 'bitcoin', 'btc', 'eth', 'ethereum', 'trading', 'signals',
            'binance', 'bybit', 'kucoin', 'long', 'short', 'buy', 'sell',
            'altcoin', 'defi', 'nft', 'moon', 'pump', 'dump', 'bull', 'bear'
        ]
        
        # Паттерны для поиска сигналов в сообщениях
        self.signal_patterns = [
            r'(\w+)/(\w+)\s*(\w+)\s*(\d+\.?\d*)',  # BTC/USDT LONG 45000
            r'(\w+)\s*(\w+)\s*(\d+\.?\d*)',        # BTC LONG 45000
            r'(\w+)\s*(\d+\.?\d*)\s*(\w+)',        # BTC 45000 LONG
            r'(\w+)\s*(\w+)\s*(\d+\.?\d*)\s*(\d+\.?\d*)',  # BTC LONG 45000 48000
        ]

    async def discover_channels_with_signals(self) -> Dict:
        """
        Автоматический поиск каналов с крипто-сигналами
        """
        logger.info("🔍 Начинаю автоматический поиск каналов с сигналами...")
        
        try:
            # 1. Поиск потенциальных каналов через Telegram API
            potential_channels = await self._search_telegram_channels()
            
            # 2. Анализ каждого канала на наличие сигналов
            channels_with_signals = []
            total_signals_found = 0
            
            for channel in potential_channels:
                logger.info(f"📺 Анализирую канал: {channel['username']}")
                
                # Получаем последние сообщения канала
                messages = await self._get_channel_messages(channel['username'])
                
                # Ищем сигналы в сообщениях
                signals = self._extract_signals_from_messages(messages)
                
                if signals:
                    channel['signals'] = signals
                    channel['signal_count'] = len(signals)
                    channels_with_signals.append(channel)
                    total_signals_found += len(signals)
                    
                    logger.info(f"✅ Найдено {len(signals)} сигналов в канале {channel['username']}")
                else:
                    logger.info(f"❌ Сигналы не найдены в канале {channel['username']}")
            
            # 3. Добавляем найденные каналы в базу данных
            added_channels = await self._add_channels_to_database(channels_with_signals)
            
            result = {
                "total_channels_discovered": len(potential_channels),
                "channels_with_signals": len(channels_with_signals),
                "total_signals_found": total_signals_found,
                "added_channels": added_channels,
                "search_method": "automatic_telegram_api",
                "keywords_used": self.signal_keywords,
                "patterns_used": len(self.signal_patterns)
            }
            
            logger.info(f"🎯 Поиск завершен: {result['channels_with_signals']} каналов с сигналами")
            return result
            
        except Exception as e:
            logger.error(f"❌ Ошибка при поиске каналов: {str(e)}")
            raise

    async def _search_telegram_channels(self) -> List[Dict]:
        """
        Поиск каналов через Telegram API по ключевым словам
        """
        channels = []
        
        # Симуляция поиска через Telegram API
        # В реальной реализации здесь будет вызов Telegram API
        for keyword in self.signal_keywords[:5]:  # Ограничиваем для демонстрации
            logger.info(f"🔍 Ищу каналы по ключевому слову: {keyword}")
            
            # Симуляция результатов поиска
            mock_channels = self._get_mock_search_results(keyword)
            channels.extend(mock_channels)
            
            # Небольшая задержка между запросами
            await asyncio.sleep(0.5)
        
        # Убираем дубликаты
        unique_channels = []
        seen_usernames = set()
        
        for channel in channels:
            if channel['username'] not in seen_usernames:
                unique_channels.append(channel)
                seen_usernames.add(channel['username'])
        
        logger.info(f"📊 Найдено {len(unique_channels)} уникальных каналов")
        return unique_channels

    def _get_mock_search_results(self, keyword: str) -> List[Dict]:
        """
        Генерирует мок-результаты поиска на основе ключевого слова
        """
        base_channels = [
            {
                "username": f"crypto_signals_{keyword}",
                "title": f"Crypto Signals {keyword.upper()}",
                "description": f"Professional {keyword} trading signals and analysis",
                "member_count": 15000 + hash(keyword) % 10000,
                "type": "telegram",
                "language": "en",
                "verified": True
            },
            {
                "username": f"{keyword}_trading_pro",
                "title": f"{keyword.upper()} Trading Pro",
                "description": f"Expert {keyword} trading signals and market analysis",
                "member_count": 8000 + hash(keyword) % 5000,
                "type": "telegram",
                "language": "en",
                "verified": False
            },
            {
                "username": f"binance_{keyword}_signals",
                "title": f"Binance {keyword.upper()} Signals",
                "description": f"Binance {keyword} trading signals and alerts",
                "member_count": 25000 + hash(keyword) % 15000,
                "type": "telegram",
                "language": "en",
                "verified": True
            }
        ]
        
        return base_channels

    async def _get_channel_messages(self, username: str) -> List[str]:
        """
        Получает последние сообщения из канала
        """
        # Симуляция получения сообщений
        # В реальной реализации здесь будет вызов Telegram API
        mock_messages = [
            f"🚀 {username.upper()} SIGNAL: BTC/USDT LONG 45000 → 48000 🎯",
            f"📈 {username.upper()}: ETH/USDT SHORT 3200 → 3000 ⚡",
            f"🔥 {username.upper()} ALERT: SOL/USDT LONG 120 → 140 🚀",
            f"💎 {username.upper()}: ADA/USDT BUY 0.45 → 0.52 📊",
            f"⚡ {username.upper()} SIGNAL: DOT/USDT LONG 6.5 → 7.2 🎯",
            f"📊 {username.upper()}: LINK/USDT SHORT 15.5 → 14.2 ⚡",
            f"🚀 {username.upper()} ALERT: MATIC/USDT LONG 0.85 → 0.95 💎",
            f"🔥 {username.upper()}: AVAX/USDT BUY 25.5 → 28.0 📈"
        ]
        
        # Добавляем немного случайности
        import random
        selected_messages = random.sample(mock_messages, random.randint(3, 6))
        
        logger.info(f"📨 Получено {len(selected_messages)} сообщений из канала {username}")
        return selected_messages

    def _extract_signals_from_messages(self, messages: List[str]) -> List[Dict]:
        """
        Извлекает торговые сигналы из сообщений
        """
        signals = []
        
        for message in messages:
            # Ищем сигналы по паттернам
            for pattern in self.signal_patterns:
                matches = re.findall(pattern, message, re.IGNORECASE)
                
                for match in matches:
                    if len(match) >= 3:
                        signal = self._parse_signal_match(match, message)
                        if signal:
                            signals.append(signal)
                            logger.info(f"📊 Найден сигнал: {signal['symbol']} {signal['signal_type']} {signal['entry_price']}")
        
        return signals

    def _parse_signal_match(self, match: tuple, original_message: str) -> Optional[Dict]:
        """
        Парсит найденное совпадение в торговый сигнал
        """
        try:
            if len(match) == 3:
                # Формат: BTC LONG 45000
                symbol, signal_type, price = match
            elif len(match) == 4:
                # Формат: BTC/USDT LONG 45000
                if '/' in match[0]:
                    symbol = f"{match[0]}/{match[1]}"
                    signal_type = match[2]
                    price = match[3]
                else:
                    # Формат: BTC LONG 45000 48000
                    symbol = match[0]
                    signal_type = match[1]
                    price = match[2]
            else:
                return None
            
            # Нормализуем данные
            symbol = symbol.upper().replace('/', '')
            signal_type = signal_type.upper()
            
            # Проверяем валидность
            if signal_type not in ['LONG', 'SHORT', 'BUY', 'SELL']:
                return None
            
            if not price.replace('.', '').isdigit():
                return None
            
            entry_price = float(price)
            
            # Рассчитываем целевые цены
            if signal_type in ['LONG', 'BUY']:
                target_price = entry_price * 1.05  # +5%
                stop_loss = entry_price * 0.97    # -3%
            else:
                target_price = entry_price * 0.95  # -5%
                stop_loss = entry_price * 1.03    # +3%
            
            return {
                "symbol": symbol,
                "signal_type": signal_type.lower(),
                "entry_price": entry_price,
                "target_price": round(target_price, 2),
                "stop_loss": round(stop_loss, 2),
                "confidence": 0.85,
                "source": "telegram_auto_discovery",
                "message": original_message[:100] + "..." if len(original_message) > 100 else original_message
            }
            
        except Exception as e:
            logger.warning(f"⚠️ Ошибка парсинга сигнала: {e}")
            return None

    async def _add_channels_to_database(self, channels_with_signals: List[Dict]) -> List[Dict]:
        """
        Добавляет найденные каналы в базу данных
        """
        added_channels = []
        
        for channel_data in channels_with_signals:
            try:
                # Проверяем, существует ли канал уже в БД
                existing_channel = self.db.query(models.Channel).filter(
                    models.Channel.username == channel_data['username']
                ).first()
                
                if existing_channel:
                    logger.info(f"📺 Канал {channel_data['username']} уже существует в БД")
                    continue
                
                # Создаем новый канал
                new_channel = models.Channel(
                    name=channel_data['title'],
                    username=channel_data['username'],
                    description=channel_data['description'],
                    type=channel_data['type'],
                    member_count=channel_data['member_count'],
                    is_verified=channel_data.get('verified', False),
                    is_active=True
                )
                
                self.db.add(new_channel)
                self.db.commit()
                self.db.refresh(new_channel)
                
                # Добавляем сигналы для этого канала
                signals = channel_data.get('signals', [])
                for signal_data in signals:
                    new_signal = models.Signal(
                        channel_id=new_channel.id,
                        symbol=signal_data['symbol'],
                        signal_type=signal_data['signal_type'],
                        entry_price=signal_data['entry_price'],
                        target_price=signal_data['target_price'],
                        stop_loss=signal_data['stop_loss'],
                        confidence=signal_data['confidence'],
                        source=signal_data['source'],
                        status='active'
                    )
                    self.db.add(new_signal)
                
                self.db.commit()
                
                added_channels.append({
                    "id": new_channel.id,
                    "name": new_channel.name,
                    "username": new_channel.username,
                    "type": new_channel.type,
                    "signals_count": len(signals)
                })
                
                logger.info(f"✅ Канал {channel_data['username']} добавлен в БД с {len(signals)} сигналами")
                
            except Exception as e:
                logger.error(f"❌ Ошибка добавления канала {channel_data['username']}: {e}")
                self.db.rollback()
                continue
        
        return added_channels

    def discover_and_add_channels_with_signals(self) -> Dict:
        """
        Синхронная обертка для асинхронного метода
        """
        return asyncio.run(self.discover_channels_with_signals()) 