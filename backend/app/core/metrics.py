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


def get_metrics() -> bytes:
    """Return Prometheus metrics in text format."""
    return generate_latest()


def metrics_response() -> Response:
    """FastAPI response for /metrics endpoint."""
    return Response(
        content=get_metrics(),
        media_type=CONTENT_TYPE_LATEST
    )
