"""
TradingView Parser - Парсер для TradingView Ideas
Извлекает торговые сигналы и аналитику из TradingView
"""

import json
import logging
import time
import re
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
import requests
from improved_signal_parser import ImprovedSignal, ImprovedSignalExtractor, SignalDirection, SignalQuality

logger = logging.getLogger(__name__)

@dataclass
class TradingViewIdea:
    """Идея с TradingView"""
    id: str
    title: str
    description: str
    author: str
    symbol: str
    timeframe: str
    direction: str
    likes: int
    comments: int
    created_at: str
    url: str
    tags: List[str]

class TradingViewParser:
    """Парсер для TradingView"""
    
    def __init__(self):
        self.extractor = ImprovedSignalExtractor()
        self.base_url = "https://www.tradingview.com"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.tradingview.com/ideas/'
        }
        
        # Криптовалютные символы для парсинга
        self.crypto_symbols = [
            'BTCUSD', 'ETHUSD', 'ADAUSD', 'SOLUSD', 'DOTUSD', 'LINKUSD',
            'UNIUSD', 'AVAXUSD', 'MATICUSD', 'ATOMUSD', 'XRPUSD', 'DOGEUSD',
            'SHIBUSD', 'LTCUSD', 'BCHUSD', 'BNBUSD', 'LUNAUSD', 'NEARUSD',
            'FTMUSD', 'ALGOUSD', 'SYSUSD', 'ENAUSD', 'ZIGUSD', 'ATAUSD',
            'MAVIAUSD', 'ORDIUSD', 'BANDUSD', 'BSWUSD', 'WOOUSD', 'JASMYUSD'
        ]
        
        # Фильтры для качества
        self.min_likes = 5
        self.min_comments = 2
        self.max_age_hours = 48
    
    def get_ideas_for_symbol(self, symbol: str, limit: int = 20) -> List[TradingViewIdea]:
        """Получает идеи для конкретного символа"""
        try:
            # Используем TradingView API для получения идей
            url = f"{self.base_url}/api/v1/ideas/search"
            params = {
                'symbol': symbol,
                'sort': 'recent',
                'limit': limit,
                'offset': 0
            }
            
            response = requests.get(url, headers=self.headers, params=params, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            ideas = []
            
            for idea_data in data.get('ideas', []):
                # Фильтруем по качеству
                if (idea_data.get('likes', 0) >= self.min_likes and
                    idea_data.get('comments', 0) >= self.min_comments):
                    
                    # Проверяем возраст идеи
                    created_at = datetime.fromisoformat(idea_data['created_at'].replace('Z', '+00:00'))
                    age_hours = (datetime.now(created_at.tzinfo) - created_at).total_seconds() / 3600
                    
                    if age_hours <= self.max_age_hours:
                        idea = TradingViewIdea(
                            id=idea_data['id'],
                            title=idea_data['title'],
                            description=idea_data.get('description', ''),
                            author=idea_data['author']['username'],
                            symbol=idea_data['symbol'],
                            timeframe=idea_data.get('timeframe', ''),
                            direction=idea_data.get('direction', ''),
                            likes=idea_data.get('likes', 0),
                            comments=idea_data.get('comments', 0),
                            created_at=idea_data['created_at'],
                            url=f"{self.base_url}/ideas/{idea_data['id']}",
                            tags=idea_data.get('tags', [])
                        )
                        ideas.append(idea)
            
            return ideas
            
        except Exception as e:
            logger.error(f"Error fetching ideas for {symbol}: {e}")
            return []
    
    def extract_signals_from_idea(self, idea: TradingViewIdea) -> List[ImprovedSignal]:
        """Извлекает сигналы из идеи TradingView"""
        try:
            # Объединяем заголовок и описание
            full_text = f"{idea.title}\n{idea.description}"
            
            # Очищаем текст от TradingView-специфичных элементов
            cleaned_text = self._clean_tradingview_text(full_text)
            
            # Извлекаем сигналы
            signals = self.extractor.extract_signals_from_text(
                cleaned_text, f"tradingview_{idea.symbol}", f"idea_{idea.id}"
            )
            
            # Обогащаем сигналы информацией из идеи
            for signal in signals:
                signal.channel = f"tradingview_{idea.symbol}"
                signal.message_id = f"idea_{idea.id}"
                signal.signal_type = "tradingview"
                signal.timeframe = idea.timeframe or signal.timeframe
                
                # Если направление не определено в сигнале, используем из идеи
                if not signal.direction and idea.direction:
                    try:
                        signal.direction = SignalDirection(idea.direction.upper())
                    except:
                        pass
                
                # Добавляем метаданные
                signal.original_text = f"TradingView Idea: {idea.title}\n{idea.description}"
                signal.cleaned_text = cleaned_text
                
                # Рассчитываем дополнительную уверенность на основе популярности
                popularity_score = min((idea.likes + idea.comments) / 10, 20)
                if signal.real_confidence:
                    signal.real_confidence = min(signal.real_confidence + popularity_score, 100)
            
            return signals
            
        except Exception as e:
            logger.error(f"Error extracting signals from idea {idea.id}: {e}")
            return []
    
    def _clean_tradingview_text(self, text: str) -> str:
        """Очищает текст от TradingView-специфичных элементов"""
        # Убираем HTML теги
        text = re.sub(r'<[^>]+>', '', text)
        
        # Убираем ссылки на TradingView
        text = re.sub(r'https?://(?:www\.)?tradingview\.com[^\s]*', '', text)
        
        # Убираем упоминания символов в формате TradingView
        text = re.sub(r'[A-Z]{3,}USD', '', text)
        text = re.sub(r'[A-Z]{3,}USDT', '', text)
        
        # Убираем хештеги
        text = re.sub(r'#[^\s]+', '', text)
        
        # Убираем лишние пробелы и переносы строк
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\n+', '\n', text)
        
        return text.strip()
    
    def analyze_idea_quality(self, idea: TradingViewIdea) -> float:
        """Анализирует качество идеи"""
        quality_score = 0.0
        
        # Базовый скор за популярность
        quality_score += min(idea.likes / 10, 10.0)  # Максимум 10 баллов за лайки
        quality_score += min(idea.comments / 5, 5.0)  # Максимум 5 баллов за комментарии
        
        # Бонус за длинное описание
        if len(idea.description) > 100:
            quality_score += 5.0
        elif len(idea.description) > 50:
            quality_score += 2.0
        
        # Бонус за наличие тегов
        if idea.tags:
            quality_score += min(len(idea.tags) * 2, 10.0)
        
        # Бонус за указание таймфрейма
        if idea.timeframe:
            quality_score += 3.0
        
        # Бонус за указание направления
        if idea.direction:
            quality_score += 2.0
        
        return min(quality_score, 30.0)  # Максимум 30 баллов
    
    def parse_symbol(self, symbol: str) -> Dict[str, Any]:
        """Парсит идеи для конкретного символа"""
        try:
            logger.info(f"Parsing TradingView ideas for {symbol}")
            
            # Получаем идеи
            ideas = self.get_ideas_for_symbol(symbol)
            logger.info(f"Found {len(ideas)} relevant ideas for {symbol}")
            
            all_signals = []
            processed_ideas = 0
            
            for idea in ideas:
                try:
                    # Анализируем качество идеи
                    quality = self.analyze_idea_quality(idea)
                    
                    if quality >= 5.0:  # Минимальное качество
                        # Извлекаем сигналы
                        signals = self.extract_signals_from_idea(idea)
                        all_signals.extend(signals)
                        processed_ideas += 1
                        
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
        
        return filtered_signals[:30]  # Возвращаем топ-30 сигналов
    
    def parse_all_symbols(self) -> Dict[str, Any]:
        """Парсит идеи для всех настроенных символов"""
        all_results = []
        total_signals = 0
        
        for symbol in self.crypto_symbols:
            try:
                result = self.parse_symbol(symbol)
                all_results.append(result)
                
                if result['success']:
                    total_signals += result['filtered_signals']
                
                # Пауза между запросами
                time.sleep(3)
                
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
            'total_symbols': len(self.crypto_symbols),
            'successful_symbols': len([r for r in all_results if r['success']]),
            'total_signals': total_signals,
            'all_signals': all_signals,
            'symbol_results': all_results,
            'timestamp': datetime.now().isoformat()
        }
    
    def get_trending_ideas(self, limit: int = 50) -> List[TradingViewIdea]:
        """Получает трендовые идеи со всех символов"""
        try:
            url = f"{self.base_url}/api/v1/ideas/trending"
            params = {
                'limit': limit,
                'category': 'crypto'
            }
            
            response = requests.get(url, headers=self.headers, params=params, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            ideas = []
            
            for idea_data in data.get('ideas', []):
                # Проверяем, что это криптовалюта
                symbol = idea_data.get('symbol', '')
                if any(crypto in symbol for crypto in ['USD', 'USDT', 'BTC', 'ETH']):
                    idea = TradingViewIdea(
                        id=idea_data['id'],
                        title=idea_data['title'],
                        description=idea_data.get('description', ''),
                        author=idea_data['author']['username'],
                        symbol=idea_data['symbol'],
                        timeframe=idea_data.get('timeframe', ''),
                        direction=idea_data.get('direction', ''),
                        likes=idea_data.get('likes', 0),
                        comments=idea_data.get('comments', 0),
                        created_at=idea_data['created_at'],
                        url=f"{self.base_url}/ideas/{idea_data['id']}",
                        tags=idea_data.get('tags', [])
                    )
                    ideas.append(idea)
            
            return ideas
            
        except Exception as e:
            logger.error(f"Error fetching trending ideas: {e}")
            return []

def main():
    """Тестирование TradingView парсера"""
    parser = TradingViewParser()
    
    print("=== Тестирование TradingView парсера ===")
    
    # Тестируем парсинг одного символа
    print("\n1. Парсинг идей для BTCUSD:")
    result = parser.parse_symbol('BTCUSD')
    
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
    
    # Тестируем получение трендовых идей
    print("\n2. Получение трендовых идей:")
    trending_ideas = parser.get_trending_ideas(10)
    
    if trending_ideas:
        print(f"✅ Найдено {len(trending_ideas)} трендовых идей")
        
        all_signals = []
        for idea in trending_ideas[:5]:  # Обрабатываем первые 5
            signals = parser.extract_signals_from_idea(idea)
            all_signals.extend(signals)
        
        print(f"  Извлечено сигналов: {len(all_signals)}")
        
        if all_signals:
            print(f"\n📊 Примеры сигналов из трендовых идей:")
            for signal in all_signals[:3]:
                print(f"  - {signal.asset} {signal.direction.value}: {signal.signal_quality.value}")
    else:
        print(f"❌ Не удалось получить трендовые идеи")
    
    # Тестируем парсинг всех символов (ограниченно)
    print("\n3. Парсинг популярных символов:")
    popular_symbols = ['BTCUSD', 'ETHUSD', 'ADAUSD', 'SOLUSD']
    
    all_results = []
    total_signals = 0
    
    for symbol in popular_symbols:
        result = parser.parse_symbol(symbol)
        all_results.append(result)
        
        if result['success']:
            total_signals += result['filtered_signals']
        
        time.sleep(2)  # Пауза между запросами
    
    print(f"✅ Обработано {len([r for r in all_results if r['success']])} символов из {len(popular_symbols)}")
    print(f"  Всего сигналов: {total_signals}")
    
    # Сохраняем результаты
    with open('tradingview_signals.json', 'w', encoding='utf-8') as f:
        json.dump({
            'success': True,
            'total_symbols': len(popular_symbols),
            'successful_symbols': len([r for r in all_results if r['success']]),
            'total_signals': total_signals,
            'symbol_results': all_results,
            'timestamp': datetime.now().isoformat()
        }, f, indent=2, ensure_ascii=False)
    
    print(f"  Результаты сохранены в tradingview_signals.json")

if __name__ == "__main__":
    main()
