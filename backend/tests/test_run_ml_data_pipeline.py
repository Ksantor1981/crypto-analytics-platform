"""Dry-run оркестратора ML pipeline (без Binance/БД)."""
import os
import subprocess
import sys
from pathlib import Path

import pytest

_BACKEND = Path(__file__).resolve().parent.parent
_SCRIPT = _BACKEND / "scripts" / "run_ml_data_pipeline.py"


@pytest.mark.skipif(not _SCRIPT.is_file(), reason="pipeline script missing")
def test_ml_data_pipeline_dry_run_zero_exit():
    env = os.environ.copy()
    env.setdefault("SECRET_KEY", "test-secret-key-32-chars-minimum")
    r = subprocess.run(
        [
            sys.executable,
            str(_SCRIPT),
            "--dry-run",
            "--skip-train",
            "--symbols",
            "BTCUSDT",
        ],
        cwd=str(_BACKEND),
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert r.returncode == 0, r.stderr + r.stdout
    out = (r.stdout or "") + (r.stderr or "")
    assert "dry-run" in out.lower() or "fetch_market_data" in out
