"""
Review labels — внутренний API для разметки raw_events (ADMIN).
Очередь и карточка события — Review Console v0.1. См. docs/REVIEW_GUIDELINES.md
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import exists, func, or_
from sqlalchemy.orm import Session, joinedload

from app.core.auth import require_admin
from app.core.config import get_settings
from app.core.database import get_db
from app.models.channel import Channel
from app.models.extraction import Extraction
from app.models.normalized_signal import NormalizedSignal
from app.models.raw_ingestion import MessageVersion, RawEvent
from app.models.review_label import ReviewLabel
from app.models.signal_outcome import SignalOutcome
from app.models.signal_relation import SignalRelation
from app.models.user import User
from app.services.outcome_service import ensure_pending_outcomes_for_raw_event

router = APIRouter()

_PREVIEW_LEN = 400


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
    corrected_fields: Optional[dict] = None
    linked_signal_id: Optional[int]
    notes: Optional[str]
    created_at: object
    updated_at: object


class ReviewQueueItem(BaseModel):
    raw_event_id: int
    source_type: str
    channel_id: Optional[int]
    channel_username: Optional[str]
    platform_message_id: Optional[str]
    raw_text_preview: Optional[str]
    first_seen_at: Optional[datetime]
    version_count: int
    labels_count: int


class ReviewQueueResponse(BaseModel):
    items: List[ReviewQueueItem]
    total: int
    limit: int
    offset: int


class MessageVersionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    version_no: int
    text_snapshot: Optional[str]
    content_hash: Optional[str]
    version_reason: str
    observed_at: Optional[datetime]


class ChannelSnippet(BaseModel):
    id: int
    username: Optional[str]
    name: str


class ExtractionDecisionBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    decision_type: str
    decision_source: str
    confidence: Optional[float] = None


class ExtractionBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    message_version_id: int
    classification_status: str
    extractor_name: str
    extractor_version: str
    confidence: Optional[float] = None
    decision: Optional[ExtractionDecisionBrief] = None


class NormalizedSignalBrief(BaseModel):
    id: int
    extraction_id: int
    asset: str
    direction: str
    entry_price: str
    take_profit: Optional[str] = None
    """Цепочка TP из provenance (мульти-TP из экстракции), для Review UI."""
    take_profits: Optional[List[str]] = None
    stop_loss: Optional[str] = None
    trading_lifecycle_status: str
    relation_status: str
    legacy_signal_id: Optional[int] = None


class SignalRelationBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    from_normalized_signal_id: int
    to_normalized_signal_id: int
    relation_type: str
    relation_source: str
    confidence: Optional[float] = None


class SignalOutcomeBrief(BaseModel):
    id: int
    normalized_signal_id: int
    execution_model_key: str
    execution_display_name: str
    outcome_status: str
    entry_fill_price: Optional[str] = None
    calculated_at: Optional[datetime] = None
    policy_ref: Optional[str] = None


class RawEventDetailRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source_type: str
    source_id: Optional[str]
    channel_id: Optional[int]
    author_id: Optional[int]
    platform_message_id: Optional[str]
    reply_to_message_id: Optional[str]
    forward_from: Optional[dict] = None
    raw_payload: dict[str, Any]
    raw_text: Optional[str]
    media_refs: Optional[Any] = None
    content_hash: Optional[str]
    language: Optional[str]
    first_seen_at: Optional[datetime]
    ingested_at: Optional[datetime]


class RawEventDetailResponse(BaseModel):
    raw_event: RawEventDetailRead
    message_versions: List[MessageVersionRead]
    review_labels: List[ReviewLabelRead]
    channel: Optional[ChannelSnippet] = None
    extractions: List[ExtractionBrief] = Field(default_factory=list)
    normalized_signals: List[NormalizedSignalBrief] = Field(default_factory=list)
    signal_relations: List[SignalRelationBrief] = Field(default_factory=list)
    signal_outcomes: List[SignalOutcomeBrief] = Field(default_factory=list)


def _preview_text(text: Optional[str]) -> Optional[str]:
    if not text:
        return None
    t = text.strip()
    if len(t) <= _PREVIEW_LEN:
        return t
    return t[: _PREVIEW_LEN] + "…"


@router.get("/queue", response_model=ReviewQueueResponse)
def review_queue(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    unlabeled_only: bool = Query(True, description="Только raw_events без review_labels"),
    edited_only: bool = Query(False, description="Только события с version_no > 1"),
    channel_id: Optional[int] = Query(None, ge=1),
):
    """Очередь Review Console: пагинация и фильтры (см. REVIEW_GUIDELINES приоритеты)."""
    q = db.query(RawEvent)
    if unlabeled_only:
        q = q.filter(~exists().where(ReviewLabel.raw_event_id == RawEvent.id))
    if edited_only:
        edited_ids = (
            db.query(MessageVersion.raw_event_id)
            .group_by(MessageVersion.raw_event_id)
            .having(func.max(MessageVersion.version_no) > 1)
        )
        q = q.filter(RawEvent.id.in_(edited_ids))
    if channel_id is not None:
        q = q.filter(RawEvent.channel_id == channel_id)

    total = q.count()
    events: List[RawEvent] = (
        q.order_by(RawEvent.first_seen_at.desc()).offset(offset).limit(limit).all()
    )
    if not events:
        return ReviewQueueResponse(items=[], total=total, limit=limit, offset=offset)

    ids = [e.id for e in events]
    v_rows = (
        db.query(MessageVersion.raw_event_id, func.count(MessageVersion.id))
        .filter(MessageVersion.raw_event_id.in_(ids))
        .group_by(MessageVersion.raw_event_id)
        .all()
    )
    l_rows = (
        db.query(ReviewLabel.raw_event_id, func.count(ReviewLabel.id))
        .filter(ReviewLabel.raw_event_id.in_(ids))
        .group_by(ReviewLabel.raw_event_id)
        .all()
    )
    v_map = {r[0]: int(r[1]) for r in v_rows}
    l_map = {r[0]: int(r[1]) for r in l_rows}

    ch_ids = {e.channel_id for e in events if e.channel_id}
    ch_map: dict[int, Channel] = {}
    if ch_ids:
        for ch in db.query(Channel).filter(Channel.id.in_(ch_ids)).all():
            ch_map[ch.id] = ch

    items = [
        ReviewQueueItem(
            raw_event_id=e.id,
            source_type=e.source_type,
            channel_id=e.channel_id,
            channel_username=ch_map[e.channel_id].username if e.channel_id and e.channel_id in ch_map else None,
            platform_message_id=e.platform_message_id,
            raw_text_preview=_preview_text(e.raw_text),
            first_seen_at=e.first_seen_at,
            version_count=v_map.get(e.id, 0),
            labels_count=l_map.get(e.id, 0),
        )
        for e in events
    ]
    return ReviewQueueResponse(items=items, total=total, limit=limit, offset=offset)


@router.get("/raw-events/{raw_event_id}", response_model=RawEventDetailResponse)
def get_raw_event_detail(
    raw_event_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    ev = db.query(RawEvent).filter(RawEvent.id == raw_event_id).first()
    if not ev:
        raise HTTPException(status_code=404, detail="raw_event not found")
    versions = (
        db.query(MessageVersion)
        .filter(MessageVersion.raw_event_id == raw_event_id)
        .order_by(MessageVersion.version_no.asc())
        .all()
    )
    labels = (
        db.query(ReviewLabel)
        .filter(ReviewLabel.raw_event_id == raw_event_id)
        .order_by(ReviewLabel.created_at.desc())
        .all()
    )
    channel_snip: Optional[ChannelSnippet] = None
    if ev.channel_id:
        ch = db.query(Channel).filter(Channel.id == ev.channel_id).first()
        if ch:
            channel_snip = ChannelSnippet(id=ch.id, username=ch.username, name=ch.name)

    extractions = (
        db.query(Extraction)
        .options(joinedload(Extraction.decision))
        .filter(Extraction.raw_event_id == raw_event_id)
        .order_by(Extraction.id.asc())
        .all()
    )
    extraction_briefs: List[ExtractionBrief] = []
    extraction_fields_by_id: dict[int, dict] = {}
    for ex in extractions:
        dec = ex.decision
        extraction_fields_by_id[int(ex.id)] = ex.extracted_fields if isinstance(ex.extracted_fields, dict) else {}
        extraction_briefs.append(
            ExtractionBrief(
                id=ex.id,
                message_version_id=ex.message_version_id,
                classification_status=ex.classification_status,
                extractor_name=ex.extractor_name,
                extractor_version=ex.extractor_version,
                confidence=ex.confidence,
                decision=ExtractionDecisionBrief.model_validate(dec) if dec else None,
            )
        )

    ns_rows = (
        db.query(NormalizedSignal)
        .filter(NormalizedSignal.raw_event_id == raw_event_id)
        .order_by(NormalizedSignal.id.asc())
        .all()
    )
    if get_settings().OUTCOME_SLOTS_AUTO_ENSURE_ON_REVIEW_DETAIL and ns_rows:
        _n_norm, created_total, err = ensure_pending_outcomes_for_raw_event(
            db, raw_event_id=raw_event_id
        )
        if err:
            db.rollback()
            raise HTTPException(status_code=500, detail=err)
        if created_total > 0:
            db.commit()

    def _tp_ladder_from_provenance(ns_row: NormalizedSignal) -> Optional[List[str]]:
        prov = ns_row.provenance or {}
        raw = prov.get("take_profits")
        if not isinstance(raw, list) or len(raw) < 2:
            return None
        return [str(x) for x in raw]

    def _tp_ladder_from_extraction(extraction_id: int) -> Optional[List[str]]:
        ef = extraction_fields_by_id.get(int(extraction_id)) or {}
        raw = ef.get("take_profits")
        if not isinstance(raw, list) or len(raw) < 2:
            return None
        return [str(x) for x in raw]

    def _tp_ladder_for_normalized(ns_row: NormalizedSignal) -> Optional[List[str]]:
        a = _tp_ladder_from_provenance(ns_row)
        if a:
            return a
        return _tp_ladder_from_extraction(int(ns_row.extraction_id))

    ns_briefs = [
        NormalizedSignalBrief(
            id=ns.id,
            extraction_id=ns.extraction_id,
            asset=ns.asset,
            direction=ns.direction,
            entry_price=str(ns.entry_price),
            take_profit=str(ns.take_profit) if ns.take_profit is not None else None,
            take_profits=_tp_ladder_for_normalized(ns),
            stop_loss=str(ns.stop_loss) if ns.stop_loss is not None else None,
            trading_lifecycle_status=ns.trading_lifecycle_status,
            relation_status=ns.relation_status,
            legacy_signal_id=ns.legacy_signal_id,
        )
        for ns in ns_rows
    ]

    ns_ids = [ns.id for ns in ns_rows]
    rel_briefs: List[SignalRelationBrief] = []
    if ns_ids:
        rels = (
            db.query(SignalRelation)
            .filter(
                or_(
                    SignalRelation.from_normalized_signal_id.in_(ns_ids),
                    SignalRelation.to_normalized_signal_id.in_(ns_ids),
                )
            )
            .order_by(SignalRelation.id.asc())
            .all()
        )
        rel_briefs = [SignalRelationBrief.model_validate(r) for r in rels]

    outcome_briefs: List[SignalOutcomeBrief] = []
    if ns_ids:
        oc_rows = (
            db.query(SignalOutcome)
            .options(joinedload(SignalOutcome.execution_model))
            .filter(SignalOutcome.normalized_signal_id.in_(ns_ids))
            .order_by(SignalOutcome.normalized_signal_id.asc(), SignalOutcome.execution_model_id.asc())
            .all()
        )
        for oc in oc_rows:
            em = oc.execution_model
            outcome_briefs.append(
                SignalOutcomeBrief(
                    id=int(oc.id),
                    normalized_signal_id=int(oc.normalized_signal_id),
                    execution_model_key=em.model_key,
                    execution_display_name=em.display_name,
                    outcome_status=oc.outcome_status,
                    entry_fill_price=str(oc.entry_fill_price) if oc.entry_fill_price is not None else None,
                    calculated_at=oc.calculated_at,
                    policy_ref=oc.policy_ref,
                )
            )

    return RawEventDetailResponse(
        raw_event=RawEventDetailRead.model_validate(ev),
        message_versions=[MessageVersionRead.model_validate(v) for v in versions],
        review_labels=[ReviewLabelRead.model_validate(x) for x in labels],
        channel=channel_snip,
        extractions=extraction_briefs,
        normalized_signals=ns_briefs,
        signal_relations=rel_briefs,
        signal_outcomes=outcome_briefs,
    )


@router.post("/", response_model=ReviewLabelRead)
def create_review_label(
    body: ReviewLabelCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    raw_row = db.query(RawEvent).filter(RawEvent.id == body.raw_event_id).first()
    if not raw_row:
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
