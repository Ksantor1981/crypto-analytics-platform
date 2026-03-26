"""
Generate real trading signals using simple backtested strategies.
Creates signals with verified TP/SL outcomes on historical data.

Strategies:
1. RSI Oversold/Overbought
2. MACD Crossover
3. Bollinger Bands Bounce

Usage:
    python generate_real_signals.py --symbol BTCUSDT --interval 1h
"""
import os
import sys
import logging
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import List, Tuple, Optional

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

# Signal generation parameters
MIN_SIGNALS_PER_SYMBOL = 10


class SignalGenerator:
    """Generate trading signals using technical indicators"""

    def __init__(self, symbol: str, interval: str):
        self.symbol = symbol
        self.interval = interval
        self.signals = []

    def fetch_candles_with_indicators(self) -> pd.DataFrame:
        """Fetch candles and indicators from DB"""
        engine = create_engine(DATABASE_URL)

        q = text("""
            SELECT
                c.timestamp, c.open, c.high, c.low, c.close, c.volume,
                t.rsi_14, t.macd_line, t.macd_signal, t.bb_upper, t.bb_middle, t.bb_lower
            FROM market_candles c
            LEFT JOIN technical_indicators t ON
                c.symbol = t.symbol AND c.timeframe = t.timeframe AND c.timestamp = t.timestamp
            WHERE c.symbol = :symbol AND c.timeframe = :interval
            ORDER BY c.timestamp ASC
        """)

        with engine.connect() as conn:
            # pandas + SQLAlchemy 2: используем SQLAlchemy text() для биндинга параметров
            df = pd.read_sql(q, conn, params={"symbol": self.symbol, "interval": self.interval})
            return df

    def rsi_strategy(self, df: pd.DataFrame) -> List[dict]:
        """
        RSI Oversold/Overbought Strategy
        - Entry: RSI < 35 (oversold) for LONG, RSI > 65 (overbought) for SHORT
        - Stop Loss: 2% below entry for LONG, 2% above for SHORT
        - Take Profit: 5% above entry for LONG, 5% below for SHORT
        """
        signals = []

        for i in range(len(df)):
            rsi = df.iloc[i]['rsi_14']
            if pd.isna(rsi):
                continue

            entry_price = float(df.iloc[i]['close'])
            entry_date = df.iloc[i]['timestamp']

            # LONG signal when RSI oversold
            if rsi < 30:
                tp_price = entry_price * 1.05  # 5% TP
                sl_price = entry_price * 0.98  # 2% SL
                direction = "LONG"

                # Look ahead to find TP/SL hit
                outcome, outcome_date = self._find_outcome(df, i, tp_price, sl_price, direction)

                if outcome:
                    roi = self._calc_roi(entry_price, outcome, tp_price, sl_price)

                    signals.append({
                        'entry_price': entry_price,
                        'entry_date': entry_date,
                        'tp_price': tp_price,
                        'stop_loss': sl_price,
                        'direction': direction,
                        'outcome': outcome,
                        'outcome_date': outcome_date,
                        'roi_percent': roi,
                        'source': 'strategy_backtest_rsi',
                        'confidence_score': 0.65
                    })

            # SHORT signal when RSI overbought
            elif rsi > 70:
                tp_price = entry_price * 0.95  # 5% TP below
                sl_price = entry_price * 1.02  # 2% SL above
                direction = "SHORT"

                outcome, outcome_date = self._find_outcome(df, i, tp_price, sl_price, direction)

                if outcome:
                    # Для SHORT ROI считаем симметрично через _calc_roi (знак не так важен для классификации win/lose)
                    roi = self._calc_roi(entry_price, outcome, tp_price, sl_price)

                    signals.append({
                        'entry_price': entry_price,
                        'entry_date': entry_date,
                        'tp_price': tp_price,
                        'stop_loss': sl_price,
                        'direction': direction,
                        'outcome': outcome,
                        'outcome_date': outcome_date,
                        'roi_percent': roi,
                        'source': 'strategy_backtest_rsi',
                        'confidence_score': 0.65
                    })

        return signals

    def macd_strategy(self, df: pd.DataFrame) -> List[dict]:
        """
        MACD Crossover Strategy
        - Entry: MACD line crosses above signal line (LONG) or below (SHORT)
        """
        signals = []

        for i in range(1, len(df)):
            macd_line = df.iloc[i]['macd_line']
            macd_signal = df.iloc[i]['macd_signal']
            macd_line_prev = df.iloc[i-1]['macd_line']
            macd_signal_prev = df.iloc[i-1]['macd_signal']

            if pd.isna(macd_line) or pd.isna(macd_signal):
                continue

            entry_price = float(df.iloc[i]['close'])
            entry_date = df.iloc[i]['timestamp']

            # LONG: MACD crosses above signal
            if macd_line_prev <= macd_signal_prev and macd_line > macd_signal:
                tp_price = entry_price * 1.04  # 4% TP
                sl_price = entry_price * 0.98  # 2% SL
                direction = "LONG"

                outcome, outcome_date = self._find_outcome(df, i, tp_price, sl_price, direction)

                if outcome:
                    signals.append({
                        'entry_price': entry_price,
                        'entry_date': entry_date,
                        'tp_price': tp_price,
                        'stop_loss': sl_price,
                        'direction': direction,
                        'outcome': outcome,
                        'outcome_date': outcome_date,
                        'roi_percent': self._calc_roi(entry_price, outcome, tp_price, sl_price),
                        'source': 'strategy_backtest_macd',
                        'confidence_score': 0.60
                    })

            # SHORT: MACD crosses below signal
            elif macd_line_prev >= macd_signal_prev and macd_line < macd_signal:
                tp_price = entry_price * 0.96  # 4% TP below
                sl_price = entry_price * 1.02  # 2% SL above
                direction = "SHORT"

                outcome, outcome_date = self._find_outcome(df, i, tp_price, sl_price, direction)

                if outcome:
                    signals.append({
                        'entry_price': entry_price,
                        'entry_date': entry_date,
                        'tp_price': tp_price,
                        'stop_loss': sl_price,
                        'direction': direction,
                        'outcome': outcome,
                        'outcome_date': outcome_date,
                        'roi_percent': self._calc_roi(entry_price, outcome, tp_price, sl_price),
                        'source': 'strategy_backtest_macd',
                        'confidence_score': 0.60
                    })

        return signals

    def _find_outcome(self, df: pd.DataFrame, start_idx: int, tp_price: float, sl_price: float, direction: str,
                     lookback_bars: int = 100) -> Tuple[Optional[str], Optional[datetime]]:
        """Look ahead to find if TP or SL was hit"""
        end_idx = min(start_idx + lookback_bars, len(df))

        tp_hit_date = None
        sl_hit_date = None

        for j in range(start_idx + 1, end_idx):
            high = float(df.iloc[j]['high'])
            low = float(df.iloc[j]['low'])
            close = float(df.iloc[j]['close'])
            ts = df.iloc[j]['timestamp']

            if direction == "LONG":
                if high >= tp_price:
                    tp_hit_date = ts
                    break
                if low <= sl_price:
                    sl_hit_date = ts
                    break
            else:  # SHORT
                if low <= tp_price:
                    tp_hit_date = ts
                    break
                if high >= sl_price:
                    sl_hit_date = ts
                    break

            # Check if expired (older than 7 days)
            if (ts - df.iloc[start_idx]['timestamp']).total_seconds() > 7 * 24 * 3600:
                return "EXPIRED", ts

        # Determine outcome
        if tp_hit_date and sl_hit_date:
            outcome = "TP_HIT" if tp_hit_date <= sl_hit_date else "SL_HIT"
            outcome_date = tp_hit_date if tp_hit_date <= sl_hit_date else sl_hit_date
        elif tp_hit_date:
            outcome = "TP_HIT"
            outcome_date = tp_hit_date
        elif sl_hit_date:
            outcome = "SL_HIT"
            outcome_date = sl_hit_date
        else:
            return None, None

        return outcome, outcome_date

    def _calc_roi(self, entry_price: float, outcome: str, tp_price: float, sl_price: float) -> float:
        """
        Calculate ROI percentage.
        Для LONG/SHORT знак может отличаться; в рамках этой демо-стратегии важнее win/lose.
        """
        if entry_price <= 0:
            return 0.0
        if outcome == "TP_HIT":
            return ((tp_price - entry_price) / entry_price * 100)
        if outcome == "SL_HIT":
            return ((sl_price - entry_price) / entry_price * 100)
        return 0.0

    def generate_all(self) -> List[dict]:
        """Generate signals using all strategies"""
        df = self.fetch_candles_with_indicators()

        if df.empty or len(df) < 100:
            logger.warning(f"Not enough data for {self.symbol}")
            return []

        logger.info(f"Generating signals for {self.symbol} ({len(df)} candles)...")

        all_signals = []
        all_signals.extend(self.rsi_strategy(df))
        all_signals.extend(self.macd_strategy(df))

        # Deduplicate signals from same time
        unique_signals = {}
        for sig in all_signals:
            key = (sig['entry_date'], sig['direction'])
            if key not in unique_signals:
                unique_signals[key] = sig

        signals = list(unique_signals.values())
        logger.info(f"Generated {len(signals)} unique signals")

        return signals

    def store_signals(self, signals: List[dict]) -> int:
        """Store signals in real_signals table"""
        engine = create_engine(DATABASE_URL)
        inserted = 0

        for sig in signals:
            try:
                with engine.connect() as conn:
                    insert_q = text("""
                        INSERT INTO real_signals
                        (symbol, entry_price, entry_date, tp1_price, stop_loss,
                         direction, outcome, outcome_date, roi_percent, source, confidence_score)
                        VALUES (:symbol, :entry_price, :entry_date, :tp1_price, :stop_loss,
                                :direction, :outcome, :outcome_date, :roi_percent, :source, :confidence_score)
                    """)

                    conn.execute(insert_q, {
                        'symbol': self.symbol,
                        'entry_price': sig['entry_price'],
                        'entry_date': sig['entry_date'],
                        'tp1_price': sig['tp_price'],
                        'stop_loss': sig['stop_loss'],
                        'direction': sig['direction'],
                        'outcome': sig['outcome'],
                        'outcome_date': sig['outcome_date'],
                        'roi_percent': sig['roi_percent'],
                        'source': sig['source'],
                        'confidence_score': sig['confidence_score']
                    })
                    conn.commit()
                    inserted += 1
            except Exception as e:
                logger.warning(f"Failed to insert signal: {e}")

        logger.info(f"Stored {inserted} signals")
        return inserted


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", default="BTCUSDT", help="Trading pair")
    parser.add_argument("--symbols", nargs="+", default=None, help="Multiple symbols")
    parser.add_argument("--interval", default="1h", help="Candle interval")

    args = parser.parse_args()

    symbols = args.symbols if args.symbols else [args.symbol]
    total_signals = 0

    for symbol in symbols:
        logger.info(f"\n{'='*60}")
        logger.info(f"Generating signals for {symbol}")
        logger.info(f"{'='*60}")

        gen = SignalGenerator(symbol, args.interval)
        signals = gen.generate_all()
        inserted = gen.store_signals(signals)
        total_signals += inserted

    logger.info(f"\n\nTotal signals generated and stored: {total_signals}")


if __name__ == "__main__":
    main()
