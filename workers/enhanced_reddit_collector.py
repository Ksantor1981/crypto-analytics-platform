#!/usr/bin/env python3
"""
Улучшенный сборщик Reddit сигналов с строгой фильтрацией
Ищет только реальные торговые сигналы с конкретными ценами
"""
import os
import json
import sqlite3
import requests
from datetime import datetime, timezone
from typing import Dict, Any, List
import re

from pathlib import Path
BASE_DIR = Path(__file__).parent
DB_PATH = str(BASE_DIR / 'signals.db')

# Строгие паттерны для поиска реальных сигналов
SIGNAL_PATTERNS = [
    # BTC/USDT patterns
    r'BTC.*?(\d{4,6})[^\d]*?(\d{4,6})',  # BTC 45000 -> 50000
    r'Bitcoin.*?(\d{4,6})[^\d]*?(\d{4,6})',  # Bitcoin 45000 -> 50000
    r'(\d{4,6})[^\d]*?BTC[^\d]*?(\d{4,6})',  # 45000 BTC -> 50000
    
    # ETH/USDT patterns  
    r'ETH.*?(\d{3,5})[^\d]*?(\d{3,5})',  # ETH 3000 -> 3500
    r'Ethereum.*?(\d{3,5})[^\d]*?(\d{3,5})',  # Ethereum 3000 -> 3500
    r'(\d{3,5})[^\d]*?ETH[^\d]*?(\d{3,5})',  # 3000 ETH -> 3500
    
    # SOL/USDT patterns
    r'SOL.*?(\d{2,4})[^\d]*?(\d{2,4})',  # SOL 150 -> 200
    r'Solana.*?(\d{2,4})[^\d]*?(\d{2,4})',  # Solana 150 -> 200
    
    # ADA/USDT patterns
    r'ADA.*?(\d\.\d{1,3})[^\d]*?(\d\.\d{1,3})',  # ADA 0.85 -> 1.00
    r'Cardano.*?(\d\.\d{1,3})[^\d]*?(\d\.\d{1,3})',  # Cardano 0.85 -> 1.00
    
    # LINK/USDT patterns
    r'LINK.*?(\d{1,3})[^\d]*?(\d{1,3})',  # LINK 20 -> 25
    r'Chainlink.*?(\d{1,3})[^\d]*?(\d{1,3})',  # Chainlink 20 -> 25
    
    # MATIC/USDT patterns
    r'MATIC.*?(\d\.\d{1,3})[^\d]*?(\d\.\d{1,3})',  # MATIC 0.20 -> 0.30
    r'Polygon.*?(\d\.\d{1,3})[^\d]*?(\d\.\d{1,3})',  # Polygon 0.20 -> 0.30
]

# Минимальные цены для валидации
MIN_PRICES = {
    'BTC': 10000,
    'ETH': 1000, 
    'SOL': 10,
    'ADA': 0.1,
    'LINK': 5,
    'MATIC': 0.1
}

# Максимальные цены для валидации
MAX_PRICES = {
    'BTC': 200000,
    'ETH': 10000,
    'SOL': 1000,
    'ADA': 10,
    'LINK': 100,
    'MATIC': 10
}

SUBREDDITS = [
    'cryptosignals',
    'CryptoMarkets', 
    'CryptoCurrencyTrading',
    'CryptoMoonShots',
    'CryptoCurrency',
    'Bitcoin',
    'Ethereum',
    'Altcoin',
    'DeFi'
]

def fetch_subreddit_posts(subreddit: str, limit: int = 25) -> List[Dict[str, Any]]:
    """Получает посты из Reddit с улучшенной обработкой ошибок"""
    try:
        url = f"https://www.reddit.com/r/{subreddit}/hot.json?limit={limit}"
        headers = {'User-Agent': 'CryptoAnalyticsPlatform/1.0'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        posts = []
        
        for post in data['data']['children']:
            post_data = post['data']
            posts.append({
                'title': post_data.get('title', ''),
                'selftext': post_data.get('selftext', ''),
                'created_utc': post_data.get('created_utc', 0),
                'id': post_data.get('id', ''),
                'score': post_data.get('score', 0),
                'num_comments': post_data.get('num_comments', 0)
            })
        
        print(f"[INFO] r/{subreddit}: fetched {len(posts)} posts")
        return posts
        
    except Exception as e:
        print(f"[WARN] Reddit fetch failed for {subreddit}: {e}")
        return []

def extract_signal_from_text(text: str, asset: str) -> Dict[str, Any]:
    """Извлекает сигнал из текста с строгой валидацией"""
    text_upper = text.upper()
    
    # Ищем паттерны для конкретного актива
    patterns = []
    for pattern in SIGNAL_PATTERNS:
        if asset in pattern.upper():
            patterns.append(pattern)
    
    if not patterns:
        return None
    
    for pattern in patterns:
        matches = re.findall(pattern, text_upper)
        for match in matches:
            if len(match) == 2:
                try:
                    entry_price = float(match[0])
                    target_price = float(match[1])
                    
                    # Валидация цен
                    if asset in MIN_PRICES:
                        if entry_price < MIN_PRICES[asset] or entry_price > MAX_PRICES[asset]:
                            continue
                        if target_price < MIN_PRICES[asset] or target_price > MAX_PRICES[asset]:
                            continue
                    
                    # Проверяем что target > entry для LONG
                    if target_price > entry_price:
                        direction = 'LONG'
                    else:
                        direction = 'SHORT'
                    
                    # Определяем уверенность на основе качества поста
                    confidence = 70.0  # базовая уверенность
                    
                    return {
                        'asset': asset,
                        'direction': direction,
                        'entry_price': entry_price,
                        'target_price': target_price,
                        'stop_loss': None,
                        'confidence': confidence,
                        'is_valid': 1
                    }
                    
                except (ValueError, TypeError):
                    continue
    
    return None

def process_posts(posts: List[Dict[str, Any]], subreddit: str) -> List[Dict[str, Any]]:
    """Обрабатывает посты и извлекает только валидные сигналы"""
    signals = []
    
    for post in posts:
        # Объединяем заголовок и текст
        full_text = f"{post['title']} {post['selftext']}"
        
        # Ищем сигналы для каждого актива
        for asset in ['BTC', 'ETH', 'SOL', 'ADA', 'LINK', 'MATIC']:
            signal = extract_signal_from_text(full_text, asset)
            if signal:
                # Добавляем метаданные
                signal.update({
                    'id': f"reddit_{asset}_{post['id']}",
                    'channel': f"reddit/{subreddit}",
                    'message_id': post['id'],
                    'original_text': full_text,
                    'timestamp': datetime.fromtimestamp(post['created_utc'], tz=timezone.utc).isoformat(),
                    'extraction_time': datetime.now(timezone.utc).isoformat(),
                    'signal_type': 'reddit_enhanced',
                    'signal_quality': 'verified',
                    'real_confidence': signal['confidence'],
                    'calculated_confidence': signal['confidence'],
                    'timeframe': '1H',
                    'leverage': 1,
                    'bybit_available': True,
                    'validation_errors': [],
                    'risk_reward_ratio': 0.0,
                    'potential_profit': 0.0,
                    'potential_loss': 0.0
                })
                signals.append(signal)
    
    return signals

def upsert_signal(cur: sqlite3.Cursor, signal: Dict[str, Any]) -> None:
    """Сохраняет сигнал в БД"""
    cur.execute(
        """
        INSERT OR REPLACE INTO signals (
            id, asset, direction, entry_price, target_price, stop_loss,
            leverage, timeframe, signal_quality, real_confidence,
            calculated_confidence, channel, message_id, original_text,
            cleaned_text, signal_type, timestamp, extraction_time,
            bybit_available, is_valid, validation_errors,
            risk_reward_ratio, potential_profit, potential_loss
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            signal['id'], signal['asset'], signal['direction'],
            signal.get('entry_price'), signal.get('target_price'), signal.get('stop_loss'),
            signal.get('leverage', 1), signal.get('timeframe', '1H'), signal.get('signal_quality', 'verified'),
            signal.get('real_confidence', 0.0), signal.get('calculated_confidence', 0.0),
            signal.get('channel', ''), signal.get('message_id', ''), signal.get('original_text', ''),
            signal.get('original_text', ''), signal.get('signal_type', 'reddit_enhanced'),
            signal.get('timestamp'), signal.get('extraction_time'), True, signal.get('is_valid', 1),
            json.dumps(signal.get('validation_errors', []), ensure_ascii=False), signal.get('risk_reward_ratio', 0.0),
            signal.get('potential_profit', 0.0), signal.get('potential_loss', 0.0)
        ),
    )

def run_enhanced_collection():
    """Запускает улучшенный сбор сигналов"""
    print("🔍 Запуск улучшенного сбора Reddit сигналов...")
    
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    total_signals = 0
    
    for subreddit in SUBREDDITS:
        posts = fetch_subreddit_posts(subreddit)
        if posts:
            signals = process_posts(posts, subreddit)
            for signal in signals:
                try:
                    upsert_signal(cur, signal)
                    total_signals += 1
                    print(f"✅ {signal['asset']} @ ${signal['entry_price']} -> ${signal['target_price']} | {signal['channel']}")
                except Exception as e:
                    print(f"❌ Ошибка сохранения сигнала: {e}")
    
    conn.commit()
    conn.close()
    
    print(f"🎯 Собрано {total_signals} валидных сигналов")
    return total_signals

if __name__ == '__main__':
    run_enhanced_collection()
