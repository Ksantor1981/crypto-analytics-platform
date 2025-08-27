"""
Reddit Parser - Парсер для Reddit криптовалютных сообществ
Извлекает сигналы и аналитику из популярных subreddit'ов
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

@dataclass
class RedditComment:
    """Комментарий с Reddit"""
    id: str
    body: str
    author: str
    score: int
    created_utc: int
    parent_id: str

class RedditParser:
    """Парсер для Reddit"""
    
    def __init__(self):
        self.extractor = ImprovedSignalExtractor()
        self.base_url = "https://www.reddit.com"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Криптовалютные subreddit'ы
        self.subreddits = [
            'cryptocurrency',
            'bitcoin',
            'altcoin',
            'CryptoMoonShots',
            'CryptoCurrency',
            'CryptoMarkets',
            'CryptoNews',
            'CryptoTechnology'
        ]
        
        # Фильтры для релевантности
        self.min_score = 10  # Минимальный рейтинг поста
        self.min_comments = 5  # Минимальное количество комментариев
        self.max_age_hours = 24  # Максимальный возраст поста в часах
    
    def get_hot_posts(self, subreddit: str, limit: int = 25) -> List[RedditPost]:
        """Получает горячие посты из subreddit"""
        try:
            url = f"{self.base_url}/r/{subreddit}/hot.json?limit={limit}"
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            posts = []
            
            for post_data in data['data']['children']:
                post = post_data['data']
                
                # Фильтруем по релевантности
                if (post['score'] >= self.min_score and 
                    post['num_comments'] >= self.min_comments and
                    not post['stickied'] and
                    not post['over_18']):
                    
                    # Проверяем возраст поста
                    post_age = time.time() - post['created_utc']
                    if post_age <= self.max_age_hours * 3600:
                        
                        reddit_post = RedditPost(
                            id=post['id'],
                            title=post['title'],
                            content=post.get('selftext', ''),
                            author=post['author'],
                            subreddit=post['subreddit'],
                            score=post['score'],
                            comments_count=post['num_comments'],
                            created_utc=post['created_utc'],
                            url=post['url'],
                            is_self=post['is_self']
                        )
                        posts.append(reddit_post)
            
            return posts
            
        except Exception as e:
            logger.error(f"Error fetching posts from r/{subreddit}: {e}")
            return []
    
    def get_post_comments(self, subreddit: str, post_id: str, limit: int = 50) -> List[RedditComment]:
        """Получает комментарии к посту"""
        try:
            url = f"{self.base_url}/r/{subreddit}/comments/{post_id}.json?limit={limit}"
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            comments = []
            
            if len(data) > 1:  # Есть комментарии
                comments_data = data[1]['data']['children']
                
                for comment_data in comments_data:
                    if comment_data['kind'] == 't1':  # Комментарий
                        comment = comment_data['data']
                        
                        # Фильтруем по релевантности
                        if comment['score'] >= 2 and len(comment['body']) > 20:
                            
                            reddit_comment = RedditComment(
                                id=comment['id'],
                                body=comment['body'],
                                author=comment['author'],
                                score=comment['score'],
                                created_utc=comment['created_utc'],
                                parent_id=comment['parent_id']
                            )
                            comments.append(reddit_comment)
            
            return comments
            
        except Exception as e:
            logger.error(f"Error fetching comments for post {post_id}: {e}")
            return []
    
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
            
            # Получаем горячие посты
            posts = self.get_hot_posts(subreddit)
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
                            comments = self.get_post_comments(subreddit, post.id)
                            
                            for comment in comments[:10]:  # Топ-10 комментариев
                                comment_signals = self.extract_signals_from_text(
                                    comment.body, f"reddit_{subreddit}", f"comment_{comment.id}"
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
        
        return filtered_signals[:50]  # Возвращаем топ-50 сигналов
    
    def parse_all_subreddits(self) -> Dict[str, Any]:
        """Парсит все настроенные subreddit'ы"""
        all_results = []
        total_signals = 0
        
        for subreddit in self.subreddits:
            try:
                result = self.parse_subreddit(subreddit)
                all_results.append(result)
                
                if result['success']:
                    total_signals += result['filtered_signals']
                
                # Пауза между запросами
                time.sleep(2)
                
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
            'total_subreddits': len(self.subreddits),
            'successful_subreddits': len([r for r in all_results if r['success']]),
            'total_signals': total_signals,
            'all_signals': all_signals,
            'subreddit_results': all_results,
            'timestamp': datetime.now().isoformat()
        }

def main():
    """Тестирование Reddit парсера"""
    parser = RedditParser()
    
    print("=== Тестирование Reddit парсера ===")
    
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
        with open('reddit_signals.json', 'w', encoding='utf-8') as f:
            json.dump(all_results, f, indent=2, ensure_ascii=False)
        
        print(f"  Результаты сохранены в reddit_signals.json")
    else:
        print(f"❌ Ошибка при парсинге всех subreddit'ов")

if __name__ == "__main__":
    main()
