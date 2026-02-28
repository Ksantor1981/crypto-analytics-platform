#!/usr/bin/env python3
"""
Ручной запуск обучения ML-модели (train_from_db.py в ml-service).
Использует DATABASE_URL из конфига backend.

Запуск из корня проекта:
  python backend/scripts/run_ml_train.py

Или из backend:
  python scripts/run_ml_train.py
"""
import os
import sys
import subprocess
from pathlib import Path

# Add backend to path for get_settings
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.core.config import get_settings


def _get_ml_python(ml_service_dir: Path):
    """Use ml-service venv if present (has xgboost, psycopg2), else current Python."""
    if sys.platform == "win32":
        venv_py = ml_service_dir / ".venv" / "Scripts" / "python.exe"
    else:
        venv_py = ml_service_dir / ".venv" / "bin" / "python"
    if venv_py.exists():
        return str(venv_py)
    return sys.executable


def _database_url_for_host(db_url: str) -> str:
    """
    Для запуска на хосте (не в Docker): подменить хост postgres на localhost,
    порт привести к 5432, добавить имя БД если нет.
    В .env для Docker указан postgres:543 — с хоста так не подключиться.
    """
    if "@postgres" not in db_url and "@postgres:" not in db_url:
        return db_url
    try:
        from urllib.parse import urlparse, urlunparse
        p = urlparse(db_url)
        if p.port in (None, 543):
            netloc = f"{p.hostname or 'localhost'}:5432" if p.username else "localhost:5432"
        else:
            netloc = f"{p.hostname or 'localhost'}:{p.port}"
        if p.username:
            netloc = f"{p.username}:{p.password or ''}@{netloc}" if p.password else f"{p.username}@{netloc}"
        path = p.path if p.path and p.path != "/" else "/crypto_analytics"
        new_url = urlunparse((p.scheme, netloc.replace("postgres:", "localhost:").replace("@postgres", "@localhost"), path, p.params, p.query, p.fragment))
        return new_url
    except Exception:
        return db_url


def main():
    settings = get_settings()
    project_root = backend_dir.parent
    ml_service_dir = project_root / "ml-service"
    train_script = ml_service_dir / "train_from_db.py"
    if not train_script.exists():
        print(f"ERROR: {train_script} not found", file=sys.stderr)
        print("Run from project root: cd crypto-analytics-platform && python backend/scripts/run_ml_train.py", file=sys.stderr)
        print("Install deps: pip install -r ml-service/requirements-train.txt (or ml-service/requirements.txt)", file=sys.stderr)
        sys.exit(1)
    env = os.environ.copy()
    env["DATABASE_URL"] = _database_url_for_host(settings.database_url)
    python_exe = _get_ml_python(ml_service_dir)
    if python_exe != sys.executable:
        print("Using ml-service venv:", python_exe, file=sys.stderr)
    code = subprocess.run(
        [python_exe, str(train_script)],
        cwd=str(ml_service_dir),
        env=env,
    ).returncode
    sys.exit(code)


if __name__ == "__main__":
    main()
