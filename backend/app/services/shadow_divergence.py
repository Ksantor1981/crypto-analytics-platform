"""
Сравнение legacy Signal с каноническим NormalizedSignal (feedback loop, TZ C5).

Используется, когда материализация выставила legacy_signal_id — иначе сравнения нет.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.models.normalized_signal import NormalizedSignal
from app.models.signal import Signal


def _norm_direction(d: Optional[str]) -> str:
    if not d:
        return ""
    u = str(d).strip().upper()
    if u in ("BUY", "LONG"):
        return "LONG"
    if u in ("SELL", "SHORT"):
        return "SHORT"
    return u


def _norm_asset(a: Optional[str]) -> str:
    if not a:
        return ""
    s = str(a).strip().upper().replace(" ", "")
    return s.replace("/", "")


def _rel_price_diff(a: Optional[Decimal], b: Optional[Decimal]) -> float:
    if a is None or b is None:
        return 1.0
    af = float(a)
    bf = float(b)
    if af == 0 and bf == 0:
        return 0.0
    denom = max(abs(af), abs(bf), 1e-12)
    return abs(af - bf) / denom


def compare_pair(legacy: Signal, norm: NormalizedSignal) -> dict[str, Any]:
    """
    Возвращает поля сравнения и match_score в [0, 1].
    """
    leg_asset = _norm_asset(legacy.asset) or _norm_asset(legacy.symbol)
    norm_asset = _norm_asset(norm.asset)
    asset_match = bool(leg_asset and norm_asset and leg_asset == norm_asset)

    ld = getattr(legacy.direction, "value", legacy.direction)
    leg_dir = _norm_direction(str(ld) if ld is not None else "")
    norm_dir = _norm_direction(norm.direction)
    direction_match = bool(leg_dir and norm_dir and leg_dir == norm_dir)

    rdiff = _rel_price_diff(legacy.entry_price, norm.entry_price)
    if rdiff < 0.001:
        price_score = 1.0
    elif rdiff < 0.01:
        price_score = 0.7
    elif rdiff < 0.05:
        price_score = 0.4
    else:
        price_score = 0.0

    match_score = (
        (1.0 if asset_match else 0.0)
        + (1.0 if direction_match else 0.0)
        + price_score
    ) / 3.0

    return {
        "normalized_signal_id": norm.id,
        "legacy_signal_id": legacy.id,
        "asset_match": asset_match,
        "direction_match": direction_match,
        "entry_price_relative_diff": round(rdiff, 6),
        "legacy_asset": legacy.asset,
        "normalized_asset": norm.asset,
        "legacy_direction": str(ld) if ld is not None else None,
        "normalized_direction": norm.direction,
        "match_score": round(match_score, 4),
    }


def build_divergence_report(
    db: Session,
    *,
    limit: int = 100,
) -> dict[str, Any]:
    """
    Агрегат по последним записям NormalizedSignal с привязкой к legacy.
    """
    q = (
        db.query(NormalizedSignal)
        .filter(NormalizedSignal.legacy_signal_id.isnot(None))
        .order_by(NormalizedSignal.id.desc())
        .limit(max(1, min(limit, 500)))
    )
    rows = q.all()
    samples: list[dict[str, Any]] = []
    scores: list[float] = []

    for norm in rows:
        lid = norm.legacy_signal_id
        if lid is None:
            continue
        leg = db.get(Signal, lid)
        if leg is None:
            samples.append(
                {
                    "normalized_signal_id": norm.id,
                    "legacy_signal_id": lid,
                    "error": "legacy_signal_not_found",
                    "match_score": 0.0,
                }
            )
            scores.append(0.0)
            continue
        row = compare_pair(leg, norm)
        samples.append(row)
        scores.append(float(row["match_score"]))

    n = len(scores)
    mean_score = sum(scores) / n if n else None

    return {
        "sample_size": n,
        "mean_match_score": round(mean_score, 4) if mean_score is not None else None,
        "samples": samples,
    }


def _classify_sample(sample: dict[str, Any]) -> str:
    if sample.get("error") == "legacy_signal_not_found":
        return "missing_legacy"
    score = float(sample.get("match_score") or 0.0)
    if score >= 0.9:
        return "strong_match"
    if score >= 0.5:
        return "partial_match"
    return "divergent"


def build_ab_report(
    db: Session,
    *,
    limit: int = 100,
    min_sample_size: int = 100,
    go_threshold: float = 0.9,
    block_threshold: float = 0.5,
) -> dict[str, Any]:
    """
    A/B отчёт legacy↔canonical для dashboard/readiness.

    Это не делает canonical источником истины автоматически. Отчёт отвечает на
    вопрос: достаточно ли совпадает канонический слой с legacy, чтобы идти к
    review/switch-over, или нужно разбирать расхождения.
    """
    divergence = build_divergence_report(db, limit=limit)
    samples = divergence.get("samples") or []
    buckets = {
        "strong_match": 0,
        "partial_match": 0,
        "divergent": 0,
        "missing_legacy": 0,
    }

    for sample in samples:
        buckets[_classify_sample(sample)] += 1

    sample_size = int(divergence.get("sample_size") or 0)
    mean_score = divergence.get("mean_match_score")
    legacy_count = db.query(Signal).count()
    canonical_count = db.query(NormalizedSignal).count()
    linked_canonical_count = (
        db.query(NormalizedSignal)
        .filter(NormalizedSignal.legacy_signal_id.isnot(None))
        .count()
    )

    if sample_size < min_sample_size:
        readiness = "insufficient_sample"
        recommendation = "continue_shadow_collection"
    elif mean_score is not None and mean_score >= go_threshold and buckets["divergent"] == 0:
        readiness = "ready_for_review"
        recommendation = "review_switch_over_candidates"
    elif mean_score is not None and mean_score < block_threshold:
        readiness = "blocked"
        recommendation = "investigate_extraction_or_mapping"
    else:
        readiness = "needs_review"
        recommendation = "send_divergent_samples_to_review_queue"

    return {
        "readiness": readiness,
        "recommendation": recommendation,
        "sample_size": sample_size,
        "min_sample_size": min_sample_size,
        "mean_match_score": mean_score,
        "legacy_count": legacy_count,
        "canonical_count": canonical_count,
        "linked_canonical_count": linked_canonical_count,
        "buckets": buckets,
        "samples": samples,
    }
