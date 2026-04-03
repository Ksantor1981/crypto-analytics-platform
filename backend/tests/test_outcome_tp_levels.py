"""Сбор и санитизация уровней TP для outcome engine."""
from decimal import Decimal

from app.services.outcome_tp_levels import collect_take_profit_levels, sanitize_take_profit_levels


def test_sanitize_long_sorts_asc():
    r = sanitize_take_profit_levels("LONG", Decimal("100"), [Decimal("130"), Decimal("115"), Decimal("115")])
    assert r == [Decimal("115"), Decimal("130")]


def test_sanitize_short_sorts_desc():
    r = sanitize_take_profit_levels("SHORT", Decimal("100"), [Decimal("70"), Decimal("85")])
    assert r == [Decimal("85"), Decimal("70")]


def test_collect_merges_list_and_scalars():
    ef = {
        "take_profits": [120, 125],
        "tp3_price": "130",
        "take_profit": 110,
    }
    r = collect_take_profit_levels(ef, Decimal("105"), "LONG", Decimal("100"))
    assert r == [Decimal("105"), Decimal("110"), Decimal("120"), Decimal("125"), Decimal("130")]
