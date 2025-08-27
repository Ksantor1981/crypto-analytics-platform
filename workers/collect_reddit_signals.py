#!/usr/bin/env python3
"""
Реальный сборщик сигналов с Reddit без ключей API.
Тянет посты через публичные JSON-эндпоинты Reddit, извлекает сигналы
через EnhancedPriceExtractor и сохраняет в workers/signals.db
"""

import json
import sqlite3
import time
from datetime import datetime
from typing import List, Dict
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__)))
from enhanced_price_extractor import EnhancedPriceExtractor

DB_PATH = os.path.join(os.path.dirname(__file__), 'signals.db')
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) RedditCollector/1.0'
# Обновленный список сабреддитов для сбора сигналов
SUBREDDITS = [
    'cryptosignals',           # ~7 тыс. участников
    'CryptoMarkets',           # ~1.8 млн участников  
    'CryptoCurrencyTrading',   # Трейдинг и сигналы
    'CryptoMoonShots',         # Альткоины с высоким потенциалом
    'CryptoCurrency',          # Крупное и активное сообщество
    'Bitcoin',                 # BTC-фокус
    'Ethereum',                # ETH-фокус
    'Altcoin',                 # Альткойн-дискуссии
    'DeFi',                    # Обсуждение DeFi
    'CryptoCurrencySignals'    # Обсуждения сигналов
]

LIMIT_PER_SUB = 25
TIMEOUT = 10


def fetch_reddit_json(url: str) -> Dict:
    req = Request(url, headers={'User-Agent': USER_AGENT})
    with urlopen(req, timeout=TIMEOUT) as resp:
        return json.loads(resp.read().decode('utf-8'))


def fetch_subreddit_posts(subreddit: str, limit: int) -> List[Dict]:
    # new and hot for variety
    urls = [
        f'https://www.reddit.com/r/{subreddit}/new.json?limit={limit}',
        f'https://www.reddit.com/r/{subreddit}/hot.json?limit={limit}',
    ]
    posts: List[Dict] = []
    seen = set()
    for url in urls:
        try:
            data = fetch_reddit_json(url)
            children = (data.get('data') or {}).get('children') or []
            for item in children:
                post = item.get('data') or {}
                post_id = post.get('id')
                if not post_id or post_id in seen:
                    continue
                seen.add(post_id)
                posts.append(post)
        except (URLError, HTTPError) as e:
            print(f'[WARN] Reddit fetch failed for {subreddit}: {e}')
        except Exception as e:
            print(f'[WARN] Unexpected error for {subreddit}: {e}')
        time.sleep(0.5)
    return posts


def ensure_tables(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    # Таблица signals должна уже существовать, но добавим страховку
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS signals (
            id TEXT PRIMARY KEY,
            asset TEXT,
            direction TEXT,
            entry_price REAL,
            target_price REAL,
            stop_loss REAL,
            leverage INTEGER,
            timeframe TEXT,
            signal_quality TEXT,
            real_confidence REAL,
            calculated_confidence REAL,
            channel TEXT,
            message_id TEXT,
            original_text TEXT,
            cleaned_text TEXT,
            signal_type TEXT,
            timestamp TEXT,
            extraction_time TEXT,
            bybit_available BOOLEAN,
            is_valid BOOLEAN,
            validation_errors TEXT,
            risk_reward_ratio REAL,
            potential_profit REAL,
            potential_loss REAL
        )
        """
    )
    conn.commit()


def upsert_signal(conn: sqlite3.Connection, signal: Dict) -> None:
    cur = conn.cursor()
    columns = ','.join(signal.keys())
    placeholders = ','.join(['?'] * len(signal))
    update_assignments = ','.join([f"{k} = excluded.{k}" for k in signal.keys() if k != 'id'])
    cur.execute(
        f"""
        INSERT INTO signals ({columns}) VALUES ({placeholders})
        ON CONFLICT(id) DO UPDATE SET {update_assignments}
        """,
        list(signal.values()),
    )


def to_db_row(signal: Dict) -> Dict:
    normalized: Dict = {}
    for k, v in signal.items():
        if isinstance(v, (dict, list)):
            normalized[k] = json.dumps(v, ensure_ascii=False)
        else:
            normalized[k] = v
    # Явно строка для validation_errors
    if 'validation_errors' in normalized and normalized['validation_errors'] is None:
        normalized['validation_errors'] = '[]'
    return normalized


def main() -> None:
    extractor = EnhancedPriceExtractor()
    conn = sqlite3.connect(DB_PATH)
    ensure_tables(conn)

    total_posts = 0
    total_signals = 0

    for sub in SUBREDDITS:
        posts = fetch_subreddit_posts(sub, LIMIT_PER_SUB)
        print(f'[INFO] r/{sub}: fetched {len(posts)} posts')
        total_posts += len(posts)

        for post in posts:
            title = (post.get('title') or '').strip()
            selftext = (post.get('selftext') or '').strip()
            text = f"{title}\n\n{selftext}".strip()
            if not text:
                continue

            channel = f"reddit/{sub}"
            message_id = post.get('id') or ''

            try:
                signal = extractor.extract_signal(text=text, channel=channel, message_id=message_id)
                # Обогащаем полями времени
                created_utc = post.get('created_utc')
                if created_utc:
                    dt = datetime.utcfromtimestamp(created_utc).isoformat()
                    signal['timestamp'] = dt
                    signal['extraction_time'] = datetime.utcnow().isoformat()
                # Генерируем стабильный id на основе reddit id
                asset = signal.get('asset') or 'UNK'
                signal['id'] = f"{asset}_{message_id}"
                upsert_signal(conn, to_db_row(signal))
                total_signals += 1
            except Exception as e:
                print(f'[WARN] Extract/insert failed for post {message_id}: {e}')

        conn.commit()

    conn.close()
    print(f'[DONE] Processed posts: {total_posts}, inserted/updated signals: {total_signals}')


if __name__ == '__main__':
    main()
