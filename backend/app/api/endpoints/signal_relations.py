"""
Admin API: signal_relations между normalized_signals (фаза 7 data plane).
"""
from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.core.auth import require_admin
from app.core.database import get_db
from app.models.signal_relation import SignalRelation
from app.models.user import User
from app.services.signal_relation_service import ALLOWED_RELATION_TYPES, create_signal_relation

router = APIRouter()


class SignalRelationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    from_normalized_signal_id: int
    to_normalized_signal_id: int
    relation_type: str
    relation_source: str
    confidence: Optional[float]
    relation_meta: Optional[dict]
    created_at: object


class SignalRelationCreate(BaseModel):
    from_normalized_signal_id: int = Field(..., ge=1)
    to_normalized_signal_id: int = Field(..., ge=1)
    relation_type: str = Field(..., min_length=1, max_length=32)
    confidence: Optional[float] = None
    relation_meta: Optional[dict] = None


@router.post("/", response_model=SignalRelationRead)
def post_signal_relation(
    body: SignalRelationCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    rt = body.relation_type.strip().lower()
    if rt not in ALLOWED_RELATION_TYPES:
        raise HTTPException(
            status_code=422,
            detail=f"relation_type must be one of: {sorted(ALLOWED_RELATION_TYPES)}",
        )
    if body.from_normalized_signal_id == body.to_normalized_signal_id:
        raise HTTPException(status_code=422, detail="from and to must differ")

    try:
        row = create_signal_relation(
            db,
            from_normalized_signal_id=body.from_normalized_signal_id,
            to_normalized_signal_id=body.to_normalized_signal_id,
            relation_type=rt,
            relation_source="manual",
            confidence=body.confidence,
            relation_meta=body.relation_meta,
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e)) from e

    if row is None:
        raise HTTPException(status_code=404, detail="normalized signal not found")
    db.commit()
    db.refresh(row)
    return row


@router.get("/", response_model=List[SignalRelationRead])
def list_signal_relations(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
    from_normalized_signal_id: Optional[int] = Query(None, ge=1),
    to_normalized_signal_id: Optional[int] = Query(None, ge=1),
):
    if from_normalized_signal_id is None and to_normalized_signal_id is None:
        raise HTTPException(
            status_code=422,
            detail="provide from_normalized_signal_id and/or to_normalized_signal_id",
        )
    q = db.query(SignalRelation)
    if from_normalized_signal_id is not None:
        q = q.filter(SignalRelation.from_normalized_signal_id == from_normalized_signal_id)
    if to_normalized_signal_id is not None:
        q = q.filter(SignalRelation.to_normalized_signal_id == to_normalized_signal_id)
    return q.order_by(SignalRelation.created_at.desc()).all()
