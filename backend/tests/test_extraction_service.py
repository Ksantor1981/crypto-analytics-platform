"""Классификация extraction без БД."""
from app.services.extraction_service import (
    classify_and_fields,
    map_classification_to_decision_type,
)


def test_map_classification_to_decision():
    assert map_classification_to_decision_type("PARSED") == "signal"
    assert map_classification_to_decision_type("NOISE") == "noise"
    assert map_classification_to_decision_type("UNRESOLVED") == "unresolved"
    assert map_classification_to_decision_type("AMBIGUOUS") == "unresolved"
    assert map_classification_to_decision_type("UNKNOWN") == "unresolved"


def test_classify_whitespace_noise():
    status, conf, fields = classify_and_fields("  \n\t  ")
    assert status == "NOISE"
    assert conf is None
    assert fields == {}


def test_classify_non_signal_unresolved():
    status, conf, fields = classify_and_fields("Good morning everyone!")
    assert status == "UNRESOLVED"
    assert conf is None
    assert fields == {}


def test_classify_trading_text_parsed():
    text = "#BTC LONG entry $65000 TP $72000 SL $63000"
    status, conf, fields = classify_and_fields(text)
    assert status == "PARSED"
    assert conf is not None
    assert fields.get("asset")
    assert fields.get("entry_price") is not None


def test_classify_multi_tp_in_extracted_fields():
    text = "#BTC LONG entry $65000 TP1: $70000 TP2: $72000 SL $63000"
    status, conf, fields = classify_and_fields(text)
    assert status == "PARSED"
    assert fields.get("take_profit") == 70000.0
    assert fields.get("take_profits") == [70000.0, 72000.0]
