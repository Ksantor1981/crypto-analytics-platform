"""Tests for telegram scraper and signal parser."""
import json
from pathlib import Path

import pytest
from app.services.telegram_scraper import parse_signal_from_text, _detect_asset, _validate_price


class TestAssetDetection:
    def test_btc_hashtag(self):
        assert _detect_asset("#BTC long from $65k") == "BTC/USDT"

    def test_eth_dollar(self):
        assert _detect_asset("$ETH breaks above $2000") == "ETH/USDT"

    def test_sol_usdt_pair(self):
        assert _detect_asset("SOL/USDT looking bullish") == "SOL/USDT"

    def test_no_asset(self):
        assert _detect_asset("Market is looking good today") is None

    def test_link_in_text(self):
        assert _detect_asset("LINK showing strength at $15") == "LINK/USDT"

    def test_ada_pair(self):
        assert _detect_asset("#ADA/USDT entry at 0.45") == "ADA/USDT"


class TestPriceValidation:
    def test_btc_valid(self):
        assert _validate_price(65000, "BTC/USDT") is True

    def test_btc_too_low(self):
        assert _validate_price(5, "BTC/USDT") is False

    def test_eth_valid(self):
        assert _validate_price(1950, "ETH/USDT") is True

    def test_sol_valid(self):
        assert _validate_price(150, "SOL/USDT") is True

    def test_ada_valid(self):
        assert _validate_price(0.45, "ADA/USDT") is True


class TestSignalParsing:
    def test_btc_long_with_prices(self):
        text = "#BTC LONG entry $65,500 TP $72,000 SL $63,000"
        sig = parse_signal_from_text(text)
        assert sig is not None
        assert sig.asset == "BTC/USDT"
        assert sig.direction == "LONG"
        assert sig.entry_price == 65500.0
        assert sig.take_profit == 72000.0
        assert sig.stop_loss == 63000.0

    def test_eth_short(self):
        text = "$ETH SHORT from $2100"
        sig = parse_signal_from_text(text)
        assert sig is not None
        assert sig.asset == "ETH/USDT"
        assert sig.direction == "SHORT"

    def test_buy_signal_russian(self):
        text = "BTC/USDT Лонг вход 64000"
        sig = parse_signal_from_text(text)
        assert sig is not None
        assert sig.direction == "LONG"

    def test_no_direction(self):
        text = "#BTC at $65000"
        sig = parse_signal_from_text(text)
        assert sig is None

    def test_no_asset(self):
        text = "Market is crashing, sell everything"
        sig = parse_signal_from_text(text)
        assert sig is None

    def test_dollar_k_price(self):
        text = "#BTC buy at $65k, target $72k"
        sig = parse_signal_from_text(text)
        assert sig is not None
        assert sig.entry_price == 65000.0

    def test_confidence_full(self):
        text = "#BTC LONG entry $65000 TP $70000 SL $63000"
        sig = parse_signal_from_text(text)
        assert sig.confidence == 0.85

    def test_confidence_no_prices(self):
        text = "#BTC LONG"
        sig = parse_signal_from_text(text)
        assert sig.confidence == 0.4


class TestSignalParsingCorpus:
    """Small corpus-based tests using real-world-like examples."""

    @pytest.mark.parametrize("case", json.loads(
        Path(__file__).with_name("data").joinpath("sample_telegram_messages.json").read_text(encoding="utf-8")
    ))
    def test_corpus_cases(self, case):
        text = case["text"]
        expected = case["expected"]
        sig = parse_signal_from_text(text)

        if expected is None:
            assert sig is None
            return

        assert sig is not None, f"Expected signal for case {case['id']}"
        if "asset" in expected:
            assert sig.asset == expected["asset"]
        if "direction" in expected:
            assert sig.direction == expected["direction"]
        if "entry_price" in expected:
            assert sig.entry_price == expected["entry_price"]
        if "take_profit" in expected:
            assert sig.take_profit == expected["take_profit"]
        if "stop_loss" in expected:
            assert sig.stop_loss == expected["stop_loss"]


class TestMetricsCalculator:
    def test_import(self):
        from app.services.metrics_calculator import recalculate_channel_metrics
        assert recalculate_channel_metrics is not None
