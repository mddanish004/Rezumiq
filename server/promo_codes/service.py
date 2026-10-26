"""Promo code redemption, ported from modules/promo-codes."""

from __future__ import annotations

from django.db import transaction

from api.common.errors import AppError, ConflictError
from billing.models import PromoCode, PromoRedemption, Subscription
from billing.service import grant_plan, recompute_plan


def normalize_code(code: str) -> str:
    return code.strip().upper()


def redeem_problem(code, redeemed, now=None):
    from django.utils import timezone

    if now is None:
        now = timezone.now()
    if code is None or not code.active:
        return "This code doesn't exist or is no longer active"
    if code.expires_at and code.expires_at <= now:
        return "This code has expired"
    if code.max_redemptions is not None and redeemed >= code.max_redemptions:
        return "This code has been fully used"
    return None


def redeem_code(user_id, raw_code) -> dict:
    from django.contrib.auth import get_user_model

    User = get_user_model()
    with transaction.atomic():
        user = User.objects.select_for_update().get(id=user_id)
        if user.plan != "free":
            raise ConflictError("You already have a paid plan")
        if getattr(user, "is_guest", False):
            from api.common.errors import ForbiddenError

            raise ForbiddenError(
                "Create an account first, so your plan isn't deleted with this guest account"
            )
        if PromoRedemption.objects.filter(user_id=user_id).exists():
            raise ConflictError("You've already used a code")

        try:
            code = PromoCode.objects.select_for_update().get(code=normalize_code(raw_code))
        except PromoCode.DoesNotExist:
            code = None
        redeemed = PromoRedemption.objects.filter(promo_code=code).count() if code else 0
        problem = redeem_problem(code, redeemed)
        if problem:
            raise AppError(422, "PROMO_CODE_INVALID", problem)

        sub = grant_plan(user_id, code.plan, code.months)
        subscription = Subscription.objects.get(id=sub["id"])
        PromoRedemption.objects.create(promo_code=code, user_id=user_id, subscription=subscription)
        recompute_plan(user_id)
        return subscription
