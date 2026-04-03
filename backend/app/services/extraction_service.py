"""
Канонический extraction: текст MessageVersion → структура + classification_status.

Экстрактор v0: обёртка над legacy `parse_signal_from_text` (telegram_scraper).
Включается флагом EXTRACTION_PIPELINE_ENABLED и вызывается из admin API / jobs.
"""
from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.extraction import Extraction
from app.models.extraction_decision import ExtractionDecision
from app.models.raw_ingestion import MessageVersion, RawEvent
from app.services.telegram_scraper import ParsedSignal, parse_signal_from_text

EXTRACTOR_NAME = "legacy_text"
EXTRACTOR_VERSION = "0.1.0"
RULES_SOURCE = "rules_v0"

# classification_status (extraction) → decision_type (REVIEW_GUIDELINES / глоссарий)
_CLASSIFICATION_TO_DECISION = {
    "PARSED": "signal",
    "NOISE": "noise",
    "UNRESOLVED": "unresolved",
    "AMBIGUOUS": "unresolved",
}

ALLOWED_DECISION_TYPES = frozenset(
    {"signal", "update", "close", "commentary", "duplicate", "noise", "unresolved"}
)


def map_classification_to_decision_type(classification_status: str) -> str:
    return _CLASSIFICATION_TO_DECISION.get(classification_status, "unresolved")


def ensure_decision_for_extraction(db: Session, extraction: Extraction) -> Optional[ExtractionDecision]:
    """
    Создаёт или обновляет ExtractionDecision по правилам; ручные (manual) не перезаписываются.
    """
    if not get_settings().EXTRACTION_PIPELINE_ENABLED:
        return None

    ed = (
        db.query(ExtractionDecision)
        .filter(ExtractionDecision.extraction_id == extraction.id)
        .one_or_none()
    )
    if ed is not None and ed.decision_source == "manual":
        return ed

    decision_type = map_classification_to_decision_type(extraction.classification_status)
    rationale = {"classification_status": extraction.classification_status, "source": RULES_SOURCE}

    if ed is not None:
        ed.decision_type = decision_type
        ed.confidence = extraction.confidence
        ed.rationale = rationale
        ed.decision_source = RULES_SOURCE
        db.flush()
        return ed

    row = ExtractionDecision(
        extraction_id=extraction.id,
        raw_event_id=extraction.raw_event_id,
        decision_type=decision_type,
        decision_source=RULES_SOURCE,
        confidence=extraction.confidence,
        rationale=rationale,
    )
    db.add(row)
    db.flush()
    return row


def _parsed_to_fields(parsed: ParsedSignal) -> Dict[str, Any]:
    out: Dict[str, Any] = {
        "asset": parsed.asset,
        "direction": parsed.direction,
        "confidence": parsed.confidence,
    }
    if parsed.entry_price is not None:
        out["entry_price"] = parsed.entry_price
    if parsed.take_profit is not None:
        out["take_profit"] = parsed.take_profit
    if len(getattr(parsed, "take_profits", []) or []) >= 2:
        out["take_profits"] = list(parsed.take_profits)
    if parsed.stop_loss is not None:
        out["stop_loss"] = parsed.stop_loss
    if parsed.entry_zone_low is not None:
        out["entry_zone_low"] = parsed.entry_zone_low
    if parsed.entry_zone_high is not None:
        out["entry_zone_high"] = parsed.entry_zone_high
    return out


def classify_and_fields(text: Optional[str]) -> Tuple[str, Optional[float], Dict[str, Any]]:
    """
    Возвращает (classification_status, confidence, extracted_fields).
    Статусы: NOISE, UNRESOLVED, AMBIGUOUS, PARSED — см. DOMAIN_GLOSSARY_CANONICAL.
    """
    if not (text or "").strip():
        return "NOISE", None, {}

    sig = parse_signal_from_text(text)
    if sig is None:
        return "UNRESOLVED", None, {}

    fields = _parsed_to_fields(sig)
    if sig.entry_price is not None:
        return "PARSED", float(sig.confidence), fields

    return "AMBIGUOUS", float(sig.confidence), fields


def get_or_create_extraction_for_message_version(
    db: Session,
    *,
    message_version_id: int,
) -> Optional[Extraction]:
    """
    Идемпотентно создаёт Extraction для версии сообщения.
    None если EXTRACTION_PIPELINE_ENABLED=false.
    """
    if not get_settings().EXTRACTION_PIPELINE_ENABLED:
        return None

    existing = (
        db.query(Extraction)
        .filter(
            Extraction.message_version_id == message_version_id,
            Extraction.extractor_name == EXTRACTOR_NAME,
            Extraction.extractor_version == EXTRACTOR_VERSION,
        )
        .one_or_none()
    )
    if existing:
        ensure_decision_for_extraction(db, existing)
        return existing

    mv = db.query(MessageVersion).filter(MessageVersion.id == message_version_id).first()
    if not mv:
        return None

    raw = db.query(RawEvent).filter(RawEvent.id == mv.raw_event_id).first()
    if not raw:
        return None

    status, conf, fields = classify_and_fields(mv.text_snapshot)
    row = Extraction(
        raw_event_id=raw.id,
        message_version_id=mv.id,
        extractor_name=EXTRACTOR_NAME,
        extractor_version=EXTRACTOR_VERSION,
        classification_status=status,
        confidence=conf,
        extracted_fields=fields,
    )
    db.add(row)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        ex = (
            db.query(Extraction)
            .filter(
                Extraction.message_version_id == message_version_id,
                Extraction.extractor_name == EXTRACTOR_NAME,
                Extraction.extractor_version == EXTRACTOR_VERSION,
            )
            .one_or_none()
        )
        if ex is not None:
            ensure_decision_for_extraction(db, ex)
        return ex
    ensure_decision_for_extraction(db, row)
    return row


def override_decision(
    db: Session,
    *,
    extraction_id: int,
    decision_type: str,
    rationale: Optional[Dict[str, Any]] = None,
) -> Optional[ExtractionDecision]:
    """Ручная правка decision_type; не трогает строку extraction."""
    dt = decision_type.strip().lower()
    if dt not in ALLOWED_DECISION_TYPES:
        return None

    ex = db.query(Extraction).filter(Extraction.id == extraction_id).first()
    if not ex:
        return None

    ed = (
        db.query(ExtractionDecision)
        .filter(ExtractionDecision.extraction_id == ex.id)
        .one_or_none()
    )
    rat: Dict[str, Any] = dict(rationale) if rationale else {}
    rat["override"] = True

    if ed:
        ed.decision_type = dt
        ed.decision_source = "manual"
        ed.rationale = rat
        db.flush()
        return ed

    row = ExtractionDecision(
        extraction_id=ex.id,
        raw_event_id=ex.raw_event_id,
        decision_type=dt,
        decision_source="manual",
        confidence=ex.confidence,
        rationale=rat,
    )
    db.add(row)
    db.flush()
    return row


def resolve_message_version_for_raw_event(
    db: Session,
    raw_event_id: int,
    message_version_id: Optional[int],
) -> Optional[MessageVersion]:
    if message_version_id is not None:
        mv = (
            db.query(MessageVersion)
            .filter(
                MessageVersion.id == message_version_id,
                MessageVersion.raw_event_id == raw_event_id,
            )
            .first()
        )
        return mv
    return (
        db.query(MessageVersion)
        .filter(MessageVersion.raw_event_id == raw_event_id)
        .order_by(MessageVersion.version_no.desc())
        .first()
    )
