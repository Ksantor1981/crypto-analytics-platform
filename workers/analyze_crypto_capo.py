"""
Анализатор для канала CryptoCapo и подобных аналитических каналов
"""
import re
import json
from datetime import datetime
from typing import Dict, Any, List

class CryptoCapoAnalyzer:
    """
    Анализатор для извлечения торговых идей из аналитических каналов
    """
    
    def __init__(self):
        # Паттерны для различных типов анализа
        self.analysis_patterns = {
            'dxy': [
                r'#DXY',
                r'DOLLAR INDEX',
                r'DXY',
                r'dollar.*index'
            ],
            'btc': [
                r'#BTC',
                r'BITCOIN',
                r'BTC',
                r'bitcoin'
            ],
            'eth': [
                r'#ETH',
                r'ETHEREUM',
                r'ETH',
                r'ethereum'
            ],
            'direction': {
                'bullish': [
                    r'bullish',
                    r'long',
                    r'buy',
                    r'up',
                    r'higher',
                    r'🚀',
                    r'📈',
                    r'green',
                    r'positive'
                ],
                'bearish': [
                    r'bearish',
                    r'short',
                    r'sell',
                    r'down',
                    r'lower',
                    r'📉',
                    r'🔻',
                    r'red',
                    r'negative'
                ]
            },
            'levels': [
                r'(\d+(?:\.\d+)?)\s*(?:level|resistance|support|target)',
                r'(?:above|below)\s*(\d+(?:\.\d+)?)',
                r'confirmation\s*(?:above|below)\s*(\d+(?:\.\d+)?)',
                r'break\s*(?:above|below)\s*(\d+(?:\.\d+)?)'
            ]
        }
    
    def analyze_message(self, text: str, channel: str = "CryptoCapo") -> Dict[str, Any]:
        """
        Анализ сообщения из аналитического канала
        
        Args:
            text: Текст сообщения
            channel: Название канала
            
        Returns:
            Результат анализа
        """
        analysis = {
            'channel': channel,
            'timestamp': datetime.now().isoformat(),
            'asset': None,
            'direction': None,
            'confidence': 0.0,
            'levels': [],
            'analysis_type': 'market_analysis',
            'raw_text': text
        }
        
        text_lower = text.lower()
        
        # Определяем актив
        if any(re.search(pattern, text_lower) for pattern in self.analysis_patterns['dxy']):
            analysis['asset'] = 'DXY'
            analysis['asset_name'] = 'Dollar Index'
        elif any(re.search(pattern, text_lower) for pattern in self.analysis_patterns['btc']):
            analysis['asset'] = 'BTC'
            analysis['asset_name'] = 'Bitcoin'
        elif any(re.search(pattern, text_lower) for pattern in self.analysis_patterns['eth']):
            analysis['asset'] = 'ETH'
            analysis['asset_name'] = 'Ethereum'
        elif 'dxy' in text_lower or 'dollar' in text_lower:
            analysis['asset'] = 'DXY'
            analysis['asset_name'] = 'Dollar Index'
        else:
            analysis['asset'] = 'UNKNOWN'
            analysis['asset_name'] = 'Unknown Asset'
        
        # Определяем направление
        bullish_count = sum(1 for pattern in self.analysis_patterns['direction']['bullish'] 
                           for match in re.finditer(pattern, text_lower))
        bearish_count = sum(1 for pattern in self.analysis_patterns['direction']['bearish'] 
                           for match in re.finditer(pattern, text_lower))
        
        if bullish_count > bearish_count:
            analysis['direction'] = 'BULLISH'
            analysis['confidence'] = min(0.8, 0.5 + (bullish_count * 0.1))
        elif bearish_count > bullish_count:
            analysis['direction'] = 'BEARISH'
            analysis['confidence'] = min(0.8, 0.5 + (bearish_count * 0.1))
        
        # Извлекаем уровни
        levels = []
        for pattern in self.analysis_patterns['levels']:
            matches = re.finditer(pattern, text_lower)
            for match in matches:
                try:
                    level = float(match.group(1))
                    if 0 < level < 1000000:  # Разумный диапазон
                        levels.append(level)
                except (ValueError, IndexError):
                    continue
        
        analysis['levels'] = sorted(list(set(levels)))
        
        return analysis
    
    def extract_trading_ideas(self, analyses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Извлечение торговых идей из анализов
        
        Args:
            analyses: Список анализов
            
        Returns:
            Список торговых идей
        """
        trading_ideas = []
        
        for analysis in analyses:
            if analysis['asset'] and analysis['direction'] and analysis['levels']:
                # Создаем торговую идею
                idea = {
                    'asset': analysis['asset'],
                    'asset_name': analysis['asset_name'],
                    'direction': analysis['direction'],
                    'confidence': analysis['confidence'],
                    'entry_levels': analysis['levels'],
                    'source': analysis['channel'],
                    'analysis_type': 'technical_analysis',
                    'timestamp': analysis['timestamp']
                }
                
                # Добавляем рекомендации
                if analysis['direction'] == 'BULLISH':
                    idea['recommendation'] = f"Рассмотреть покупку {analysis['asset']} при достижении уровней: {', '.join(map(str, analysis['levels']))}"
                else:
                    idea['recommendation'] = f"Рассмотреть продажу {analysis['asset']} при достижении уровней: {', '.join(map(str, analysis['levels']))}"
                
                trading_ideas.append(idea)
        
        return trading_ideas

def test_crypto_capo_analysis():
    """Тест анализа CryptoCapo"""
    
    analyzer = CryptoCapoAnalyzer()
    
    # Тестовые сообщения из CryptoCapo
    test_messages = [
        {
            'text': '#DXY\nExpecting a bullish move for the dollar. Confirmation above 100.',
            'channel': 'CryptoCapo'
        },
        {
            'text': 'BITCOIN ANALYSIS\nBTC showing bullish momentum. Key resistance at 45000. Break above 47000 confirms uptrend.',
            'channel': 'CryptoCapo'
        },
        {
            'text': 'ETHEREUM UPDATE\nETH bearish below 3200. Support at 3000. Break below 2800 accelerates decline.',
            'channel': 'CryptoCapo'
        }
    ]
    
    print("🔍 АНАЛИЗ СООБЩЕНИЙ CRYPTOCAPO")
    print("=" * 60)
    
    all_analyses = []
    
    for i, msg in enumerate(test_messages):
        print(f"\n📝 Сообщение {i+1}:")
        print(f"Канал: {msg['channel']}")
        print(f"Текст: {msg['text']}")
        
        analysis = analyzer.analyze_message(msg['text'], msg['channel'])
        all_analyses.append(analysis)
        
        print(f"Актив: {analysis['asset']} ({analysis['asset_name']})")
        print(f"Направление: {analysis['direction']}")
        print(f"Уверенность: {analysis['confidence']:.2f}")
        print(f"Уровни: {analysis['levels']}")
        print("-" * 40)
    
    # Извлекаем торговые идеи
    print("\n💡 ТОРГОВЫЕ ИДЕИ:")
    print("=" * 60)
    
    trading_ideas = analyzer.extract_trading_ideas(all_analyses)
    
    for i, idea in enumerate(trading_ideas):
        print(f"\n{i+1}. {idea['asset']} ({idea['asset_name']})")
        print(f"   Направление: {idea['direction']}")
        print(f"   Уверенность: {idea['confidence']:.2f}")
        print(f"   Уровни входа: {idea['entry_levels']}")
        print(f"   Рекомендация: {idea['recommendation']}")
        print(f"   Источник: {idea['source']}")
    
    # Сохраняем результаты
    results = {
        'analyses': all_analyses,
        'trading_ideas': trading_ideas,
        'timestamp': datetime.now().isoformat()
    }
    
    with open('crypto_capo_analysis.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2, default=str)
    
    print(f"\n✅ Результаты сохранены в crypto_capo_analysis.json")
    print(f"📊 Всего анализов: {len(all_analyses)}")
    print(f"💡 Торговых идей: {len(trading_ideas)}")

if __name__ == "__main__":
    test_crypto_capo_analysis()
