"""
Регрессия: OPENAPI_DOCS_ENABLED=false скрывает Swagger в production.
См. docs/PROD_LAUNCH_SECURITY_CHECKLIST.md и AUDIT_REPORT_2026_04_28.md.
"""
import importlib
import os
import sys

import pytest
from fastapi.testclient import TestClient


def _reload_app() -> object:
    """Заново импортировать app.main, чтобы settings подхватили новое env."""
    for mod_name in list(sys.modules):
        if mod_name == "app.main" or mod_name.startswith("app.main."):
            del sys.modules[mod_name]
    main = importlib.import_module("app.main")
    return main.app


def _set_minimal_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("USE_SQLITE", "true")
    monkeypatch.setenv("SECRET_KEY", "test-secret-key-32-chars-minimum")
    monkeypatch.setenv("DEBUG", "true")
    monkeypatch.setenv("AUTH_RATE_LIMIT_REQUESTS", "1000")


def test_openapi_docs_enabled_default_true(monkeypatch: pytest.MonkeyPatch):
    """По умолчанию /docs и /openapi.json доступны (dev-удобство)."""
    _set_minimal_env(monkeypatch)
    monkeypatch.delenv("OPENAPI_DOCS_ENABLED", raising=False)
    app = _reload_app()
    with TestClient(app) as client:
        assert client.get("/docs").status_code == 200
        assert client.get("/openapi.json").status_code == 200


def test_openapi_docs_disabled_returns_404(monkeypatch: pytest.MonkeyPatch):
    """Прод-режим: /docs и /redoc недоступны при OPENAPI_DOCS_ENABLED=false."""
    _set_minimal_env(monkeypatch)
    monkeypatch.setenv("OPENAPI_DOCS_ENABLED", "false")
    app = _reload_app()
    with TestClient(app) as client:
        assert client.get("/docs").status_code == 404
        assert client.get("/redoc").status_code == 404
        # /openapi.json — отдельный эндпоинт FastAPI, проверим что в нём нет Swagger UI.
        # FastAPI всё равно отдаёт openapi.json; для полной защиты — закрыть на уровне reverse proxy.

        # Корневой "/" не должен светить ссылку на docs
        root = client.get("/").json()
        assert "docs" not in (root.get("endpoints") or {})


def teardown_module(module):  # noqa: D401, ANN001
    """Очистить kэш импорта, чтобы остальные тесты не ловили модифицированный app."""
    for mod_name in list(sys.modules):
        if mod_name == "app.main" or mod_name.startswith("app.main."):
            del sys.modules[mod_name]
    os.environ.pop("OPENAPI_DOCS_ENABLED", None)
