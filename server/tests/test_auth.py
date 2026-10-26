from allauth.account.models import EmailAddress
from django.core import mail
from django.test import Client

from tests.test_me import make_user


def _post_json(client: Client, path: str, body: dict):
    return client.post(path, body, content_type="application/json", HTTP_ACCEPT="application/json")


def test_signup_and_reset_mail_link_to_the_frontend(client: Client, db, settings):
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    mail.outbox.clear()

    response = _post_json(
        client,
        "/_allauth/browser/v1/auth/signup",
        {"email": "verify@example.com", "password": "CorrectHorseBattery9!"},
    )
    assert response.status_code == 200, response.content
    assert len(mail.outbox) == 1
    assert f"{settings.FRONTEND_URL}/account/verify-email/" in mail.outbox[0].body

    user = make_user(email="reset@example.com", username="reset")
    assert EmailAddress.objects.filter(user=user, verified=True).exists()
    mail.outbox.clear()

    response = _post_json(
        client,
        "/_allauth/browser/v1/auth/password/request",
        {"email": user.email},
    )
    assert response.status_code == 200, response.content
    assert len(mail.outbox) == 1
    assert f"{settings.FRONTEND_URL}/account/password/key/" in mail.outbox[0].body


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
