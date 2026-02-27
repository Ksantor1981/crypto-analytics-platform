"""Test configuration — set env vars before any app import."""
import os

os.environ.setdefault("USE_SQLITE", "true")
os.environ.setdefault("SECRET_KEY", "test-secret-key-32-chars-minimum-length")
os.environ.setdefault("SENTRY_DSN", "")
os.environ.setdefault("STRIPE_SECRET_KEY", "")
os.environ.setdefault("TELEGRAM_BOT_TOKEN", "")
os.environ["AUTH_RATE_LIMIT_REQUESTS"] = "1000"
os.environ["AUTH_RATE_LIMIT_WINDOW"] = "60"
os.environ["RATE_LIMIT_REQUESTS"] = "10000"
os.environ["RATE_LIMIT_WINDOW"] = "60"
