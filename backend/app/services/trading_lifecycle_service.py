"""
Допустимые переходы trading_lifecycle_status для NormalizedSignal (фаза 9, черновик).

См. docs/DOMAIN_GLOSSARY_CANONICAL.md — trading_lifecycle_status.
"""
from __future__ import annotations

from typing import FrozenSet, Optional

from sqlalchemy.orm import Session

from app.models.normalized_signal import NormalizedSignal

ALL_TRADING_LIFECYCLE_STATUSES: FrozenSet[str] = frozenset(
    {
        "PENDING_ENTRY",
        "ACTIVE",
        "PARTIALLY_CLOSED",
        "COMPLETED_TP",
        "COMPLETED_SL",
        "CANCELED",
        "EXPIRED",
        "DELETED_BY_AUTHOR",
    }
)

# Исходный статус → допустимые целевые
ALLOWED_TRANSITIONS: dict[str, FrozenSet[str]] = {
    "PENDING_ENTRY": frozenset(
        {"ACTIVE", "CANCELED", "EXPIRED", "DELETED_BY_AUTHOR"}
    ),
    "ACTIVE": frozenset(
        {
            "PARTIALLY_CLOSED",
            "COMPLETED_TP",
            "COMPLETED_SL",
            "CANCELED",
            "EXPIRED",
            "DELETED_BY_AUTHOR",
        }
    ),
    "PARTIALLY_CLOSED": frozenset(
        {"COMPLETED_TP", "COMPLETED_SL", "CANCELED", "EXPIRED", "ACTIVE"}
    ),
    "COMPLETED_TP": frozenset(),
    "COMPLETED_SL": frozenset(),
    "CANCELED": frozenset(),
    "EXPIRED": frozenset(),
    "DELETED_BY_AUTHOR": frozenset(),
}


def is_valid_status(status: str) -> bool:
    return status in ALL_TRADING_LIFECYCLE_STATUSES


def can_transition(current: str, target: str) -> bool:
    if not is_valid_status(target):
        return False
    if current == target:
        return True
    allowed = ALLOWED_TRANSITIONS.get(current, frozenset())
    return target in allowed


def apply_lifecycle_transition(
    db: Session,
    *,
    normalized_signal_id: int,
    to_status: str,
) -> tuple[Optional[NormalizedSignal], Optional[str]]:
    """
    Возвращает (normalized_signal, error_message).
    error_message если не найден сигнал или переход запрещён.
    """
    ns = db.query(NormalizedSignal).filter(NormalizedSignal.id == normalized_signal_id).first()
    if not ns:
        return None, "normalized_signal not found"

    cur = (ns.trading_lifecycle_status or "PENDING_ENTRY").strip().upper()
    tgt = to_status.strip().upper()
    if not is_valid_status(tgt):
        return None, f"unknown status: {tgt}"
    if not can_transition(cur, tgt):
        return None, f"transition not allowed: {cur} → {tgt}"

    ns.trading_lifecycle_status = tgt
    db.flush()
    return ns, None
