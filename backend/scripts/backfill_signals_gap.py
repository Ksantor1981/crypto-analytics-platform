#!/usr/bin/env python3
"""
Дозаполнение сигналов за интервал дат (когда БД не принимала записи).

Запуск из каталога backend (или из контейнера WORKDIR=/app):
  python scripts/backfill_signals_gap.py --start 2026-03-18 --end 2026-03-25

Границы: [start, end) в UTC (end не включается).
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

# Запуск как файл: добавляем корень backend в path
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

from app.core.config import get_settings  # noqa: E402
from app.core.database import SessionLocal  # noqa: E402
from app.services.metrics_calculator import recalculate_all_channels  # noqa: E402
from app.services.signal_backfill import backfill_signals_for_window  # noqa: E402


def parse_utc_date(s: str) -> datetime:
    """Принимает YYYY-MM-DD или полный ISO; возвращает aware UTC."""
    s = s.strip()
    if len(s) == 10 and s[4] == "-" and s[7] == "-":
        dt = datetime.fromisoformat(s).replace(tzinfo=timezone.utc)
        return dt
    dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


async def _run(start: datetime, end: datetime, tg_pages: int, rd_pages: int) -> dict:
    db = SessionLocal()
    try:
        settings = get_settings()
        result = await backfill_signals_for_window(
            db,
            settings,
            start,
            end,
            telegram_max_pages=tg_pages,
            reddit_max_pages=rd_pages,
        )
        db.commit()
        recalculate_all_channels(db)
        db.commit()
        return result
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def main() -> int:
    p = argparse.ArgumentParser(description="Backfill signals for a UTC date range")
    p.add_argument(
        "--start",
        default="2026-03-18",
        help="Начало интервала UTC (YYYY-MM-DD или ISO)",
    )
    p.add_argument(
        "--end",
        default="2026-03-25",
        help="Конец интервала UTC, не включая день (YYYY-MM-DD или ISO)",
    )
    p.add_argument(
        "--telegram-max-pages",
        type=int,
        default=45,
        help="Страниц t.me/s на канал (глубина истории)",
    )
    p.add_argument(
        "--reddit-max-pages",
        type=int,
        default=40,
        help="Страниц JSON /new на сабреддит",
    )
    args = p.parse_args()
    start = parse_utc_date(args.start)
    end = parse_utc_date(args.end)
    if start >= end:
        print("error: start must be < end", file=sys.stderr)
        return 2

    out = asyncio.run(
        _run(start, end, args.telegram_max_pages, args.reddit_max_pages)
    )
    print(json.dumps(out, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
