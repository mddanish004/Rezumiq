import base64
import hashlib
import hmac
import json
import os
import time
from datetime import UTC, datetime, timedelta

import jwt as pyjwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from django.test import Client

from accounts.models import User
from tests.test_me import make_user


def _make_signing_pair():
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_pem = private_key.public_key().public_bytes(
        serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
    )
    private_pem = private_key.private_bytes(
        serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()
    )
    return private_pem, public_pem


class FakeJWKClient:
    class _Key:
        def __init__(self, value):
            self.key = value

    def __init__(self, public_pem):
        self._public = public_pem

    def get_signing_key_from_jwt(self, token):
        return self._Key(self._public)


def _install_clerk_keys(monkeypatch, settings):
    private_pem, public_pem = _make_signing_pair()
    monkeypatch.setattr("accounts.clerk._jwks_client", FakeJWKClient(public_pem))
    settings.CLERK_JWKS_URL = "https://clerk.example/.well-known/jwks.json"
    return private_pem


def _session_token(private_pem: str, clerk_id: str) -> str:
    now = datetime.now(tz=UTC)
    return pyjwt.encode(
        {"sub": clerk_id, "exp": now + timedelta(minutes=1), "iat": now, "nbf": now},
        private_pem,
        algorithm="RS256",
    )


def test_bearer_token_provisions_and_authenticates(client, db, settings, monkeypatch):
    private_pem = _install_clerk_keys(monkeypatch, settings)
    monkeypatch.setattr(
        "accounts.clerk._clerk_user",
        lambda clerk_id: {
            "id": clerk_id,
            "first_name": "Biraj",
            "last_name": "Chowdhury",
            "image_url": "https://img.clerk.example/a.png",
            "email_addresses": [
                {
                    "id": "email_1",
                    "email_address": "biraj@example.com",
                    "verification": {"status": "verified"},
                }
            ],
            "primary_email_address_id": "email_1",
        },
    )

    token = _session_token(private_pem, "user_2AbCdEfGh")
    headers = {"HTTP_AUTHORIZATION": f"Bearer {token}"}

    response = client.get("/v1/me", **headers)
    assert response.status_code == 200, response.content

    user = User.objects.get(clerk_id="user_2AbCdEfGh")
    assert user.username
    assert user.email == "biraj@example.com"
    assert user.email_verified is True
    assert user.avatar_url == "https://img.clerk.example/a.png"

    body = response.json()["data"]
    assert body["email"] == "biraj@example.com"
    assert body["name"] == "Biraj Chowdhury"
    assert body["image"] == "https://img.clerk.example/a.png"
    assert body["username"] == user.username

    user.username = "biraj"
    user.save()
    response = client.get("/v1/me", **headers)
    assert response.status_code == 200
    assert response.json()["data"]["username"] == "biraj"


def test_invalid_bearer_token_is_401(client, db, settings, monkeypatch):
    _install_clerk_keys(monkeypatch, settings)
    other_private_pem, _ = _make_signing_pair()

    response = client.get(
        "/v1/me", HTTP_AUTHORIZATION=f"Bearer {_session_token(other_private_pem, 'user_x')}"
    )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"

    response = client.get("/v1/me", HTTP_AUTHORIZATION="Bearer not-a-token")
    assert response.status_code == 401

    assert User.objects.count() == 0


def test_webhook_validates_signature_and_mirrors_user(client, db, settings):
    raw = os.urandom(32)
    settings.CLERK_WEBHOOK_SECRET = "whsec_" + base64.b64encode(raw).decode()
    settings.CLERK_JWKS_URL = None

    user = make_user(email="old@example.com", username="old")
    user.clerk_id = "user_2Webhook"
    user.save()

    event_payload = {
        "type": "user.updated",
        "data": {
            "id": "user_2Webhook",
            "first_name": "New",
            "last_name": "Name",
            "image_url": "https://img.clerk.example/n.png",
            "email_addresses": [
                {
                    "id": "e_1",
                    "email_address": "new@example.com",
                    "verification": {"status": "verified"},
                }
            ],
            "primary_email_address_id": "e_1",
        },
    }

    def _post_signed(payload: dict, secret: str | None = None):
        body_bytes = json.dumps(payload).encode()
        message_id = "msg_1"
        timestamp = str(int(time.time()))

        sec_raw = base64.b64decode((secret or settings.CLERK_WEBHOOK_SECRET).removeprefix("whsec_"))
        msg = f"{message_id}.{timestamp}.{body_bytes.decode()}".encode()
        signature = base64.b64encode(hmac.new(sec_raw, msg, hashlib.sha256).digest()).decode()

        return client.post(
            "/v1/webhooks/clerk",
            data=body_bytes,
            content_type="application/json",
            HTTP_SVIX_ID=message_id,
            HTTP_SVIX_TIMESTAMP=timestamp,
            HTTP_SVIX_SIGNATURE=f"v1,{signature}",
            HTTP_ACCEPT="application/json",
        )

    response = _post_signed(event_payload)
    assert response.status_code == 200, response.content

    user.refresh_from_db()
    assert user.email == "new@example.com"
    assert user.email_verified is True
    assert user.name == "New Name"
    assert user.avatar_url == "https://img.clerk.example/n.png"

    bad = _post_signed(event_payload, secret="whsec_" + base64.b64encode(os.urandom(32)).decode())
    assert bad.status_code == 400

    delete_payload = {"type": "user.deleted", "data": {"id": "user_2Webhook"}}
    deleted = _post_signed(delete_payload)
    assert deleted.status_code == 200
    assert not User.objects.filter(clerk_id="user_2Webhook").exists()


def test_webhook_without_secret_is_rejected(client, db, settings):
    settings.CLERK_WEBHOOK_SECRET = None
    response = client.post(
        "/v1/webhooks/clerk",
        data=b"{}",
        content_type="application/json",
        HTTP_ACCEPT="application/json",
    )
    assert response.status_code == 400


def test_old_allauth_urls_are_gone(client: Client, db):
    assert (
        client.get("/_allauth/browser/v1/auth/session", HTTP_ACCEPT="application/json").status_code
        == 404
    )
    assert client.get("/accounts/login/").status_code == 404


def test_guest_login_disabled_is_403(client: Client, db, settings):
    settings.ENABLE_GUEST_LOGIN = False
    response = client.post("/auth/guest")
    assert response.status_code == 403


def test_guest_login_creates_and_signs_in(client: Client, db, settings):
    settings.ENABLE_GUEST_LOGIN = True
    response = client.post("/auth/guest")
    assert response.status_code == 201

    body = response.json()
    assert body["ok"] is True

    from accounts.models import User

    user = User.objects.get(pk=body["user"]["id"])
    assert user.is_guest
    assert user.guest_expires_at is not None
    assert user.has_usable_password() is False
    assert user.plan == User.Plan.FREE

    response = client.post("/auth/guest")
    assert response.status_code == 201
    assert response.json()["user"]["id"] != user.pk
