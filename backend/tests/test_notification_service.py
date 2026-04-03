"""Тесты NotificationService (рендер и рассылка с моками)."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.notification_service import NotificationService


def _signal_mock(**kwargs):
    ch = MagicMock()
    ch.name = kwargs.get("channel_name", "TestCh")
    s = MagicMock()
    s.id = kwargs.get("id", 1)
    s.asset = kwargs.get("asset", "BTC")
    s.direction = kwargs.get("direction", "LONG")
    s.entry_price = kwargs.get("entry_price", 100.0)
    s.tp1_price = kwargs.get("tp1_price", 110.0)
    s.stop_loss = kwargs.get("stop_loss", 90.0)
    s.channel = kwargs.get("channel", ch)
    return s


def test_render_html_contains_signal_fields():
    db = MagicMock()
    svc = NotificationService(db)
    data = {
        "user_name": "U",
        "signal_asset": "ETH",
        "signal_direction": "SHORT",
        "signal_entry": "$1.00",
        "signal_tp": "$2.00",
        "signal_sl": "$0.50",
        "channel_name": "Ch",
        "dashboard_url": "https://example.com/d",
    }
    html = svc._render_signal_notification_template(data)
    assert "ETH" in html and "SHORT" in html
    assert "U" in html and "example.com" in html


def test_render_text_multiline():
    db = MagicMock()
    svc = NotificationService(db)
    data = {
        "user_name": "Nick",
        "signal_asset": "BTC",
        "signal_direction": "LONG",
        "signal_entry": "N/A",
        "signal_tp": "N/A",
        "signal_sl": "N/A",
        "channel_name": "X",
        "dashboard_url": "https://x",
    }
    text = svc._render_signal_notification_text(data)
    assert "Nick" in text and "BTC" in text


@pytest.mark.asyncio
async def test_notify_users_calls_email_per_subscriber():
    user = MagicMock()
    user.id = 42
    user.email = "u@example.com"
    user.full_name = "Full Name"

    q = MagicMock()
    q.filter.return_value = q
    q.all.return_value = [user]
    db = MagicMock()
    db.query.return_value = q

    svc = NotificationService(db)
    with patch.object(
        svc.email_service, "_send_email", new_callable=AsyncMock
    ) as send:
        await svc.notify_users_of_new_signal(_signal_mock())
        send.assert_awaited_once()
        call_kw = send.await_args.kwargs
        assert call_kw["to_email"] == "u@example.com"
        assert "BTC" in call_kw["subject"]


@pytest.mark.asyncio
async def test_notify_skips_failed_user_continues_others():
    u1 = MagicMock()
    u1.id = 1
    u1.email = "a@x.com"
    u1.full_name = "A"
    u2 = MagicMock()
    u2.id = 2
    u2.email = "b@x.com"
    u2.full_name = "B"

    q = MagicMock()
    q.filter.return_value = q
    q.all.return_value = [u1, u2]
    db = MagicMock()
    db.query.return_value = q

    svc = NotificationService(db)
    with patch.object(
        svc.email_service,
        "_send_email",
        new_callable=AsyncMock,
        side_effect=[None, RuntimeError("smtp down")],
    ) as send:
        await svc.notify_users_of_new_signal(_signal_mock())
        assert send.await_count == 2


@pytest.mark.asyncio
async def test_notify_outer_exception_logged():
    db = MagicMock()
    db.query.side_effect = RuntimeError("db dead")
    svc = NotificationService(db)
    with patch("app.services.notification_service.logger") as log:
        await svc.notify_users_of_new_signal(_signal_mock())
        log.error.assert_called()


@pytest.mark.asyncio
async def test_send_notification_na_prices():
    user = MagicMock()
    user.email = "x@y.z"
    user.full_name = None
    sig = _signal_mock()
    sig.entry_price = None
    sig.tp1_price = None
    sig.stop_loss = None

    db = MagicMock()
    svc = NotificationService(db)
    with patch.object(svc.email_service, "_send_email", new_callable=AsyncMock) as send:
        await svc._send_signal_notification(user, sig)
        send.assert_awaited()
        assert "N/A" in send.await_args.kwargs["html_content"]
