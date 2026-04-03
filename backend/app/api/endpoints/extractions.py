"""
Admin API: запуск канонического extraction по raw_event / message_version.
См. docs/DATA_PLANE_MIGRATION.md фаза 5.
"""
from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.core.auth import require_admin
from app.core.config import get_settings
from app.core.database import get_db
from app.models.extraction import Extraction
from app.models.user import User
from app.services import extraction_service

router = APIRouter()


class ExtractionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    raw_event_id: int
    message_version_id: int
    extractor_name: str
    extractor_version: str
    classification_status: str
    confidence: Optional[float]
    extracted_fields: dict
    created_at: object


@router.post("/run-for-raw-event/{raw_event_id}", response_model=ExtractionRead)
def run_extraction_for_raw_event(
    raw_event_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
    message_version_id: Optional[int] = Query(
        None,
        description="Иначе берётся последняя версия по version_no",
    ),
):
    if not get_settings().EXTRACTION_PIPELINE_ENABLED:
        raise HTTPException(
            status_code=503,
            detail="EXTRACTION_PIPELINE_ENABLED=false",
        )

    mv = extraction_service.resolve_message_version_for_raw_event(
        db, raw_event_id, message_version_id
    )
    if not mv:
        raise HTTPException(status_code=404, detail="message_version not found")

    try:
        row = extraction_service.get_or_create_extraction_for_message_version(
            db, message_version_id=mv.id
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e)) from e

    if row is None:
        raise HTTPException(status_code=503, detail="extraction disabled")
    db.commit()
    db.refresh(row)
    return row


@router.get("/", response_model=List[ExtractionRead])
def list_extractions_for_raw_event(
    raw_event_id: int = Query(..., ge=1),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    return (
        db.query(Extraction)
        .filter(Extraction.raw_event_id == raw_event_id)
        .order_by(Extraction.created_at.desc())
        .all()
    )
