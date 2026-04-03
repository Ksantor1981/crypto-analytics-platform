"""
Слоты и обеспечение строк signal_outcomes (фаза 11).

Полный расчёт по свечам — отдельный worker; здесь создание PENDING, заглушка пересчёта, ручной PATCH.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional, Tuple

from sqlalchemy.orm import Session

from app.models.execution_model import ExecutionModel
from app.models.normalized_signal import NormalizedSignal
from app.models.signal_outcome import SignalOutcome

ALLOWED_PATCH_STATUSES = frozenset({"PENDING", "COMPLETE", "DATA_INCOMPLETE", "ERROR", "SKIPPED"})

STUB_POLICY_REF = "MARKET_OUTCOME_POLICY.md#stub"
STUB_ERROR_CODE = "canonical_market_data_pipeline_not_enabled"

_PATCHABLE_ATTRS = frozenset(
    {
        "outcome_status",
        "entry_reached",
        "entry_fill_price",
        "tp_hits",
        "sl_hit",
        "expiry_hit",
        "mfe",
        "mae",
        "time_to_entry_sec",
        "time_to_outcome_sec",
        "calculated_at",
        "market_data_version",
        "policy_ref",
        "error_detail",
    }
)


def ensure_pending_outcomes_for_normalized(
    db: Session,
    *,
    normalized_signal_id: int,
) -> Tuple[Optional[int], Optional[str]]:
    """
    Для каждой активной ExecutionModel, для которой ещё нет строки outcome, создаёт PENDING.

    Возвращает (число созданных записей, None) или (None, сообщение об ошибке).
    """
    ns = db.query(NormalizedSignal).filter(NormalizedSignal.id == normalized_signal_id).first()
    if not ns:
        return None, "normalized_signal not found"

    models = (
        db.query(ExecutionModel)
        .filter(ExecutionModel.is_active.is_(True))
        .order_by(ExecutionModel.sort_order.asc(), ExecutionModel.id.asc())
        .all()
    )
    existing_ids = {
        r[0]
        for r in db.query(SignalOutcome.execution_model_id)
        .filter(SignalOutcome.normalized_signal_id == normalized_signal_id)
        .all()
    }

    created = 0
    for m in models:
        if m.id in existing_ids:
            continue
        db.add(
            SignalOutcome(
                normalized_signal_id=normalized_signal_id,
                execution_model_id=m.id,
                outcome_status="PENDING",
            )
        )
        created += 1

    db.flush()
    return created, None


def ensure_pending_outcomes_for_raw_event(
    db: Session,
    *,
    raw_event_id: int,
) -> Tuple[int, int, Optional[str]]:
    """
    Для всех NormalizedSignal данного raw_event создаёт недостающие PENDING outcomes.

    Возвращает (число normalized сигналов, суммарно созданных строк outcome, error_message).
    При отсутствии normalized — (0, 0, None).
    """
    ns_list = (
        db.query(NormalizedSignal)
        .filter(NormalizedSignal.raw_event_id == raw_event_id)
        .order_by(NormalizedSignal.id.asc())
        .all()
    )
    if not ns_list:
        return 0, 0, None

    total_created = 0
    for ns in ns_list:
        created, err = ensure_pending_outcomes_for_normalized(db, normalized_signal_id=int(ns.id))
        if err:
            return len(ns_list), total_created, err
        total_created += int(created or 0)

    return len(ns_list), total_created, None


def apply_stub_recalculate(
    db: Session,
    *,
    signal_outcome_id: int,
) -> Tuple[Optional[SignalOutcome], Optional[str]]:
    """
    Заглушка «пересчёта»: выставляет DATA_INCOMPLETE с пояснением (пайплайн свечей не подключён).
    """
    row = db.query(SignalOutcome).filter(SignalOutcome.id == signal_outcome_id).first()
    if not row:
        return None, "signal_outcome not found"
    if row.outcome_status == "COMPLETE":
        return None, "stub_recalculate: outcome is COMPLETE; use PATCH to change"

    row.outcome_status = "DATA_INCOMPLETE"
    row.calculated_at = datetime.now(timezone.utc)
    row.policy_ref = STUB_POLICY_REF
    row.error_detail = {
        "code": STUB_ERROR_CODE,
        "message": "Расчёт по свечам не подключён; заглушка для трассировки контура.",
    }
    db.flush()
    return row, None


def patch_signal_outcome_fields(
    db: Session,
    *,
    signal_outcome_id: int,
    data: dict[str, Any],
) -> Tuple[Optional[SignalOutcome], Optional[str]]:
    """Частичное обновление полей outcome (admin / gold dataset)."""
    row = db.query(SignalOutcome).filter(SignalOutcome.id == signal_outcome_id).first()
    if not row:
        return None, "signal_outcome not found"

    for key, val in data.items():
        if key not in _PATCHABLE_ATTRS:
            continue
        if key == "outcome_status" and val is not None:
            if val not in ALLOWED_PATCH_STATUSES:
                return None, f"invalid outcome_status: {val}"
        setattr(row, key, val)

    db.flush()
    return row, None
