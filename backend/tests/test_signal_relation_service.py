"""signal_relation_service без БД — граничные случаи."""
from unittest.mock import MagicMock

from app.services.signal_relation_service import create_signal_relation


def test_create_relation_same_id_returns_none():
    db = MagicMock()
    assert create_signal_relation(db, from_normalized_signal_id=1, to_normalized_signal_id=1, relation_type="update_to") is None


def test_create_relation_bad_type_returns_none():
    db = MagicMock()
    assert (
        create_signal_relation(db, from_normalized_signal_id=1, to_normalized_signal_id=2, relation_type="nope")
        is None
    )
