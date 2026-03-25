#!/usr/bin/env python3
"""
Проверка живости API на реальном стеке (Docker / локально).
Запуск с хоста:  python scripts/smoke_real_services.py
Из контейнера backend:  python scripts/smoke_real_services.py --base-url http://localhost:8000
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request


def get_json(url: str, timeout: float = 15.0):
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode())


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument(
        "--base-url",
        default="http://127.0.0.1:8000",
        help="Базовый URL API (с хоста при docker-compose: http://127.0.0.1:8000)",
    )
    args = p.parse_args()
    base = args.base_url.rstrip("/")

    ok = True
    for path, name in [
        ("/health", "health"),
        ("/ready", "ready"),
        ("/", "root"),
    ]:
        url = f"{base}{path}"
        try:
            data = get_json(url)
            print(f"OK {name}: {url}")
            if path == "/health" and isinstance(data, dict):
                svc = data.get("services") or {}
                print(f"    database={svc.get('database')} redis={svc.get('redis')} ml_service={svc.get('ml_service')}")
            if path == "/" and isinstance(data, dict):
                feat = (data.get("features") or {})
                print(f"    ml_service(reachable)={feat.get('ml_service')}")
        except urllib.error.HTTPError as e:
            print(f"FAIL {name}: HTTP {e.code} {url}", file=sys.stderr)
            ok = False
        except Exception as e:
            print(f"FAIL {name}: {e} ({url})", file=sys.stderr)
            ok = False

    print()
    if ok:
        print("All probes OK. Signal collection runs inside backend container (see crypto-analytics-backend logs).")
        return 0
    print("Some probes failed: check docker compose and port mapping.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
