"""Suspended accounts are cut off the moment any request passes through."""

from django.test import Client
from django.utils import timezone

from accounts.models import User
from tests.test_me import make_user


def test_suspended_user_gets_403_and_is_signed_out(client: Client, db):
    user = make_user()
    client.force_login(user)
    user.suspend()

    response = client.get("/v1/me")
    assert response.status_code == 403
    assert response.json()["error"] == {
        "code": "FORBIDDEN",
        "message": "This account is suspended",
        "details": None,
    }

    response = client.get("/v1/me")
    assert response.status_code == 401


def test_unsuspend_restores_access(client: Client, db):
    user = make_user()
    user.unsuspend()
    client.force_login(user)
    user.suspend()
    user.unsuspend()
    assert user.suspended_at is None
    assert client.get("/v1/me").status_code == 200


def test_user_row_defaults(client: Client, db):
    user = make_user()
    assert user.suspended_at is None
    assert not user.is_suspended
    assert user.is_staff is False
    assert User.Plan.FREE == user.plan
    assert timezone.now() > user.date_joined
