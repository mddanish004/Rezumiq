"""Promo codes."""

from datetime import timedelta

import pytest
from django.core.management import call_command
from django.test import Client
from django.utils import timezone

from billing.models import PromoCode
from tests.test_me import make_user


@pytest.fixture(autouse=True)
def templates(db):
    call_command("seed_templates")


def _code(plan="season_pass", months=6, max_redemptions=None, active=True, expires_at=None):
    return PromoCode.objects.create(
        code="TESTCODE",
        plan=plan,
        months=months,
        max_redemptions=max_redemptions,
        active=active,
        expires_at=expires_at,
    )


def test_redeem_success(client: Client, db):
    user = make_user()
    client.force_login(user)
    _code()
    r = client.post("/v1/promo-redemptions", {"code": "testcode"}, content_type="application/json")
    assert r.status_code == 201
    assert r.json()["data"]["plan"] == "season_pass"
    from django.contrib.auth import get_user_model

    u = get_user_model().objects.get(id=user.id)
    assert u.plan == "season_pass"


def test_redeem_already_paid(client: Client, db):
    user = make_user()
    client.force_login(user)
    user.plan = "season_pass"
    user.save()
    _code()
    r = client.post("/v1/promo-redemptions", {"code": "TESTCODE"}, content_type="application/json")
    assert r.status_code == 409


def test_redeem_expired(client: Client, db):
    user = make_user()
    client.force_login(user)
    _code(expires_at=timezone.now() - timedelta(days=1))
    r = client.post("/v1/promo-redemptions", {"code": "TESTCODE"}, content_type="application/json")
    assert r.status_code == 422


def test_redeem_twice_same_user(client: Client, db):
    user = make_user()
    client.force_login(user)
    _code()
    client.post("/v1/promo-redemptions", {"code": "TESTCODE"}, content_type="application/json")
    PromoCode.objects.create(code="OTHER", plan="season_pass", months=3, active=True)
    r = client.post("/v1/promo-redemptions", {"code": "OTHER"}, content_type="application/json")
    assert r.status_code == 409
