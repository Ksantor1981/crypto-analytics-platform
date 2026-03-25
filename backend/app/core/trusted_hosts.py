"""Список доверенных Host для TrustedHostMiddleware (имена хостов, не full URL)."""
from __future__ import annotations

from typing import List, Set
from urllib.parse import urlparse


def build_trusted_hosts(
    explicit: str | None,
    cors_origins: List[str] | None,
) -> List[str]:
    """
    TRUSTED_HOSTS env: comma-separated hostnames.
    Иначе — hostname из BACKEND_CORS_ORIGINS + служебные имена Docker/локали.
    """
    if explicit and explicit.strip() and explicit.strip() != "*":
        return [h.strip().lower() for h in explicit.split(",") if h.strip()]

    hosts: Set[str] = {
        "localhost",
        "127.0.0.1",
        "backend",
        "frontend",
        "ml-service",
        "nginx",
        "0.0.0.0",
    }
    for origin in cors_origins or []:
        if not origin or not isinstance(origin, str):
            continue
        try:
            p = urlparse(origin)
            h = (p.hostname or "").lower()
            if h:
                hosts.add(h)
        except Exception:
            continue
    return sorted(hosts)
