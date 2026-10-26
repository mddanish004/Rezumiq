"""Rate limits on the unauthenticated public endpoints."""

import pytest
from django.core.management import call_command
from django.test import Client

from tests.test_me import make_user
from tests.test_resumes import CONTENT

ATS_TEXT = """Aarav Sharma
Backend Engineer
aarav.sharma@gmail.com | +91 98765 43210 | Bengaluru, India

Experience
Backend Engineer | Acme | 2020 - present
- Built and scaled REST APIs serving 2M requests daily.
- Led migration to microservices improving latency by 40%.

Skills
Python, Go, Django, REST APIs"""


@pytest.fixture(autouse=True)
def setup(db):
    call_command("seed_templates")


def _share_with_password(client: Client, password="secret123"):
    user = make_user()
    client.force_login(user)
    resume = client.post(
        "/v1/resumes",
        {"title": "R", "source": {"type": "content", "content": CONTENT}},
        content_type="application/json",
    ).json()["data"]
    link = client.post(
        f"/v1/resumes/{resume['id']}/share-links",
        {"isListed": True, "password": password},
        content_type="application/json",
    ).json()["data"]
    client.logout()
    return user, link


def _ats(client: Client, ip: str):
    return client.post(
        "/v1/ats-reports",
        {"text": ATS_TEXT, "jobDescription": None},
        content_type="application/json",
        REMOTE_ADDR=ip,
    )


def test_public_ats_allows_twenty_then_throttles(client: Client, db):
    for _ in range(20):
        assert _ats(client, "203.0.113.9").status_code == 200

    blocked = _ats(client, "203.0.113.9")
    assert blocked.status_code == 429
    assert blocked.json()["error"]["code"] == "RATE_LIMITED"

    assert _ats(client, "203.0.113.10").status_code == 200


def test_share_password_guesses_are_throttled(client: Client, db):
    user, link = _share_with_password(client)
    url = f"/v1/public/users/{user.username}/resumes/{link['slug']}"

    for _ in range(10):
        response = client.get(url, HTTP_X_SHARE_PASSWORD="wrong", REMOTE_ADDR="203.0.113.9")
        assert response.status_code == 401

    assert (
        client.get(url, HTTP_X_SHARE_PASSWORD="wrong", REMOTE_ADDR="203.0.113.9").status_code == 429
    )
    assert (
        client.get(url, HTTP_X_SHARE_PASSWORD="secret123", REMOTE_ADDR="203.0.113.9").status_code
        == 429
    )
    assert client.get(url, REMOTE_ADDR="203.0.113.9").status_code == 401
    assert (
        client.get(url, HTTP_X_SHARE_PASSWORD="secret123", REMOTE_ADDR="203.0.113.10").status_code
        == 200
    )
