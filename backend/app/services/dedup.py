"""Signal deduplication utility."""
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.models.signal import Signal


def signal_exists(db: Session, channel_id: int, text: str) -> bool:
    """Check if signal already exists (by first 500 chars of text)."""
    text_500 = (text or "")[:500]
    return db.query(Signal).filter(
        Signal.channel_id == channel_id,
        func.left(Signal.original_text, 500) == text_500,
    ).first() is not None


def cleanup_duplicates(db: Session) -> int:
    """Remove duplicate signals, keep oldest."""
    from sqlalchemy import func
    subq = db.query(
        func.min(Signal.id).label('keep_id'),
        Signal.channel_id,
        Signal.original_text,
    ).group_by(Signal.channel_id, Signal.original_text).subquery()

    keep_ids = [r.keep_id for r in db.query(subq.c.keep_id).all()]
    if not keep_ids:
        return 0
    deleted = db.query(Signal).filter(~Signal.id.in_(keep_ids)).delete(synchronize_session=False)
    db.commit()
    return deleted
