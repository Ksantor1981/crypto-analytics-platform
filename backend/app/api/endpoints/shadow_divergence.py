"""
Admin: отчёт расхождений legacy Signal vs NormalizedSignal (data plane feedback, TZ C5).
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.auth import require_admin
from app.core.database import get_db
from app.core.metrics import (
    SHADOW_LEGACY_DIVERGENCE_LOW,
    SHADOW_LEGACY_DIVERGENCE_REPORTS,
    SHADOW_LEGACY_DIVERGENCE_SCORE,
)
from app.models.user import User
from app.services.shadow_divergence import build_divergence_report

router = APIRouter()


@router.get("/divergence-report")
def get_divergence_report(
    limit: int = Query(100, ge=1, le=500),
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Сравнение канонического слоя с legacy для строк `normalized_signals.legacy_signal_id IS NOT NULL`.
    Обновляет Prometheus-гистограмму `shadow_legacy_divergence_score`.
    """
    report = build_divergence_report(db, limit=limit)
    SHADOW_LEGACY_DIVERGENCE_REPORTS.inc()
    for s in report.get("samples") or []:
        if "match_score" in s and "error" not in s:
            sc = float(s["match_score"])
            SHADOW_LEGACY_DIVERGENCE_SCORE.observe(sc)
            if sc < 0.5:
                SHADOW_LEGACY_DIVERGENCE_LOW.inc()
    return report
