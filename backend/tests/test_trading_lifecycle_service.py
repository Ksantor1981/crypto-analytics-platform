"""Граф переходов trading_lifecycle_status."""
from app.services.trading_lifecycle_service import can_transition, is_valid_status


def test_valid_status():
    assert is_valid_status("ACTIVE")
    assert not is_valid_status("nope")


def test_same_status_idempotent():
    assert can_transition("PENDING_ENTRY", "PENDING_ENTRY")


def test_pending_to_active():
    assert can_transition("PENDING_ENTRY", "ACTIVE")
    assert not can_transition("PENDING_ENTRY", "COMPLETED_TP")


def test_active_to_partial_and_terminal():
    assert can_transition("ACTIVE", "PARTIALLY_CLOSED")
    assert can_transition("ACTIVE", "COMPLETED_TP")
    assert not can_transition("ACTIVE", "PENDING_ENTRY")


def test_partially_closed_reopen_active():
    assert can_transition("PARTIALLY_CLOSED", "ACTIVE")


def test_terminal_locked():
    assert not can_transition("COMPLETED_TP", "ACTIVE")
    assert not can_transition("CANCELED", "ACTIVE")
