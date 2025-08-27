"""
Универсальный парсер структурированных торговых сигналов
Поддерживает все форматы: BinanceKillers, Wolf of Trading, Crypto Inner Circle и др.
"""

import re
import json
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

@dataclass
class UniversalSignal:
    """Универсальная структура торгового сигнала"""
    signal_id: str
    asset: str
    direction: str
    entry_price: Optional[float] = None
    entry_range: Optional[List[float]] = None
    entry_type: str = "market"  # market, limit, range
    targets: List[float] = None
    stop_loss: Optional[float] = None
    stop_loss_percent: Optional[float] = None
    leverage: Optional[str] = None
    timeframe: Optional[str] = None
    confidence: float = 95.0
    channel: str = ""
    timestamp: str = ""
    signal_type: str = "regular"
    risk_level: str = "medium"

class UniversalSignalParser:
    """Универсальный парсер для всех форматов сигналов"""
    
    def __init__(self):
        # Расширенные паттерны для всех форматов
        self.patterns = {
            # ID сигнала
            'signal_id': [
                r'SIGNAL\s+ID[:\s]*#?(\d+)',
                r'ID[:\s]*#?(\d+)',
                r'#(\d+)',
                r'Signal[:\s]*#?(\d+)'
            ],
            
            # Торговая пара
            'asset': [
                r'COIN[:\s]*\$?([A-Z]+)/?([A-Z]*)',
                r'PAIR[:\s]*\$?([A-Z]+)/?([A-Z]*)',
                r'\$([A-Z]+)/?([A-Z]*)',
                r'([A-Z]+)/?([A-Z]*)\s*[|⚡]',
                r'([A-Z]+)\s*[|⚡]',
                r'([A-Z]+)\s+(LONG|SHORT|BUY|SELL)',
                r'([A-Z]+)\s+в\s+(LONG|SHORT|BUY|SELL)',
                r'Открываем\s+пару\s+([A-Z]+)\s*/\s*([A-Z]+)',
                r'Заходим\s+([A-Z]+)\s+(LONG|SHORT)'
            ],
            
            # Направление
            'direction': [
                r'(LONG|SHORT|BUY|SELL)\s*[📈📉🚀🔥]?',
                r'Direction[:\s]*(LONG|SHORT|BUY|SELL)',
                r'🔴\s*(SHORT)',
                r'🟢\s*(LONG)',
                r'([A-Z]+)\s+в\s+(SHORT|LONG)',
                r'([A-Z]+)\s+(SHORT|LONG)\s+\d+x',
                r'Signal\s+Type[:\s]*Regular\s*\(([A-Z]+)\)'
            ],
            
            # Цена входа
            'entry': [
                # Диапазон входа
                r'ENTRY[:\s]*(\d+(?:[.,]\d+)?)\s*[-–—]\s*(\d+(?:[.,]\d+)?)',
                r'Entry[:\s]*(\d+(?:[.,]\d+)?)\s*[-–—]\s*(\d+(?:[.,]\d+)?)',
                r'👆\s*Entry[:\s]*(\d+(?:[.,]\d+)?)\s*[-–—]\s*(\d+(?:[.,]\d+)?)',
                r'Вход[:\s]*(\d+(?:[.,]\d+)?)\s*[-–—]\s*(\d+(?:[.,]\d+)?)',
                # Конкретная цена
                r'Entry\s+Targets?[:\s]*(\d+(?:[.,]\d+)?)',
                r'Рыночный\s+ордер[:\s]*(\d+(?:[.,]\d+)?)',
                r'Вход[:\s]*по\s+рынку',
                r'➡️\s*Enter\s*-\s*market',
                # Market entry
                r'по\s+рынку',
                r'market'
            ],
            
            # Целевые цены
            'targets': [
                # Множественные цели с разделителями
                r'TARGETS?[:\s]*((?:\d+(?:[.,]\d+)?\s*[-–—\s]*)*\d+(?:[.,]\d+)?)',
                r'Target[:\s]*((?:\d+(?:[.,]\d+)?\s*[-–—\s]*)*\d+(?:[.,]\d+)?)',
                r'TP[:\s]*((?:\d+(?:[.,]\d+)?\s*[-–—\s]*)*\d+(?:[.,]\d+)?)',
                r'📌\s*Target[:\s]*((?:\d+(?:[.,]\d+)?\s*[-–—\s]*)*\d+(?:[.,]\d+)?)',
                r'Тейк[:\s]*((?:\d+(?:[.,]\d+)?\s*[/\s]*)*\d+(?:[.,]\d+)?)',
                r'Take-Profit\s+Targets?[:\s]*((?:\d+(?:[.,]\d+)?\s*[,,\s]*)*\d+(?:[.,]\d+)?)',
                r'Тейки[:\s]*((?:\d+(?:[.,]\d+)?\s*[,,\s]*)*\d+(?:[.,]\d+)?)',
                # Отдельные цели
                r'🎯\s*Target\s*(\d+)[:\s]*(\d+(?:[.,]\d+)?)',
                r'Target\s*(\d+)[:\s]*(\d+(?:[.,]\d+)?)'
            ],
            
            # Стоп-лосс
            'stop_loss': [
                r'STOP\s+LOSS[:\s]*(\d+(?:[.,]\d+)?)',
                r'Stop[:\s]*(\d+(?:[.,]\d+)?)',
                r'SL[:\s]*(\d+(?:[.,]\d+)?)',
                r'❌\s*Stop[:\s]*(\d+(?:[.,]\d+)?)',
                r'❌\s*StopLoss[:\s]*(\d+(?:[.,]\d+)?)',
                r'Стоп[:\s]*(\d+(?:[.,]\d+)?)',
                r'Stop\s+Targets?[:\s]*(\d+(?:[.,]\d+)?)',
                # Процентный стоп
                r'Stop\s+Targets?[:\s]*(\d+)-(\d+)%',
                r'Стоп[:\s]*(\d+)-(\d+)%'
            ],
            
            # Кредитное плечо
            'leverage': [
                r'\((\d+-\d+x)\)',
                r'(\d+-\d+x)',
                r'Leverage[:\s]*(\d+-\d+x)',
                r'🌐\s*Leverage[:\s]*(\d+x)',
                r'Плечо[:\s]*(\d+x)',
                r'Leverage[:\s]*Cross\s*\((\d+x)\)',
                r'Cross\s*\((\d+x)\)',
                r'([A-Z]+)\s+(LONG|SHORT)\s+(\d+x)'
            ],
            
            # Временной фрейм
            'timeframe': [
                r'(\d+[Hh])\s*[-–—]',
                r'Timeframe[:\s]*(\d+[Hh])',
                r'(\d+[Hh])',
                r'(\d+[Mm])',
                r'(\d+[Dd])'
            ]
        }
    
    def parse_signal(self, text: str, channel: str = "") -> Optional[UniversalSignal]:
        """Парсит сигнал из текста"""
        
        if not text:
            return None
        
        # Извлекаем компоненты
        signal_id = self._extract_signal_id(text)
        asset = self._extract_asset(text)
        direction = self._extract_direction(text)
        entry_info = self._extract_entry_info(text)
        targets = self._extract_targets(text)
        stop_loss_info = self._extract_stop_loss_info(text)
        leverage = self._extract_leverage(text)
        timeframe = self._extract_timeframe(text)
        
        # Проверяем основные компоненты
        if not asset or not direction:
            return None
        
        return UniversalSignal(
            signal_id=signal_id or f"signal_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            asset=asset,
            direction=direction,
            entry_price=entry_info.get('price'),
            entry_range=entry_info.get('range'),
            entry_type=entry_info.get('type', 'market'),
            targets=targets,
            stop_loss=stop_loss_info.get('price'),
            stop_loss_percent=stop_loss_info.get('percent'),
            leverage=leverage,
            timeframe=timeframe,
            confidence=95.0,
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
                groups = match.groups()
                if len(groups) >= 2 and groups[1]:
                    return f"{groups[0]}/{groups[1]}"
                else:
                    return f"{groups[0]}/USDT"
        return None
    
    def _extract_direction(self, text: str) -> Optional[str]:
        """Извлекает направление"""
        for pattern in self.patterns['direction']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                groups = match.groups()
                # Ищем направление в группах
                for group in groups:
                    if group and group.upper() in ['LONG', 'SHORT', 'BUY', 'SELL']:
                        return group.upper()
        return None
    
    def _extract_entry_info(self, text: str) -> Dict:
        """Извлекает информацию о входе"""
        result = {'type': 'market', 'price': None, 'range': None}
        
        # Проверяем на market entry
        if any(re.search(pattern, text, re.IGNORECASE) for pattern in ['по\s+рынку', 'market']):
            result['type'] = 'market'
            return result
        
        # Ищем диапазон входа
        for pattern in self.patterns['entry']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                groups = match.groups()
                if len(groups) >= 2:
                    try:
                        start = float(groups[0].replace(',', ''))
                        end = float(groups[1].replace(',', ''))
                        result['type'] = 'range'
                        result['range'] = [start, end]
                        result['price'] = (start + end) / 2
                        return result
                    except ValueError:
                        continue
                elif len(groups) == 1:
                    try:
                        price = float(groups[0].replace(',', ''))
                        result['type'] = 'limit'
                        result['price'] = price
                        return result
                    except ValueError:
                        continue
        
        return result
    
    def _extract_targets(self, text: str) -> List[float]:
        """Извлекает целевые цены"""
        targets = []
        
        # Ищем множественные цели
        for pattern in self.patterns['targets']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                groups = match.groups()
                if len(groups) == 1:
                    # Одна группа с текстом целей
                    targets_text = groups[0]
                    # Извлекаем все числа
                    for target_match in re.finditer(r'(\d+(?:[.,]\d+)?)', targets_text):
                        try:
                            target = float(target_match.group(1).replace(',', ''))
                            targets.append(target)
                        except ValueError:
                            continue
                elif len(groups) == 2:
                    # Две группы: номер цели и цена
                    try:
                        target = float(groups[1].replace(',', ''))
                        targets.append(target)
                    except ValueError:
                        continue
        
        return targets
    
    def _extract_stop_loss_info(self, text: str) -> Dict:
        """Извлекает информацию о стоп-лоссе"""
        result = {'price': None, 'percent': None}
        
        # Ищем ценовой стоп
        for pattern in self.patterns['stop_loss']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                groups = match.groups()
                if len(groups) == 1:
                    try:
                        price = float(groups[0].replace(',', ''))
                        result['price'] = price
                        return result
                    except ValueError:
                        continue
                elif len(groups) == 2:
                    try:
                        # Процентный стоп
                        start_percent = float(groups[0])
                        end_percent = float(groups[1])
                        result['percent'] = (start_percent + end_percent) / 2
                        return result
                    except ValueError:
                        continue
        
        return result
    
    def _extract_leverage(self, text: str) -> Optional[str]:
        """Извлекает кредитное плечо"""
        for pattern in self.patterns['leverage']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                groups = match.groups()
                for group in groups:
                    if group and ('x' in group.lower() or '-' in group):
                        return group
        return None
    
    def _extract_timeframe(self, text: str) -> Optional[str]:
        """Извлекает временной фрейм"""
        for pattern in self.patterns['timeframe']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).upper()
        return None
    
    def convert_to_standard_format(self, signal: UniversalSignal) -> Dict:
        """Конвертирует в стандартный формат"""
        
        return {
            'id': signal.signal_id,
            'asset': signal.asset.split('/')[0] if '/' in signal.asset else signal.asset,
            'direction': signal.direction,
            'entry_price': signal.entry_price,
            'target_price': signal.targets[0] if signal.targets else None,
            'stop_loss': signal.stop_loss,
            'confidence': signal.confidence,
            'channel': signal.channel,
            'message_id': signal.signal_id,
            'timestamp': signal.timestamp,
            'extraction_time': datetime.now().isoformat(),
            'original_text': f"Universal Signal: {signal.asset} {signal.direction}",
            'cleaned_text': f"Universal Signal: {signal.asset} {signal.direction}",
            'bybit_available': True,
            'signal_type': 'universal',
            'entry_range': signal.entry_range,
            'entry_type': signal.entry_type,
            'all_targets': signal.targets,
            'leverage': signal.leverage,
            'timeframe': signal.timeframe,
            'stop_loss_percent': signal.stop_loss_percent
        }

def test_universal_parser():
    """Тестирует универсальный парсер на всех форматах"""
    
    test_cases = [
        {
            'name': 'BinanceKillers',
            'text': """
            SIGNAL ID: #1956
            COIN: $BTC/USDT (3-5x)
            Direction: LONG 📈
            ENTRY: 112207 - 110500
            TARGETS: 113500 - 114800 - 117000 - 123236
            STOP LOSS: 109638
            """,
            'channel': 'BinanceKillers'
        },
        {
            'name': 'Wolf of Trading',
            'text': """
            #BAND/USDT
            🔴 SHORT
            👆 Entry: 1.0700 - 1.1050
            🌐 Leverage: 20x
            🎯 Target 1: 1.0590
            🎯 Target 2: 1.0480
            🎯 Target 3: 1.0370
            🎯 Target 4: 1.0260
            🎯 Target 5: 1.0150
            🎯 Target 6: 1.0040
            ❌ StopLoss: 1.1340
            """,
            'channel': 'Wolf of Trading'
        },
        {
            'name': 'Crypto Inner Circle',
            'text': """
            ⚡⚡ BSW/USDT ⚡
            Signal Type: Regular (Short)
            Leverage: Cross (25x)
            Entry Targets: 0.01862
            Take-Profit Targets: 0.01834, 0.01815, 0.01797, 0.01769, 0.01750, 0.01722
            Stop Targets: 5-10%
            """,
            'channel': 'Crypto Inner Circle'
        },
        {
            'name': 'Дневник Трейдера',
            'text': """
            Открываем пару WOO / USDT в SHORT
            Рыночный ордер: 0.07673
            Cross маржа
            Плечо: 17x
            Тейки: 0.0756, 0.07447, 0.07221
            Стоп: 0.08304
            """,
            'channel': 'Дневник Трейдера'
        },
        {
            'name': 'Торговля Криптовалютой',
            'text': """
            Заходим JASMY SHORT 25x
            Вход: по рынку
            Тейк: 0.015956 / 0.014906 / 0.013173
            Стоп: 0.017547
            """,
            'channel': 'Торговля Криптовалютой'
        }
    ]
    
    parser = UniversalSignalParser()
    
    print("🧪 ТЕСТИРОВАНИЕ УНИВЕРСАЛЬНОГО ПАРСЕРА")
    print("=" * 60)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📊 Тест {i}: {test_case['name']}")
        print("-" * 40)
        
        signal = parser.parse_signal(test_case['text'], test_case['channel'])
        
        if signal:
            print(f"✅ Успешно извлечен сигнал!")
            print(f"Asset: {signal.asset}")
            print(f"Direction: {signal.direction}")
            print(f"Entry Type: {signal.entry_type}")
            if signal.entry_price:
                print(f"Entry Price: ${signal.entry_price:,.6f}")
            if signal.entry_range:
                print(f"Entry Range: {signal.entry_range}")
            print(f"Targets: {signal.targets}")
            if signal.stop_loss:
                print(f"Stop Loss: ${signal.stop_loss:,.6f}")
            if signal.stop_loss_percent:
                print(f"Stop Loss %: {signal.stop_loss_percent}%")
            print(f"Leverage: {signal.leverage}")
            print(f"Timeframe: {signal.timeframe}")
            
            # Конвертируем в стандартный формат
            standard = parser.convert_to_standard_format(signal)
            print(f"Standard Format: {standard['asset']} {standard['direction']} @ ${standard['entry_price']:,.6f if standard['entry_price'] else 'Market'}")
        else:
            print("❌ Не удалось извлечь сигнал")
    
    return True

if __name__ == "__main__":
    test_universal_parser()
