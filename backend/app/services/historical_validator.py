"""
Validate historical signals against real price data.
Uses CoinGecko historical API to check if TP/SL was hit after signal date.
"""
import logging
import httpx
from datetime import datetime, timedelta
from typing import Optional, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)

COINGECKO_IDS = {
    "BTC": "bitcoin", "ETH": "ethereum", "BNB": "binancecoin",
    "SOL": "solana", "ADA": "cardano", "XRP": "ripple",
    "DOT": "polkadot", "LINK": "chainlink", "UNI": "uniswap",
    "AVAX": "avalanche-2", "NEAR": "near", "APT": "aptos",
    "DOGE": "dogecoin", "SHIB": "shiba-inu",
}


@dataclass
class ValidationResult:
    signal_id: int
    asset: str
    direction: str
    entry_price: float
    tp_price: Optional[float]
    sl_price: Optional[float]
    signal_date: str
    outcome: str  # "TP_HIT", "SL_HIT", "PENDING", "NO_DATA"
    exit_price: Optional[float] = None
    pnl_pct: Optional[float] = None
    days_to_outcome: Optional[int] = None
    high_after: Optional[float] = None
    low_after: Optional[float] = None


async def get_price_range_after(asset: str, after_date: datetime, days: int = 14) -> Optional[dict]:
    """Get high/low prices for an asset in the days after a signal."""
    pair = asset.replace("/USDT", "").replace("/USD", "").upper()
    cg_id = COINGECKO_IDS.get(pair)
    if not cg_id:
        return None

    from_ts = int(after_date.timestamp())
    to_ts = int((after_date + timedelta(days=days)).timestamp())

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(
                f"https://api.coingecko.com/api/v3/coins/{cg_id}/market_chart/range",
                params={"vs_currency": "usd", "from": from_ts, "to": to_ts}
            )
            if r.status_code == 200:
                data = r.json()
                prices = [p[1] for p in data.get("prices", [])]
                if prices:
                    return {
                        "high": max(prices),
                        "low": min(prices),
                        "close": prices[-1],
                        "data_points": len(prices),
                    }
    except Exception as e:
        logger.warning(f"CoinGecko historical error for {pair}: {e}")

    return None


async def validate_signal_historically(
    asset: str, direction: str, entry_price: float,
    tp_price: Optional[float], sl_price: Optional[float],
    signal_date: datetime, signal_id: int = 0,
) -> ValidationResult:
    """Check if a historical signal would have hit TP or SL."""
    price_data = await get_price_range_after(asset, signal_date, days=14)

    if not price_data:
        return ValidationResult(
            signal_id=signal_id, asset=asset, direction=direction,
            entry_price=entry_price, tp_price=tp_price, sl_price=sl_price,
            signal_date=signal_date.isoformat(), outcome="NO_DATA",
        )

    high = price_data["high"]
    low = price_data["low"]

    outcome = "PENDING"
    exit_price = None
    pnl = None

    if direction == "LONG":
        if tp_price and high >= tp_price:
            outcome = "TP_HIT"
            exit_price = tp_price
            pnl = ((tp_price - entry_price) / entry_price) * 100
        elif sl_price and low <= sl_price:
            outcome = "SL_HIT"
            exit_price = sl_price
            pnl = ((sl_price - entry_price) / entry_price) * 100
        else:
            exit_price = price_data["close"]
            pnl = ((exit_price - entry_price) / entry_price) * 100
    elif direction == "SHORT":
        if tp_price and low <= tp_price:
            outcome = "TP_HIT"
            exit_price = tp_price
            pnl = ((entry_price - tp_price) / entry_price) * 100
        elif sl_price and high >= sl_price:
            outcome = "SL_HIT"
            exit_price = sl_price
            pnl = ((entry_price - sl_price) / entry_price) * 100
        else:
            exit_price = price_data["close"]
            pnl = ((entry_price - exit_price) / entry_price) * 100

    return ValidationResult(
        signal_id=signal_id, asset=asset, direction=direction,
        entry_price=entry_price, tp_price=tp_price, sl_price=sl_price,
        signal_date=signal_date.isoformat(), outcome=outcome,
        exit_price=exit_price, pnl_pct=round(pnl, 2) if pnl else None,
        high_after=high, low_after=low,
    )


async def validate_all_signals(db) -> dict:
    """Validate all signals in DB against historical prices."""
    from app.models.signal import Signal
    from app.models.channel import Channel

    signals = db.query(Signal).all()
    results = []
    tp_count = 0
    sl_count = 0
    total_validated = 0

    for s in signals:
        if not s.entry_price:
            continue

        sig_date = s.message_timestamp or s.created_at
        if not sig_date:
            continue
        if isinstance(sig_date, str):
            sig_date = datetime.fromisoformat(sig_date)

        r = await validate_signal_historically(
            asset=s.asset, direction=s.direction,
            entry_price=float(s.entry_price),
            tp_price=float(s.tp1_price) if s.tp1_price else None,
            sl_price=float(s.stop_loss) if s.stop_loss else None,
            signal_date=sig_date, signal_id=s.id,
        )

        if r.outcome != "NO_DATA":
            total_validated += 1
            if r.outcome == "TP_HIT":
                tp_count += 1
                s.status = "TP1_HIT"
                s.is_successful = True
            elif r.outcome == "SL_HIT":
                sl_count += 1
                s.status = "SL_HIT"
                s.is_successful = False

            if r.pnl_pct is not None:
                s.profit_loss_percentage = r.pnl_pct
                s.profit_loss_absolute = r.pnl_pct

        results.append({
            "id": r.signal_id, "asset": r.asset, "direction": r.direction,
            "entry": r.entry_price, "outcome": r.outcome,
            "pnl": r.pnl_pct, "high": r.high_after, "low": r.low_after,
        })

    db.commit()

    # Recalculate channel metrics
    from app.services.metrics_calculator import recalculate_all_channels
    recalculate_all_channels(db)

    accuracy = (tp_count / total_validated * 100) if total_validated > 0 else 0

    return {
        "total_signals": len(signals),
        "validated": total_validated,
        "tp_hit": tp_count,
        "sl_hit": sl_count,
        "accuracy": round(accuracy, 1),
        "results": results,
    }
