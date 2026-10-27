import base64
import hashlib
import hmac
import json
import time

from django.conf import settings

_SIGNATURE_TOLERANCE_SECONDS = 300


def verify_request(body: bytes, headers) -> dict:
    """Validate Clerk's Svix signature headers and return the event payload."""
    secret = (settings.CLERK_WEBHOOK_SECRET or "").removeprefix("whsec_")
    if not secret:
        raise ValueError("CLERK_WEBHOOK_SECRET is not configured")

    message_id = headers.get("svix-id", "")
    timestamp = headers.get("svix-timestamp", "")
    signature = headers.get("svix-signature", "")
    if not message_id or not timestamp or not signature:
        raise ValueError("missing signature headers")

    age = time.time() - float(timestamp)
    if not age <= _SIGNATURE_TOLERANCE_SECONDS + 60:
        raise ValueError("expired signature")

    secret_bytes = base64.b64decode(secret)
    message = f"{message_id}.{timestamp}.{body.decode('utf-8')}".encode()
    expected = hmac.new(secret_bytes, message, hashlib.sha256).digest()
    for part in signature.split(" "):
        version, _, digest = part.partition(",")
        if version == "v1" and hmac.compare_digest(base64.b64decode(digest), expected):
            return json.loads(body)
    raise ValueError("invalid signature")


def apply_event(event: dict) -> None:
    from . import clerk

    event_type = event.get("type", "")
    data = event.get("data") or {}

    if event_type in ("user.created", "user.updated"):
        clerk.sync_user(data)
    elif event_type == "user.deleted":
        clerk_id = data.get("id")
        if clerk_id:
            from django.contrib.auth import get_user_model

            get_user_model().objects.filter(clerk_id=clerk_id).delete()
