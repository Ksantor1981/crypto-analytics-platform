"""
Simple TradingView Parser - Упрощенный парсер для TradingView
Демонстрационная версия без внешних зависимостей
"""

import json
import logging
import time
import re
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, asdict
from improved_signal_parser import ImprovedSignal, ImprovedSignalExtractor, SignalDirection, SignalQuality

class SignalJSONEncoder(json.JSONEncoder):
    """Кастомный JSON encoder для сигналов"""
    def default(self, obj):
        if isinstance(obj, (SignalDirection, SignalQuality)):
            return obj.value
        return super().default(obj)

logger = logging.getLogger(__name__)

@dataclass
class TradingViewIdea:
    """Идея с TradingView"""
    id: str
    title: str
    description: str
    author: str
    symbol: str
    likes: int
    comments: int
    created_at: int
    timeframe: str
    direction: str
    entry_price: Optional[float]
    target_price: Optional[float]
    stop_loss: Optional[float]
    url: str

class SimpleTradingViewParser:
    """Упрощенный парсер для TradingView"""
    
    def __init__(self):
        self.extractor = ImprovedSignalExtractor()
        
        # Демонстрационные данные TradingView
        self.demo_ideas = [
            {
                'id': 'tv_1',
                'title': 'BTC/USDT: Bullish Breakout Confirmed',
                'description': 'Bitcoin has broken out of the descending triangle pattern. Strong bullish momentum with increasing volume. Entry: 50000, Target: 55000, Stop Loss: 48000. Risk/Reward ratio: 2.5:1',
                'author': 'CryptoMaster',
                'symbol': 'BTCUSDT',
                'likes': 245,
                'comments': 67,
                'created_at': int(time.time()) - 3600,
                'timeframe': '4H',
                'direction': 'LONG',
                'entry_price': 50000,
                'target_price': 55000,
                'stop_loss': 48000,
                'url': 'https://www.tradingview.com/ideas/tv_1'
            },
            {
                'id': 'tv_2',
                'title': 'ETH/USDT: Bearish Divergence on RSI',
                'description': 'Ethereum showing bearish divergence on RSI. Price action suggests a potential reversal. Short entry at 3000, target 2800, stop loss at 3200. MACD crossing below signal line.',
                'author': 'ETH_Analyst',
                'symbol': 'ETHUSDT',
                'likes': 189,
                'comments': 43,
                'created_at': int(time.time()) - 7200,
                'timeframe': '1H',
                'direction': 'SHORT',
                'entry_price': 3000,
                'target_price': 2800,
                'stop_loss': 3200,
                'url': 'https://www.tradingview.com/ideas/tv_2'
            },
            {
                'id': 'tv_3',
                'title': 'ADA/USDT: Support Level Test',
                'description': 'Cardano testing key support level at 0.42. Volume profile shows accumulation. Long entry at 0.45, target 0.55, stop loss at 0.42. Strong support zone.',
                'author': 'ADA_Trader',
                'symbol': 'ADAUSDT',
                'likes': 156,
                'comments': 28,
                'created_at': int(time.time()) - 10800,
                'timeframe': '4H',
                'direction': 'LONG',
                'entry_price': 0.45,
                'target_price': 0.55,
                'stop_loss': 0.42,
                'url': 'https://www.tradingview.com/ideas/tv_3'
            },
            {
                'id': 'tv_4',
                'title': 'SOL/USDT: Resistance Breakout',
                'description': 'Solana breaking above resistance at 125. Momentum indicators confirm bullish trend. Long entry at 125, target 140, stop loss at 120. Breakout confirmed.',
                'author': 'SOL_Expert',
                'symbol': 'SOLUSDT',
                'likes': 203,
                'comments': 51,
                'created_at': int(time.time()) - 14400,
                'timeframe': '1D',
                'direction': 'LONG',
                'entry_price': 125,
                'target_price': 140,
                'stop_loss': 120,
                'url': 'https://www.tradingview.com/ideas/tv_4'
            },
            {
                'id': 'tv_5',
                'title': 'DOT/USDT: Consolidation Pattern',
                'description': 'Polkadot in consolidation pattern. Price action suggests breakout soon. Long entry at 6.5, target 7.5, stop loss at 6.2. Symmetrical triangle formation.',
                'author': 'DOT_Analyst',
                'symbol': 'DOTUSDT',
                'likes': 134,
                'comments': 35,
                'created_at': int(time.time()) - 18000,
                'timeframe': '4H',
                'direction': 'LONG',
                'entry_price': 6.5,
                'target_price': 7.5,
                'stop_loss': 6.2,
                'url': 'https://www.tradingview.com/ideas/tv_5'
            },
            {
                'id': 'tv_6',
                'title': 'LINK/USDT: Bearish Flag Pattern',
                'description': 'Chainlink forming bearish flag pattern. Price likely to continue downward. Short entry at 15, target 13, stop loss at 16. Bearish momentum.',
                'author': 'LINK_Trader',
                'symbol': 'LINKUSDT',
                'likes': 98,
                'comments': 22,
                'created_at': int(time.time()) - 21600,
                'timeframe': '1H',
                'direction': 'SHORT',
                'entry_price': 15,
                'target_price': 13,
                'stop_loss': 16,
                'url': 'https://www.tradingview.com/ideas/tv_6'
            },
            {
                'id': 'tv_7',
                'title': 'MATIC/USDT: Bullish Pennant',
                'description': 'Polygon forming bullish pennant pattern. Volume decreasing during consolidation. Long entry at 0.8, target 1.0, stop loss at 0.75. Bullish continuation.',
                'author': 'MATIC_Expert',
                'symbol': 'MATICUSDT',
                'likes': 167,
                'comments': 39,
                'created_at': int(time.time()) - 25200,
                'timeframe': '4H',
                'direction': 'LONG',
                'entry_price': 0.8,
                'target_price': 1.0,
                'stop_loss': 0.75,
                'url': 'https://www.tradingview.com/ideas/tv_7'
            },
            {
                'id': 'tv_8',
                'title': 'AVAX/USDT: Double Top Formation',
                'description': 'Avalanche showing double top formation. Bearish reversal pattern confirmed. Short entry at 35, target 30, stop loss at 37. Neckline break.',
                'author': 'AVAX_Analyst',
                'symbol': 'AVAXUSDT',
                'likes': 145,
                'comments': 31,
                'created_at': int(time.time()) - 28800,
                'timeframe': '1D',
                'direction': 'SHORT',
                'entry_price': 35,
                'target_price': 30,
                'stop_loss': 37,
                'url': 'https://www.tradingview.com/ideas/tv_8'
            }
        ]
    
    def get_demo_ideas(self, symbol: str = None) -> List[TradingViewIdea]:
        """Получает демонстрационные идеи"""
        ideas = []
        
        for idea_data in self.demo_ideas:
            if symbol is None or idea_data['symbol'] == symbol:
                idea = TradingViewIdea(
                    id=idea_data['id'],
                    title=idea_data['title'],
                    description=idea_data['description'],
                    author=idea_data['author'],
                    symbol=idea_data['symbol'],
                    likes=idea_data['likes'],
                    comments=idea_data['comments'],
                    created_at=idea_data['created_at'],
                    timeframe=idea_data['timeframe'],
                    direction=idea_data['direction'],
                    entry_price=idea_data['entry_price'],
                    target_price=idea_data['target_price'],
                    stop_loss=idea_data['stop_loss'],
                    url=idea_data['url']
                )
                ideas.append(idea)
        
        return ideas
    
    def extract_signals_from_idea(self, idea: TradingViewIdea) -> List[ImprovedSignal]:
        """Извлекает сигналы из идеи TradingView"""
        try:
            # Объединяем заголовок и описание
            full_text = f"{idea.title}\n{idea.description}"
            logger.info(f"Processing idea {idea.id}: {idea.title}")
            
            # Очищаем текст от TradingView-специфичных элементов
            cleaned_text = self._clean_tradingview_text(full_text)
            logger.info(f"Cleaned text: {cleaned_text[:200]}...")
            
            # Извлекаем сигналы
            signals = self.extractor.extract_signals_from_text(cleaned_text, f"tradingview_{idea.symbol}", idea.id)
            logger.info(f"Extractor returned {len(signals)} signals")
            
            # Обогащаем сигналы информацией о источнике
            for signal in signals:
                signal.channel = f"tradingview_{idea.symbol}"
                signal.message_id = idea.id
                signal.signal_type = "tradingview"
                signal.timeframe = idea.timeframe
                
                # Если в идее есть конкретные цены, используем их
                if idea.entry_price and not signal.entry_price:
                    signal.entry_price = idea.entry_price
                if idea.target_price and not signal.target_price:
                    signal.target_price = idea.target_price
                if idea.stop_loss and not signal.stop_loss:
                    signal.stop_loss = idea.stop_loss
            
            return signals
            
        except Exception as e:
            logger.error(f"Error extracting signals from idea {idea.id}: {e}")
            return []
    
    def _clean_tradingview_text(self, text: str) -> str:
        """Очищает текст от TradingView-специфичных элементов"""
        # Убираем ссылки на TradingView
        text = re.sub(r'https?://(?:www\.)?tradingview\.com[^\s]*', '', text)
        
        # Убираем упоминания пользователей
        text = re.sub(r'@[^\s]+', '', text)
        
        # Убираем символы валютных пар
        text = re.sub(r'[A-Z]{3,5}/[A-Z]{3,5}', '', text)
        
        # Убираем лишние пробелы
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def analyze_idea_quality(self, idea: TradingViewIdea) -> float:
        """Анализирует качество идеи"""
        quality_score = 0.0
        
        # Базовые баллы за популярность
        quality_score += min(idea.likes / 50, 10.0)  # Максимум 10 баллов за лайки
        quality_score += min(idea.comments / 20, 5.0)  # Максимум 5 баллов за комментарии
        
        # Бонус за наличие всех цен
        if idea.entry_price and idea.target_price and idea.stop_loss:
            quality_score += 5.0
        
        # Бонус за четкое направление
        if idea.direction in ['LONG', 'SHORT']:
            quality_score += 2.0
        
        # Бонус за временной фрейм
        if idea.timeframe:
            quality_score += 1.0
        
        # Бонус за свежесть (идеи не старше 24 часов)
        age_hours = (time.time() - idea.created_at) / 3600
        if age_hours <= 24:
            quality_score += 3.0
        elif age_hours <= 48:
            quality_score += 1.0
        
        return min(quality_score, 25.0)  # Максимум 25 баллов
    
    def parse_symbol(self, symbol: str) -> Dict[str, Any]:
        """Парсит идеи для конкретного символа"""
        try:
            logger.info(f"Parsing TradingView ideas for {symbol}")
            
            # Получаем демонстрационные идеи
            ideas = self.get_demo_ideas(symbol)
            logger.info(f"Found {len(ideas)} ideas for {symbol}")
            
            all_signals = []
            processed_ideas = 0
            
            for idea in ideas:
                try:
                    # Анализируем качество идеи
                    quality = self.analyze_idea_quality(idea)
                    
                    if quality >= 8.0:  # Минимальное качество
                        # Извлекаем сигналы
                        signals = self.extract_signals_from_idea(idea)
                        logger.info(f"Extracted {len(signals)} signals from idea {idea.id}")
                        all_signals.extend(signals)
                        processed_ideas += 1
                    else:
                        logger.info(f"Idea {idea.id} quality {quality} below threshold 8.0")
                        
                except Exception as e:
                    logger.error(f"Error processing idea {idea.id}: {e}")
                    continue
            
            # Фильтруем и ранжируем сигналы
            filtered_signals = self._filter_and_rank_signals(all_signals)
            
            return {
                'success': True,
                'symbol': symbol,
                'total_ideas': len(ideas),
                'processed_ideas': processed_ideas,
                'total_signals': len(all_signals),
                'filtered_signals': len(filtered_signals),
                'signals': filtered_signals,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error parsing symbol {symbol}: {e}")
            return {
                'success': False,
                'symbol': symbol,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def _filter_and_rank_signals(self, signals: List[ImprovedSignal]) -> List[ImprovedSignal]:
        """Фильтрует и ранжирует сигналы"""
        if not signals:
            return []
        
        # Фильтруем по качеству
        filtered_signals = []
        for signal in signals:
            # Проверяем наличие основных полей
            if (signal.asset and 
                signal.direction and 
                (signal.entry_price or signal.target_price or signal.stop_loss)):
                filtered_signals.append(signal)
        
        # Ранжируем по качеству
        filtered_signals.sort(key=lambda s: s.real_confidence or 0, reverse=True)
        
        return filtered_signals[:15]  # Возвращаем топ-15 сигналов
    
    def parse_all_symbols(self) -> Dict[str, Any]:
        """Парсит идеи для всех настроенных символов"""
        symbols = ['BTCUSDT', 'ETHUSDT', 'ADAUSDT', 'SOLUSDT', 'DOTUSDT', 'LINKUSDT', 'MATICUSDT', 'AVAXUSDT']
        all_results = []
        total_signals = 0
        
        for symbol in symbols:
            try:
                result = self.parse_symbol(symbol)
                all_results.append(result)
                
                if result['success']:
                    total_signals += result['filtered_signals']
                
                # Пауза между запросами
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Error parsing symbol {symbol}: {e}")
                continue
        
        # Объединяем все сигналы
        all_signals = []
        for result in all_results:
            if result['success']:
                all_signals.extend(result['signals'])
        
        return {
            'success': True,
            'total_symbols': len(symbols),
            'successful_symbols': len([r for r in all_results if r['success']]),
            'total_signals': total_signals,
            'all_signals': all_signals,
            'symbol_results': all_results,
            'timestamp': datetime.now().isoformat()
        }
    
    def get_trending_ideas(self, limit: int = 20) -> List[TradingViewIdea]:
        """Получает трендовые идеи (по лайкам)"""
        ideas = self.get_demo_ideas()
        
        # Сортируем по лайкам
        ideas.sort(key=lambda x: x.likes, reverse=True)
        
        return ideas[:limit]

def main():
    """Тестирование упрощенного TradingView парсера"""
    parser = SimpleTradingViewParser()
    
    print("=== Тестирование упрощенного TradingView парсера ===")
    
    # Тестируем парсинг одного символа
    print("\n1. Парсинг BTCUSDT:")
    result = parser.parse_symbol('BTCUSDT')
    
    if result['success']:
        print(f"✅ Обработано {result['processed_ideas']} идей из {result['total_ideas']}")
        print(f"  Найдено сигналов: {result['total_signals']}")
        print(f"  Отфильтровано: {result['filtered_signals']}")
        
        if result['signals']:
            print(f"\n📊 Примеры сигналов:")
            for signal in result['signals'][:3]:
                print(f"  - {signal.asset} {signal.direction.value}: {signal.signal_quality.value}")
    else:
        print(f"❌ Ошибка: {result['error']}")
    
    # Тестируем парсинг всех символов
    print("\n2. Парсинг всех символов:")
    all_results = parser.parse_all_symbols()
    
    if all_results['success']:
        print(f"✅ Обработано {all_results['successful_symbols']} символов из {all_results['total_symbols']}")
        print(f"  Всего сигналов: {all_results['total_signals']}")
        
        # Сохраняем результаты
        with open('simple_tradingview_signals.json', 'w', encoding='utf-8') as f:
            # Конвертируем сигналы в словари для JSON сериализации
            serializable_results = all_results.copy()
            serializable_results['all_signals'] = [asdict(signal) for signal in all_results['all_signals']]
            for result in serializable_results['symbol_results']:
                if result['success']:
                    result['signals'] = [asdict(signal) for signal in result['signals']]
            
            json.dump(serializable_results, f, indent=2, ensure_ascii=False, cls=SignalJSONEncoder)
        
        print(f"  Результаты сохранены в simple_tradingview_signals.json")
    else:
        print(f"❌ Ошибка при парсинге всех символов")
    
    # Тестируем получение трендовых идей
    print("\n3. Трендовые идеи:")
    trending = parser.get_trending_ideas(5)
    print(f"  Топ-5 идей по лайкам:")
    for idea in trending:
        print(f"    - {idea.symbol}: {idea.title} (❤️ {idea.likes})")

if __name__ == "__main__":
    main()
