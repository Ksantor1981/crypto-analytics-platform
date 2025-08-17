"""
Паттерны для извлечения крипто-сигналов из текста
"""
import re
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class SignalPatterns:
    """
    Класс для извлечения сигналов из текста с помощью паттернов
    """
    
    def __init__(self):
        # Паттерны для торговых пар
        self.pair_patterns = [
            r'\b([A-Z]{2,10})/([A-Z]{2,10})\b',  # BTC/USDT
            r'\b([A-Z]{2,10})([A-Z]{2,10})\b',   # BTCUSDT
            r'\$([A-Z]{2,10})\b',                # $BTC
            r'\b([A-Z]{2,10})\s*([A-Z]{2,10})\b', # BTC USDT
            r'\b(Bitcoin|Ethereum)\b'            # Bitcoin, Ethereum
        ]
        
        # Паттерны для направлений
        self.direction_patterns = {
            'long': [
                r'\b(long|buy|bullish|moon|pump|🚀|📈|лонг|покупка)\b',
                r'\b(вход|входим|открываем)\s+(лонг|long|buy)',
                r'\b(цель|target|tp)\s*[:=]\s*\d+',
                r'🚀',  # Эмодзи ракета
                r'📈',  # Эмодзи график вверх
            ],
            'short': [
                r'\b(short|sell|bearish|dump|crash|📉|🔻|шорт|продажа)\b',
                r'\b(вход|входим|открываем)\s+(шорт|short|sell)',
                r'\b(стоп|stop|sl)\s*[:=]\s*\d+',
                r'📉',  # Эмодзи график вниз
                r'🔻',  # Эмодзи стрелка вниз
            ]
        }
        
        # Паттерны для цен
        self.price_patterns = [
            r'\b(\d+\.?\d*)\s*(?:usdt|usd|\$)?\b',  # 45000 USDT
            r'\b(?:цена|price|entry|вход)\s*[:=]\s*(\d+\.?\d*)',
            r'\b(?:цель|target|tp)\s*[:=]\s*(\d+\.?\d*)',
            r'\b(?:стоп|stop|sl)\s*[:=]\s*(\d+\.?\d*)',
        ]
        
        # Комплексные паттерны для сигналов
        self.signal_patterns = [
            # Английский формат
            r'(?i)(\w+usdt)\s+(long|short)\s+(\d+\.?\d*)\s+(?:tp|target)\s*[:=]\s*(\d+\.?\d*)\s+(?:sl|stop)\s*[:=]\s*(\d+\.?\d*)',
            r'(?i)(long|short)\s+(\w+usdt)\s+(\d+\.?\d*)\s+(?:tp|target)\s*[:=]\s*(\d+\.?\d*)\s+(?:sl|stop)\s*[:=]\s*(\d+\.?\d*)',
            
            # Русский формат
            r'(?i)(\w+usdt)\s+(лонг|шорт)\s+(\d+\.?\d*)\s+цель\s*[:=]\s*(\d+\.?\d*)\s+стоп\s*[:=]\s*(\d+\.?\d*)',
            r'(?i)(лонг|шорт)\s+(\w+usdt)\s+(\d+\.?\d*)\s+цель\s*[:=]\s*(\d+\.?\d*)\s+стоп\s*[:=]\s*(\d+\.?\d*)',
            
            # С эмодзи
            r'(?i)(\w+usdt)\s*🚀\s*(\d+\.?\d*)\s*📈\s*(\d+\.?\d*)\s*📉\s*(\d+\.?\d*)',
            r'(?i)(\w+usdt)\s*📉\s*(\d+\.?\d*)\s*📈\s*(\d+\.?\d*)\s*📉\s*(\d+\.?\d*)',
            
            # Простой формат
            r'(?i)(\w+usdt)\s+(long|short|лонг|шорт)\s+(\d+\.?\d*)\s+(\d+\.?\d*)\s+(\d+\.?\d*)',
        ]
    
    def extract_signals_from_text(self, text: str, channel_username: str, message_id: str) -> List[Dict[str, Any]]:
        """
        Извлечение сигналов из текста
        
        Args:
            text: Текст сообщения
            channel_username: Имя канала
            message_id: ID сообщения
            
        Returns:
            Список извлеченных сигналов
        """
        signals = []
        
        if not text:
            return signals
        
        try:
            # Метод 1: Комплексные паттерны
            complex_signals = self._extract_with_complex_patterns(text, channel_username, message_id)
            signals.extend(complex_signals)
            
            # Метод 2: Пошаговое извлечение
            step_signals = self._extract_with_step_patterns(text, channel_username, message_id)
            signals.extend(step_signals)
            
            # Удаление дубликатов
            unique_signals = self._remove_duplicate_signals(signals)
            
            return unique_signals
            
        except Exception as e:
            logger.error(f"Ошибка извлечения сигналов: {e}")
            return []
    
    def _extract_with_complex_patterns(self, text: str, channel_username: str, message_id: str) -> List[Dict[str, Any]]:
        """Извлечение с помощью комплексных паттернов"""
        signals = []
        
        for pattern in self.signal_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
            
            for match in matches:
                try:
                    groups = match.groups()
                    
                    if len(groups) >= 5:
                        # Определяем формат на основе групп
                        if groups[0].upper().endswith('USDT'):
                            # Формат: PAIR DIRECTION ENTRY TARGET STOP
                            pair = groups[0].upper()
                            direction = self._normalize_direction(groups[1])
                            entry_price = float(groups[2])
                            target_price = float(groups[3])
                            stop_loss = float(groups[4])
                        else:
                            # Формат: DIRECTION PAIR ENTRY TARGET STOP
                            direction = self._normalize_direction(groups[0])
                            pair = groups[1].upper()
                            entry_price = float(groups[2])
                            target_price = float(groups[3])
                            stop_loss = float(groups[4])
                        
                        # Валидация сигнала
                        if self._validate_signal(pair, direction, entry_price, target_price, stop_loss):
                            signal = {
                                'trading_pair': pair,
                                'direction': direction,
                                'entry_price': entry_price,
                                'target_price': target_price,
                                'stop_loss': stop_loss,
                                'confidence': 0.9,  # Высокая уверенность для комплексных паттернов
                                'source': 'complex_pattern',
                                'channel_username': channel_username,
                                'message_id': message_id,
                                'extracted_at': datetime.utcnow()
                            }
                            signals.append(signal)
                            
                except (ValueError, IndexError) as e:
                    logger.warning(f"Ошибка парсинга комплексного паттерна: {e}")
                    continue
        
        return signals
    
    def _extract_with_step_patterns(self, text: str, channel_username: str, message_id: str) -> List[Dict[str, Any]]:
        """Пошаговое извлечение сигналов"""
        signals = []
        
        try:
            # Шаг 1: Извлечение торговой пары
            pairs = self._extract_trading_pairs(text)
            if not pairs:
                logger.debug("Нет торговых пар")
                return signals
            
            # Шаг 2: Определение направления
            direction = self._extract_direction(text)
            if not direction:
                logger.debug("Нет направления")
                return signals
            
            # Шаг 3: Извлечение цен
            prices = self._extract_prices(text)
            if len(prices) < 3:
                logger.debug(f"Недостаточно цен: {prices}")
                return signals
            
            logger.debug(f"Пара: {pairs}, Направление: {direction}, Цены: {prices}")
            
            # Шаг 4: Создание сигналов для каждой пары
            for pair in pairs:
                try:
                    # Сортируем цены для определения entry, target, stop
                    sorted_prices = sorted(prices)
                    
                    if direction == 'LONG':
                        # Для LONG: entry < target, stop < entry
                        entry_price = sorted_prices[1]  # Средняя цена как entry
                        target_price = sorted_prices[-1]  # Максимальная как target
                        stop_loss = sorted_prices[0]  # Минимальная как stop
                    else:  # SHORT
                        # Для SHORT: entry > target, stop > entry
                        entry_price = sorted_prices[1]  # Средняя цена как entry
                        target_price = sorted_prices[0]  # Минимальная как target
                        stop_loss = sorted_prices[-1]  # Максимальная как stop
                    
                    logger.debug(f"Создаем сигнал: {pair} {direction} Entry:{entry_price} Target:{target_price} Stop:{stop_loss}")
                    
                    # Валидация сигнала
                    if self._validate_signal(pair, direction, entry_price, target_price, stop_loss):
                        signal = {
                            'trading_pair': pair,
                            'direction': direction,
                            'entry_price': entry_price,
                            'target_price': target_price,
                            'stop_loss': stop_loss,
                            'confidence': 0.7,  # Средняя уверенность для пошагового извлечения
                            'source': 'step_pattern',
                            'channel_username': channel_username,
                            'message_id': message_id,
                            'extracted_at': datetime.utcnow()
                        }
                        signals.append(signal)
                        logger.debug(f"Сигнал создан: {signal}")
                    else:
                        logger.debug("Сигнал не прошел валидацию")
                    
                except Exception as e:
                    logger.warning(f"Ошибка создания сигнала для пары {pair}: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Ошибка пошагового извлечения: {e}")
        
        return signals
    
    def _extract_trading_pairs(self, text: str) -> List[str]:
        """Извлечение торговых пар"""
        pairs = []
        
        for pattern in self.pair_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    try:
                    if len(match.groups()) == 2:
                        # Формат: BTC/USDT
                        pair = f"{match.group(1).upper()}/{match.group(2).upper()}"
                        else:
                        # Формат: BTCUSDT
                        pair = match.group(1).upper()
                    
                    # Нормализация
                    if '/' not in pair and pair.endswith('USDT'):
                        base = pair[:-4]
                        pair = f"{base}/USDT"
                    
                    if self._is_valid_trading_pair(pair):
                        pairs.append(pair)
                        
                except Exception as e:
                    logger.warning(f"Ошибка извлечения пары: {e}")
                        continue
                
                    # Дополнительная проверка для случаев без явных пар
            if not pairs:
                # Ищем BTC, ETH и другие криптовалюты
                crypto_pattern = r'\b(BTC|ETH|BNB|ADA|SOL|DOT|MATIC|AVAX|LINK|UNI|SHIB|DOGE|PEPE|FLOKI|BONK|WIF|BOME|MYRO|POPCAT|BOOK)\b'
                crypto_matches = re.finditer(crypto_pattern, text, re.IGNORECASE)
                for match in crypto_matches:
                    crypto = match.group(1).upper()
                    pair = f"{crypto}/USDT"
                    if self._is_valid_trading_pair(pair):
                        pairs.append(pair)
                
                # Проверяем полные названия
                if 'bitcoin' in text.lower():
                    pairs.append('BTC/USDT')
                if 'ethereum' in text.lower():
                    pairs.append('ETH/USDT')
                
                # Проверяем формат ETHUSDT
                if 'ethusdt' in text.lower():
                    pairs.append('ETH/USDT')
        
        return list(set(pairs))  # Удаление дубликатов
    
    def _extract_direction(self, text: str) -> Optional[str]:
        """Извлечение направления"""
        text_lower = text.lower()
        
        # Подсчет ключевых слов
        long_count = sum(1 for pattern in self.direction_patterns['long'] 
                        for match in re.finditer(pattern, text_lower))
        short_count = sum(1 for pattern in self.direction_patterns['short'] 
                         for match in re.finditer(pattern, text_lower))
        
        if long_count > short_count:
            return 'LONG'
        elif short_count > long_count:
            return 'SHORT'
        
        return None
    
    def _extract_prices(self, text: str) -> List[float]:
        """Извлечение цен"""
        prices = []
        
        # Удаляем запятые из чисел
        text = re.sub(r'(\d+),(\d+)', r'\1\2', text)
            
        for pattern in self.price_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    price = float(match.group(1))
                    # Фильтрация разумных цен
                    if 0.000001 <= price <= 1000000:
                        prices.append(price)
                except (ValueError, IndexError):
                    continue
        
        # Дополнительный поиск чисел в тексте
        if len(prices) < 3:
            number_pattern = r'\b(\d+\.?\d*)\b'
            number_matches = re.finditer(number_pattern, text)
            for match in number_matches:
                try:
                    price = float(match.group(1))
                    # Фильтрация разумных цен для криптовалют
                    if 1 <= price <= 1000000:
                        prices.append(price)
                except (ValueError, IndexError):
                    continue
        
        return sorted(list(set(prices)))  # Удаление дубликатов и сортировка
    
    def _normalize_direction(self, direction: str) -> str:
        """Нормализация направления"""
        direction_lower = direction.lower()
        
        if any(word in direction_lower for word in ['long', 'buy', 'bullish', 'moon', 'pump', 'лонг', 'покупка']):
            return 'LONG'
        elif any(word in direction_lower for word in ['short', 'sell', 'bearish', 'dump', 'crash', 'шорт', 'продажа']):
            return 'SHORT'
        
        return 'LONG'  # По умолчанию
    
    def _is_valid_trading_pair(self, pair: str) -> bool:
        """Проверка валидности торговой пары"""
        # Поддерживаемые пары
        supported_pairs = [
            'BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'ADA/USDT', 'SOL/USDT',
            'DOT/USDT', 'MATIC/USDT', 'AVAX/USDT', 'LINK/USDT', 'UNI/USDT',
            'SHIB/USDT', 'DOGE/USDT', 'PEPE/USDT', 'FLOKI/USDT', 'BONK/USDT',
            'WIF/USDT', 'BOME/USDT', 'MYRO/USDT', 'POPCAT/USDT', 'BOOK/USDT'
        ]
        
        # Проверка известных пар
        if pair in supported_pairs:
            return True
        
        # Проверка паттерна крипто/USDT
        if re.match(r'^[A-Z]{2,10}/USDT$', pair):
            return True
        
        return False
    
    def _validate_signal(self, pair: str, direction: str, entry_price: float, target_price: float, stop_loss: float) -> bool:
        """Валидация сигнала"""
        try:
            # Проверка валидности пары
            if not self._is_valid_trading_pair(pair):
                return False
            
            # Проверка валидности цен
            if not (0.000001 <= entry_price <= 1000000):
                return False
            if not (0.000001 <= target_price <= 1000000):
                return False
            if not (0.000001 <= stop_loss <= 1000000):
                return False
            
            # Проверка логики цен
            if direction == 'LONG':
                if target_price <= entry_price:
                    return False
                if stop_loss >= entry_price:
                    return False
            else:  # SHORT
                if target_price >= entry_price:
                    return False
                if stop_loss <= entry_price:
                    return False
        
            return True
            
        except Exception as e:
            logger.warning(f"Ошибка валидации сигнала: {e}")
            return False

    def _remove_duplicate_signals(self, signals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Удаление дубликатов сигналов"""
        unique_signals = []
        seen = set()
        
        for signal in signals:
            # Создаем ключ для сравнения
            key = (
                signal.get('trading_pair', ''),
                signal.get('direction', ''),
                round(signal.get('entry_price', 0), 6),
                round(signal.get('target_price', 0), 6),
                round(signal.get('stop_loss', 0), 6)
            )
            
            if key not in seen:
                seen.add(key)
                unique_signals.append(signal)
        
        return unique_signals
    
    def extract_signal_info(self, text: str) -> Dict[str, Any]:
        """Извлечение информации о сигнале из текста (для совместимости)"""
        signals = self.extract_signals_from_text(text, "test", "test")
        if signals:
            return signals[0]
        return {}

# Экспорты для совместимости
SIGNAL_PATTERNS = SignalPatterns().signal_patterns

def extract_signal_info(text: str) -> Dict[str, Any]:
    """Функция для извлечения информации о сигнале из текста"""
    patterns = SignalPatterns()
    signals = patterns.extract_signals_from_text(text, "test", "test")
    if signals:
        return signals[0]
    return {} 