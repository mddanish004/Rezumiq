import json
from urllib.request import Request, urlopen

import jwt
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import IntegrityError

from .usernames import generate_username

_jwks_client = None

_clerk_session_alg = "RS256"


def _verify_session_token(token: str) -> dict:
    global _jwks_client
    if not settings.CLERK_JWKS_URL:
        raise jwt.InvalidKeyError("CLERK_JWKS_URL is not configured")
    if _jwks_client is None:
        _jwks_client = jwt.PyJWKClient(settings.CLERK_JWKS_URL)
    key = _jwks_client.get_signing_key_from_jwt(token)
    return jwt.decode(
        token,
        key.key,
        algorithms=[_clerk_session_alg],
        options={"verify_aud": False, "verify_iss": False},
    )


def authenticate(token: str):
    """Verify a Clerk session JWT and return the matching local user, creating
    the row on first sight. Raises jwt exceptions for invalid tokens."""
    payload = _verify_session_token(token)
    clerk_id = payload.get("sub")
    if not clerk_id:
        raise jwt.InvalidTokenError("missing sub claim")

    User = get_user_model()
    return User.objects.get(clerk_id=clerk_id) if _ensure_user(clerk_id) else None


def _ensure_user(clerk_id: str) -> bool:
    """Create the local row for a Clerk id when missing. True when it exists
    afterwards (an IntegrityError from a concurrent provision resolves here)."""
    User = get_user_model()
    if User.objects.filter(clerk_id=clerk_id).exists():
        return True

    fields = _user_fields(_clerk_user(clerk_id))
    attempts = 0
    while attempts < 50:
        attempts += 1
        username = generate_username(fields.get("name"), fields.get("email", ""))
        values = {**fields, "clerk_id": clerk_id, "username": username}
        if not values["email"]:
            values["email"] = f"{username}@unset.invalid"
        try:
            User.objects.create(**values)
            return True
        except IntegrityError:
            if User.objects.filter(clerk_id=clerk_id).exists():
                return True
    raise jwt.InvalidTokenError("could not provision the account")


def sync_user(clerk_user: dict) -> bool:
    """Apply a Clerk user payload (backend API shape, same as user.* webhooks).
    Returns False when no local user matches."""
    User = get_user_model()
    clerk_id = clerk_user.get("id")
    if not clerk_id:
        return False
    user = User.objects.filter(clerk_id=clerk_id).first()
    if user is None:
        return False

    updates = {
        "username": user.username,
        "email": user.email,
        **_user_fields(clerk_user),
    }
    for key, value in updates.items():
        setattr(user, key, value)
    user.save(update_fields=list(updates.keys()))
    return True


def _user_fields(clerk_user: dict) -> dict:
    data = {
        "name": " ".join(filter(None, [clerk_user.get("first_name"), clerk_user.get("last_name")])),
        "avatar_url": clerk_user.get("image_url") or "",
    }
    emails = clerk_user.get("email_addresses") or []
    primary_id = clerk_user.get("primary_email_address_id")
    primary = emails[0] if emails else None
    for address in emails:
        if address.get("id") == primary_id:
            primary = address
            break
    data["email"] = (primary or {}).get("email_address", "")
    verification = (primary or {}).get("verification") or {}
    data["email_verified"] = verification.get("status") == "verified"
    return data


def _clerk_user(clerk_id: str) -> dict:
    """Fetch the Clerk user at provisioning. An empty payload means no backend
    key is configured, so the row starts email-less until a webhook syncs it."""
    if not settings.CLERK_SECRET_KEY:
        return {}
    request = Request(
        f"https://api.clerk.com/v1/users/{clerk_id}",
        headers={"Authorization": f"Bearer {settings.CLERK_SECRET_KEY}"},
    )
    try:
        with urlopen(request, timeout=5) as response:
            return json.loads(response.read())
    except (OSError, json.JSONDecodeError):
        return {}
