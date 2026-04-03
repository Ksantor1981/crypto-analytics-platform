"""
Сбор уровней take-profit для расчёта outcome: normalized + extracted_fields.

Поддерживаются списки в полях экстракции и отдельные ключи tp2/tp3 (ручные правки, будущие парсеры).
"""
from __future__ import annotations

from decimal import Decimal
from typing import Any, List, Optional


def _to_decimal(v: Any) -> Optional[Decimal]:
    if v is None:
        return None
    try:
        return Decimal(str(v))
    except Exception:
        return None


def sanitize_take_profit_levels(
    direction: str,
    entry: Decimal,
    levels: List[Decimal],
) -> List[Decimal]:
    """Фильтр по направлению, дедуп, сортировка: LONG по возрастанию цены, SHORT по убыванию."""
    d = (direction or "").upper()
    cand: List[Decimal] = []
    for p in levels:
        if d == "LONG" and p > entry:
            cand.append(p)
        elif d == "SHORT" and p < entry:
            cand.append(p)
    seen: set[Decimal] = set()
    uniq: List[Decimal] = []
    for p in cand:
        if p not in seen:
            seen.add(p)
            uniq.append(p)
    if d == "LONG":
        uniq.sort()
    elif d == "SHORT":
        uniq.sort(reverse=True)
    return uniq


def collect_take_profit_levels(
    extracted_fields: Optional[dict],
    primary_tp: Optional[Decimal],
    direction: str,
    entry: Decimal,
) -> List[Decimal]:
    raw: List[Decimal] = []

    ef = extracted_fields or {}
    for key in ("take_profits", "tp_levels", "targets", "take_profit_prices"):
        val = ef.get(key)
        if isinstance(val, list):
            for x in val:
                d = _to_decimal(x)
                if d is not None:
                    raw.append(d)

    scalar_keys = (
        "take_profit",
        "tp1",
        "tp1_price",
        "take_profit_1",
        "take_profit_2",
        "tp2",
        "tp2_price",
        "take_profit_3",
        "tp3",
        "tp3_price",
    )
    for key in scalar_keys:
        d = _to_decimal(ef.get(key))
        if d is not None:
            raw.append(d)

    if primary_tp is not None:
        raw.append(primary_tp)

    return sanitize_take_profit_levels(direction, entry, raw)
