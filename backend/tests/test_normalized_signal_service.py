"""Правила материализации NormalizedSignal без БД."""
from unittest.mock import MagicMock

from app.services.normalized_signal_service import eligible_for_materialization


def _ex(fields, classification="PARSED"):
    ex = MagicMock()
    ex.classification_status = classification
    ex.extracted_fields = fields
    return ex


def _dec(decision_type="signal"):
    d = MagicMock()
    d.decision_type = decision_type
    return d


def test_eligible_full():
    assert eligible_for_materialization(
        _ex({"asset": "BTC", "direction": "LONG", "entry_price": 1.0}),
        _dec("signal"),
    ) is True


def test_eligible_requires_signal_decision():
    assert not eligible_for_materialization(
        _ex({"asset": "BTC", "direction": "LONG", "entry_price": 1.0}),
        _dec("noise"),
    )


def test_eligible_requires_parsed():
    assert not eligible_for_materialization(
        _ex({"asset": "BTC", "direction": "LONG", "entry_price": 1.0}, classification="AMBIGUOUS"),
        _dec("signal"),
    )


def test_eligible_requires_fields():
    assert not eligible_for_materialization(_ex({}), _dec("signal"))
    assert not eligible_for_materialization(
        _ex({"asset": "", "direction": "LONG", "entry_price": 1}),
        _dec("signal"),
    )
