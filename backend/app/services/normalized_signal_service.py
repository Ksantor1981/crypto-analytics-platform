"""
Материализация NormalizedSignal из Extraction + ExtractionDecision.

Условия: EXTRACTION_PIPELINE_ENABLED, decision_type == signal, classification PARSED,
в extracted_fields есть asset, direction, entry_price.
"""
from __future__ import annotations

from typing import Any, List, Optional

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.extraction import Extraction
from app.models.extraction_decision import ExtractionDecision
from app.models.normalized_signal import NormalizedSignal


def eligible_for_materialization(
    ex: Extraction,
    dec: Optional[ExtractionDecision],
) -> bool:
    if dec is None or dec.decision_type != "signal":
        return False
    if ex.classification_status != "PARSED":
        return False
    fields = ex.extracted_fields or {}
    if fields.get("entry_price") is None:
        return False
    asset = (fields.get("asset") or "").strip()
    direction = (fields.get("direction") or "").strip()
    return bool(asset and direction)


def materialize_from_extraction(db: Session, extraction_id: int) -> Optional[NormalizedSignal]:
    if not get_settings().EXTRACTION_PIPELINE_ENABLED:
        return None

    existing = (
        db.query(NormalizedSignal)
        .filter(NormalizedSignal.extraction_id == extraction_id)
        .one_or_none()
    )
    if existing:
        return existing

    ex = db.query(Extraction).filter(Extraction.id == extraction_id).first()
    if not ex:
        return None

    dec = (
        db.query(ExtractionDecision)
        .filter(ExtractionDecision.extraction_id == ex.id)
        .one_or_none()
    )
    if not eligible_for_materialization(ex, dec):
        return None

    fields = ex.extracted_fields or {}
    ep = fields.get("entry_price")
    asset = (fields.get("asset") or "").strip()
    direction = (fields.get("direction") or "").strip().upper()

    provenance: dict[str, Any] = {
        "extractor_name": ex.extractor_name,
        "extractor_version": ex.extractor_version,
        "extraction_id": ex.id,
    }
    raw_tps = fields.get("take_profits")
    if isinstance(raw_tps, list) and len(raw_tps) >= 2:
        serial: List[float] = []
        for x in raw_tps:
            d = NormalizedSignal.numeric_or_none(x)
            if d is not None:
                serial.append(float(d))
        if len(serial) >= 2:
            provenance["take_profits"] = serial

    row = NormalizedSignal(
        raw_event_id=ex.raw_event_id,
        message_version_id=ex.message_version_id,
        extraction_id=ex.id,
        asset=asset[:64],
        direction=direction[:16],
        entry_price=NormalizedSignal.numeric_or_none(ep),
        take_profit=NormalizedSignal.numeric_or_none(fields.get("take_profit")),
        stop_loss=NormalizedSignal.numeric_or_none(fields.get("stop_loss")),
        entry_zone_low=NormalizedSignal.numeric_or_none(fields.get("entry_zone_low")),
        entry_zone_high=NormalizedSignal.numeric_or_none(fields.get("entry_zone_high")),
        provenance=provenance,
    )
    # SQLite: BigInteger PK не даёт INTEGER PRIMARY KEY autoincrement — без id INSERT падает NOT NULL.
    bind = db.get_bind()
    if bind.dialect.name == "sqlite":
        m = db.query(func.max(NormalizedSignal.id)).scalar()
        row.id = int(m or 0) + 1
    db.add(row)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        return (
            db.query(NormalizedSignal)
            .filter(NormalizedSignal.extraction_id == extraction_id)
            .one_or_none()
        )
    return row
