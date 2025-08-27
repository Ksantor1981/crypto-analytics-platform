"""
Парсер структурированных торговых сигналов
Специально для каналов типа BinanceKillers с четким форматом
"""

import re
import json
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass

@dataclass
class StructuredSignal:
    """Структурированный торговый сигнал"""
    signal_id: str
    asset: str
    direction: str
    entry_range: List[float]
    targets: List[float]
    stop_loss: float
    leverage: Optional[str] = None
    timeframe: Optional[str] = None
    confidence: float = 95.0
    channel: str = ""
    timestamp: str = ""

class StructuredSignalParser:
    """Парсер структурированных сигналов"""
    
    def __init__(self):
        # Паттерны для извлечения структурированных сигналов
        self.patterns = {
            'signal_id': [
                r'SIGNAL\s+ID[:\s]*#?(\d+)',
                r'ID[:\s]*#?(\d+)',
                r'#(\d+)'
            ],
            'asset': [
                r'COIN[:\s]*\$?([A-Z]+)/?([A-Z]*)',
                r'PAIR[:\s]*\$?([A-Z]+)/?([A-Z]*)',
                r'\$([A-Z]+)/?([A-Z]*)'
            ],
            'direction': [
                r'(LONG|SHORT|BUY|SELL)\s*[📈📉🚀🔥]?',
                r'Direction[:\s]*(LONG|SHORT|BUY|SELL)'
            ],
            'entry': [
                r'ENTRY[:\s]*(\d+(?:[.,]\d+)?)\s*[-–—]\s*(\d+(?:[.,]\d+)?)',
                r'Entry[:\s]*(\d+(?:[.,]\d+)?)\s*[-–—]\s*(\d+(?:[.,]\d+)?)',
                r'Buy[:\s]*(\d+(?:[.,]\d+)?)\s*[-–—]\s*(\d+(?:[.,]\d+)?)'
            ],
            'targets': [
                r'TARGETS?[:\s]*((?:\d+(?:[.,]\d+)?\s*[-–—]\s*)*\d+(?:[.,]\d+)?)',
                r'Target[:\s]*((?:\d+(?:[.,]\d+)?\s*[-–—]\s*)*\d+(?:[.,]\d+)?)',
                r'TP[:\s]*((?:\d+(?:[.,]\d+)?\s*[-–—]\s*)*\d+(?:[.,]\d+)?)'
            ],
            'stop_loss': [
                r'STOP\s+LOSS[:\s]*(\d+(?:[.,]\d+)?)',
                r'Stop[:\s]*(\d+(?:[.,]\d+)?)',
                r'SL[:\s]*(\d+(?:[.,]\d+)?)'
            ],
            'leverage': [
                r'\((\d+-\d+x)\)',
                r'(\d+-\d+x)',
                r'Leverage[:\s]*(\d+-\d+x)'
            ],
            'timeframe': [
                r'(\d+[Hh])\s*[-–—]',
                r'Timeframe[:\s]*(\d+[Hh])',
                r'(\d+[Hh])'
            ]
        }
    
    def parse_structured_signal(self, text: str, channel: str = "") -> Optional[StructuredSignal]:
        """Парсит структурированный сигнал из текста"""
        
        if not text:
            return None
        
        # Извлекаем компоненты сигнала
        signal_id = self._extract_signal_id(text)
        asset = self._extract_asset(text)
        direction = self._extract_direction(text)
        entry_range = self._extract_entry_range(text)
        targets = self._extract_targets(text)
        stop_loss = self._extract_stop_loss(text)
        leverage = self._extract_leverage(text)
        timeframe = self._extract_timeframe(text)
        
        # Проверяем, что у нас есть основные компоненты
        if not asset or not direction or not entry_range:
            return None
        
        return StructuredSignal(
            signal_id=signal_id or f"signal_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            asset=asset,
            direction=direction,
            entry_range=entry_range,
            targets=targets,
            stop_loss=stop_loss,
            leverage=leverage,
            timeframe=timeframe,
            confidence=95.0,  # Высокая уверенность для структурированных сигналов
            channel=channel,
            timestamp=datetime.now().isoformat()
        )
    
    def _extract_signal_id(self, text: str) -> Optional[str]:
        """Извлекает ID сигнала"""
        for pattern in self.patterns['signal_id']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        return None
    
    def _extract_asset(self, text: str) -> Optional[str]:
        """Извлекает торговую пару"""
        for pattern in self.patterns['asset']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                base = match.group(1)
                quote = match.group(2) if len(match.groups()) > 1 else "USDT"
                return f"{base}/{quote}"
        return None
    
    def _extract_direction(self, text: str) -> Optional[str]:
        """Извлекает направление"""
        for pattern in self.patterns['direction']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).upper()
        return None
    
    def _extract_entry_range(self, text: str) -> List[float]:
        """Извлекает диапазон входа"""
        for pattern in self.patterns['entry']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    start = float(match.group(1).replace(',', ''))
                    end = float(match.group(2).replace(',', ''))
                    return [start, end]
                except ValueError:
                    continue
        return []
    
    def _extract_targets(self, text: str) -> List[float]:
        """Извлекает целевые цены"""
        for pattern in self.patterns['targets']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                targets_text = match.group(1)
                # Разбираем список целей
                targets = []
                for target_match in re.finditer(r'(\d+(?:[.,]\d+)?)', targets_text):
                    try:
                        target = float(target_match.group(1).replace(',', ''))
                        targets.append(target)
                    except ValueError:
                        continue
                return targets
        return []
    
    def _extract_stop_loss(self, text: str) -> Optional[float]:
        """Извлекает стоп-лосс"""
        for pattern in self.patterns['stop_loss']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    return float(match.group(1).replace(',', ''))
                except ValueError:
                    continue
        return None
    
    def _extract_leverage(self, text: str) -> Optional[str]:
        """Извлекает кредитное плечо"""
        for pattern in self.patterns['leverage']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        return None
    
    def _extract_timeframe(self, text: str) -> Optional[str]:
        """Извлекает временной фрейм"""
        for pattern in self.patterns['timeframe']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).upper()
        return None
    
    def convert_to_standard_format(self, signal: StructuredSignal) -> Dict:
        """Конвертирует структурированный сигнал в стандартный формат"""
        
        # Берем среднюю цену входа
        entry_price = sum(signal.entry_range) / len(signal.entry_range) if signal.entry_range else None
        
        # Берем первую цель как основную
        target_price = signal.targets[0] if signal.targets else None
        
        return {
            'id': signal.signal_id,
            'asset': signal.asset.split('/')[0] if '/' in signal.asset else signal.asset,
            'direction': signal.direction,
            'entry_price': entry_price,
            'target_price': target_price,
            'stop_loss': signal.stop_loss,
            'confidence': signal.confidence,
            'channel': signal.channel,
            'message_id': signal.signal_id,
            'timestamp': signal.timestamp,
            'extraction_time': datetime.now().isoformat(),
            'original_text': f"Structured Signal: {signal.asset} {signal.direction}",
            'cleaned_text': f"Structured Signal: {signal.asset} {signal.direction}",
            'bybit_available': True,
            'signal_type': 'structured',
            'entry_range': signal.entry_range,
            'all_targets': signal.targets,
            'leverage': signal.leverage,
            'timeframe': signal.timeframe
        }

def test_structured_parser():
    """Тестирует парсер на примере сигнала из BinanceKillers"""
    
    # Пример текста из изображения
    test_text = """
    SIGNAL ID: #1956
    COIN: $BTC/USDT (3-5x)
    Direction: LONG 📈
    ENTRY: 112207 - 110500
    TARGETS: 113500 - 114800 - 117000 - 123236
    STOP LOSS: 109638
    """
    
    parser = StructuredSignalParser()
    signal = parser.parse_structured_signal(test_text, "BinanceKillers")
    
    if signal:
        print("✅ Структурированный сигнал успешно извлечен!")
        print(f"ID: {signal.signal_id}")
        print(f"Asset: {signal.asset}")
        print(f"Direction: {signal.direction}")
        print(f"Entry Range: {signal.entry_range}")
        print(f"Targets: {signal.targets}")
        print(f"Stop Loss: {signal.stop_loss}")
        print(f"Leverage: {signal.leverage}")
        print(f"Timeframe: {signal.timeframe}")
        
        # Конвертируем в стандартный формат
        standard_signal = parser.convert_to_standard_format(signal)
        print(f"\n📊 Стандартный формат:")
        print(f"Asset: {standard_signal['asset']}")
        print(f"Direction: {standard_signal['direction']}")
        print(f"Entry: ${standard_signal['entry_price']:,.0f}")
        print(f"Target: ${standard_signal['target_price']:,.0f}")
        print(f"Stop Loss: ${standard_signal['stop_loss']:,.0f}")
        print(f"Confidence: {standard_signal['confidence']}%")
        
        return standard_signal
    else:
        print("❌ Не удалось извлечь структурированный сигнал")
        return None

if __name__ == "__main__":
    test_structured_parser()
