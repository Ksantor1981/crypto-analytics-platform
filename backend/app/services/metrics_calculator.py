"""
Calculate channel accuracy and ROI from signal history.
"""
import logging
from sqlalchemy.orm import Session
from app.models.channel import Channel
from app.models.signal import Signal

logger = logging.getLogger(__name__)

HIT_STATUSES = {"TP1_HIT", "TP2_HIT", "TP3_HIT", "ENTRY_HIT"}
MISS_STATUSES = {"SL_HIT", "EXPIRED", "CANCELLED"}
RESOLVED_STATUSES = HIT_STATUSES | MISS_STATUSES


def recalculate_channel_metrics(db: Session, channel_id: int) -> dict:
    """Recalculate accuracy and ROI for a channel from its signals."""
    channel = db.query(Channel).filter(Channel.id == channel_id).first()
    if not channel:
        return {"error": "Channel not found"}

    signals = db.query(Signal).filter(Signal.channel_id == channel_id).all()
    total = len(signals)
    resolved = [s for s in signals if s.status in RESOLVED_STATUSES]
    hits = [s for s in signals if s.status in HIT_STATUSES]

    channel.signals_count = total

    if resolved:
        channel.accuracy = round(len(hits) / len(resolved) * 100, 1)
        channel.successful_signals = len(hits)
    elif total > 0:
        channel.accuracy = None
        channel.successful_signals = 0
    else:
        channel.accuracy = None
        channel.successful_signals = 0

    total_roi = 0.0
    roi_count = 0
    for s in signals:
        if s.profit_loss_absolute is not None:
            total_roi += float(s.profit_loss_absolute)
            roi_count += 1
    channel.average_roi = round(total_roi / roi_count, 2) if roi_count > 0 else None

    db.commit()

    return {
        "channel": channel.name,
        "total_signals": total,
        "resolved": len(resolved),
        "hits": len(hits),
        "accuracy": channel.accuracy,
        "average_roi": channel.average_roi,
    }


def recalculate_all_channels(db: Session) -> list:
    """Recalculate metrics for all channels."""
    channels = db.query(Channel).all()
    results = []
    for ch in channels:
        r = recalculate_channel_metrics(db, ch.id)
        results.append(r)
    return results
