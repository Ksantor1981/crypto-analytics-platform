"""
Repeatable migration check for staging/prod-like environments.

Scenario:
1) Drop/recreate public schema (partial reset simulation)
2) Run alembic upgrade head
3) Print current revision

Usage (inside backend container):
    python scripts/check_partial_reset_upgrade.py --yes
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys

from sqlalchemy import create_engine, text


def run(cmd: list[str]) -> None:
    proc = subprocess.run(cmd, check=False)
    if proc.returncode != 0:
        raise SystemExit(proc.returncode)


def main() -> int:
    parser = argparse.ArgumentParser(description="Check alembic upgrade after partial reset.")
    parser.add_argument("--yes", action="store_true", help="Confirm destructive schema reset.")
    args = parser.parse_args()

    if not args.yes:
        print("Refusing to run without --yes (this drops schema public).", file=sys.stderr)
        return 2

    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("DATABASE_URL is not set.", file=sys.stderr)
        return 2

    print("[1/3] Resetting schema public...")
    engine = create_engine(database_url)
    with engine.connect() as conn:
        conn.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))
        conn.commit()

    print("[2/3] Running alembic upgrade head...")
    run(["alembic", "upgrade", "head"])

    print("[3/3] Current alembic revision:")
    run(["alembic", "current", "-v"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
