"""
Validate signal prices against real market data from CoinGecko.
"""
import logging
import httpx
from typing import Optional, Dict
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

CACHE_TTL = 300  # 5 minutes


COINGECKO_IDS = {
    "BTC": "bitcoin", "ETH": "ethereum", "BNB": "binancecoin",
    "SOL": "solana", "ADA": "cardano", "XRP": "ripple",
    "DOT": "polkadot", "DOGE": "dogecoin", "AVAX": "avalanche-2",
    "MATIC": "matic-network", "LINK": "chainlink", "UNI": "uniswap",
    "ATOM": "cosmos", "LTC": "litecoin", "NEAR": "near",
    "APT": "aptos", "ARB": "arbitrum", "OP": "optimism",
    "FTM": "fantom", "SUI": "sui", "INJ": "injective-protocol",
    "TIA": "celestia", "SEI": "sei-network", "AAVE": "aave",
    "SNX": "havven", "RUNE": "thorchain", "FET": "fetch-ai",
    "RENDER": "render-token", "TON": "the-open-network",
    "SHIB": "shiba-inu", "PEPE": "pepe",
}


async def get_current_price(symbol: str) -> Optional[float]:
    """Get current price for a crypto asset from CoinGecko."""
    pair = symbol.replace("/USDT", "").replace("/USD", "").upper()
    coingecko_id = COINGECKO_IDS.get(pair)
    if not coingecko_id:
        return None

    from app.services.redis_cache import cache_get, cache_set
    cached = cache_get(f"price:{pair}")
    if cached and "price" in cached:
        return cached["price"]

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"https://api.coingecko.com/api/v3/simple/price",
                params={"ids": coingecko_id, "vs_currencies": "usd"}
            )
            if resp.status_code == 200:
                data = resp.json()
                price = data.get(coingecko_id, {}).get("usd")
                if price:
                    cache_set(f"price:{pair}", {"price": price}, CACHE_TTL)
                    return price
    except Exception as e:
        logger.warning(f"CoinGecko price fetch failed for {pair}: {e}")

    return None


async def validate_signal_price(symbol: str, entry_price: float) -> dict:
    """Validate if a signal's entry price is reasonable vs current market."""
    current_price = await get_current_price(symbol)
    if current_price is None:
        return {"valid": True, "reason": "no_market_data", "current_price": None}

    deviation = abs(entry_price - current_price) / current_price * 100

    if deviation > 50:
        return {
            "valid": False,
            "reason": f"price_deviation_{deviation:.1f}%",
            "current_price": current_price,
            "deviation_pct": deviation,
        }

    return {
        "valid": True,
        "reason": "ok",
        "current_price": current_price,
        "deviation_pct": deviation,
    }
