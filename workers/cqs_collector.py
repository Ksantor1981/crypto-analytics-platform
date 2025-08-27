#!/usr/bin/env python3
"""
Сборщик сигналов из Crypto Quality Signals (открытое API)
- Бесплатный ключ: api_key=FREE
- Фильтры: тип сигналов, биржа, окно времени публикации

Переменные окружения (необязательно):
  CQS_API_KEY       — ключ API (по умолчанию 'FREE')
  CQS_BASE_URL      — базовый URL API (по умолчанию https://api.cryptoqualitysignals.com)
  CQS_EXCHANGE      — биржа (по умолчанию BINANCE)
  CQS_SIGNAL_TYPE   — тип (по умолчанию SHORT TERM)
  CQS_SINCE_MINUTES — окно в минутах (по умолчанию 20)
"""
import os
import json
import sqlite3
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List
import requests

from pathlib import Path
BASE_DIR = Path(__file__).parent
DB_PATH = str(BASE_DIR / 'signals.db')

API_KEY = os.getenv('CQS_API_KEY', 'FREE')
BASE_URL = os.getenv('CQS_BASE_URL', 'https://api.cryptoqualitysignals.com')
DEFAULT_EXCHANGE = os.getenv('CQS_EXCHANGE', 'BINANCE')
DEFAULT_SIGNAL_TYPE = os.getenv('CQS_SIGNAL_TYPE', 'SHORT TERM')
DEFAULT_SINCE_MINUTES = int(os.getenv('CQS_SINCE_MINUTES', '20'))

SESSION = requests.Session()
SESSION.headers.update({
    'Accept': 'application/json',
    'User-Agent': 'CryptoAnalyticsPlatform/1.0 (CQSCollector)'
})


def fetch_cqs_signals(exchange: str, signal_type: str, since_minutes: int) -> List[Dict[str, Any]]:
    """Запрашивает сигналы из CQS API.
    Ожидаемый ответ: список объектов с полями: symbol, side, entry, target, stop, ts (ISO/epoch)
    """
    url = f"{BASE_URL.rstrip('/')}/signals"
    params = {
        'api_key': API_KEY,
        'exchange': exchange,
        'type': signal_type,
        'since_minutes': since_minutes,
    }
    resp = SESSION.get(url, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    if isinstance(data, dict) and 'signals' in data:
        return data['signals']
    if isinstance(data, list):
        return data
    return []


def normalize_symbol_to_asset(symbol: str) -> str:
    sym = (symbol or '').upper()
    for suffix in ('USDT', 'USD', 'PERP', 'USDC', 'BTC', 'ETH'):
        if sym.endswith(suffix):
            sym = sym[: -len(suffix)]
            break
    # Примеры: BTC, ETH, SOL
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
            signal.get('leverage', 1), signal.get('timeframe', '1H'), signal.get('signal_quality', 'verified'),
            signal.get('real_confidence', 0.0), signal.get('calculated_confidence', 0.0),
            signal.get('channel', 'api/CQS'), signal.get('message_id', ''), json.dumps(signal.get('original', {}), ensure_ascii=False),
            json.dumps(signal.get('original', {}), ensure_ascii=False), signal.get('signal_type', 'cqs_api'),
            signal.get('timestamp'), signal.get('extraction_time'), True, signal.get('is_valid', 1),
            json.dumps(signal.get('validation_errors', []), ensure_ascii=False), signal.get('risk_reward_ratio', 0.0),
            signal.get('potential_profit', 0.0), signal.get('potential_loss', 0.0)
        ),
    )


def transform_signal(raw: Dict[str, Any]) -> Dict[str, Any]:
    # Пример сопоставления полей, допускаем разные ключи у провайдера
    symbol = raw.get('symbol') or raw.get('pair') or ''
    asset = normalize_symbol_to_asset(symbol)
    side = (raw.get('side') or raw.get('direction') or '').upper()
    direction = 'LONG' if side in ('BUY', 'LONG') else 'SHORT' if side in ('SELL', 'SHORT') else 'UNKNOWN'
    entry = raw.get('entry') or raw.get('entry_price')
    target = raw.get('target') or raw.get('tp') or raw.get('target_price')
    stop = raw.get('stop') or raw.get('sl') or raw.get('stop_loss')

    # Время
    ts_raw = raw.get('ts') or raw.get('timestamp')
    if isinstance(ts_raw, (int, float)):
        ts = datetime.fromtimestamp(ts_raw, tz=timezone.utc)
    elif isinstance(ts_raw, str):
        try:
            ts = datetime.fromisoformat(ts_raw.replace('Z', '+00:00'))
        except Exception:
            ts = datetime.now(timezone.utc)
    else:
        ts = datetime.now(timezone.utc)

    signal: Dict[str, Any] = {
        'id': f"CQS_{asset}_{raw.get('id') or raw.get('uid') or int(ts.timestamp())}",
        'asset': asset,
        'direction': direction,
        'entry_price': float(entry) if entry not in (None, '') else None,
        'target_price': float(target) if target not in (None, '') else None,
        'stop_loss': float(stop) if stop not in (None, '') else None,
        'timeframe': raw.get('timeframe') or '1H',
        'leverage': int(raw.get('leverage') or 1),
        'signal_quality': 'verified',
        'real_confidence': float(raw.get('confidence') or 0.0),
        'calculated_confidence': float(raw.get('confidence') or 0.0),
        'channel': 'api/CryptoQualitySignals',
        'message_id': str(raw.get('id') or raw.get('uid') or ''),
        'original': raw,
        'signal_type': 'cqs_api',
        'timestamp': ts.isoformat(),
        'extraction_time': datetime.now(timezone.utc).isoformat(),
        'is_valid': 1 if asset != 'UNKNOWN' and direction != 'UNKNOWN' and (entry or target or stop) else 0,
        'validation_errors': [],
        'risk_reward_ratio': 0.0,
        'potential_profit': 0.0,
        'potential_loss': 0.0,
    }
    return signal


def run_collection(exchange: str = DEFAULT_EXCHANGE, signal_type: str = DEFAULT_SIGNAL_TYPE, since_minutes: int = DEFAULT_SINCE_MINUTES) -> int:
    raws = fetch_cqs_signals(exchange, signal_type, since_minutes)
    if not raws:
        print('⚠️ CQS: пустой ответ или нет сигналов')
        return 0
    signals = [transform_signal(r) for r in raws]
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    inserted = 0
    for s in signals:
        try:
            upsert_signal(cur, s)
            inserted += 1
        except Exception as e:
            print(f"❌ Ошибка сохранения {s.get('id')}: {e}")
    conn.commit()
    conn.close()
    print(f"✅ CQS: сохранено {inserted} сигналов ({exchange}, {signal_type}, last {since_minutes}m)")
    return inserted


if __name__ == '__main__':
    run_collection()
