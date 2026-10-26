"""Plan quotas and limits, ported from modules/usage/quotas.ts.

The usage endpoint reads through get_usage; every AI call that costs the plan
reserve_ai_run's a pending AiRun first, then record/fail it when the model answers.
"""

from datetime import UTC, datetime, timedelta

from api.common.errors import AppError, NotFoundError

PLAN_LIMITS: dict[str, dict[str, int]] = {
    "free": {
        "resumes": 1000,
        "tailor": 1,
        "edit": 50,
        "import": 20,
        "draft": 1,
        "job": 10,
        "ats": 20,
        "review": 0,
    },
    "season_pass": {
        "resumes": 1000,
        "tailor": 40,
        "edit": 1000,
        "import": 20,
        "draft": 30,
        "job": 100,
        "ats": 200,
        "review": 100,
    },
    "pro": {
        "resumes": 1000,
        "tailor": 60,
        "edit": 1000,
        "import": 20,
        "draft": 30,
        "job": 100,
        "ats": 200,
        "review": 100,
    },
}


def quota_error(message: str, limit: int, used: int, resets_at=None) -> AppError:
    details = {"limit": limit, "used": used}
    if resets_at:
        details["resetsAt"] = resets_at
    return AppError(402, "QUOTA_EXCEEDED", message, details)


def active_resumes(user_id: str) -> int:
    from resumes.models import Resume

    return Resume.objects.filter(user_id=user_id, deleted_at__isnull=True).count()


def plan_of(user_id: str) -> str:
    from django.contrib.auth import get_user_model

    User = get_user_model()
    try:
        return User.objects.get(id=user_id).plan
    except User.DoesNotExist:
        raise NotFoundError("User") from None


def assert_paid_plan(user_id: str, feature: str) -> None:
    if plan_of(user_id) == "free":
        raise AppError(402, "PLAN_REQUIRED", f"{feature} is part of Season Pass and Pro")


def assert_resume_quota(user_id: str, plan: str) -> None:
    limit = PLAN_LIMITS[plan]["resumes"]
    used = active_resumes(user_id)
    if used >= limit:
        raise quota_error(
            f"You've reached the limit of {limit} resumes. Delete some you no longer need.",
            limit,
            used,
        )


STEPS_FOR: dict[str, list[str]] = {
    "tailor": ["rewrite"],
    "edit": ["chat_edit", "inline_edit", "fix_compile"],
    "import": ["import"],
    "draft": ["draft"],
    "job": ["jd_parse"],
    "ats": ["ats_match"],
    "review": ["ats_review"],
}


def period_start() -> datetime:
    """Calendar month in UTC."""
    from django.utils import timezone

    return timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def period_end() -> datetime:
    from django.utils import timezone

    now = timezone.now()
    year, month = (now.year + 1, 1) if now.month == 12 else (now.year, now.month + 1)
    return now.replace(year=year, month=month, day=1, hour=0, minute=0, second=0, microsecond=0)


_EPOCH = datetime(1970, 1, 1, tzinfo=UTC)
PENDING_TTL = timedelta(minutes=10)


def runs_since(user_id: str, kind: str, since: datetime) -> int:
    """Charged runs of one kind since a moment, counted the way quotas count them."""
    from django.db.models import Q
    from django.utils import timezone

    from ai.models import AiRun

    return AiRun.objects.filter(
        Q(user_id=user_id),
        Q(byok=False),
        Q(status=AiRun.Status.SUCCEEDED)
        | (Q(status=AiRun.Status.PENDING) & Q(created_at__gt=timezone.now() - PENDING_TTL)),
        Q(step__in=STEPS_FOR[kind]),
        Q(created_at__gte=since),
        ~Q(patch_ops__operations=[]),
    ).count()


def used_this_period(user_id: str, kind: str, all_time: bool = False) -> int:
    """`all_time` counts every run, for allowances given once per account rather than per month."""
    from django.contrib.auth import get_user_model

    reset_at = (
        get_user_model().objects.filter(id=user_id).values_list("usage_reset_at", flat=True).first()
    )
    start = _EPOCH if all_time else period_start()
    since = reset_at if reset_at is not None and reset_at > start else start
    return runs_since(user_id, kind, since)


def check_quota(user_id: str, kind: str) -> None:
    plan = plan_of(user_id)
    limit = PLAN_LIMITS[plan][kind]
    once = kind == "draft" and plan == "free"
    used = used_this_period(user_id, kind, once)
    if used >= limit and once:
        raise quota_error(
            "You've used your free AI-written resume. Season Pass and Pro include more, or add your own AI key.",
            limit,
            used,
        )
    if used >= limit:
        raise quota_error(
            f"You've used all {limit} {kind} requests for this month", limit, used, period_end()
        )


def assert_ai_quota(user_id: str, kind: str) -> None:
    from ai_keys.service import has_user_ai_key

    if not has_user_ai_key(user_id):
        check_quota(user_id, kind)


def reserve_ai_run(user_id: str, kind: str, step: str, resume_id=None, job_id=None) -> str:
    """Checks the quota and records a pending run in one step, under a per-user lock: a parallel
    request waits, then counts this run. The early assert_ai_quota only fails fast; this holds."""
    from django.db import transaction

    from ai.models import AiRun

    with transaction.atomic():
        from django.contrib.auth import get_user_model
        from django.utils import timezone

        get_user_model().objects.select_for_update().get(id=user_id)
        AiRun.objects.filter(
            user_id=user_id,
            status=AiRun.Status.PENDING,
            created_at__lt=timezone.now() - PENDING_TTL,
        ).update(status=AiRun.Status.FAILED, error="abandoned before the model answered")
        check_quota(user_id, kind)
        run = AiRun.objects.create(
            user_id=user_id,
            step=step,
            status=AiRun.Status.PENDING,
            model="pending",
            resume_id=resume_id,
            job_id=job_id,
        )
        return str(run.id)


def get_usage(user_id: str) -> dict:
    from ai_keys.service import has_user_ai_key

    plan = plan_of(user_id)
    limits = PLAN_LIMITS[plan]
    return {
        "plan": plan,
        "ownAiKey": has_user_ai_key(user_id),
        "periodStart": period_start(),
        "periodEnd": period_end(),
        "resumes": {"used": active_resumes(user_id), "limit": limits["resumes"]},
        "tailor": {"used": used_this_period(user_id, "tailor"), "limit": limits["tailor"]},
        "edit": {"used": used_this_period(user_id, "edit"), "limit": limits["edit"]},
        "import": {"used": used_this_period(user_id, "import"), "limit": limits["import"]},
        "draft": {
            "used": used_this_period(user_id, "draft", plan == "free"),
            "limit": limits["draft"],
        },
        "job": {"used": used_this_period(user_id, "job"), "limit": limits["job"]},
        "ats": {"used": used_this_period(user_id, "ats"), "limit": limits["ats"]},
        "review": {"used": used_this_period(user_id, "review"), "limit": limits["review"]},
    }
