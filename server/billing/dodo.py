"""Dodo Payments HTTP client and Standard Webhooks signature checks."""

from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import json
import time
import urllib.error
import urllib.request

from django.conf import settings

from api.common.errors import AppError

TEST_URL = "https://test.dodopayments.com"
LIVE_URL = "https://live.dodopayments.com"
TIMESTAMP_TOLERANCE = 5 * 60


def base_url() -> str:
    return LIVE_URL if settings.DODO_ENVIRONMENT == "live_mode" else TEST_URL


def request(method: str, path: str, body=None) -> dict:
    key = settings.DODO_API_KEY
    if not key:
        raise AppError(503, "PAYMENTS_NOT_CONFIGURED", "Payments are not configured")
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    data = json.dumps(body).encode() if body is not None else None
    http_request = urllib.request.Request(
        base_url() + path, data=data, headers=headers, method=method
    )
    try:
        with urllib.request.urlopen(http_request, timeout=15) as response:
            return json.loads(response.read() or b"{}")
    except urllib.error.HTTPError:
        raise AppError(
            502, "PAYMENT_PROVIDER_ERROR", "Could not reach the payment provider. Try again."
        ) from None
    except (urllib.error.URLError, TimeoutError):
        raise AppError(
            502, "PAYMENT_PROVIDER_ERROR", "Could not reach the payment provider. Try again."
        ) from None


def verify_webhook_signature(raw_body: bytes, headers) -> bool:
    """Standard Webhooks: HMAC-SHA256 of "{webhook-id}.{webhook-timestamp}.{body}".

    The secret may arrive as "whsec_<base64>"; the signature header holds one or more
    space-separated "v1,<base64>" entries and any match wins.
    """
    secret = settings.DODO_WEBHOOK_KEY
    webhook_id = headers.get("webhook-id")
    timestamp = headers.get("webhook-timestamp")
    signatures = headers.get("webhook-signature")
    if not secret or not webhook_id or not timestamp or not signatures:
        return False
    try:
        if abs(time.time() - int(timestamp)) > TIMESTAMP_TOLERANCE:
            return False
    except ValueError:
        return False

    key = secret.removeprefix("whsec_")
    try:
        signing_key = base64.b64decode(key)
    except (binascii.Error, ValueError):
        return False
    signed = b".".join([webhook_id.encode(), timestamp.encode(), raw_body])
    expected = base64.b64encode(hmac.new(signing_key, signed, hashlib.sha256).digest()).decode()
    for candidate in signatures.split():
        version, _, signature = candidate.partition(",")
        if version == "v1" and hmac.compare_digest(signature, expected):
            return True
    return False
