#!/usr/bin/env python3
"""
Сбор РЕАЛЬНЫХ данных из Reddit и API
Без Telethon (пока не решена проблема с виртуальным окружением)
"""
import os
import sqlite3
import json
import re
from datetime import datetime, timezone, timedelta
from pathlib import Path

def load_env():
    """Загружает данные из .env файла"""
    env_path = Path('.env')
    if env_path.exists():
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value

def collect_from_reddit():
    """Собирает данные из Reddit"""
    print("📊 Сбор РЕАЛЬНЫХ данных из Reddit...")
    
    try:
        import requests
        print("✅ Requests импортирован")
    except ImportError:
        print("❌ Requests не установлен")
        return 0
    
    # Reddit API данные
    client_id = os.getenv('REDDIT_CLIENT_ID')
    client_secret = os.getenv('REDDIT_CLIENT_SECRET')
    user_agent = os.getenv('REDDIT_USER_AGENT', 'crypto app v1.0')
    
    if not all([client_id, client_secret]):
        print("❌ Reddit API данные не настроены")
        return 0
    
    # Авторизация в Reddit
    auth_url = 'https://www.reddit.com/api/v1/access_token'
    auth_data = {
        'grant_type': 'client_credentials'
    }
    auth_headers = {
        'User-Agent': user_agent
    }
    
    try:
        response = requests.post(
            auth_url,
            data=auth_data,
            headers=auth_headers,
            auth=(client_id, client_secret)
        )
        response.raise_for_status()
        token = response.json()['access_token']
        print("✅ Авторизация в Reddit успешна")
    except Exception as e:
        print(f"❌ Ошибка авторизации Reddit: {e}")
        return 0
    
    # Список сабреддитов для сбора
    subreddits = [
        'cryptosignals', 'CryptoMarkets', 'CryptoCurrencyTrading',
        'CryptoMoonShots', 'CryptoCurrency', 'Bitcoin', 'Ethereum',
        'Altcoin', 'DeFi'
    ]
    
    total_signals = 0
    
    for subreddit in subreddits:
        try:
            print(f"📊 Сбор из r/{subreddit}...")
            
            url = f'https://oauth.reddit.com/r/{subreddit}/hot.json?limit=25'
            headers = {
                'Authorization': f'Bearer {token}',
                'User-Agent': user_agent
            }
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            subreddit_signals = 0
            for post in data['data']['children']:
                post_data = post['data']
                title = post_data.get('title', '')
                selftext = post_data.get('selftext', '')
                full_text = f"{title}\n{selftext}"
                
                # Ищем сигналы в тексте
                signal = extract_signal_from_text(full_text, f"reddit/{subreddit}", post_data['id'])
                if signal:
                    save_signal_to_db(signal, datetime.fromtimestamp(post_data['created_utc'], tz=timezone.utc))
                    subreddit_signals += 1
                    total_signals += 1
            
            print(f"   📈 Собрано {subreddit_signals} сигналов из r/{subreddit}")
            
        except Exception as e:
            print(f"   ❌ Ошибка сбора из r/{subreddit}: {str(e)[:50]}")
    
    return total_signals

def collect_from_crypto_apis():
    """Собирает данные из крипто API"""
    print("📊 Сбор РЕАЛЬНЫХ данных из крипто API...")
    
    try:
        import requests
    except ImportError:
        print("❌ Requests не установлен")
        return 0
    
    total_signals = 0
    
    # Crypto Quality Signals API
    try:
        print("📊 Сбор из Crypto Quality Signals...")
        
        url = "https://api.cryptoqualitysignals.com/v1/signals"
        params = {
            'api_key': 'FREE',  # Бесплатный доступ
            'limit': 20
        }
        
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            
            api_signals = 0
            for signal_data in data.get('signals', []):
                signal = convert_api_signal(signal_data, 'crypto_quality_signals')
                if signal:
                    save_signal_to_db(signal, datetime.now(timezone.utc))
                    api_signals += 1
                    total_signals += 1
            
            print(f"   📈 Собрано {api_signals} сигналов из Crypto Quality Signals")
        else:
            print(f"   ❌ Ошибка API: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Ошибка Crypto Quality Signals: {str(e)[:50]}")
    
    return total_signals

def extract_signal_from_text(text, source, message_id):
    """Извлекает сигнал из текста"""
    if not text:
        return None
    
    text_upper = text.upper()
    
    # Определяем актив
    asset = None
    if 'BTC' in text_upper or 'BITCOIN' in text_upper:
        asset = 'BTC'
    elif 'ETH' in text_upper or 'ETHEREUM' in text_upper:
        asset = 'ETH'
    elif 'SOL' in text_upper or 'SOLANA' in text_upper:
        asset = 'SOL'
    elif 'ADA' in text_upper or 'CARDANO' in text_upper:
        asset = 'ADA'
    elif 'LINK' in text_upper or 'CHAINLINK' in text_upper:
        asset = 'LINK'
    elif 'MATIC' in text_upper or 'POLYGON' in text_upper:
        asset = 'MATIC'
    
    if not asset:
        return None
    
    # Ищем цены с более гибкими паттернами
    price_patterns = [
        rf'{asset}.*?(\d{{4,6}})[^\d]*?(\d{{4,6}})',
        rf'(\d{{4,6}})[^\d]*?{asset}[^\d]*?(\d{{4,6}})',
        rf'{asset}.*?(\d{{3,5}})[^\d]*?(\d{{3,5}})',
        rf'(\d{{3,5}})[^\d]*?{asset}[^\d]*?(\d{{3,5}})',
    ]
    
    for pattern in price_patterns:
        matches = re.findall(pattern, text_upper)
        for match in matches:
            if len(match) == 2:
                try:
                    entry_price = float(match[0])
                    target_price = float(match[1])
                    
                    # Валидация цен
                    if entry_price <= 0 or target_price <= 0:
                        continue
                    
                    # Проверяем разумность цен
                    if asset == 'BTC' and (entry_price < 10000 or entry_price > 200000):
                        continue
                    elif asset == 'ETH' and (entry_price < 1000 or entry_price > 10000):
                        continue
                    elif asset == 'SOL' and (entry_price < 10 or entry_price > 1000):
                        continue
                    
                    # Определяем направление
                    direction = 'LONG' if target_price > entry_price else 'SHORT'
                    
                    # Рассчитываем stop loss
                    stop_loss = entry_price * 0.98 if direction == 'LONG' else entry_price * 1.02
                    
                    return {
                        'asset': asset,
                        'direction': direction,
                        'entry_price': entry_price,
                        'target_price': target_price,
                        'stop_loss': stop_loss,
                        'confidence': 70.0,  # Базовая уверенность
                        'is_valid': 1,
                        'source': source,
                        'message_id': message_id,
                        'original_text': text[:200]  # Ограничиваем длину
                    }
                    
                except (ValueError, TypeError):
                    continue
    
    return None

def convert_api_signal(api_data, source):
    """Конвертирует API сигнал в наш формат"""
    try:
        asset = api_data.get('symbol', '').upper()
        if not asset or asset not in ['BTC', 'ETH', 'SOL', 'ADA', 'LINK', 'MATIC']:
            return None
        
        entry_price = float(api_data.get('entry_price', 0))
        target_price = float(api_data.get('target_price', 0))
        
        if entry_price <= 0 or target_price <= 0:
            return None
        
        direction = api_data.get('side', 'LONG').upper()
        if direction not in ['LONG', 'SHORT']:
            direction = 'LONG' if target_price > entry_price else 'SHORT'
        
        stop_loss = float(api_data.get('stop_loss', entry_price * 0.98))
        
        return {
            'asset': asset,
            'direction': direction,
            'entry_price': entry_price,
            'target_price': target_price,
            'stop_loss': stop_loss,
            'confidence': float(api_data.get('confidence', 75.0)),
            'is_valid': 1,
            'source': f"api/{source}",
            'message_id': api_data.get('id', str(datetime.now().timestamp())),
            'original_text': json.dumps(api_data, ensure_ascii=False)
        }
        
    except Exception:
        return None

def save_signal_to_db(signal_data, timestamp):
    """Сохраняет сигнал в БД"""
    conn = sqlite3.connect('workers/signals.db')
    cur = conn.cursor()
    
    signal_id = f"real_{signal_data['asset']}_{signal_data['message_id']}"
    
    cur.execute("""
        INSERT OR REPLACE INTO signals (
            id, asset, direction, entry_price, target_price, stop_loss,
            leverage, timeframe, signal_quality, real_confidence,
            calculated_confidence, channel, message_id, original_text,
            cleaned_text, signal_type, timestamp, extraction_time,
            bybit_available, is_valid, validation_errors,
            risk_reward_ratio, potential_profit, potential_loss
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        signal_id, signal_data['asset'], signal_data['direction'],
        signal_data['entry_price'], signal_data['target_price'], signal_data['stop_loss'],
        1, '1H', 'verified', signal_data['confidence'], signal_data['confidence'],
        signal_data['source'], signal_data['message_id'], signal_data['original_text'],
        signal_data['original_text'], 'real_collected', timestamp.isoformat(),
        datetime.now(timezone.utc).isoformat(), True, signal_data['is_valid'],
        json.dumps([], ensure_ascii=False), 0.0, 0.0, 0.0
    ))
    
    conn.commit()
    conn.close()
    
    print(f"✅ {signal_data['asset']} @ ${signal_data['entry_price']} -> ${signal_data['target_price']} | {signal_data['source']}")

def main():
    """Основная функция"""
    print("🚀 Сбор РЕАЛЬНЫХ данных из Reddit и API")
    print("=" * 50)
    
    # Загружаем данные из .env
    load_env()
    
    total_signals = 0
    
    # Собираем из Reddit
    reddit_signals = collect_from_reddit()
    total_signals += reddit_signals
    
    # Собираем из API
    api_signals = collect_from_crypto_apis()
    total_signals += api_signals
    
    if total_signals > 0:
        print(f"\n🎉 Успешно собрано {total_signals} РЕАЛЬНЫХ сигналов!")
        print("✅ Теперь запустите дашборд: python start_dashboard.py")
    else:
        print("\n❌ Не удалось собрать РЕАЛЬНЫЕ данные")
        print("💡 Попробуйте позже или проверьте настройки API")

if __name__ == '__main__':
    main()
