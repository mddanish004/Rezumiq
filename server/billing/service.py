"""Billing: subscriptions, payments, refunds, on Dodo Payments (merchant of record).

Checkout returns a hosted Dodo checkout URL. Webhooks are the source of truth for what
was paid; with no API key configured every paid route answers 503 PAYMENTS_NOT_CONFIGURED.
"""

from __future__ import annotations

import calendar
from datetime import datetime, timedelta

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from api.common.errors import AppError, ConflictError, ForbiddenError, NotFoundError
from billing.dodo import request as dodo
from billing.models import Payment, Subscription

PRICES = {"season_pass": 49900, "pro": 12900}

REFUND_WINDOW = timedelta(hours=6)
REFUND_USE_LIMIT = 3


def _add_months(start: datetime, months: int) -> datetime:
    month_index = start.month - 1 + months
    year = start.year + month_index // 12
    month = month_index % 12 + 1
    return start.replace(
        year=year, month=month, day=min(start.day, calendar.monthrange(year, month)[1])
    )


def recompute_plan(user_id) -> str:
    from django.contrib.auth import get_user_model

    User = get_user_model()
    active = Subscription.objects.filter(
        user_id=user_id,
        status__in=["active", "cancelled", "past_due"],
        current_period_end__gt=timezone.now(),
    )
    plan = "free"
    if active.filter(plan="pro").exists():
        plan = "pro"
    elif active.exists():
        plan = "season_pass"
    User.objects.filter(id=user_id).update(plan=plan)
    return plan


def grant_plan(user_id, plan, months) -> dict:
    start = timezone.now()
    sub = Subscription.objects.create(
        user_id=user_id,
        plan=plan,
        status="active",
        current_period_start=start,
        current_period_end=_add_months(start, months),
    )
    return {"id": sub.id}


def assert_not_guest(user_id) -> None:
    from django.contrib.auth import get_user_model

    User = get_user_model()
    user = User.objects.get(id=user_id)
    if getattr(user, "is_guest", False):
        raise ForbiddenError(
            "Create an account first, so your plan isn't deleted with this guest account"
        )


def create_checkout(user_id, plan) -> dict:
    if not settings.DODO_API_KEY:
        raise AppError(503, "PAYMENTS_NOT_CONFIGURED", "Payments are not configured")
    product_id = (
        settings.DODO_SEASON_PASS_PRODUCT_ID
        if plan == "season_pass"
        else settings.DODO_PRO_PRODUCT_ID
    )
    if not product_id:
        raise AppError(503, "PAYMENTS_NOT_CONFIGURED", "This plan is not configured")
    assert_not_guest(user_id)
    if (
        plan == "pro"
        and Subscription.objects.filter(user_id=user_id, plan="pro", status="active").exists()
    ):
        raise ConflictError("You already have an active Pro subscription")

    from django.contrib.auth import get_user_model

    user = get_user_model().objects.get(id=user_id)
    session = dodo(
        "POST",
        "/checkouts",
        {
            "product_cart": [{"product_id": product_id, "quantity": 1}],
            "metadata": {"user_id": str(user_id), "plan": plan},
            "customer": {"email": user.email, "name": user.name or user.username},
            "return_url": f"{settings.FRONTEND_URL}/billing?status=success",
            "cancel_url": f"{settings.FRONTEND_URL}/billing?status=cancelled",
        },
    )
    with transaction.atomic():
        subscription = Subscription.objects.create(user_id=user_id, plan=plan, status="created")
        Payment.objects.create(
            user_id=user_id,
            subscription=subscription,
            dodo_checkout_session_id=session["session_id"],
            amount_paise=PRICES[plan],
        )
    return {
        "provider": "dodo",
        "sessionId": session["session_id"],
        "checkoutUrl": session["checkout_url"],
        "plan": plan,
        "amountPaise": PRICES[plan],
        "currency": "INR",
    }


def get_subscription(user_id) -> dict:
    from django.contrib.auth import get_user_model

    User = get_user_model()
    plan = User.objects.filter(id=user_id).values_list("plan", flat=True).first() or "free"
    subscription = (
        Subscription.objects.filter(user_id=user_id, status__in=["active", "cancelled", "past_due"])
        .order_by("-current_period_end")
        .first()
    )
    return {
        "plan": plan,
        "subscription": None
        if not subscription
        else {
            "id": subscription.id,
            "plan": subscription.plan,
            "status": subscription.status,
            "currentPeriodEnd": subscription.current_period_end,
            "cancelledAt": subscription.cancelled_at,
        },
    }


def cancel_subscription(user_id) -> dict:
    subscription = Subscription.objects.filter(
        user_id=user_id,
        plan="pro",
        status="active",
        dodo_subscription_id__isnull=False,
    ).first()
    if not subscription:
        raise NotFoundError("Active Pro subscription")
    dodo(
        "PATCH",
        f"/subscriptions/{subscription.dodo_subscription_id}",
        {"status": "cancelled", "cancel_at_next_billing_date": True},
    )
    subscription.status = Subscription.Status.CANCELLED
    subscription.cancelled_at = timezone.now()
    subscription.save(update_fields=["status", "cancelled_at"])
    return get_subscription(user_id)


def _why_not_refundable(user_id, since) -> str | None:
    from usage.quotas import runs_since

    if Payment.objects.filter(user_id=user_id, status="refunded").exists():
        return "Each account can get one refund, and yours has already had one."
    tailored = runs_since(user_id, "tailor", since)
    written = runs_since(user_id, "draft", since)
    if tailored > REFUND_USE_LIMIT or written > REFUND_USE_LIMIT:
        return (
            f"Refunds are for trying the plan: you've made {tailored} tailored and {written} "
            f"AI-written resumes since paying, and the limit is {REFUND_USE_LIMIT} of each."
        )
    return None


def _refundable(user_id, now):
    from django.db.models import Q

    return Q(
        user_id=user_id,
        status="captured",
        refunded_at__isnull=True,
        dodo_payment_id__isnull=False,
        captured_at__gt=now - REFUND_WINDOW,
    )


def get_refund_quote(user_id, now=None) -> dict:
    now = now or timezone.now()
    row = (
        Payment.objects.filter(_refundable(user_id, now))
        .select_related("subscription")
        .order_by("-captured_at")
        .first()
    )
    if not row:
        return {"quote": None, "reason": None}
    reason = _why_not_refundable(user_id, row.captured_at)
    if reason:
        return {"quote": None, "reason": reason}
    return {
        "quote": {
            "paymentId": row.id,
            "plan": row.subscription.plan if row.subscription_id else None,
            "amountPaidPaise": row.amount_paise,
            "feePaise": 0,
            "refundPaise": row.amount_paise,
            "refundableUntil": row.captured_at + REFUND_WINDOW,
        },
        "reason": None,
    }


def request_refund(user_id, payment_id, now=None) -> dict:
    now = now or timezone.now()
    claimed = Payment.objects.filter(_refundable(user_id, now), id=payment_id).update(
        refunded_at=now
    )
    if not claimed:
        raise ConflictError("Refunds are available once per payment, within 6 hours of paying")
    row = Payment.objects.select_related("subscription").get(id=payment_id)

    def release():
        Payment.objects.filter(id=row.id).update(refunded_at=None)

    reason = _why_not_refundable(user_id, row.captured_at)
    if reason:
        release()
        raise ConflictError(reason)

    subscription = row.subscription
    try:
        refund = dodo(
            "POST",
            "/refunds",
            {
                "payment_id": row.dodo_payment_id,
                "reason": f"Self-serve refund {row.id}",
                "metadata": {"user_id": str(user_id), "payment_row": str(row.id)},
            },
        )
    except Exception:
        release()
        raise
    if refund.get("status") == "failed":
        release()
        raise AppError(
            502, "PAYMENT_PROVIDER_ERROR", "The payment provider declined the refund. Try again."
        )

    amount = refund.get("amount") or row.amount_paise
    refund_id = refund.get("refund_id")
    if subscription and subscription.plan == "pro" and subscription.dodo_subscription_id:
        try:
            dodo(
                "PATCH",
                f"/subscriptions/{subscription.dodo_subscription_id}",
                {"status": "cancelled"},
            )
        except Exception:  # noqa: BLE001, S110
            pass
    if refund.get("status") == "succeeded":
        finalize_refund(row, amount, refund_id, now)
    else:
        row.dodo_refund_id = refund_id
        row.save(update_fields=["dodo_refund_id"])
    return {"paymentId": row.id, "refundPaise": amount, "dodoRefundId": refund_id or ""}


def finalize_refund(row: Payment, amount: int, refund_id: str | None, now=None) -> None:
    """A succeeded refund ends the plan, whichever plan paid for it."""
    now = now or timezone.now()
    with transaction.atomic():
        row.status = Payment.Status.REFUNDED
        row.refunded_paise = amount
        row.dodo_refund_id = refund_id or row.dodo_refund_id
        row.save(update_fields=["status", "refunded_paise", "dodo_refund_id"])
        subscription = row.subscription
        if subscription:
            subscription.status = Subscription.Status.EXPIRED
            subscription.current_period_end = now
            subscription.cancelled_at = subscription.cancelled_at or now
            subscription.save(update_fields=["status", "current_period_end", "cancelled_at"])
        recompute_plan(row.user_id)


def revert_refund_claim(row: Payment) -> None:
    """A failed refund leaves the money with us, so the payment is captured again and can be retried."""
    row.refunded_at = None
    row.refunded_paise = None
    row.dodo_refund_id = None
    row.save(update_fields=["refunded_at", "refunded_paise", "dodo_refund_id"])
