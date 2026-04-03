"""
Запись в канонический слой raw/message_versions при включённом shadow pipeline.

Вызов из ingestion workers после фазы 3. Пока без commit — транзакцию завершает вызывающий код.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping, Optional, Union

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.raw_ingestion import MessageVersion, RawEvent


def _stable_json_hash(payload: Mapping[str, Any]) -> str:
    dumped = json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(dumped.encode("utf-8")).hexdigest()


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
) -> Optional[RawEvent]:
    """
    Создаёт RawEvent и первую MessageVersion (initial).

    Возвращает None, если SHADOW_PIPELINE_ENABLED=false (legacy-only режим).
    """
    if not get_settings().SHADOW_PIPELINE_ENABLED:
        return None

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
    db.add(ev)
    db.flush()
    db.add(
        MessageVersion(
            raw_event_id=ev.id,
            version_no=1,
            text_snapshot=raw_text,
            content_hash=ch,
            version_reason="initial",
        )
    )
    db.flush()
    return ev
