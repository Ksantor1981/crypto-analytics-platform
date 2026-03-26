"""
Deep historical collector — scrapes ALL available posts from Telegram channels
using pagination, extracts signals, validates against CoinGecko historical prices.
"""
import re
import logging
import httpx
from bs4 import BeautifulSoup
from datetime import datetime
from typing import List, Tuple
from app.services.telegram_scraper import ParsedSignal, parse_signal_from_text, ChannelPost

logger = logging.getLogger(__name__)


async def fetch_all_posts(username: str, max_pages: int = 10) -> List[ChannelPost]:
    """Fetch ALL available posts from a channel using pagination."""
    all_posts = []
    url = f"https://t.me/s/{username}"
    before_id = None

    async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
        for page in range(max_pages):
            params = {}
            if before_id:
                params["before"] = before_id

            try:
                r = await client.get(url, params=params, headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                })
                if r.status_code != 200:
                    break

                soup = BeautifulSoup(r.text, "html.parser")
                messages = soup.select(".tgme_widget_message_wrap")

                if not messages:
                    break

                new_posts = 0
                earliest_id = None
                for msg in messages:
                    msg_el = msg.select_one(".tgme_widget_message")
                    text_el = msg.select_one(".tgme_widget_message_text")
                    date_el = msg.select_one(".tgme_widget_message_date time")

                    if not text_el:
                        continue

                    # Get message ID for pagination
                    if msg_el:
                        data_post = msg_el.get("data-post", "")
                        if "/" in data_post:
                            msg_id = int(data_post.split("/")[-1])
                            if earliest_id is None or msg_id < earliest_id:
                                earliest_id = msg_id

                    text = text_el.get_text(separator="\n").strip()
                    date = None
                    if date_el and date_el.get("datetime"):
                        try:
                            date = datetime.fromisoformat(date_el["datetime"].replace("Z", "+00:00"))
                        except ValueError:
                            pass

                    # message id is embedded in data-post like "channel/12345"
                    mid = None
                    if msg_el:
                        data_post = msg_el.get("data-post", "")
                        if "/" in data_post:
                            mid = data_post.split("/")[-1]
                    all_posts.append(ChannelPost(text=text, date=date, message_id=mid))
                    new_posts += 1

                if new_posts == 0 or earliest_id is None:
                    break

                before_id = earliest_id
                logger.info(f"@{username} page {page+1}: {new_posts} posts (total: {len(all_posts)}, before={before_id})")

            except Exception as e:
                logger.warning(f"@{username} page {page+1} error: {e}")
                break

    logger.info(f"@{username}: {len(all_posts)} total posts collected")
    return all_posts


async def collect_deep_signals(username: str, max_pages: int = 10) -> List[ParsedSignal]:
    """Collect all historical signals from a channel."""
    posts = await fetch_all_posts(username, max_pages)
    signals = []
    for post in posts:
        sig = parse_signal_from_text(post.text)
        if sig and sig.entry_price:
            sig.timestamp = post.date
            signals.append(sig)
    return signals


async def deep_collect_and_validate(db, channel_usernames: List[str] = None) -> dict:
    """Collect deep history from all channels and validate against market prices."""
    from app.models.channel import Channel
    from app.models.signal import Signal
    from app.services.historical_validator import validate_signal_historically

    if channel_usernames is None:
        channels = db.query(Channel).filter(Channel.is_active == True, Channel.platform == "telegram").all()
    else:
        channels = db.query(Channel).filter(Channel.username.in_(channel_usernames)).all()

    total_posts = 0
    total_signals = 0
    total_validated = 0
    tp_count = 0
    sl_count = 0
    channel_results = []

    for ch in channels:
        uname = ch.username or (ch.url or "").rstrip("/").split("/")[-1]
        if not uname:
            continue

        signals = await collect_deep_signals(uname, max_pages=5)
        total_posts += len(signals)

        saved = 0
        validated_signals = []
        for sig in signals:
            # Save to DB
            existing = db.query(Signal).filter(
                Signal.channel_id == ch.id,
                Signal.original_text == sig.original_text[:500],
            ).first()
            if not existing:
                db_sig = Signal(
                    channel_id=ch.id, asset=sig.asset, symbol=sig.asset.replace("/", ""),
                    direction=sig.direction, entry_price=sig.entry_price,
                    tp1_price=sig.take_profit, stop_loss=sig.stop_loss,
                    confidence_score=sig.confidence, original_text=sig.original_text,
                    status="PENDING", message_timestamp=sig.timestamp,
                )
                db.add(db_sig)
                saved += 1

            # Validate historically
            if sig.timestamp:
                try:
                    v = await validate_signal_historically(
                        asset=sig.asset, direction=sig.direction,
                        entry_price=sig.entry_price,
                        tp_price=sig.take_profit, sl_price=sig.stop_loss,
                        signal_date=sig.timestamp.replace(tzinfo=None) if sig.timestamp.tzinfo else sig.timestamp,
                    )
                    if v.outcome != "NO_DATA":
                        total_validated += 1
                        if v.outcome == "TP_HIT":
                            tp_count += 1
                        elif v.outcome == "SL_HIT":
                            sl_count += 1
                        validated_signals.append({
                            "asset": v.asset, "direction": v.direction,
                            "entry": v.entry_price, "outcome": v.outcome,
                            "pnl": v.pnl_pct, "date": sig.timestamp.strftime("%Y-%m-%d"),
                        })
                except Exception as e:
                    logger.debug(f"Validation error: {e}")

        ch.signals_count = db.query(Signal).filter(Signal.channel_id == ch.id).count()
        total_signals += saved

        if validated_signals:
            ch_tp = sum(1 for v in validated_signals if v["outcome"] == "TP_HIT")
            ch_sl = sum(1 for v in validated_signals if v["outcome"] == "SL_HIT")
            ch_resolved = ch_tp + ch_sl
            ch_acc = (ch_tp / ch_resolved * 100) if ch_resolved > 0 else None
            ch.accuracy = ch_acc
            avg_pnl = sum(v["pnl"] for v in validated_signals if v["pnl"]) / len(validated_signals) if validated_signals else None
            ch.average_roi = round(avg_pnl, 2) if avg_pnl else None

            channel_results.append({
                "channel": ch.name, "username": uname,
                "signals": len(validated_signals), "tp": ch_tp, "sl": ch_sl,
                "accuracy": ch_acc, "avg_pnl": avg_pnl,
                "signals_detail": validated_signals[:10],
            })

    db.commit()

    resolved = tp_count + sl_count
    accuracy = (tp_count / resolved * 100) if resolved > 0 else 0

    return {
        "channels_processed": len(channels),
        "total_signals_found": total_posts,
        "new_saved": total_signals,
        "validated": total_validated,
        "tp_hit": tp_count,
        "sl_hit": sl_count,
        "open": total_validated - resolved,
        "accuracy_resolved": round(accuracy, 1),
        "accuracy_all": round(tp_count / total_validated * 100, 1) if total_validated > 0 else 0,
        "channels": channel_results,
    }
