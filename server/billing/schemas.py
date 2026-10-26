"""Billing schemas, ported from billing.schemas.ts."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from api.common.models import ApiModel

Plan = Literal["free", "season_pass", "pro"]
PaidPlan = Literal["season_pass", "pro"]


class CreateCheckoutBody(ApiModel):
    plan: PaidPlan


class CheckoutOut(ApiModel):
    provider: Literal["dodo"]
    session_id: str
    checkout_url: str
    plan: PaidPlan
    amount_paise: int
    currency: Literal["INR"]


class SubscriptionRow(ApiModel):
    id: UUID
    plan: PaidPlan
    status: Literal["created", "active", "past_due", "cancelled", "expired"]
    current_period_end: datetime | None
    cancelled_at: datetime | None


class SubscriptionOut(ApiModel):
    plan: Plan
    subscription: SubscriptionRow | None


class RefundQuote(ApiModel):
    payment_id: UUID
    plan: PaidPlan | None
    amount_paid_paise: int
    fee_paise: int
    refund_paise: int
    refundable_until: datetime


class RefundQuoteOut(ApiModel):
    quote: RefundQuote | None
    reason: str | None


class CreateRefundBody(ApiModel):
    payment_id: UUID


class RefundOut(ApiModel):
    payment_id: UUID
    refund_paise: int
    dodo_refund_id: str


class WebhookOut(ApiModel):
    received: bool
