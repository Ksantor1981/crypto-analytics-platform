#!/usr/bin/env python3
from pathlib import Path
import re
import sys


def fail(msg: str) -> None:
    print(f"[docs-sync] FAIL: {msg}")
    raise SystemExit(1)


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    readme = (root / "README.md").read_text(encoding="utf-8")

    if "Последнее обновление:" not in readme:
        fail("README must include 'Последнее обновление:'")

    required_links = [
        "SPEC_COMPLIANCE_2026_02_25.md",
        "docs/DATA_INTEGRITY_FIX.md",
    ]
    for link in required_links:
        if link not in readme:
            fail(f"README is missing required reference: {link}")

    banned_patterns = [
        r"\*\*87\.2%\*\*.*подтвержд",
        r"\b96%\b.*(точност|accuracy)",
    ]
    for pattern in banned_patterns:
        if re.search(pattern, readme, flags=re.IGNORECASE):
            fail(f"README contains banned metric pattern: {pattern}")

    print("[docs-sync] OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
