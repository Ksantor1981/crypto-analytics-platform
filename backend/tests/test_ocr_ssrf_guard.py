"""Regression tests for OCR URL SSRF guard."""

from app.services.ocr_signal_parser import _is_safe_public_image_url


def test_ocr_url_guard_blocks_localhost():
    assert _is_safe_public_image_url("http://localhost:8000/secret.png") is False
    assert _is_safe_public_image_url("http://127.0.0.1:8000/secret.png") is False
    assert _is_safe_public_image_url("http://10.0.0.5/secret.png") is False


def test_ocr_url_guard_rejects_non_http_schemes():
    assert _is_safe_public_image_url("file:///etc/passwd") is False
    assert _is_safe_public_image_url("ftp://example.com/image.png") is False
