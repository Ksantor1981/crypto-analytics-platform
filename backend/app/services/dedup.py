"""Signal deduplication: content fingerprint (SHA-256) + legacy left(500)."""
import hashlib
import re
from typing import Optional

from sqlalchemy.orm import Session

from app.models.signal import Signal


def normalize_text_for_dedup(text: Optional[str]) -> str:
    """Нормализация текста для устойчивого хеша дедупа."""
    if not text:
        return ""
    t = text.strip().lower()
    t = re.sub(r"\s+", " ", t)
    return t[:4000]


def content_fingerprint(text: Optional[str]) -> str:
    """SHA-256 hex от нормализованного текста сигнала."""
    n = normalize_text_for_dedup(text)
    return hashlib.sha256(n.encode("utf-8")).hexdigest()


def signal_exists(db: Session, channel_id: int, text: Optional[str]) -> bool:
    """
    Проверка дубликата: сначала по content_fingerprint, затем legacy по первым 500 символам
    для строк без заполненного fingerprint (старые записи).
    """
    fp = content_fingerprint(text)
    if (
        db.query(Signal)
        .filter(Signal.channel_id == channel_id, Signal.content_fingerprint == fp)
        .first()
    ):
        return True

    prefix = (text or "")[:500]
    if not prefix:
        return False

    legacy = (
        db.query(Signal)
        .filter(
            Signal.channel_id == channel_id,
            Signal.content_fingerprint.is_(None),
        )
        .all()
    )
    for row in legacy:
        if (row.original_text or "")[:500] == prefix:
            return True
    return False


def cleanup_duplicates(db: Session) -> int:
    """
    Удалить дубликаты: для записей с fingerprint — группировка по (channel_id, fingerprint);
    без fingerprint — по (channel_id, original_text). Оставляем минимальный id.
    """
    from sqlalchemy import func

    deleted = 0

    # 1) Строки с заполненным fingerprint
    sub_fp = (
        db.query(
            func.min(Signal.id).label("keep_id"),
            Signal.channel_id,
            Signal.content_fingerprint,
        )
        .filter(Signal.content_fingerprint.isnot(None))
        .group_by(Signal.channel_id, Signal.content_fingerprint)
        .subquery()
    )
    keep_fp_ids = [r.keep_id for r in db.query(sub_fp.c.keep_id).all()]
    if keep_fp_ids:
        deleted += (
            db.query(Signal)
            .filter(
                Signal.content_fingerprint.isnot(None),
                ~Signal.id.in_(keep_fp_ids),
            )
            .delete(synchronize_session=False)
        )

    # 2) Legacy без fingerprint — по полному original_text
    sub_txt = (
        db.query(
            func.min(Signal.id).label("keep_id"),
            Signal.channel_id,
            Signal.original_text,
        )
        .filter(Signal.content_fingerprint.is_(None))
        .group_by(Signal.channel_id, Signal.original_text)
        .subquery()
    )
    keep_txt_ids = [r.keep_id for r in db.query(sub_txt.c.keep_id).all()]
    if keep_txt_ids:
        deleted += (
            db.query(Signal)
            .filter(
                Signal.content_fingerprint.is_(None),
                ~Signal.id.in_(keep_txt_ids),
            )
            .delete(synchronize_session=False)
        )

    db.commit()
    return deleted
