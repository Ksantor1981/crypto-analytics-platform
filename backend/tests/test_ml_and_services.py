"""Tests for ML predictions and backend services."""
import pytest


class TestPriceValidator:
    def test_import(self):
        from app.services.price_validator import validate_signal_price, COINGECKO_IDS
        assert "BTC" in COINGECKO_IDS
        assert "ETH" in COINGECKO_IDS

    def test_coingecko_ids(self):
        from app.services.price_validator import COINGECKO_IDS
        assert COINGECKO_IDS["BTC"] == "bitcoin"
        assert COINGECKO_IDS["ETH"] == "ethereum"
        assert COINGECKO_IDS["SOL"] == "solana"
        assert len(COINGECKO_IDS) >= 20


class TestSignalChecker:
    def test_import(self):
        from app.services.signal_checker import check_pending_signals
        assert callable(check_pending_signals)

    def test_metrics_statuses(self):
        from app.services.metrics_calculator import HIT_STATUSES, MISS_STATUSES, RESOLVED_STATUSES
        assert "TP1_HIT" in HIT_STATUSES
        assert "SL_HIT" in MISS_STATUSES
        assert HIT_STATUSES.issubset(RESOLVED_STATUSES)
        assert len(HIT_STATUSES & MISS_STATUSES) == 0


class TestMetricsCalculator:
    def test_import(self):
        from app.services.metrics_calculator import recalculate_channel_metrics, recalculate_all_channels
        assert callable(recalculate_channel_metrics)
        assert callable(recalculate_all_channels)

    def test_hit_statuses(self):
        from app.services.metrics_calculator import HIT_STATUSES
        assert "TP1_HIT" in HIT_STATUSES
        assert "TP2_HIT" in HIT_STATUSES


class TestTelegramScraper:
    def test_detect_btc_formats(self):
        from app.services.telegram_scraper import _detect_asset
        assert _detect_asset("#BTC long") == "BTC/USDT"
        assert _detect_asset("$BTC breaks $65k") == "BTC/USDT"
        assert _detect_asset("BTC/USDT analysis") == "BTC/USDT"
        assert _detect_asset("BTCUSDT signal") == "BTC/USDT"

    def test_detect_various_assets(self):
        from app.services.telegram_scraper import _detect_asset
        assert _detect_asset("#SOL pump") == "SOL/USDT"
        assert _detect_asset("$DOGE 🚀") == "DOGE/USDT"
        assert _detect_asset("LINK/USDT entry") == "LINK/USDT"

    def test_validate_price_ranges(self):
        from app.services.telegram_scraper import _validate_price
        assert _validate_price(65000, "BTC/USDT") is True
        assert _validate_price(0.5, "BTC/USDT") is False
        assert _validate_price(1950, "ETH/USDT") is True
        assert _validate_price(0.001, "ETH/USDT") is False
        assert _validate_price(150, "SOL/USDT") is True
        assert _validate_price(0.0000001, "PEPE/USDT") is True

    def test_parse_long_signal(self):
        from app.services.telegram_scraper import parse_signal_from_text
        sig = parse_signal_from_text("#BTC LONG entry $65,500 TP $72,000 SL $63,000")
        assert sig is not None
        assert sig.direction == "LONG"
        assert sig.entry_price == 65500.0

    def test_parse_short_signal(self):
        from app.services.telegram_scraper import parse_signal_from_text
        sig = parse_signal_from_text("$ETH SHORT from $2100")
        assert sig is not None
        assert sig.direction == "SHORT"

    def test_parse_no_signal(self):
        from app.services.telegram_scraper import parse_signal_from_text
        assert parse_signal_from_text("Good morning everyone!") is None
        assert parse_signal_from_text("") is None

    def test_parse_russian(self):
        from app.services.telegram_scraper import parse_signal_from_text
        sig = parse_signal_from_text("BTC/USDT Лонг вход 64000")
        assert sig is not None
        assert sig.direction == "LONG"
