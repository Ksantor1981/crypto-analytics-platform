"""Тесты Celery email tasks (локальный .run(), моки БД и PaymentService)."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


def _gen_db(mock_session):
    def _g():
        yield mock_session

    return _g


@pytest.mark.parametrize(
    "task_name,async_method",
    [
        ("send_daily_payment_reminders", "send_payment_reminders"),
        ("send_expired_subscription_notifications", "send_expired_subscription_notifications"),
    ],
)
def test_payment_tasks_run_async_service(task_name, async_method):
    from app.tasks import email_tasks

    db = MagicMock()
    db.close = MagicMock()
    task = getattr(email_tasks, task_name)
    ps_instance = MagicMock()
    setattr(ps_instance, async_method, AsyncMock(return_value={"done": True}))

    with patch.object(email_tasks, "get_db", _gen_db(db)):
        with patch.object(email_tasks, "PaymentService", return_value=ps_instance):
            out = task.run()
    assert out == {"done": True}
    db.close.assert_called_once()


def test_send_weekly_payment_summary_aggregates():
    from app.tasks import email_tasks

    db = MagicMock()
    db.close = MagicMock()
    p1 = MagicMock()
    p1.status = "SUCCEEDED"
    p1.amount = 10.0
    p2 = MagicMock()
    p2.status = "SUCCEEDED"
    p2.amount = 5.5
    p3 = MagicMock()
    p3.status = "FAILED"
    p3.amount = 99.0

    q = MagicMock()
    q.filter.return_value = q
    q.all.return_value = [p1, p2, p3]

    db.query.return_value = q

    with patch.object(email_tasks, "get_db", _gen_db(db)):
        out = email_tasks.send_weekly_payment_summary.run()

    assert out["success"] is True
    assert out["total_payments"] == 3
    assert out["successful_payments"] == 2
    assert out["total_amount"] == pytest.approx(15.5)
    assert out["period"] == "weekly"
    db.close.assert_called_once()


def test_send_weekly_payment_summary_error_path():
    from app.tasks import email_tasks

    db = MagicMock()
    db.close = MagicMock()
    db.query.side_effect = RuntimeError("db err")

    with patch.object(email_tasks, "get_db", _gen_db(db)):
        out = email_tasks.send_weekly_payment_summary.run()

    assert out["success"] is False
    assert "db err" in out["error"]
    db.close.assert_called_once()


def test_send_daily_payment_reminders_async_error():
    from app.tasks import email_tasks

    db = MagicMock()
    db.close = MagicMock()
    ps_instance = MagicMock()
    ps_instance.send_payment_reminders = AsyncMock(side_effect=ValueError("mail"))

    with patch.object(email_tasks, "get_db", _gen_db(db)):
        with patch.object(email_tasks, "PaymentService", return_value=ps_instance):
            out = email_tasks.send_daily_payment_reminders.run()

    assert out["success"] is False
    assert "mail" in out["error"]
    db.close.assert_called_once()


def test_send_expired_subscription_notifications_async_error():
    from app.tasks import email_tasks

    db = MagicMock()
    db.close = MagicMock()
    ps_instance = MagicMock()
    ps_instance.send_expired_subscription_notifications = AsyncMock(
        side_effect=RuntimeError("expired flow")
    )

    with patch.object(email_tasks, "get_db", _gen_db(db)):
        with patch.object(email_tasks, "PaymentService", return_value=ps_instance):
            out = email_tasks.send_expired_subscription_notifications.run()

    assert out["success"] is False
    assert "expired flow" in out["error"]
    db.close.assert_called_once()
