#!/usr/bin/env python3
"""
Process RAW telegram media signals (kind=RAW_MEDIA_SIGNAL) into full `signals`.

Source: telegram_signals table (TelegramSignal model) stores RAW media posts with
asset+direction in text, but missing entry/TP/SL (often only present on image).

This job:
- selects pending RAW rows
- extracts media URL (from "[MEDIA] <url>" in original_text)
- runs OCR and parsing
- if entry_price appears -> saves a full Signal via collection_pipeline
- marks RAW row status accordingly and updates signal_metadata

Run (inside backend container):
  docker exec crypto-analytics-backend python scripts/process_raw_media_signals.py --limit 200
"""

import argparse
import asyncio
import re
from datetime import datetime, timezone
from pathlib import Path
import sys

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))
project_root = backend_dir.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings
from app.models.channel import Channel
from app.models.signal import TelegramSignal
from app.services.collection_pipeline import persist_parsed_signals_for_channel
from app.services.ocr_signal_parser import extract_text_from_url
from app.services.telegram_scraper import ParsedSignal, parse_signal_from_text


_MEDIA_RE = re.compile(r"\[MEDIA\]\s+(https?://\S+)", re.I)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _get_media_url(raw_text: str) -> str | None:
    if not raw_text:
        return None
    m = _MEDIA_RE.search(raw_text)
    return m.group(1).strip() if m else None


def _ensure_channel(db, source: str) -> Channel | None:
    if not source:
        return None
    ch = (
        db.query(Channel)
        .filter(Channel.platform == "telegram", Channel.username == source)
        .first()
    )
    return ch


async def _parse_from_raw(raw_text: str, media_url: str | None, *, ocr_max_chars: int) -> ParsedSignal | None:
    base = (raw_text or "").strip()
    if media_url and "[MEDIA]" not in base:
        base = (base + "\n" if base else "") + f"[MEDIA] {media_url}"

    # 1) Try parse from caption/alt text only
    sig = parse_signal_from_text(base) if base else None
    if sig:
        sig.original_text = base
        if sig.entry_price:
            return sig

    if not media_url:
        return None

    # 2) Try OCR text + parse combined (caption + OCR text)
    ocr_text = (await extract_text_from_url(media_url)) or ""
    ocr_text = ocr_text.strip()
    if ocr_max_chars > 0:
        ocr_text = ocr_text[:ocr_max_chars]

    combined = base
    if ocr_text:
        combined = (combined + "\n" if combined else "") + f"[OCR_TEXT]\n{ocr_text}"

    sig2 = parse_signal_from_text(combined) if combined else None
    if sig2:
        sig2.original_text = combined[:500]
        if sig2.entry_price:
            return sig2

    # If we at least have asset+direction (RAW), return it for potential raw bookkeeping.
    return sig or sig2


async def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=200)
    ap.add_argument("--only-sources", type=str, default="", help="comma-separated telegram channel usernames to process")
    ap.add_argument("--max-attempts", type=int, default=5)
    ap.add_argument("--ocr-max-chars", type=int, default=1200)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    settings = get_settings()
    engine = create_engine(settings.database_url)
    Session = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    db = Session()

    try:
        sources = [s.strip() for s in (args.only_sources or "").split(",") if s.strip()]

        # SQLAlchemy JSON access differs by dialect; keep it simple and portable for Postgres:
        q = db.query(TelegramSignal).filter(text("signal_metadata->>'kind' = 'RAW_MEDIA_SIGNAL'"))
        # Only process pending raws; do not churn exhausted rows unless explicitly reset.
        q = q.filter((TelegramSignal.status == None) | (TelegramSignal.status == "PENDING"))
        if sources:
            q = q.filter(TelegramSignal.source.in_(sources))
        raws = q.order_by(TelegramSignal.id.asc()).limit(args.limit).all()

        processed = 0
        upgraded = 0
        skipped_no_channel = 0
        skipped_no_media = 0
        skipped_no_entry = 0
        marked_exhausted = 0

        for raw in raws:
            processed += 1
            raw_meta = dict(raw.signal_metadata or {})
            attempts = int(raw_meta.get("raw_process_attempts") or 0)
            raw_meta["raw_last_attempt_at"] = _now_iso()
            raw_meta["raw_process_attempts"] = attempts + 1

            media_url = _get_media_url(raw.original_text or "")
            if not media_url:
                raw.status = "SKIPPED_NO_MEDIA"
                raw.signal_metadata = raw_meta
                skipped_no_media += 1
                continue

            ch = _ensure_channel(db, raw.source)
            if not ch:
                raw.status = "SKIPPED_NO_CHANNEL"
                raw.signal_metadata = raw_meta
                skipped_no_channel += 1
                continue

            sig = await _parse_from_raw(raw.original_text or "", media_url, ocr_max_chars=args.ocr_max_chars)
            if not sig:
                if raw_meta["raw_process_attempts"] >= args.max_attempts:
                    raw.status = "EXHAUSTED_NO_ENTRY"
                    marked_exhausted += 1
                else:
                    raw.status = "PENDING"
                raw.signal_metadata = raw_meta
                skipped_no_entry += 1
                continue

            if not sig.entry_price:
                if raw_meta["raw_process_attempts"] >= args.max_attempts:
                    raw.status = "EXHAUSTED_NO_ENTRY"
                    marked_exhausted += 1
                else:
                    raw.status = "PENDING"
                raw.signal_metadata = raw_meta
                skipped_no_entry += 1
                continue

            sig.timestamp = raw.timestamp or raw.created_at
            sig.telegram_message_id = str(raw_meta.get("telegram_message_id") or "") or None

            if args.dry_run:
                raw.status = "DRY_RUN_WOULD_UPGRADE"
                raw.signal_metadata = raw_meta
                upgraded += 1
                continue

            st = persist_parsed_signals_for_channel(
                db,
                ch,
                [sig],
                posts_fetched=0,
                record_metrics=True,
                use_message_time_for_created_at=True,
            )
            if st.get("saved", 0) > 0:
                raw.status = "UPGRADED_TO_SIGNAL"
                upgraded += 1
            else:
                # Probably duplicate
                raw.status = "UPGRADE_DUPLICATE"
            raw_meta["raw_upgrade_result"] = st
            raw.signal_metadata = raw_meta

            # commit in small batches via implicit transaction (we'll commit at end)

        if not args.dry_run:
            db.commit()
        else:
            db.rollback()

        print(
            "DONE",
            {
                "selected": len(raws),
                "processed": processed,
                "upgraded": upgraded,
                "skipped_no_channel": skipped_no_channel,
                "skipped_no_media": skipped_no_media,
                "skipped_no_entry": skipped_no_entry,
                "marked_exhausted": marked_exhausted,
                "dry_run": bool(args.dry_run),
            },
        )
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))

