"""
Telethon-based Telegram collector — reads FULL history from any channel.
Requires one-time phone auth (creates .session file).

Setup: python -m app.services.telethon_collector --auth
Collect: python -m app.services.telethon_collector --collect
"""
import os
import sys
import asyncio
import logging
from datetime import datetime, timedelta
import base64
from typing import Any, Dict, List, Optional, Tuple

from app.services.telegram_scraper import ChannelPost, ParsedSignal, parse_signal_from_text

logger = logging.getLogger(__name__)


def _json_safe_mtproto(obj: Any) -> Any:
    """TLObject.to_dict() → JSON-совместимое дерево (datetime → iso, bytes → base64)."""
    if obj is None or isinstance(obj, (bool, int, float, str)):
        return obj
    if isinstance(obj, bytes):
        return {
            "_": "bytes_b64",
            "b64": base64.standard_b64encode(obj).decode("ascii"),
        }
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, dict):
        return {str(k): _json_safe_mtproto(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_json_safe_mtproto(x) for x in obj]
    return str(obj)


def _custom_message_to_tl_object(message: Any) -> Any:
    """telethon.tl.custom.message.Message → types.Message | types.MessageService для to_dict()."""
    from telethon.tl import types as tl_types

    if getattr(message, "action", None) is not None:
        return tl_types.MessageService(
            id=message.id,
            peer_id=message.peer_id,
            date=message.date,
            action=message.action,
            out=message.out,
            mentioned=message.mentioned,
            media_unread=message.media_unread,
            silent=message.silent,
            post=message.post,
            legacy=message.legacy,
            from_id=message.from_id,
            reply_to=message.reply_to,
            ttl_period=message.ttl_period,
        )
    return tl_types.Message(
        id=message.id,
        peer_id=message.peer_id,
        date=message.date,
        message=message.message or "",
        out=message.out,
        mentioned=message.mentioned,
        media_unread=message.media_unread,
        silent=message.silent,
        post=message.post,
        from_scheduled=message.from_scheduled,
        legacy=message.legacy,
        edit_hide=message.edit_hide,
        pinned=message.pinned,
        noforwards=message.noforwards,
        invert_media=message.invert_media,
        from_id=message.from_id,
        fwd_from=message.fwd_from,
        via_bot_id=message.via_bot_id,
        reply_to=message.reply_to,
        media=message.media,
        reply_markup=message.reply_markup,
        entities=message.entities,
        views=message.views,
        forwards=message.forwards,
        replies=message.replies,
        edit_date=message.edit_date,
        post_author=message.post_author,
        grouped_id=message.grouped_id,
        reactions=message.reactions,
        restriction_reason=message.restriction_reason,
        ttl_period=message.ttl_period,
    )


def telethon_message_to_mtproto_dict(message: Any) -> Dict[str, Any]:
    """Полный снимок MTProto сообщения для raw_payload['mtproto']."""
    raw = _custom_message_to_tl_object(message)
    return _json_safe_mtproto(raw.to_dict())

_raw_api_id = os.getenv("TELEGRAM_API_ID", "0")
try:
    API_ID = int(_raw_api_id)
except ValueError:
    import re
    m = re.search(r"(\d{5,})", _raw_api_id)
    API_ID = int(m.group(1)) if m else 0
API_HASH = os.getenv("TELEGRAM_API_HASH", "")
SESSION_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "telegram_session")


def _get_client():
    """Create Telethon client."""
    try:
        from telethon import TelegramClient
        return TelegramClient(SESSION_PATH, API_ID, API_HASH)
    except ImportError:
        logger.error("Telethon not installed: pip install telethon")
        return None


async def auth_interactive():
    """One-time interactive authentication. Creates .session file."""
    client = _get_client()
    if not client:
        return False

    await client.start()
    me = await client.get_me()
    print(f"✅ Authenticated as: {me.first_name} (@{me.username})")
    print(f"Session saved to: {SESSION_PATH}.session")
    await client.disconnect()
    return True


def is_authenticated() -> bool:
    """Check if session file exists."""
    return os.path.exists(f"{SESSION_PATH}.session")


async def collect_channel_history(
    username: str, days_back: int = 90, limit: int = 500
) -> Tuple[List[ParsedSignal], List[ChannelPost]]:
    """
    Collect messages from a channel using Telethon.

    Returns (parsed_signals, all_text_posts) — второй список для shadow raw_events
    (см. persist_shadow_telegram_posts_if_enabled, scraper=telethon).
    """
    if not is_authenticated():
        logger.warning("Telethon not authenticated. Run: python -m app.services.telethon_collector --auth")
        return [], []

    client = _get_client()
    if not client:
        return [], []

    signals: List[ParsedSignal] = []
    shadow_posts: List[ChannelPost] = []
    from app.core.config import get_settings

    full_mtproto = get_settings().SHADOW_TELETHON_FULL_MTPROTO
    try:
        await client.connect()
        if not await client.is_user_authorized():
            logger.warning("Session expired. Re-run auth.")
            return [], []

        entity = await client.get_entity(username)
        since = datetime.utcnow() - timedelta(days=days_back)

        async for message in client.iter_messages(entity, limit=limit, offset_date=datetime.utcnow()):
            if message.date.replace(tzinfo=None) < since:
                break
            if not message.text:
                continue

            msg_dt = message.date.replace(tzinfo=None) if message.date else None
            views = getattr(message, "views", None)
            mt_snapshot: Optional[Dict[str, Any]] = None
            if full_mtproto:
                try:
                    mt_snapshot = telethon_message_to_mtproto_dict(message)
                except Exception as exc:
                    logger.warning(
                        "Telethon mtproto snapshot failed id=%s: %s",
                        message.id,
                        exc,
                    )
            shadow_posts.append(
                ChannelPost(
                    text=message.text,
                    date=msg_dt,
                    message_id=str(message.id) if message.id is not None else None,
                    views=int(views) if views is not None else None,
                    mtproto=mt_snapshot,
                )
            )

            sig = parse_signal_from_text(message.text)
            if sig and sig.entry_price:
                sig.timestamp = msg_dt
                sig.original_text = message.text[:500]
                signals.append(sig)

        logger.info(
            "Telethon @%s: %s signals, %s text posts (last %s days)",
            username,
            len(signals),
            len(shadow_posts),
            days_back,
        )

    except Exception as e:
        logger.error(f"Telethon @{username}: {e}")
    finally:
        await client.disconnect()

    return signals, shadow_posts


async def collect_all_channels(usernames: List[str], days_back: int = 90) -> dict:
    """Collect from multiple channels."""
    results = {}
    total = 0
    for uname in usernames:
        sigs, _posts = await collect_channel_history(uname, days_back)
        results[uname] = len(sigs)
        total += len(sigs)
    return {"channels": len(usernames), "total_signals": total, "per_channel": results}


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    if "--auth" in sys.argv:
        print("=== Telethon Authentication ===")
        print(f"API_ID: {API_ID}")
        print(f"Session: {SESSION_PATH}")
        print("You will be asked for your phone number and SMS code.")
        print()
        asyncio.run(auth_interactive())

    elif "--check" in sys.argv:
        if is_authenticated():
            print(f"✅ Session file exists: {SESSION_PATH}.session")
        else:
            print("❌ Not authenticated. Run: python -m app.services.telethon_collector --auth")

    elif "--collect" in sys.argv:
        channels = sys.argv[sys.argv.index("--collect") + 1:] if len(sys.argv) > sys.argv.index("--collect") + 1 else ["binancekillers"]
        result = asyncio.run(collect_all_channels(channels, days_back=90))
        print(f"Result: {result}")

    else:
        print("Usage:")
        print("  --auth     One-time phone authentication")
        print("  --check    Check if authenticated")
        print("  --collect [channels...]  Collect signals")
