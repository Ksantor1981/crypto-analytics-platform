"""
Prometheus metrics for monitoring.
Exposes /metrics endpoint for Prometheus scraping.
"""
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Response
import time

# HTTP request metrics
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"]
)
REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency",
    ["method", "endpoint"],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0)
)

# App metrics
SIGNALS_COLLECTED = Counter("signals_collected_total", "Total signals collected")
ML_PREDICTIONS = Counter("ml_predictions_total", "Total ML predictions made")
API_ERRORS = Counter("api_errors_total", "Total API errors", ["endpoint"])

# Pipeline metrics (incoming -> parsed -> saved -> skipped)
SIGNALS_POSTS_FETCHED = Counter(
    "signals_posts_fetched_total",
    "HTML/RSS posts fetched before text-level parse",
)
SIGNALS_COLLECTED_RAW = Counter(
    "signals_collected_raw_total",
    "Raw posts from scraper that passed basic parsing (ParsedSignal)",
)
SIGNALS_PARSED_OK = Counter(
    "signals_parsed_ok_total",
    "Signals with entry_price ready for save",
)
SIGNALS_SAVED = Counter(
    "signals_saved_total",
    "New signals written to DB",
)
SIGNALS_SKIPPED = Counter(
    "signals_skipped_total",
    "Signals skipped by reason",
    ["reason"],  # no_entry_price, duplicate
)
SIGNALS_VALIDATED = Counter(
    "signals_validated_total",
    "Signals processed by historical validator",
    ["status"],  # hit, miss, pending
)

# Shadow canonical raw layer (telegram web scrape → raw_events)
SHADOW_RAW_EVENTS_WRITTEN = Counter(
    "shadow_raw_events_written_total",
    "New raw_events rows from shadow Telegram web ingestion",
)
SHADOW_RAW_EVENTS_DEDUP = Counter(
    "shadow_raw_events_dedup_total",
    "Shadow re-scrape skipped: same text (and same payload hash if text empty)",
)
SHADOW_MESSAGE_VERSIONS_ADDED = Counter(
    "shadow_message_versions_added_total",
    "New message_versions rows from re-scrape with changed text (or payload if no text)",
)


def get_metrics() -> bytes:
    """Return Prometheus metrics in text format."""
    return generate_latest()


def metrics_response() -> Response:
    """FastAPI response for /metrics endpoint."""
    return Response(
        content=get_metrics(),
        media_type=CONTENT_TYPE_LATEST
    )
