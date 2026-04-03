"""Тесты app.core.trusted_hosts."""
from app.core.trusted_hosts import build_trusted_hosts


def test_explicit_hosts_trimmed_and_lowered():
    hosts = build_trusted_hosts(" API.example.com , localhost ", None)
    assert hosts == ["api.example.com", "localhost"]


def test_explicit_wildcard_falls_back_to_derived():
    hosts = build_trusted_hosts("*", ["https://App.EXAMPLE.org/path"])
    assert "app.example.org" in hosts
    assert "localhost" in hosts


def test_empty_explicit_uses_defaults_and_cors():
    hosts = build_trusted_hosts(None, ["https://foo.bar:8080", "", None, 123])
    assert "foo.bar" in hosts
    assert "backend" in hosts
    assert hosts == sorted(set(hosts))


def test_explicit_empty_string_uses_derived():
    hosts = build_trusted_hosts("   ", ["https://x.test"])
    assert "x.test" in hosts


def test_malformed_origin_skipped():
    hosts = build_trusted_hosts(None, ["not-a-url", "https://valid.host"])
    assert "valid.host" in hosts
