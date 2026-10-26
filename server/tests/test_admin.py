"""Admin dashboard endpoints."""

import pytest
from django.core.management import call_command
from django.test import Client
from django.utils import timezone

from ai.models import AiRun
from billing.models import Payment, Subscription
from resumes.models import Job, Resume
from share_links.models import LinkView, ShareLink
from tests.test_me import make_user


@pytest.fixture(autouse=True)
def templates(db):
    call_command("seed_templates")


def make_admin(email="admin@example.com", username="admin"):
    return make_user(email=email, username=username)


@pytest.fixture
def admin_client(client: Client, db, settings):
    admin = make_admin()
    settings.ADMIN_EMAILS = [admin.email]
    client.force_login(admin)
    return client, admin


def test_admin_endpoints_need_admin(client: Client, db, settings):
    plain = make_user()
    settings.ADMIN_EMAILS = []
    client.force_login(plain)
    assert client.get("/v1/admin/overview").status_code == 403
    client.logout()
    assert client.get("/v1/admin/overview").status_code == 401


def test_overview_counts(admin_client):
    client, _ = admin_client
    user = make_user(email="amit@example.com", username="amit")
    guest = make_user(email="guest@example.com", username="guest")
    guest.is_guest = True
    guest.save(update_fields=["is_guest"])
    resume = Resume.objects.create(user=user, title="Backend")
    AiRun.objects.create(
        user=user, step="rewrite", status="succeeded", model="groq:x", cost_usd_micros=5
    )
    AiRun.objects.create(
        user=user, step="rewrite", status="failed", model="groq:x", cost_usd_micros=3
    )
    link = ShareLink.objects.create(user=user, resume=resume, slug="amit")
    LinkView.objects.create(share_link=link)
    Payment.objects.create(
        user=user, dodo_checkout_session_id="cs_1", amount_paise=49900, status="captured"
    )

    data = client.get("/v1/admin/overview?days=7").json()["data"]
    totals = data["totals"]
    assert totals["users"] == 2
    assert totals["guests"] == 1
    assert totals["aiRuns"] == 2 and totals["aiFailed"] == 1
    assert totals["aiCostUsdMicros"] == 8
    assert totals["revenuePaise"] == 49900
    assert totals["shareViews"] == 1
    assert len(data["byDay"]) == 7
    assert data["byDay"][-1]["aiRuns"] == 2
    assert data["funnel"]["signedUp"] >= 1
    assert data["plans"][0]["label"] == "free"


def test_users_list_filters(admin_client):
    client, _ = admin_client
    amit = make_user(email="amit@example.com", username="amit")
    guest = make_user(email="guest@example.com", username="guest")
    guest.is_guest = True
    guest.save(update_fields=["is_guest"])
    suspended = make_user(email="susp@example.com", username="susp")
    suspended.suspended_at = timezone.now()
    suspended.save(update_fields=["suspended_at"])
    Resume.objects.create(user=amit, title="One")

    body = client.get("/v1/admin/users").json()["data"]
    assert body["page"] == 1 and body["pageSize"] == 25
    assert {row["username"] for row in body["users"]} == {"admin", "amit", "susp"}
    amit_row = next(row for row in body["users"] if row["username"] == "amit")
    assert amit_row["resumes"] == 1 and amit_row["isAnonymous"] is False

    assert [r["username"] for r in client.get("/v1/admin/users?q=ami").json()["data"]["users"]] == [
        "amit"
    ]
    assert [
        r["username"] for r in client.get("/v1/admin/users?status=guest").json()["data"]["users"]
    ] == ["guest"]
    assert [
        r["username"]
        for r in client.get("/v1/admin/users?status=suspended").json()["data"]["users"]
    ] == ["susp"]
    assert client.get("/v1/admin/users?page=0").status_code == 400
    assert client.get("/v1/admin/users?plan=nope").status_code == 400


def test_user_detail_shape(admin_client):
    client, _ = admin_client
    user = make_user(email="amit@example.com", username="amit")
    resume = Resume.objects.create(user=user, title="Backend")
    AiRun.objects.create(
        user=user, step="rewrite", status="succeeded", model="groq:x", cost_usd_micros=4
    )
    ShareLink.objects.create(user=user, resume=resume, slug="amit", view_count=3)
    Job.objects.create(user=user, raw_text="job text", text_hash="a" * 64)

    data = client.get(f"/v1/admin/users/{user.id}").json()["data"]
    assert data["user"]["email"] == "amit@example.com" and data["user"]["emailVerified"] is True
    assert data["resumes"][0]["title"] == "Backend" and data["resumes"][0]["versions"] == 0
    assert data["ai"]["runs"] == 1 and data["ai"]["bySteps"][0]["step"] == "rewrite"
    assert data["usage"]["plan"] == "free" and data["usage"]["tailor"] == {"used": 1, "limit": 1}
    assert data["shareLinks"] == 1 and data["shareViews"] == 3 and data["jobs"] == 1
    assert client.get("/v1/admin/users/not-a-number").status_code == 400
    assert client.get("/v1/admin/users/999999").status_code == 404


def test_suspend_and_unsuspend(admin_client):
    client, admin = admin_client
    user = make_user(email="amit@example.com", username="amit")

    response = client.patch(
        f"/v1/admin/users/{user.id}", {"suspended": True}, content_type="application/json"
    )
    assert response.status_code == 200
    assert response.json()["data"]["user"]["suspendedAt"] is not None
    user.refresh_from_db()
    assert user.suspended_at is not None

    response = client.patch(
        f"/v1/admin/users/{user.id}", {"suspended": False}, content_type="application/json"
    )
    assert response.json()["data"]["user"]["suspendedAt"] is None

    assert (
        client.patch(
            f"/v1/admin/users/{admin.id}", {"suspended": True}, content_type="application/json"
        ).status_code
        == 409
    )


def test_reset_usage_zeroes_the_period(admin_client):
    client, _ = admin_client
    user = make_user(email="amit@example.com", username="amit")
    AiRun.objects.create(user=user, step="rewrite", status="succeeded", model="groq:x")
    assert client.get(f"/v1/admin/users/{user.id}").json()["data"]["usage"]["tailor"]["used"] == 1

    assert client.delete(f"/v1/admin/users/{user.id}/usage").status_code == 204
    user.refresh_from_db()
    assert user.usage_reset_at is not None
    assert client.get(f"/v1/admin/users/{user.id}").json()["data"]["usage"]["tailor"]["used"] == 0


def test_grant_and_revoke_complimentary_subscription(admin_client):
    client, _ = admin_client
    user = make_user(email="amit@example.com", username="amit")

    response = client.post(
        f"/v1/admin/users/{user.id}/subscriptions",
        {"plan": "pro", "months": 2},
        content_type="application/json",
    )
    assert response.status_code == 201
    data = response.json()["data"]
    assert data["user"]["plan"] == "pro"
    assert (
        data["subscriptions"][0]["plan"] == "pro"
        and data["subscriptions"][0]["complimentary"] is True
    )

    subscription = Subscription.objects.get(user=user)
    assert (
        client.delete(f"/v1/admin/users/{user.id}/subscriptions/{subscription.id}").status_code
        == 204
    )
    user.refresh_from_db()
    assert user.plan == "free"

    assert (
        client.post(
            f"/v1/admin/users/{user.id}/subscriptions",
            {"plan": "pro", "months": 0},
            content_type="application/json",
        ).status_code
        == 400
    )


def test_revoke_paid_subscription_is_conflict(admin_client):
    client, _ = admin_client
    user = make_user(email="amit@example.com", username="amit")
    paid = Subscription.objects.create(
        user=user, plan="pro", status="active", dodo_subscription_id="sub_123"
    )
    assert client.delete(f"/v1/admin/users/{user.id}/subscriptions/{paid.id}").status_code == 409


def test_ai_usage(admin_client):
    client, _ = admin_client
    user = make_user(email="amit@example.com", username="amit")
    for latency in (10, 20, 30, 40):
        AiRun.objects.create(
            user=user,
            step="rewrite",
            status="succeeded",
            model="groq:x",
            latency_ms=latency,
            cost_usd_micros=2,
            input_tokens=10,
            output_tokens=5,
        )
    AiRun.objects.create(
        user=user, step="rewrite", status="failed", model="groq:y", error="boom", latency_ms=50
    )

    data = client.get("/v1/admin/ai?days=30").json()["data"]
    assert data["totals"]["runs"] == 5 and data["totals"]["failed"] == 1
    assert data["totals"]["inputTokens"] == 40 and data["totals"]["outputTokens"] == 20
    step = data["bySteps"][0]
    assert step["step"] == "rewrite" and step["runs"] == 5 and step["failed"] == 1
    assert step["p50Ms"] == 30 and step["p95Ms"] == 50
    assert len(data["byDay"]) == 30
    assert (
        data["failures"][0]["error"] == "boom"
        and data["failures"][0]["email"] == "amit@example.com"
    )
    assert data["topUsers"][0]["userId"] == user.id


def test_revenue(admin_client):
    client, _ = admin_client
    user = make_user(email="amit@example.com", username="amit")
    Payment.objects.create(
        user=user, dodo_checkout_session_id="cs_1", amount_paise=49900, status="captured"
    )
    Payment.objects.create(
        user=user, dodo_checkout_session_id="cs_2", amount_paise=12900, status="created"
    )

    data = client.get("/v1/admin/revenue?days=30").json()["data"]
    assert data["totals"]["paise"] == 49900 and data["totals"]["allTimePaise"] == 49900
    assert data["totals"]["payers"] == 1
    assert data["totals"]["checkouts"] == 2 and data["totals"]["checkoutsPaid"] == 1
    assert data["byDay"][-1]["paise"] == 49900
    assert {row["label"] for row in data["statuses"]} == {"captured", "created"}
    assert data["payments"][0]["email"] == "amit@example.com"
    assert data["dodoConfigured"] is False


def test_content(admin_client):
    client, _ = admin_client
    user = make_user(email="amit@example.com", username="amit")
    live = Resume.objects.create(user=user, title="Live")
    Resume.objects.create(user=user, title="Gone", deleted_at=timezone.now())
    ShareLink.objects.create(user=user, resume=live, slug="amit", is_listed=True, password_hash="x")

    data = client.get("/v1/admin/content?days=30").json()["data"]
    assert (
        data["resumes"]["total"] == 2
        and data["resumes"]["live"] == 1
        and data["resumes"]["deleted"] == 1
    )
    assert (
        data["sharing"]["links"] == 1
        and data["sharing"]["listed"] == 1
        and data["sharing"]["protected"] == 1
    )
    assert data["topLinks"][0]["slug"] == "amit" and data["topLinks"][0]["username"] == "amit"
    assert data["byTemplate"][0]["label"] == "Own LaTeX"
    assert data["uploads"]["files"] == 0


def test_system(admin_client):
    client, _ = admin_client
    data = client.get("/v1/admin/system").json()["data"]
    assert data["api"]["nodeVersion"].startswith("3.")
    assert data["database"]["version"]
    assert data["compiler"]["mode"] == "in-process" and data["compiler"]["ok"] is True
    assert data["backup"] is None
    names = {row["name"] for row in data["integrations"]}
    assert "AI (groq)" in names


def test_traffic_is_unconfigured_without_posthog(admin_client):
    client, _ = admin_client
    data = client.get("/v1/admin/traffic").json()["data"]
    assert data["configured"] is False and data["data"] is None and data["error"] is None
