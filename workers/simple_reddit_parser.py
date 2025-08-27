"""
Simple Reddit Parser - Упрощенный парсер для Reddit
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
class RedditPost:
    """Пост с Reddit"""
    id: str
    title: str
    content: str
    author: str
    subreddit: str
    score: int
    comments_count: int
    created_utc: int
    url: str
    is_self: bool

class SimpleRedditParser:
    """Упрощенный парсер для Reddit"""
    
    def __init__(self):
        self.extractor = ImprovedSignalExtractor()
        
        # Демонстрационные данные Reddit
        self.demo_posts = [
            {
                'id': 'demo_1',
                'title': 'BTC LONG Entry: 50000 Target: 55000 Stop: 48000 - Technical Analysis',
                'content': 'Bitcoin showing strong bullish momentum. Entry at 50000, target 55000, stop loss at 48000. Risk/Reward ratio is excellent.',
                'author': 'crypto_analyst',
                'subreddit': 'cryptocurrency',
                'score': 150,
                'comments_count': 25,
                'created_utc': int(time.time()) - 3600,
                'url': 'https://reddit.com/r/cryptocurrency/demo_1',
                'is_self': True
            },
            {
                'id': 'demo_2',
                'title': 'ETH SHORT opportunity - Entry: 3000 Target: 2800 Stop: 3200',
                'content': 'Ethereum facing resistance at 3200. Short entry at 3000, target 2800, stop loss at 3200. Bearish divergence on RSI.',
                'author': 'eth_trader',
                'subreddit': 'bitcoin',
                'score': 89,
                'comments_count': 15,
                'created_utc': int(time.time()) - 7200,
                'url': 'https://reddit.com/r/bitcoin/demo_2',
                'is_self': True
            },
            {
                'id': 'demo_3',
                'title': 'ADA breakout confirmed - LONG Entry: 0.45 Target: 0.55 Stop: 0.42',
                'content': 'Cardano breaking out of consolidation. Long entry at 0.45, target 0.55, stop loss at 0.42. Volume increasing.',
                'author': 'ada_hodler',
                'subreddit': 'altcoin',
                'score': 67,
                'comments_count': 12,
                'created_utc': int(time.time()) - 10800,
                'url': 'https://reddit.com/r/altcoin/demo_3',
                'is_self': True
            },
            {
                'id': 'demo_4',
                'title': 'SOL potential reversal - SHORT Entry: 120 Target: 110 Stop: 125',
                'content': 'Solana showing bearish signals. Short entry at 120, target 110, stop loss at 125. MACD crossing down.',
                'author': 'sol_analyst',
                'subreddit': 'CryptoMarkets',
                'score': 45,
                'comments_count': 8,
                'created_utc': int(time.time()) - 14400,
                'url': 'https://reddit.com/r/CryptoMarkets/demo_4',
                'is_self': True
            },
            {
                'id': 'demo_5',
                'title': 'DOT accumulation zone - LONG Entry: 6.5 Target: 7.5 Stop: 6.2',
                'content': 'Polkadot in accumulation zone. Long entry at 6.5, target 7.5, stop loss at 6.2. Strong support level.',
                'author': 'dot_investor',
                'subreddit': 'cryptocurrency',
                'score': 123,
                'comments_count': 18,
                'created_utc': int(time.time()) - 18000,
                'url': 'https://reddit.com/r/cryptocurrency/demo_5',
                'is_self': True
            }
        ]
        
        # Демонстрационные комментарии
        self.demo_comments = [
            {
                'id': 'comment_1',
                'body': 'Great analysis! I agree with the BTC long setup. Entry at 50000 looks solid.',
                'author': 'trader_pro',
                'score': 15,
                'created_utc': int(time.time()) - 1800,
                'parent_id': 'demo_1'
            },
            {
                'id': 'comment_2',
                'body': 'ETH short signal confirmed. Entry: 3000 Target: 2800 Stop: 3200. Risk/Reward 2:1',
                'author': 'eth_whale',
                'score': 23,
                'created_utc': int(time.time()) - 3600,
                'parent_id': 'demo_2'
            },
            {
                'id': 'comment_3',
                'body': 'ADA breakout looks promising. LONG Entry: 0.45 Target: 0.55 Stop: 0.42',
                'author': 'ada_fan',
                'score': 8,
                'created_utc': int(time.time()) - 5400,
                'parent_id': 'demo_3'
            }
        ]
    
    def get_demo_posts(self, subreddit: str = None) -> List[RedditPost]:
        """Получает демонстрационные посты"""
        posts = []
        
        for post_data in self.demo_posts:
            if subreddit is None or post_data['subreddit'] == subreddit:
                post = RedditPost(
                    id=post_data['id'],
                    title=post_data['title'],
                    content=post_data['content'],
                    author=post_data['author'],
                    subreddit=post_data['subreddit'],
                    score=post_data['score'],
                    comments_count=post_data['comments_count'],
                    created_utc=post_data['created_utc'],
                    url=post_data['url'],
                    is_self=post_data['is_self']
                )
                posts.append(post)
        
        return posts
    
    def get_demo_comments(self, post_id: str) -> List[Dict]:
        """Получает демонстрационные комментарии к посту"""
        return [comment for comment in self.demo_comments if comment['parent_id'] == post_id]
    
    def extract_signals_from_text(self, text: str, source: str, source_id: str) -> List[ImprovedSignal]:
        """Извлекает сигналы из текста"""
        try:
            # Очищаем текст от Reddit-специфичных элементов
            cleaned_text = self._clean_reddit_text(text)
            
            # Извлекаем сигналы
            signals = self.extractor.extract_signals_from_text(cleaned_text, source, source_id)
            
            # Обогащаем сигналы информацией о источнике
            for signal in signals:
                signal.channel = source
                signal.message_id = source_id
                signal.signal_type = "reddit"
            
            return signals
            
        except Exception as e:
            logger.error(f"Error extracting signals from text: {e}")
            return []
    
    def _clean_reddit_text(self, text: str) -> str:
        """Очищает текст от Reddit-специфичных элементов"""
        # Убираем ссылки на Reddit
        text = re.sub(r'https?://(?:www\.)?reddit\.com[^\s]*', '', text)
        
        # Убираем упоминания пользователей
        text = re.sub(r'/u/[^\s]+', '', text)
        text = re.sub(r'u/[^\s]+', '', text)
        
        # Убираем ссылки на subreddit'ы
        text = re.sub(r'/r/[^\s]+', '', text)
        text = re.sub(r'r/[^\s]+', '', text)
        
        # Убираем markdown разметку
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)  # Жирный текст
        text = re.sub(r'\*([^*]+)\*', r'\1', text)      # Курсив
        text = re.sub(r'`([^`]+)`', r'\1', text)        # Код
        text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)  # Ссылки
        
        # Убираем лишние пробелы
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def analyze_post_relevance(self, post: RedditPost) -> float:
        """Анализирует релевантность поста для крипто-сигналов"""
        relevance_score = 0.0
        
        # Ключевые слова для крипто-сигналов
        crypto_keywords = [
            'buy', 'sell', 'long', 'short', 'entry', 'target', 'stop loss',
            'btc', 'eth', 'bitcoin', 'ethereum', 'altcoin', 'moon', 'pump',
            'dump', 'bullish', 'bearish', 'breakout', 'support', 'resistance',
            'technical analysis', 'ta', 'chart', 'price', 'market'
        ]
        
        # Анализируем заголовок
        title_lower = post.title.lower()
        for keyword in crypto_keywords:
            if keyword in title_lower:
                relevance_score += 2.0
        
        # Анализируем контент
        content_lower = post.content.lower()
        for keyword in crypto_keywords:
            if keyword in content_lower:
                relevance_score += 1.0
        
        # Бонус за популярность
        relevance_score += min(post.score / 100, 5.0)  # Максимум 5 баллов за рейтинг
        relevance_score += min(post.comments_count / 20, 3.0)  # Максимум 3 балла за комментарии
        
        return min(relevance_score, 20.0)  # Максимум 20 баллов
    
    def parse_subreddit(self, subreddit: str) -> Dict[str, Any]:
        """Парсит subreddit и извлекает сигналы"""
        try:
            logger.info(f"Parsing subreddit: r/{subreddit}")
            
            # Получаем демонстрационные посты
            posts = self.get_demo_posts(subreddit)
            logger.info(f"Found {len(posts)} relevant posts in r/{subreddit}")
            
            all_signals = []
            processed_posts = 0
            
            for post in posts:
                try:
                    # Анализируем релевантность
                    relevance = self.analyze_post_relevance(post)
                    
                    if relevance >= 5.0:  # Минимальная релевантность
                        # Извлекаем сигналы из заголовка и контента
                        title_signals = self.extract_signals_from_text(
                            post.title, f"reddit_{subreddit}", f"post_{post.id}_title"
                        )
                        
                        content_signals = self.extract_signals_from_text(
                            post.content, f"reddit_{subreddit}", f"post_{post.id}_content"
                        )
                        
                        # Получаем комментарии для топ-постов
                        if post.score >= 50:
                            comments = self.get_demo_comments(post.id)
                            
                            for comment in comments[:5]:  # Топ-5 комментариев
                                comment_signals = self.extract_signals_from_text(
                                    comment['body'], f"reddit_{subreddit}", f"comment_{comment['id']}"
                                )
                                all_signals.extend(comment_signals)
                        
                        all_signals.extend(title_signals)
                        all_signals.extend(content_signals)
                        processed_posts += 1
                        
                except Exception as e:
                    logger.error(f"Error processing post {post.id}: {e}")
                    continue
            
            # Фильтруем и ранжируем сигналы
            filtered_signals = self._filter_and_rank_signals(all_signals)
            
            return {
                'success': True,
                'subreddit': subreddit,
                'total_posts': len(posts),
                'processed_posts': processed_posts,
                'total_signals': len(all_signals),
                'filtered_signals': len(filtered_signals),
                'signals': filtered_signals,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error parsing subreddit r/{subreddit}: {e}")
            return {
                'success': False,
                'subreddit': subreddit,
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
        
        return filtered_signals[:20]  # Возвращаем топ-20 сигналов
    
    def parse_all_subreddits(self) -> Dict[str, Any]:
        """Парсит все настроенные subreddit'ы"""
        subreddits = ['cryptocurrency', 'bitcoin', 'altcoin', 'CryptoMarkets']
        all_results = []
        total_signals = 0
        
        for subreddit in subreddits:
            try:
                result = self.parse_subreddit(subreddit)
                all_results.append(result)
                
                if result['success']:
                    total_signals += result['filtered_signals']
                
                # Пауза между запросами
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Error parsing subreddit {subreddit}: {e}")
                continue
        
        # Объединяем все сигналы
        all_signals = []
        for result in all_results:
            if result['success']:
                all_signals.extend(result['signals'])
        
        return {
            'success': True,
            'total_subreddits': len(subreddits),
            'successful_subreddits': len([r for r in all_results if r['success']]),
            'total_signals': total_signals,
            'all_signals': all_signals,
            'subreddit_results': all_results,
            'timestamp': datetime.now().isoformat()
        }

def main():
    """Тестирование упрощенного Reddit парсера"""
    parser = SimpleRedditParser()
    
    print("=== Тестирование упрощенного Reddit парсера ===")
    
    # Тестируем парсинг одного subreddit
    print("\n1. Парсинг r/cryptocurrency:")
    result = parser.parse_subreddit('cryptocurrency')
    
    if result['success']:
        print(f"✅ Обработано {result['processed_posts']} постов из {result['total_posts']}")
        print(f"  Найдено сигналов: {result['total_signals']}")
        print(f"  Отфильтровано: {result['filtered_signals']}")
        
        if result['signals']:
            print(f"\n📊 Примеры сигналов:")
            for signal in result['signals'][:3]:
                print(f"  - {signal.asset} {signal.direction.value}: {signal.signal_quality.value}")
    else:
        print(f"❌ Ошибка: {result['error']}")
    
    # Тестируем парсинг всех subreddit'ов
    print("\n2. Парсинг всех subreddit'ов:")
    all_results = parser.parse_all_subreddits()
    
    if all_results['success']:
        print(f"✅ Обработано {all_results['successful_subreddits']} subreddit'ов из {all_results['total_subreddits']}")
        print(f"  Всего сигналов: {all_results['total_signals']}")
        
        # Сохраняем результаты
        with open('simple_reddit_signals.json', 'w', encoding='utf-8') as f:
            # Конвертируем сигналы в словари для JSON сериализации
            serializable_results = all_results.copy()
            serializable_results['all_signals'] = [asdict(signal) for signal in all_results['all_signals']]
            for result in serializable_results['subreddit_results']:
                if result['success']:
                    result['signals'] = [asdict(signal) for signal in result['signals']]
            
            json.dump(serializable_results, f, indent=2, ensure_ascii=False, cls=SignalJSONEncoder)
        
        print(f"  Результаты сохранены в simple_reddit_signals.json")
    else:
        print(f"❌ Ошибка при парсинге всех subreddit'ов")

if __name__ == "__main__":
    main()
