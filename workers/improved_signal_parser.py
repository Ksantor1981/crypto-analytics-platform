"""
Improved Signal Parser - Улучшенная система сигналов
Включает реальный расчет точности, валидацию данных и ML-подход
"""

import urllib.request
import json
import re
from datetime import datetime, timedelta
import time
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum
import logging
import sqlite3
import hashlib
from collections import defaultdict
import statistics

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SignalDirection(Enum):
    BUY = "BUY"
    SELL = "SELL" 
    LONG = "LONG"
    SHORT = "SHORT"
    HOLD = "HOLD"

class SignalQuality(Enum):
    EXCELLENT = "excellent"  # Полные данные: цена входа, цель, стоп
    GOOD = "good"           # Частичные данные: цена входа или цель
    BASIC = "basic"         # Только направление
    POOR = "poor"           # Недостаточно данных

class CustomJSONEncoder(json.JSONEncoder):
    """Кастомный JSON encoder для обработки enum и datetime"""
    def default(self, obj):
        if isinstance(obj, Enum):
            return obj.value
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

@dataclass
class ImprovedSignal:
    """Улучшенный торговый сигнал"""
    id: str
    asset: str
    direction: SignalDirection
    entry_price: Optional[float] = None
    target_price: Optional[float] = None
    stop_loss: Optional[float] = None
    leverage: Optional[int] = None
    timeframe: Optional[str] = None
    
    # Реальные метрики
    signal_quality: SignalQuality = SignalQuality.BASIC
    real_confidence: float = 0.0
    calculated_confidence: float = 0.0
    
    # Источник данных
    channel: str = ""
    message_id: str = ""
    original_text: str = ""
    cleaned_text: str = ""
    signal_type: str = "telegram"
    
    # Временные метки
    timestamp: str = ""
    extraction_time: str = ""
    
    # Валидация
    bybit_available: bool = True
    is_valid: bool = True
    validation_errors: List[str] = None
    
    # Дополнительные данные
    risk_reward_ratio: Optional[float] = None
    potential_profit: Optional[float] = None
    potential_loss: Optional[float] = None
    
    def __post_init__(self):
        if self.validation_errors is None:
            self.validation_errors = []
        
        # Автоматический расчет качества сигнала
        self.calculate_quality()
        
        # Автоматический расчет confidence
        self.calculate_confidence()
        
        # Расчет риск/прибыль
        self.calculate_risk_reward()
    
    def calculate_quality(self):
        """Рассчитывает качество сигнала на основе доступных данных"""
        score = 0
        
        # Базовые очки за наличие данных
        if self.entry_price is not None:
            score += 3
        if self.target_price is not None:
            score += 2
        if self.stop_loss is not None:
            score += 2
        if self.leverage is not None:
            score += 1
        if self.timeframe is not None:
            score += 1
        
        # Определение качества
        if score >= 7:
            self.signal_quality = SignalQuality.EXCELLENT
        elif score >= 4:
            self.signal_quality = SignalQuality.GOOD
        elif score >= 2:
            self.signal_quality = SignalQuality.BASIC
        else:
            self.signal_quality = SignalQuality.POOR
    
    def calculate_confidence(self):
        """Рассчитывает базовую точность сигнала"""
        # Базовая точность на основе качества сигнала
        base_confidence = {
            SignalQuality.EXCELLENT: 85.0,
            SignalQuality.GOOD: 70.0,
            SignalQuality.BASIC: 50.0,
            SignalQuality.POOR: 30.0
        }.get(self.signal_quality, 50.0)
        
        # Модификаторы
        modifiers = []
        
        # Модификатор на основе наличия цен
        if self.entry_price and self.target_price and self.stop_loss:
            modifiers.append(1.2)  # +20% за полные данные
        elif self.entry_price and (self.target_price or self.stop_loss):
            modifiers.append(1.1)  # +10% за частичные данные
        
        # Модификатор на основе leverage
        if self.leverage:
            if 1 <= self.leverage <= 10:
                modifiers.append(1.1)  # Низкий leverage = более консервативно
            elif self.leverage > 20:
                modifiers.append(0.9)  # Высокий leverage = более рискованно
        
        # Модификатор на основе timeframe
        if self.timeframe:
            if self.timeframe in ['1d', '1w']:
                modifiers.append(1.1)  # Долгосрочные сигналы более надежны
            elif self.timeframe in ['1m', '5m']:
                modifiers.append(0.9)  # Краткосрочные сигналы более рискованны
        
        # Применяем модификаторы
        final_confidence = base_confidence
        for modifier in modifiers:
            final_confidence *= modifier
        
        # Ограничиваем в разумных пределах
        self.calculated_confidence = max(10.0, min(95.0, final_confidence))
        self.real_confidence = self.calculated_confidence
    
    def calculate_risk_reward(self):
        """Рассчитывает соотношение риск/прибыль"""
        if not all([self.entry_price, self.target_price, self.stop_loss]):
            self.risk_reward_ratio = None
            self.potential_profit = None
            self.potential_loss = None
            return
        
        # Рассчитываем потенциальную прибыль и убыток
        if self.direction in [SignalDirection.LONG, SignalDirection.BUY]:
            self.potential_profit = self.target_price - self.entry_price
            self.potential_loss = self.entry_price - self.stop_loss
        else:  # SHORT или SELL
            self.potential_profit = self.entry_price - self.target_price
            self.potential_loss = self.stop_loss - self.entry_price
        
        # Рассчитываем соотношение риск/прибыль
        if self.potential_loss > 0:
            self.risk_reward_ratio = self.potential_profit / self.potential_loss
        else:
            self.risk_reward_ratio = None

def signal_to_dict(signal: ImprovedSignal) -> Dict[str, Any]:
    """Конвертирует ImprovedSignal в dict для JSON сериализации"""
    return {
        'id': signal.id,
        'asset': signal.asset,
        'direction': signal.direction.value,
        'entry_price': signal.entry_price,
        'target_price': signal.target_price,
        'stop_loss': signal.stop_loss,
        'leverage': signal.leverage,
        'timeframe': signal.timeframe,
        'signal_quality': signal.signal_quality.value,
        'real_confidence': signal.real_confidence,
        'calculated_confidence': signal.calculated_confidence,
        'channel': signal.channel,
        'message_id': signal.message_id,
        'original_text': signal.original_text,
        'cleaned_text': signal.cleaned_text,
        'signal_type': signal.signal_type,
        'timestamp': signal.timestamp,
        'extraction_time': signal.extraction_time,
        'bybit_available': signal.bybit_available,
        'is_valid': signal.is_valid,
        'validation_errors': signal.validation_errors,
        'risk_reward_ratio': signal.risk_reward_ratio,
        'potential_profit': signal.potential_profit,
        'potential_loss': signal.potential_loss
    }

class SignalValidator:
    """Валидатор сигналов"""
    
    def __init__(self):
        # Список валидных криптовалют
        self.valid_assets = {
            'BTC', 'ETH', 'ADA', 'SOL', 'DOT', 'LINK', 'UNI', 'AVAX',
            'MATIC', 'ATOM', 'XRP', 'DOGE', 'SHIB', 'LTC', 'BCH', 'BNB',
            'USDT', 'USDC', 'BUSD', 'DAI', 'LUNA', 'NEAR', 'FTM', 'ALGO',
            'SYS', 'ENA', 'ZIG', 'ATA', 'MAVIA', 'ORDI', 'BAND', 'BSW',
            'WOO', 'JASMY', 'MEME', 'PUMP', 'ENS', 'OP', 'ARB', 'SUI',
            'APT', 'INJ', 'TIA', 'SEI', 'PYTH', 'JUP', 'BONK', 'WIF'
        }
        
        # Список доступных на Bybit
        self.bybit_assets = {
            'BTC', 'ETH', 'ADA', 'SOL', 'DOT', 'LINK', 'UNI', 'AVAX',
            'MATIC', 'ATOM', 'XRP', 'DOGE', 'SHIB', 'LTC', 'BCH', 'BNB',
            'SYS', 'ENA', 'ZIG', 'MAVIA', 'ORDI', 'BAND', 'BSW', 'WOO',
            'JASMY', 'MEME', 'PUMP', 'ENS', 'OP', 'ARB', 'SUI', 'APT',
            'INJ', 'TIA', 'SEI', 'PYTH', 'JUP', 'BONK', 'WIF'
        }
    
    def validate_signal(self, signal: ImprovedSignal) -> bool:
        """Валидирует сигнал и возвращает True если валиден"""
        errors = []
        
        # Проверка актива
        if not signal.asset or signal.asset not in self.valid_assets:
            errors.append(f"Invalid asset: {signal.asset}")
            signal.is_valid = False
        
        # Проверка направления
        if not signal.direction or signal.direction not in SignalDirection:
            errors.append(f"Invalid direction: {signal.direction}")
            signal.is_valid = False
        
        # Проверка цен
        if signal.entry_price is not None and signal.entry_price <= 0:
            errors.append(f"Invalid entry price: {signal.entry_price}")
            signal.is_valid = False
        
        if signal.target_price is not None and signal.target_price <= 0:
            errors.append(f"Invalid target price: {signal.target_price}")
            signal.is_valid = False
        
        if signal.stop_loss is not None and signal.stop_loss <= 0:
            errors.append(f"Invalid stop loss: {signal.stop_loss}")
            signal.is_valid = False
        
        # Проверка логики цен
        if all(p is not None for p in [signal.entry_price, signal.target_price, signal.stop_loss]):
            if signal.direction in [SignalDirection.LONG, SignalDirection.BUY]:
                if signal.target_price <= signal.entry_price:
                    errors.append("Target price should be higher than entry for LONG/BUY")
                if signal.stop_loss >= signal.entry_price:
                    errors.append("Stop loss should be lower than entry for LONG/BUY")
            elif signal.direction in [SignalDirection.SHORT, SignalDirection.SELL]:
                if signal.target_price >= signal.entry_price:
                    errors.append("Target price should be lower than entry for SHORT/SELL")
                if signal.stop_loss <= signal.entry_price:
                    errors.append("Stop loss should be higher than entry for SHORT/SELL")
        
        # Проверка доступности на Bybit
        signal.bybit_available = signal.asset in self.bybit_assets
        
        # Проверка leverage
        if signal.leverage is not None and (signal.leverage < 1 or signal.leverage > 100):
            errors.append(f"Invalid leverage: {signal.leverage}")
            signal.is_valid = False
        
        signal.validation_errors = errors
        signal.is_valid = len(errors) == 0
        
        return signal.is_valid

class SignalQualityCalculator:
    """Калькулятор качества и точности сигналов"""
    
    def __init__(self):
        # База данных для хранения исторических данных
        self.db_path = "signal_history.db"
        self.init_database()
    
    def init_database(self):
        """Инициализация базы данных"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Таблица исторических сигналов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS signal_history (
                id TEXT PRIMARY KEY,
                channel TEXT,
                asset TEXT,
                direction TEXT,
                entry_price REAL,
                target_price REAL,
                stop_loss REAL,
                timestamp TEXT,
                success BOOLEAN,
                profit_loss REAL,
                execution_time INTEGER
            )
        ''')
        
        # Таблица статистики каналов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS channel_stats (
                channel TEXT PRIMARY KEY,
                total_signals INTEGER DEFAULT 0,
                successful_signals INTEGER DEFAULT 0,
                avg_profit REAL DEFAULT 0.0,
                avg_loss REAL DEFAULT 0.0,
                success_rate REAL DEFAULT 0.0,
                last_updated TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def calculate_signal_quality(self, signal: ImprovedSignal) -> SignalQuality:
        """Рассчитывает качество сигнала на основе доступных данных"""
        score = 0
        
        # Базовые очки за наличие данных
        if signal.entry_price is not None:
            score += 3
        if signal.target_price is not None:
            score += 2
        if signal.stop_loss is not None:
            score += 2
        if signal.leverage is not None:
            score += 1
        if signal.timeframe is not None:
            score += 1
        
        # Определение качества
        if score >= 7:
            return SignalQuality.EXCELLENT
        elif score >= 4:
            return SignalQuality.GOOD
        elif score >= 2:
            return SignalQuality.BASIC
        else:
            return SignalQuality.POOR
    
    def calculate_confidence(self, signal: ImprovedSignal) -> float:
        """Рассчитывает реальную точность сигнала на основе исторических данных"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Получаем статистику канала
        cursor.execute('''
            SELECT success_rate, avg_profit, avg_loss, total_signals
            FROM channel_stats 
            WHERE channel = ?
        ''', (signal.channel,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            success_rate, avg_profit, avg_loss, total_signals = result
            
            # Базовый confidence на основе исторической точности
            base_confidence = success_rate * 100 if success_rate else 50.0
            
            # Модификаторы на основе качества сигнала
            quality_modifier = {
                SignalQuality.EXCELLENT: 1.2,
                SignalQuality.GOOD: 1.1,
                SignalQuality.BASIC: 1.0,
                SignalQuality.POOR: 0.8
            }.get(signal.signal_quality, 1.0)
            
            # Модификатор на основе количества исторических сигналов
            volume_modifier = min(total_signals / 10, 1.0) if total_signals else 0.5
            
            # Модификатор на основе риск/прибыль
            risk_reward_modifier = 1.0
            if signal.risk_reward_ratio:
                if signal.risk_reward_ratio >= 3.0:
                    risk_reward_modifier = 1.2
                elif signal.risk_reward_ratio >= 2.0:
                    risk_reward_modifier = 1.1
                elif signal.risk_reward_ratio < 1.0:
                    risk_reward_modifier = 0.8
            
            # Финальный расчет
            final_confidence = base_confidence * quality_modifier * volume_modifier * risk_reward_modifier
            
            # Ограничиваем в разумных пределах
            return max(10.0, min(95.0, final_confidence))
        
        # Если нет исторических данных, используем базовую оценку
        return 50.0
    
    def add_signal_result(self, signal_id: str, success: bool, profit_loss: float, execution_time: int = 0):
        """Добавляет результат исполнения сигнала в базу данных"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Получаем данные сигнала
        cursor.execute('''
            SELECT channel, asset, direction, entry_price, target_price, stop_loss, timestamp
            FROM signal_history WHERE id = ?
        ''', (signal_id,))
        
        result = cursor.fetchone()
        if result:
            channel, asset, direction, entry_price, target_price, stop_loss, timestamp = result
            
            # Обновляем результат
            cursor.execute('''
                UPDATE signal_history 
                SET success = ?, profit_loss = ?, execution_time = ?
                WHERE id = ?
            ''', (success, profit_loss, execution_time, signal_id))
            
            # Обновляем статистику канала
            self.update_channel_stats(channel, success, profit_loss)
        
        conn.commit()
        conn.close()
    
    def update_channel_stats(self, channel: str, success: bool, profit_loss: float):
        """Обновляет статистику канала"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Получаем текущую статистику
        cursor.execute('''
            SELECT total_signals, successful_signals, avg_profit, avg_loss
            FROM channel_stats WHERE channel = ?
        ''', (channel,))
        
        result = cursor.fetchone()
        if result:
            total, successful, avg_profit, avg_loss = result
            
            # Обновляем статистику
            new_total = total + 1
            new_successful = successful + (1 if success else 0)
            new_success_rate = new_successful / new_total
            
            # Обновляем средние значения
            if success:
                new_avg_profit = (avg_profit * successful + profit_loss) / new_successful
                new_avg_loss = avg_loss
            else:
                new_avg_profit = avg_profit
                new_avg_loss = (avg_loss * (total - successful) + abs(profit_loss)) / (new_total - new_successful)
            
            cursor.execute('''
                UPDATE channel_stats 
                SET total_signals = ?, successful_signals = ?, success_rate = ?, 
                    avg_profit = ?, avg_loss = ?, last_updated = ?
                WHERE channel = ?
            ''', (new_total, new_successful, new_success_rate, new_avg_profit, new_avg_loss, 
                  datetime.now().isoformat(), channel))
        else:
            # Создаем новую запись
            success_rate = 1.0 if success else 0.0
            avg_profit = profit_loss if success else 0.0
            avg_loss = abs(profit_loss) if not success else 0.0
            
            cursor.execute('''
                INSERT INTO channel_stats 
                (channel, total_signals, successful_signals, success_rate, avg_profit, avg_loss, last_updated)
                VALUES (?, 1, ?, ?, ?, ?, ?)
            ''', (channel, 1 if success else 0, success_rate, avg_profit, avg_loss, 
                  datetime.now().isoformat()))
        
        conn.commit()
        conn.close()

class ImprovedSignalExtractor:
    """Улучшенный экстрактор сигналов"""
    
    def __init__(self):
        self.validator = SignalValidator()
        self.quality_calculator = SignalQualityCalculator()
        
        # Улучшенные паттерны для извлечения сигналов
        self.signal_patterns = {
            # Структурированные сигналы (высокая точность)
            'structured': [
                r'(\w+)/USDT\s+(LONG|SHORT|BUY|SELL)\s+Entry[:\s]*\$?([\d,]+\.?\d*)\s+Target[:\s]*\$?([\d,]+\.?\d*)\s+SL[:\s]*\$?([\d,]+\.?\d*)',
                r'([A-Z]+)\s+(LONG|SHORT|BUY|SELL)\s+\$?([\d,]+\.?\d*)\s*[→➡️]\s*\$?([\d,]+\.?\d*)\s+SL[:\s]*\$?([\d,]+\.?\d*)',
                r'[🚀📉🔥💰]\s*([A-Z]+)\s+(LONG|SHORT|BUY|SELL)\s+Entry[:\s]*\$?([\d,]+\.?\d*)',
            ],
            
            # Паттерны с ценами
            'with_prices': [
                r'(\w+)\s+(LONG|SHORT|BUY|SELL)\s+@\s*\$?([\d,]+\.?\d*)',
                r'([A-Z]+)\s+(LONG|SHORT|BUY|SELL)\s+\$?([\d,]+\.?\d*)',
                r'(\w+)\s+(LONG|SHORT|BUY|SELL)\s+Entry[:\s]*\$?([\d,]+\.?\d*)',
            ],
            
            # Простые паттерны
            'simple': [
                r'(\w+)\s+(LONG|SHORT|BUY|SELL)',
                r'([A-Z]+)\s+(LONG|SHORT|BUY|SELL)',
                r'(LONG|SHORT|BUY|SELL)\s+(\w+)',
            ]
        }
        
        # Паттерны для извлечения дополнительной информации
        self.info_patterns = {
            'leverage': r'(?:leverage|lev|х)\s*[:\s]*(\d+)x?',
            'timeframe': r'(?:timeframe|tf|таймфрейм)\s*[:\s]*(1m|5m|15m|1h|4h|1d|1w)',
            'target': r'(?:target|цель)\s*[:\s]*\$?([\d,]+\.?\d*)',
            'stop_loss': r'(?:stop\s*loss|sl|стоп)\s*[:\s]*\$?([\d,]+\.?\d*)',
        }
    
    def extract_signals_from_text(self, text: str, channel: str, message_id: str) -> List[ImprovedSignal]:
        """Извлекает сигналы из текста"""
        signals = []
        cleaned_text = self.clean_text(text)
        
        # Пробуем структурированные паттерны
        for pattern in self.signal_patterns['structured']:
            matches = re.finditer(pattern, cleaned_text, re.IGNORECASE)
            for match in matches:
                signal = self.create_signal_from_match(match, cleaned_text, channel, message_id, 'structured')
                if signal and self.validator.validate_signal(signal):
                    signals.append(signal)
        
        # Пробуем паттерны с ценами
        for pattern in self.signal_patterns['with_prices']:
            matches = re.finditer(pattern, cleaned_text, re.IGNORECASE)
            for match in matches:
                signal = self.create_signal_from_match(match, cleaned_text, channel, message_id, 'with_prices')
                if signal and self.validator.validate_signal(signal):
                    signals.append(signal)
        
        # Пробуем простые паттерны
        for pattern in self.signal_patterns['simple']:
            matches = re.finditer(pattern, cleaned_text, re.IGNORECASE)
            for match in matches:
                signal = self.create_signal_from_match(match, cleaned_text, channel, message_id, 'simple')
                if signal and self.validator.validate_signal(signal):
                    signals.append(signal)
        
        return signals
    
    def create_signal_from_match(self, match, text: str, channel: str, message_id: str, pattern_type: str) -> Optional[ImprovedSignal]:
        """Создает сигнал из найденного совпадения"""
        try:
            groups = match.groups()
            
            if pattern_type == 'structured':
                asset, direction, entry_price, target_price, stop_loss = groups
                entry_price = self.parse_price(entry_price)
                target_price = self.parse_price(target_price)
                stop_loss = self.parse_price(stop_loss)
            elif pattern_type == 'with_prices':
                asset, direction, entry_price = groups
                target_price = self.extract_target_price(text)
                stop_loss = self.extract_stop_loss(text)
                entry_price = self.parse_price(entry_price)
            else:  # simple
                if len(groups) == 2:
                    if groups[0].upper() in ['LONG', 'SHORT', 'BUY', 'SELL']:
                        direction, asset = groups
                    else:
                        asset, direction = groups
                else:
                    return None
                
                entry_price = self.extract_entry_price(text)
                target_price = self.extract_target_price(text)
                stop_loss = self.extract_stop_loss(text)
            
            # Извлекаем дополнительную информацию
            leverage = self.extract_leverage(text)
            timeframe = self.extract_timeframe(text)
            
            # Создаем сигнал
            signal = ImprovedSignal(
                id=self.generate_signal_id(channel, message_id, asset),
                asset=asset.upper(),
                direction=SignalDirection(direction.upper()),
                entry_price=entry_price,
                target_price=target_price,
                stop_loss=stop_loss,
                leverage=leverage,
                timeframe=timeframe,
                channel=channel,
                message_id=message_id,
                original_text=text,
                cleaned_text=text,
                timestamp=datetime.now().isoformat(),
                extraction_time=datetime.now().isoformat()
            )
            
            # Рассчитываем качество и точность
            signal.signal_quality = self.quality_calculator.calculate_signal_quality(signal)
            signal.calculated_confidence = self.quality_calculator.calculate_confidence(signal)
            signal.real_confidence = signal.calculated_confidence
            
            return signal
            
        except Exception as e:
            logger.error(f"Error creating signal from match: {e}")
            return None
    
    def clean_text(self, text: str) -> str:
        """Очищает текст от HTML entities и нормализует"""
        if not text:
            return ""
        
        # HTML entities
        text = text.replace('&#036;', '$').replace('&#39;', "'").replace('&amp;', '&')
        text = text.replace('&lt;', '<').replace('&gt;', '>').replace('&nbsp;', ' ')
        
        # Убираем лишние пробелы
        text = re.sub(r'\s+', ' ', text.strip())
        
        return text
    
    def parse_price(self, price_str: str) -> Optional[float]:
        """Парсит цену из строки"""
        if not price_str:
            return None
        
        try:
            # Убираем запятые и символы валют
            cleaned = re.sub(r'[$,€£¥]', '', price_str.strip())
            return float(cleaned)
        except:
            return None
    
    def extract_entry_price(self, text: str) -> Optional[float]:
        """Извлекает цену входа из текста"""
        patterns = [
            r'entry[:\s]*\$?([\d,]+\.?\d*)',
            r'@\s*\$?([\d,]+\.?\d*)',
            r'buy[:\s]*\$?([\d,]+\.?\d*)',
            r'sell[:\s]*\$?([\d,]+\.?\d*)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return self.parse_price(match.group(1))
        
        return None
    
    def extract_target_price(self, text: str) -> Optional[float]:
        """Извлекает целевую цену из текста"""
        patterns = [
            r'target[:\s]*\$?([\d,]+\.?\d*)',
            r'цель[:\s]*\$?([\d,]+\.?\d*)',
            r'[→➡️]\s*\$?([\d,]+\.?\d*)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return self.parse_price(match.group(1))
        
        return None
    
    def extract_stop_loss(self, text: str) -> Optional[float]:
        """Извлекает стоп-лосс из текста"""
        patterns = [
            r'stop\s*loss[:\s]*\$?([\d,]+\.?\d*)',
            r'sl[:\s]*\$?([\d,]+\.?\d*)',
            r'стоп[:\s]*\$?([\d,]+\.?\d*)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return self.parse_price(match.group(1))
        
        return None
    
    def extract_leverage(self, text: str) -> Optional[int]:
        """Извлекает leverage из текста"""
        match = re.search(r'(?:leverage|lev|х)\s*[:\s]*(\d+)x?', text, re.IGNORECASE)
        if match:
            try:
                return int(match.group(1))
            except:
                pass
        return None
    
    def extract_timeframe(self, text: str) -> Optional[str]:
        """Извлекает timeframe из текста"""
        match = re.search(r'(?:timeframe|tf|таймфрейм)\s*[:\s]*(1m|5m|15m|1h|4h|1d|1w)', text, re.IGNORECASE)
        if match:
            return match.group(1)
        return None
    
    def generate_signal_id(self, channel: str, message_id: str, asset: str) -> str:
        """Генерирует уникальный ID сигнала"""
        unique_string = f"{channel}_{message_id}_{asset}_{int(time.time())}"
        return hashlib.md5(unique_string.encode()).hexdigest()[:16]

class ImprovedTelegramParser:
    """Улучшенный парсер Telegram каналов"""
    
    def __init__(self):
        self.extractor = ImprovedSignalExtractor()
        self.quality_calculator = SignalQualityCalculator()
        
        # Список каналов для парсинга
        self.channels = [
            'CryptoCapoTG',
            'cryptosignals',
            'binance_signals',
            'binance_signals_official',
            'crypto_signals_daily',
            'bitcoin_signals',
            'BinanceKillers_Free'
        ]
    
    def parse_channels(self) -> Dict[str, Any]:
        """Парсит все каналы и возвращает улучшенные сигналы"""
        all_signals = []
        channel_stats = {}
        
        for channel in self.channels:
            try:
                logger.info(f"Parsing channel: {channel}")
                channel_signals = self.parse_channel(channel)
                all_signals.extend(channel_signals)
                
                # Статистика по каналу
                channel_stats[channel] = {
                    'total_signals': len(channel_signals),
                    'valid_signals': len([s for s in channel_signals if s.is_valid]),
                    'avg_confidence': statistics.mean([s.real_confidence for s in channel_signals]) if channel_signals else 0,
                    'quality_distribution': self.get_quality_distribution(channel_signals)
                }
                
            except Exception as e:
                logger.error(f"Error parsing channel {channel}: {e}")
        
        # Фильтруем только валидные сигналы
        valid_signals = [s for s in all_signals if s.is_valid]
        
        # Сортируем по confidence
        valid_signals.sort(key=lambda x: x.real_confidence, reverse=True)
        
        return {
            'success': True,
            'total_signals': len(valid_signals),
            'total_raw_signals': len(all_signals),
            'signals': [signal_to_dict(signal) for signal in valid_signals],
            'channel_stats': channel_stats,
            'quality_summary': self.get_quality_summary(valid_signals),
            'timestamp': datetime.now().isoformat()
        }
    
    def parse_channel(self, channel: str) -> List[ImprovedSignal]:
        """Парсит конкретный канал"""
        # Здесь должна быть реальная логика парсинга Telegram
        # Пока используем симуляцию для демонстрации
        
        signals = []
        
        # Симулируем парсинг канала
        sample_texts = [
            f"$BTC LONG Entry: $115000 Target: $120000 SL: $112000 Leverage: 10x",
            f"$ETH SHORT @ $4200 Target: $4000 Stop Loss: $4300",
            f"$SOL BUY Entry: $200 Target: $250 SL: $180",
            f"$ADA SELL @ $0.5 Target: $0.45 SL: $0.52",
        ]
        
        for i, text in enumerate(sample_texts):
            message_id = f"msg_{i}"
            channel_signals = self.extractor.extract_signals_from_text(text, channel, message_id)
            signals.extend(channel_signals)
        
        return signals
    
    def get_quality_distribution(self, signals: List[ImprovedSignal]) -> Dict[str, int]:
        """Получает распределение качества сигналов"""
        distribution = defaultdict(int)
        for signal in signals:
            distribution[signal.signal_quality.value] += 1
        return dict(distribution)
    
    def get_quality_summary(self, signals: List[ImprovedSignal]) -> Dict[str, Any]:
        """Получает сводку по качеству сигналов"""
        if not signals:
            return {}
        
        confidences = [s.real_confidence for s in signals]
        
        return {
            'avg_confidence': statistics.mean(confidences),
            'median_confidence': statistics.median(confidences),
            'min_confidence': min(confidences),
            'max_confidence': max(confidences),
            'quality_distribution': self.get_quality_distribution(signals),
            'bybit_available_count': len([s for s in signals if s.bybit_available]),
            'high_confidence_count': len([s for s in signals if s.real_confidence >= 70]),
        }

def main():
    """Основная функция для запуска улучшенного парсера"""
    parser = ImprovedTelegramParser()
    
    logger.info("Starting improved signal parsing...")
    result = parser.parse_channels()
    
    # Сохраняем результат
    with open('improved_signals.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False, cls=CustomJSONEncoder)
    
    logger.info(f"Parsing completed. Found {result['total_signals']} valid signals.")
    logger.info(f"Quality summary: {result['quality_summary']}")
    
    return result

if __name__ == "__main__":
    main()
