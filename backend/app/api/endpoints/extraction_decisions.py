"""
Admin API: ExtractionDecision — просмотр и ручной override.
См. docs/DATA_PLANE_MIGRATION.md фаза 6.
"""
from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.core.auth import require_admin
from app.core.database import get_db
from app.models.extraction_decision import ExtractionDecision
from app.models.user import User
from app.services.extraction_service import ALLOWED_DECISION_TYPES, override_decision

router = APIRouter()


class ExtractionDecisionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    extraction_id: int
    raw_event_id: int
    decision_type: str
    decision_source: str
    confidence: Optional[float]
    rationale: Optional[dict]
    created_at: object
    updated_at: object


class DecisionOverrideBody(BaseModel):
    extraction_id: int = Field(..., ge=1)
    decision_type: str = Field(..., min_length=1, max_length=32)
    rationale: Optional[dict] = None


@router.get("/", response_model=List[ExtractionDecisionRead])
def list_decisions_for_raw_event(
    raw_event_id: int = Query(..., ge=1),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    return (
        db.query(ExtractionDecision)
        .filter(ExtractionDecision.raw_event_id == raw_event_id)
        .order_by(ExtractionDecision.created_at.desc())
        .all()
    )


@router.post("/override", response_model=ExtractionDecisionRead)
def post_override_decision(
    body: DecisionOverrideBody,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    dt = body.decision_type.strip().lower()
    if dt not in ALLOWED_DECISION_TYPES:
        raise HTTPException(
            status_code=422,
            detail=f"decision_type must be one of: {sorted(ALLOWED_DECISION_TYPES)}",
        )
    row = override_decision(
        db,
        extraction_id=body.extraction_id,
        decision_type=dt,
        rationale=body.rationale,
    )

    if row is None:
        raise HTTPException(status_code=404, detail="extraction not found")
    db.commit()
    db.refresh(row)
    return row
