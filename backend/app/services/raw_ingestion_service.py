"""
Запись в канонический слой raw/message_versions при включённом shadow pipeline.

Вызов из ingestion workers после фазы 3. Пока без commit — транзакцию завершает вызывающий код.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Literal, Mapping, Optional, Tuple, Union

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.raw_ingestion import MessageVersion, RawEvent

ShadowUpsertAction = Literal["disabled", "created", "versioned", "unchanged"]


def _to_utc_aware(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _stable_json_hash(payload: Mapping[str, Any]) -> str:
    dumped = json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(dumped.encode("utf-8")).hexdigest()


def _insert_raw_event_and_initial_version(
    db: Session,
    *,
    source_type: str,
    raw_payload: dict[str, Any],
    channel_id: Optional[int] = None,
    author_id: Optional[int] = None,
    platform_message_id: Optional[str] = None,
    reply_to_message_id: Optional[str] = None,
    forward_from: Optional[dict] = None,
    raw_text: Optional[str] = None,
    media_refs: Optional[Union[list, dict]] = None,
    source_id: Optional[str] = None,
    language: Optional[str] = None,
    content_hash: Optional[str] = None,
    source_observed_at: Optional[datetime] = None,
) -> RawEvent:
    ch = content_hash or _stable_json_hash(raw_payload)
    ev = RawEvent(
        source_type=source_type,
        source_id=source_id,
        channel_id=channel_id,
        author_id=author_id,
        platform_message_id=platform_message_id,
        reply_to_message_id=reply_to_message_id,
        forward_from=forward_from,
        raw_payload=raw_payload,
        raw_text=raw_text,
        media_refs=media_refs,
        content_hash=ch,
        language=language,
    )
    if source_observed_at is not None:
        ta = _to_utc_aware(source_observed_at)
        ev.first_seen_at = ta
        ev.ingested_at = ta
    db.add(ev)
    db.flush()
    db.add(
        MessageVersion(
            raw_event_id=ev.id,
            version_no=1,
            text_snapshot=raw_text,
            content_hash=ch,
            version_reason="initial",
            observed_at=ev.first_seen_at,
        )
    )
    db.flush()
    return ev


def persist_raw_event_from_payload(
    db: Session,
    *,
    source_type: str,
    raw_payload: dict[str, Any],
    channel_id: Optional[int] = None,
    author_id: Optional[int] = None,
    platform_message_id: Optional[str] = None,
    reply_to_message_id: Optional[str] = None,
    forward_from: Optional[dict] = None,
    raw_text: Optional[str] = None,
    media_refs: Optional[Union[list, dict]] = None,
    source_id: Optional[str] = None,
    language: Optional[str] = None,
    content_hash: Optional[str] = None,
    source_observed_at: Optional[datetime] = None,
) -> Optional[RawEvent]:
    """
    Создаёт RawEvent и первую MessageVersion (initial).

    Возвращает None, если SHADOW_PIPELINE_ENABLED=false (legacy-only режим).
    """
    if not get_settings().SHADOW_PIPELINE_ENABLED:
        return None
    return _insert_raw_event_and_initial_version(
        db,
        source_type=source_type,
        raw_payload=raw_payload,
        channel_id=channel_id,
        author_id=author_id,
        platform_message_id=platform_message_id,
        reply_to_message_id=reply_to_message_id,
        forward_from=forward_from,
        raw_text=raw_text,
        media_refs=media_refs,
        source_id=source_id,
        language=language,
        content_hash=content_hash,
        source_observed_at=source_observed_at,
    )


def upsert_shadow_raw_event(
    db: Session,
    *,
    source_type: str,
    raw_payload: dict[str, Any],
    channel_id: Optional[int] = None,
    author_id: Optional[int] = None,
    platform_message_id: Optional[str] = None,
    reply_to_message_id: Optional[str] = None,
    forward_from: Optional[dict] = None,
    raw_text: Optional[str] = None,
    media_refs: Optional[Union[list, dict]] = None,
    source_id: Optional[str] = None,
    language: Optional[str] = None,
    content_hash: Optional[str] = None,
    source_observed_at: Optional[datetime] = None,
) -> Tuple[Optional[RawEvent], ShadowUpsertAction]:
    """
    Shadow ingestion: вставка нового факта или новая MessageVersion при смене текста.

    Повторный скан с тем же текстом → unchanged (без дублей версий). Метаданные в payload
    (views и т.д.) не порождают версию, пока совпадает text_snapshot.
    Без пары (channel_id, platform_message_id) — только insert (как раньше).
    """
    if not get_settings().SHADOW_PIPELINE_ENABLED:
        return None, "disabled"

    if channel_id is None or not platform_message_id:
        ev = _insert_raw_event_and_initial_version(
            db,
            source_type=source_type,
            raw_payload=raw_payload,
            channel_id=channel_id,
            author_id=author_id,
            platform_message_id=platform_message_id,
            reply_to_message_id=reply_to_message_id,
            forward_from=forward_from,
            raw_text=raw_text,
            media_refs=media_refs,
            source_id=source_id,
            language=language,
            content_hash=content_hash,
            source_observed_at=source_observed_at,
        )
        return ev, "created"

    existing = (
        db.query(RawEvent)
        .filter(
            RawEvent.channel_id == channel_id,
            RawEvent.platform_message_id == platform_message_id,
        )
        .one_or_none()
    )
    if existing is None:
        ev = _insert_raw_event_and_initial_version(
            db,
            source_type=source_type,
            raw_payload=raw_payload,
            channel_id=channel_id,
            author_id=author_id,
            platform_message_id=platform_message_id,
            reply_to_message_id=reply_to_message_id,
            forward_from=forward_from,
            raw_text=raw_text,
            media_refs=media_refs,
            source_id=source_id,
            language=language,
            content_hash=content_hash,
            source_observed_at=source_observed_at,
        )
        return ev, "created"

    latest = (
        db.query(MessageVersion)
        .filter(MessageVersion.raw_event_id == existing.id)
        .order_by(MessageVersion.version_no.desc())
        .first()
    )
    new_t = (raw_text or "").strip()
    old_t = (latest.text_snapshot or "").strip() if latest else ""
    if new_t == old_t:
        if new_t:
            return existing, "unchanged"
        ch_new = content_hash or _stable_json_hash(raw_payload)
        if latest and latest.content_hash == ch_new:
            return existing, "unchanged"

    ch = content_hash or _stable_json_hash(raw_payload)
    next_no = (latest.version_no + 1) if latest else 1
    obs = (
        _to_utc_aware(source_observed_at)
        if source_observed_at is not None
        else datetime.now(timezone.utc)
    )
    db.add(
        MessageVersion(
            raw_event_id=existing.id,
            version_no=next_no,
            text_snapshot=raw_text,
            content_hash=ch,
            version_reason="rescanned",
            observed_at=obs,
        )
    )
    db.flush()
    return existing, "versioned"
