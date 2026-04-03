"""Юнит-тесты UserService с моками Session (покрытие CRUD и списков)."""
import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException

from app.models.user import UserRole as ModelUserRole
from app.schemas.user import UserChangePassword, UserCreate, UserUpdate
from app.services.user_service import UserService


def _user_row(**kw):
    u = MagicMock()
    u.id = kw.get("id", 1)
    u.email = kw.get("email", "u@test.com")
    u.full_name = kw.get("full_name", "U")
    u.hashed_password = kw.get("hashed_password", "hashed")
    u.is_active = kw.get("is_active", True)
    u.role = kw.get("role", ModelUserRole.FREE_USER)
    u.current_subscription_expires = kw.get("current_subscription_expires")
    return u


def test_get_user_by_id_and_email():
    db = MagicMock()
    u = _user_row()
    db.query.return_value.filter.return_value.first.return_value = u
    svc = UserService(db)
    assert svc.get_user_by_id(1) is u
    assert svc.get_user_by_email("u@test.com") is u


def test_get_users_active_filter_and_pagination():
    db = MagicMock()

    def make_q():
        q = MagicMock()
        q.filter.return_value = q
        q.offset.return_value = q
        q.limit.return_value = q
        q.all.return_value = []
        return q

    q_active = make_q()
    q_inactive = make_q()
    db.query.side_effect = [q_active, q_inactive]
    svc = UserService(db)
    svc.get_users(skip=5, limit=10, active_only=True)
    q_active.filter.assert_called()
    svc.get_users(active_only=False)
    assert db.query.call_count == 2


def test_get_users_count_scalar():
    db = MagicMock()
    q = MagicMock()
    q.filter.return_value = q
    q.scalar.return_value = 42
    db.query.return_value = q
    assert UserService(db).get_users_count(active_only=True) == 42


def test_is_email_available():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None
    assert UserService(db).is_email_available("free@x.com") is True
    db.query.return_value.filter.return_value.first.return_value = _user_row()
    assert UserService(db).is_email_available("taken@x.com") is False


def test_create_user_duplicate_email():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = _user_row()
    svc = UserService(db)
    data = UserCreate(
        email="a@b.com",
        full_name="A",
        password="secret12",
        confirm_password="secret12",
    )
    with pytest.raises(HTTPException) as ei:
        svc.create_user(data)
    assert ei.value.status_code == 400


def test_create_user_success():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None
    svc = UserService(db)
    data = UserCreate(
        email="new@b.com",
        full_name="N",
        password="secret12",
        confirm_password="secret12",
    )
    with patch("app.services.user_service.get_password_hash", return_value="hpwd"):
        out = svc.create_user(data)
    db.add.assert_called_once()
    db.commit.assert_called_once()
    db.refresh.assert_called_once()
    assert out is not None


def test_update_user_not_found():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None
    svc = UserService(db)
    with pytest.raises(HTTPException) as ei:
        svc.update_user(99, UserUpdate(full_name="X"))
    assert ei.value.status_code == 404


def test_update_user_email_conflict():
    db = MagicMock()
    current = _user_row(id=1, email="old@test.com")
    other = _user_row(id=2, email="taken@test.com")
    calls: list[int] = []

    def query_side_effect(_model):
        m = MagicMock()
        m.filter.return_value = m
        if not calls:
            calls.append(1)
            m.first.return_value = current
        else:
            m.first.return_value = other
        return m

    db.query.side_effect = query_side_effect
    svc = UserService(db)

    with pytest.raises(HTTPException) as ei:
        svc.update_user(1, UserUpdate(email="taken@test.com"))
    assert ei.value.status_code == 400


def test_update_user_applies_fields():
    db = MagicMock()
    user = _user_row(email="same@test.com")
    q = MagicMock()
    q.filter.return_value = q
    q.first.return_value = user
    db.query.return_value = q
    svc = UserService(db)
    svc.update_user(1, UserUpdate(full_name="New Name"))
    assert user.full_name == "New Name"
    db.commit.assert_called_once()


def test_change_password_wrong_current():
    db = MagicMock()
    u = _user_row()
    db.query.return_value.filter.return_value.first.return_value = u
    svc = UserService(db)
    with patch("app.services.user_service.verify_password", return_value=False):
        with pytest.raises(HTTPException) as ei:
            svc.change_password(
                1,
                UserChangePassword(
                    current_password="bad",
                    new_password="newpass1",
                    confirm_new_password="newpass1",
                ),
            )
    assert ei.value.status_code == 400


def test_change_password_success():
    db = MagicMock()
    u = _user_row()
    db.query.return_value.filter.return_value.first.return_value = u
    svc = UserService(db)
    with patch("app.services.user_service.verify_password", return_value=True):
        with patch("app.services.user_service.get_password_hash", return_value="nh"):
            assert svc.change_password(
                1,
                UserChangePassword(
                    current_password="ok",
                    new_password="newpass1",
                    confirm_new_password="newpass1",
                ),
            ) is True
    assert u.hashed_password == "nh"
    db.commit.assert_called_once()


def test_deactivate_activate_delete():
    db = MagicMock()
    u = _user_row()
    db.query.return_value.filter.return_value.first.return_value = u
    svc = UserService(db)
    assert svc.deactivate_user(1) is True
    assert u.is_active is False
    assert svc.activate_user(1) is True
    assert u.is_active is True
    assert svc.delete_user(1) is True
    db.delete.assert_called_once_with(u)


def test_upgrade_subscription_premium_sets_expiry():
    db = MagicMock()
    u = _user_row()
    db.query.return_value.filter.return_value.first.return_value = u
    svc = UserService(db)
    out = svc.upgrade_subscription(1, ModelUserRole.PREMIUM_USER)
    assert out.role == ModelUserRole.PREMIUM_USER
    assert u.current_subscription_expires is not None
    db.commit.assert_called_once()


def test_verify_email_token():
    db = MagicMock()
    u = _user_row()
    db.query.return_value.filter.return_value.first.return_value = u
    out = UserService(db).verify_email_token("tok")
    assert out is u
    assert u.is_verified is True
    assert u.email_verification_token is None
    db.commit.assert_called_once()


def test_verify_email_token_missing():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None
    assert UserService(db).verify_email_token("bad") is None


def test_authenticate_delegates():
    db = MagicMock()
    u = _user_row()
    with patch("app.services.user_service.authenticate_user", return_value=u):
        assert UserService(db).authenticate("a@b.com", "p") is u
