"""
Оркестрация пересчёта signal_outcomes по свечам (worker / admin API).
"""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Optional

from sqlalchemy.orm import Session, joinedload

from app.core.config import get_settings
from app.models.execution_model import ExecutionModel
from app.models.extraction import Extraction
from app.models.normalized_signal import NormalizedSignal
from app.models.raw_ingestion import RawEvent
from app.models.signal_outcome import SignalOutcome

from app.services.outcome_candle_engine import (
    ENGINE_VERSION,
    _midpoint_entry,
    compute_outcome_from_candles,
    load_candles_for_window,
)
from app.services.outcome_tp_levels import collect_take_profit_levels


def _signal_time_utc(ns: NormalizedSignal, raw: Optional[RawEvent]) -> datetime:
    if raw and raw.first_seen_at:
        t = raw.first_seen_at
        if t.tzinfo is None:
            return t.replace(tzinfo=timezone.utc)
        return t.astimezone(timezone.utc)
    t = ns.created_at
    if t.tzinfo is None:
        return t.replace(tzinfo=timezone.utc)
    return t.astimezone(timezone.utc)


def recalculate_signal_outcome_from_candles(
    db: Session,
    *,
    signal_outcome_id: int,
    force: bool = False,
    lookahead_days: int,
    timeframe: str,
) -> tuple[Optional[SignalOutcome], Optional[str]]:
    """
    Загружает свечи, считает поля, обновляет строку outcome.

    Без force: не трогает COMPLETE. PENDING / DATA_INCOMPLETE / ERROR пересчитываются.
    """
    row = (
        db.query(SignalOutcome)
        .options(
            joinedload(SignalOutcome.execution_model),
            joinedload(SignalOutcome.normalized_signal),
        )
        .filter(SignalOutcome.id == signal_outcome_id)
        .first()
    )
    if not row:
        return None, "signal_outcome not found"

    if row.outcome_status == "COMPLETE" and not force:
        return None, "recalculate: outcome is COMPLETE; pass force=true to overwrite"

    ns = row.normalized_signal
    em = row.execution_model
    if not ns or not em:
        return None, "missing normalized_signal or execution_model"

    raw = db.query(RawEvent).filter(RawEvent.id == ns.raw_event_id).first()
    sig_time = _signal_time_utc(ns, raw)

    candles, data_src = load_candles_for_window(
        db,
        asset=ns.asset,
        signal_time=sig_time,
        lookahead_days=lookahead_days,
        timeframe=timeframe,
    )
    md_ver = data_src or "none"

    sl = Decimal(str(ns.stop_loss)) if ns.stop_loss is not None else None
    entry = Decimal(str(ns.entry_price))
    mid = _midpoint_entry(ns)

    ex = db.query(Extraction).filter(Extraction.id == ns.extraction_id).first()
    primary_tp = Decimal(str(ns.take_profit)) if ns.take_profit is not None else None
    tp_levels = collect_take_profit_levels(
        ex.extracted_fields if ex else None,
        primary_tp,
        ns.direction,
        entry,
    )

    settings = get_settings()
    status, fields = compute_outcome_from_candles(
        model_key=em.model_key,
        direction=ns.direction,
        entry_price=entry,
        take_profit=None,
        stop_loss=sl,
        signal_time=sig_time,
        candles=candles,
        timeframe=timeframe,
        midpoint_price=mid,
        take_profit_levels=tp_levels,
        mop_reference=settings.OUTCOME_MOP_REFERENCE,
        sl_before_tp_same_bar=settings.OUTCOME_INTRABAR_SL_BEFORE_TP,
    )

    ver_suffix = f"{md_ver or 'none'}|{ENGINE_VERSION}"[:64]

    now = datetime.now(timezone.utc)
    row.calculated_at = now

    if status == "COMPLETE":
        row.outcome_status = "COMPLETE"
        row.entry_reached = fields.get("entry_reached")
        row.entry_fill_price = fields.get("entry_fill_price")
        row.tp_hits = fields.get("tp_hits")
        row.sl_hit = fields.get("sl_hit")
        row.expiry_hit = fields.get("expiry_hit")
        row.mfe = fields.get("mfe")
        row.mae = fields.get("mae")
        row.time_to_entry_sec = fields.get("time_to_entry_sec")
        row.time_to_outcome_sec = fields.get("time_to_outcome_sec")
        row.policy_ref = fields.get("policy_ref")
        row.market_data_version = ver_suffix
        row.error_detail = None
    elif status == "DATA_INCOMPLETE":
        row.outcome_status = "DATA_INCOMPLETE"
        row.entry_reached = fields.get("entry_reached")
        row.entry_fill_price = None
        row.tp_hits = None
        row.sl_hit = None
        row.expiry_hit = None
        row.mfe = None
        row.mae = None
        row.time_to_entry_sec = None
        row.time_to_outcome_sec = None
        row.policy_ref = fields.get("policy_ref")
        row.market_data_version = ver_suffix
        row.error_detail = fields.get("error_detail") or {"code": "data_incomplete"}
    else:
        row.outcome_status = "ERROR"
        row.error_detail = fields.get("error_detail") or {"code": "engine_error"}
        row.policy_ref = fields.get("policy_ref")
        row.market_data_version = ver_suffix

    db.flush()
    return row, None


def process_pending_signal_outcomes(
    db: Session,
    *,
    limit: int,
    lookahead_days: int,
    timeframe: str,
) -> dict[str, Any]:
    """Пакетная обработка PENDING outcomes (для Celery). Коммит после каждой успешной строки."""
    lim = max(1, min(int(limit), 500))
    rows = (
        db.query(SignalOutcome)
        .filter(SignalOutcome.outcome_status == "PENDING")
        .order_by(SignalOutcome.id.asc())
        .limit(lim)
        .all()
    )
    ok = 0
    failed = 0
    errors: list[str] = []
    for r in rows:
        try:
            _, err = recalculate_signal_outcome_from_candles(
                db,
                signal_outcome_id=int(r.id),
                force=False,
                lookahead_days=lookahead_days,
                timeframe=timeframe,
            )
            if err:
                db.rollback()
                failed += 1
                errors.append(f"id={r.id}: {err}")
            else:
                db.commit()
                ok += 1
        except Exception as ex:
            db.rollback()
            failed += 1
            errors.append(f"id={r.id}: {ex!s}")
    return {"processed": len(rows), "ok": ok, "failed": failed, "errors": errors[:20]}
