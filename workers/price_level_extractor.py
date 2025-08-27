"""
Price Level Extractor - Система улучшения извлечения цен и уровней
Улучшает качество извлечения сигналов с помощью продвинутого парсинга цен
"""

import json
import logging
import time
import re
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict
from decimal import Decimal, InvalidOperation

from improved_signal_parser import ImprovedSignal, ImprovedSignalExtractor, SignalDirection, SignalQuality

logger = logging.getLogger(__name__)

@dataclass
class PriceLevel:
    """Уровень цены"""
    value: float
    confidence: float
    source: str  # entry, target, stop_loss, support, resistance
    context: str  # Описание контекста
    line_number: int

@dataclass
class EnhancedPriceData:
    """Улучшенные данные о ценах"""
    entry_price: Optional[PriceLevel]
    target_prices: List[PriceLevel]
    stop_loss: Optional[PriceLevel]
    support_levels: List[PriceLevel]
    resistance_levels: List[PriceLevel]
    price_confidence: float
    validation_errors: List[str]
    suggestions: List[str]

class PriceLevelExtractor:
    """Система улучшения извлечения цен и уровней"""
    
    def __init__(self):
        # Паттерны для извлечения цен
        self.price_patterns = {
            'entry': [
                r'entry[:\s]+([\d,]+\.?\d*)',
                r'buy[:\s]+([\d,]+\.?\d*)',
                r'long[:\s]+([\d,]+\.?\d*)',
                r'enter[:\s]+([\d,]+\.?\d*)',
                r'position[:\s]+([\d,]+\.?\d*)'
            ],
            'target': [
                r'target[:\s]+([\d,]+\.?\d*)',
                r'take\s+profit[:\s]+([\d,]+\.?\d*)',
                r'tp[:\s]+([\d,]+\.?\d*)',
                r'profit[:\s]+([\d,]+\.?\d*)',
                r'goal[:\s]+([\d,]+\.?\d*)'
            ],
            'stop_loss': [
                r'stop\s+loss[:\s]+([\d,]+\.?\d*)',
                r'sl[:\s]+([\d,]+\.?\d*)',
                r'stop[:\s]+([\d,]+\.?\d*)',
                r'loss[:\s]+([\d,]+\.?\d*)',
                r'risk[:\s]+([\d,]+\.?\d*)'
            ],
            'support': [
                r'support[:\s]+([\d,]+\.?\d*)',
                r'floor[:\s]+([\d,]+\.?\d*)',
                r'bottom[:\s]+([\d,]+\.?\d*)',
                r'low[:\s]+([\d,]+\.?\d*)',
                r'buy\s+zone[:\s]+([\d,]+\.?\d*)'
            ],
            'resistance': [
                r'resistance[:\s]+([\d,]+\.?\d*)',
                r'ceiling[:\s]+([\d,]+\.?\d*)',
                r'top[:\s]+([\d,]+\.?\d*)',
                r'high[:\s]+([\d,]+\.?\d*)',
                r'sell\s+zone[:\s]+([\d,]+\.?\d*)'
            ]
        }
        
        # Паттерны для диапазонов цен
        self.range_patterns = [
            r'([\d,]+\.?\d*)\s*-\s*([\d,]+\.?\d*)',
            r'([\d,]+\.?\d*)\s*to\s*([\d,]+\.?\d*)',
            r'([\d,]+\.?\d*)\s*until\s*([\d,]+\.?\d*)',
            r'between\s+([\d,]+\.?\d*)\s+and\s+([\d,]+\.?\d*)'
        ]
        
        # Паттерны для процентов
        self.percentage_patterns = [
            r'([\d,]+\.?\d*)%',
            r'percent[:\s]+([\d,]+\.?\d*)',
            r'([\d,]+\.?\d*)\s+percent'
        ]
        
        # Валидные диапазоны цен для разных активов
        self.price_ranges = {
            'BTC': {'min': 1000, 'max': 1000000},
            'ETH': {'min': 10, 'max': 100000},
            'ADA': {'min': 0.01, 'max': 100},
            'SOL': {'min': 1, 'max': 10000},
            'DOT': {'min': 0.1, 'max': 1000},
            'LINK': {'min': 0.1, 'max': 1000},
            'MATIC': {'min': 0.01, 'max': 100},
            'AVAX': {'min': 0.1, 'max': 1000}
        }
        
        # Множители для разных единиц измерения
        self.unit_multipliers = {
            'k': 1000,
            'K': 1000,
            'm': 1000000,
            'M': 1000000,
            'b': 1000000000,
            'B': 1000000000
        }
    
    def extract_price_levels(self, text: str, asset: str = "BTC") -> EnhancedPriceData:
        """Извлекает все уровни цен из текста"""
        try:
            lines = text.split('\n')
            price_levels = {
                'entry_price': None,
                'target_prices': [],
                'stop_loss': None,
                'support_levels': [],
                'resistance_levels': []
            }
            
            # Извлекаем цены по типам
            for price_type, patterns in self.price_patterns.items():
                for line_num, line in enumerate(lines):
                    for pattern in patterns:
                        matches = re.findall(pattern, line, re.IGNORECASE)
                        for match in matches:
                            price_value = self._parse_price(match, asset)
                            if price_value:
                                price_level = PriceLevel(
                                    value=price_value,
                                    confidence=self._calculate_price_confidence(line, pattern),
                                    source=price_type,
                                    context=line.strip(),
                                    line_number=line_num
                                )
                                
                                if price_type == 'entry':
                                    price_levels['entry_price'] = price_level
                                elif price_type == 'target':
                                    price_levels['target_prices'].append(price_level)
                                elif price_type == 'stop_loss':
                                    price_levels['stop_loss'] = price_level
                                elif price_type == 'support':
                                    price_levels['support_levels'].append(price_level)
                                elif price_type == 'resistance':
                                    price_levels['resistance_levels'].append(price_level)
            
            # Извлекаем диапазоны цен
            self._extract_price_ranges(text, price_levels, asset)
            
            # Извлекаем проценты
            self._extract_percentages(text, price_levels, asset)
            
            # Валидируем и улучшаем цены
            validation_errors = []
            suggestions = []
            
            # Проверяем логику цен
            if price_levels['entry_price'] and price_levels['target_prices']:
                entry = price_levels['entry_price'].value
                targets = [t.value for t in price_levels['target_prices']]
                
                # Проверяем, что цели выше входа для LONG
                for target in targets:
                    if target <= entry:
                        validation_errors.append(f"Target price {target} should be higher than entry {entry} for LONG position")
                        suggestions.append(f"Consider adjusting target to {entry * 1.05:.2f} or higher")
            
            if price_levels['entry_price'] and price_levels['stop_loss']:
                entry = price_levels['entry_price'].value
                stop = price_levels['stop_loss'].value
                
                # Проверяем, что стоп ниже входа для LONG
                if stop >= entry:
                    validation_errors.append(f"Stop loss {stop} should be lower than entry {entry} for LONG position")
                    suggestions.append(f"Consider adjusting stop loss to {entry * 0.95:.2f} or lower")
            
            # Рассчитываем общую уверенность
            price_confidence = self._calculate_overall_confidence(price_levels)
            
            return EnhancedPriceData(
                entry_price=price_levels['entry_price'],
                target_prices=price_levels['target_prices'],
                stop_loss=price_levels['stop_loss'],
                support_levels=price_levels['support_levels'],
                resistance_levels=price_levels['resistance_levels'],
                price_confidence=price_confidence,
                validation_errors=validation_errors,
                suggestions=suggestions
            )
            
        except Exception as e:
            logger.error(f"Error extracting price levels: {e}")
            return EnhancedPriceData(
                entry_price=None,
                target_prices=[],
                stop_loss=None,
                support_levels=[],
                resistance_levels=[],
                price_confidence=0.0,
                validation_errors=[f"Error: {str(e)}"],
                suggestions=[]
            )
    
    def _parse_price(self, price_str: str, asset: str) -> Optional[float]:
        """Парсит строку цены в число"""
        try:
            # Убираем запятые и пробелы
            price_str = price_str.replace(',', '').strip()
            
            # Проверяем множители (k, m, b)
            multiplier = 1
            for unit, mult in self.unit_multipliers.items():
                if price_str.endswith(unit):
                    price_str = price_str[:-1]
                    multiplier = mult
                    break
            
            # Парсим число
            price = float(price_str) * multiplier
            
            # Проверяем валидность диапазона
            if asset in self.price_ranges:
                min_price = self.price_ranges[asset]['min']
                max_price = self.price_ranges[asset]['max']
                
                if price < min_price or price > max_price:
                    logger.warning(f"Price {price} for {asset} is outside valid range [{min_price}, {max_price}]")
                    return None
            
            return price
            
        except (ValueError, InvalidOperation) as e:
            logger.warning(f"Could not parse price '{price_str}': {e}")
            return None
    
    def _calculate_price_confidence(self, line: str, pattern: str) -> float:
        """Рассчитывает уверенность в цене"""
        confidence = 0.5  # Базовая уверенность
        
        # Бонус за четкий формат
        if ':' in line:
            confidence += 0.2
        
        # Бонус за наличие единиц измерения
        if any(unit in line for unit in ['$', 'USD', 'USDT']):
            confidence += 0.1
        
        # Бонус за структурированный текст
        if re.search(r'entry|target|stop|support|resistance', line, re.IGNORECASE):
            confidence += 0.2
        
        # Штраф за неопределенность
        if any(word in line.lower() for word in ['around', 'about', 'approximately', 'maybe', 'possibly']):
            confidence -= 0.2
        
        return min(max(confidence, 0.0), 1.0)
    
    def _extract_price_ranges(self, text: str, price_levels: Dict, asset: str):
        """Извлекает диапазоны цен"""
        for pattern in self.range_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if len(match) == 2:
                    price1 = self._parse_price(match[0], asset)
                    price2 = self._parse_price(match[1], asset)
                    
                    if price1 and price2:
                        # Определяем, какой из диапазонов что означает
                        if not price_levels['entry_price']:
                            # Первая цена как вход
                            price_levels['entry_price'] = PriceLevel(
                                value=price1,
                                confidence=0.7,
                                source='entry',
                                context=f"Range: {price1} - {price2}",
                                line_number=0
                            )
                        
                        if not price_levels['target_prices']:
                            # Вторая цена как цель
                            price_levels['target_prices'].append(PriceLevel(
                                value=price2,
                                confidence=0.7,
                                source='target',
                                context=f"Range: {price1} - {price2}",
                                line_number=0
                            ))
    
    def _extract_percentages(self, text: str, price_levels: Dict, asset: str):
        """Извлекает проценты и конвертирует их в цены"""
        if not price_levels['entry_price']:
            return  # Нужна базовая цена для расчета процентов
        
        entry_price = price_levels['entry_price'].value
        
        for pattern in self.percentage_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    percentage = float(match)
                    
                    # Определяем контекст процента
                    context_words = text.lower().split()
                    if any(word in context_words for word in ['target', 'profit', 'goal']):
                        # Процент как цель
                        target_price = entry_price * (1 + percentage / 100)
                        price_levels['target_prices'].append(PriceLevel(
                            value=target_price,
                            confidence=0.6,
                            source='target',
                            context=f"{percentage}% from entry",
                            line_number=0
                        ))
                    elif any(word in context_words for word in ['stop', 'loss', 'risk']):
                        # Процент как стоп-лосс
                        stop_price = entry_price * (1 - percentage / 100)
                        if not price_levels['stop_loss']:
                            price_levels['stop_loss'] = PriceLevel(
                                value=stop_price,
                                confidence=0.6,
                                source='stop_loss',
                                context=f"{percentage}% stop loss",
                                line_number=0
                            )
                except ValueError:
                    continue
    
    def _calculate_overall_confidence(self, price_levels: Dict) -> float:
        """Рассчитывает общую уверенность в ценах"""
        total_confidence = 0.0
        total_prices = 0
        
        if price_levels['entry_price']:
            total_confidence += price_levels['entry_price'].confidence
            total_prices += 1
        
        for target in price_levels['target_prices']:
            total_confidence += target.confidence
            total_prices += 1
        
        if price_levels['stop_loss']:
            total_confidence += price_levels['stop_loss'].confidence
            total_prices += 1
        
        for support in price_levels['support_levels']:
            total_confidence += support.confidence
            total_prices += 1
        
        for resistance in price_levels['resistance_levels']:
            total_confidence += resistance.confidence
            total_prices += 1
        
        return total_confidence / max(total_prices, 1)
    
    def enhance_signal_with_price_data(self, signal: ImprovedSignal, text: str) -> ImprovedSignal:
        """Улучшает сигнал с помощью улучшенных данных о ценах"""
        try:
            # Извлекаем улучшенные данные о ценах
            price_data = self.extract_price_levels(text, signal.asset)
            
            # Обновляем цены сигнала, если они не были найдены или улучшены
            if not signal.entry_price and price_data.entry_price:
                signal.entry_price = price_data.entry_price.value
                signal.real_confidence = max(signal.real_confidence or 0, 
                                           price_data.entry_price.confidence * 100)
            
            if not signal.target_price and price_data.target_prices:
                # Берем самую уверенную цель
                best_target = max(price_data.target_prices, key=lambda x: x.confidence)
                signal.target_price = best_target.value
                signal.real_confidence = max(signal.real_confidence or 0, 
                                           best_target.confidence * 100)
            
            if not signal.stop_loss and price_data.stop_loss:
                signal.stop_loss = price_data.stop_loss.value
                signal.real_confidence = max(signal.real_confidence or 0, 
                                           price_data.stop_loss.confidence * 100)
            
            # Добавляем дополнительные цели
            if len(price_data.target_prices) > 1:
                signal.additional_targets = [
                    {
                        'price': target.value,
                        'confidence': target.confidence,
                        'context': target.context
                    }
                    for target in price_data.target_prices
                ]
            
            # Добавляем уровни поддержки и сопротивления
            if price_data.support_levels or price_data.resistance_levels:
                signal.technical_levels = {
                    'support': [
                        {
                            'price': support.value,
                            'confidence': support.confidence,
                            'context': support.context
                        }
                        for support in price_data.support_levels
                    ],
                    'resistance': [
                        {
                            'price': resistance.value,
                            'confidence': resistance.confidence,
                            'context': resistance.context
                        }
                        for resistance in price_data.resistance_levels
                    ]
                }
            
            # Добавляем метаданные о ценах
            signal.price_metadata = {
                'price_confidence': price_data.price_confidence,
                'validation_errors': price_data.validation_errors,
                'suggestions': price_data.suggestions,
                'total_price_levels': (
                    (1 if price_data.entry_price else 0) +
                    len(price_data.target_prices) +
                    (1 if price_data.stop_loss else 0) +
                    len(price_data.support_levels) +
                    len(price_data.resistance_levels)
                )
            }
            
            # Добавляем предупреждения
            if price_data.validation_errors:
                if not hasattr(signal, 'warnings') or signal.warnings is None:
                    signal.warnings = []
                signal.warnings.extend(price_data.validation_errors)
            
            # Обновляем качество сигнала на основе уверенности в ценах
            if price_data.price_confidence > 0.8:
                if signal.signal_quality == SignalQuality.MEDIUM:
                    signal.signal_quality = SignalQuality.GOOD
                elif signal.signal_quality == SignalQuality.GOOD:
                    signal.signal_quality = SignalQuality.EXCELLENT
            
            return signal
            
        except Exception as e:
            logger.error(f"Error enhancing signal with price data: {e}")
            return signal
    
    def validate_price_logic(self, signal: ImprovedSignal) -> Dict[str, Any]:
        """Валидирует логику цен в сигнале"""
        validation_result = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'suggestions': []
        }
        
        try:
            if not signal.entry_price:
                validation_result['errors'].append("Missing entry price")
                validation_result['is_valid'] = False
                return validation_result
            
            entry = signal.entry_price
            
            # Проверяем цели
            if signal.target_price:
                target = signal.target_price
                if signal.direction == SignalDirection.LONG:
                    if target <= entry:
                        validation_result['errors'].append(
                            f"Target price {target} should be higher than entry {entry} for LONG position"
                        )
                        validation_result['suggestions'].append(
                            f"Consider target price around {entry * 1.05:.2f}"
                        )
                        validation_result['is_valid'] = False
                else:  # SHORT
                    if target >= entry:
                        validation_result['errors'].append(
                            f"Target price {target} should be lower than entry {entry} for SHORT position"
                        )
                        validation_result['suggestions'].append(
                            f"Consider target price around {entry * 0.95:.2f}"
                        )
                        validation_result['is_valid'] = False
            
            # Проверяем стоп-лосс
            if signal.stop_loss:
                stop = signal.stop_loss
                if signal.direction == SignalDirection.LONG:
                    if stop >= entry:
                        validation_result['errors'].append(
                            f"Stop loss {stop} should be lower than entry {entry} for LONG position"
                        )
                        validation_result['suggestions'].append(
                            f"Consider stop loss around {entry * 0.95:.2f}"
                        )
                        validation_result['is_valid'] = False
                else:  # SHORT
                    if stop <= entry:
                        validation_result['errors'].append(
                            f"Stop loss {stop} should be higher than entry {entry} for SHORT position"
                        )
                        validation_result['suggestions'].append(
                            f"Consider stop loss around {entry * 1.05:.2f}"
                        )
                        validation_result['is_valid'] = False
            
            # Проверяем риск/прибыль
            if signal.target_price and signal.stop_loss:
                if signal.direction == SignalDirection.LONG:
                    profit = target - entry
                    loss = entry - stop
                else:  # SHORT
                    profit = entry - target
                    loss = stop - entry
                
                if loss > 0:
                    risk_reward = profit / loss
                    if risk_reward < 1.0:
                        validation_result['warnings'].append(
                            f"Risk/Reward ratio is {risk_reward:.2f}, consider better risk management"
                        )
                    elif risk_reward > 5.0:
                        validation_result['warnings'].append(
                            f"Risk/Reward ratio is {risk_reward:.2f}, target might be too optimistic"
                        )
            
            # Проверяем дополнительные цели
            if hasattr(signal, 'additional_targets') and signal.additional_targets:
                for i, target_data in enumerate(signal.additional_targets):
                    target_price = target_data['price']
                    if signal.direction == SignalDirection.LONG:
                        if target_price <= entry:
                            validation_result['warnings'].append(
                                f"Additional target {i+1} ({target_price}) should be higher than entry"
                            )
                    else:  # SHORT
                        if target_price >= entry:
                            validation_result['warnings'].append(
                                f"Additional target {i+1} ({target_price}) should be lower than entry"
                            )
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Error validating price logic: {e}")
            validation_result['errors'].append(f"Validation error: {str(e)}")
            validation_result['is_valid'] = False
            return validation_result

def main():
    """Тестирование экстрактора цен"""
    extractor = PriceLevelExtractor()
    
    print("=== Тестирование экстрактора цен ===")
    
    # Тестовые тексты
    test_texts = [
        "BTC LONG Entry: 50000 Target: 55000 Stop: 48000 - Strong bullish momentum",
        "ETH SHORT Entry: 3000 Target: 2800 Stop: 3200 - Bearish divergence",
        "ADA LONG Entry: 0.45 Target: 0.55 Stop: 0.42 - Volume increasing",
        "SOL Entry around 120-125, target 140-150, stop 110-115",
        "DOT Support at 6.5, resistance at 7.5, entry 6.8, target 7.2"
    ]
    
    for i, text in enumerate(test_texts, 1):
        print(f"\n{i}. Анализ текста: {text[:50]}...")
        
        # Извлекаем цены
        price_data = extractor.extract_price_levels(text, "BTC")
        
        print(f"  💰 Entry: {price_data.entry_price.value if price_data.entry_price else 'Not found'}")
        print(f"  🎯 Targets: {[t.value for t in price_data.target_prices]}")
        print(f"  🛑 Stop Loss: {price_data.stop_loss.value if price_data.stop_loss else 'Not found'}")
        print(f"  📊 Support: {[s.value for s in price_data.support_levels]}")
        print(f"  📈 Resistance: {[r.value for r in price_data.resistance_levels]}")
        print(f"  ✅ Confidence: {price_data.price_confidence:.3f}")
        
        if price_data.validation_errors:
            print(f"  ❌ Errors: {price_data.validation_errors}")
        
        if price_data.suggestions:
            print(f"  💡 Suggestions: {price_data.suggestions}")
    
    # Тестируем улучшение сигналов
    print(f"\n🔧 Тестирование улучшения сигналов:")
    
    test_signal = ImprovedSignal(
        id="test_1",
        asset="BTC",
        direction=SignalDirection.LONG,
        entry_price=50000,
        target_price=55000,
        stop_loss=48000,
        leverage=10,
        timeframe="4H",
        channel="test_channel",
        message_id="test_message",
        original_text="BTC LONG Entry: 50000 Target: 55000 Stop: 48000 - Strong bullish momentum",
        cleaned_text="BTC LONG Entry: 50000 Target: 55000 Stop: 48000 - Strong bullish momentum",
        timestamp=datetime.now(),
        extraction_time=0.1,
        signal_quality=SignalQuality.MEDIUM,
        real_confidence=65.0,
        calculated_confidence=60.0,
        bybit_available=True,
        is_valid=True,
        validation_errors=[],
        risk_reward_ratio=2.5,
        potential_profit=10.0,
        potential_loss=4.0
    )
    
    enhanced_signal = extractor.enhance_signal_with_price_data(test_signal, test_signal.original_text)
    
    print(f"  📈 Сигнал до улучшения: {test_signal.real_confidence:.1f}% уверенности")
    print(f"  📈 Сигнал после улучшения: {enhanced_signal.real_confidence:.1f}% уверенности")
    
    if hasattr(enhanced_signal, 'price_metadata') and enhanced_signal.price_metadata:
        print(f"  💰 Уверенность в ценах: {enhanced_signal.price_metadata['price_confidence']:.3f}")
        print(f"  📊 Всего уровней цен: {enhanced_signal.price_metadata['total_price_levels']}")
    
    # Тестируем валидацию
    print(f"\n🔍 Тестирование валидации цен:")
    validation = extractor.validate_price_logic(enhanced_signal)
    
    print(f"  ✅ Валидность: {validation['is_valid']}")
    if validation['errors']:
        print(f"  ❌ Ошибки: {validation['errors']}")
    if validation['warnings']:
        print(f"  ⚠️ Предупреждения: {validation['warnings']}")
    if validation['suggestions']:
        print(f"  💡 Предложения: {validation['suggestions']}")

if __name__ == "__main__":
    main()
