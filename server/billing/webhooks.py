"""Dodo Payments webhook effects.

Dodo is the merchant of record, so a payment event is the record that money was taken:
rows are created/updated here rather than at checkout.
"""

from __future__ import annotations

from datetime import UTC, datetime

from django.db import IntegrityError, transaction
from django.utils import timezone

from billing.models import Payment, Subscription, WebhookEvent
from billing.service import _add_months, finalize_refund, recompute_plan, revert_refund_claim

SEASON_PASS_MONTHS = 6


def _dt(value) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value))
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)


def _first_delivery(webhook_id: str | None) -> bool:
    """Dodo retries deliveries; each webhook-id is processed once. Recorded in the same transaction as
    the event's effects, so a failure rolls both back and the retry runs it again."""
    if not webhook_id:
        return True
    try:
        WebhookEvent.objects.create(id=f"dodo:{webhook_id}")
        return True
    except IntegrityError:
        return False


def _activate_season_pass(subscription: Subscription, now: datetime) -> None:
    """A new Season Pass extends the latest-ending current one."""
    current = (
        Subscription.objects.filter(
            user_id=subscription.user_id, plan="season_pass", status="active"
        )
        .exclude(id=subscription.id)
        .order_by("-current_period_end")
        .first()
    )
    start = (
        current.current_period_end
        if current and current.current_period_end and current.current_period_end > now
        else now
    )
    subscription.status = Subscription.Status.ACTIVE
    subscription.current_period_start = start
    subscription.current_period_end = _add_months(start, SEASON_PASS_MONTHS)
    subscription.save(update_fields=["status", "current_period_start", "current_period_end"])


def _subscription_for_payment(entity: dict):
    ids = entity.get("subscription_ids") or []
    if ids:
        subscription = Subscription.objects.filter(dodo_subscription_id=ids[0]).first()
        if subscription:
            return subscription
    metadata = entity.get("metadata") or {}
    user_id = metadata.get("user_id")
    if not user_id:
        return None
    plan = metadata.get("plan") or "season_pass"
    return Subscription.objects.filter(user_id=user_id, plan=plan).order_by(
        "-created_at"
    ).first() or Subscription.objects.create(user_id=user_id, plan=plan, status="created")


def _on_payment_captured(event: dict, entity: dict) -> None:
    dodo_payment_id = entity.get("payment_id")
    if not dodo_payment_id or Payment.objects.filter(dodo_payment_id=dodo_payment_id).exists():
        return
    session_id = entity.get("checkout_session_id")
    row = (
        Payment.objects.filter(dodo_checkout_session_id=session_id).first() if session_id else None
    )
    subscription = (row.subscription if row else None) or _subscription_for_payment(entity)
    if subscription and not subscription.dodo_subscription_id:
        ids = entity.get("subscription_ids") or []
        if ids:
            subscription.dodo_subscription_id = ids[0]
            subscription.save(update_fields=["dodo_subscription_id"])
    if row is None:
        user_id = (entity.get("metadata") or {}).get("user_id") or (
            subscription.user_id if subscription else None
        )
        if not user_id:
            return
        row = Payment.objects.create(user_id=user_id, subscription=subscription, amount_paise=0)

    now = timezone.now()
    row.status = Payment.Status.CAPTURED
    row.captured_at = _dt(entity.get("created_at")) or now
    row.dodo_payment_id = dodo_payment_id
    row.method = entity.get("payment_method")
    row.amount_paise = entity.get("total_amount") or row.amount_paise
    row.raw = event
    row.save(
        update_fields=[
            "status",
            "captured_at",
            "dodo_payment_id",
            "method",
            "amount_paise",
            "raw",
        ]
    )
    if subscription and subscription.plan == "season_pass":
        _activate_season_pass(subscription, now)
    recompute_plan(row.user_id)


def _on_payment_failed(event: dict, entity: dict) -> None:
    session_id = entity.get("checkout_session_id")
    if not session_id:
        return
    Payment.objects.filter(dodo_checkout_session_id=session_id).exclude(
        status=Payment.Status.CAPTURED
    ).update(status=Payment.Status.FAILED, raw=event)


DODO_STATUSES = {
    "active": Subscription.Status.ACTIVE,
    "pending": Subscription.Status.CREATED,
    "cancelled": Subscription.Status.CANCELLED,
    "expired": Subscription.Status.EXPIRED,
    "failed": Subscription.Status.EXPIRED,
    "past_due": Subscription.Status.PAST_DUE,
    "on_hold": Subscription.Status.PAST_DUE,
    "paused": Subscription.Status.PAST_DUE,
}


def _on_subscription(event: dict, entity: dict) -> None:
    dodo_subscription_id = entity.get("subscription_id")
    if not dodo_subscription_id:
        return
    row = Subscription.objects.filter(dodo_subscription_id=dodo_subscription_id).first()
    if row is None:
        metadata = entity.get("metadata") or {}
        user_id = metadata.get("user_id")
        if not user_id:
            return
        plan = metadata.get("plan") or (
            "pro" if entity.get("product_id") == settings_product("pro") else "season_pass"
        )
        created = (
            Subscription.objects.filter(user_id=user_id, plan=plan).order_by("-created_at").first()
        )
        row = created or Subscription.objects.create(user_id=user_id, plan=plan, status="created")
        row.dodo_subscription_id = dodo_subscription_id
    if row.status == Subscription.Status.EXPIRED and event.get("type") != "subscription.expired":
        return

    row.status = DODO_STATUSES.get(entity.get("status"), Subscription.Status.ACTIVE)
    if event.get("type") == "subscription.expired":
        row.status = Subscription.Status.EXPIRED
    elif event.get("type") == "subscription.cancelled":
        row.status = Subscription.Status.CANCELLED
    row.current_period_start = _dt(entity.get("previous_billing_date")) or row.current_period_start
    row.current_period_end = _dt(entity.get("next_billing_date")) or row.current_period_end
    if row.status == Subscription.Status.CANCELLED and not row.cancelled_at:
        row.cancelled_at = _dt(entity.get("cancelled_at")) or timezone.now()
    row.save()
    recompute_plan(row.user_id)


def settings_product(plan: str) -> str | None:
    from django.conf import settings

    return settings.DODO_PRO_PRODUCT_ID if plan == "pro" else settings.DODO_SEASON_PASS_PRODUCT_ID


def _on_refund(event: dict, entity: dict) -> None:
    dodo_payment_id = entity.get("payment_id")
    if not dodo_payment_id:
        return
    row = Payment.objects.filter(dodo_payment_id=dodo_payment_id).first()
    if not row:
        return
    if event.get("type") == "refund.failed":
        revert_refund_claim(row)
        return
    amount = entity.get("amount") or row.amount_paise
    if entity.get("is_partial") or amount < row.amount_paise:
        row.refunded_paise = (row.refunded_paise or 0) + amount
        row.status = Payment.Status.REFUNDED
        row.save(update_fields=["refunded_paise", "status"])
        return
    finalize_refund(row, amount, entity.get("refund_id"))


def _apply(event: dict) -> None:
    name = event.get("type")
    entity = event.get("data") or {}
    if name == "payment.succeeded":
        _on_payment_captured(event, entity)
    elif name == "payment.failed":
        _on_payment_failed(event, entity)
    elif name in ("refund.succeeded", "refund.failed"):
        _on_refund(event, entity)
    elif name in (
        "subscription.active",
        "subscription.updated",
        "subscription.renewed",
        "subscription.plan_changed",
        "subscription.cancelled",
        "subscription.expired",
        "subscription.failed",
        "subscription.past_due",
        "subscription.on_hold",
        "subscription.paused",
        "subscription.unpaused",
    ):
        _on_subscription(event, entity)


def handle_dodo_event(event: dict, webhook_id: str | None) -> None:
    with transaction.atomic():
        if not _first_delivery(webhook_id):
            return
        _apply(event)
