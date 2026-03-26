"""
Download historical OHLCV candles from Binance and load to PostgreSQL.
No API key required for historical data.

Usage:
    python fetch_market_data.py --symbol BTCUSDT --days 180 --interval 1h
"""
import os
import sys
import logging
import json
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import List, Tuple

import requests
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    os.getenv(
        "BACKEND_DATABASE_URL",
        "postgresql://crypto_analytics_user@localhost:5432/crypto_analytics",
    ),
)

# Binance API endpoints (no auth required for public data)
BINANCE_API_URL = "https://api.binance.com/api/v3"

# Default symbols to load
DEFAULT_SYMBOLS = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT", "ADAUSDT",
                   "DOGEUSDT", "MATICUSDT", "LINKUSDT", "SOLUSDT", "AVAXUSDT"]
DEFAULT_DAYS = 180
DEFAULT_INTERVAL = "1h"  # 1m, 5m, 15m, 1h, 4h, 1d


def get_klines(symbol: str, interval: str = "1h", days: int = 180) -> List[Tuple]:
    """
    Fetch OHLCV candles from Binance.
    Returns list of (timestamp, open, high, low, close, volume)
    """
    try:
        # Calculate start time
        start_time = datetime.now(timezone.utc) - timedelta(days=days)
        start_ts = int(start_time.timestamp() * 1000)

        klines = []
        params = {
            "symbol": symbol,
            "interval": interval,
            "startTime": start_ts,
            "limit": 1000  # Max per request
        }

        logger.info(f"Fetching {symbol} {interval} from {days} days ago...")

        # Binance returns max 1000 candles per request, so fetch in chunks
        current_time = start_ts
        end_time = int(datetime.now(timezone.utc).timestamp() * 1000)

        while current_time < end_time:
            params["startTime"] = current_time
            response = requests.get(
                f"{BINANCE_API_URL}/klines",
                params=params,
                timeout=10
            )
            response.raise_for_status()

            candles = response.json()
            if not candles:
                break

            for candle in candles:
                klines.append((
                    datetime.fromtimestamp(candle[0] / 1000, tz=timezone.utc),
                    Decimal(str(candle[1])),  # open
                    Decimal(str(candle[2])),  # high
                    Decimal(str(candle[3])),  # low
                    Decimal(str(candle[4])),  # close
                    Decimal(str(candle[7])),  # quote asset volume
                ))

            # Set next start time to last candle timestamp + interval
            if len(candles) > 0:
                current_time = candles[-1][0] + 1

            logger.info(f"Fetched {len(klines)} candles so far...")

        logger.info(f"Total fetched: {len(klines)} candles for {symbol}")
        return klines

    except Exception as e:
        logger.error(f"Failed to fetch klines for {symbol}: {e}")
        return []


def load_klines_to_db(symbol: str, interval: str, klines: List[Tuple], source: str = "binance"):
    """Load candles to market_candles table"""
    if not klines:
        logger.warning(f"No klines to load for {symbol}")
        return 0

    try:
        engine = create_engine(DATABASE_URL)
        with engine.connect() as conn:
            # Check existing candles
            check_q = text("""
                SELECT MAX(timestamp) FROM market_candles
                WHERE symbol = :symbol AND timeframe = :interval
            """)
            result = conn.execute(check_q, {"symbol": symbol, "interval": interval}).scalar()
            last_timestamp = result if result else None

            # Filter out existing candles
            new_klines = [k for k in klines if last_timestamp is None or k[0] > last_timestamp]

            if not new_klines:
                logger.info(f"No new candles to load for {symbol} {interval}")
                return 0

            logger.info(f"Loading {len(new_klines)} new candles for {symbol} {interval}...")

            # Batch insert
            batch_size = 500
            inserted = 0
            for i in range(0, len(new_klines), batch_size):
                batch = new_klines[i:i+batch_size]
                insert_q = text("""
                    INSERT INTO market_candles
                    (symbol, timeframe, timestamp, open, high, low, close, volume, source)
                    VALUES (:symbol, :timeframe, :timestamp, :open, :high, :low, :close, :volume, :source)
                    ON CONFLICT (symbol, timeframe, timestamp) DO NOTHING
                """)

                for candle in batch:
                    conn.execute(insert_q, {
                        "symbol": symbol,
                        "timeframe": interval,
                        "timestamp": candle[0],
                        "open": candle[1],
                        "high": candle[2],
                        "low": candle[3],
                        "close": candle[4],
                        "volume": candle[5],
                        "source": source
                    })

                conn.commit()
                inserted += len(batch)
                logger.info(f"Inserted {inserted}/{len(new_klines)} candles")

            return inserted

    except Exception as e:
        logger.error(f"Failed to load candles to DB: {e}")
        return 0


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", default="BTCUSDT", help="Trading pair")
    parser.add_argument("--symbols", nargs="+", default=None, help="Multiple symbols")
    parser.add_argument("--days", type=int, default=DEFAULT_DAYS, help="Days of history")
    parser.add_argument("--interval", default=DEFAULT_INTERVAL, help="Candle interval (1m, 5m, 1h, 4h, 1d)")

    args = parser.parse_args()

    symbols = args.symbols if args.symbols else [args.symbol]

    total_loaded = 0
    for symbol in symbols:
        logger.info(f"\n{'='*60}")
        logger.info(f"Processing {symbol}")
        logger.info(f"{'='*60}")

        klines = get_klines(symbol, args.interval, args.days)
        loaded = load_klines_to_db(symbol, args.interval, klines)
        total_loaded += loaded

    logger.info(f"\n\nTotal candles loaded: {total_loaded}")


if __name__ == "__main__":
    main()
