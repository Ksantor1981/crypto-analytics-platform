#!/usr/bin/env python3
"""
Сборщик сигналов из CryptoTradingAPI.io (технические BUY/SELL/HOLD)
Документация: https://cryptotradingapi.io (примерный эндпойнт, адаптируйте при необходимости)

Переменные окружения:
  CTA_API_KEY        — ключ API (обязательно)
  CTA_BASE_URL       — базовый URL API (по умолчанию https://api.cryptotradingapi.io)
  CTA_EXCHANGE       — биржа (по умолчанию BINANCE)
  CTA_SYMBOLS        — список символов через запятую (например BTCUSDT,ETHUSDT)
  CTA_INTERVAL       — таймфрейм (например 1h)
  CTA_LIMIT          — кол-во записей (по умолчанию 50)
"""
import os
import json
import sqlite3
from datetime import datetime, timezone
from typing import Dict, Any, List
import requests
from pathlib import Path

BASE_DIR = Path(__file__).parent
DB_PATH = str(BASE_DIR / 'signals.db')

API_KEY = os.getenv('CTA_API_KEY', '')
BASE_URL = os.getenv('CTA_BASE_URL', 'https://api.cryptotradingapi.io')
EXCHANGE = os.getenv('CTA_EXCHANGE', 'BINANCE')
SYMBOLS = [s.strip() for s in os.getenv('CTA_SYMBOLS', 'BTCUSDT,ETHUSDT,SOLUSDT').split(',') if s.strip()]
INTERVAL = os.getenv('CTA_INTERVAL', '1h')
LIMIT = int(os.getenv('CTA_LIMIT', '50'))

SESSION = requests.Session()
SESSION.headers.update({
    'Accept': 'application/json',
    'Authorization': f'Bearer {API_KEY}' if API_KEY else '',
    'User-Agent': 'CryptoAnalyticsPlatform/1.0 (CTAPICollector)'
})


def fetch_cta_signal(symbol: str) -> Dict[str, Any]:
    """Получает агрегированный сигнал BUY/SELL/HOLD по символу.
    Примерный формат ответа: {symbol, exchange, interval, signal: BUY/SELL/HOLD, price}
    """
    url = f"{BASE_URL.rstrip('/')}/v1/signal"
    params = {
        'symbol': symbol,
        'exchange': EXCHANGE,
        'interval': INTERVAL,
        'limit': LIMIT,
    }
    resp = SESSION.get(url, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()


def normalize_symbol_to_asset(symbol: str) -> str:
    sym = (symbol or '').upper()
    for suffix in ('USDT', 'USD', 'PERP', 'USDC'):
        if sym.endswith(suffix):
            sym = sym[: -len(suffix)]
            break
    return sym or 'UNKNOWN'


def upsert_signal(cur: sqlite3.Cursor, signal: Dict[str, Any]) -> None:
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
            1, signal.get('timeframe', INTERVAL), 'verified',
            signal.get('real_confidence', 0.0), signal.get('calculated_confidence', 0.0),
            'api/CryptoTradingAPI', '', json.dumps(signal.get('original', {}), ensure_ascii=False),
            json.dumps(signal.get('original', {}), ensure_ascii=False), 'cta_api',
            signal.get('timestamp'), signal.get('extraction_time'), True, signal.get('is_valid', 1),
            json.dumps(signal.get('validation_errors', []), ensure_ascii=False), 0.0, 0.0, 0.0
        ),
    )


def transform_signal(raw: Dict[str, Any]) -> Dict[str, Any]:
    symbol = raw.get('symbol') or ''
    asset = normalize_symbol_to_asset(symbol)
    sig = (raw.get('signal') or '').upper()
    direction = 'LONG' if sig == 'BUY' else 'SHORT' if sig == 'SELL' else 'UNKNOWN'
    price = raw.get('price')

    now = datetime.now(timezone.utc).isoformat()
    return {
        'id': f"CTA_{asset}_{int(datetime.now(timezone.utc).timestamp())}",
        'asset': asset,
        'direction': direction,
        'entry_price': float(price) if price not in (None, '') else None,
        'target_price': None,
        'stop_loss': None,
        'timeframe': raw.get('interval') or INTERVAL,
        'real_confidence': 0.0,
        'calculated_confidence': 0.0,
        'original': raw,
        'timestamp': now,
        'extraction_time': now,
        'is_valid': 1 if asset != 'UNKNOWN' and direction != 'UNKNOWN' and price else 0,
        'validation_errors': [],
    }


def run_collection(symbols: List[str] = None) -> int:
    if not API_KEY:
        print('⚠️ CTA: не задан CTA_API_KEY — пропускаю')
        return 0
    use_symbols = symbols or SYMBOLS
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    inserted = 0
    for sym in use_symbols:
        try:
            raw = fetch_cta_signal(sym)
            # Некоторые API возвращают массив — нормализуем
            if isinstance(raw, list):
                for item in raw:
                    s = transform_signal(item)
                    if s['is_valid']:
                        upsert_signal(cur, s)
                        inserted += 1
            else:
                s = transform_signal(raw)
                if s['is_valid']:
                    upsert_signal(cur, s)
                    inserted += 1
        except Exception as e:
            print(f"❌ CTA ошибка {sym}: {e}")
    conn.commit()
    conn.close()
    print(f"✅ CTA: сохранено {inserted} сигналов ({EXCHANGE}, {INTERVAL})")
    return inserted


if __name__ == '__main__':
    run_collection()
