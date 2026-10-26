"""Usage quota accounting and the GET /v1/usage endpoint."""

import datetime

import pytest
from django.core.management import call_command
from django.test import Client
from django.utils import timezone

from ai.models import AiRun
from tests.test_me import make_user


@pytest.fixture(autouse=True)
def templates(db):
    call_command("seed_templates")


def _run(
    user, step, kind_ops=None, status="succeeded", created=None, byok=False, patch_empty=False
):
    row = AiRun.objects.create(
        user=user,
        step=step,
        status=status,
        model="test",
        byok=byok,
        created_at=created or timezone.now(),
    )
    if created is not None:
        row.created_at = created
        row.save(update_fields=["created_at"])
    if kind_ops is not None or patch_empty:
        operations = [] if patch_empty else kind_ops
        row.patch_ops = {"type": "rewrite", "operations": operations}
        row.save(update_fields=["patch_ops"])
    return row


def test_runs_since_counts_charged_runs_only(db):
    from usage.quotas import runs_since

    user = make_user()
    stale = timezone.now() - datetime.timedelta(minutes=15)
    _run(user, "rewrite", patch_empty=True)
    _run(user, "rewrite")
    _run(user, "rewrite", status="pending")
    _run(user, "rewrite", status="pending", created=stale)
    _run(user, "rewrite", byok=True)
    _run(user, "ats_match")
    assert runs_since(user.id, "tailor", timezone.now() - datetime.timedelta(days=1)) == 2


def test_check_quota_count_and_boundary(db):
    from api.common.errors import AppError
    from usage.quotas import check_quota

    user = make_user()
    for _ in range(19):
        _run(user, "ats_match")
    check_quota(user.id, "ats")
    _run(user, "ats_match")
    with pytest.raises(AppError) as err:
        check_quota(user.id, "ats")
    assert err.value.details["used"] == 20 and err.value.details["limit"] == 20
    assert err.value.details["resetsAt"]


def test_check_quota_draft_is_all_time_on_free(db):
    from api.common.errors import AppError
    from usage.quotas import check_quota

    user = make_user()
    old = timezone.now() - datetime.timedelta(days=90)
    _run(user, "draft", created=old)
    with pytest.raises(AppError) as err:
        check_quota(user.id, "draft")
    assert err.value.details["used"] == 1


def test_reserved_pending_run_blocks_quota(db):
    from api.common.errors import AppError
    from usage.quotas import reserve_ai_run

    user = make_user()
    for _ in range(19):
        _run(user, "ats_match")
    run_id = reserve_ai_run(user.id, "ats", AiRun.Step.ATS_MATCH)
    run = AiRun.objects.get(id=run_id)
    assert run.status == AiRun.Status.PENDING and run.model == "pending"
    with pytest.raises(AppError):
        reserve_ai_run(user.id, "ats", AiRun.Step.ATS_MATCH)


def test_reserve_ai_run_expires_abandoned_pendings(db):
    from datetime import timedelta

    from usage.quotas import reserve_ai_run

    user = make_user()
    stale_created = timezone.now() - timedelta(minutes=11)
    _run(user, "ats_match", status="pending", created=stale_created)
    reserve_ai_run(user.id, "ats", AiRun.Step.ATS_MATCH)
    abandoned = AiRun.objects.get(user=user, created_at=stale_created)
    assert abandoned.status == AiRun.Status.FAILED
    assert abandoned.error == "abandoned before the model answered"
    assert AiRun.objects.filter(user=user, status=AiRun.Status.PENDING).count() == 1


def test_assert_ai_quota_skips_own_key(db, monkeypatch):
    from usage.quotas import assert_ai_quota

    user = make_user()
    for _ in range(50):
        _run(user, "ats_match")
    monkeypatch.setattr("ai_keys.service.has_user_ai_key", lambda uid: True)
    assert_ai_quota(user.id, "ats")
    monkeypatch.setattr("ai_keys.service.has_user_ai_key", lambda uid: False)
    from api.common.errors import AppError

    with pytest.raises(AppError):
        assert_ai_quota(user.id, "ats")


def test_review_quota_free_is_plan_required_before_quota(db):
    from api.common.errors import AppError
    from ats.ai import review_resume
    from usage.quotas import runs_since

    user = make_user()
    _run(user, "ats_review")
    with pytest.raises(AppError) as err:
        review_resume(user.id, "some resume text", None)
    assert err.value.code == "PLAN_REQUIRED"
    assert runs_since(user.id, "review", timezone.now() - datetime.timedelta(days=1)) == 1


def test_get_usage_shape(db):
    from usage.quotas import get_usage

    user = make_user()
    _run(user, "rewrite")
    _run(user, "draft", created=timezone.now() - datetime.timedelta(days=90))

    usage = get_usage(user.id)
    assert usage["plan"] == "free"
    assert usage["tailor"] == {"used": 1, "limit": 1}
    assert usage["draft"] == {"used": 1, "limit": 1}
    assert usage["import"] == {"used": 0, "limit": 20}
    assert usage["periodStart"] <= usage["periodEnd"]


def test_usage_endpoint(client: Client, db):
    from usage.quotas import period_end, period_start

    user = make_user()
    client.force_login(user)

    response = client.get("/v1/usage")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["plan"] == "free"
    assert data["ownAiKey"] is False
    assert data["resumes"] == {"used": 0, "limit": 1000}
    assert data["import"] == {"used": 0, "limit": 20}
    assert data["periodStart"] == period_start().isoformat().replace("+00:00", "Z")
    assert data["periodEnd"] == period_end().isoformat().replace("+00:00", "Z")


def test_usage_endpoint_needs_auth(client: Client, db):
    assert client.get("/v1/usage").status_code == 401


def test_usage_includes_ats_job_and_review_counters(client: Client, db):
    user = make_user()
    client.force_login(user)
    _run(user, "ats_match")
    _run(user, "jd_parse")
    _run(user, "ats_review")
    data = client.get("/v1/usage").json()["data"]
    assert data["ats"] == {"used": 1, "limit": 20}
    assert data["job"] == {"used": 1, "limit": 10}
    assert data["review"] == {"used": 1, "limit": 0}
