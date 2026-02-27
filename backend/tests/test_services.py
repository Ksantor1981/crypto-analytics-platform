"""Tests for core services — price validator, signal checker, metrics, sanitizer, dedup."""
import pytest
import asyncio


class TestSanitizer:
    def test_script_tag(self):
        from app.services.sanitizer import sanitize_text
        assert "<script>" not in sanitize_text("<script>alert(1)</script>")

    def test_javascript_protocol(self):
        from app.services.sanitizer import sanitize_text
        assert "javascript:" not in sanitize_text("javascript:alert(1)")

    def test_onclick(self):
        from app.services.sanitizer import sanitize_text
        assert "onclick=" not in sanitize_text('onclick=alert(1)')

    def test_normal_text(self):
        from app.services.sanitizer import sanitize_text
        assert sanitize_text("Hello world") == "Hello world"

    def test_max_length(self):
        from app.services.sanitizer import sanitize_text
        assert len(sanitize_text("A" * 10000)) <= 5000

    def test_empty(self):
        from app.services.sanitizer import sanitize_text
        assert sanitize_text("") == ""
        assert sanitize_text(None) == ""


class TestPriceValidator:
    def test_coingecko_ids(self):
        from app.services.price_validator import COINGECKO_IDS
        assert COINGECKO_IDS["BTC"] == "bitcoin"
        assert COINGECKO_IDS["ETH"] == "ethereum"
        assert len(COINGECKO_IDS) >= 20

    def test_get_price_returns_type(self):
        from app.services.price_validator import get_current_price
        result = asyncio.get_event_loop().run_until_complete(get_current_price("BTC/USDT"))
        # May be None if rate limited, but should be float or None
        assert result is None or isinstance(result, (int, float))

    def test_validate_signal_returns_dict(self):
        from app.services.price_validator import validate_signal_price
        result = asyncio.get_event_loop().run_until_complete(validate_signal_price("BTC/USDT", 65000))
        assert isinstance(result, dict)
        assert "valid" in result


class TestMetricsCalculator:
    def test_hit_statuses(self):
        from app.services.metrics_calculator import HIT_STATUSES, MISS_STATUSES, RESOLVED_STATUSES
        assert "TP1_HIT" in HIT_STATUSES
        assert "SL_HIT" in MISS_STATUSES
        assert HIT_STATUSES.issubset(RESOLVED_STATUSES)
        assert len(HIT_STATUSES & MISS_STATUSES) == 0

    def test_functions_callable(self):
        from app.services.metrics_calculator import recalculate_channel_metrics, recalculate_all_channels
        assert callable(recalculate_channel_metrics)
        assert callable(recalculate_all_channels)


class TestSignalChecker:
    def test_import(self):
        from app.services.signal_checker import check_pending_signals
        assert callable(check_pending_signals)


class TestDedup:
    def test_import(self):
        from app.services.dedup import signal_exists, cleanup_duplicates
        assert callable(signal_exists)
        assert callable(cleanup_duplicates)


class TestRedditScraper:
    def test_subreddits(self):
        from app.services.reddit_scraper import CRYPTO_SUBREDDITS
        assert "CryptoCurrency" in CRYPTO_SUBREDDITS
        assert "Bitcoin" in CRYPTO_SUBREDDITS
        assert len(CRYPTO_SUBREDDITS) >= 10

    def test_functions(self):
        from app.services.reddit_scraper import collect_reddit_signals, collect_all_reddit_signals
        assert callable(collect_reddit_signals)


class TestOCR:
    def test_import(self):
        from app.services.ocr_signal_parser import parse_signal_from_image, extract_text_from_image
        assert callable(parse_signal_from_image)

    def test_sanitize_integration(self):
        from app.services.sanitizer import sanitize_signal_text
        result = sanitize_signal_text("BTC LONG $65000 <script>hack</script>")
        assert "BTC" in result
        assert "<script>" not in result


class TestTelegramScraper:
    def test_ignore_assets(self):
        from app.services.telegram_scraper import IGNORE_ASSETS
        assert "XAU" in IGNORE_ASSETS
        assert "GOLD" in IGNORE_ASSETS

    def test_crypto_pairs(self):
        from app.services.telegram_scraper import CRYPTO_PAIRS
        assert "BTC" in CRYPTO_PAIRS
        assert CRYPTO_PAIRS["BTC"] >= 1000

    def test_parse_complete_signal(self):
        from app.services.telegram_scraper import parse_signal_from_text
        sig = parse_signal_from_text("#BTC LONG entry $65000 TP $72000 SL $63000")
        assert sig.asset == "BTC/USDT"
        assert sig.direction == "LONG"
        assert sig.entry_price == 65000
        assert sig.take_profit == 72000
        assert sig.stop_loss == 63000
        assert sig.confidence == 0.85

    def test_parse_short(self):
        from app.services.telegram_scraper import parse_signal_from_text
        sig = parse_signal_from_text("$ETH SHORT from $2100 tp $1900 sl $2200")
        assert sig.direction == "SHORT"
        assert sig.entry_price == 2100

    def test_ignore_gold(self):
        from app.services.telegram_scraper import parse_signal_from_text
        assert parse_signal_from_text("XAU/USD BUY at 5190") is None

    def test_no_direction_returns_none(self):
        from app.services.telegram_scraper import parse_signal_from_text
        assert parse_signal_from_text("#BTC at $65000") is None

    def test_validate_btc_price(self):
        from app.services.telegram_scraper import _validate_price
        assert _validate_price(65000, "BTC/USDT")
        assert not _validate_price(5, "BTC/USDT")
        assert not _validate_price(168.4, "BTC/USDT")  # too low for BTC
        assert not _validate_price(300000, "BTC/USDT")  # too high

    def test_skip_news_digest(self):
        from app.services.telegram_scraper import parse_signal_from_text
        news = "Trump speaking in Congress. Bank of America acquired 2,486 BTC ($168.4 million). Weekly Digest."
        assert parse_signal_from_text(news) is None

    def test_skip_price_in_million_context(self):
        from app.services.telegram_scraper import parse_signal_from_text
        # $168.4 million — не entry price для BTC
        text = "BTC LONG Strategy acquired $168.4 million worth of BTC"
        sig = parse_signal_from_text(text)
        assert sig is None or (sig and sig.entry_price != 168.4)

    def test_detect_asset_formats(self):
        from app.services.telegram_scraper import _detect_asset
        assert _detect_asset("#BTC long") == "BTC/USDT"
        assert _detect_asset("$ETH pump") == "ETH/USDT"
        assert _detect_asset("SOL/USDT entry") == "SOL/USDT"
        assert _detect_asset("nothing here") is None
