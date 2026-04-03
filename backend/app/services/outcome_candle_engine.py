"""
Расчёт canonical SignalOutcome по OHLC-свечам (фаза 11).

Семантика v0: MARKET_OUTCOME_POLICY.md + engine_version в policy_ref.
Источник свечей: сначала market_candles (если таблица есть), иначе CoinGecko /ohlc.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, List, Optional, Sequence, Tuple

from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

POLICY_REF_V0 = "MARKET_OUTCOME_POLICY.md#candle_engine_v0.2"
ENGINE_VERSION = "candle_engine_v0.2"

try:
    from app.services.price_validator import COINGECKO_IDS
except ImportError:  # pragma: no cover
    COINGECKO_IDS = {}


@dataclass(frozen=True)
class OhlcCandle:
    ts_open: datetime  # UTC, начало периода свечи
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal


def timeframe_to_delta(timeframe: str) -> timedelta:
    tf = (timeframe or "1h").strip().lower()
    if tf == "1h":
        return timedelta(hours=1)
    if tf == "4h":
        return timedelta(hours=4)
    if tf == "1d" or tf == "1D":
        return timedelta(days=1)
    return timedelta(hours=1)


def _asset_base(asset: str) -> str:
    if not asset:
        return ""
    a = asset.strip().upper()
    for sep in ("/USDT", "/USD", "-USDT", "-USD"):
        if sep in a:
            a = a.split(sep)[0]
            break
    if a.endswith("USDT") and len(a) > 4:
        a = a[:-4]
    return a


def _asset_to_db_symbol(asset: str) -> Optional[str]:
    base = _asset_base(asset)
    if not base:
        return None
    return f"{base}USDT"


def _normalize_ts(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def list_candles_from_db(
    db: Session,
    *,
    asset: str,
    timeframe: str,
    from_ts: datetime,
    to_ts: datetime,
) -> Tuple[List[OhlcCandle], Optional[str]]:
    symbol = _asset_to_db_symbol(asset)
    if not symbol:
        return [], None
    try:
        q = text(
            """
            SELECT timestamp, open, high, low, close
            FROM market_candles
            WHERE symbol = :symbol
              AND timeframe = :tf
              AND timestamp >= :from_ts
              AND timestamp <= :to_ts
            ORDER BY timestamp ASC
            """
        )
        rows = db.execute(
            q,
            {"symbol": symbol, "tf": timeframe, "from_ts": from_ts, "to_ts": to_ts},
        ).fetchall()
        if not rows:
            return [], None
        out: List[OhlcCandle] = []
        for r in rows:
            ts = r[0]
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            else:
                ts = ts.astimezone(timezone.utc)
            out.append(
                OhlcCandle(
                    ts_open=ts,
                    open=Decimal(str(r[1])),
                    high=Decimal(str(r[2])),
                    low=Decimal(str(r[3])),
                    close=Decimal(str(r[4])),
                )
            )
        return out, f"db.market_candles.{timeframe}"
    except Exception as e:
        logger.debug("market_candles read skipped: %s", e)
        return [], None


def _coingecko_days_param(lookahead_days: int) -> int:
    d = max(1, int(lookahead_days))
    if d <= 1:
        return 1
    if d <= 7:
        return 7
    if d <= 14:
        return 14
    if d <= 30:
        return 30
    return 90


def fetch_coingecko_ohlc_sync(
    asset: str,
    *,
    lookahead_days: int,
) -> Tuple[List[OhlcCandle], Optional[str]]:
    base = _asset_base(asset)
    cg_id = COINGECKO_IDS.get(base)
    if not cg_id:
        return [], None
    days = _coingecko_days_param(lookahead_days)
    try:
        import httpx

        r = httpx.get(
            f"https://api.coingecko.com/api/v3/coins/{cg_id}/ohlc",
            params={"vs_currency": "usd", "days": days},
            timeout=25.0,
        )
        if r.status_code != 200:
            logger.warning("CoinGecko ohlc HTTP %s for %s", r.status_code, base)
            return [], None
        raw = r.json()
        if not isinstance(raw, list):
            return [], None
        out: List[OhlcCandle] = []
        for row in raw:
            if not row or len(row) < 5:
                continue
            ts_ms = int(row[0])
            ts = datetime.fromtimestamp(ts_ms / 1000.0, tz=timezone.utc)
            out.append(
                OhlcCandle(
                    ts_open=ts,
                    open=Decimal(str(row[1])),
                    high=Decimal(str(row[2])),
                    low=Decimal(str(row[3])),
                    close=Decimal(str(row[4])),
                )
            )
        return out, f"coingecko.ohlc.days_{days}"
    except Exception as e:
        logger.warning("CoinGecko ohlc error for %s: %s", base, e)
        return [], None


def load_candles_for_window(
    db: Session,
    *,
    asset: str,
    signal_time: datetime,
    lookahead_days: int,
    timeframe: str,
) -> Tuple[List[OhlcCandle], Optional[str]]:
    st = _normalize_ts(signal_time)
    end = st + timedelta(days=max(1, lookahead_days))
    candles, src = list_candles_from_db(db, asset=asset, timeframe=timeframe, from_ts=st, to_ts=end)
    if candles:
        return candles, src
    all_cg, src_cg = fetch_coingecko_ohlc_sync(asset, lookahead_days=max(lookahead_days, 14))
    filtered = [c for c in all_cg if c.ts_open <= end and c.ts_open + timeframe_to_delta(timeframe) >= st - timedelta(days=1)]
    filtered.sort(key=lambda x: x.ts_open)
    if filtered:
        return filtered, src_cg
    return [], None


def _find_candle_index(signal_time: datetime, candles: Sequence[OhlcCandle], delta: timedelta) -> int:
    st = _normalize_ts(signal_time)
    for i, c in enumerate(candles):
        if c.ts_open <= st < c.ts_open + delta:
            return i
    for i, c in enumerate(candles):
        if c.ts_open >= st:
            return i
    return -1


def _midpoint_entry(ns) -> Decimal:
    lo = ns.entry_zone_low
    hi = ns.entry_zone_high
    if lo is not None and hi is not None:
        return (Decimal(str(lo)) + Decimal(str(hi))) / Decimal(2)
    return Decimal(str(ns.entry_price))


def _sanitize_sl(direction: str, entry: Decimal, sl: Optional[Decimal]) -> Optional[Decimal]:
    d = (direction or "").upper()
    if sl is None:
        return None
    if d == "LONG" and sl > entry:
        return None
    if d == "SHORT" and sl < entry:
        return None
    return sl


def mop_reference_price(candle: OhlcCandle, mode: str) -> Decimal:
    """Цена «на публикации» для market_on_publish (свеча, содержащая signal_time)."""
    m = (mode or "close").strip().lower()
    if m == "open":
        return candle.open
    if m == "hl2":
        return (candle.high + candle.low) / Decimal(2)
    if m == "ohlc4":
        return (candle.open + candle.high + candle.low + candle.close) / Decimal(4)
    return candle.close


def _mfe_mae_long(entry: Decimal, candles: Sequence[OhlcCandle], start_i: int, end_i: int) -> Tuple[Decimal, Decimal]:
    mfe = Decimal(0)
    mae = Decimal(0)
    for i in range(start_i, min(end_i + 1, len(candles))):
        c = candles[i]
        up = c.high - entry
        down = entry - c.low
        if up > mfe:
            mfe = up
        if down > mae:
            mae = down
    return mfe, mae


def _mfe_mae_short(entry: Decimal, candles: Sequence[OhlcCandle], start_i: int, end_i: int) -> Tuple[Decimal, Decimal]:
    mfe = Decimal(0)
    mae = Decimal(0)
    for i in range(start_i, min(end_i + 1, len(candles))):
        c = candles[i]
        up = entry - c.low
        down = c.high - entry
        if up > mfe:
            mfe = up
        if down > mae:
            mae = down
    return mfe, mae


def _exit_scan_long(
    candles: Sequence[OhlcCandle],
    exit_start: int,
    tp_levels: List[Decimal],
    sl: Optional[Decimal],
    sl_first: bool,
) -> Tuple[bool, List[dict], int, int]:
    """sl_hit, tp_hits, outcome_bar_index, tp_idx (сколько уровней закрыто)."""
    last_i = len(candles) - 1
    outcome_i = last_i
    tp_hits: List[dict] = []
    tp_idx = 0
    sl_hit = False
    for i in range(exit_start, len(candles)):
        c = candles[i]
        if sl_first:
            if sl is not None and c.low <= sl:
                sl_hit = True
                outcome_i = i
                break
            while tp_idx < len(tp_levels) and c.high >= tp_levels[tp_idx]:
                tp_hits.append({"level": tp_idx + 1, "price": str(tp_levels[tp_idx])})
                tp_idx += 1
            if sl is not None and c.low <= sl:
                sl_hit = True
                outcome_i = i
                break
        else:
            while tp_idx < len(tp_levels) and c.high >= tp_levels[tp_idx]:
                tp_hits.append({"level": tp_idx + 1, "price": str(tp_levels[tp_idx])})
                tp_idx += 1
            if sl is not None and c.low <= sl:
                sl_hit = True
                outcome_i = i
                break
        if tp_levels and tp_idx >= len(tp_levels):
            outcome_i = i
            break
    return sl_hit, tp_hits, outcome_i, tp_idx


def _exit_scan_short(
    candles: Sequence[OhlcCandle],
    exit_start: int,
    tp_levels: List[Decimal],
    sl: Optional[Decimal],
    sl_first: bool,
) -> Tuple[bool, List[dict], int, int]:
    last_i = len(candles) - 1
    outcome_i = last_i
    tp_hits: List[dict] = []
    tp_idx = 0
    sl_hit = False
    for i in range(exit_start, len(candles)):
        c = candles[i]
        if sl_first:
            if sl is not None and c.high >= sl:
                sl_hit = True
                outcome_i = i
                break
            while tp_idx < len(tp_levels) and c.low <= tp_levels[tp_idx]:
                tp_hits.append({"level": tp_idx + 1, "price": str(tp_levels[tp_idx])})
                tp_idx += 1
            if sl is not None and c.high >= sl:
                sl_hit = True
                outcome_i = i
                break
        else:
            while tp_idx < len(tp_levels) and c.low <= tp_levels[tp_idx]:
                tp_hits.append({"level": tp_idx + 1, "price": str(tp_levels[tp_idx])})
                tp_idx += 1
            if sl is not None and c.high >= sl:
                sl_hit = True
                outcome_i = i
                break
        if tp_levels and tp_idx >= len(tp_levels):
            outcome_i = i
            break
    return sl_hit, tp_hits, outcome_i, tp_idx


def compute_outcome_from_candles(
    *,
    model_key: str,
    direction: str,
    entry_price: Decimal,
    take_profit: Optional[Decimal],
    stop_loss: Optional[Decimal],
    signal_time: datetime,
    candles: Sequence[OhlcCandle],
    timeframe: str,
    midpoint_price: Optional[Decimal] = None,
    take_profit_levels: Optional[Sequence[Decimal]] = None,
    mop_reference: str = "close",
    sl_before_tp_same_bar: bool = True,
) -> Tuple[str, dict[str, Any]]:
    """
    Возвращает (outcome_status, fields) для записи в SignalOutcome.
    outcome_status: COMPLETE | DATA_INCOMPLETE | ERROR

    take_profit_levels — приоритетнее скаляра take_profit; уровни уже отфильтрованы по направлению.
    """
    if not candles:
        return "DATA_INCOMPLETE", {
            "entry_reached": None,
            "error_detail": {"code": "no_candles", "message": "Нет свечей в окне"},
            "policy_ref": POLICY_REF_V0,
            "market_data_version": None,
        }

    delta = timeframe_to_delta(timeframe)
    st = _normalize_ts(signal_time)
    mk = (model_key or "").strip()
    d = (direction or "").upper()

    if take_profit_levels is not None:
        tp_levels = [Decimal(str(x)) for x in take_profit_levels]
    elif take_profit is not None:
        tp_levels = [Decimal(str(take_profit))]
    else:
        tp_levels = []

    sl = _sanitize_sl(d, entry_price, stop_loss)

    idx0 = _find_candle_index(st, candles, delta)
    if idx0 < 0:
        return "DATA_INCOMPLETE", {
            "entry_reached": False,
            "error_detail": {"code": "signal_after_candles", "message": "Сигнал позже доступных свечей"},
            "policy_ref": POLICY_REF_V0,
            "market_data_version": ENGINE_VERSION,
        }

    entry_idx: int
    entry_fill: Decimal
    exit_start: int

    if mk == "market_on_publish":
        entry_idx = idx0
        entry_fill = mop_reference_price(candles[entry_idx], mop_reference)
        exit_start = entry_idx + 1
        entry_reached = True
    elif mk == "first_touch_limit":
        entry_lvl = entry_price
        entry_idx = -1
        for i in range(idx0, len(candles)):
            c = candles[i]
            if d == "LONG" and c.low <= entry_lvl <= c.high:
                entry_idx = i
                break
            if d == "LONG" and c.low <= entry_lvl:
                entry_idx = i
                break
            if d == "SHORT" and c.low <= entry_lvl <= c.high:
                entry_idx = i
                break
            if d == "SHORT" and c.high >= entry_lvl:
                entry_idx = i
                break
        if entry_idx < 0:
            return "DATA_INCOMPLETE", {
                "entry_reached": False,
                "error_detail": {"code": "entry_not_touched", "message": "Лимитный вход не касался свечей в окне"},
                "policy_ref": POLICY_REF_V0,
                "market_data_version": ENGINE_VERSION,
            }
        entry_fill = entry_lvl
        exit_start = entry_idx
        entry_reached = True
    elif mk == "midpoint_entry":
        mid = midpoint_price if midpoint_price is not None else entry_price
        entry_lvl = mid
        entry_idx = -1
        for i in range(idx0, len(candles)):
            c = candles[i]
            if d == "LONG" and c.low <= entry_lvl <= c.high:
                entry_idx = i
                break
            if d == "LONG" and c.low <= entry_lvl:
                entry_idx = i
                break
            if d == "SHORT" and c.high >= entry_lvl:
                entry_idx = i
                break
            if d == "SHORT" and c.low <= entry_lvl <= c.high:
                entry_idx = i
                break
        if entry_idx < 0:
            return "DATA_INCOMPLETE", {
                "entry_reached": False,
                "error_detail": {"code": "midpoint_not_touched", "message": "Midpoint не касался свечей в окне"},
                "policy_ref": POLICY_REF_V0,
                "market_data_version": ENGINE_VERSION,
            }
        entry_fill = entry_lvl
        exit_start = entry_idx
        entry_reached = True
    else:
        return "ERROR", {
            "error_detail": {"code": "unknown_model_key", "message": mk},
            "policy_ref": POLICY_REF_V0,
            "market_data_version": ENGINE_VERSION,
        }

    if exit_start >= len(candles):
        t_entry = int((candles[entry_idx].ts_open + delta - st).total_seconds())
        return "COMPLETE", {
            "outcome_status": "COMPLETE",
            "entry_reached": entry_reached,
            "entry_fill_price": entry_fill,
            "tp_hits": [],
            "sl_hit": False,
            "expiry_hit": True,
            "mfe": Decimal(0),
            "mae": Decimal(0),
            "time_to_entry_sec": max(0, t_entry),
            "time_to_outcome_sec": max(0, t_entry),
            "policy_ref": POLICY_REF_V0,
            "market_data_version": ENGINE_VERSION,
        }

    if d == "LONG":
        sl_hit, tp_hits, outcome_i, tp_idx = _exit_scan_long(
            candles, exit_start, tp_levels, sl, sl_before_tp_same_bar
        )
        mfe, mae = _mfe_mae_long(entry_fill, candles, exit_start, outcome_i)
    elif d == "SHORT":
        sl_hit, tp_hits, outcome_i, tp_idx = _exit_scan_short(
            candles, exit_start, tp_levels, sl, sl_before_tp_same_bar
        )
        mfe, mae = _mfe_mae_short(entry_fill, candles, exit_start, outcome_i)
    else:
        return "ERROR", {
            "error_detail": {"code": "unknown_direction", "message": d},
            "policy_ref": POLICY_REF_V0,
            "market_data_version": ENGINE_VERSION,
        }

    if tp_levels:
        expiry_hit = not sl_hit and tp_idx < len(tp_levels)
    else:
        expiry_hit = not sl_hit and len(tp_hits) == 0
    t_entry = int((candles[entry_idx].ts_open + (delta if mk == "market_on_publish" else timedelta(0)) - st).total_seconds())
    if t_entry < 0:
        t_entry = 0
    out_ts = candles[outcome_i].ts_open + delta
    t_out = int((out_ts - st).total_seconds())
    if t_out < 0:
        t_out = 0

    return "COMPLETE", {
        "outcome_status": "COMPLETE",
        "entry_reached": entry_reached,
        "entry_fill_price": entry_fill,
        "tp_hits": tp_hits or None,
        "sl_hit": sl_hit,
        "expiry_hit": expiry_hit,
        "mfe": mfe,
        "mae": mae,
        "time_to_entry_sec": t_entry,
        "time_to_outcome_sec": t_out,
        "policy_ref": POLICY_REF_V0,
        "market_data_version": ENGINE_VERSION,
    }
