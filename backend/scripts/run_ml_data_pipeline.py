"""
Оркестрация фазы C: свечи → индикаторы → real_signals (опц.) → обучение ML.

Соответствует порядку в docs/ML_DATA_EXECUTION_CHECKLIST.md.
Запуск из каталога backend (нужны DATABASE_URL и сеть для Binance):

  python scripts/run_ml_data_pipeline.py
  python scripts/run_ml_data_pipeline.py --dry-run
  python scripts/run_ml_data_pipeline.py --skip-train --days 90

Обучение выполняется в ml-service/train_from_db.py (тот же DATABASE_URL).
"""
from __future__ import annotations

import argparse
import logging
import os
import subprocess
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

_BACKEND = Path(__file__).resolve().parent.parent
_SCRIPTS = _BACKEND / "scripts"
_REPO_ROOT = _BACKEND.parent
_ML_SERVICE = _REPO_ROOT / "ml-service"
_TRAIN = _ML_SERVICE / "train_from_db.py"


def _load_dotenv() -> None:
    env_file = _REPO_ROOT / ".env"
    if not env_file.is_file():
        return
    try:
        from dotenv import load_dotenv

        load_dotenv(env_file)
    except ImportError:
        pass


def _run(
    label: str,
    cmd: list[str],
    *,
    cwd: Path | None,
    dry_run: bool,
) -> int:
    if dry_run:
        logger.info("[dry-run] %s: %s (cwd=%s)", label, " ".join(cmd), cwd or ".")
        return 0
    logger.info("=== %s ===", label)
    r = subprocess.run(cmd, cwd=str(cwd) if cwd else None, env=os.environ.copy())
    if r.returncode != 0:
        logger.error("Step failed: %s (exit %s)", label, r.returncode)
    return r.returncode


def main() -> int:
    parser = argparse.ArgumentParser(description="ML data pipeline (phase C)")
    parser.add_argument(
        "--symbols",
        nargs="+",
        default=["BTCUSDT", "ETHUSDT"],
        help="Пары для свечей/индикаторов/сигналов",
    )
    parser.add_argument("--days", type=int, default=180, help="Глубина свечей (fetch)")
    parser.add_argument("--interval", default="1h", help="Таймфрейм свечей")
    parser.add_argument("--skip-fetch", action="store_true")
    parser.add_argument("--skip-indicators", action="store_true")
    parser.add_argument("--skip-signals", action="store_true", help="Пропустить generate_real_signals")
    parser.add_argument("--skip-train", action="store_true", help="Пропустить ml-service/train_from_db.py")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    _load_dotenv()
    py = sys.executable
    sym_args = ["--symbols", *args.symbols]

    if not args.skip_fetch:
        cmd = [
            py,
            str(_SCRIPTS / "fetch_market_data.py"),
            *sym_args,
            "--days",
            str(args.days),
            "--interval",
            args.interval,
        ]
        if _run("1. fetch_market_data", cmd, cwd=_BACKEND, dry_run=args.dry_run) != 0:
            return 1

    if not args.skip_indicators:
        cmd = [
            py,
            str(_SCRIPTS / "calculate_indicators.py"),
            *sym_args,
            "--interval",
            args.interval,
        ]
        if _run("2. calculate_indicators", cmd, cwd=_BACKEND, dry_run=args.dry_run) != 0:
            return 1

    if not args.skip_signals:
        cmd = [
            py,
            str(_SCRIPTS / "generate_real_signals.py"),
            *sym_args,
            "--interval",
            args.interval,
        ]
        if _run("3. generate_real_signals", cmd, cwd=_BACKEND, dry_run=args.dry_run) != 0:
            return 1

    if not args.skip_train:
        if not _TRAIN.is_file():
            logger.error("Не найден %s", _TRAIN)
            return 1
        cmd = [py, str(_TRAIN)]
        if _run("4. train_from_db (ml-service)", cmd, cwd=_ML_SERVICE, dry_run=args.dry_run) != 0:
            return 1

    logger.info("Pipeline finished OK.")
    logger.info("Update docs/ML_METRIC_LATEST.md after successful train (see checklist).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
