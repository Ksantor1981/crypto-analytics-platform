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
from typing import List, Optional
from app.services.telegram_scraper import ParsedSignal, parse_signal_from_text

logger = logging.getLogger(__name__)

API_ID = int(os.getenv("TELEGRAM_API_ID", "21073808"))
API_HASH = os.getenv("TELEGRAM_API_HASH", "2e3adb8940912dd295fe20c1d2ce5368")
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
) -> List[ParsedSignal]:
    """Collect messages from a channel using Telethon."""
    if not is_authenticated():
        logger.warning("Telethon not authenticated. Run: python -m app.services.telethon_collector --auth")
        return []

    client = _get_client()
    if not client:
        return []

    signals = []
    try:
        await client.connect()
        if not await client.is_user_authorized():
            logger.warning("Session expired. Re-run auth.")
            return []

        from telethon.tl.functions.messages import GetHistoryRequest
        entity = await client.get_entity(username)
        since = datetime.utcnow() - timedelta(days=days_back)

        async for message in client.iter_messages(entity, limit=limit, offset_date=datetime.utcnow()):
            if message.date.replace(tzinfo=None) < since:
                break
            if not message.text:
                continue

            sig = parse_signal_from_text(message.text)
            if sig and sig.entry_price:
                sig.timestamp = message.date.replace(tzinfo=None)
                sig.original_text = message.text[:500]
                signals.append(sig)

        logger.info(f"Telethon @{username}: {len(signals)} signals (last {days_back} days)")

    except Exception as e:
        logger.error(f"Telethon @{username}: {e}")
    finally:
        await client.disconnect()

    return signals


async def collect_all_channels(usernames: List[str], days_back: int = 90) -> dict:
    """Collect from multiple channels."""
    results = {}
    total = 0
    for uname in usernames:
        sigs = await collect_channel_history(uname, days_back)
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
