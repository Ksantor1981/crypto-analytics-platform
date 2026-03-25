"""
Check if pending signals have hit TP or SL based on current market prices.
Updates signal status and recalculates channel metrics.
"""
import logging
from sqlalchemy.orm import Session
from app.models.signal import Signal
from app.services.price_validator import get_current_price
from app.services.metrics_calculator import recalculate_all_channels

logger = logging.getLogger(__name__)


async def check_pending_signals(db: Session) -> dict:
    """Check all PENDING signals against current market prices."""
    pending = (
        db.query(Signal)
        .filter(
            Signal.status == "PENDING",
            Signal.entry_price.isnot(None),
        )
        .all()
    )
    updated = 0
    results = []

    for signal in pending:
        current_price = await get_current_price(signal.asset)
        if current_price is None:
            continue

        entry = float(signal.entry_price) if signal.entry_price else None
        tp = float(signal.tp1_price) if signal.tp1_price else None
        sl = float(signal.stop_loss) if signal.stop_loss else None

        if not entry:
            continue

        new_status = None
        pnl = None

        if signal.direction == "LONG":
            if tp and current_price >= tp:
                new_status = "TP1_HIT"
                pnl = ((tp - entry) / entry) * 100
            elif sl and current_price <= sl:
                new_status = "SL_HIT"
                pnl = ((sl - entry) / entry) * 100
        elif signal.direction == "SHORT":
            if tp and current_price <= tp:
                new_status = "TP1_HIT"
                pnl = ((entry - tp) / entry) * 100
            elif sl and current_price >= sl:
                new_status = "SL_HIT"
                pnl = ((entry - sl) / entry) * 100

        if new_status:
            signal.status = new_status
            if pnl is not None:
                signal.profit_loss_percentage = pnl
                entry = float(signal.entry_price)
                signal.profit_loss_absolute = round(entry * pnl / 100, 8)
            signal.is_successful = new_status == "TP1_HIT"
            updated += 1
            results.append({
                "id": signal.id,
                "asset": signal.asset,
                "direction": signal.direction,
                "status": new_status,
                "entry": entry,
                "current": current_price,
                "pnl": round(pnl, 2) if pnl else None,
            })

    if updated > 0:
        db.commit()
        recalculate_all_channels(db)

    return {
        "checked": len(pending),
        "updated": updated,
        "results": results,
    }
