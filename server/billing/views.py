"""Billing endpoints, ported from billing.routes.ts and now backed by Dodo Payments."""

import json

from django.http import HttpRequest
from django.views.decorators.csrf import csrf_exempt

from api.common.errors import AppError, not_allowed
from api.common.guards import require_auth
from api.common.parse import parse_body
from api.common.responses import send_data

from . import service
from .dodo import verify_webhook_signature
from .schemas import (
    CheckoutOut,
    CreateCheckoutBody,
    CreateRefundBody,
    RefundOut,
    RefundQuoteOut,
    SubscriptionOut,
    WebhookOut,
)
from .webhooks import handle_dodo_event


@require_auth
@csrf_exempt
def checkouts(request: HttpRequest):
    """POST /v1/checkouts"""
    if request.method != "POST":
        return not_allowed(["POST"])
    body = parse_body(CreateCheckoutBody, request)
    return send_data(CheckoutOut, service.create_checkout(request.user.id, body.plan), status=201)


@require_auth
@csrf_exempt
def subscription(request: HttpRequest):
    """GET and DELETE /v1/subscription"""
    if request.method == "GET":
        return send_data(SubscriptionOut, service.get_subscription(request.user.id))
    if request.method == "DELETE":
        return send_data(SubscriptionOut, service.cancel_subscription(request.user.id))
    return not_allowed(["GET", "DELETE"])


@require_auth
@csrf_exempt
def refund_quote(request: HttpRequest):
    """GET /v1/refunds/quote"""
    if request.method != "GET":
        return not_allowed(["GET"])
    return send_data(RefundQuoteOut, service.get_refund_quote(request.user.id))


@require_auth
@csrf_exempt
def refunds(request: HttpRequest):
    """POST /v1/refunds"""
    if request.method != "POST":
        return not_allowed(["POST"])
    body = parse_body(CreateRefundBody, request)
    return send_data(
        RefundOut, service.request_refund(request.user.id, body.payment_id), status=201
    )


@csrf_exempt
def dodo_webhook(request: HttpRequest):
    """POST /v1/webhooks/dodo - signature is computed over the raw body."""
    if request.method != "POST":
        return not_allowed(["POST"])
    raw = request.body
    if not verify_webhook_signature(raw, request.headers):
        raise AppError(400, "INVALID_SIGNATURE", "Webhook signature verification failed")
    handle_dodo_event(json.loads(raw.decode("utf-8")), request.headers.get("webhook-id"))
    return send_data(WebhookOut, {"received": True})
