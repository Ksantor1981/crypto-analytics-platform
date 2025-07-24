"""
Service for validating crypto signals in channels
"""
from typing import List, Dict, Any, Optional
import re
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class SignalValidationService:
    """Service for validating crypto trading signals."""
    
    def __init__(self):
        # Паттерны для поиска сигналов в тексте
        self.signal_patterns = [
            # Паттерн для LONG сигналов
            r'(?i)(long|buy|покупка|лонг).*?(\w+usdt).*?entry.*?(\d+\.?\d*).*?target.*?(\d+\.?\d*).*?stop.*?(\d+\.?\d*)',
            # Паттерн для SHORT сигналов
            r'(?i)(short|sell|продажа|шорт).*?(\w+usdt).*?entry.*?(\d+\.?\d*).*?target.*?(\d+\.?\d*).*?stop.*?(\d+\.?\d*)',
            # Упрощенный паттерн для любых сигналов
            r'(\w+usdt).*?(long|short|buy|sell).*?(\d+\.?\d*).*?(\d+\.?\d*).*?(\d+\.?\d*)',
            # Паттерн с эмодзи
            r'🚀.*?(\w+usdt).*?(\d+\.?\d*).*?(\d+\.?\d*).*?(\d+\.?\d*)',
            r'📉.*?(\w+usdt).*?(\d+\.?\d*).*?(\d+\.?\d*).*?(\d+\.?\d*)'
        ]
        
        # Список поддерживаемых криптопар
        self.supported_pairs = [
            'BTCUSDT', 'ETHUSDT', 'ADAUSDT', 'SOLUSDT', 'DOGEUSDT',
            'BNBUSDT', 'XRPUSDT', 'DOTUSDT', 'LINKUSDT', 'MATICUSDT',
            'AVAXUSDT', 'UNIUSDT', 'ATOMUSDT', 'LTCUSDT', 'BCHUSDT'
        ]
    
    def extract_signals_from_text(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract trading signals from text content.
        """
        signals = []
        
        if not text:
            return signals
        
        # Приводим текст к нижнему регистру для поиска
        text_lower = text.lower()
        
        # Проверяем каждый паттерн
        for pattern in self.signal_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE | re.DOTALL)
            
            for match in matches:
                try:
                    signal = self._parse_signal_match(match, text)
                    if signal:
                        signals.append(signal)
                except Exception as e:
                    logger.warning(f"Error parsing signal match: {e}")
                    continue
        
        # Удаляем дубликаты
        unique_signals = []
        seen = set()
        
        for signal in signals:
            signal_key = f"{signal['symbol']}_{signal['signal_type']}_{signal['entry_price']}"
            if signal_key not in seen:
                seen.add(signal_key)
                unique_signals.append(signal)
        
        return unique_signals
    
    def _parse_signal_match(self, match, original_text: str) -> Optional[Dict[str, Any]]:
        """
        Parse a regex match into a signal dictionary.
        """
        try:
            groups = match.groups()
            
            if len(groups) >= 5:
                # Полный паттерн с направлением
                direction = groups[0].lower()
                symbol = groups[1].upper()
                entry_price = float(groups[2])
                target_price = float(groups[3])
                stop_loss = float(groups[4])
            elif len(groups) >= 4:
                # Упрощенный паттерн
                symbol = groups[0].upper()
                direction = groups[1].lower()
                entry_price = float(groups[2])
                target_price = float(groups[3])
                stop_loss = float(groups[4]) if len(groups) > 4 else entry_price * 0.98
            else:
                return None
            
            # Определяем тип сигнала
            if direction in ['long', 'buy', 'покупка', 'лонг']:
                signal_type = 'long'
            elif direction in ['short', 'sell', 'продажа', 'шорт']:
                signal_type = 'short'
            else:
                signal_type = 'long'  # По умолчанию
            
            # Проверяем валидность символа
            if symbol not in self.supported_pairs:
                return None
            
            # Проверяем валидность цен
            if entry_price <= 0 or target_price <= 0 or stop_loss <= 0:
                return None
            
            # Рассчитываем уверенность на основе качества данных
            confidence = self._calculate_confidence(entry_price, target_price, stop_loss, signal_type)
            
            return {
                'symbol': symbol,
                'signal_type': signal_type,
                'entry_price': entry_price,
                'target_price': target_price,
                'stop_loss': stop_loss,
                'confidence': confidence,
                'original_text': original_text,
                'metadata': {
                    'extracted_at': datetime.utcnow().isoformat(),
                    'pattern_matched': True
                }
            }
            
        except (ValueError, IndexError) as e:
            logger.warning(f"Error parsing signal: {e}")
            return None
    
    def _calculate_confidence(self, entry_price: float, target_price: float, 
                            stop_loss: float, signal_type: str) -> float:
        """
        Calculate confidence level for a signal based on various factors.
        """
        confidence = 0.5  # Базовая уверенность
        
        try:
            # Рассчитываем соотношение риск/прибыль
            if signal_type == 'long':
                risk = entry_price - stop_loss
                reward = target_price - entry_price
            else:  # short
                risk = stop_loss - entry_price
                reward = entry_price - target_price
            
            if risk > 0:
                risk_reward_ratio = reward / risk
                
                # Увеличиваем уверенность на основе соотношения риск/прибыль
                if risk_reward_ratio >= 3.0:
                    confidence += 0.3
                elif risk_reward_ratio >= 2.0:
                    confidence += 0.2
                elif risk_reward_ratio >= 1.5:
                    confidence += 0.1
                elif risk_reward_ratio < 0.5:
                    confidence -= 0.2
            
            # Проверяем разумность цен
            if signal_type == 'long':
                if target_price > entry_price and stop_loss < entry_price:
                    confidence += 0.1
                else:
                    confidence -= 0.3
            else:  # short
                if target_price < entry_price and stop_loss > entry_price:
                    confidence += 0.1
                else:
                    confidence -= 0.3
            
            # Ограничиваем уверенность
            confidence = max(0.1, min(0.95, confidence))
            
        except ZeroDivisionError:
            confidence = 0.3
        
        return round(confidence, 2)
    
    def validate_channel_content(self, channel_content: List[str]) -> List[Dict[str, Any]]:
        """
        Validate channel content for trading signals.
        """
        all_signals = []
        
        for content in channel_content:
            signals = self.extract_signals_from_text(content)
            all_signals.extend(signals)
        
        # Удаляем дубликаты и сортируем по уверенности
        unique_signals = []
        seen = set()
        
        for signal in all_signals:
            signal_key = f"{signal['symbol']}_{signal['signal_type']}_{signal['entry_price']}"
            if signal_key not in seen:
                seen.add(signal_key)
                unique_signals.append(signal)
        
        # Сортируем по уверенности (убывание)
        unique_signals.sort(key=lambda x: x['confidence'], reverse=True)
        
        return unique_signals
    
    def is_valid_signal(self, signal: Dict[str, Any]) -> bool:
        """
        Check if a signal is valid.
        """
        required_fields = ['symbol', 'signal_type', 'entry_price', 'target_price', 'stop_loss']
        
        # Проверяем наличие всех обязательных полей
        for field in required_fields:
            if field not in signal:
                return False
        
        # Проверяем валидность символа
        if signal['symbol'] not in self.supported_pairs:
            return False
        
        # Проверяем валидность цен
        if (signal['entry_price'] <= 0 or 
            signal['target_price'] <= 0 or 
            signal['stop_loss'] <= 0):
            return False
        
        # Проверяем валидность типа сигнала
        if signal['signal_type'] not in ['long', 'short']:
            return False
        
        # Проверяем логику цен
        if signal['signal_type'] == 'long':
            if signal['target_price'] <= signal['entry_price'] or signal['stop_loss'] >= signal['entry_price']:
                return False
        else:  # short
            if signal['target_price'] >= signal['entry_price'] or signal['stop_loss'] <= signal['entry_price']:
                return False
        
        return True
