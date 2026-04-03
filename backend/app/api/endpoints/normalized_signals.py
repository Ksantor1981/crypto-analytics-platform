"""
Admin API: normalized_signals — материализация из extraction (фаза 8 data plane).
"""
from __future__ import annotations

from decimal import Decimal
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.core.auth import require_admin
from app.core.config import get_settings
from app.core.database import get_db
from app.models.normalized_signal import NormalizedSignal
from app.models.signal import Signal
from app.models.user import User
from app.services.normalized_signal_service import materialize_from_extraction
from app.services.outcome_service import ensure_pending_outcomes_for_normalized
from app.services.trading_lifecycle_service import apply_lifecycle_transition

router = APIRouter()


class NormalizedSignalRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    raw_event_id: int
    message_version_id: int
    extraction_id: int
    legacy_signal_id: Optional[int]
    asset: str
    direction: str
    entry_price: Decimal
    take_profit: Optional[Decimal]
    stop_loss: Optional[Decimal]
    entry_zone_low: Optional[Decimal]
    entry_zone_high: Optional[Decimal]
    trading_lifecycle_status: str
    relation_status: str
    provenance: Optional[dict]
    created_at: object
    updated_at: object


class LegacyLinkBody(BaseModel):
    legacy_signal_id: Optional[int] = Field(None, ge=1, description="null — отвязать")


class LifecyclePatchBody(BaseModel):
    trading_lifecycle_status: str = Field(..., min_length=1, max_length=32)


@router.patch("/{normalized_signal_id}/lifecycle", response_model=NormalizedSignalRead)
def patch_trading_lifecycle(
    normalized_signal_id: int,
    body: LifecyclePatchBody,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """Переход trading_lifecycle_status по графу (см. trading_lifecycle_service)."""
    ns, err = apply_lifecycle_transition(
        db,
        normalized_signal_id=normalized_signal_id,
        to_status=body.trading_lifecycle_status,
    )
    if err == "normalized_signal not found":
        raise HTTPException(status_code=404, detail=err)
    if err:
        raise HTTPException(status_code=422, detail=err)
    db.commit()
    db.refresh(ns)
    return ns


@router.patch("/{normalized_signal_id}/legacy-link", response_model=NormalizedSignalRead)
def patch_legacy_signal_link(
    normalized_signal_id: int,
    body: LegacyLinkBody,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    ns = db.query(NormalizedSignal).filter(NormalizedSignal.id == normalized_signal_id).first()
    if not ns:
        raise HTTPException(status_code=404, detail="normalized_signal not found")
    if body.legacy_signal_id is not None:
        sig = db.query(Signal).filter(Signal.id == body.legacy_signal_id).first()
        if not sig:
            raise HTTPException(status_code=404, detail="legacy signal not found")
        ns.legacy_signal_id = body.legacy_signal_id
    else:
        ns.legacy_signal_id = None
    db.commit()
    db.refresh(ns)
    return ns


@router.post("/materialize/{extraction_id}", response_model=NormalizedSignalRead)
def post_materialize_from_extraction(
    extraction_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    if not get_settings().EXTRACTION_PIPELINE_ENABLED:
        raise HTTPException(status_code=503, detail="EXTRACTION_PIPELINE_ENABLED=false")

    try:
        row = materialize_from_extraction(db, extraction_id)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e)) from e

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="cannot materialize: need extraction, decision_type=signal, PARSED, asset/direction/entry_price",
        )
    if get_settings().OUTCOME_SLOTS_AUTO_ENSURE:
        ensure_pending_outcomes_for_normalized(db, normalized_signal_id=row.id)
    db.commit()
    db.refresh(row)
    return row


@router.get("/", response_model=List[NormalizedSignalRead])
def list_normalized_signals_for_raw_event(
    raw_event_id: int = Query(..., ge=1),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    return (
        db.query(NormalizedSignal)
        .filter(NormalizedSignal.raw_event_id == raw_event_id)
        .order_by(NormalizedSignal.created_at.desc())
        .all()
    )
