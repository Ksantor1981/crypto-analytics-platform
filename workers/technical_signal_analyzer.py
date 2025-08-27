"""
Анализатор технических сигналов из аналитических постов
"""

import json
import re
from datetime import datetime
from typing import List, Dict, Optional

class TechnicalSignalAnalyzer:
    """Анализатор технических сигналов из аналитических постов"""
    
    def __init__(self):
        self.technical_keywords = {
            'bearish': ['bearish', 'bear', 'dumping', 'down', 'decline', 'capitulation', 'breakdown'],
            'bullish': ['bullish', 'bull', 'pumping', 'up', 'rally', 'recovery', 'breakout'],
            'support': ['support', 'floor', 'bottom', 'bounce'],
            'resistance': ['resistance', 'ceiling', 'top', 'rejection'],
            'breakout': ['break', 'breaks', 'breakout', 'breakdown'],
            'target': ['target', 'targets', 'goal', 'objective']
        }
    
    def analyze_technical_post(self, text: str) -> Dict:
        """Анализирует технический пост и извлекает структурированные сигналы"""
        
        analysis = {
            'asset': None,
            'direction': 'HOLD',
            'entry_level': None,
            'target_level': None,
            'stop_level': None,
            'confidence': 0.0,
            'technical_indicators': [],
            'key_levels': [],
            'sentiment': 'neutral',
            'timeframe': None,
            'risk_level': 'medium'
        }
        
        # Извлекаем актив
        asset_match = re.search(r'\$([A-Z]+)', text, re.IGNORECASE)
        if asset_match:
            analysis['asset'] = asset_match.group(1).upper()
        
        # Определяем направление на основе ключевых слов
        text_lower = text.lower()
        
        # Анализируем sentiment
        bearish_count = sum(1 for word in self.technical_keywords['bearish'] if word in text_lower)
        bullish_count = sum(1 for word in self.technical_keywords['bullish'] if word in text_lower)
        
        if bearish_count > bullish_count:
            analysis['direction'] = 'SELL'
            analysis['sentiment'] = 'bearish'
        elif bullish_count > bearish_count:
            analysis['direction'] = 'BUY'
            analysis['sentiment'] = 'bullish'
        
        # Извлекаем ценовые уровни
        price_patterns = [
            r'\$?(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*[kK]?',  # Цены с k/K
            r'(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*[kK]',      # Цены с k/K без $
        ]
        
        prices = []
        for pattern in price_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                try:
                    price_str = match.replace(',', '')
                    if price_str.endswith(('k', 'K')):
                        price = float(price_str[:-1]) * 1000
                    else:
                        price = float(price_str)
                    prices.append(price)
                except ValueError:
                    continue
        
        # Сортируем цены и определяем уровни
        if prices:
            prices.sort()
            if len(prices) >= 2:
                analysis['entry_level'] = prices[0]  # Самый низкий уровень
                analysis['target_level'] = prices[-1]  # Самый высокий уровень
            else:
                analysis['entry_level'] = prices[0]
        
        # Ищем ключевые уровни
        support_match = re.search(r'support\s+(?:at\s+)?\$?(\d+[kK]?)', text, re.IGNORECASE)
        resistance_match = re.search(r'resistance\s+(?:at\s+)?\$?(\d+[kK]?)', text, re.IGNORECASE)
        key_zone_match = re.search(r'key\s+zone\s+\$?(\d+[kK]?)', text, re.IGNORECASE)
        
        if support_match:
            analysis['key_levels'].append(f"Support: {support_match.group(1)}")
        if resistance_match:
            analysis['key_levels'].append(f"Resistance: {resistance_match.group(1)}")
        if key_zone_match:
            analysis['key_levels'].append(f"Key Zone: {key_zone_match.group(1)}")
        
        # Определяем временной фрейм
        timeframe_patterns = {
            '1W': r'1W|weekly|week',
            '1D': r'1D|daily|day',
            '4H': r'4H|4h',
            '1H': r'1H|1h|hourly',
            '15M': r'15M|15m|15\s*min',
        }
        
        for tf, pattern in timeframe_patterns.items():
            if re.search(pattern, text, re.IGNORECASE):
                analysis['timeframe'] = tf
                break
        
        # Рассчитываем уверенность
        confidence = 0.0
        
        # Базовые бонусы
        if analysis['asset']:
            confidence += 0.2
        if analysis['direction'] != 'HOLD':
            confidence += 0.3
        if analysis['entry_level']:
            confidence += 0.2
        if analysis['target_level']:
            confidence += 0.15
        if analysis['key_levels']:
            confidence += 0.1
        if analysis['timeframe']:
            confidence += 0.05
        
        # Бонусы за технические индикаторы
        if any(word in text_lower for word in ['rsi', 'macd', 'moving average', 'ema', 'sma']):
            confidence += 0.1
        if any(word in text_lower for word in ['trendline', 'fibonacci', 'elliot wave']):
            confidence += 0.1
        
        analysis['confidence'] = min(confidence, 1.0)
        
        return analysis
    
    def extract_signals_from_analysis(self, analysis: Dict) -> List[Dict]:
        """Преобразует анализ в торговые сигналы"""
        
        signals = []
        
        if not analysis['asset'] or analysis['direction'] == 'HOLD':
            return signals
        
        # Основной сигнал
        signal = {
            'id': f"technical_{analysis['asset']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'asset': analysis['asset'],
            'direction': analysis['direction'],
            'entry_price': analysis['entry_level'],
            'target_price': analysis['target_level'],
            'stop_loss': analysis['stop_level'],
            'confidence': round(analysis['confidence'] * 100, 1),
            'channel': 'technical_analysis',
            'message_id': 'technical',
            'timestamp': datetime.now().isoformat(),
            'extraction_time': datetime.now().isoformat(),
            'original_text': f"Technical Analysis: {analysis['asset']} {analysis['direction']}",
            'cleaned_text': f"Technical Analysis: {analysis['asset']} {analysis['direction']}",
            'bybit_available': True,
            'analysis_type': 'technical',
            'timeframe': analysis['timeframe'],
            'sentiment': analysis['sentiment'],
            'key_levels': analysis['key_levels'],
            'risk_level': analysis['risk_level']
        }
        
        signals.append(signal)
        
        return signals

def analyze_technical_posts():
    """Анализирует технические посты из собранных данных"""
    
    analyzer = TechnicalSignalAnalyzer()
    
    # Загружаем данные
    with open('enhanced_telegram_signals.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print('🔬 АНАЛИЗ ТЕХНИЧЕСКИХ СИГНАЛОВ')
    print('=' * 50)
    
    technical_signals = []
    
    for signal in data['signals']:
        # Анализируем только сигналы с техническим контекстом
        if signal['confidence'] > 0 and 'technical' in signal['original_text'].lower():
            analysis = analyzer.analyze_technical_post(signal['original_text'])
            if analysis['asset'] and analysis['direction'] != 'HOLD':
                new_signals = analyzer.extract_signals_from_analysis(analysis)
                technical_signals.extend(new_signals)
    
    print(f'📊 Найдено {len(technical_signals)} технических сигналов')
    
    for signal in technical_signals:
        print(f'\n🎯 {signal["asset"]} {signal["direction"]}')
        print(f'   Entry: ${signal["entry_price"]:,.0f}' if signal["entry_price"] else '   Entry: Market')
        print(f'   Target: ${signal["target_price"]:,.0f}' if signal["target_price"] else '   Target: N/A')
        print(f'   Confidence: {signal["confidence"]}%')
        print(f'   Timeframe: {signal["timeframe"] or "N/A"}')
        print(f'   Sentiment: {signal["sentiment"]}')
        if signal["key_levels"]:
            print(f'   Key Levels: {", ".join(signal["key_levels"])}')
    
    return technical_signals

if __name__ == "__main__":
    signals = analyze_technical_posts()
