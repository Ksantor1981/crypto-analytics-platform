#!/usr/bin/env python3
import sqlite3
import os
import sys
from datetime import datetime
sys.path.append(os.path.join(os.path.dirname(__file__), 'workers'))
from collect_reddit_signals import fetch_subreddit_posts, ensure_tables, upsert_signal
from enhanced_price_extractor import EnhancedPriceExtractor

DB_PATH = 'workers/signals.db'

def clean_and_reload():
    # Очищаем БД
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM signals")
    conn.commit()
    conn.close()
    
    print("🗑️ БД очищена")
    
    # Загружаем только реальные reddit данные
    extractor = EnhancedPriceExtractor()
    conn = sqlite3.connect(DB_PATH)
    ensure_tables(conn)
    
    subreddits = ['CryptoCurrency', 'Bitcoin', 'CryptoMarkets', 'CryptoCurrencyTrading']
    total_signals = 0
    
    for sub in subreddits:
        posts = fetch_subreddit_posts(sub, 25)
        print(f'[INFO] r/{sub}: fetched {len(posts)} posts')
        
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
                
                # Сериализуем для БД
                from collect_reddit_signals import to_db_row
                upsert_signal(conn, to_db_row(signal))
                total_signals += 1
            except Exception as e:
                print(f'[WARN] Extract/insert failed for post {message_id}: {e}')

        conn.commit()

    conn.close()
    print(f'[DONE] Загружено {total_signals} реальных сигналов из Reddit')

if __name__ == '__main__':
    clean_and_reload()
