"""Admin dashboard, ported from modules/admin/admin.service.ts.

Aggregations run through the ORM; day buckets and latency percentiles are done in
Python so the same code serves sqlite in tests and Postgres in production.
"""

from __future__ import annotations

import os
import platform
import resource
import time
from collections import Counter
from datetime import timedelta

from django.conf import settings
from django.db import connection
from django.db.models import Count, Max, Q, Sum
from django.utils import timezone

from analytics.service import _day_key
from api.common.errors import ConflictError, NotFoundError

PAGE_SIZE = 25
_STARTED = time.monotonic()


def day_keys(days: int, time_zone: str, now) -> list[str]:
    """Every day of the range, oldest first, in the requested time zone."""
    return [_day_key(now - timedelta(days=offset), time_zone) for offset in range(days - 1, -1, -1)]


def users():
    from django.contrib.auth import get_user_model

    return get_user_model()


def get_admin_user(user_id):
    try:
        return users().objects.get(id=user_id)
    except users().DoesNotExist:
        raise NotFoundError("User") from None


def _decoded_sessions() -> list[dict]:
    """django_session rows carry no timestamps; expiry minus the cookie age is
    the best activity proxy (ponytail: switch to a session audit table if admin
    needs true login times)."""
    from django.contrib.sessions.models import Session

    proxy = timedelta(seconds=getattr(settings, "SESSION_COOKIE_AGE", 1209600))
    now = timezone.now()
    rows = []
    for row in Session.objects.filter(expire_date__gt=now):
        user_id = row.get_decoded().get("_auth_user_id")
        if user_id:
            rows.append(
                {
                    "id": row.session_key,
                    "user_id": user_id,
                    "updated_at": row.expire_date - proxy,
                    "expires_at": row.expire_date,
                }
            )
    return rows


def _active_session_ids(sessions, since) -> set:
    ids = {s["user_id"] for s in sessions if s["updated_at"] >= since}
    if not ids:
        return set()
    return set(users().objects.filter(is_guest=False, id__in=ids).values_list("id", flat=True))


def get_overview(days: int, time_zone: str) -> dict:
    from ai.models import AiRun
    from billing.models import Payment
    from resumes.models import Resume
    from share_links.models import LinkView, ShareLink

    now = timezone.now()
    since = now - timedelta(days=days)
    previous_since = since - timedelta(days=days)

    user_totals = users().objects.aggregate(
        users=Count("id", filter=~Q(is_guest=True)),
        guests=Count("id", filter=Q(is_guest=True)),
        paid=Count("id", filter=~Q(plan="free")),
        suspended=Count("id", filter=Q(suspended_at__isnull=False)),
    )
    new_users = users().objects.filter(is_guest=False, date_joined__gte=since).count()
    previous_new_users = (
        users()
        .objects.filter(is_guest=False, date_joined__gte=previous_since, date_joined__lt=since)
        .count()
    )

    sessions = [s for s in _decoded_sessions() if s["updated_at"] >= previous_since]
    active_ids = _active_session_ids([s for s in sessions if s["updated_at"] >= since], since)
    previous_active_ids = _active_session_ids(
        [s for s in sessions if previous_since <= s["updated_at"] < since], since
    )

    resume_totals = Resume.objects.aggregate(
        total=Count("id", filter=Q(deleted_at__isnull=True)),
        created=Count("id", filter=Q(created_at__gte=since)),
        previous_created=Count(
            "id", filter=Q(created_at__gte=previous_since) & Q(created_at__lt=since)
        ),
    )
    ai = AiRun.objects.aggregate(
        runs=Count("id", filter=Q(created_at__gte=since)),
        previous_runs=Count(
            "id", filter=Q(created_at__gte=previous_since) & Q(created_at__lt=since)
        ),
        failed=Count("id", filter=Q(created_at__gte=since, status="failed")),
        cost=Sum("cost_usd_micros", filter=Q(created_at__gte=since), default=0),
        previous_cost=Sum(
            "cost_usd_micros",
            filter=Q(created_at__gte=previous_since) & Q(created_at__lt=since),
            default=0,
        ),
    )
    revenue = Payment.objects.filter(status="captured").aggregate(
        paise=Sum("amount_paise", filter=Q(updated_at__gte=since), default=0),
        previous_paise=Sum(
            "amount_paise",
            filter=Q(updated_at__gte=previous_since) & Q(updated_at__lt=since),
            default=0,
        ),
    )
    views = LinkView.objects.aggregate(
        views=Count("id", filter=Q(viewed_at__gte=since)),
        previous_views=Count(
            "id", filter=Q(viewed_at__gte=previous_since) & Q(viewed_at__lt=since)
        ),
    )

    by_day_sources = {
        "signups": users()
        .objects.filter(is_guest=False, date_joined__gte=since)
        .values_list("date_joined", flat=True),
        "resumes": Resume.objects.filter(created_at__gte=since).values_list(
            "created_at", flat=True
        ),
        "aiRuns": AiRun.objects.filter(created_at__gte=since).values_list("created_at", flat=True),
        "views": LinkView.objects.filter(viewed_at__gte=since).values_list("viewed_at", flat=True),
    }
    keys = day_keys(days, time_zone, now)
    merged = {day: {"signups": 0, "resumes": 0, "aiRuns": 0, "views": 0} for day in keys}
    for field, datetimes in by_day_sources.items():
        per_day = Counter(_day_key(dt, time_zone) for dt in datetimes)
        for day, count in per_day.items():
            if day in merged:
                merged[day][field] = count

    plan_rows = (
        users()
        .objects.filter(is_guest=False)
        .values("plan")
        .annotate(count=Count("id"))
        .order_by("-count")
    )
    plans = [{"label": row["plan"], "count": row["count"]} for row in plan_rows]

    from allauth.socialaccount.models import SocialAccount

    provider_rows = (
        SocialAccount.objects.filter(user__is_guest=False)
        .values("provider")
        .annotate(count=Count("user_id", distinct=True))
        .order_by("-count")
    )
    providers = [{"label": row["provider"], "count": row["count"]} for row in provider_rows]

    funnel_ids = list(
        users().objects.filter(is_guest=False, date_joined__gte=since).values_list("id", flat=True)
    )
    created_resume = set(
        Resume.objects.filter(user_id__in=funnel_ids).values_list("user_id", flat=True)
    )
    used_ai = set(AiRun.objects.filter(user_id__in=funnel_ids).values_list("user_id", flat=True))
    shared = set(ShareLink.objects.filter(user_id__in=funnel_ids).values_list("user_id", flat=True))
    paid = set(
        Payment.objects.filter(user_id__in=funnel_ids, status="captured").values_list(
            "user_id", flat=True
        )
    )
    funnel = {
        "signedUp": len(funnel_ids),
        "createdResume": len(created_resume),
        "usedAi": len(used_ai),
        "shared": len(shared),
        "paid": len(paid),
    }

    recent_signups = [
        {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "image": None,
            "plan": user.plan,
            "createdAt": user.date_joined,
            "providers": list(user.socialaccount_set.values_list("provider", flat=True)),
        }
        for user in users().objects.filter(is_guest=False).order_by("-date_joined")[:8]
    ]

    return {
        "days": days,
        "totals": {
            "users": user_totals["users"],
            "guests": user_totals["guests"],
            "newUsers": new_users,
            "previousNewUsers": previous_new_users,
            "activeUsers": len(active_ids),
            "previousActiveUsers": len(previous_active_ids),
            "paidUsers": user_totals["paid"],
            "suspendedUsers": user_totals["suspended"],
            "resumes": resume_totals["total"],
            "resumesCreated": resume_totals["created"],
            "previousResumesCreated": resume_totals["previous_created"],
            "aiRuns": ai["runs"],
            "previousAiRuns": ai["previous_runs"],
            "aiFailed": ai["failed"],
            "aiCostUsdMicros": ai["cost"],
            "previousAiCostUsdMicros": ai["previous_cost"],
            "revenuePaise": revenue["paise"],
            "previousRevenuePaise": revenue["previous_paise"],
            "shareViews": views["views"],
            "previousShareViews": views["previous_views"],
        },
        "byDay": [{"day": day, **merged[day]} for day in keys],
        "plans": plans,
        "providers": providers,
        "funnel": funnel,
        "recentSignups": recent_signups,
    }


def list_users(query: dict) -> dict:
    filters = Q()
    if query.get("q"):
        pattern = query["q"][:100]
        filters &= (
            Q(name__icontains=pattern)
            | Q(email__icontains=pattern)
            | Q(username__icontains=pattern)
        )
    if query.get("plan"):
        filters &= Q(plan=query["plan"])
    status = query["status"]
    if status == "guest":
        filters &= Q(is_guest=True)
    else:
        filters &= Q(is_guest=False)
        if status == "suspended":
            filters &= Q(suspended_at__isnull=False)
        elif status == "active":
            filters &= Q(suspended_at__isnull=True)

    total = users().objects.filter(filters).count()
    last_active = {s["user_id"]: s["updated_at"] for s in _decoded_sessions()}
    page = query["page"]
    from ai.models import AiRun
    from resumes.models import Resume

    rows = (
        users()
        .objects.filter(filters)
        .order_by("-date_joined")[(page - 1) * PAGE_SIZE : page * PAGE_SIZE]
    )
    out = [
        {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "image": None,
            "username": user.username,
            "plan": user.plan,
            "isAnonymous": user.is_guest,
            "suspendedAt": user.suspended_at,
            "createdAt": user.date_joined,
            "lastActiveAt": last_active.get(str(user.id)),
            "providers": list(user.socialaccount_set.values_list("provider", flat=True)),
            "resumes": Resume.objects.filter(user=user, deleted_at__isnull=True).count(),
            "aiRuns": AiRun.objects.filter(user=user).count(),
        }
        for user in rows
    ]
    return {"users": out, "page": page, "pageSize": PAGE_SIZE, "total": total}


def _email_verified(user) -> bool:
    from allauth.account.models import EmailAddress

    return EmailAddress.objects.filter(user=user, email=user.email, verified=True).exists()


def get_user_detail(user_id) -> dict:
    from ai.models import AiRun
    from billing.models import Payment, Subscription
    from resumes.models import Job, Resume
    from share_links.models import ShareLink
    from usage.quotas import get_usage

    user = get_admin_user(user_id)

    user_resumes = [
        {
            "id": str(resume.id),
            "title": resume.title,
            "mode": resume.mode,
            "templateId": resume.template_id,
            "createdAt": resume.created_at,
            "updatedAt": resume.updated_at,
            "archivedAt": resume.archived_at,
            "deletedAt": resume.deleted_at,
            "versions": resume.versions.count(),
        }
        for resume in Resume.objects.filter(user=user).order_by("-updated_at")
    ]

    ai_by_steps = list(
        AiRun.objects.filter(user=user)
        .values("step")
        .annotate(
            runs=Count("id"),
            failed=Count("id", filter=Q(status="failed")),
            cost=Sum("cost_usd_micros", default=0),
        )
        .order_by("-runs")
    )
    for row in ai_by_steps:
        row["cost_usd_micros"] = row.pop("cost")
    ai_totals = AiRun.objects.filter(user=user).aggregate(
        runs=Count("id"),
        byok=Count("id", filter=Q(byok=True)),
        cost=Sum("cost_usd_micros", default=0),
        last_run_at=Max("created_at"),
    )

    subscriptions = [
        {
            "id": str(subscription.id),
            "plan": subscription.plan,
            "status": subscription.status,
            "currentPeriodStart": subscription.current_period_start,
            "currentPeriodEnd": subscription.current_period_end,
            "dodoSubscriptionId": subscription.dodo_subscription_id,
            "complimentary": (
                not subscription.dodo_subscription_id
                and not Payment.objects.filter(subscription=subscription).exists()
            ),
            "createdAt": subscription.created_at,
        }
        for subscription in Subscription.objects.filter(user=user).order_by("-created_at")
    ]

    payments = [
        {
            "id": str(payment.id),
            "amountPaise": payment.amount_paise,
            "status": payment.status,
            "method": payment.method,
            "dodoPaymentId": payment.dodo_payment_id,
            "createdAt": payment.created_at,
        }
        for payment in Payment.objects.filter(user=user).order_by("-created_at")
    ]

    sessions = [
        {
            "id": session["id"],
            "createdAt": session["updated_at"],
            "updatedAt": session["updated_at"],
            "expiresAt": session["expires_at"],
            "userAgent": None,
        }
        for session in _decoded_sessions()
        if session["user_id"] == str(user.id)
    ]
    sessions.sort(key=lambda session: session["updatedAt"], reverse=True)

    sharing = ShareLink.objects.filter(user=user, deleted_at__isnull=True).aggregate(
        links=Count("id"), views=Sum("view_count", default=0)
    )

    return {
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "emailVerified": _email_verified(user),
            "image": None,
            "username": user.username,
            "plan": user.plan,
            "isAnonymous": user.is_guest,
            "suspendedAt": user.suspended_at,
            "createdAt": user.date_joined,
            "updatedAt": user.date_joined,
        },
        "accounts": [
            {"providerId": account.provider, "createdAt": account.date_joined}
            for account in user.socialaccount_set.all()
        ],
        "resumes": user_resumes,
        "ai": {
            "runs": ai_totals["runs"],
            "byokRuns": ai_totals["byok"],
            "costUsdMicros": ai_totals["cost"],
            "lastRunAt": ai_totals["last_run_at"],
            "bySteps": ai_by_steps,
        },
        "usage": get_usage(user.id),
        "subscriptions": subscriptions,
        "payments": payments,
        "sessions": sessions[:10],
        "shareLinks": sharing["links"],
        "shareViews": sharing["views"],
        "jobs": Job.objects.filter(user=user).count(),
    }


def set_suspended(admin_id, user_id, suspended: bool) -> None:
    from api.common.errors import ConflictError

    if admin_id == user_id:
        raise ConflictError("You can't suspend your own account")
    user = get_admin_user(user_id)
    user.suspended_at = timezone.now() if suspended else None
    user.save(update_fields=["suspended_at"])
    if suspended:
        _revoke_user_sessions(user_id)


def revoke_sessions(admin_id, user_id) -> int:
    _revoke_user_sessions(user_id)


def _revoke_user_sessions(user_id) -> None:
    from django.contrib.sessions.models import Session

    ids = [s["id"] for s in _decoded_sessions() if s["user_id"] == str(user_id)]
    Session.objects.filter(session_key__in=ids).delete()


def reset_usage(admin_id, user_id) -> None:
    user = get_admin_user(user_id)
    user.usage_reset_at = timezone.now()
    user.save(update_fields=["usage_reset_at"])


def grant_subscription(admin_id, user_id, plan: str, months: int) -> None:
    from billing.service import grant_plan, recompute_plan

    get_admin_user(user_id)
    grant_plan(user_id, plan, months)
    recompute_plan(user_id)


def revoke_subscription(admin_id, user_id, subscription_id) -> None:
    from billing.models import Payment, Subscription
    from billing.service import recompute_plan

    subscription = Subscription.objects.filter(id=subscription_id, user_id=user_id).first()
    if not subscription:
        raise NotFoundError("Subscription")
    if (
        subscription.dodo_subscription_id
        or Payment.objects.filter(subscription=subscription).exists()
    ):
        raise ConflictError("Paid plans are cancelled or refunded in Dodo Payments, not here")
    subscription.status = Subscription.Status.EXPIRED
    subscription.current_period_end = timezone.now()
    subscription.save(update_fields=["status", "current_period_end"])
    recompute_plan(user_id)


def get_ai_usage(days: int, time_zone: str) -> dict:
    from ai.models import AiRun

    now = timezone.now()
    since = now - timedelta(days=days)

    row = AiRun.objects.filter(created_at__gte=since).aggregate(
        runs=Count("id"),
        failed=Count("id", filter=Q(status="failed")),
        byok=Count("id", filter=Q(byok=True)),
        cost=Sum("cost_usd_micros", default=0),
        input=Sum("input_tokens", default=0),
        cached=Sum("cached_input_tokens", default=0),
        output=Sum("output_tokens", default=0),
        users=Count("user_id", distinct=True),
    )
    totals = {
        "runs": row["runs"],
        "failed": row["failed"],
        "byok": row["byok"],
        "costUsdMicros": row["cost"],
        "inputTokens": row["input"],
        "cachedInputTokens": row["cached"],
        "outputTokens": row["output"],
        "users": row["users"],
    }

    by_steps = list(
        AiRun.objects.filter(created_at__gte=since)
        .values("step")
        .annotate(
            runs=Count("id"),
            failed=Count("id", filter=Q(status="failed")),
            cost=Sum("cost_usd_micros", default=0),
        )
        .order_by("-runs")
    )
    for row in by_steps:
        row["cost_usd_micros"] = row.pop("cost")
    latencies = AiRun.objects.filter(created_at__gte=since).values_list("step", "latency_ms")
    perstep = {}
    for step, latency in latencies:
        if latency is not None:
            perstep.setdefault(step, []).append(latency)
    for row in by_steps:
        values = sorted(perstep.get(row["step"], []))
        row["p50Ms"] = _percentile(values, 0.5)
        row["p95Ms"] = _percentile(values, 0.95)

    by_models = list(
        AiRun.objects.filter(created_at__gte=since)
        .values("model")
        .annotate(
            runs=Count("id"),
            cost=Sum("cost_usd_micros", default=0),
            tokens=Sum("input_tokens", default=0) + Sum("output_tokens", default=0),
        )
        .order_by("-cost")
    )
    for row in by_models:
        row["cost_usd_micros"] = row.pop("cost")

    failures = [
        {
            "id": str(run.id),
            "createdAt": run.created_at,
            "step": run.step,
            "model": run.model,
            "error": run.error,
            "userId": run.user_id,
            "email": run.user.email,
        }
        for run in AiRun.objects.filter(created_at__gte=since, status="failed")
        .select_related("user")
        .order_by("-created_at")[:20]
    ]
    top_users = [
        {
            "userId": row["user_id"],
            "email": row["user__email"],
            "name": row["user__name"],
            "runs": row["runs"],
            "costUsdMicros": row["cost"],
        }
        for row in AiRun.objects.filter(created_at__gte=since)
        .values("user_id", "user__email", "user__name")
        .annotate(runs=Count("id"), cost=Sum("cost_usd_micros", default=0))
        .order_by("-cost")[:10]
    ]

    run_day = Counter(
        _day_key(created_at, time_zone)
        for created_at in AiRun.objects.filter(created_at__gte=since).values_list(
            "created_at", flat=True
        )
    )
    cost_day = Counter()
    for created_at, cost in AiRun.objects.filter(created_at__gte=since).values_list(
        "created_at", "cost_usd_micros"
    ):
        cost_day[_day_key(created_at, time_zone)] += cost or 0
    keys = day_keys(days, time_zone, now)
    by_day = [
        {"day": day, "runs": run_day.get(day, 0), "costUsdMicros": cost_day.get(day, 0)}
        for day in keys
    ]

    return {
        "days": days,
        "totals": totals,
        "bySteps": by_steps,
        "byModels": by_models,
        "byDay": by_day,
        "failures": failures,
        "topUsers": top_users,
    }


def _percentile(values: list, fraction: float) -> int:
    if not values:
        return 0
    index = max(0, min(len(values) - 1, round(fraction * (len(values) - 1))))
    return round(values[index])


def get_revenue(days: int, time_zone: str) -> dict:
    from billing.models import Payment, Subscription

    now = timezone.now()
    since = now - timedelta(days=days)
    previous_since = since - timedelta(days=days)
    captured = Q(status="captured")

    totals = Payment.objects.aggregate(
        paise=Sum("amount_paise", filter=captured & Q(updated_at__gte=since), default=0),
        previous_paise=Sum(
            "amount_paise",
            filter=captured & Q(updated_at__gte=previous_since) & Q(updated_at__lt=since),
            default=0,
        ),
        all_time_paise=Sum("amount_paise", filter=captured, default=0),
        payers=Count("user_id", filter=captured, distinct=True),
        checkouts=Count("id", filter=Q(created_at__gte=since)),
        checkouts_paid=Count("id", filter=Q(created_at__gte=since) & captured),
    )

    by_day: Counter = Counter()
    for updated_at, amount in Payment.objects.filter(captured, updated_at__gte=since).values_list(
        "updated_at", "amount_paise"
    ):
        by_day[_day_key(updated_at, time_zone)] += amount
    day_money = [
        {"day": day, "paise": by_day.get(day, 0)} for day in day_keys(days, time_zone, now)
    ]

    active_subscriptions = list(
        Subscription.objects.filter(
            status__in=("active", "cancelled", "past_due"), current_period_end__gt=timezone.now()
        )
        .values("plan")
        .annotate(active=Count("id"))
    )

    recent = [
        {
            "id": str(payment.id),
            "createdAt": payment.created_at,
            "amountPaise": payment.amount_paise,
            "status": payment.status,
            "method": payment.method,
            "dodoPaymentId": payment.dodo_payment_id,
            "plan": payment.subscription.plan if payment.subscription_id else None,
            "userId": payment.user_id,
            "email": payment.user.email,
        }
        for payment in Payment.objects.select_related("user", "subscription").order_by(
            "-created_at"
        )[:50]
    ]

    statuses = [
        {"label": row["status"], "count": row["count"]}
        for row in Payment.objects.filter(created_at__gte=since)
        .values("status")
        .annotate(count=Count("id"))
    ]

    return {
        "days": days,
        "totals": totals,
        "byDay": day_money,
        "activeSubscriptions": active_subscriptions,
        "statuses": statuses,
        "payments": recent,
        "dodoConfigured": bool(settings.DODO_API_KEY),
    }


def get_content(days: int) -> dict:
    from resumes.models import Job, Resume, ResumeVersion, Template
    from share_links.models import LinkView, ShareLink
    from uploads.models import Upload

    now = timezone.now()
    since = now - timedelta(days=days)

    resume_totals = Resume.objects.aggregate(
        total=Count("id"),
        live=Count("id", filter=Q(deleted_at__isnull=True, archived_at__isnull=True)),
        archived=Count("id", filter=Q(deleted_at__isnull=True, archived_at__isnull=False)),
        deleted=Count("id", filter=Q(deleted_at__isnull=False)),
        structured=Count("id", filter=Q(mode="structured")),
        code=Count("id", filter=Q(mode="code")),
        tailored=Count("id", filter=Q(job_id__isnull=False)),
    )

    by_template_rows = (
        Resume.objects.filter(deleted_at__isnull=True)
        .values("template_id")
        .annotate(count=Count("id"))
        .order_by("-count")
    )
    by_template = [
        {"label": row["template_id"] or "Own LaTeX", "count": row["count"]}
        for row in by_template_rows
    ]

    version_kinds = [
        {"label": row["kind"], "count": row["count"]}
        for row in ResumeVersion.objects.filter(created_at__gte=since)
        .values("kind")
        .annotate(count=Count("id"))
        .order_by("-count")
    ]

    sharing_totals = ShareLink.objects.aggregate(
        links=Count("id", filter=Q(deleted_at__isnull=True)),
        listed=Count("id", filter=Q(deleted_at__isnull=True, is_listed=True)),
        protected=Count("id", filter=Q(deleted_at__isnull=True, password_hash__isnull=False)),
        plain=Count(
            "id",
            filter=Q(deleted_at__isnull=True, is_listed=False, password_hash__isnull=True),
        ),
        views=Sum("view_count", default=0),
    )

    recent_views = list(
        LinkView.objects.filter(viewed_at__gte=since)
        .values("share_link_id")
        .annotate(viewCount=Count("id"))
    )
    recent_by_link = {row["share_link_id"]: row["viewCount"] for row in recent_views}
    top_links = [
        {
            "id": str(link.id),
            "slug": link.slug,
            "username": link.user.username,
            "resumeTitle": link.resume.title,
            "views": recent_by_link.get(link.id, 0),
            "totalViews": link.view_count,
        }
        for link in sorted(
            ShareLink.objects.filter(deleted_at__isnull=True).select_related("user", "resume"),
            key=lambda link: (recent_by_link.get(link.id, 0), link.view_count),
            reverse=True,
        )[:10]
    ]

    upload_totals = Upload.objects.aggregate(
        files=Count("id"),
        bytes=Sum("size_bytes", default=0),
        pdf=Count("id", filter=Q(kind="pdf")),
        tex=Count("id", filter=Q(kind="tex")),
        text=Count("id", filter=Q(kind="text")),
    )

    return {
        "days": days,
        "resumes": resume_totals,
        "byTemplate": by_template,
        "versionKinds": version_kinds,
        "sharing": sharing_totals,
        "topLinks": top_links,
        "customTemplates": Template.objects.count(),
        "jobs": Job.objects.count(),
        "jobsFromUrl": Job.objects.filter(source_url__isnull=False).count(),
        "uploads": upload_totals,
    }


def compiler_health() -> dict:
    if not settings.COMPILER_URL:
        return {"mode": "in-process", "ok": True, "latencyMs": None}
    import urllib.request

    started = time.monotonic()
    try:
        with urllib.request.urlopen(settings.COMPILER_URL + "/health", timeout=3) as response:
            return {
                "mode": "service",
                "ok": response.status < 400,
                "latencyMs": int((time.monotonic() - started) * 1000),
            }
    except Exception:  # noqa: BLE001
        return {"mode": "service", "ok": False, "latencyMs": None}


def get_system() -> dict:
    from billing.models import WebhookEvent

    started = time.monotonic()
    with connection.cursor() as cursor:
        if connection.vendor == "postgresql":
            cursor.execute(
                "select current_setting('server_version'), pg_database_size(current_database())"
            )
            version, size_bytes = cursor.fetchone()
            cursor.execute(
                """select relname, n_live_tup, pg_total_relation_size(relid)
                   from pg_stat_user_tables order by pg_total_relation_size(relid) desc"""
            )
            tables = [
                {"name": name, "rows": rows, "sizeBytes": size}
                for name, rows, size in cursor.fetchall()
            ]
            cursor.execute(
                "select state, count(*) from pg_stat_activity where datname = current_database() group by state"
            )
            connections = [
                {"state": state or "background", "count": count}
                for state, count in cursor.fetchall()
            ]
        else:
            cursor.execute("select sqlite_version()")
            version = cursor.fetchone()[0]
            size_bytes = 0
            tables = []
            connections = [{"state": "connected", "count": 1}]

    provider = settings.AI_PROVIDER
    key = {
        "groq": settings.GROQ_API_KEY,
        "openai": settings.OPENAI_API_KEY,
        "anthropic": settings.ANTHROPIC_API_KEY,
        "openrouter": settings.OPENROUTER_API_KEY,
    }.get(provider)
    return {
        "api": {
            "nodeVersion": platform.python_version(),
            "uptimeSeconds": round(time.monotonic() - _STARTED),
            "rssBytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024,
            "heapUsedBytes": 0,
            "environment": "development" if settings.DEBUG else "production",
        },
        "database": {
            "version": version,
            "sizeBytes": size_bytes,
            "latencyMs": round((time.monotonic() - started) * 1000),
            "connections": connections,
            "tables": tables,
        },
        "compiler": compiler_health(),
        "backup": None,
        "lastWebhookAt": WebhookEvent.objects.order_by("-received_at")
        .values_list("received_at", flat=True)
        .first(),
        "integrations": [
            {"name": "Google sign-in", "configured": bool(os.getenv("GOOGLE_CLIENT_ID"))},
            {"name": "GitHub sign-in", "configured": bool(os.getenv("GITHUB_CLIENT_ID"))},
            {"name": "ChatGPT sign-in", "configured": bool(os.getenv("CHATGPT_CLIENT_ID"))},
            {"name": f"AI ({provider})", "configured": bool(key)},
            {"name": f"Storage ({settings.STORAGE_DRIVER})", "configured": True},
            {
                "name": "Dodo Payments",
                "configured": bool(settings.DODO_API_KEY and settings.DODO_WEBHOOK_KEY),
            },
            {"name": "PostHog events", "configured": bool(os.getenv("POSTHOG_KEY"))},
            {
                "name": "PostHog admin reads",
                "configured": bool(
                    os.getenv("POSTHOG_PERSONAL_API_KEY") and os.getenv("POSTHOG_PROJECT_ID")
                ),
            },
            {"name": "Jina Reader key", "configured": bool(os.getenv("JINA_API_KEY"))},
        ],
    }


def get_traffic(days: int, time_zone: str) -> dict:
    return {
        "configured": bool(
            os.getenv("POSTHOG_PERSONAL_API_KEY") and os.getenv("POSTHOG_PROJECT_ID")
        ),
        "dashboardUrl": os.getenv("POSTHOG_URL", "https://app.posthog.com"),
        "error": None,
        "data": None,
    }
