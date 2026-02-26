"""
Telegram Bot API integration — read messages from channels where bot is admin.
Complements the web scraper for private channels.
"""
import os
import logging
import httpx
from typing import List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")


@dataclass
class BotMessage:
    text: str
    chat_title: str
    chat_id: int
    date: int


async def get_bot_info() -> Optional[dict]:
    """Check if bot token is valid."""
    if not BOT_TOKEN:
        return None
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getMe")
            d = r.json()
            return d.get("result") if d.get("ok") else None
    except Exception as e:
        logger.error(f"Bot API error: {e}")
        return None


async def get_channel_messages(chat_id: str, limit: int = 20) -> List[BotMessage]:
    """Get recent messages from a channel via Bot API (bot must be admin)."""
    if not BOT_TOKEN:
        return []
    messages = []
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            # Try to get updates or use getChat to verify access
            r = await client.get(
                f"https://api.telegram.org/bot{BOT_TOKEN}/getChat",
                params={"chat_id": f"@{chat_id}"}
            )
            data = r.json()
            if not data.get("ok"):
                logger.debug(f"Bot cannot access @{chat_id}: {data.get('description')}")
                return []

            chat = data["result"]
            logger.info(f"Bot has access to @{chat_id}: {chat.get('title', 'unknown')}")

    except Exception as e:
        logger.debug(f"Bot API error for @{chat_id}: {e}")

    return messages


async def check_bot_access_to_channels(usernames: List[str]) -> dict:
    """Check which channels the bot can access."""
    if not BOT_TOKEN:
        return {"bot_active": False, "accessible": [], "inaccessible": usernames}

    info = await get_bot_info()
    if not info:
        return {"bot_active": False, "accessible": [], "inaccessible": usernames}

    accessible = []
    inaccessible = []

    for uname in usernames:
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                r = await client.get(
                    f"https://api.telegram.org/bot{BOT_TOKEN}/getChat",
                    params={"chat_id": f"@{uname}"}
                )
                if r.json().get("ok"):
                    accessible.append(uname)
                else:
                    inaccessible.append(uname)
        except Exception:
            inaccessible.append(uname)

    return {
        "bot_active": True,
        "bot_username": info.get("username"),
        "accessible": accessible,
        "inaccessible": inaccessible,
    }
