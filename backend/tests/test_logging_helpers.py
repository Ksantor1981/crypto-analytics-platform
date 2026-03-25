"""Покрытие app.core.logging — вспомогательные функции логирования (ТЗ: наблюдаемость)."""
import pytest

from app.core.logging import (
    get_logger,
    log_authentication_attempt,
    log_security_event,
    log_api_request,
    log_signal_processing,
)


def test_get_logger_returns_bound_logger():
    log = get_logger("pytest_logging")
    assert log is not None
    # structlog BoundLogger
    assert hasattr(log, "info")


def test_log_authentication_attempt_success_with_ua():
    log_authentication_attempt(
        "user@example.com",
        True,
        "127.0.0.1",
        user_agent="pytest",
        additional_data={"source": "test"},
    )


def test_log_authentication_attempt_failure_minimal():
    log_authentication_attempt("bad@example.com", False, "10.0.0.1")


def test_log_security_event_with_details():
    log_security_event(
        "suspicious_login",
        user_id=42,
        ip_address="192.168.1.1",
        details={"attempts": 5},
    )


def test_log_security_event_minimal():
    log_security_event("generic")


def test_log_api_request_full():
    log_api_request(
        "POST",
        "/api/v1/signals",
        user_id=1,
        ip_address="203.0.113.1",
        response_status=201,
        response_time_ms=45.2,
    )


def test_log_api_request_minimal():
    log_api_request("GET", "/health")


def test_log_signal_processing_success_and_failure():
    log_signal_processing(999, "validate", True, details={"channel_id": 1})
    log_signal_processing(1000, "validate", False)
