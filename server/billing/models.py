"""Billing: subscriptions, payments, promo codes."""

import uuid

from django.conf import settings
from django.db import models


class Subscription(models.Model):
    class Plan(models.TextChoices):
        SEASON_PASS = "season_pass", "Season Pass"
        PRO = "pro", "Pro"

    class Status(models.TextChoices):
        CREATED = "created", "Created"
        ACTIVE = "active", "Active"
        PAST_DUE = "past_due", "Past Due"
        CANCELLED = "cancelled", "Cancelled"
        EXPIRED = "expired", "Expired"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    plan = models.CharField(max_length=16, choices=Plan.choices)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.CREATED)
    dodo_subscription_id = models.CharField(max_length=128, blank=True, null=True, unique=True)
    current_period_start = models.DateTimeField(blank=True, null=True)
    current_period_end = models.DateTimeField(blank=True, null=True)
    cancelled_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [models.Index(fields=["user"])]


class Payment(models.Model):
    class Status(models.TextChoices):
        CREATED = "created", "Created"
        CAPTURED = "captured", "Captured"
        FAILED = "failed", "Failed"
        REFUNDED = "refunded", "Refunded"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    subscription = models.ForeignKey(Subscription, on_delete=models.SET_NULL, blank=True, null=True)
    dodo_checkout_session_id = models.CharField(max_length=128, blank=True, null=True)
    dodo_payment_id = models.CharField(max_length=128, blank=True, null=True, unique=True)
    amount_paise = models.IntegerField()
    currency = models.CharField(max_length=8, default="INR")
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.CREATED)
    method = models.CharField(max_length=32, blank=True, null=True)
    captured_at = models.DateTimeField(blank=True, null=True)
    refunded_at = models.DateTimeField(blank=True, null=True)
    refunded_paise = models.IntegerField(blank=True, null=True)
    dodo_refund_id = models.CharField(max_length=128, blank=True, null=True, unique=True)
    raw = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["user"]),
            models.Index(
                fields=["dodo_checkout_session_id"], name="billing_pay_dodo_ch_9c3f5b_idx"
            ),
            models.Index(fields=["subscription"]),
        ]


class WebhookEvent(models.Model):
    id = models.CharField(primary_key=True, max_length=128)
    received_at = models.DateTimeField(auto_now_add=True)


class PromoCode(models.Model):
    class Kind(models.TextChoices):
        PROMO = "promo", "Promo"
        AMBASSADOR = "ambassador", "Ambassador"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=64, unique=True)
    kind = models.CharField(max_length=16, choices=Kind.choices, default=Kind.PROMO)
    plan = models.CharField(
        max_length=16, choices=Subscription.Plan.choices, default=Subscription.Plan.SEASON_PASS
    )
    months = models.IntegerField()
    max_redemptions = models.IntegerField(blank=True, null=True)
    expires_at = models.DateTimeField(blank=True, null=True)
    active = models.BooleanField(default=True)
    owner = models.CharField(max_length=128, blank=True, null=True)
    note = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class PromoRedemption(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    promo_code = models.ForeignKey(PromoCode, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, unique=True)
    subscription = models.ForeignKey(Subscription, on_delete=models.SET_NULL, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
