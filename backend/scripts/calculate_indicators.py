"""
Calculate technical indicators (RSI, MACD, Bollinger Bands, ATR, Stochastic, ADX)
from market_candles and store in technical_indicators table.

Usage:
    python calculate_indicators.py --symbol BTCUSDT --interval 1h
"""
import os
import sys
import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, List, Tuple

import numpy as np
from sqlalchemy import create_engine, text
import pandas as pd

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    os.getenv(
        "BACKEND_DATABASE_URL",
        "postgresql://crypto_analytics_user@localhost:5432/crypto_analytics",
    ),
)


class TechnicalIndicators:
    """Calculate various technical indicators"""

    @staticmethod
    def rsi(prices: np.ndarray, period: int = 14) -> np.ndarray:
        """Calculate Relative Strength Index"""
        if len(prices) < period + 1:
            return np.full(len(prices), np.nan)

        deltas = np.diff(prices)
        seed = deltas[:period+1]
        up = seed[seed >= 0].sum() / period
        down = -seed[seed < 0].sum() / period
        rs = up / down if down != 0 else 0
        rsi = np.zeros_like(prices, dtype=float)
        rsi[:period] = 100.0 - 100.0 / (1.0 + rs)

        for i in range(period, len(prices)):
            delta = deltas[i-1]
            if delta > 0:
                upval = delta
                downval = 0.0
            else:
                upval = 0.0
                downval = -delta

            up = (up * (period - 1) + upval) / period
            down = (down * (period - 1) + downval) / period

            rs = up / down if down != 0 else 0
            rsi[i] = 100.0 - 100.0 / (1.0 + rs)

        return rsi

    @staticmethod
    def macd(prices: np.ndarray, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Calculate MACD (Moving Average Convergence Divergence)"""
        if len(prices) < slow + signal - 1:
            return (np.full(len(prices), np.nan), np.full(len(prices), np.nan), np.full(len(prices), np.nan))

        ema_fast = pd.Series(prices).ewm(span=fast, adjust=False).mean().values
        ema_slow = pd.Series(prices).ewm(span=slow, adjust=False).mean().values

        macd_line = ema_fast - ema_slow
        signal_line = pd.Series(macd_line).ewm(span=signal, adjust=False).mean().values
        histogram = macd_line - signal_line

        return macd_line, signal_line, histogram

    @staticmethod
    def bollinger_bands(prices: np.ndarray, period: int = 20, std_dev: float = 2.0) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Calculate Bollinger Bands"""
        if len(prices) < period:
            return (np.full(len(prices), np.nan), np.full(len(prices), np.nan), np.full(len(prices), np.nan))

        sma = pd.Series(prices).rolling(window=period).mean().values
        std = pd.Series(prices).rolling(window=period).std().values

        upper_band = sma + (std_dev * std)
        lower_band = sma - (std_dev * std)

        return upper_band, sma, lower_band

    @staticmethod
    def atr(high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int = 14) -> np.ndarray:
        """Calculate Average True Range"""
        if len(high) < period + 1:
            return np.full(len(high), np.nan)

        tr1 = high - low
        tr2 = np.abs(high - np.roll(close, 1))
        tr3 = np.abs(low - np.roll(close, 1))
        tr = np.maximum(tr1, np.maximum(tr2, tr3))

        atr_values = np.zeros(len(tr))
        atr_values[period-1] = np.mean(tr[:period])
        for i in range(period, len(tr)):
            atr_values[i] = (atr_values[i-1] * (period - 1) + tr[i]) / period

        return atr_values

    @staticmethod
    def stochastic(high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int = 14, smooth_k: int = 3, smooth_d: int = 3) -> Tuple[np.ndarray, np.ndarray]:
        """Calculate Stochastic Oscillator"""
        if len(close) < period:
            return (np.full(len(close), np.nan), np.full(len(close), np.nan))

        lowest_low = pd.Series(low).rolling(window=period).min().values
        highest_high = pd.Series(high).rolling(window=period).max().values

        k_fast = 100 * (close - lowest_low) / (highest_high - lowest_low + 1e-10)
        k = pd.Series(k_fast).rolling(window=smooth_k).mean().values
        d = pd.Series(k).rolling(window=smooth_d).mean().values

        return k, d


def fetch_candles(symbol: str, interval: str) -> Tuple[List[datetime], np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Fetch candles from market_candles table"""
    engine = create_engine(DATABASE_URL)

    with engine.connect() as conn:
        q = text("""
            SELECT timestamp, open, high, low, close, volume
            FROM market_candles
            WHERE symbol = :symbol AND timeframe = :interval
            ORDER BY timestamp ASC
        """)
        rows = conn.execute(q, {"symbol": symbol, "interval": interval}).fetchall()

    if not rows:
        return [], np.array([]), np.array([]), np.array([]), np.array([])

    timestamps = [row[0] for row in rows]
    opens = np.array([float(row[1]) for row in rows])
    highs = np.array([float(row[2]) for row in rows])
    lows = np.array([float(row[3]) for row in rows])
    closes = np.array([float(row[4]) for row in rows])

    return timestamps, opens, highs, lows, closes


def calculate_and_store(symbol: str, interval: str):
    """Calculate indicators for symbol and store in DB"""
    logger.info(f"Fetching candles for {symbol} {interval}...")
    timestamps, opens, highs, lows, closes = fetch_candles(symbol, interval)

    if len(timestamps) == 0:
        logger.warning(f"No candles found for {symbol} {interval}")
        return 0

    logger.info(f"Calculating indicators for {len(timestamps)} candles...")

    # Calculate indicators
    rsi_values = TechnicalIndicators.rsi(closes, period=14)
    macd_line, macd_signal, macd_hist = TechnicalIndicators.macd(closes, fast=12, slow=26, signal=9)
    bb_upper, bb_middle, bb_lower = TechnicalIndicators.bollinger_bands(closes, period=20, std_dev=2.0)
    atr_values = TechnicalIndicators.atr(highs, lows, closes, period=14)
    stoch_k, stoch_d = TechnicalIndicators.stochastic(highs, lows, closes, period=14, smooth_k=3, smooth_d=3)
    adx_values = np.full(len(closes), np.nan)  # ADX is complex, skip for now

    # Store in DB
    engine = create_engine(DATABASE_URL)
    inserted = 0

    logger.info("Storing indicators in DB...")
    for i, ts in enumerate(timestamps):
        try:
            with engine.connect() as conn:
                insert_q = text("""
                    INSERT INTO technical_indicators
                    (symbol, timeframe, timestamp, rsi_14, macd_line, macd_signal, macd_histogram,
                     bb_upper, bb_middle, bb_lower, atr_14, stoch_k, stoch_d)
                    VALUES (:symbol, :timeframe, :timestamp, :rsi_14, :macd_line, :macd_signal, :macd_histogram,
                            :bb_upper, :bb_middle, :bb_lower, :atr_14, :stoch_k, :stoch_d)
                    ON CONFLICT (symbol, timeframe, timestamp) DO NOTHING
                """)

                conn.execute(insert_q, {
                    "symbol": symbol,
                    "timeframe": interval,
                    "timestamp": ts,
                    "rsi_14": float(rsi_values[i]) if not np.isnan(rsi_values[i]) else None,
                    "macd_line": float(macd_line[i]) if not np.isnan(macd_line[i]) else None,
                    "macd_signal": float(macd_signal[i]) if not np.isnan(macd_signal[i]) else None,
                    "macd_histogram": float(macd_hist[i]) if not np.isnan(macd_hist[i]) else None,
                    "bb_upper": float(bb_upper[i]) if not np.isnan(bb_upper[i]) else None,
                    "bb_middle": float(bb_middle[i]) if not np.isnan(bb_middle[i]) else None,
                    "bb_lower": float(bb_lower[i]) if not np.isnan(bb_lower[i]) else None,
                    "atr_14": float(atr_values[i]) if not np.isnan(atr_values[i]) else None,
                    "stoch_k": float(stoch_k[i]) if not np.isnan(stoch_k[i]) else None,
                    "stoch_d": float(stoch_d[i]) if not np.isnan(stoch_d[i]) else None,
                })
                conn.commit()
                inserted += 1

                if (i + 1) % 100 == 0:
                    logger.info(f"Processed {i+1}/{len(timestamps)} candles")
        except Exception as e:
            logger.warning(f"Failed to insert indicator for {ts}: {e}")

    logger.info(f"Stored indicators for {inserted} candles")
    return inserted


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", default="BTCUSDT", help="Trading pair")
    parser.add_argument("--symbols", nargs="+", default=None, help="Multiple symbols")
    parser.add_argument("--interval", default="1h", help="Candle interval")

    args = parser.parse_args()

    symbols = args.symbols if args.symbols else [args.symbol]

    for symbol in symbols:
        logger.info(f"\nCalculating indicators for {symbol} {args.interval}...")
        calculate_and_store(symbol, args.interval)


if __name__ == "__main__":
    main()
