"""
Admin API: signal_outcomes (фаза 11 data plane).

Слоты PENDING, чтение, PATCH, stub-recalculate; расчёт по свечам — POST .../recalculate, process-pending-recalc, Celery.
"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session, joinedload

from app.core.auth import require_admin
from app.core.config import get_settings
from app.core.database import get_db
from app.models.raw_ingestion import RawEvent
from app.models.signal_outcome import SignalOutcome
from app.models.user import User
from app.services.outcome_service import (
    apply_stub_recalculate,
    ensure_pending_outcomes_for_normalized,
    ensure_pending_outcomes_for_raw_event,
    patch_signal_outcome_fields,
)
from app.services.outcome_recalc_service import (
    process_pending_signal_outcomes,
    recalculate_signal_outcome_from_candles,
)

router = APIRouter()


class SignalOutcomeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

    id: int
    normalized_signal_id: int
    execution_model_id: int
    execution_model_key: str
    execution_display_name: str
    outcome_status: str
    entry_reached: Optional[bool] = None
    entry_fill_price: Optional[Decimal] = None
    tp_hits: Optional[list] = None
    sl_hit: Optional[bool] = None
    expiry_hit: Optional[bool] = None
    mfe: Optional[Decimal] = None
    mae: Optional[Decimal] = None
    time_to_entry_sec: Optional[int] = None
    time_to_outcome_sec: Optional[int] = None
    calculated_at: Optional[object] = None
    market_data_version: Optional[str] = None
    policy_ref: Optional[str] = None
    error_detail: Optional[dict] = None
    created_at: object
    updated_at: object


class EnsureOutcomesResponse(BaseModel):
    normalized_signal_id: int
    created: int


class EnsureRawEventOutcomesResponse(BaseModel):
    raw_event_id: int
    normalized_signal_count: int
    created_total: int


class ProcessPendingOutcomesResponse(BaseModel):
    processed: int
    ok: int
    failed: int
    errors: List[str] = Field(default_factory=list)


class SignalOutcomePatchBody(BaseModel):
    outcome_status: Optional[str] = Field(None, max_length=32)
    entry_reached: Optional[bool] = None
    entry_fill_price: Optional[Decimal] = None
    tp_hits: Optional[list] = None
    sl_hit: Optional[bool] = None
    expiry_hit: Optional[bool] = None
    mfe: Optional[Decimal] = None
    mae: Optional[Decimal] = None
    time_to_entry_sec: Optional[int] = None
    time_to_outcome_sec: Optional[int] = None
    calculated_at: Optional[datetime] = None
    market_data_version: Optional[str] = Field(None, max_length=64)
    policy_ref: Optional[str] = Field(None, max_length=128)
    error_detail: Optional[dict] = None


def _to_read(row: SignalOutcome) -> SignalOutcomeRead:
    em = row.execution_model
    return SignalOutcomeRead(
        id=int(row.id),
        normalized_signal_id=int(row.normalized_signal_id),
        execution_model_id=int(row.execution_model_id),
        execution_model_key=em.model_key,
        execution_display_name=em.display_name,
        outcome_status=row.outcome_status,
        entry_reached=row.entry_reached,
        entry_fill_price=row.entry_fill_price,
        tp_hits=row.tp_hits,
        sl_hit=row.sl_hit,
        expiry_hit=row.expiry_hit,
        mfe=row.mfe,
        mae=row.mae,
        time_to_entry_sec=row.time_to_entry_sec,
        time_to_outcome_sec=row.time_to_outcome_sec,
        calculated_at=row.calculated_at,
        market_data_version=row.market_data_version,
        policy_ref=row.policy_ref,
        error_detail=row.error_detail,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


@router.get("/", response_model=List[SignalOutcomeRead])
def list_signal_outcomes(
    normalized_signal_id: int = Query(..., ge=1),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    rows = (
        db.query(SignalOutcome)
        .options(joinedload(SignalOutcome.execution_model))
        .filter(SignalOutcome.normalized_signal_id == normalized_signal_id)
        .order_by(SignalOutcome.execution_model_id.asc())
        .all()
    )
    return [_to_read(r) for r in rows]


@router.post(
    "/ensure/{normalized_signal_id}",
    response_model=EnsureOutcomesResponse,
)
def post_ensure_outcome_slots(
    normalized_signal_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """Создать недостающие строки PENDING для всех активных execution_models."""
    created, err = ensure_pending_outcomes_for_normalized(db, normalized_signal_id=normalized_signal_id)
    if err:
        if err == "normalized_signal not found":
            raise HTTPException(status_code=404, detail=err)
        raise HTTPException(status_code=500, detail=err)
    db.commit()
    return EnsureOutcomesResponse(normalized_signal_id=normalized_signal_id, created=created)


@router.post(
    "/ensure-for-raw-event/{raw_event_id}",
    response_model=EnsureRawEventOutcomesResponse,
)
def post_ensure_outcome_slots_for_raw_event(
    raw_event_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """Создать недостающие PENDING для всех normalized_signals данного raw_event."""
    ev = db.query(RawEvent).filter(RawEvent.id == raw_event_id).first()
    if not ev:
        raise HTTPException(status_code=404, detail="raw_event not found")

    ns_count, created_total, err = ensure_pending_outcomes_for_raw_event(
        db, raw_event_id=raw_event_id
    )
    if err:
        db.rollback()
        raise HTTPException(status_code=500, detail=err)
    db.commit()
    return EnsureRawEventOutcomesResponse(
        raw_event_id=raw_event_id,
        normalized_signal_count=ns_count,
        created_total=created_total,
    )


@router.patch("/{signal_outcome_id}", response_model=SignalOutcomeRead)
def patch_signal_outcome(
    signal_outcome_id: int,
    body: SignalOutcomePatchBody,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """Ручное обновление полей outcome (разметка / правки до worker)."""
    payload = body.model_dump(exclude_unset=True)
    row, err = patch_signal_outcome_fields(db, signal_outcome_id=signal_outcome_id, data=payload)
    if err == "signal_outcome not found":
        raise HTTPException(status_code=404, detail=err)
    if err:
        raise HTTPException(status_code=422, detail=err)
    db.commit()
    db.refresh(row)
    row = (
        db.query(SignalOutcome)
        .options(joinedload(SignalOutcome.execution_model))
        .filter(SignalOutcome.id == signal_outcome_id)
        .first()
    )
    return _to_read(row)


@router.post("/process-pending-recalc", response_model=ProcessPendingOutcomesResponse)
def post_process_pending_outcome_recalc(
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """Пакетный пересчёт PENDING outcomes по свечам (см. Celery task)."""
    settings = get_settings()
    if not settings.OUTCOME_RECALC_ENABLED:
        raise HTTPException(status_code=503, detail="OUTCOME_RECALC_ENABLED=false")
    stats = process_pending_signal_outcomes(
        db,
        limit=limit,
        lookahead_days=settings.OUTCOME_RECALC_LOOKAHEAD_DAYS,
        timeframe=settings.OUTCOME_RECALC_TIMEFRAME,
    )
    return ProcessPendingOutcomesResponse(**stats)


@router.post("/{signal_outcome_id}/recalculate", response_model=SignalOutcomeRead)
def post_recalculate_outcome_from_candles(
    signal_outcome_id: int,
    force: bool = Query(False, description="Пересчитать даже если статус COMPLETE"),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """Расчёт по свечам: market_candles или CoinGecko OHLC (флаг OUTCOME_RECALC_ENABLED)."""
    settings = get_settings()
    if not settings.OUTCOME_RECALC_ENABLED:
        raise HTTPException(status_code=503, detail="OUTCOME_RECALC_ENABLED=false")
    row, err = recalculate_signal_outcome_from_candles(
        db,
        signal_outcome_id=signal_outcome_id,
        force=force,
        lookahead_days=settings.OUTCOME_RECALC_LOOKAHEAD_DAYS,
        timeframe=settings.OUTCOME_RECALC_TIMEFRAME,
    )
    if err == "signal_outcome not found":
        raise HTTPException(status_code=404, detail=err)
    if err:
        raise HTTPException(status_code=422, detail=err)
    db.commit()
    row = (
        db.query(SignalOutcome)
        .options(joinedload(SignalOutcome.execution_model))
        .filter(SignalOutcome.id == signal_outcome_id)
        .first()
    )
    return _to_read(row)


@router.post("/{signal_outcome_id}/stub-recalculate", response_model=SignalOutcomeRead)
def post_stub_recalculate_outcome(
    signal_outcome_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """Заглушка пересчёта: DATA_INCOMPLETE + error_detail (свечи/market worker не подключены)."""
    row, err = apply_stub_recalculate(db, signal_outcome_id=signal_outcome_id)
    if err == "signal_outcome not found":
        raise HTTPException(status_code=404, detail=err)
    if err:
        raise HTTPException(status_code=422, detail=err)
    db.commit()
    db.refresh(row)
    row = (
        db.query(SignalOutcome)
        .options(joinedload(SignalOutcome.execution_model))
        .filter(SignalOutcome.id == signal_outcome_id)
        .first()
    )
    return _to_read(row)


@router.get("/{signal_outcome_id}", response_model=SignalOutcomeRead)
def get_signal_outcome(
    signal_outcome_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    row = (
        db.query(SignalOutcome)
        .options(joinedload(SignalOutcome.execution_model))
        .filter(SignalOutcome.id == signal_outcome_id)
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="signal_outcome not found")
    return _to_read(row)
