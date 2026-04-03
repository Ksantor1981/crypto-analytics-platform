"""
Создание signal_relations между normalized_signals + обновление relation_status.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.normalized_signal import NormalizedSignal
from app.models.signal_relation import SignalRelation

ALLOWED_RELATION_TYPES = frozenset({"duplicate_of", "update_to", "close_of"})


def create_signal_relation(
    db: Session,
    *,
    from_normalized_signal_id: int,
    to_normalized_signal_id: int,
    relation_type: str,
    relation_source: str = "manual",
    confidence: Optional[float] = None,
    relation_meta: Optional[Dict[str, Any]] = None,
) -> Optional[SignalRelation]:
    if from_normalized_signal_id == to_normalized_signal_id:
        return None
    rt = relation_type.strip().lower()
    if rt not in ALLOWED_RELATION_TYPES:
        return None

    fs = db.query(NormalizedSignal).filter(NormalizedSignal.id == from_normalized_signal_id).first()
    ts = db.query(NormalizedSignal).filter(NormalizedSignal.id == to_normalized_signal_id).first()
    if not fs or not ts:
        return None

    row = SignalRelation(
        from_normalized_signal_id=fs.id,
        to_normalized_signal_id=ts.id,
        relation_type=rt,
        relation_source=relation_source[:32],
        confidence=confidence,
        relation_meta=relation_meta,
    )
    db.add(row)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        return (
            db.query(SignalRelation)
            .filter(
                SignalRelation.from_normalized_signal_id == from_normalized_signal_id,
                SignalRelation.to_normalized_signal_id == to_normalized_signal_id,
                SignalRelation.relation_type == rt,
            )
            .one_or_none()
        )

    fs.relation_status = "LINKED"
    ts.relation_status = "LINKED"
    db.flush()
    return row
