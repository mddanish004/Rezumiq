"""Billing routes on Dodo Payments: subscription, checkout, refunds, webhooks."""

import base64
import hashlib
import hmac
import json
import time

import pytest
from django.core.management import call_command
from django.test import Client
from django.utils import timezone

from ai.models import AiRun
from billing.models import Payment, Subscription, WebhookEvent
from tests.test_me import make_user

WEBHOOK_SECRET = b"test-webhook-secret"


@pytest.fixture(autouse=True)
def templates(db):
    call_command("seed_templates")


@pytest.fixture
def paid_client(client: Client, db, settings):
    settings.DODO_API_KEY = "dodo_test"
    settings.DODO_WEBHOOK_KEY = "whsec_" + base64.b64encode(WEBHOOK_SECRET).decode()
    settings.DODO_SEASON_PASS_PRODUCT_ID = "pdt_pass"
    settings.DODO_PRO_PRODUCT_ID = "pdt_pro"
    user = make_user()
    client.force_login(user)
    return client, user


def _captured(user, **fields):
    return Payment.objects.create(
        user=user,
        dodo_checkout_session_id=fields.pop("checkout_session_id", "cs_1"),
        dodo_payment_id=fields.pop("payment_id", "pay_1"),
        amount_paise=fields.pop("amount_paise", 49900),
        status="captured",
        captured_at=fields.pop("captured_at", timezone.now()),
        **fields,
    )


def test_subscription_requires_auth(client: Client, db):
    assert client.get("/v1/subscription").status_code == 401


def test_subscription_free(client: Client, db):
    client.force_login(make_user())
    data = client.get("/v1/subscription").json()["data"]
    assert data == {"plan": "free", "subscription": None}


def test_subscription_shows_active_subscription(client: Client, db):
    user = make_user()
    subscription = Subscription.objects.create(
        user=user,
        plan="season_pass",
        status="active",
        current_period_end=timezone.now() + timezone.timedelta(days=30),
    )
    client.force_login(user)
    data = client.get("/v1/subscription").json()["data"]
    assert data["plan"] == "free"
    assert data["subscription"]["id"] == str(subscription.id)


def test_cancel_only_finds_real_dodo_pro(client: Client, db):
    user = make_user()
    Subscription.objects.create(
        user=user,
        plan="pro",
        status="active",
        current_period_end=timezone.now() + timezone.timedelta(days=30),
    )
    client.force_login(user)
    assert client.delete("/v1/subscription").status_code == 404


def test_cancel_pro_calls_dodo(client: Client, db, monkeypatch):
    user = make_user()
    Subscription.objects.create(
        user=user,
        plan="pro",
        status="active",
        dodo_subscription_id="sub_1",
        current_period_end=timezone.now() + timezone.timedelta(days=30),
    )
    client.force_login(user)
    calls = []
    monkeypatch.setattr("billing.service.dodo", lambda *a: calls.append(a) or {})
    response = client.delete("/v1/subscription")
    assert response.status_code == 200
    assert calls[0][0] == "PATCH" and calls[0][1] == "/subscriptions/sub_1"
    assert calls[0][2]["cancel_at_next_billing_date"] is True
    assert response.json()["data"]["subscription"]["status"] == "cancelled"


def test_checkout_without_keys_is_not_configured(client: Client, db, settings):
    settings.DODO_API_KEY = None
    client.force_login(make_user())
    response = client.post(
        "/v1/checkouts", {"plan": "season_pass"}, content_type="application/json"
    )
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "PAYMENTS_NOT_CONFIGURED"


def test_checkout_season_pass_returns_hosted_url(paid_client, monkeypatch):
    client, user = paid_client
    seen = {}

    def fake(method, path, body=None):
        seen.update({"method": method, "path": path, "body": body})
        return {"session_id": "cs_1", "checkout_url": "https://test.dodopayments.com/c/cs_1"}

    monkeypatch.setattr("billing.service.dodo", fake)
    response = client.post(
        "/v1/checkouts", {"plan": "season_pass"}, content_type="application/json"
    )
    assert response.status_code == 201
    assert response.json()["data"] == {
        "provider": "dodo",
        "sessionId": "cs_1",
        "checkoutUrl": "https://test.dodopayments.com/c/cs_1",
        "plan": "season_pass",
        "amountPaise": 49900,
        "currency": "INR",
    }
    assert seen["path"] == "/checkouts"
    assert seen["body"]["product_cart"] == [{"product_id": "pdt_pass", "quantity": 1}]
    assert seen["body"]["metadata"] == {"user_id": str(user.id), "plan": "season_pass"}
    payment = Payment.objects.get(user=user)
    assert payment.dodo_checkout_session_id == "cs_1" and payment.status == "created"
    assert payment.amount_paise == 49900
    assert payment.subscription.plan == "season_pass"


def test_checkout_pro_conflict(paid_client, monkeypatch):
    client, user = paid_client
    Subscription.objects.create(
        user=user, plan="pro", status="active", current_period_end=timezone.now()
    )
    monkeypatch.setattr(
        "billing.service.dodo", lambda *a: {"session_id": "cs", "checkout_url": "x"}
    )
    response = client.post("/v1/checkouts", {"plan": "pro"}, content_type="application/json")
    assert response.status_code == 409


def test_checkout_guest_is_forbidden(paid_client, monkeypatch):
    client, user = paid_client
    user.is_guest = True
    user.save(update_fields=["is_guest"])
    monkeypatch.setattr(
        "billing.service.dodo", lambda *a: {"session_id": "cs", "checkout_url": "x"}
    )
    response = client.post(
        "/v1/checkouts", {"plan": "season_pass"}, content_type="application/json"
    )
    assert response.status_code == 403


def test_refund_quote_refunds_the_whole_charge(paid_client):
    client, user = paid_client
    subscription = Subscription.objects.create(user=user, plan="season_pass", status="active")
    _captured(user, subscription=subscription)
    data = client.get("/v1/refunds/quote").json()["data"]
    assert data["reason"] is None
    assert data["quote"]["refundPaise"] == 49900
    assert data["quote"]["feePaise"] == 0
    assert data["quote"]["amountPaidPaise"] == 49900
    assert data["quote"]["plan"] == "season_pass"


def test_refund_quote_ignores_payments_outside_the_window(paid_client):
    client, user = paid_client
    _captured(user, captured_at=timezone.now() - timezone.timedelta(hours=7))
    assert client.get("/v1/refunds/quote").json()["data"] == {"quote": None, "reason": None}


def test_refund_quote_reason_after_heavy_use(paid_client):
    client, user = paid_client
    _captured(user)
    for _ in range(4):
        AiRun.objects.create(user=user, step="rewrite", status="succeeded", model="groq:x")
    data = client.get("/v1/refunds/quote").json()["data"]
    assert data["quote"] is None and "limit is 3" in data["reason"]


def test_request_refund(paid_client, monkeypatch):
    client, user = paid_client
    subscription = Subscription.objects.create(
        user=user,
        plan="season_pass",
        status="active",
        current_period_end=timezone.now() + timezone.timedelta(days=30),
    )
    payment = _captured(user, subscription=subscription)
    user.plan = "season_pass"
    user.save(update_fields=["plan"])

    calls = []

    def fake(method, path, body=None):
        calls.append((method, path, body))
        return {"refund_id": "rfd_1", "amount": 49900, "status": "succeeded"}

    monkeypatch.setattr("billing.service.dodo", fake)
    response = client.post(
        "/v1/refunds", {"paymentId": str(payment.id)}, content_type="application/json"
    )
    assert response.status_code == 201
    assert response.json()["data"] == {
        "paymentId": str(payment.id),
        "refundPaise": 49900,
        "dodoRefundId": "rfd_1",
    }
    assert calls[0][0] == "POST" and calls[0][1] == "/refunds"
    assert calls[0][2]["payment_id"] == "pay_1"
    payment.refresh_from_db()
    subscription.refresh_from_db()
    user.refresh_from_db()
    assert payment.status == "refunded" and payment.refunded_paise == 49900
    assert payment.dodo_refund_id == "rfd_1"
    assert subscription.status == "expired"
    assert user.plan == "free"

    again = client.post(
        "/v1/refunds", {"paymentId": str(payment.id)}, content_type="application/json"
    )
    assert again.status_code == 409


def test_request_refund_cancels_pro_mandate(paid_client, monkeypatch):
    client, user = paid_client
    subscription = Subscription.objects.create(
        user=user,
        plan="pro",
        status="active",
        dodo_subscription_id="sub_1",
        current_period_end=timezone.now() + timezone.timedelta(days=30),
    )
    payment = _captured(user, subscription=subscription, amount_paise=12900)
    calls = []

    def fake(method, path, body=None):
        calls.append((method, path, body))
        if path == "/refunds":
            return {"refund_id": "rfd_1", "amount": 12900, "status": "succeeded"}
        return {}

    monkeypatch.setattr("billing.service.dodo", fake)
    assert (
        client.post(
            "/v1/refunds", {"paymentId": str(payment.id)}, content_type="application/json"
        ).status_code
        == 201
    )
    assert ("PATCH", "/subscriptions/sub_1", {"status": "cancelled"}) in calls


def test_refund_failure_releases_the_claim(paid_client, monkeypatch):
    client, user = paid_client
    payment = _captured(user)

    def fail(*a, **k):
        raise RuntimeError("provider down")

    monkeypatch.setattr("billing.service.dodo", fail)
    response = client.post(
        "/v1/refunds", {"paymentId": str(payment.id)}, content_type="application/json"
    )
    assert response.status_code == 500
    payment.refresh_from_db()
    assert payment.refunded_at is None and payment.status == "captured"


def _post_webhook(client, settings, payload, webhook_id=None, signature=None, timestamp=None):
    raw = json.dumps(payload).encode()
    timestamp = str(timestamp or int(time.time()))
    webhook_id = webhook_id or "msg_1"
    signed = f"{webhook_id}.{timestamp}.".encode() + raw
    digest = base64.b64encode(hmac.new(WEBHOOK_SECRET, signed, hashlib.sha256).digest()).decode()
    headers = {
        "HTTP_WEBHOOK_ID": webhook_id,
        "HTTP_WEBHOOK_TIMESTAMP": timestamp,
        "HTTP_WEBHOOK_SIGNATURE": signature if signature is not None else f"v1,{digest}",
    }
    return client.post("/v1/webhooks/dodo", raw, content_type="application/json", **headers)


def test_webhook_rejects_bad_signature(client: Client, db, settings):
    settings.DODO_WEBHOOK_KEY = "whsec_" + base64.b64encode(WEBHOOK_SECRET).decode()
    response = _post_webhook(client, settings, {"type": "payment.succeeded"}, signature="v1,nope")
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_SIGNATURE"


def test_webhook_rejects_a_stale_timestamp(client: Client, db, settings):
    settings.DODO_WEBHOOK_KEY = "whsec_" + base64.b64encode(WEBHOOK_SECRET).decode()
    response = _post_webhook(
        client,
        settings,
        {"type": "payment.succeeded"},
        timestamp=int(time.time()) - 3600,
    )
    assert response.status_code == 400


def test_webhook_payment_succeeded_activates_season_pass(client: Client, db, settings):
    settings.DODO_WEBHOOK_KEY = "whsec_" + base64.b64encode(WEBHOOK_SECRET).decode()
    user = make_user()
    subscription = Subscription.objects.create(user=user, plan="season_pass", status="created")
    payment = Payment.objects.create(
        user=user,
        subscription=subscription,
        dodo_checkout_session_id="cs_1",
        amount_paise=49900,
    )
    event = {
        "type": "payment.succeeded",
        "data": {
            "payment_id": "pay_1",
            "checkout_session_id": "cs_1",
            "total_amount": 49900,
            "payment_method": "card",
            "created_at": "2026-01-15T10:30:00Z",
            "metadata": {"user_id": str(user.id), "plan": "season_pass"},
        },
    }
    response = _post_webhook(client, settings, event, webhook_id="msg_1")
    assert response.status_code == 200 and response.json()["data"] == {"received": True}

    payment.refresh_from_db()
    subscription.refresh_from_db()
    user.refresh_from_db()
    assert payment.status == "captured" and payment.dodo_payment_id == "pay_1"
    assert payment.method == "card"
    assert subscription.status == "active" and subscription.current_period_end
    assert user.plan == "season_pass"
    assert WebhookEvent.objects.filter(id="dodo:msg_1").exists()


def test_webhook_payment_succeeded_for_a_renewal(client: Client, db, settings):
    settings.DODO_WEBHOOK_KEY = "whsec_" + base64.b64encode(WEBHOOK_SECRET).decode()
    user = make_user()
    subscription = Subscription.objects.create(
        user=user, plan="pro", status="active", dodo_subscription_id="sub_1"
    )
    event = {
        "type": "payment.succeeded",
        "data": {
            "payment_id": "pay_9",
            "total_amount": 12900,
            "payment_method": "upi",
            "created_at": "2026-02-01T00:00:00Z",
            "subscription_ids": ["sub_1"],
        },
    }
    _post_webhook(client, settings, event)
    payment = Payment.objects.get(dodo_payment_id="pay_9")
    assert payment.amount_paise == 12900 and payment.subscription_id == subscription.id


def test_webhook_is_idempotent_per_webhook_id(client: Client, db, settings):
    settings.DODO_WEBHOOK_KEY = "whsec_" + base64.b64encode(WEBHOOK_SECRET).decode()
    user = make_user()
    subscription = Subscription.objects.create(user=user, plan="season_pass", status="created")
    Payment.objects.create(
        user=user,
        subscription=subscription,
        dodo_checkout_session_id="cs_1",
        amount_paise=49900,
    )
    event = {
        "type": "payment.succeeded",
        "data": {"payment_id": "pay_1", "checkout_session_id": "cs_1", "total_amount": 49900},
    }
    _post_webhook(client, settings, event, webhook_id="msg_same")
    _post_webhook(client, settings, event, webhook_id="msg_same")
    assert Payment.objects.filter(dodo_payment_id="pay_1").count() == 1


def test_webhook_payment_failed_marks_the_checkout_failed(client: Client, db, settings):
    settings.DODO_WEBHOOK_KEY = "whsec_" + base64.b64encode(WEBHOOK_SECRET).decode()
    user = make_user()
    payment = Payment.objects.create(
        user=user,
        dodo_checkout_session_id="cs_1",
        amount_paise=49900,
    )
    event = {"type": "payment.failed", "data": {"checkout_session_id": "cs_1"}}
    _post_webhook(client, settings, event)
    payment.refresh_from_db()
    assert payment.status == "failed"


def test_webhook_subscription_cancelled(client: Client, db, settings):
    settings.DODO_WEBHOOK_KEY = "whsec_" + base64.b64encode(WEBHOOK_SECRET).decode()
    user = make_user()
    subscription = Subscription.objects.create(
        user=user,
        plan="pro",
        status="active",
        dodo_subscription_id="sub_1",
        current_period_end=timezone.now() + timezone.timedelta(days=30),
    )
    event = {
        "type": "subscription.cancelled",
        "data": {
            "subscription_id": "sub_1",
            "status": "cancelled",
            "previous_billing_date": timezone.now().isoformat(),
            "next_billing_date": (timezone.now() + timezone.timedelta(days=30)).isoformat(),
            "cancelled_at": timezone.now().isoformat(),
        },
    }
    _post_webhook(client, settings, event)
    subscription.refresh_from_db()
    assert subscription.status == "cancelled" and subscription.cancelled_at


def test_webhook_subscription_active_creates_the_local_row(client: Client, db, settings):
    settings.DODO_WEBHOOK_KEY = "whsec_" + base64.b64encode(WEBHOOK_SECRET).decode()
    settings.DODO_PRO_PRODUCT_ID = "pdt_pro"
    user = make_user()
    start = timezone.now()
    event = {
        "type": "subscription.active",
        "data": {
            "subscription_id": "sub_new",
            "status": "active",
            "product_id": "pdt_pro",
            "previous_billing_date": start.isoformat(),
            "next_billing_date": (start + timezone.timedelta(days=30)).isoformat(),
            "metadata": {"user_id": str(user.id), "plan": "pro"},
        },
    }
    _post_webhook(client, settings, event)
    subscription = Subscription.objects.get(dodo_subscription_id="sub_new")
    assert subscription.plan == "pro" and subscription.status == "active"
    user.refresh_from_db()
    assert user.plan == "pro"


def test_webhook_refund_succeeded_expires_pass(client: Client, db, settings):
    settings.DODO_WEBHOOK_KEY = "whsec_" + base64.b64encode(WEBHOOK_SECRET).decode()
    user = make_user()
    subscription = Subscription.objects.create(user=user, plan="season_pass", status="active")
    payment = _captured(user, subscription=subscription)
    event = {
        "type": "refund.succeeded",
        "data": {
            "refund_id": "rfd_1",
            "payment_id": "pay_1",
            "amount": 49900,
            "is_partial": False,
            "status": "succeeded",
        },
    }
    _post_webhook(client, settings, event)
    payment.refresh_from_db()
    subscription.refresh_from_db()
    assert payment.status == "refunded" and payment.dodo_refund_id == "rfd_1"
    assert subscription.status == "expired"


def test_pending_refund_waits_for_the_webhook(paid_client, monkeypatch):
    client, user = paid_client
    subscription = Subscription.objects.create(
        user=user,
        plan="pro",
        status="active",
        current_period_end=timezone.now() + timezone.timedelta(days=30),
    )
    payment = _captured(user, subscription=subscription, amount_paise=15222)
    monkeypatch.setattr(
        "billing.service.dodo",
        lambda *a: {"refund_id": "rfd_pending", "amount": 15222, "status": "pending"},
    )
    response = client.post(
        "/v1/refunds", {"paymentId": str(payment.id)}, content_type="application/json"
    )
    assert response.status_code == 201
    payment.refresh_from_db()
    subscription.refresh_from_db()
    assert payment.status == "captured" and payment.refunded_at is not None
    assert payment.dodo_refund_id == "rfd_pending"
    assert subscription.status == "active"

    from django.conf import settings

    settings.DODO_WEBHOOK_KEY = "whsec_" + base64.b64encode(WEBHOOK_SECRET).decode()
    event = {
        "type": "refund.succeeded",
        "data": {
            "refund_id": "rfd_pending",
            "payment_id": "pay_1",
            "amount": 15222,
            "is_partial": False,
        },
    }
    _post_webhook(client, settings, event)
    payment.refresh_from_db()
    subscription.refresh_from_db()
    user.refresh_from_db()
    assert payment.status == "refunded" and payment.refunded_paise == 15222
    assert subscription.status == "expired"
    assert user.plan == "free"


def test_failed_refund_releases_the_claim(paid_client, monkeypatch):
    client, user = paid_client
    payment = _captured(user, amount_paise=15222)
    monkeypatch.setattr(
        "billing.service.dodo",
        lambda *a: {"refund_id": "rfd_failed", "amount": 15222, "status": "pending"},
    )
    assert (
        client.post(
            "/v1/refunds", {"paymentId": str(payment.id)}, content_type="application/json"
        ).status_code
        == 201
    )
    from django.conf import settings

    settings.DODO_WEBHOOK_KEY = "whsec_" + base64.b64encode(WEBHOOK_SECRET).decode()
    event = {
        "type": "refund.failed",
        "data": {"refund_id": "rfd_failed", "payment_id": "pay_1", "amount": 15222},
    }
    _post_webhook(client, settings, event)
    payment.refresh_from_db()
    assert (
        payment.status == "captured"
        and payment.refunded_at is None
        and payment.dodo_refund_id is None
    )
