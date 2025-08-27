#!/usr/bin/env python3
"""
Улучшенный экстрактор цен для извлечения реальных цен из текста сигналов
"""

import re
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple

class EnhancedPriceExtractor:
    """Улучшенный экстрактор цен из текста сигналов"""
    
    def __init__(self):
        # Расширенные паттерны для извлечения цен из реальных сообщений
        self.price_patterns = [
            # Entry patterns - более гибкие
            r'entry[:\s]*(\d+(?:\.\d+)?)',
            r'вход[:\s]*(\d+(?:\.\d+)?)',
            r'buy[:\s]*(\d+(?:\.\d+)?)',
            r'long[:\s]*(\d+(?:\.\d+)?)',
            r'@[:\s]*(\d+(?:\.\d+)?)',
            r'entry\s*at\s*(\d+(?:\.\d+)?)',
            r'long\s*entry\s*at\s*(\d+(?:\.\d+)?)',
            r'short\s*entry\s*at\s*(\d+(?:\.\d+)?)',
            
            # Target patterns
            r'target[:\s]*(\d+(?:\.\d+)?)',
            r'цель[:\s]*(\d+(?:\.\d+)?)',
            r'take[:\s]*profit[:\s]*(\d+(?:\.\d+)?)',
            r'tp[:\s]*(\d+(?:\.\d+)?)',
            
            # Stop loss patterns
            r'stop[:\s]*loss[:\s]*(\d+(?:\.\d+)?)',
            r'стоп[:\s]*(\d+(?:\.\d+)?)',
            r'sl[:\s]*(\d+(?:\.\d+)?)',
            
            # Support/Resistance patterns
            r'support[:\s]*(\d+(?:\.\d+)?)',
            r'resistance[:\s]*(\d+(?:\.\d+)?)',
            r'поддержка[:\s]*(\d+(?:\.\d+)?)',
            r'сопротивление[:\s]*(\d+(?:\.\d+)?)',
            
            # FVG (Fair Value Gap) patterns
            r'FVG[:\s]*\((\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)\)',
            r'fair\s*value\s*gap[:\s]*(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)',
            
            # Order Block patterns
            r'OB\+[:\s]*\((\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)\)',
            r'order\s*block[:\s]*(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)',
            
            # General price patterns
            r'(\d+(?:\.\d+)?)\s*(?:usdt|btc|eth|ada|sol|dot|link|matic|avax)',
            r'(\d+(?:\.\d+)?)\s*\$',
            r'\$\s*(\d+(?:\.\d+)?)',
            
            # Цены в скобках
            r'\((\d+(?:\.\d+)?)\)',
            r'\[(\d+(?:\.\d+)?)\]',
            
            # Цены после ключевых слов
            r'below\s*(\d+(?:\.\d+)?)',
            r'above\s*(\d+(?:\.\d+)?)',
            r'at\s*(\d+(?:\.\d+)?)',
            r'from\s*(\d+(?:\.\d+)?)',
            r'to\s*(\d+(?:\.\d+)?)',
            
            # Цены в диапазонах
            r'(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)',
            r'(\d+(?:\.\d+)?)\s*to\s*(\d+(?:\.\d+)?)',
        ]
        
        # Паттерны для направления
        self.direction_patterns = {
            'long': [r'long', r'buy', r'покупка', r'бычий', r'bullish', r'bounce', r'relief'],
            'short': [r'short', r'sell', r'продажа', r'медвежий', r'bearish', r'breakdown', r'drop']
        }
        
        # Паттерны для активов
        self.asset_patterns = [
            r'(BTC|ETH|ADA|SOL|DOT|LINK|MATIC|AVAX)/?(USDT|USD)?',
            r'(Bitcoin|Ethereum|Cardano|Solana|Polkadot|Chainlink|Polygon|Avalanche)',
            r'#(BTC|ETH|ADA|SOL|DOT|LINK|MATIC|AVAX)',
        ]
        
        # Паттерны для таймфреймов
        self.timeframe_patterns = [
            r'(1m|5m|15m|30m|1h|4h|1d|1w)',
            r'(минута|час|день|неделя|месяц)',
            r'(minute|hour|day|week|month)',
            r'(weekly|daily|hourly)',
        ]
        
        # Паттерны для плеча
        self.leverage_patterns = [
            r'(\d+)x',
            r'плечо[:\s]*(\d+)',
            r'leverage[:\s]*(\d+)',
        ]

    def extract_prices(self, text: str) -> Dict[str, float]:
        """Извлекает цены из текста с улучшенной логикой"""
        text_lower = text.lower()
        has_trading_keywords = any(k in text_lower for k in [
            'entry','target','tp','stop','sl','buy','sell','long','short','resistance','support','below','above',' @','entry at','long entry','short entry'
        ])
        prices = {
            'entry_price': None,
            'target_price': None,
            'stop_loss': None
        }
        
        # Извлекаем все числа из текста
        all_numbers = re.findall(r'(\d+(?:\.\d+)?)', text)
        numbers = [float(num) for num in all_numbers]
        
        if not numbers:
            return prices
        
        # Сортируем числа для лучшего анализа
        numbers.sort()
        
        # Ищем цены по паттернам
        for pattern in self.price_patterns:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            if matches:
                if isinstance(matches[0], tuple):
                    # Для диапазонов типа FVG (110532 - 109241)
                    if len(matches[0]) >= 2:
                        prices['entry_price'] = float(matches[0][0])
                        prices['target_price'] = float(matches[0][1])
                else:
                    price = float(matches[0])
                    
                    # Определяем тип цены по контексту
                    if 'entry' in pattern or 'вход' in pattern or 'buy' in pattern or 'long' in pattern:
                        prices['entry_price'] = price
                    elif 'target' in pattern or 'цель' in pattern or 'tp' in pattern:
                        prices['target_price'] = price
                    elif 'stop' in pattern or 'стоп' in pattern or 'sl' in pattern:
                        prices['stop_loss'] = price
                    elif 'support' in pattern or 'поддержка' in pattern:
                        prices['stop_loss'] = price
                    elif 'resistance' in pattern or 'сопротивление' in pattern:
                        prices['target_price'] = price
        
        # Дополнительные паттерны для stop loss
        stop_loss_patterns = [
            r'stop\s*loss[:\s]*(\d+(?:\.\d+)?)',
            r'стоп[:\s]*(\d+(?:\.\d+)?)',
            r'sl[:\s]*(\d+(?:\.\d+)?)',
            r'stop[:\s]*(\d+(?:\.\d+)?)',
            r'below\s*(\d+(?:\.\d+)?)',
            r'under\s*(\d+(?:\.\d+)?)',
        ]
        
        for pattern in stop_loss_patterns:
            match = re.search(pattern, text_lower, re.IGNORECASE)
            if match and not prices['stop_loss']:
                prices['stop_loss'] = float(match.group(1))
                break
        
        # Если не нашли по паттернам, используем эвристики ТОЛЬКО когда есть явные торговые слова
        if has_trading_keywords and not any(prices.values()) and len(numbers) >= 2:
            # Для SHORT: entry > target > stop
            # Для LONG: stop < entry < target
            if 'short' in text_lower or 'sell' in text_lower:
                if len(numbers) >= 3:
                    prices['entry_price'] = numbers[-1]  # Самая высокая цена
                    prices['target_price'] = numbers[1]  # Средняя цена
                    prices['stop_loss'] = numbers[0]     # Самая низкая цена
                elif len(numbers) == 2:
                    prices['entry_price'] = numbers[1]   # Высокая цена
                    prices['target_price'] = numbers[0]  # Низкая цена
            else:  # LONG по умолчанию
                if len(numbers) >= 3:
                    prices['entry_price'] = numbers[1]   # Средняя цена
                    prices['target_price'] = numbers[-1] # Самая высокая цена
                    prices['stop_loss'] = numbers[0]     # Самая низкая цена
                elif len(numbers) == 2:
                    prices['entry_price'] = numbers[0]   # Низкая цена
                    prices['target_price'] = numbers[1]  # Высокая цена
        
        # Дополнительная логика для извлечения entry price
        if not prices['entry_price']:
            entry_patterns = [
                r'entry[:\s]*(\d+(?:\.\d+)?)',
                r'вход[:\s]*(\d+(?:\.\d+)?)',
                r'buy[:\s]*(\d+(?:\.\d+)?)',
                r'long[:\s]*(\d+(?:\.\d+)?)',
                r'@[:\s]*(\d+(?:\.\d+)?)',
                r'entry\s*at\s*(\d+(?:\.\d+)?)',
                r'long\s*entry\s*at\s*(\d+(?:\.\d+)?)',
                r'short\s*entry\s*at\s*(\d+(?:\.\d+)?)',
                r'from\s*(\d+(?:\.\d+)?)',
                r'at\s*(\d+(?:\.\d+)?)',
            ]
            
            for pattern in entry_patterns:
                match = re.search(pattern, text_lower, re.IGNORECASE)
                if match and not prices['entry_price']:
                    prices['entry_price'] = float(match.group(1))
                    break
        
        # Если все еще нет stop loss, вычисляем его на основе entry и target
        if has_trading_keywords and prices['entry_price'] and prices['target_price'] and not prices['stop_loss']:
            entry = prices['entry_price']
            target = prices['target_price']
            
            if 'short' in text_lower or 'sell' in text_lower:
                # Для SHORT: stop loss выше entry
                prices['stop_loss'] = entry * 1.02  # 2% выше entry
            else:
                # Для LONG: stop loss ниже entry
                prices['stop_loss'] = entry * 0.98  # 2% ниже entry
        
        return prices

    def validate_prices(self, asset: str, entry_price: float, target_price: float = None, stop_loss: float = None) -> bool:
        """Строгая валидация цен"""
        if not entry_price:
            return False
            
        # Минимальные и максимальные цены для основных активов
        price_limits = {
            'BTC': (10000, 200000), 'bitcoin': (10000, 200000),
            'ETH': (1000, 10000), 'ethereum': (1000, 10000),
            'SOL': (50, 500), 'solana': (50, 500),
            'ADA': (0.1, 10), 'cardano': (0.1, 10),
            'LINK': (5, 100), 'chainlink': (5, 100),
            'MATIC': (0.1, 5), 'polygon': (0.1, 5)
        }
        
        asset_upper = asset.upper()
        price_limit = price_limits.get(asset_upper, (0.01, 1000000))
        min_price, max_price = price_limit
        
        # Проверяем entry_price
        if entry_price < min_price or entry_price > max_price:
            return False
            
        # Проверяем target_price (должна быть разумной)
        if target_price is not None:
            # Target не должна быть 0 или отрицательной
            if target_price <= 0:
                return False
            # Target не должна быть равна entry
            if target_price == entry_price:
                return False
            # Target не должна быть больше чем 10x от entry для основных активов
            if asset_upper in ['BTC', 'BITCOIN', 'ETH', 'ETHEREUM']:
                if target_price > entry_price * 10:
                    return False
                # И не должна быть меньше чем 0.1x от entry
                if target_price < entry_price * 0.1:
                    return False
            # Для остальных активов максимум 100x
            elif target_price > entry_price * 100:
                return False
            # И не должна быть меньше чем 0.01x от entry
            elif target_price < entry_price * 0.01:
                return False
                
        # Проверяем stop_loss (не должна быть меньше чем 0.1x от entry)
        if stop_loss:
            if stop_loss < entry_price * 0.1:
                return False
                
        return True

    def extract_direction(self, text: str) -> str:
        """Извлекает направление торговли"""
        text_lower = text.lower()
        has_trading_keywords = any(k in text_lower for k in ['buy','sell','long','short'])
        
        for direction, patterns in self.direction_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    return direction.upper()
        
        return 'UNKNOWN'

    def extract_asset(self, text: str) -> str:
        """Извлекает актив"""
        for pattern in self.asset_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                asset = match.group(1)
                if asset in ['Bitcoin', 'BTC']:
                    return 'BTC'
                elif asset in ['Ethereum', 'ETH']:
                    return 'ETH'
                elif asset in ['Cardano', 'ADA']:
                    return 'ADA'
                elif asset in ['Solana', 'SOL']:
                    return 'SOL'
                elif asset in ['Polkadot', 'DOT']:
                    return 'DOT'
                elif asset in ['Chainlink', 'LINK']:
                    return 'LINK'
                elif asset in ['Polygon', 'MATIC']:
                    return 'MATIC'
                elif asset in ['Avalanche', 'AVAX']:
                    return 'AVAX'
                else:
                    return asset
        
        return 'UNKNOWN'

    def extract_timeframe(self, text: str) -> str:
        """Извлекает таймфрейм"""
        for pattern in self.timeframe_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).upper()
        
        return '1H'  # По умолчанию

    def extract_leverage(self, text: str) -> int:
        """Извлекает плечо"""
        for pattern in self.leverage_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return int(match.group(1))
        
        return 1  # По умолчанию

    def extract_signal(self, text: str, channel: str = '', message_id: str = '') -> Dict:
        """Извлекает полный сигнал из текста"""
        # Очищаем текст
        cleaned_text = re.sub(r'[^\w\s\d\.\,\-\+\$\%\@\#]', ' ', text)
        
        # Извлекаем данные
        prices = self.extract_prices(text)
        direction = self.extract_direction(text)
        asset = self.extract_asset(text)
        timeframe = self.extract_timeframe(text)
        leverage = self.extract_leverage(text)
        
        # Рассчитываем уверенность
        confidence = self.calculate_confidence(text, prices, direction, asset)
        
        # Создаем сигнал
        signal = {
            'id': f"{asset}_{int(datetime.now().timestamp())}",
            'asset': asset,
            'direction': direction,
            'entry_price': prices['entry_price'],
            'target_price': prices['target_price'],
            'stop_loss': prices['stop_loss'],
            'leverage': leverage,
            'timeframe': timeframe,
            'signal_quality': self.assess_quality(prices, direction, asset),
            'real_confidence': confidence,
            'calculated_confidence': confidence,
            'channel': channel,
            'message_id': message_id,
            'original_text': text,
            'cleaned_text': cleaned_text,
            'signal_type': 'enhanced_extraction',
            'timestamp': datetime.now().isoformat(),
            'extraction_time': datetime.now().isoformat(),
            'bybit_available': True,
            'is_valid': self.validate_signal(prices, direction, asset) and self.validate_prices(asset, prices['entry_price'], prices['target_price'], prices['stop_loss']),
            'validation_errors': [],
            'risk_reward_ratio': self.calculate_risk_reward(prices),
            'potential_profit': self.calculate_potential_profit(prices),
            'potential_loss': self.calculate_potential_loss(prices)
        }
        
        return signal

    def calculate_confidence(self, text: str, prices: Dict, direction: str, asset: str) -> float:
        """Рассчитывает уверенность в сигнале"""
        confidence = 50.0  # Базовая уверенность
        
        # Бонусы за наличие данных
        if prices['entry_price']:
            confidence += 10
        if prices['target_price']:
            confidence += 10
        if prices['stop_loss']:
            confidence += 10
        if direction != 'UNKNOWN':
            confidence += 10
        if asset != 'UNKNOWN':
            confidence += 10
        
        # Бонус за качество текста
        if len(text) > 50:
            confidence += 5
        
        return min(confidence, 100.0)

    def assess_quality(self, prices: Dict, direction: str, asset: str) -> str:
        """Оценивает качество сигнала"""
        score = 0
        
        if prices['entry_price']:
            score += 1
        if prices['target_price']:
            score += 1
        if prices['stop_loss']:
            score += 1
        if direction != 'UNKNOWN':
            score += 1
        if asset != 'UNKNOWN':
            score += 1
        
        if score >= 4:
            return 'high'
        elif score >= 2:
            return 'medium'
        else:
            return 'poor'

    def validate_signal(self, prices: Dict, direction: str, asset: str) -> bool:
        """Проверяет валидность сигнала"""
        return (
            asset != 'UNKNOWN' and
            direction != 'UNKNOWN' and
            (prices['entry_price'] or prices['target_price'] or prices['stop_loss'])
        )

    def calculate_risk_reward(self, prices: Dict) -> float:
        """Рассчитывает соотношение риск/прибыль"""
        if not prices['entry_price'] or not prices['target_price'] or not prices['stop_loss']:
            return 0.0
        
        entry = prices['entry_price']
        target = prices['target_price']
        stop = prices['stop_loss']
        
        if entry > target:  # SHORT
            profit = entry - target
            loss = stop - entry
        else:  # LONG
            profit = target - entry
            loss = entry - stop
        
        if loss == 0:
            return 0.0
        
        return profit / loss

    def calculate_potential_profit(self, prices: Dict) -> float:
        """Рассчитывает потенциальную прибыль"""
        if not prices['entry_price'] or not prices['target_price']:
            return 0.0
        
        entry = prices['entry_price']
        target = prices['target_price']
        
        return abs(target - entry)

    def calculate_potential_loss(self, prices: Dict) -> float:
        """Рассчитывает потенциальный убыток"""
        if not prices['entry_price'] or not prices['stop_loss']:
            return 0.0
        
        entry = prices['entry_price']
        stop = prices['stop_loss']
        
        return abs(entry - stop)

    def extract_multiple_signals(self, texts: List[str], channel: str = '') -> List[Dict]:
        """Извлекает множественные сигналы из списка текстов"""
        signals = []
        
        for i, text in enumerate(texts):
            try:
                signal = self.extract_signal(text, channel, f"msg_{i}")
                if signal['is_valid']:
                    signals.append(signal)
            except Exception as e:
                print(f"Ошибка извлечения сигнала из текста {i}: {e}")
        
        return signals

# Пример использования
if __name__ == "__main__":
    extractor = EnhancedPriceExtractor()
    
    # Тестовые тексты
    test_texts = [
        "BTC SHORT Entry: 50000, Target: 48000, Stop Loss: 52000",
        "ETH LONG @ 3000, TP: 3500, SL: 2800",
        "ADA/USDT: Support Level Test Cardano testing key support level at 0.42. Long entry at 0.45, target 0.55, stop loss at 0.42",
        "SOL/USDT: Resistance Breakout Solana breaking above resistance at 125. Long entry at 125, target 140, stop loss at 120"
    ]
    
    for text in test_texts:
        signal = extractor.extract_signal(text)
        print(f"Текст: {text}")
        print(f"Сигнал: {json.dumps(signal, indent=2, ensure_ascii=False)}")
        print("-" * 50)