"""
Enhanced Telegram Parser with OCR Support
Адаптированный из analyst_crypto проекта для реального извлечения сигналов
"""

import urllib.request
import json
import re
from datetime import datetime
import time
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SignalDirection(Enum):
    BUY = "BUY"
    SELL = "SELL" 
    LONG = "LONG"
    SHORT = "SHORT"
    HOLD = "HOLD"

@dataclass
class TelegramSignal:
    """Торговый сигнал из Telegram канала"""
    symbol: str
    direction: SignalDirection
    entry_price: Optional[float] = None
    target_price: Optional[float] = None
    stop_loss: Optional[float] = None
    confidence: float = 0.0
    raw_text: str = ""
    cleaned_text: str = ""
    channel: str = ""
    message_id: str = ""
    timestamp: str = ""

class TelegramTextCleaner:
    """Очистка и нормализация текста из Telegram каналов"""
    
    def __init__(self):
        # Коррекции специфичные для Telegram и OCR
        self.text_corrections = {
            # HTML entities
            '&#036;': '$', '&#39;': "'", '&amp;': '&', '&lt;': '<', '&gt;': '>',
            '&nbsp;': ' ', '&quot;': '"',
            
            # Общие ошибки в криптовалютах
            'БТС': 'BTC', 'BТС': 'BTC', 'СТС': 'BTC', 'ВТС': 'BTC', 
            'ЕТН': 'ETH', 'ЕТИ': 'ETH', 'Е7Н': 'ETH',
            'БИГ': 'BUY', 'БАЙ': 'BUY', 'ЛОНГ': 'LONG', 'ШОРТ': 'SHORT',
            'СЕЛЛ': 'SELL', 'ТАРГЕТ': 'TARGET', 'ЦЕЛЬ': 'TARGET', 'СТОП': 'STOP',
            
            # Цифровые ошибки
            'О': '0', 'о': '0', 'З': '3', 'Б': '6', 'Т': '7', 'В': '8'
        }
        
        # Криптовалюты с альтернативными написаниями
        self.crypto_symbols = {
            'BTC', 'ETH', 'ADA', 'SOL', 'DOT', 'LINK', 'UNI', 'AVAX',
            'MATIC', 'ATOM', 'XRP', 'DOGE', 'SHIB', 'LTC', 'BCH', 'BNB',
            'USDT', 'USDC', 'BUSD', 'DAI', 'LUNA', 'NEAR', 'FTM', 'ALGO',
            'SYS', 'ENA', 'ZIG', 'ATA', 'MAVIA', 'DXY', 'ALTCOINS',
            'ORDI', 'BAND', 'BSW', 'WOO', 'JASMY', 'MEME', 'PUMP'
        }
    
    def clean_text(self, text: str) -> str:
        """Очищает текст от ошибок и нормализует"""
        if not text:
            return ""
        
        cleaned = text.strip()
        
        # Применяем HTML коррекции
        for wrong, correct in self.text_corrections.items():
            cleaned = cleaned.replace(wrong, correct)
        
        # Убираем лишние пробелы
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        logger.debug(f"Cleaned: '{text[:50]}...' → '{cleaned[:50]}...'")
        return cleaned

class EnhancedSignalExtractor:
    """Улучшенный экстрактор сигналов из Telegram сообщений"""
    
    def __init__(self):
        self.cleaner = TelegramTextCleaner()
        
        # Расширенные паттерны для поиска сигналов
        self.signal_patterns = {
            # Полные паттерны с ценами (высокая точность)
            'full_signal': [
                r'(\w+)/USDT\s+(LONG|SHORT|BUY|SELL)\s+Entry[:\s]*\$?([\d,]+\.?\d*)\s+Target[:\s]*\$?([\d,]+\.?\d*)',
                r'([A-Z]+)\s+(LONG|SHORT|BUY|SELL)\s+\$?([\d,]+\.?\d*)\s*[→➡️]\s*\$?([\d,]+\.?\d*)',
                r'[🚀📉🔥💰]\s*([A-Z]+)\s+(LONG|SHORT|BUY|SELL)\s+Entry[:\s]*\$?([\d,]+\.?\d*)',
                r'LONGING\s+\$([A-Z]+)\s+HERE',
                r'(\w+)\s+(LONG|SHORT|BUY|SELL)\s+@\s+\$?([\d,]+\.?\d*)',
            ],
            
            # Простые паттерны с направлением (средняя точность)
            'direction_signal': [
                r'([A-Z]+)\s+(LONG|SHORT|BUY|SELL)\s+\$?([\d,]+\.?\d*)',
                r'([A-Z]+)\s+(LONG|SHORT|BUY|SELL)',
                r'[🚀📉🔥💰]\s*([A-Z]+)\s+(LONG|SHORT|BUY|SELL)',
                r'(\w+)\s+(LONG|SHORT|BUY|SELL)\s+update',
                r'\$([A-Z]+)\s+(LONG|SHORT|BUY|SELL)',
            ],
            
            # Аналитические паттерны с техническим анализом (средняя точность)
            'technical_analysis': [
                r'\$([A-Z]+)\s+(gives|breaks|reaches|targets)\s+.*?(\d+[kK]?)',
                r'([A-Z]+)\s+(bullish|bearish|pumping|dumping)',
                r'([A-Z]+)\s+to\s+\$?([\d,]+\.?\d*)',
                r'([A-Z]+)\s+(resistance|support)\s+\$?([\d,]+\.?\d*)',
                r'([A-Z]+)\s+update.*?(\d+[kK]?)',
                # Новые паттерны для технического анализа
                r'([A-Z]+)\s+breaks\s+(under|below)\s+\$?([\d,]+\.?\d*)',
                r'([A-Z]+)\s+targets?\s+\$?([\d,]+\.?\d*)',
                r'([A-Z]+)\s+support\s+at\s+\$?([\d,]+\.?\d*)',
                r'([A-Z]+)\s+resistance\s+at\s+\$?([\d,]+\.?\d*)',
                r'([A-Z]+)\s+key\s+zone\s+\$?([\d,]+\.?\d*)',
                r'([A-Z]+)\s+main\s+support\s+\$?([\d,]+\.?\d*)',
            ],
            
            # Ценовые цели и прогнозы (низкая точность)
            'price_target': [
                r'([A-Z]+)\s+target[:\s]*\$?([\d,]+\.?\d*)',
                r'([A-Z]+).*?next.*?\$?([\d,]+\.?\d*)',
                r'([A-Z]+).*?above\s+\$?([\d,]+\.?\d*)',
                r'([A-Z]+).*?below\s+\$?([\d,]+\.?\d*)',
                r'([A-Z]+).*?towards\s+\$?([\d,]+\.?\d*)',
                r'([A-Z]+).*?down\s+to\s+\$?([\d,]+\.?\d*)',
            ]
        }
    
    def extract_signals(self, text: str, channel: str = "", message_id: str = "") -> List[TelegramSignal]:
        """Извлекает сигналы из текста сообщения"""
        
        if not text or not text.strip():
            return []
        
        # Очищаем текст
        cleaned_text = self.cleaner.clean_text(text)
        
        signals = []
        
        # Проходим по всем категориям паттернов
        for category, patterns in self.signal_patterns.items():
            category_signals = self._extract_by_patterns(patterns, cleaned_text, text, category)
            signals.extend(category_signals)
        
        # Удаляем дубликаты
        unique_signals = self._remove_duplicates(signals)
        
        # Добавляем метаинформацию
        for signal in unique_signals:
            signal.channel = channel
            signal.message_id = message_id
            signal.timestamp = datetime.now().isoformat()
        
        logger.info(f"Extracted {len(unique_signals)} signals from text: '{text[:50]}...'")
        return unique_signals
    
    def _extract_by_patterns(self, patterns: List[str], cleaned_text: str, raw_text: str, category: str) -> List[TelegramSignal]:
        """Извлекает сигналы по заданным паттернам"""
        
        signals = []
        
        for pattern in patterns:
            matches = re.finditer(pattern, cleaned_text, re.IGNORECASE)
            
            for match in matches:
                groups = match.groups()
                
                if len(groups) >= 2:
                    signal = self._create_signal_from_match(groups, cleaned_text, raw_text, category)
                    if signal:
                        signals.append(signal)
        
        return signals
    
    def _create_signal_from_match(self, groups: Tuple, cleaned_text: str, raw_text: str, category: str) -> Optional[TelegramSignal]:
        """Создает сигнал из результата regex поиска"""
        
        try:
            symbol = groups[0].upper()
            
            # Проверяем, что это валидная криптовалюта
            if not self._is_valid_crypto_symbol(symbol):
                return None
            
            # Определяем направление с учетом контекста
            direction = self._parse_direction(groups[1] if len(groups) > 1 else "", cleaned_text)
            
            # Извлекаем цены
            entry_price = self._parse_price(groups[2]) if len(groups) > 2 else None
            target_price = self._parse_price(groups[3]) if len(groups) > 3 else None
            
            # Рассчитываем уверенность на основе категории паттерна
            confidence = self._calculate_confidence(category, len(groups), entry_price, target_price)
            
            signal = TelegramSignal(
                symbol=symbol,
                direction=direction,
                entry_price=entry_price,
                target_price=target_price,
                confidence=confidence,
                raw_text=raw_text[:200] + "..." if len(raw_text) > 200 else raw_text,
                cleaned_text=cleaned_text[:200] + "..." if len(cleaned_text) > 200 else cleaned_text
            )
            
            return signal
            
        except Exception as e:
            logger.error(f"Error creating signal from match: {e}")
            return None
    
    def _is_valid_crypto_symbol(self, symbol: str) -> bool:
        """Проверяет, является ли символ валидной криптовалютой"""
        # Строгая проверка - только известные криптовалюты
        return symbol in self.cleaner.crypto_symbols
    
    def _parse_direction(self, direction_text: str, full_text: str = "") -> SignalDirection:
        """Определяет направление сигнала с учетом контекста"""
        direction_upper = direction_text.upper()
        full_text_upper = full_text.upper()
        
        # Явные торговые сигналы
        if direction_upper in ['BUY', 'LONG', 'BULL', 'BULLISH', 'PUMPING']:
            return SignalDirection.BUY
        elif direction_upper in ['SELL', 'SHORT', 'BEAR', 'BEARISH', 'DUMPING']:
            return SignalDirection.SELL
        elif 'LONG' in direction_upper:
            return SignalDirection.LONG
        elif 'SHORT' in direction_upper:
            return SignalDirection.SHORT
        
        # Анализ контекста для технического анализа
        if full_text:
            # Bearish контекст
            if any(word in full_text_upper for word in ['BEARISH', 'DUMPING', 'DOWN', 'BREAKS UNDER', 'CAPITULATION', 'DECLINE']):
                return SignalDirection.SELL
            # Bullish контекст
            elif any(word in full_text_upper for word in ['BULLISH', 'PUMPING', 'UP', 'BREAKS ABOVE', 'RALLY', 'RECOVERY']):
                return SignalDirection.BUY
        
        return SignalDirection.HOLD
    
    def _parse_price(self, price_text: str) -> Optional[float]:
        """Парсит цену из текста"""
        if not price_text:
            return None
            
        try:
            # Убираем символы валют и разделители
            cleaned_price = re.sub(r'[\$,\s]', '', price_text)
            
            # Обрабатываем сокращения (k, K для тысяч)
            if cleaned_price.endswith(('k', 'K')):
                cleaned_price = cleaned_price[:-1]
                return float(cleaned_price) * 1000
            
            return float(cleaned_price)
            
        except (ValueError, AttributeError):
            return None
    
    def _calculate_confidence(self, category: str, groups_count: int, entry_price: Optional[float], target_price: Optional[float]) -> float:
        """Рассчитывает уверенность в сигнале"""
        
        base_confidence = {
            'full_signal': 0.85,         # Высокая точность
            'direction_signal': 0.65,    # Средняя точность
            'technical_analysis': 0.60,  # Технический анализ (средняя точность)
            'price_target': 0.45         # Ценовые цели (низкая точность)
        }.get(category, 0.25)
        
        # Бонусы за дополнительную информацию
        if entry_price:
            base_confidence += 0.15
        if target_price:
            base_confidence += 0.10
        if groups_count >= 4:
            base_confidence += 0.05
        
        # Штраф за слишком низкую уверенность
        if base_confidence < 0.4:
            base_confidence = 0.0  # Не показываем сигналы с очень низкой уверенностью
        
        return min(base_confidence, 1.0)
    
    def _remove_duplicates(self, signals: List[TelegramSignal]) -> List[TelegramSignal]:
        """Удаляет дубликаты сигналов"""
        
        seen = set()
        unique_signals = []
        
        for signal in signals:
            key = (signal.symbol, signal.direction.value)
            if key not in seen:
                seen.add(key)
                unique_signals.append(signal)
        
        return unique_signals

class EnhancedTelegramParser:
    """Улучшенный парсер Telegram каналов с поддержкой реальных сигналов"""
    
    def __init__(self):
        self.opener = urllib.request.build_opener()
        self.opener.addheaders = [
            ('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        ]
        self.signal_extractor = EnhancedSignalExtractor()
        
        # Импортируем универсальный парсер для структурированных сигналов
        try:
            from universal_signal_parser import UniversalSignalParser
            self.universal_parser = UniversalSignalParser()
            logger.info("✅ Универсальный парсер загружен")
        except ImportError:
            self.universal_parser = None
            logger.warning("⚠️ Универсальный парсер не найден")
    
    def get_channel_content(self, username: str) -> Optional[str]:
        """Получает содержимое канала"""
        try:
            url = f"https://t.me/s/{username}"
            logger.info(f"📡 Получение содержимого {username}...")
            
            with self.opener.open(url, timeout=15) as response:
                content = response.read().decode('utf-8')
                logger.info(f"✅ Получено {len(content)} символов из {username}")
                return content
                
        except Exception as e:
            logger.error(f"❌ Ошибка получения {username}: {e}")
            return None
    
    def extract_messages_from_html(self, html_content: str, username: str) -> List[Dict]:
        """Извлекает сообщения из HTML"""
        messages = []
        
        if not html_content:
            return messages
        
        # Паттерн для сообщений Telegram
        message_pattern = r'<div class="tgme_widget_message_text[^"]*"[^>]*>(.*?)</div>'
        matches = re.findall(message_pattern, html_content, re.DOTALL)
        
        for i, text_html in enumerate(matches):
            # Очищаем HTML из текста
            text = re.sub(r'<[^>]+>', '', text_html)
            text = re.sub(r'&nbsp;', ' ', text)
            text = re.sub(r'&amp;', '&', text)
            text = re.sub(r'&lt;', '<', text)
            text = re.sub(r'&gt;', '>', text)
            text = re.sub(r'&#036;', '$', text)
            text = re.sub(r'&#39;', "'", text)
            text = text.strip()
            
            if text and len(text) > 10:
                messages.append({
                    'id': f"msg_{i}",
                    'text': text,
                    'date': datetime.now().isoformat(),
                    'username': username
                })
        
        logger.info(f"✅ Найдено {len(messages)} сообщений в {username}")
        return messages
    
    def parse_channel(self, username: str, hours_back: int = 24) -> List[Dict]:
        """Парсит канал и извлекает сигналы"""
        logger.info(f"\n🔍 Парсинг канала: {username}")
        
        # Получаем содержимое канала
        content = self.get_channel_content(username)
        if not content:
            return []
        
        # Извлекаем сообщения
        messages = self.extract_messages_from_html(content, username)
        if not messages:
            logger.warning(f"❌ Не найдено сообщений в {username}")
            return []
        
        # Извлекаем сигналы из сообщений
        all_signals = []
        for message in messages:
            signals = self._extract_signals_from_message(message, username)
            all_signals.extend(signals)
        
        logger.info(f"✅ Извлечено {len(all_signals)} сигналов из {username}")
        return all_signals
    
    def _extract_signals_from_message(self, message: Dict, username: str) -> List[Dict]:
        """Извлекает сигналы из сообщения с использованием обоих парсеров"""
        signals = []
        
        # Сначала пробуем универсальный парсер для структурированных сигналов
        if self.universal_parser:
            try:
                universal_signal = self.universal_parser.parse_signal(message['text'], username)
                if universal_signal:
                    standard_signal = self.universal_parser.convert_to_standard_format(universal_signal)
                    standard_signal['message_id'] = message['id']
                    standard_signal['original_text'] = message['text'][:200] + "..." if len(message['text']) > 200 else message['text']
                    standard_signal['cleaned_text'] = message['text'][:200] + "..." if len(message['text']) > 200 else message['text']
                    signals.append(standard_signal)
                    logger.info(f"✅ Структурированный сигнал извлечен: {universal_signal.asset} {universal_signal.direction}")
                    return signals  # Если нашли структурированный сигнал, не ищем другие
            except Exception as e:
                logger.debug(f"Универсальный парсер не сработал: {e}")
        
        # Если структурированный сигнал не найден, используем обычный парсер
        telegram_signals = self.signal_extractor.extract_signals(
            message['text'], 
            channel=username, 
            message_id=message['id']
        )
        
        # Конвертируем в словари для JSON сериализации
        for signal in telegram_signals:
            signal_dict = {
                'id': f"{username}_{signal.message_id}_{signal.symbol}",
                'asset': signal.symbol,
                'direction': signal.direction.value,
                'entry_price': signal.entry_price,
                'target_price': signal.target_price,
                'stop_loss': signal.stop_loss,
                'confidence': round(signal.confidence * 100, 1),
                'channel': signal.channel,
                'message_id': signal.message_id,
                'timestamp': signal.timestamp,
                'extraction_time': datetime.now().isoformat(),
                'original_text': signal.raw_text,
                'cleaned_text': signal.cleaned_text,
                'bybit_available': self._check_bybit_availability(signal.symbol),
                'signal_type': 'telegram'
            }
            signals.append(signal_dict)
        
        return signals
    
    def _check_bybit_availability(self, symbol: str) -> bool:
        """Проверяет доступность пары на Bybit"""
        # Список популярных пар на Bybit
        bybit_pairs = {
            'BTC', 'ETH', 'SOL', 'AVAX', 'MATIC', 'DOT', 'LINK', 'UNI',
            'DOGE', 'ADA', 'XRP', 'LTC', 'BCH', 'ETC', 'ATOM', 'NEAR',
            'ORDI', 'BAND', 'BSW', 'WOO', 'JASMY', 'MEME', 'PUMP'
        }
        return symbol in bybit_pairs
    
    def parse_all_channels(self, channels: List[str], hours_back: int = 24) -> Tuple[List[Dict], Dict]:
        """Парсит все каналы"""
        all_signals = []
        channel_stats = {}
        
        for username in channels:
            try:
                signals = self.parse_channel(username, hours_back)
                all_signals.extend(signals)
                
                channel_stats[username] = {
                    'signals_found': len(signals),
                    'channel_name': username
                }
                
                # Небольшая задержка между запросами
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"❌ Ошибка парсинга {username}: {e}")
                channel_stats[username] = {
                    'signals_found': 0,
                    'channel_name': username,
                    'error': str(e)
                }
        
        return all_signals, channel_stats

def main():
    """Основная функция"""
    parser = EnhancedTelegramParser()
    
    # Расширенный список каналов для парсинга
    channels = [
        'CryptoCapoTG',
        'signalsbitcoinandethereum',
        'cryptosignals',
        'binance_signals',
        'crypto_analytics',
        'binance_signals_official',
        'coinbase_signals',
        'kraken_signals',
        'crypto_signals_daily',
        'bitcoin_signals',
        'ethereum_signals_daily',
        'altcoin_signals_pro',
        'defi_signals_daily',
        'trading_signals_24_7',
        'crypto_analytics_pro',
        'market_signals',
        'price_alerts',
        'crypto_news_signals',
        'BinanceKillers_Free',  # Добавляем канал с структурированными сигналами
        'Wolf_of_Trading',
        'Crypto_Inner_Circle',
        'Traders_Diary',
        'Crypto_Trading_RU'
    ]
    
    logger.info("🚀 Запуск расширенного парсера Telegram каналов...")
    
    # Парсим все каналы
    signals, stats = parser.parse_all_channels(channels, hours_back=24)
    
    # Сохраняем результаты
    result = {
        'success': True,
        'total_signals': len(signals),
        'signals': signals,
        'channel_stats': stats,
        'collection_time': datetime.now().isoformat(),
        'hours_back': 24,
        'parser_version': 'enhanced_v2.0_with_universal'
    }
    
    with open('enhanced_telegram_signals.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    logger.info(f"\n✅ Парсинг завершен!")
    logger.info(f"📊 Всего сигналов: {len(signals)}")
    logger.info(f"📁 Результат сохранен в: enhanced_telegram_signals.json")
    
    # Выводим статистику по каналам
    for channel, stat in stats.items():
        logger.info(f"📱 {channel}: {stat['signals_found']} сигналов")
    
    # Показываем найденные сигналы
    if signals:
        logger.info(f"\n🎯 Найденные сигналы:")
        for i, signal in enumerate(signals[:10], 1):  # Первые 10
            logger.info(f"   {i}. {signal['asset']} {signal['direction']} ${signal['entry_price'] or 'N/A'} (conf: {signal['confidence']}%)")

if __name__ == "__main__":
    main()
