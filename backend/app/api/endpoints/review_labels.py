"""
Review labels — внутренний API для разметки raw_events (ADMIN).
См. docs/REVIEW_GUIDELINES.md
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.core.auth import require_admin
from app.core.database import get_db
from app.models.raw_ingestion import RawEvent
from app.models.review_label import ReviewLabel
from app.models.user import User

router = APIRouter()


class ReviewLabelCreate(BaseModel):
    raw_event_id: int = Field(..., ge=1)
    label_type: str = Field(..., min_length=1, max_length=32)
    corrected_fields: Optional[dict] = None
    linked_signal_id: Optional[int] = Field(None, ge=1)
    notes: Optional[str] = Field(None, max_length=8000)
    reviewer_name: Optional[str] = Field(None, max_length=128)


class ReviewLabelRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    raw_event_id: int
    reviewer_user_id: Optional[int]
    reviewer_name: Optional[str]
    label_type: str
    linked_signal_id: Optional[int]
    notes: Optional[str]
    created_at: object
    updated_at: object


@router.post("/", response_model=ReviewLabelRead)
def create_review_label(
    body: ReviewLabelCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    exists = db.query(RawEvent).filter(RawEvent.id == body.raw_event_id).first()
    if not exists:
        raise HTTPException(status_code=404, detail="raw_event not found")

    name = body.reviewer_name or (current_user.email or current_user.username or str(current_user.id))[:128]
    row = ReviewLabel(
        raw_event_id=body.raw_event_id,
        reviewer_user_id=current_user.id,
        reviewer_name=name,
        label_type=body.label_type.strip().lower(),
        corrected_fields=body.corrected_fields,
        linked_signal_id=body.linked_signal_id,
        notes=body.notes,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.get("/", response_model=List[ReviewLabelRead])
def list_review_labels(
    raw_event_id: int = Query(..., ge=1),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    return (
        db.query(ReviewLabel)
        .filter(ReviewLabel.raw_event_id == raw_event_id)
        .order_by(ReviewLabel.created_at.desc())
        .all()
    )
