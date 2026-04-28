"""
Exchange service for Bybit/Binance trading operations.

The safe default is paper trading. Real exchange calls are enabled only when
EXCHANGE_LIVE_TRADING_ENABLED=true and EXCHANGE_PAPER_MODE=false.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import time
from decimal import Decimal
from typing import Any, Dict, Optional
from urllib.parse import urlencode

import aiohttp
import requests

from app.core.config import get_settings
from app.models.trading import ExchangeType

logger = logging.getLogger(__name__)


class ExchangeService:
    """Service for interacting with cryptocurrency exchanges."""

    def __init__(self):
        self.settings = get_settings()
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    def _is_paper_mode(self) -> bool:
        live = bool(getattr(self.settings, "EXCHANGE_LIVE_TRADING_ENABLED", False))
        paper = bool(getattr(self.settings, "EXCHANGE_PAPER_MODE", True))
        return paper or not live

    def _recv_window(self) -> int:
        return int(getattr(self.settings, "EXCHANGE_RECV_WINDOW_MS", 5000))

    def _timeout(self) -> int:
        return int(getattr(self.settings, "EXCHANGE_HTTP_TIMEOUT_SECONDS", 10))

    def _binance_base_url(self) -> str:
        return str(getattr(self.settings, "EXCHANGE_BINANCE_BASE_URL", "https://api.binance.com")).rstrip("/")

    def _bybit_base_url(self) -> str:
        return str(getattr(self.settings, "EXCHANGE_BYBIT_BASE_URL", "https://api.bybit.com")).rstrip("/")

    @staticmethod
    def _sign_query(api_secret: str, params: Dict[str, Any]) -> str:
        query_string = urlencode(params)
        return hmac.new(
            api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    def _signed_binance_params(self, api_secret: str, params: Dict[str, Any]) -> Dict[str, Any]:
        signed = {
            **params,
            "timestamp": int(time.time() * 1000),
            "recvWindow": self._recv_window(),
        }
        signed["signature"] = self._sign_query(api_secret, signed)
        return signed

    def _signed_bybit_headers(self, api_key: str, api_secret: str, payload: str) -> Dict[str, str]:
        timestamp = str(int(time.time() * 1000))
        recv_window = str(self._recv_window())
        signature_payload = f"{timestamp}{api_key}{recv_window}{payload}"
        signature = hmac.new(
            api_secret.encode("utf-8"),
            signature_payload.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        return {
            "X-BAPI-API-KEY": api_key,
            "X-BAPI-TIMESTAMP": timestamp,
            "X-BAPI-RECV-WINDOW": recv_window,
            "X-BAPI-SIGN": signature,
            "X-BAPI-SIGN-TYPE": "2",
            "Content-Type": "application/json",
        }

    async def _request_json(
        self,
        method: str,
        url: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        json_body: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        timeout = aiohttp.ClientTimeout(total=self._timeout())
        owns_session = self.session is None
        session = self.session or aiohttp.ClientSession(timeout=timeout)
        try:
            async with session.request(
                method,
                url,
                params=params,
                json=json_body,
                headers=headers,
                timeout=timeout,
            ) as response:
                text = await response.text()
                payload = json.loads(text) if text else {}
                if response.status >= 400:
                    raise RuntimeError(f"Exchange HTTP {response.status}: {payload}")
                return payload
        finally:
            if owns_session:
                await session.close()

    def _request_json_sync(
        self,
        method: str,
        url: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        json_body: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        response = requests.request(
            method,
            url,
            params=params,
            json=json_body,
            headers=headers,
            timeout=self._timeout(),
        )
        payload = response.json() if response.text else {}
        if response.status_code >= 400:
            raise RuntimeError(f"Exchange HTTP {response.status_code}: {payload}")
        return payload

    @staticmethod
    def _raise_for_bybit(payload: Dict[str, Any]) -> None:
        if int(payload.get("retCode", 0)) != 0:
            raise RuntimeError(f"Bybit error: {payload}")

    @staticmethod
    def _paper_order_id(exchange: str) -> str:
        return f"paper_{exchange}_{int(time.time())}"

    @staticmethod
    def _normalize_bybit_side(side: str) -> str:
        normalized = side.upper()
        if normalized == "BUY":
            return "Buy"
        if normalized == "SELL":
            return "Sell"
        raise ValueError(f"Unsupported order side: {side}")

    @staticmethod
    def _normalize_bybit_order_type(order_type: str) -> str:
        normalized = order_type.upper()
        if normalized == "MARKET":
            return "Market"
        if normalized == "LIMIT":
            return "Limit"
        raise ValueError(f"Unsupported order type: {order_type}")

    def validate_credentials(
        self,
        exchange: ExchangeType,
        api_key: str,
        api_secret: str,
        passphrase: Optional[str] = None,
    ) -> bool:
        """Validate API credentials with the exchange."""
        try:
            if exchange == ExchangeType.BYBIT:
                return self._validate_bybit_credentials(api_key, api_secret)
            if exchange == ExchangeType.BINANCE:
                return self._validate_binance_credentials(api_key, api_secret)
            logger.warning("Unsupported exchange: %s", exchange)
            return False
        except Exception:
            logger.exception("Error validating credentials for %s", exchange)
            return False

    def _validate_bybit_credentials(self, api_key: str, api_secret: str) -> bool:
        if self._is_paper_mode():
            logger.warning("[PAPER] Bybit credentials validation skipped")
            return True

        query = urlencode({"accountType": "UNIFIED"})
        payload = self._request_json_sync(
            "GET",
            f"{self._bybit_base_url()}/v5/account/wallet-balance",
            params={"accountType": "UNIFIED"},
            headers=self._signed_bybit_headers(api_key, api_secret, query),
        )
        self._raise_for_bybit(payload)
        return True

    def _validate_binance_credentials(self, api_key: str, api_secret: str) -> bool:
        if self._is_paper_mode():
            logger.warning("[PAPER] Binance credentials validation skipped")
            return True

        params = self._signed_binance_params(api_secret, {})
        self._request_json_sync(
            "GET",
            f"{self._binance_base_url()}/api/v3/account",
            params=params,
            headers={"X-MBX-APIKEY": api_key},
        )
        return True

    async def place_order(
        self,
        exchange: ExchangeType,
        api_key: str,
        api_secret: str,
        passphrase: Optional[str],
        symbol: str,
        side: str,
        order_type: str,
        quantity: Decimal,
        price: Optional[Decimal] = None,
        time_in_force: str = "GTC",
    ) -> Dict[str, Any]:
        """Place an order on the exchange."""
        if exchange == ExchangeType.BYBIT:
            return await self._place_bybit_order(api_key, api_secret, symbol, side, order_type, quantity, price, time_in_force)
        if exchange == ExchangeType.BINANCE:
            return await self._place_binance_order(api_key, api_secret, symbol, side, order_type, quantity, price, time_in_force)
        raise ValueError(f"Unsupported exchange: {exchange}")

    async def _place_bybit_order(
        self,
        api_key: str,
        api_secret: str,
        symbol: str,
        side: str,
        order_type: str,
        quantity: Decimal,
        price: Optional[Decimal],
        time_in_force: str,
    ) -> Dict[str, Any]:
        if self._is_paper_mode():
            logger.warning("[PAPER] Bybit order NOT sent: %s %s %s", symbol, side, quantity)
            return {
                "mode": "paper",
                "exchange": "bybit",
                "order_id": self._paper_order_id("bybit"),
                "client_order_id": f"paper_client_{int(time.time())}",
                "symbol": symbol,
                "side": side,
                "order_type": order_type,
                "quantity": quantity,
                "price": price,
                "status": "NEW",
                "timestamp": int(time.time() * 1000),
            }

        body: Dict[str, Any] = {
            "category": "linear",
            "symbol": symbol,
            "side": self._normalize_bybit_side(side),
            "orderType": self._normalize_bybit_order_type(order_type),
            "qty": str(quantity),
        }
        if body["orderType"] == "Limit":
            if price is None:
                raise ValueError("Limit order requires price")
            body["price"] = str(price)
            body["timeInForce"] = time_in_force

        body_text = json.dumps(body, separators=(",", ":"))
        payload = await self._request_json(
            "POST",
            f"{self._bybit_base_url()}/v5/order/create",
            json_body=body,
            headers=self._signed_bybit_headers(api_key, api_secret, body_text),
        )
        self._raise_for_bybit(payload)
        result = payload.get("result", {})
        return {
            "mode": "live",
            "exchange": "bybit",
            "order_id": result.get("orderId"),
            "client_order_id": result.get("orderLinkId"),
            "symbol": symbol,
            "side": side,
            "order_type": order_type,
            "quantity": quantity,
            "price": price,
            "status": "NEW",
            "raw": payload,
        }

    async def _place_binance_order(
        self,
        api_key: str,
        api_secret: str,
        symbol: str,
        side: str,
        order_type: str,
        quantity: Decimal,
        price: Optional[Decimal],
        time_in_force: str,
    ) -> Dict[str, Any]:
        if self._is_paper_mode():
            logger.warning("[PAPER] Binance order NOT sent: %s %s %s", symbol, side, quantity)
            return {
                "mode": "paper",
                "exchange": "binance",
                "orderId": self._paper_order_id("binance"),
                "clientOrderId": f"paper_client_{int(time.time())}",
                "symbol": symbol,
                "side": side,
                "type": order_type,
                "quantity": quantity,
                "price": price,
                "status": "NEW",
                "timestamp": int(time.time() * 1000),
            }

        params: Dict[str, Any] = {
            "symbol": symbol,
            "side": side.upper(),
            "type": order_type.upper(),
            "quantity": str(quantity),
        }
        if params["type"] == "LIMIT":
            if price is None:
                raise ValueError("Limit order requires price")
            params["price"] = str(price)
            params["timeInForce"] = time_in_force

        payload = await self._request_json(
            "POST",
            f"{self._binance_base_url()}/api/v3/order",
            params=self._signed_binance_params(api_secret, params),
            headers={"X-MBX-APIKEY": api_key},
        )
        return {
            "mode": "live",
            "exchange": "binance",
            "orderId": payload.get("orderId"),
            "clientOrderId": payload.get("clientOrderId"),
            "symbol": payload.get("symbol", symbol),
            "side": payload.get("side", side.upper()),
            "type": payload.get("type", order_type.upper()),
            "quantity": quantity,
            "price": price,
            "status": payload.get("status", "NEW"),
            "raw": payload,
        }

    async def get_current_price(
        self,
        exchange: ExchangeType,
        api_key: str,
        api_secret: str,
        passphrase: Optional[str],
        symbol: str,
    ) -> Optional[Decimal]:
        """Get current price for a symbol."""
        try:
            if exchange == ExchangeType.BYBIT:
                return await self._get_bybit_price(symbol)
            if exchange == ExchangeType.BINANCE:
                return await self._get_binance_price(symbol)
            logger.warning("Unsupported exchange for price: %s", exchange)
            return None
        except Exception:
            logger.exception("Error getting price from %s", exchange)
            return None

    async def _get_bybit_price(self, symbol: str) -> Optional[Decimal]:
        if self._is_paper_mode():
            base_price = 50000 if "BTC" in symbol else 3000 if "ETH" in symbol else 100
            logger.warning("[PAPER] Bybit price for %s: %s", symbol, base_price)
            return Decimal(str(base_price))

        payload = await self._request_json(
            "GET",
            f"{self._bybit_base_url()}/v5/market/tickers",
            params={"category": "linear", "symbol": symbol},
        )
        self._raise_for_bybit(payload)
        items = payload.get("result", {}).get("list", [])
        if not items:
            return None
        return Decimal(str(items[0]["lastPrice"]))

    async def _get_binance_price(self, symbol: str) -> Optional[Decimal]:
        if self._is_paper_mode():
            base_price = 50000 if "BTC" in symbol else 3000 if "ETH" in symbol else 100
            logger.warning("[PAPER] Binance price for %s: %s", symbol, base_price)
            return Decimal(str(base_price))

        payload = await self._request_json(
            "GET",
            f"{self._binance_base_url()}/api/v3/ticker/price",
            params={"symbol": symbol},
        )
        return Decimal(str(payload["price"]))

    async def get_account_balance(
        self,
        exchange: ExchangeType,
        api_key: str,
        api_secret: str,
        passphrase: Optional[str],
    ) -> Dict[str, Any]:
        """Get account balance from exchange."""
        try:
            if exchange == ExchangeType.BYBIT:
                return await self._get_bybit_balance(api_key, api_secret)
            if exchange == ExchangeType.BINANCE:
                return await self._get_binance_balance(api_key, api_secret)
            logger.warning("Unsupported exchange for balance: %s", exchange)
            return {}
        except Exception:
            logger.exception("Error getting balance from %s", exchange)
            return {}

    async def _get_bybit_balance(self, api_key: str, api_secret: str) -> Dict[str, Any]:
        if self._is_paper_mode():
            logger.warning("[PAPER] Bybit balance returned as paper stub")
            return {
                "mode": "paper",
                "exchange": "bybit",
                "total_balance": 10000.0,
                "available_balance": 9500.0,
                "used_balance": 500.0,
                "currencies": {
                    "USDT": {"total": 10000.0, "available": 9500.0},
                    "BTC": {"total": 0.1, "available": 0.09},
                    "ETH": {"total": 1.5, "available": 1.4},
                },
            }

        query = urlencode({"accountType": "UNIFIED"})
        payload = await self._request_json(
            "GET",
            f"{self._bybit_base_url()}/v5/account/wallet-balance",
            params={"accountType": "UNIFIED"},
            headers=self._signed_bybit_headers(api_key, api_secret, query),
        )
        self._raise_for_bybit(payload)
        accounts = payload.get("result", {}).get("list", [])
        coins = accounts[0].get("coin", []) if accounts else []
        currencies = {
            coin.get("coin"): {
                "total": float(coin.get("walletBalance") or 0),
                "available": float(coin.get("availableToWithdraw") or coin.get("walletBalance") or 0),
            }
            for coin in coins
            if coin.get("coin")
        }
        total_balance = sum(item["total"] for item in currencies.values())
        available_balance = sum(item["available"] for item in currencies.values())
        return {
            "mode": "live",
            "exchange": "bybit",
            "total_balance": total_balance,
            "available_balance": available_balance,
            "used_balance": max(total_balance - available_balance, 0),
            "currencies": currencies,
            "raw": payload,
        }

    async def _get_binance_balance(self, api_key: str, api_secret: str) -> Dict[str, Any]:
        if self._is_paper_mode():
            logger.warning("[PAPER] Binance balance returned as paper stub")
            return {
                "mode": "paper",
                "exchange": "binance",
                "total_balance": 10000.0,
                "available_balance": 9500.0,
                "used_balance": 500.0,
                "currencies": {
                    "USDT": {"total": 10000.0, "available": 9500.0},
                    "BTC": {"total": 0.1, "available": 0.09},
                    "ETH": {"total": 1.5, "available": 1.4},
                },
            }

        payload = await self._request_json(
            "GET",
            f"{self._binance_base_url()}/api/v3/account",
            params=self._signed_binance_params(api_secret, {}),
            headers={"X-MBX-APIKEY": api_key},
        )
        balances = payload.get("balances", [])
        currencies = {
            item["asset"]: {
                "total": float(item.get("free", 0)) + float(item.get("locked", 0)),
                "available": float(item.get("free", 0)),
            }
            for item in balances
            if float(item.get("free", 0)) or float(item.get("locked", 0))
        }
        total_balance = sum(item["total"] for item in currencies.values())
        available_balance = sum(item["available"] for item in currencies.values())
        return {
            "mode": "live",
            "exchange": "binance",
            "total_balance": total_balance,
            "available_balance": available_balance,
            "used_balance": max(total_balance - available_balance, 0),
            "currencies": currencies,
            "raw": payload,
        }

    async def cancel_order(
        self,
        exchange: ExchangeType,
        api_key: str,
        api_secret: str,
        passphrase: Optional[str],
        symbol: str,
        order_id: str,
    ) -> bool:
        """Cancel an order on the exchange."""
        try:
            if exchange == ExchangeType.BYBIT:
                return await self._cancel_bybit_order(api_key, api_secret, symbol, order_id)
            if exchange == ExchangeType.BINANCE:
                return await self._cancel_binance_order(api_key, api_secret, symbol, order_id)
            logger.warning("Unsupported exchange for cancel: %s", exchange)
            return False
        except Exception:
            logger.exception("Error canceling order on %s", exchange)
            return False

    async def _cancel_bybit_order(self, api_key: str, api_secret: str, symbol: str, order_id: str) -> bool:
        if self._is_paper_mode():
            logger.warning("[PAPER] Bybit order cancel skipped: %s", order_id)
            return True

        body = {"category": "linear", "symbol": symbol, "orderId": order_id}
        body_text = json.dumps(body, separators=(",", ":"))
        payload = await self._request_json(
            "POST",
            f"{self._bybit_base_url()}/v5/order/cancel",
            json_body=body,
            headers=self._signed_bybit_headers(api_key, api_secret, body_text),
        )
        self._raise_for_bybit(payload)
        return True

    async def _cancel_binance_order(self, api_key: str, api_secret: str, symbol: str, order_id: str) -> bool:
        if self._is_paper_mode():
            logger.warning("[PAPER] Binance order cancel skipped: %s", order_id)
            return True

        params = self._signed_binance_params(api_secret, {"symbol": symbol, "orderId": order_id})
        await self._request_json(
            "DELETE",
            f"{self._binance_base_url()}/api/v3/order",
            params=params,
            headers={"X-MBX-APIKEY": api_key},
        )
        return True
